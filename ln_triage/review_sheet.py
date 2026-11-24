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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifest.csv")
    ap.add_argument("--meta", default="data/thumbs_meta.jsonl")
    ap.add_argument("--tiers", default="pos_review")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--out", default="data/review_sheet.html")
    ap.add_argument("--px", type=int, default=360)
    args = ap.parse_args()

    meta = {}
    for l in open(args.meta):
        if l.strip():
            m = json.loads(l)
            meta[m["file_id"]] = m
    base = os.path.dirname(args.meta)
    rows = [r for r in csv.DictReader(open(args.manifest))
            if r["tier"] in args.tiers.split(",") and r["file_id"] in meta]
    if args.sample:
        random.Random(0).shuffle(rows)
        rows = rows[: args.sample]
    tiles = []
    for r in rows:
        im = Image.open(os.path.join(base, meta[r["file_id"]]["path"]))
        im.thumbnail((args.px, args.px))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=80)
        tiles.append({"id": r["file_id"], "name": r["file_name"][:23], "tier": r["tier"],
                      "reason": r["reason"], "img": base64.b64encode(b.getvalue()).decode()})
    html = """<!doctype html><meta charset=utf-8><title>LN label review</title>
<style>body{font:13px system-ui;margin:16px;background:#fafafa}.g{display:flex;flex-wrap:wrap;gap:10px}
.t{width:%dpx;background:#fff;border:4px solid #ccc;padding:4px;cursor:pointer}.t img{width:100%%}
.t.ln{border-color:#2a9d4b}.t.non{border-color:#c0392b}.t.uns{border-color:#e6a700}
.bar{position:sticky;top:0;background:#fafafa;padding:8px 0}</style>
<div class=bar><b>Click: LN (green) → non-LN (red) → unsure (yellow) → unset.</b>
<button onclick=dl()>Download review.csv</button> <span id=c></span></div><div class=g id=g></div>
<script>const T=%s;const S=["","ln","non","uns"];const st={};
const g=document.getElementById('g');
T.forEach(t=>{const d=document.createElement('div');d.className='t';
d.innerHTML=`<img src="data:image/jpeg;base64,${t.img}"><div>${t.name} · ${t.tier}<br><small>${t.reason}</small></div>`;
d.onclick=()=>{st[t.id]=((st[t.id]||0)+1)%%4;d.className='t '+S[st[t.id]];cnt()};g.appendChild(d)});
function cnt(){document.getElementById('c').textContent=Object.values(st).filter(v=>v).length+' / '+T.length+' reviewed'}
function dl(){const L={1:'1',2:'0',3:'unsure'};let s='file_id,review_label\\n';
for(const[k,v]of Object.entries(st))if(v)s+=k+','+L[v]+'\\n';
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{type:'text/csv'}));
a.download='review.csv';a.click()}cnt()</script>""" % (args.px, json.dumps(tiles))
    with open(args.out, "w") as f:
        f.write(html)
    print(f"{len(tiles)} tiles -> {args.out}")


if __name__ == "__main__":
    main()
