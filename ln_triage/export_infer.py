"""Step 5: export the trained model to ONNX and run CPU-only inference.

  python export_infer.py export --run runs/latest              # -> model.onnx + model.json
  python export_infer.py bench  --run runs/latest              # CPU latency (ONNX Runtime)
  python export_infer.py predict --run runs/latest --image x.jpg --mpp 8
  python export_infer.py predict --run runs/latest --svs slide.svs

`predict` prints JSON in the same shape as the pre-inference service contract,
so this model and the doctor's model are interchangeable behind one API.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import preprocess, read_lowest_level, to_tensor_np  # noqa: E402


def export(run):
    import torch
    from train import build_model
    ck = torch.load(os.path.join(run, "best.pt"), map_location="cpu")
    a = ck["args"]
    m = build_model(a["arch"])
    m.load_state_dict(ck["model"])
    m.eval()
    x = torch.zeros(1, 3, a["canvas"], a["canvas"])
    path = os.path.join(run, "model.onnx")
    torch.onnx.export(m, x, path, input_names=["image"], output_names=["logit"],
                      dynamic_axes={"image": {0: "n"}, "logit": {0: "n"}}, opset_version=17,
                      dynamo=False)
    card = {"model": f"aetherai-ln-triage-{a['arch']}", "threshold": ck["threshold"],
            "mpp": a["mpp"], "canvas": a["canvas"], "input": "RGB thumbnail, any mpp <= model mpp",
            "weights_init": "random (no ImageNet)", "train_data": "TCGA GDC open-access diagnostic slides"}
    mfile = os.path.join(run, "metrics.json")
    if os.path.exists(mfile):
        card["test_metrics"] = {k: v for k, v in json.load(open(mfile))["test"].items()}
    json.dump(card, open(os.path.join(run, "model.json"), "w"), indent=1)
    print("exported", path)


def session(run, threads=0):
    import onnxruntime as ort
    so = ort.SessionOptions()
    if threads:
        so.intra_op_num_threads = threads
    return ort.InferenceSession(os.path.join(run, "model.onnx"), so, providers=["CPUExecutionProvider"])


def run_one(sess, card, img, mpp):
    t = time.time()
    x = to_tensor_np(preprocess(img, mpp, card["mpp"], card["canvas"]))[None]
    logit = float(sess.run(None, {"image": x})[0][0, 0])
    p = 1 / (1 + np.exp(-logit))
    ln = int(p >= card["threshold"])
    return {"model": card["model"], "prediction": "LN" if ln else "Non_LN", "prediction_LN": ln,
            "probability": p, "threshold": card["threshold"], "latency_ms": round((time.time() - t) * 1e3),
            "status": "OK"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["export", "bench", "predict"])
    ap.add_argument("--run", default="runs/latest")
    ap.add_argument("--image")
    ap.add_argument("--mpp", type=float, help="microns/pixel of --image")
    ap.add_argument("--svs")
    ap.add_argument("--threads", type=int, default=4, help="CPU threads (match target server)")
    a = ap.parse_args()
    if a.cmd == "export":
        return export(a.run)
    card = json.load(open(os.path.join(a.run, "model.json")))
    sess = session(a.run, a.threads)
    if a.cmd == "bench":
        x = np.random.randn(1, 3, card["canvas"], card["canvas"]).astype(np.float32)
        for _ in range(3):
            sess.run(None, {"image": x})
        ts = []
        for _ in range(20):
            t = time.time()
            sess.run(None, {"image": x})
            ts.append(time.time() - t)
        print(json.dumps({"threads": a.threads, "canvas": card["canvas"],
                          "median_ms": round(1e3 * float(np.median(ts))),
                          "p95_ms": round(1e3 * float(np.percentile(ts, 95)))}))
        return
    if a.svs:
        arr, mpp, _ = read_lowest_level(open(a.svs, "rb"))
        img = Image.fromarray(arr)
    else:
        img, mpp = Image.open(a.image), a.mpp
    print(json.dumps(run_one(sess, card, img, mpp)))


if __name__ == "__main__":
    main()
