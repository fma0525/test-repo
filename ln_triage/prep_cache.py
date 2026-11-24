"""Optional speed-up: pre-resample thumbnails to the training mpp and crop to the
tissue bounding box, so DataLoader workers skip the big-JPEG decode + resize.
Use when GPU utilisation is low because the input pipeline is the bottleneck.

  python prep_cache.py --mpp 16
  python train.py --meta data/cache16_meta.jsonl ...

Equivalent to the online path (resize -> tissue bbox), so inference needs no change.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import resize_to_mpp, tissue_bbox  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def work(job):
    m, base, out_dir, mpp, margin = job
    dst = os.path.join(out_dir, f"{m['file_id']}.png")
    if not os.path.exists(dst):
        img = Image.open(os.path.join(base, m["path"])).convert("RGB")
        img = resize_to_mpp(img, m["mpp"], mpp) if m["mpp"] < mpp else img
        x0, y0, x1, y1 = tissue_bbox(np.asarray(img), margin=margin)
        img.crop((x0, y0, x1, y1)).save(dst, compress_level=1)
    w, h = Image.open(dst).size
    return {"file_id": m["file_id"], "path": os.path.relpath(dst, base),
            "mpp": max(mpp, m["mpp"]), "w": w, "h": h}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default="data/thumbs_meta.jsonl")
    ap.add_argument("--mpp", type=float, default=16.0)
    ap.add_argument("--margin", type=int, default=64)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()
    base = os.path.dirname(a.meta)
    tag = f"cache{a.mpp:g}"
    out_dir = os.path.join(base, tag)
    os.makedirs(out_dir, exist_ok=True)
    metas = [json.loads(l) for l in open(a.meta) if l.strip()]
    jobs = [(m, base, out_dir, a.mpp, a.margin) for m in metas]
    with Pool(a.workers) as pool, open(os.path.join(base, f"{tag}_meta.jsonl"), "w") as f:
        for i, rec in enumerate(pool.imap_unordered(work, jobs, chunksize=8), 1):
            f.write(json.dumps(rec) + "\n")
            if i % 500 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)}", flush=True)
    print(f"-> {base}/{tag}_meta.jsonl")


if __name__ == "__main__":
    main()
