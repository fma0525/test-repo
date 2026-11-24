"""Shared helpers: GDC access, HTTP range reading, and the image preprocessing
used by BOTH training and inference (keep them identical)."""
from __future__ import annotations

import io
import re
import time

import numpy as np
import requests
from PIL import Image

GDC_API = "https://api.gdc.cancer.gov"
Image.MAX_IMAGE_PIXELS = None


# --------------------------------------------------------------------------- HTTP
class RangeFile(io.RawIOBase):
    """Read-only, seekable file over HTTP Range requests with a block cache.

    Lets tifffile parse a multi-GB SVS while only downloading the bytes of the
    pages we actually read (typically a few MB for the lowest pyramid level).
    """

    def __init__(self, url: str, block: int = 256 * 1024, session=None, retries: int = 4):
        self.url, self.block, self.retries = url, block, retries
        self.s = session or requests.Session()
        r = self._get(0, 0)
        self.size = int(r.headers["Content-Range"].split("/")[1])
        self.pos, self.cache, self.fetched = 0, {}, 0

    def _get(self, a, b):
        for i in range(self.retries):
            try:
                r = self.s.get(self.url, headers={"Range": f"bytes={a}-{b}"}, timeout=120)
                r.raise_for_status()
                return r
            except requests.RequestException:
                if i == self.retries - 1:
                    raise
                time.sleep(2 ** i)

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def _blk(self, i):
        if i not in self.cache:
            a = i * self.block
            b = min(self.size, a + self.block) - 1
            self.cache[i] = self._get(a, b).content
            self.fetched += len(self.cache[i])
        return self.cache[i]

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        out = bytearray()
        while n > 0:
            i, o = divmod(self.pos, self.block)
            chunk = self._blk(i)[o:o + n]
            if not chunk:
                break
            out += chunk
            self.pos += len(chunk)
            n -= len(chunk)
        return bytes(out)

    def readinto(self, b):
        d = self.read(len(b))
        b[: len(d)] = d
        return len(d)


def gdc_files(filters: dict, fields: list[str], page: int = 2000) -> list[dict]:
    """Page through the GDC /files endpoint."""
    out, start = [], 0
    while True:
        body = {"filters": filters, "fields": ",".join(fields), "size": page, "from": start}
        r = requests.post(f"{GDC_API}/files", json=body, timeout=120)
        r.raise_for_status()
        d = r.json()["data"]
        out += d["hits"]
        start += page
        if start >= d["pagination"]["total"]:
            return out


# --------------------------------------------------------------------------- SVS
_MPP_RE = re.compile(r"MPP\s*=\s*([0-9.]+)")


def read_lowest_level(fobj, max_level_mb: float = 150.0):
    """Return (rgb uint8 array, mpp_of_array, info dict) for the lowest-res
    tiled pyramid level of an Aperio SVS (or any pyramidal TIFF)."""
    import tifffile

    tf = tifffile.TiffFile(fobj)
    pages = list(tf.pages)
    desc0 = pages[0].description or ""
    m = _MPP_RE.search(desc0)
    mpp0 = float(m.group(1)) if m else None
    w0 = pages[0].shape[1]
    tiled = [p for p in pages if p.is_tiled]
    tiled.sort(key=lambda p: p.shape[0] * p.shape[1])
    info = {"mpp0": mpp0, "mpp_assumed": mpp0 is None, "w0": w0}
    page = tiled[0]
    level_mb = sum(page.databytecounts) / 1e6
    if level_mb > max_level_mb:
        # pyramid has no small level: fall back to the embedded thumbnail strip page
        thumbs = [p for p in pages[1:] if not p.is_tiled and "label" not in (p.description or "")
                  and "macro" not in (p.description or "")]
        if thumbs:
            page = max(thumbs, key=lambda p: p.shape[0])
            info["fallback_thumbnail"] = True
    arr = page.asarray()
    if arr.ndim == 3 and arr.shape[2] == 4:
        arr = arr[..., :3]
    mpp = (mpp0 or 0.5) * w0 / arr.shape[1]
    info.update({"level_shape": list(arr.shape), "level_mpp": mpp})
    return arr, mpp, info


# --------------------------------------------------------------------------- preprocessing
def resize_to_mpp(img: Image.Image, mpp: float, target_mpp: float) -> Image.Image:
    s = mpp / target_mpp
    if abs(s - 1) < 1e-3:
        return img
    w, h = max(1, round(img.width * s)), max(1, round(img.height * s))
    return img.resize((w, h), Image.BILINEAR if s > 1 else Image.LANCZOS)


def tissue_mask(rgb: np.ndarray) -> np.ndarray:
    """Cheap tissue detector: saturation + not-white, robust to pen marks only partly."""
    a = rgb.astype(np.int16)
    sat = a.max(2) - a.min(2)
    bright = a.mean(2)
    return (sat > 20) & (bright < 235) & (bright > 30)


def tissue_bbox(rgb: np.ndarray, margin: int = 16):
    m = tissue_mask(rgb)
    ys, xs = np.nonzero(m)
    if len(ys) < 50:
        return 0, 0, rgb.shape[1], rgb.shape[0]
    # robust bbox: ignore specks with percentiles
    y0, y1 = np.percentile(ys, [0.5, 99.5]).astype(int)
    x0, x1 = np.percentile(xs, [0.5, 99.5]).astype(int)
    return (max(0, x0 - margin), max(0, y0 - margin),
            min(rgb.shape[1], x1 + margin), min(rgb.shape[0], y1 + margin))


def make_canvas(img: Image.Image, canvas: int, center=None) -> Image.Image:
    """Place img on a white canvas x canvas square (center-crop if larger)."""
    w, h = img.size
    if center is None:
        center = (w / 2, h / 2)
    left = int(round(center[0] - canvas / 2))
    top = int(round(center[1] - canvas / 2))
    out = Image.new("RGB", (canvas, canvas), (255, 255, 255))
    src = img.crop((max(0, left), max(0, top), min(w, left + canvas), min(h, top + canvas)))
    out.paste(src, (max(0, -left), max(0, -top)))
    return out


def preprocess(img: Image.Image, mpp: float, target_mpp: float, canvas: int) -> Image.Image:
    """Deterministic preprocessing used at eval / inference time."""
    img = resize_to_mpp(img.convert("RGB"), mpp, target_mpp)
    x0, y0, x1, y1 = tissue_bbox(np.asarray(img))
    img = img.crop((x0, y0, x1, y1))
    if max(img.size) > canvas:  # tissue larger than field of view: shrink to fit (rare)
        s = canvas / max(img.size)
        img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    return make_canvas(img, canvas)


MEAN = np.array([0.80, 0.65, 0.80], dtype=np.float32)  # rough H&E stats; fixed, no ImageNet
STD = np.array([0.15, 0.20, 0.12], dtype=np.float32)


def to_tensor_np(img: Image.Image) -> np.ndarray:
    a = np.asarray(img, dtype=np.float32) / 255.0
    a = (a - MEAN) / STD
    return a.transpose(2, 0, 1).copy()
