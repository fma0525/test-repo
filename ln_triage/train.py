"""Step 4: train the slide-level "contains lymph node?" classifier.

* Weights trained FROM SCRATCH (no ImageNet / no non-commercial foundation models),
  so the resulting model carries only the training data's licence.
* Fixed physical scale: thumbnails resampled to --mpp (default 16 um/px) and placed
  on a --canvas square (default 1024 px = 16.4 mm field of view).
* Patient-level split (by case_id), stratified by label; positives oversampled.
* Threshold chosen on validation for sensitivity >= --target-sens; test reported once.
* Confounding check: AUC restricted to TCGA-SKCM (positives vs same-project negatives).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageFilter
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import make_canvas, preprocess, resize_to_mpp, tissue_bbox, to_tensor_np  # noqa: E402


# --------------------------------------------------------------------------- data
def load_table(args):
    meta = {}
    for l in open(args.meta):
        if l.strip():
            m = json.loads(l)
            meta[m["file_id"]] = m
    review = {}
    if args.review and os.path.exists(args.review):
        for r in csv.DictReader(open(args.review)):
            review[r["file_id"]] = r["review_label"]
    tiers = set(args.tiers.split(","))
    base = os.path.dirname(args.meta)
    rows = []
    for r in csv.DictReader(open(args.manifest)):
        if r["file_id"] not in meta:
            continue
        lab = r["label"]
        if r["file_id"] in review:  # pathologist decision overrides weak label
            if review[r["file_id"]] not in ("0", "1"):
                continue
            lab = review[r["file_id"]]
        elif r["tier"] not in tiers:
            continue
        if lab == "":
            continue
        m = meta[r["file_id"]]
        rows.append({**r, "label": int(lab), "path": os.path.join(base, m["path"]), "mpp": m["mpp"]})
    return rows


def split_cases(rows, seed, frac=(0.7, 0.15, 0.15)):
    """Patient-level, label-stratified split. A case is 'positive' if any slide is."""
    case_lab = {}
    for r in rows:
        case_lab[r["case_id"]] = max(case_lab.get(r["case_id"], 0), r["label"])
    out = {}
    for lab in (0, 1):
        cs = sorted(c for c, l in case_lab.items() if l == lab)
        cs.sort(key=lambda c: hashlib.md5(f"{seed}{c}".encode()).hexdigest())
        n = len(cs)
        a, b = round(n * frac[0]), round(n * (frac[0] + frac[1]))
        for i, c in enumerate(cs):
            out[c] = "train" if i < a else ("val" if i < b else "test")
    for r in rows:
        r["split"] = out[r["case_id"]]
    return rows


class SlideDS(Dataset):
    def __init__(self, rows, args, train):
        self.rows, self.a, self.train = rows, args, train

    def __len__(self):
        return len(self.rows)

    def _aug(self, img):
        a = self.a
        s = random.uniform(0.85, 1.18)  # mild scale jitter around the fixed mpp
        img = resize_to_mpp(img, 1.0, 1.0 / s)
        x0, y0, x1, y1 = tissue_bbox(np.asarray(img))
        cx = random.uniform(x0 + min(a.canvas, x1 - x0) / 2, x1 - min(a.canvas, x1 - x0) / 2)
        cy = random.uniform(y0 + min(a.canvas, y1 - y0) / 2, y1 - min(a.canvas, y1 - y0) / 2)
        img = make_canvas(img, a.canvas, (cx, cy))
        if random.random() < 0.5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img = img.rotate(90 * random.randint(0, 3))
        arr = np.asarray(img).astype(np.float32)
        # H&E-ish colour jitter: per-channel gain/bias, brightness, saturation
        arr = arr * np.random.uniform(0.9, 1.1, 3) + np.random.uniform(-12, 12, 3)
        g = arr.mean(2, keepdims=True)
        arr = g + (arr - g) * random.uniform(0.7, 1.3)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        if random.random() < 0.2:
            img = img.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 1.2)))
        return img

    def __getitem__(self, i):
        r = self.rows[i]
        img = Image.open(r["path"]).convert("RGB")
        if self.train:
            img = resize_to_mpp(img, r["mpp"], self.a.mpp)
            img = self._aug(img)
        else:
            img = preprocess(img, r["mpp"], self.a.mpp, self.a.canvas)
        x = torch.from_numpy(to_tensor_np(img))
        if self.train and random.random() < 0.3:  # random erasing
            h = random.randint(self.a.canvas // 16, self.a.canvas // 5)
            y, x0 = random.randint(0, self.a.canvas - h), random.randint(0, self.a.canvas - h)
            x[:, y:y + h, x0:x0 + h] = 0
        return x, torch.tensor(float(r["label"]))


# --------------------------------------------------------------------------- model
def build_model(name, prior=0.3):
    import torchvision.models as tvm
    if name == "effb0":
        m = tvm.efficientnet_b0(weights=None, num_classes=1)
    elif name == "resnet18":
        m = tvm.resnet18(weights=None, num_classes=1)
    elif name == "mnv3":
        m = tvm.mobilenet_v3_large(weights=None, num_classes=1)
    else:
        raise ValueError(name)
    # start from the class prior: zero-weight head, bias = logit(prior). From-scratch
    # nets otherwise emit |logit|~4 at step 0 and the first epochs are wasted.
    head = [mod for mod in m.modules() if isinstance(mod, nn.Linear)][-1]
    nn.init.zeros_(head.weight)
    nn.init.constant_(head.bias, math.log(prior / (1 - prior)))
    return m


# --------------------------------------------------------------------------- metrics
def auc(y, p):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if len(set(y)) == 2 else None


def thr_for_sens(y, p, target):
    pos = np.sort(np.asarray(p)[np.asarray(y) == 1])
    if len(pos) == 0:
        return 0.5
    k = int(math.floor((1 - target) * len(pos)))  # allow k misses
    return float(pos[k]) - 1e-7


def at_thr(y, p, t):
    y, p = np.asarray(y), np.asarray(p)
    pr = p >= t
    tp, fn = int((pr & (y == 1)).sum()), int((~pr & (y == 1)).sum())
    tn, fp = int((~pr & (y == 0)).sum()), int((pr & (y == 0)).sum())
    return {"threshold": t, "tp": tp, "fn": fn, "tn": tn, "fp": fp,
            "sensitivity": tp / max(1, tp + fn), "specificity": tn / max(1, tn + fp),
            "skip_rate": float((~pr).mean())}


def boot_ci(y, p, fn, n=1000, seed=0):
    rng = np.random.default_rng(seed)
    y, p = np.asarray(y), np.asarray(p)
    v = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) == 2:
            v.append(fn(y[i], p[i]))
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None


@torch.no_grad()
def predict(model, dl, dev, amp):
    model.eval()
    out = []
    for x, _ in dl:
        with torch.autocast(dev.type, dtype=torch.bfloat16, enabled=amp):
            out.append(torch.sigmoid(model(x.to(dev, non_blocking=True)).float()).squeeze(1).cpu())
    return torch.cat(out).numpy()


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifest.csv")
    ap.add_argument("--meta", default="data/thumbs_meta.jsonl")
    ap.add_argument("--review", default="data/review.csv")
    ap.add_argument("--tiers", default="pos_high,neg_high,neg_low")
    ap.add_argument("--out", default="runs/latest")
    ap.add_argument("--arch", default="effb0", choices=["effb0", "resnet18", "mnv3"])
    ap.add_argument("--mpp", type=float, default=16.0)
    ap.add_argument("--canvas", type=int, default=1024)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--steps-per-epoch", type=int, default=200)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=0.05)
    ap.add_argument("--pos-frac", type=float, default=0.3, help="positive share per batch")
    ap.add_argument("--target-sens", type=float, default=0.98)
    ap.add_argument("--workers", type=int, default=min(16, os.cpu_count() or 4))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--patience", type=int, default=10)
    args = ap.parse_args()

    random.seed(args.seed), np.random.seed(args.seed), torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp = dev.type == "cuda" and torch.cuda.is_bf16_supported()
    rows = split_cases(load_table(args), args.seed)
    S = {s: [r for r in rows if r["split"] == s] for s in ("train", "val", "test")}
    summ = {s: {"n": len(v), "pos": sum(r["label"] for r in v)} for s, v in S.items()}
    print("device", dev, "bf16", amp, json.dumps(summ), flush=True)
    with open(os.path.join(args.out, "split.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file_id", "case_id", "project", "label", "split"])
        for r in rows:
            w.writerow([r["file_id"], r["case_id"], r["project"], r["label"], r["split"]])

    tr = S["train"]
    npos = max(1, sum(r["label"] for r in tr))
    nneg = max(1, len(tr) - npos)
    wts = [args.pos_frac / npos if r["label"] else (1 - args.pos_frac) / nneg for r in tr]
    sampler = WeightedRandomSampler(wts, args.steps_per_epoch * args.bs, replacement=True)
    kw = dict(num_workers=args.workers, pin_memory=dev.type == "cuda",
              persistent_workers=args.workers > 0)
    dl_tr = DataLoader(SlideDS(tr, args, True), batch_size=args.bs, sampler=sampler, drop_last=True, **kw)
    dl_va = DataLoader(SlideDS(S["val"], args, False), batch_size=args.bs, **kw)
    dl_te = DataLoader(SlideDS(S["test"], args, False), batch_size=args.bs, **kw)

    model = build_model(args.arch, args.pos_frac).to(dev).to(memory_format=torch.channels_last)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    total = args.epochs * args.steps_per_epoch
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, args.lr, total_steps=total, pct_start=0.1)
    lossf = nn.BCEWithLogitsLoss()

    best, bad, log = -1.0, 0, []
    yv = [r["label"] for r in S["val"]]
    for ep in range(args.epochs):
        model.train()
        t0, tl = time.time(), 0.0
        for x, y in dl_tr:
            x = x.to(dev, non_blocking=True).to(memory_format=torch.channels_last)
            y = y.to(dev)
            with torch.autocast(dev.type, dtype=torch.bfloat16, enabled=amp):
                loss = lossf(model(x).float().squeeze(1), y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tl += loss.item()
        pv = predict(model, dl_va, dev, amp)
        va = auc(yv, pv) or 0.0
        t = thr_for_sens(yv, pv, args.target_sens)
        m = at_thr(yv, pv, t)
        rec = {"epoch": ep, "loss": tl / args.steps_per_epoch, "val_auc": va,
               "val_spec_at_sens": m["specificity"], "sec": round(time.time() - t0)}
        log.append(rec)
        print(json.dumps(rec), flush=True)
        score = va + m["specificity"]  # tie-break AUC with operating-point specificity
        if score > best:
            best, bad = score, 0
            torch.save({"model": model.state_dict(), "args": vars(args), "threshold": t},
                       os.path.join(args.out, "best.pt"))
        else:
            bad += 1
            if bad >= args.patience:
                print("early stop", flush=True)
                break

    ck = torch.load(os.path.join(args.out, "best.pt"), map_location=dev)
    model.load_state_dict(ck["model"])
    res = {"data": summ, "args": vars(args), "train_log": log}
    preds = {}
    for s, dl in (("val", dl_va), ("test", dl_te)):
        p = predict(model, dl, dev, amp)
        y = [r["label"] for r in S[s]]
        preds[s] = p
        res[s] = {"auc": auc(y, p), "auc_ci95": boot_ci(y, p, auc), **at_thr(y, p, ck["threshold"])}
        sk = [i for i, r in enumerate(S[s]) if r["project"] == "TCGA-SKCM"]
        res[s]["skcm_only_auc"] = auc([y[i] for i in sk], p[sk]) if sk else None
        res[s]["skcm_only_n"] = len(sk)
    with open(os.path.join(args.out, "metrics.json"), "w") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(args.out, "predictions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file_id", "project", "split", "label", "prob"])
        for s in ("val", "test"):
            for r, p in zip(S[s], preds[s]):
                w.writerow([r["file_id"], r["project"], s, r["label"], f"{p:.6f}"])
    print(json.dumps({k: res[k] for k in ("val", "test")}, indent=1))


if __name__ == "__main__":
    main()
