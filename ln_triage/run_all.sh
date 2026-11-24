#!/usr/bin/env bash
# One-shot pipeline for GX10 (or any Linux box with a GPU). Resumable: rerun to continue.
#   bash run_all.sh               # full TCGA run
#   LIMIT=300 bash run_all.sh     # quick smoke test on 300 slides
set -euo pipefail
cd "$(dirname "$0")"

LIMIT=${LIMIT:-0}
WORKERS=${WORKERS:-16}            # parallel downloads
ARCH=${ARCH:-effb0}
EPOCHS=${EPOCHS:-40}
RUN=${RUN:-runs/$(date +%Y%m%d-%H%M)-${ARCH}}
mkdir -p data "$RUN"
exec > >(tee -a "$RUN/pipeline.log") 2>&1

echo "== 0. environment";  python3 check_env.py
echo "== 1. manifest";     [ -f data/manifest.csv ] || python3 build_manifest.py --out data/manifest.csv
echo "== 2. thumbnails";   python3 extract_thumbs.py --workers "$WORKERS" --limit "$LIMIT"
echo "== 3. review sheet"; python3 review_sheet.py --tiers pos_review || true
echo "== 4. train";        python3 train.py --arch "$ARCH" --epochs "$EPOCHS" --out "$RUN"
echo "== 5. export+bench"; python3 export_infer.py export --run "$RUN"
                           python3 export_infer.py bench  --run "$RUN" --threads 4
ln -sfn "$(basename "$RUN")" runs/latest
echo "== done: $RUN/metrics.json"
