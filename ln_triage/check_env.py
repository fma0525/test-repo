"""Sanity check: torch, GPU, bf16, GDC reachability, disk."""
import json
import platform
import shutil

import requests
import torch

info = {"python": platform.python_version(), "arch": platform.machine(), "torch": torch.__version__,
        "cuda": torch.cuda.is_available(), "disk_free_gb": shutil.disk_usage(".").free // 2**30}
if torch.cuda.is_available():
    info["gpu"] = torch.cuda.get_device_name(0)
    info["capability"] = ".".join(map(str, torch.cuda.get_device_capability(0)))
    info["bf16"] = torch.cuda.is_bf16_supported()
    x = torch.randn(2048, 2048, device="cuda")
    info["matmul_ok"] = bool(torch.isfinite(x @ x).all())
try:
    info["gdc_status"] = requests.get("https://api.gdc.cancer.gov/status", timeout=20).json().get("status")
except Exception as e:  # noqa: BLE001
    info["gdc_status"] = f"UNREACHABLE: {e}"
print(json.dumps(info, indent=1))
if not info["cuda"]:
    print("WARNING: no CUDA - training will run on CPU (very slow).")
