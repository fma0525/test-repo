#!/usr/bin/env bash
# Unattended overnight POC on GX10. Runs inside a DETACHED docker container, so it
# keeps going after you log out / the Claude session disconnects. Resumable: rerun
# the same command and finished steps are skipped.
#
#   bash run_overnight.sh                 # start (prints container name + log path)
#   docker logs -f ln-poc                 # watch
#   cat runs/overnight-*/STATUS           # current step
#   docker stop ln-poc                    # abort (rerun later to resume)
#
# Order is chosen so a usable result exists as early as possible:
#   env check -> thumbnails (~11.9k, resumable) -> cache -> effb0 baseline ->
#   resnet18 / mnv3 baselines -> pick best on VAL -> 5-fold CV of best -> export.
set -euo pipefail
cd "$(dirname "$0")"
HERE=$(pwd)

if [ "${INSIDE:-0}" != 1 ]; then
  IMAGE=${IMAGE:-$(docker images nvcr.io/nvidia/pytorch --format '{{.Repository}}:{{.Tag}}' | sort -V | tail -1)}
  [ -n "$IMAGE" ] || { echo "No NGC PyTorch image found. docker pull nvcr.io/nvidia/pytorch:<tag>-py3 first, or set IMAGE=..."; exit 1; }
  docker rm -f ln-poc >/dev/null 2>&1 || true
  docker run -d --name ln-poc --gpus all --ipc=host --ulimit memlock=-1 \
    -v "$HERE":/work -w /work -e INSIDE=1 -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    -e WORKERS="${WORKERS:-24}" -e EPOCHS="${EPOCHS:-40}" -e FOLDS="${FOLDS:-5}" -e TAG="${TAG:-$(date +%Y%m%d)}" \
    "$IMAGE" bash -c "pip install -q -r requirements.txt && bash run_overnight.sh"
  echo "started container ln-poc from $IMAGE"
  echo "log: docker logs -f ln-poc   |   status: cat $HERE/runs/overnight-${TAG:-$(date +%Y%m%d)}/STATUS"
  exit 0
fi

# ------------------------------------------------------------------ inside container
TAG=${TAG:-$(date +%Y%m%d)}
OUT=runs/overnight-$TAG
mkdir -p "$OUT" data
# container runs as root: hand files back to the host user whenever we exit
trap 'chown -R "${HOST_UID:-0}:${HOST_GID:-0}" data runs 2>/dev/null || true' EXIT
exec > >(tee -a "$OUT/pipeline.log") 2>&1
step() { echo "$(date '+%F %T') $*" | tee "$OUT/STATUS"; }

step "0 env";        python3 check_env.py | tee "$OUT/env.json"
step "1 manifest";   [ -f data/manifest.csv ] || python3 build_manifest.py --out data/manifest.csv
step "2 thumbnails"; for i in 1 2; do python3 extract_thumbs.py --workers "$WORKERS"; done  # 2nd pass retries failures
step "3 cache";      [ -f data/cache16_meta.jsonl ] && [ "$(wc -l < data/cache16_meta.jsonl)" -ge "$(wc -l < data/thumbs_meta.jsonl)" ] \
                       || python3 prep_cache.py --mpp 16
step "3b review";    python3 review_sheet.py --tiers pos_review --out "$OUT/review_pos_review.html" || true

COMMON=(--meta data/cache16_meta.jsonl --mpp 16 --canvas 1024 --epochs "$EPOCHS")
for A in effb0 resnet18 mnv3; do
  R=runs/base-$TAG-$A
  if [ ! -f "$R/metrics.json" ]; then
    step "4 baseline $A"; mkdir -p "$R"
    python3 train.py --arch "$A" --out "$R" "${COMMON[@]}" 2>&1 | tee "$R/train.log"
    python3 errors_sheet.py --run "$R" --split val || true
  fi
done

# pick architecture on VALIDATION only (AUC + specificity at target sensitivity)
BEST=$(python3 - "$TAG" <<'EOF'
import json, sys, glob
best = max(glob.glob(f"runs/base-{sys.argv[1]}-*/metrics.json"),
           key=lambda p: (lambda v: (v["auc"] or 0) + v["specificity"])(json.load(open(p))["val"]))
print(json.load(open(best))["args"]["arch"])
EOF
)
echo "$BEST" > "$OUT/best_arch.txt"
step "5 cv $BEST";    MODE=cv ARCH="$BEST" FOLDS="$FOLDS" TAG="$TAG" bash run_cv.sh "${COMMON[@]}"
step "6 export";      python3 export_infer.py export --run "runs/base-$TAG-$BEST"
                      python3 export_infer.py bench --run "runs/base-$TAG-$BEST" --threads 4 | tee "$OUT/bench_arm_cpu.json"
ln -sfn "base-$TAG-$BEST" runs/latest

step "7 report"
python3 - "$TAG" "$BEST" "$FOLDS" > "$OUT/REPORT.md" <<'EOF'
import json, sys, glob, os
tag, best, folds = sys.argv[1:]
print(f"# LN triage POC overnight {tag}\n")
print("## Baselines (fixed split; choose on val, test shown for reference)\n")
print("| arch | val AUC | val spec@sens | test AUC | test sens | test spec | SKCM-only test AUC |\n|---|---|---|---|---|---|---|")
f = lambda v: "—" if v is None else f"{v:.3f}"
for p in sorted(glob.glob(f"runs/base-{tag}-*/metrics.json")):
    m = json.load(open(p)); v, t = m["val"], m["test"]
    print(f"| {m['args']['arch']} | {f(v['auc'])} | {f(v['specificity'])} | {f(t['auc'])} | {f(t['sensitivity'])} | {f(t['specificity'])} | {f(t['skcm_only_auc'])} |")
s = glob.glob(f"runs/summary_cv-{tag}-{best}-f*.json")
if s:
    S = json.load(open(s[0])); P = S["pooled"]
    print(f"\n## {folds}-fold CV of {best} (pooled out-of-fold test)\n")
    print(f"- AUC {f(P['auc_pooled'])} (95% CI {P['auc_pooled_ci95']})")
    print(f"- sensitivity {f(P['sensitivity'])}, specificity {f(P['specificity'])}  (FN {P['fn']}, FP {P['fp']})")
    print(f"- SKCM-only AUC {f(P['skcm_only_auc_pooled'])}")
    print(f"- POC gates: {json.dumps(S['gates'])}")
print("\nError pages: runs/errors_*.html ; review sheet: runs/overnight-%s/review_pos_review.html" % tag)
print("Note: CPU latency here is ARM (Grace); re-measure on the x86 hospital server spec.")
EOF
step "DONE  -> $OUT/REPORT.md"
