"""Error analysis page for a training run: every false negative, the most
confident false positives, and the least confident true positives, at the run's
operating threshold. Same click-to-relabel UI as review_sheet.py, so label
mistakes found here go straight back into data/review.csv.

  python errors_sheet.py --run runs/latest --split test
  python errors_sheet.py --run 'runs/cv-effb0-f*' --split test   # pooled K-fold OOF
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_sheet import load_meta, render, tile  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/latest", help="run dir or glob (K-fold)")
    ap.add_argument("--split", default="test", choices=["val", "test"])
    ap.add_argument("--manifest", default="data/manifest.csv")
    ap.add_argument("--meta", default="data/thumbs_meta.jsonl")
    ap.add_argument("--top-fp", type=int, default=60)
    ap.add_argument("--low-tp", type=int, default=20)
    ap.add_argument("--px", type=int, default=320)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    runs = sorted(d for d in glob.glob(a.run) if os.path.isfile(os.path.join(d, "metrics.json"))) or [a.run]
    man = {r["file_id"]: r for r in csv.DictReader(open(a.manifest))}
    meta = load_meta(a.meta)
    base = os.path.dirname(a.meta)
    preds = []
    for run in runs:
        thr = json.load(open(os.path.join(run, "metrics.json")))[a.split]["threshold"]
        for p in csv.DictReader(open(os.path.join(run, "predictions.csv"))):
            if p["split"] == a.split:
                preds.append({**p, "prob": float(p["prob"]), "label": int(p["label"]),
                              "thr": thr, "run": os.path.basename(run)})
    fn = sorted([p for p in preds if p["label"] == 1 and p["prob"] < p["thr"]], key=lambda p: p["prob"])
    fp = sorted([p for p in preds if p["label"] == 0 and p["prob"] >= p["thr"]], key=lambda p: -p["prob"])
    tp = sorted([p for p in preds if p["label"] == 1 and p["prob"] >= p["thr"]], key=lambda p: p["prob"])
    groups = [(f"False negatives ({len(fn)}) — missed LN slides", fn),
              (f"False positives (top {min(a.top_fp, len(fp))} of {len(fp)})", fp[: a.top_fp]),
              (f"Lowest-confidence true positives ({min(a.low_tp, len(tp))})", tp[: a.low_tp])]
    tiles = []
    for name, ps in groups:
        for p in ps:
            if p["file_id"] not in meta:
                continue
            m = man.get(p["file_id"], {})
            tiles.append(tile(os.path.join(base, meta[p["file_id"]]["path"]), a.px, id=p["file_id"],
                              section=name, caption=f"p={p['prob']:.3f} (thr {p['thr']:.3f}) · {p['project']}",
                              sub=f"{m.get('file_name', '')[:23]} · {m.get('tier', '')} · {m.get('reason', '')}"))
    if a.out:
        out = a.out
    elif len(runs) == 1:
        out = os.path.join(runs[0], f"errors_{a.split}.html")
    else:  # pooled: name after the common run prefix, e.g. runs/errors_cv-20261124-effb0-f_test.html
        out = os.path.join(os.path.dirname(runs[0]),
                           f"errors_{os.path.commonprefix([os.path.basename(r) for r in runs])}_{a.split}.html")
    n = len(preds)
    render(tiles, a.px, f"LN triage errors · {a.split} · {len(runs)} run(s)", out,
           f"{n} slides · FN {len(fn)} · FP {len(fp)} · threshold chosen on val for target sensitivity. "
           "If a label is wrong, mark it and download review.csv.")


if __name__ == "__main__":
    main()
