"""Step 2: fetch the lowest pyramid level of each slide via HTTP range requests
(no full-WSI download), normalise to a fixed microns-per-pixel, save as JPEG.

Resumable: slides already in thumbs_meta.jsonl are skipped.
~5-10 MB transferred per slide; ~11.9k TCGA slides ~= 80-100 GB transfer total.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import GDC_API, RangeFile, read_lowest_level, resize_to_mpp  # noqa: E402


def one(row, out_dir, store_mpp, session):
    fid = row["file_id"]
    t = time.time()
    f = RangeFile(f"{GDC_API}/data/{fid}", session=session)
    arr, mpp, info = read_lowest_level(f)
    img = Image.fromarray(arr)
    if mpp < store_mpp:
        img = resize_to_mpp(img, mpp, store_mpp)
        mpp_out = store_mpp
    else:
        mpp_out = mpp  # level coarser than requested; keep and record
    path = os.path.join(out_dir, f"{fid}.jpg")
    img.save(path, quality=90)
    return {"file_id": fid, "path": os.path.relpath(path, os.path.dirname(out_dir)),
            "mpp": mpp_out, "w": img.width, "h": img.height,
            "fetched_mb": round(f.fetched / 1e6, 2), "sec": round(time.time() - t, 1), **info}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifest.csv")
    ap.add_argument("--out", default="data/thumbs")
    ap.add_argument("--store-mpp", type=float, default=8.0)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--tiers", default="pos_high,pos_review,neg_high,neg_low")
    ap.add_argument("--limit", type=int, default=0,
                    help="debug: take N slides (all positives first, then random negatives)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    meta_path = os.path.join(os.path.dirname(args.out), "thumbs_meta.jsonl")
    done = set()
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            done = {json.loads(l)["file_id"] for l in f if l.strip()}

    tiers = set(args.tiers.split(","))
    rows = [r for r in csv.DictReader(open(args.manifest)) if r["tier"] in tiers]
    if args.limit:
        rnd = random.Random(args.seed)
        pos = [r for r in rows if r["tier"].startswith("pos")]
        neg = [r for r in rows if r["tier"].startswith("neg")]
        rnd.shuffle(pos), rnd.shuffle(neg)
        npos = min(len(pos), args.limit // 3)
        rows = pos[:npos] + neg[: args.limit - npos]
    todo = [r for r in rows if r["file_id"] not in done]
    print(f"{len(rows)} selected, {len(done)} already done, {len(todo)} to fetch", flush=True)

    lock = threading.Lock()
    local = threading.local()

    def sess():
        if not hasattr(local, "s"):
            local.s = requests.Session()
        return local.s

    t0, n_ok, n_err, mb = time.time(), 0, 0, 0.0
    with ThreadPoolExecutor(args.workers) as ex, open(meta_path, "a") as meta, \
            open(os.path.join(os.path.dirname(args.out), "thumbs_errors.log"), "a") as errlog:
        futs = {ex.submit(lambda r: one(r, args.out, args.store_mpp, sess()), r): r for r in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            r = futs[fu]
            try:
                rec = fu.result()
                with lock:
                    meta.write(json.dumps(rec) + "\n")
                    meta.flush()
                n_ok += 1
                mb += rec["fetched_mb"]
            except Exception as e:  # keep going; failures are logged and retried next run
                n_err += 1
                errlog.write(f"{r['file_id']}\t{type(e).__name__}: {e}\n")
                errlog.flush()
            if i % 50 == 0 or i == len(todo):
                el = time.time() - t0
                print(f"[{i}/{len(todo)}] ok={n_ok} err={n_err} {mb/1e3:.1f}GB "
                      f"{i/el:.2f} slides/s eta {(len(todo)-i)/(i/el)/3600:.1f}h", flush=True)


if __name__ == "__main__":
    main()
