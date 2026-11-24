#!/usr/bin/env bash
# Robustness runs once an architecture is chosen (GX10_PLAN.md step E).
#   MODE=cv    ARCH=effb0 bash run_cv.sh   # 5-fold case-level CV, pooled out-of-fold test
#   MODE=seeds ARCH=effb0 bash run_cv.sh   # 3 init seeds on the fixed split
# Extra train.py flags pass through, e.g.  bash run_cv.sh --meta data/cache16_meta.jsonl
set -euo pipefail
cd "$(dirname "$0")"
MODE=${MODE:-cv}; ARCH=${ARCH:-effb0}; FOLDS=${FOLDS:-5}; SEEDS=${SEEDS:-"0 1 2"}
TAG=${TAG:-$(date +%Y%m%d)}
mkdir -p runs

if [ "$MODE" = cv ]; then
  for k in $(seq 0 $((FOLDS-1))); do
    out=runs/cv-$TAG-$ARCH-f$k
    [ -f "$out/metrics.json" ] && { echo "skip $out"; continue; }
    mkdir -p "$out"; python3 train.py --arch "$ARCH" --folds "$FOLDS" --fold "$k" --out "$out" "$@" 2>&1 | tee "$out/train.log"
  done
  pat="runs/cv-$TAG-$ARCH-f*"
else
  for s in $SEEDS; do
    out=runs/seed-$TAG-$ARCH-s$s
    [ -f "$out/metrics.json" ] && { echo "skip $out"; continue; }
    mkdir -p "$out"; python3 train.py --arch "$ARCH" --seed "$s" --out "$out" "$@" 2>&1 | tee "$out/train.log"
  done
  pat="runs/seed-$TAG-$ARCH-s*"
fi
python3 summarize_runs.py "$pat"
python3 errors_sheet.py --run "$pat" --split test
