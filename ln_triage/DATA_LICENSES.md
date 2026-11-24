# 資料與權重來源登記（商用審查用）

每個進入訓練的資料集、預訓練權重都要在這裡登記；模型版本的 `model.json` 會寫明用了哪些。

| 來源 | 狀態 | 授權 / 依據 | 用途 | 備註 |
|---|---|---|---|---|
| TCGA diagnostic slides（GDC open access） | **使用中** | GDC open access 層，無 DUA；NCI 稱 TCGA 資料屬 public domain | 訓練 / 驗證 | 需法務書面確認商用；查詢日期 2026-11-24，共 11,901 張 SVS |
| CAMELYON16 / 17 | **未使用** | 官網矛盾：Data 頁寫 CC0，Download 頁寫 CC BY-NC-ND 4.0 | — | 取得 Radboud UMC 書面確認 CC0 後才能加入 |
| TCIA 病理資料集 | 未使用 | 依資料集而定 | — | 只收 CC BY 4.0；CC BY-NC 排除 |
| ImageNet 預訓練權重 | **不使用** | ImageNet 條款限非商業研究，權重是否繼承未定 | — | 權重一律隨機初始化 |
| UNI / Virchow 等病理 foundation model | **不使用** | CC BY-NC-ND | — | — |
| 院內資料（北榮、長庚、癌醫…） | 未使用 | 需合約含商品化條款 + IRB | — | 北榮葉主任的模型、權重、2 萬張資料不得使用 |

## 軟體

PyTorch / torchvision（BSD）、ONNX Runtime（MIT）、tifffile（BSD）、imagecodecs（BSD）、scikit-learn（BSD）、Pillow（MIT-CMU）、requests（Apache-2.0）。
不使用 GPL / AGPL 套件。NGC 容器只用於 GX10 開發，出貨用的 docker image 另以授權寬鬆的 base image 建置。
