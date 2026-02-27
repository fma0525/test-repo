# 故事星球 StoryPlanet 🪐

> AI 驅動的兒童有聲書 Web App — 給幾個關鍵字，為 3-6 歲孩子生成專屬故事

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-38bdf8?logo=tailwindcss)

---

## 功能

- **故事生成** — 選擇風格 + 輸入關鍵字，AI 自動生成故事文字、封面插圖、語音朗讀
- **故事收聽** — 書架式瀏覽，點擊即可播放故事、閱讀文字內容
- **三種風格** — 🌙 晚安溫柔風 ｜ ⚡ 冒險精彩風 ｜ 😄 趣味歡笑風
- **Mock 模式** — 不需要任何 API Key 就能體驗完整流程

## 快速開始

```bash
# 安裝依賴
cd story-planet
npm install

# 啟動開發伺服器（預設 Mock 模式，不需 API Key）
npm run dev
```

打開 [http://localhost:3000](http://localhost:3000) 即可使用。

## 截圖預覽

| 書架首頁 | 建立故事 | 播放器 |
|:---:|:---:|:---:|
| 瀏覽所有故事 | 選風格 + 關鍵字 | 封面 + 音訊 + 文字 |

## 專案結構

```
story-planet/
├── app/
│   ├── page.tsx                ← 書架首頁
│   ├── create/page.tsx         ← 建立故事頁
│   ├── story/[id]/page.tsx     ← 故事播放器頁
│   └── api/
│       ├── generate/route.ts   ← POST 觸發 AI 生成
│       ├── stories/route.ts    ← GET 故事列表
│       └── stories/[id]/       ← GET 單一故事
├── components/
│   ├── StoryCard.tsx           ← 故事卡片元件
│   ├── AudioPlayer.tsx         ← 音訊播放器元件
│   └── GeneratingStatus.tsx    ← 生成進度元件
├── lib/
│   ├── types.ts                ← TypeScript 型別定義
│   └── mock-data.ts            ← Mock 模式資料與邏輯
├── .env.local.example          ← 環境變數範例
└── package.json
```

## 環境變數

複製 `.env.local.example` 為 `.env.local` 並填入 API Key：

```bash
cp .env.local.example .env.local
```

| 變數 | 用途 | 必要性 |
|------|------|--------|
| `USE_MOCK` | `true` = 使用內建假資料（預設） | 選填 |
| `ANTHROPIC_API_KEY` | 故事文字生成（Claude API） | 真實模式必填 |
| `OPENAI_API_KEY` | 封面插圖生成（DALL-E 3） | 真實模式必填 |
| `ELEVENLABS_API_KEY` | 語音朗讀合成（ElevenLabs TTS） | 選填 |
| `SUPABASE_URL` | 資料庫（未來擴充） | 選填 |
| `SUPABASE_ANON_KEY` | 資料庫（未來擴充） | 選填 |

### Mock 模式 vs 真實模式

- **Mock 模式**（預設）：內建 3 個中文故事，建立故事時產生假資料，不需任何 API Key
- **真實模式**：設定 `USE_MOCK=false` 並填入 API Key 後，AI 即時生成故事

## AI 管線

```
使用者輸入關鍵字 + 風格
         │
         ▼
  Claude API → 故事文字 + 封面描述（JSON）
         │
    ┌────┴────┐
    ▼         ▼
 DALL-E 3   ElevenLabs
 封面插圖    語音朗讀
    └────┬────┘
         ▼
    完成！跳轉到播放器
```

## 技術棧

- **框架**：Next.js 15（App Router）
- **語言**：TypeScript
- **樣式**：Tailwind CSS 4
- **AI 文字**：Anthropic Claude API
- **AI 圖片**：OpenAI DALL-E 3
- **AI 語音**：ElevenLabs TTS
- **部署**：Vercel（建議）

## 部署到 Vercel

```bash
npm i -g vercel
vercel
```

在 Vercel Dashboard 設定環境變數後即可上線。

## 開發指令

```bash
npm run dev      # 啟動開發伺服器
npm run build    # 建置生產版本
npm run start    # 啟動生產伺服器
npm run lint     # ESLint 檢查
```

## License

MIT
