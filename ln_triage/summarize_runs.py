"""Aggregate several runs (seeds or K folds) into one table.

  python summarize_runs.py 'runs/cv-effb0-f*'      # K-fold: pooled out-of-fold test
  python summarize_runs.py 'runs/seed-effb0-s*'    # seeds: mean ± sd

Pooled confusion counts use each run's own val-chosen threshold, so the pooled
sensitivity/specificity is what the deployed procedure would have achieved.
Writes <parent>/summary_<pattern>.json and prints a markdown table.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train import auc, boot_ci  # noqa: E402

GATES = {"sensitivity": 0.98, "specificity": 0.90, "skcm_only_auc": 0.90}


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else "runs/*"
    runs = sorted(d for d in glob.glob(pat) if os.path.exists(os.path.join(d, "metrics.json")))
    if not runs:
        sys.exit(f"no finished runs match {pat}")
    rows, y, p, sk_y, sk_p = [], [], [], [], []
    tot = {"tp": 0, "fn": 0, "tn": 0, "fp": 0}
    for d in runs:
        t = json.load(open(os.path.join(d, "metrics.json")))["test"]
        rows.append({"run": os.path.basename(d), **{k: t.get(k) for k in
                     ("auc", "sensitivity", "specificity", "skcm_only_auc", "threshold", "tp", "fn", "tn", "fp")}})
        for k in tot:
            tot[k] += t[k]
        for r in csv.DictReader(open(os.path.join(d, "predictions.csv"))):
            if r["split"] == "test":
                y.append(int(r["label"]))
                p.append(float(r["prob"]))
                if r["project"] == "TCGA-SKCM":
                    sk_y.append(int(r["label"]))
                    sk_p.append(float(r["prob"]))

    def ms(k):
        v = [r[k] for r in rows if r[k] is not None]
        return (float(np.mean(v)), float(np.std(v))) if v else (None, None)

    pooled = {"n_runs": len(runs), "n_test_preds": len(y), **tot,
              "sensitivity": tot["tp"] / max(1, tot["tp"] + tot["fn"]),
              "specificity": tot["tn"] / max(1, tot["tn"] + tot["fp"]),
              "auc_pooled": auc(y, p), "auc_pooled_ci95": boot_ci(y, p, auc),
              "skcm_only_auc_pooled": auc(sk_y, sk_p)}
    per_run = {k: ms(k) for k in ("auc", "sensitivity", "specificity", "skcm_only_auc")}
    gates = {"sensitivity": pooled["sensitivity"] >= GATES["sensitivity"],
             "specificity": pooled["specificity"] >= GATES["specificity"],
             "skcm_only_auc": (pooled["skcm_only_auc_pooled"] or 0) >= GATES["skcm_only_auc"]}
    out = {"pattern": pat, "pooled": pooled, "per_run_mean_sd": per_run, "gates": gates, "runs": rows}
    parent = os.path.dirname(runs[0])
    name = "".join(c if c.isalnum() or c in "-_" else "_" for c in os.path.basename(pat))
    json.dump(out, open(os.path.join(parent, f"summary_{name}.json"), "w"), indent=1)

    f = lambda v: "—" if v is None else f"{v:.3f}"  # noqa: E731
    print("| run | AUC | sens | spec | SKCM-only AUC | FN | FP |\n|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['run']} | {f(r['auc'])} | {f(r['sensitivity'])} | {f(r['specificity'])} | "
              f"{f(r['skcm_only_auc'])} | {r['fn']} | {r['fp']} |")
    print(f"| **pooled** | {f(pooled['auc_pooled'])} | {f(pooled['sensitivity'])} | "
          f"{f(pooled['specificity'])} | {f(pooled['skcm_only_auc_pooled'])} | {tot['fn']} | {tot['fp']} |")
    print("\nPOC gates:", json.dumps(gates))


if __name__ == "__main__":
    main()
