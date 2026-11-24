"""Step 3 (human-in-the-loop, optional): build an offline HTML contact sheet so a
pathologist can confirm weak labels. Clicking a tile cycles LN / non-LN / unsure;
"Download CSV" saves review.csv, which train.py picks up via --review.

  python review_sheet.py --tiers pos_review            # confirm ambiguous positives
  python review_sheet.py --tiers pos_high --sample 60  # QA the high-confidence set
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import os
import random

from PIL import Image


def load_meta(meta_path):
    meta = {}
    for l in open(meta_path):
        if l.strip():
            m = json.loads(l)
            meta[m["file_id"]] = m
    return meta


def tile(path, px, **fields):
    im = Image.open(path)
    im.thumbnail((px, px))
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=80)
    return {**fields, "img": base64.b64encode(b.getvalue()).decode()}


def render(tiles, px, title, out, note=""):
    """tiles: dicts with id, caption, sub, img. Writes a self-contained HTML page."""
    html = """<!doctype html><meta charset=utf-8><title>%s</title>
<style>body{font:13px system-ui;margin:16px;background:#fafafa;color:#222}h2{margin:4px 0}
.g{display:flex;flex-wrap:wrap;gap:10px}.t{width:%dpx;background:#fff;border:4px solid #ccc;padding:4px;cursor:pointer}
.t img{width:100%%}.t.ln{border-color:#2a9d4b}.t.non{border-color:#c0392b}.t.uns{border-color:#e6a700}
.bar{position:sticky;top:0;background:#fafafa;padding:8px 0;z-index:1}.sec{width:100%%;margin-top:14px}</style>
<div class=bar><h2>%s</h2><div>%s</div>
<b>Click: LN (green) → non-LN (red) → unsure (yellow) → unset.</b>
<button onclick=dl()>Download review.csv</button> <span id=c></span></div><div class=g id=g></div>
<script>const T=%s;const S=["","ln","non","uns"];const st={};
const g=document.getElementById('g');let sec=null;
T.forEach(t=>{if(t.section&&t.section!==sec){sec=t.section;const h=document.createElement('h3');
h.className='sec';h.textContent=sec;g.appendChild(h)}
const d=document.createElement('div');d.className='t';
d.innerHTML=`<img src="data:image/jpeg;base64,${t.img}"><div>${t.caption}<br><small>${t.sub||''}</small></div>`;
d.onclick=()=>{st[t.id]=((st[t.id]||0)+1)%%4;d.className='t '+S[st[t.id]];cnt()};g.appendChild(d)});
function cnt(){document.getElementById('c').textContent=Object.values(st).filter(v=>v).length+' / '+T.length+' reviewed'}
function dl(){const L={1:'1',2:'0',3:'unsure'};let s='file_id,review_label\\n';
for(const[k,v]of Object.entries(st))if(v)s+=k+','+L[v]+'\\n';
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{type:'text/csv'}));
a.download='review.csv';a.click()}cnt()</script>""" % (title, px, title, note, json.dumps(tiles))
    with open(out, "w") as f:
        f.write(html)
    print(f"{len(tiles)} tiles -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifest.csv")
    ap.add_argument("--meta", default="data/thumbs_meta.jsonl")
    ap.add_argument("--tiers", default="pos_review")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--out", default="data/review_sheet.html")
    ap.add_argument("--px", type=int, default=360)
    args = ap.parse_args()

    meta = load_meta(args.meta)
    base = os.path.dirname(args.meta)
    rows = [r for r in csv.DictReader(open(args.manifest))
            if r["tier"] in args.tiers.split(",") and r["file_id"] in meta]
    if args.sample:
        random.Random(0).shuffle(rows)
        rows = rows[: args.sample]
    rows.sort(key=lambda r: (r["tier"], r["project"], r["file_name"]))
    tiles = [tile(os.path.join(base, meta[r["file_id"]]["path"]), args.px, id=r["file_id"],
                  section=f"{r['tier']} · {r['project']}",
                  caption=r["file_name"][:23], sub=r["reason"]) for r in rows]
    render(tiles, args.px, "LN label review", args.out,
           "Does this slide contain lymph node tissue? Mark every tile you are sure about.")


if __name__ == "__main__":
    main()
