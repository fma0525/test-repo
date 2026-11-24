# GX10 執行計畫

這份計畫給之後連上 GX10、要直接下指令跑的 session 使用。每一關都有通過條件，沒過就停下來回報，不往下跑。

## 事前準備（使用者）
- [ ] GX10 能連到 `api.gdc.cancer.gov`
- [ ] 裝好 Docker 和 NVIDIA Container Toolkit，並選定 NGC PyTorch（arm64）容器的 tag
- [ ] 磁碟可用空間 ≥ 150 GB（縮圖約 80–100 GB，加上 runs）
- [ ] 在 `test-repo/ln_triage` 執行 `claude remote-control`，讓雲端 session 可以接上
- [ ] 下載和訓練期間 GX10 不關機、不休眠

## A. 環境確認（約 15 分鐘）
`python3 check_env.py`
- 通過條件：`cuda: true`、`bf16: true`、`gdc_status: OK`，並且有顯示 GPU 名稱
- 沒過就換 NGC tag，再不行改用 venv 裝 aarch64 版的 PyTorch

## B. 小量測試（約 30–60 分鐘）
`LIMIT=300 EPOCHS=3 bash run_all.sh`
- 通過條件：整條流程跑完、loss 有下降、`model.onnx` 能推論
- 量測這些數字，用來調參數：
  - 下載速度（張/秒）
  - 訓練吞吐量（img/s）
  - GPU 使用率：如果被 dataloader 拖住，就調 `--workers` 或改成先把縮圖預處理好
  - 決定全量訓練的 `WORKERS` 和 `--bs`

## C. 全量抓縮圖（約 5–6 小時，背景執行，可以接續）
`nohup python3 extract_thumbs.py --workers 16 > data/extract.log 2>&1 &`
- 通過條件：失敗率 < 1%（看 `data/thumbs_errors.log`），失敗的重跑一次
- 被 GDC 限流就降 `--workers`

## D. 人工審核（和 E 同時進行）
- 從 `review_sheet.py` 產生 `data/review_sheet.html`，交給內部病理醫師
- 150 張待審片：106 張 SKCM、44 張 DLBC。DLBC 要不要算淋巴結，要先定案
- 另外抽 60 張 `pos_high` 做品質檢查：`--tiers pos_high --sample 60`
- 審核結果存成 `data/review.csv`，交回後重訓

## E. Baseline 訓練
三個架構都跑，seed 0，1024² 輸入，16 µm/px：
`for A in effb0 resnet18 mnv3; do python3 train.py --arch $A --out runs/base-$A; done`
- 用 validation 的 AUC 和 spec@sens0.98 選架構，test 只在最後看一次
- 陽性只有約 110 張，分數會不穩，選定架構後再跑：
  - `MODE=cv ARCH=<選定> bash run_cv.sh`：5-fold，用 case 切分，彙整各 fold 的測試結果
  - `MODE=seeds ARCH=<選定> bash run_cv.sh`：固定切分，跑 3 個初始化 seed
  - 兩者都會自動跑 `summarize_runs.py`（各 run 加總，對照 POC 門檻）和 `errors_sheet.py`
- 如果 B 階段發現 GPU 在等資料：先跑 `python3 prep_cache.py --mpp 16`，訓練時加 `--meta data/cache16_meta.jsonl`

## F. 檢查
- `skcm_only_auc`：混淆檢查。整體 AUC 高但這個低，代表模型學到的是癌別，不是淋巴結
- 逐張看 FN 和 FP 的縮圖：用 `python3 errors_sheet.py --run runs/<run>` 產生檢視頁，分類整理錯誤類型。發現標籤錯的，直接在頁面上改，存成 `review.csv`
- 標記筆痕跡：TCGA 有些片子有很粗的筆痕。檢查判錯的片子是不是跟筆痕有關，若是，就加筆痕偵測或遮罩
- CPU latency：GX10 是 ARM 的 Grace CPU，量出來不代表院內 x86 伺服器的表現，要另外在 x86 機器上跑 `export_infer.py bench --threads 4`

## G. POC 判定
| 指標 | 通過門檻 |
|---|---|
| test sensitivity | ≥ 0.98 |
| test specificity（同一個閾值） | ≥ 0.90 |
| skcm_only_auc | ≥ 0.90 |
| x86 CPU 單張 latency（4 threads） | < 1 s |

通過的話，下一步加入非黑色素瘤的淋巴結資料：先確認 CAMELYON 授權，再談院內資料合約。
沒通過的話，先看錯誤類型：是資料問題（標籤、數量），還是模型問題（解析度、架構）。

## 跑 GX10 之前程式還要補的
- [x] 錯誤分析頁：`errors_sheet.py`
- [x] 5-fold CV 和多 seed：`train.py --folds/--fold/--split-seed`、`run_cv.sh`、`summarize_runs.py`
- [x] 縮圖預處理快取：`prep_cache.py`
