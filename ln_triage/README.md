# LN triage：玻片是否含淋巴結（雲象版 pre-inference 模型）

用低倍縮圖判斷一張 WSI 有沒有淋巴結組織，給 LNM 推論前的預篩選使用。
**推論只用 CPU**；訓練資料目前只用 **TCGA（GDC open access）**，權重**從頭訓練**（不用 ImageNet 或非商用的 foundation model），方便之後商用。

## 流程

| 步驟 | 腳本 | 產出 |
|---|---|---|
| 0 | `check_env.py` | 確認 GPU、bf16、GDC 連線、磁碟 |
| 1 | `build_manifest.py` | `data/manifest.csv`：11,901 張 TCGA 診斷片 + 弱標籤層級 |
| 2 | `extract_thumbs.py` | `data/thumbs/*.jpg`（8 µm/px）：用 HTTP Range 只抓最低倍層，每張約 6 MB，不下載整張 WSI |
| 3 | `review_sheet.py` | `data/review_sheet.html`：給病理醫師點選確認標籤，下載 `review.csv` 放到 `data/` |
| 4 | `train.py` | `runs/<run>/best.pt`、`metrics.json`、`predictions.csv`、`split.csv` |
| 5 | `export_infer.py` | `model.onnx`、`model.json`、CPU latency、單張推論 JSON |

一鍵跑完（可中斷、重跑會接續）：

```bash
LIMIT=300 bash run_all.sh      # 先跑 300 張的 smoke test
bash run_all.sh                # 全量
```

## 標籤層級（TCGA 的部位記在病例診斷上，不在玻片上，所以是弱標籤）

| tier | 定義 | 張數 | 預設用途 |
|---|---|---|---|
| `pos_high` | 轉移樣本（barcode 06）且主要診斷部位為淋巴結 | 110（全為 SKCM） | 訓練 |
| `pos_review` | 部位為淋巴結但樣本未標轉移（SKCM 106）＋ 淋巴瘤 DLBC 44 | 150 | 待審核 |
| `neg_high` | 主要診斷部位為非淋巴結器官（含 SKCM 皮膚/軟組織轉移＝同來源困難陰性） | 11,637 | 訓練 |
| `neg_low` | 部位未填、實體器官專案 | 4 | 訓練 |

**限制**：陽性目前只有黑色素瘤淋巴結轉移，跟肺癌、乳癌、胃癌的淋巴結清除片（多為正常淋巴結＋脂肪）外觀不同。TCGA POC 只能證明流程與可行性，臨床等級需要再加入其他來源的淋巴結片（見 `DATA_LICENSES.md`）。
`metrics.json` 裡的 `skcm_only_auc` 是混淆檢查：只在 SKCM 內比較（淋巴結轉移 vs 皮膚轉移/原發），如果整體 AUC 很高但這個很低，代表模型學到的是「黑色素瘤 vs 其他癌別」而不是淋巴結。

## 在 GX10 上執行

GX10（GB10 Grace Blackwell，ARM64）建議用 NVIDIA NGC 的 PyTorch 容器（arm64），自己 pip 裝 CUDA 版 PyTorch 在 aarch64 上容易踩雷：

```bash
git clone <this repo> && cd test-repo/ln_triage
docker run --gpus all --ipc=host -it --rm -v "$PWD":/work -w /work \
  nvcr.io/nvidia/pytorch:<支援 DGX Spark 的最新 tag>-py3 bash
pip install -r requirements.txt
python3 check_env.py           # 應看到 cuda: true、gpu 名稱、bf16: true、gdc_status: OK
LIMIT=300 bash run_all.sh       # smoke test
bash run_all.sh                 # 全量（背景跑：nohup bash run_all.sh &）
```

時間預估（實際以 log 為準）：縮圖下載在測試環境約 0.6 張/秒（10 併發），全量約 5–6 小時，主要看網路頻寬；訓練預設 40 epoch × 200 step × 32 張，1024² 輸入。

常用參數：`ARCH=resnet18|mnv3|effb0`、`EPOCHS`、`WORKERS`（下載併發）。訓練細節參數見 `python3 train.py -h`（`--mpp` 預設 16 µm/px、`--canvas` 1024、`--target-sens` 0.98）。

## 推論輸出（對齊 pre-inference 服務的介面）

```bash
python3 export_infer.py predict --run runs/latest --svs slide.svs
python3 export_infer.py predict --run runs/latest --image thumb.jpg --mpp 8
```

```json
{"model": "aetherai-ln-triage-effb0", "prediction": "LN", "prediction_LN": 1,
 "probability": 0.93, "threshold": 0.12, "latency_ms": 180, "status": "OK"}
```

閾值是在 validation 上選的，條件是 sensitivity ≥ 0.98：漏判淋巴結片會讓 LNM 不推論，代價比多跑一張高。
