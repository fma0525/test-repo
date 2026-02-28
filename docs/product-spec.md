# iOS 兒童有聲書 APP — 產品規劃設計方案（修訂版）

## Context

使用者希望打造一個面向 3-6 歲學齡前兒童的 iOS 有聲書 APP。

**核心概念 — 「單頁互動有聲書」：**
- 不是傳統多頁翻頁繪本，而是類似**有聲書專輯**的形式
- AI 只生成**一張封面圖**，封面即是故事的全部視覺呈現
- 封面上的每個角色都是**可點擊的互動按鈕**
- 故事以**語音朗讀**推進，畫面不翻頁、不變化
- 當某角色有台詞時，該角色在封面上**亮起/高亮**
- 家長可錄製自己的聲音替換 AI 朗讀，或加在故事開頭

商業模式：免費增值（前 5 本免費，超過需訂閱）

**v3 新增設計決策：**
- **畫風固定化**：不再每本書選畫風，而是在 App 設定/首次使用時選定 2-3 種預設畫風，後續所有故事都使用該畫風，簡化 AI 生成流程
- **小朋友專屬化身（彩蛋角色）**：家長拍一張小朋友照片，AI 依據小朋友的造型（非臉部）生成一個風格化角色。此角色不參與劇情，但會以「彩蛋」形式出現在每一本故事的封面中，讓小朋友感覺自己就在故事裡

---

## 一、產品願景與定位

### 產品名稱建議
**「故事星球」(StoryPlanet)** — 每個孩子都能擁有自己的故事宇宙

### 核心價值主張
> 「給我幾個關鍵字，AI 幫你變出一個專屬有聲故事」

### 產品形態類比
| 傳統繪本 App | 我們的產品 |
|-------------|-----------|
| 多頁翻頁 | 單頁封面，語音驅動故事推進 |
| 每頁一張插圖 | 一張封面圖，角色各自可互動 |
| 視覺主導 | 聽覺主導，視覺輔助互動 |
| 像看書 | 像聽廣播劇 + 看互動海報 |

更精確的比喻：**兒童版 Podcast + 互動封面藝術**

### 目標用戶
| 角色 | 描述 | 核心需求 |
|------|------|----------|
| 主要使用者 | 3-6 歲學齡前兒童 | 聽故事、點角色互動 |
| 決策者/付費者 | 家長（25-40 歲） | 優質內容、安全環境、教育價值 |
| 共同使用者 | 家長+孩子 | 親子共聽、錄音互動 |

### 競品分析
| 競品 | 優勢 | 我們的差異化 |
|------|------|-------------|
| Moonlite | 投影+故事 | AI 生成無限故事、互動封面 |
| Epic! | 海量繪本庫 | 個人化 AI 即時創作 |
| Yoto Player | 音訊卡片播放器 | 軟體形態、AI 生成、可視化互動 |
| 小火箭/KaDa 故事 | 中文有聲書 | AI 即時生成 + 家長錄音 + 互動封面 |

---

## 二、功能規格（Feature Specification）

### 2.1 核心功能模組

#### 模組 A：AI 故事生成引擎
```
使用者輸入 → AI 處理 → 有聲書產出

[關鍵字/主題] → [故事文本生成] → [封面圖生成] → [AI 語音合成] → [互動元素偵測] → [完成]
```

**詳細流程：**

1. **故事創建入口**
   - 家長/孩子選擇「創建新故事」
   - **選擇故事風格**（每次建立時選，影響敘事+語音語調）：
     - 🌙 **晚安溫柔風** — 輕柔節奏、助眠語調、溫暖結局
     - ⚡ **冒險精彩風** — 緊湊情節、激昂語氣、充滿驚喜轉折
     - 😄 **趣味歡笑風** — 搞笑對白、誇張語氣、輕鬆歡樂
   - 輸入 1-5 個關鍵字（文字輸入 or 語音輸入）
   - 可選：選擇主角名字
   - **畫風 & 聲線已在設定中預選好，不需每次選擇**

2. **AI 文本生成**
   - 基於關鍵字生成一個完整的有聲故事腳本
   - 故事長度：約 2-5 分鐘朗讀時間（300-800 字）
   - 包含多個角色，每個角色有明確台詞
   - 故事結構：旁白 + 角色對話交替進行
   - 語言風格：簡單句型、重複韻律、生動擬聲詞
   - 支援語言：繁體中文（初期）

3. **AI 封面圖生成（單張）**
   - 生成一張包含所有主要角色的場景圖
   - 角色必須清晰可辨、大小適中（可點擊）
   - **使用帳號中已設定好的畫風**（不再每次選擇）
   - 角色佈局需考慮互動點擊區域（不重疊、不過小）
   - 標題文字疊加於封面上方
   - **若用戶已建立「小朋友化身」，需將化身角色融入封面場景中**

4. **AI 語音合成（受故事風格影響）**
   - 旁白語音：選定的聲線朗讀
   - **語音語調隨故事風格變化**：
     - 🌙 晚安溫柔風 → 語速慢、語調低柔、停頓較多、像哄睡
     - ⚡ 冒險精彩風 → 語速中快、語調起伏大、緊張處加速
     - 😄 趣味歡笑風 → 語調誇張活潑、角色聲音對比大、多擬聲詞
   - 生成時間戳：標記每個角色的說話時間點
   - 支援聲線選擇（溫柔媽媽/活潑姐姐/穩重爸爸，設定中選定）
   - 語速可調

5. **互動元素偵測**
   - AI 分析封面圖，辨識各角色位置
   - 為每個角色生成 hitbox（點擊區域）
   - 配對角色與故事中的台詞時間戳
   - 為每個角色指定點擊音效

#### 模組 B：有聲書播放器（核心體驗）

**單頁互動設計：**
```
┌──────────────────────────────────┐
│                                  │
│  ┌────────────────────────────┐  │
│  │                            │  │
│  │      🌟 故事封面圖 🌟       │  │
│  │                            │  │
│  │   [角色A]    [角色B]        │  │
│  │      ✨         💬          │  │  ← 說話的角色亮起
│  │           [角色C]           │  │
│  │              [物件D]        │  │  ← 物件可點擊觸發音效
│  │                            │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ "小熊走進了森林，遇到了..."  │  │  ← 當前朗讀文字（可選顯示）
│  └────────────────────────────┘  │
│                                  │
│       ▶ advancement bar ━━━━━━  │  ← 播放進度條
│                                  │
│   ⏮   ▶/⏸   ⏭               │  ← 播放控制
│                                  │
│   [🔊 聲音] [🎙 錄音] [⚙ 設定]  │
└──────────────────────────────────┘
```

**播放器功能：**
- **語音朗讀**：連續播放整個故事的語音
- **角色高亮**：當某角色說話時，該角色在封面上發光/放大/跳動
- **文字同步（可選）**：底部顯示當前朗讀的文字段落，karaoke 式高亮
- **點擊互動**：隨時可點擊封面上的角色，觸發角色專屬音效/動畫
- **播放控制**：播放/暫停、快進/快退（以段落為單位）
- **夜間模式**：降低亮度、暖色調背光
- **背景播放**：可鎖屏繼續聽（如同 Podcast）
- **自動重播**：故事結束後可自動重播

**角色高亮效果設計：**
```
正常狀態     →  說話狀態
┌─────┐       ┌─────┐
│ 角色 │  →   │✨角色✨│  發光邊框
│  A   │       │  A   │  微微放大 (1.1x)
└─────┘       └─────┘  輕微上下浮動動畫

用戶點擊     →  回饋狀態
┌─────┐       ┌─────┐
│ 角色 │  →   │ 角色 │  彈跳動畫
│  B   │       │ B↕  │  播放角色專屬音效
└─────┘       └─────┘  如：「嗨！我是小兔子！」
```

#### 模組 C：互動元素系統

**封面互動設計原則：**
- 每個角色都是一個可點擊的互動物件
- 點擊角色 → 播放該角色的招牌音效或自我介紹
- 點擊場景物件（如太陽、花朵）→ 播放環境音效
- 故事播放中點擊不會中斷故事朗讀（音效疊加播放）
- 隱藏彩蛋：封面中藏 1-2 個小物件，點擊可發現驚喜

**互動元素資料結構：**
```json
{
  "story_id": "story_abc123",
  "cover_image_url": "https://cdn.example.com/covers/abc123.png",
  "interactive_elements": [
    {
      "id": "char_bear",
      "label": "小熊",
      "type": "character",
      "hitbox": {"x": 0.15, "y": 0.30, "width": 0.25, "height": 0.35},
      "tap_sound": "bear_hello.mp3",
      "tap_animation": "bounce",
      "speaking_glow_color": "#FFD700",
      "dialogue_timestamps": [
        {"start": 12.5, "end": 18.2},
        {"start": 45.0, "end": 52.3}
      ]
    },
    {
      "id": "char_rabbit",
      "label": "小兔子",
      "type": "character",
      "hitbox": {"x": 0.55, "y": 0.25, "width": 0.20, "height": 0.30},
      "tap_sound": "rabbit_hello.mp3",
      "tap_animation": "wiggle",
      "speaking_glow_color": "#FF69B4",
      "dialogue_timestamps": [
        {"start": 20.0, "end": 28.5},
        {"start": 55.0, "end": 61.0}
      ]
    },
    {
      "id": "obj_sun",
      "label": "太陽",
      "type": "scene_object",
      "hitbox": {"x": 0.75, "y": 0.05, "width": 0.15, "height": 0.15},
      "tap_sound": "sunshine_sparkle.mp3",
      "tap_animation": "spin",
      "is_hidden": false
    },
    {
      "id": "hidden_star",
      "label": "隱藏小星星",
      "type": "hidden_item",
      "hitbox": {"x": 0.85, "y": 0.80, "width": 0.08, "height": 0.08},
      "tap_sound": "magic_sparkle.mp3",
      "tap_animation": "fly_away",
      "is_hidden": true,
      "discovered_reward": "你找到了隱藏的小星星！"
    }
  ]
}
```

> 注意：hitbox 使用 0-1 的比例座標，以適應不同螢幕尺寸

#### 模組 D：畫風固定化系統（v3 新增）

**設計理念：**
畫風不再是每次創作時選擇，而是在「帳號設定」或「首次使用」時選定。
所有後續生成的故事封面都使用同一畫風，確保：
- AI 生成品質更穩定（針對特定風格優化 prompt）
- App 整體視覺一致、書架看起來協調
- 簡化創作流程（少一個步驟，孩子更快聽到故事）

**支援的畫風（初期 2-3 種）：**
| 畫風 | 適合的圖片生成模型 | 說明 |
|------|-------------------|------|
| **柔和卡通風** | DALL-E 3 / Flux | 圓潤線條、明亮色彩、最容易生成角色 |
| **水彩繪本風** | Midjourney / Flux | 柔美、有手繪感、適合溫馨故事 |
| **蠟筆塗鴉風** | Flux + style prompt | 童趣感強、像孩子自己畫的 |
| **韓系水彩手繪風** | Midjourney / Flux | 韓式繪本質感、水彩+不透明水彩、暖色大地色調、細膩自然場景、擬人化小動物、微型世界視角、手繪紙質感 |

> 選定後可在家長設定中切換，切換不影響已生成的故事

**畫風設定時機：**
- 首次使用引導流程中（Onboarding Step 2）
- 家長區設定頁面可隨時修改
- 免費用戶可選 2 種，訂閱用戶可選全部

**技術實現：**
- 每種畫風對應一組預調好的 image prompt 模板
- 封面生成時自動套用當前畫風的 prompt prefix
- 如：`"[watercolor children's book illustration style] A scene with..."`

#### 模組 E：小朋友專屬化身（v3 新增 — 重要差異化功能）

**功能概述：**
家長拍攝一張小朋友的照片，AI 根據小朋友的**造型特徵**（髮型、服裝顏色、配件等）生成一個風格化的卡通角色。此角色作為「彩蛋」出現在每一個故事的封面中。

**關鍵設計原則：**
1. **不使用小朋友真實臉部** — 隱私保護 + 避免恐怖谷效應
2. 以小朋友的**造型輪廓**為基礎（髮型、髮色、衣服顏色、眼鏡等配件）
3. 生成後的角色是**固定的**，不會每次重新生成
4. 角色以小尺寸、不顯眼的方式出現在封面中（彩蛋感）
5. 孩子可以在封面上「找到自己」— 增加參與感和驚喜感

**化身生成流程：**
```
[拍照/選擇照片]
      │
      ▼
[AI 分析造型特徵]
  - 髮型（短髮/長髮/馬尾/捲髮...）
  - 髮色
  - 服裝主色
  - 配件（眼鏡、帽子、髮箍...）
      │
      ▼
[生成風格化角色]
  - 使用當前畫風渲染
  - 生成 3 個候選（用戶選一個）
  - 角色為固定姿勢的小圖（如：站立/坐著/招手）
      │
      ▼
[確認儲存]
  - 儲存為「我的化身」
  - 之後每個故事封面都自動融入此角色
```

**封面中的化身出現方式：**
```
┌────────────────────────────────┐
│                                │
│  [故事角色A]    [故事角色B]     │
│                                │
│       [場景元素]                │
│                                │
│                   ┌──────┐     │
│                   │小朋友│     │  ← 化身以小尺寸出現
│                   │ 化身 │     │    在角落或場景中
│  🌲🌲            └──────┘     │    不參與劇情
│                                │    但可以點擊互動！
└────────────────────────────────┘

化身互動：點擊化身 → 播放「嗨！我在這裡！」音效 + 揮手動畫
```

**化身融入封面的技術方案：**

方案 A（推薦）：**圖層合成法**
- 化身角色預先生成為 PNG（透明背景）
- 封面圖生成時不包含化身
- 後端將化身 PNG 合成到封面的隨機位置
- 優點：化身品質穩定、位置可控、不影響封面生成品質
- 缺點：可能看起來稍微「貼上去」的感覺

方案 B：**Prompt 注入法**
- 在封面生成的 prompt 中加入化身描述
- 如：`"...and a small [cartoon child with short black hair and red shirt] peeking from behind a tree"`
- 優點：化身與場景更自然融合
- 缺點：角色一致性難保證，可能每次長得不一樣

**建議策略：MVP 用方案 A（穩定），後期可嘗試方案 B（自然）**

**化身資料模型：**
```swift
@Model
class ChildAvatar {
    var id: UUID
    var profileId: UUID                 // 關聯的孩子檔案
    var sourcePhotoLocalPath: String?   // 原始照片（僅本地、不上傳）
    var avatarImageURL: String          // 生成的化身圖 URL
    var avatarLocalPath: String?        // 本地快取

    // AI 提取的造型特徵
    var hairStyle: String               // 髮型描述
    var hairColor: String               // 髮色
    var outfitColor: String             // 服裝主色
    var accessories: [String]           // 配件列表
    var characterPrompt: String         // 用於圖片生成的角色描述 prompt

    var createdAt: Date
    var isActive: Bool                  // 是否啟用
}
```

**隱私注意事項：**
- 原始照片**不上傳到伺服器**
- AI 造型分析在設備端完成（或僅上傳到臨時分析後立即刪除）
- 僅儲存提取的文字特徵描述和生成的卡通角色圖
- 符合 COPPA / Apple 兒童 App 隱私要求

#### 模組 F：家長錄音功能

**錄音模式：**
1. **完整錄音替換**：家長錄製整個故事的朗讀，完全替換 AI 語音
2. **開頭錄音**：錄製一段開場白加在故事前面
   - 如：「寶貝，這是媽媽為你說的故事，今天我們來聽小熊的冒險...」
3. **段落錄音**：為特定段落（旁白或角色台詞）錄音替換

**錄音流程：**
```
選擇故事 → 進入錄音模式 → 選擇錄音類型
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        [完整錄音]      [開頭錄音]      [段落錄音]
              │               │               │
              ▼               ▼               ▼
        顯示全文提詞      自由發揮       顯示段落提詞
              │               │               │
              ▼               ▼               ▼
        [錄音中...] ──→ [預覽播放] ──→ [確認儲存]
                          │
                          ▼
                      [重錄?]
```

**技術要求：**
- 錄音格式：AAC, 44.1kHz
- 基本環境噪音消除
- 錄音品質指示器（音量 meter + 波形顯示）
- 錄音檔本地儲存 + iCloud 同步
- 錄音長度限制：開頭錄音最長 30 秒，完整錄音依故事長度

#### 模組 E：書架（故事庫）

**書架設計 — 類似音樂專輯牆：**
```
┌──────────────────────────────────┐
│  故事星球                         │
│                                  │
│  最近收聽                         │
│  ┌─────────────────────────────┐ │
│  │ [封面A]   [封面B]   [封面C]  │ │  ← 橫向滾動
│  │  森林     太空     海洋      │ │
│  │  冒險     探索     故事      │ │
│  └─────────────────────────────┘ │
│                                  │
│  我的故事 (3/5 免費)              │
│  ┌──────┐ ┌──────┐ ┌──────┐    │
│  │ 封面  │ │ 封面  │ │ 封面  │    │
│  │  1   │ │  2   │ │  3   │    │
│  │ 2:30 │ │ 3:15 │ │ 4:02 │    │  ← 顯示故事長度
│  └──────┘ └──────┘ └──────┘    │
│  ┌──────┐ ┌──────┐              │
│  │  +   │ │ 🔒   │              │
│  │ 新增  │ │ 訂閱  │              │
│  │ 故事  │ │ 解鎖  │              │
│  └──────┘ └──────┘              │
│                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  [🏠首頁]  [📚書架]  [✨創作]  [👤] │
└──────────────────────────────────┘
```

**書架功能：**
- 封面網格展示（2-3 欄）
- 長按封面顯示選單（刪除、重新生成語音、分享）
- 顯示每個故事的時長
- 排序方式：最近收聽 / 建立時間 / 收藏
- 免費額度顯示（3/5 免費）
- 搜尋/篩選功能

---

### 2.2 家長控制與安全

#### 兒童安全合規（COPPA / 台灣個資法 / Apple Kids Category）
- **家長閘門（Parent Gate）**：進入設定、付費、刪除故事需驗證
  - 驗證方式：數學計算題（如「32 + 15 = ?」）
- **無外部連結**：App 內不含任何外部網頁連結
- **無社交功能**：不含聊天、分享至社群（初期）
- **數據最小化**：僅收集必要數據
- **AI 內容安全過濾**：所有 AI 生成內容（文字+圖片）經多層過濾
- **無推播通知**（兒童 App 限制）

#### 家長面板功能
- 收聽時間設定（每日時長限制 + 就寢時間）
- 收聽歷史記錄（哪些故事、聽了多久）
- 訂閱管理
- 故事主題偏好設定（排除不想要的主題）
- 內容審核（預覽 AI 生成的故事後再對孩子開放）

---

### 2.3 商業模式詳細設計

#### 免費增值（Freemium）機制
| 等級 | 內容 | 價格 |
|------|------|------|
| 免費方案 | 可生成/保存 5 個故事、基本畫風 2 種、AI 聲線 1 種 | 免費 |
| 月訂閱 | 無限生成、全部畫風、全部聲線、家長錄音、離線收聽 | NT$149/月 |
| 年訂閱 | 同月訂閱 + 優先體驗新功能 | NT$990/年（約 67 折） |
| 家庭方案 | 最多 4 個孩子帳號 + 家長管理面板 | NT$1,490/年 |

#### 付費轉換策略
- 免費用戶用完 5 個故事後：「你的故事星球已經有 5 個故事了！訂閱可以創作無限故事」
- 每週推送「本週精選關鍵字」靈感，吸引創作
- 新畫風/聲線上線時提供 1 次免費試用
- 訂閱頁面展示高級畫風的封面對比

---

## 三、技術架構設計

### 3.1 系統架構總覽

```
┌──────────────────────────────────────────────────┐
│                 iOS App (SwiftUI)                 │
│  ┌───────────┐ ┌────────────┐ ┌────────────────┐ │
│  │ 書架/首頁  │ │ 有聲書播放器│ │ 故事創作流程    │ │
│  └───────────┘ └────────────┘ └────────────────┘ │
│  ┌───────────┐ ┌────────────┐ ┌────────────────┐ │
│  │ 錄音模組   │ │ 家長控制    │ │ 訂閱/付費管理   │ │
│  └───────────┘ └────────────┘ └────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │       本地資料層 (SwiftData + FileManager)     │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────┘
                         │ HTTPS / REST API
                         ▼
┌──────────────────────────────────────────────────┐
│               Backend (API Server)                │
│          Python (FastAPI) / Node.js               │
├──────────────────────────────────────────────────┤
│  ┌───────────┐ ┌────────────┐ ┌────────────────┐ │
│  │ 用戶/認證  │ │ 故事生成    │ │ 訂閱驗證       │ │
│  │ 服務      │ │ 編排服務    │ │ 服務           │ │
│  └───────────┘ └────────────┘ └────────────────┘ │
│  ┌───────────┐ ┌────────────────────────────────┐ │
│  │ 內容安全   │ │         物件儲存服務             │ │
│  │ 過濾服務   │ │   (封面圖、音訊檔、錄音檔)       │ │
│  └───────────┘ └────────────────────────────────┘ │
└────────────────────────┬─────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
  ┌──────────────┐ ┌───────────┐ ┌────────────┐
  │ AI 文本生成   │ │ AI 圖片   │ │ AI 語音    │
  │ Claude API   │ │ 生成       │ │ 合成       │
  │              │ │ DALL-E 3  │ │ ElevenLabs │
  │ - 故事腳本   │ │ / Flux    │ │ / Azure    │
  │ - 角色定義   │ │           │ │ TTS        │
  │ - 互動描述   │ │ - 封面圖  │ │            │
  └──────────────┘ └───────────┘ │ - 旁白     │
                                 │ - 角色台詞  │
                                 │ - 時間戳    │
                                 └────────────┘
```

### 3.2 技術選型

| 層級 | 技術選擇 | 理由 |
|------|----------|------|
| **iOS 前端** | SwiftUI + Swift 6 | Apple 官方推薦、動畫生態豐富 |
| **最低版本** | iOS 17.0+ | SwiftData + 最新動畫 API |
| **架構模式** | MVVM + Clean Architecture | 模組化、可測試 |
| **本地儲存** | SwiftData | 故事/設定資料 |
| **檔案快取** | FileManager + URLCache | 封面圖/音訊本地快取 |
| **音訊播放** | AVFoundation (AVAudioPlayer) | 支援背景播放、音訊疊加 |
| **音訊錄製** | AVFoundation (AVAudioRecorder) | 原生錄音 API |
| **動畫引擎** | SwiftUI Animation + Lottie | 角色高亮/點擊動畫 |
| **網路層** | URLSession + async/await | 原生 Swift Concurrency |
| **後端** | Python (FastAPI) | AI 整合生態佳、async 支援 |
| **資料庫** | PostgreSQL + Redis | 結構化資料 + 快取/佇列 |
| **物件儲存** | AWS S3 / CloudFlare R2 | 封面圖、音訊檔儲存 |
| **AI 文本** | Claude API (Anthropic) | 安全性高、結構化輸出佳 |
| **AI 圖像** | DALL-E 3 / Flux | 風格穩定、角色清晰 |
| **AI 語音** | ElevenLabs / Azure TTS | 自然語調、中文支援佳 |
| **付費系統** | StoreKit 2 | Apple 官方訂閱管理 |
| **CI/CD** | Xcode Cloud / Fastlane | 自動化建構部署 |

### 3.3 iOS App 模組架構

```
StoryPlanet/
├── App/
│   ├── StoryPlanetApp.swift            # App 入口
│   ├── AppCoordinator.swift            # 導航協調器
│   └── DependencyContainer.swift       # 依賴注入
│
├── Features/
│   ├── Onboarding/                     # 首次使用引導
│   │   ├── Views/
│   │   │   ├── WelcomeView.swift
│   │   │   ├── ChildProfileSetupView.swift
│   │   │   └── TutorialView.swift
│   │   └── ViewModels/
│   │
│   ├── Bookshelf/                      # 書架/故事庫
│   │   ├── Views/
│   │   │   ├── BookshelfView.swift
│   │   │   └── StoryCoverCardView.swift
│   │   └── ViewModels/
│   │       └── BookshelfViewModel.swift
│   │
│   ├── StoryCreation/                  # 故事創作
│   │   ├── Views/
│   │   │   ├── KeywordInputView.swift
│   │   │   ├── ConfirmCreateView.swift    # 確認創作（顯示已選畫風/聲線）
│   │   │   └── GeneratingView.swift       # 生成等待動畫
│   │   └── ViewModels/
│   │       └── StoryCreationViewModel.swift
│   │
│   ├── Avatar/                            # 小朋友化身（v3 新增）
│   │   ├── Views/
│   │   │   ├── AvatarCaptureView.swift    # 拍照/選照片
│   │   │   ├── AvatarPreviewView.swift    # 預覽 3 個候選化身
│   │   │   └── AvatarSettingsView.swift   # 化身管理（重新生成/刪除）
│   │   └── ViewModels/
│   │       └── AvatarViewModel.swift
│   │
│   ├── Player/                         # 有聲書播放器（核心）
│   │   ├── Views/
│   │   │   ├── PlayerView.swift              # 播放器主頁面
│   │   │   ├── InteractiveCoverView.swift    # 互動封面圖
│   │   │   ├── CharacterOverlayView.swift    # 角色高亮覆蓋層
│   │   │   └── PlaybackControlsView.swift    # 播放控制列
│   │   ├── ViewModels/
│   │   │   └── PlayerViewModel.swift
│   │   └── Engine/
│   │       ├── AudioPlaybackEngine.swift     # 音訊播放引擎
│   │       ├── CharacterSyncEngine.swift     # 角色高亮同步引擎
│   │       └── InteractionHandler.swift      # 點擊互動處理
│   │
│   ├── Recording/                      # 家長錄音
│   │   ├── Views/
│   │   │   ├── RecordingModeView.swift
│   │   │   ├── RecordingSessionView.swift
│   │   │   └── RecordingPreviewView.swift
│   │   └── ViewModels/
│   │       └── RecordingViewModel.swift
│   │
│   ├── ParentZone/                     # 家長控制區
│   │   ├── Views/
│   │   │   ├── ParentGateView.swift
│   │   │   ├── ParentDashboardView.swift
│   │   │   ├── ListeningStatsView.swift
│   │   │   └── ContentReviewView.swift
│   │   └── ViewModels/
│   │
│   └── Subscription/                   # 訂閱管理
│       ├── StoreKitManager.swift
│       └── SubscriptionView.swift
│
├── Core/
│   ├── Models/
│   │   ├── Story.swift
│   │   ├── Character.swift
│   │   ├── InteractiveElement.swift
│   │   ├── DialogueSegment.swift
│   │   ├── Recording.swift
│   │   └── ChildProfile.swift
│   │
│   ├── Services/
│   │   ├── AI/
│   │   │   ├── StoryGenerationService.swift
│   │   │   ├── CoverImageService.swift
│   │   │   └── VoiceSynthesisService.swift
│   │   ├── Audio/
│   │   │   ├── AudioPlayer.swift
│   │   │   ├── AudioRecorder.swift
│   │   │   └── SoundEffectPlayer.swift    # 互動音效（獨立播放）
│   │   ├── Storage/
│   │   │   ├── LocalCacheManager.swift
│   │   │   └── CloudSyncManager.swift
│   │   └── Safety/
│   │       ├── ContentFilterService.swift
│   │       └── ParentGateService.swift
│   │
│   ├── Network/
│   │   ├── APIClient.swift
│   │   └── Endpoints.swift
│   │
│   └── Utilities/
│       ├── Constants.swift
│       └── Extensions/
│
├── Resources/
│   ├── Assets.xcassets
│   ├── SoundEffects/                   # 互動音效素材
│   ├── Animations/                     # Lottie 動畫
│   └── Localizable.xcstrings
│
└── Tests/
    ├── UnitTests/
    └── UITests/
```

---

## 四、資料模型設計

### 4.1 核心資料模型

```swift
// MARK: - Story（有聲書主體）
@Model
class Story {
    @Attribute(.unique) var id: UUID
    var title: String                       // AI 生成的故事標題
    var keywords: [String]                  // 用戶輸入的關鍵字
    var storyStyle: StoryStyle              // 故事風格
    var artStyle: ArtStyle                  // 畫風
    var coverImageURL: String               // 封面圖 URL（唯一的一張圖）
    var coverImageLocalPath: String?        // 本地快取路徑

    // 故事內容
    var fullText: String                    // 完整故事文本
    var segments: [StorySegment]            // 故事段落（旁白+台詞）
    var characters: [StoryCharacter]        // 角色列表
    var interactiveElements: [InteractiveElement] // 封面上的互動元素

    // 音訊
    var aiAudioURL: String                  // AI 合成的完整語音 URL
    var aiAudioLocalPath: String?           // 本地快取路徑
    var duration: TimeInterval              // 故事總長度（秒）
    var voiceType: VoiceType                // AI 聲線

    // 家長錄音
    var recordings: [Recording]             // 家長錄音列表

    // 狀態
    var isGenerated: Bool                   // 是否生成完成
    var isFavorite: Bool
    var createdAt: Date
    var lastPlayedAt: Date?
    var playCount: Int                      // 收聽次數
    var ownerProfileId: UUID
}

// MARK: - StorySegment（故事段落 — 旁白或角色台詞）
struct StorySegment: Codable, Identifiable {
    var id: UUID
    var type: SegmentType                   // narrator（旁白）或 dialogue（台詞）
    var characterId: UUID?                  // 如果是台詞，對應哪個角色
    var text: String                        // 段落文字
    var startTime: TimeInterval             // 在音訊中的開始時間
    var endTime: TimeInterval               // 結束時間
}

enum SegmentType: String, Codable {
    case narrator       // 旁白
    case dialogue       // 角色台詞
}

// MARK: - StoryCharacter（故事角色）
struct StoryCharacter: Codable, Identifiable {
    var id: UUID
    var name: String                        // 角色名字（如「小熊」）
    var description: String                 // 角色簡述
    var personalityTrait: String            // 性格特點（用於語音語氣調整）
    var introSound: String                  // 點擊時的自我介紹音效 URL
    var glowColor: String                   // 說話時的高亮顏色（hex）
}

// MARK: - InteractiveElement（封面上的互動元素）
struct InteractiveElement: Codable, Identifiable {
    var id: UUID
    var label: String                       // 元素名稱
    var type: InteractiveElementType
    var characterId: UUID?                  // 關聯角色（如果是角色類型）

    // 位置（比例座標 0-1）
    var hitboxX: Double
    var hitboxY: Double
    var hitboxWidth: Double
    var hitboxHeight: Double

    // 互動效果
    var tapSoundURL: String                 // 點擊音效
    var tapAnimation: AnimationType         // 點擊動畫
    var speakingGlowColor: String?          // 說話高亮色（僅角色）

    // 隱藏彩蛋
    var isHidden: Bool
    var isDiscovered: Bool
    var discoveryReward: String?            // 發現彩蛋的文字獎勵
}

enum InteractiveElementType: String, Codable {
    case character      // 角色
    case sceneObject    // 場景物件
    case hiddenItem     // 隱藏彩蛋
}

enum AnimationType: String, Codable {
    case bounce         // 彈跳
    case wiggle         // 搖擺
    case spin           // 旋轉
    case glow           // 發光
    case flyAway        // 飛走
    case grow           // 放大
}

// MARK: - Recording（家長錄音）
@Model
class Recording {
    var id: UUID
    var storyId: UUID
    var type: RecordingType                 // 完整替換 / 開頭 / 段落
    var segmentId: UUID?                    // 如果是段落錄音，對應哪個段落
    var audioFileURL: String
    var audioLocalPath: String?
    var duration: TimeInterval
    var recorderName: String                // "爸爸" / "媽媽" / 自定義
    var recordedAt: Date
    var isActive: Bool                      // 是否啟用（用戶可切換 AI/錄音）
}

enum RecordingType: String, Codable {
    case full           // 完整替換 AI 語音
    case intro          // 故事開頭加入
    case segment        // 替換特定段落
}

// MARK: - ChildProfile（孩子檔案）
@Model
class ChildProfile {
    var id: UUID
    var name: String
    var avatarName: String                  // 預設頭像（App 內建圖示）
    var birthDate: Date?
    var preferredArtStyle: ArtStyle         // 選定的畫風（固定使用）
    var preferredVoiceType: VoiceType       // 選定的聲線（固定使用）
    var childAvatar: ChildAvatar?           // 小朋友專屬化身（可選）
    var storiesCreated: Int
    var totalListeningTime: TimeInterval
    var dailyLimitMinutes: Int?
    var bedtime: Date?
}

// MARK: - ChildAvatar（小朋友專屬化身 — v3 新增）
@Model
class ChildAvatar {
    var id: UUID
    var profileId: UUID                     // 關聯的孩子檔案
    var avatarImageURL: String              // 生成的化身圖 URL（透明背景 PNG）
    var avatarLocalPath: String?            // 本地快取

    // AI 提取的造型特徵（不儲存原始照片）
    var hairStyle: String                   // 髮型描述
    var hairColor: String                   // 髮色
    var outfitColor: String                 // 服裝主色
    var accessories: [String]               // 配件（眼鏡、帽子等）
    var characterPrompt: String             // 用於圖片合成的角色描述

    var createdAt: Date
    var isActive: Bool
}

// MARK: - Enums
enum StoryStyle: String, Codable, CaseIterable {
    // 初期 3 種標準風格（每次建立故事時選擇）
    case goodnightGentle = "晚安溫柔風"   // 輕柔敘事、助眠、節奏慢
    case adventureExciting = "冒險精彩風" // 情節緊湊、語氣激昂、充滿驚喜
    case funnyLaughs = "趣味歡笑風"       // 搞笑對白、誇張音效、輕鬆節奏

    // 未來付費擴展風格（Phase 4+）
    // case educational = "知識探索風"
    // case fantasy = "魔法奇幻風"
    // case seasonal = "節日特別風"
}

enum ArtStyle: String, Codable, CaseIterable {
    case softCartoon = "柔和卡通風"         // 初期預設
    case watercolor = "水彩繪本風"          // 初期預設
    case crayon = "蠟筆塗鴉風"             // 初期預設
    case koreanGouache = "韓系水彩手繪風"   // 韓式繪本・水彩+gouache・暖色調自然場景
    // 未來擴展：剪紙風、像素風等
}

enum VoiceType: String, Codable, CaseIterable {
    case gentleMom = "溫柔媽媽"
    case livelyBigSis = "活潑姐姐"
    case steadyDad = "穩重爸爸"
}
```

### 4.2 後端 API 設計

```
# 故事生成
POST   /api/v1/stories/generate           # 觸發故事生成（回傳 story_id）
GET    /api/v1/stories/{id}/status         # 查詢生成進度（polling）
GET    /api/v1/stories/{id}                # 取得完整故事資料
DELETE /api/v1/stories/{id}                # 刪除故事

# 使用者認證
POST   /api/v1/auth/apple                  # Apple Sign In
POST   /api/v1/auth/token/refresh          # 刷新 Token

# 孩子檔案
GET    /api/v1/profiles                    # 列表
POST   /api/v1/profiles                    # 建立
PUT    /api/v1/profiles/{id}               # 更新

# 錄音
POST   /api/v1/recordings/upload           # 上傳錄音（multipart）
GET    /api/v1/recordings?story_id={id}    # 取得故事的錄音列表
DELETE /api/v1/recordings/{id}             # 刪除錄音

# 訂閱
POST   /api/v1/subscription/verify         # 驗證 App Store 收據
GET    /api/v1/subscription/status         # 查詢訂閱狀態

# 使用統計
POST   /api/v1/analytics/listen            # 回報收聽事件
GET    /api/v1/analytics/stats             # 家長查看統計
```

### 4.3 AI 生成 API 回傳格式

```json
{
  "story_id": "uuid-xxx",
  "title": "小熊的太空冒險",
  "cover_image_url": "https://cdn.example.com/covers/xxx.png",
  "ai_audio_url": "https://cdn.example.com/audio/xxx.mp3",
  "duration": 180.5,
  "full_text": "從前從前，在一個充滿星星的夜晚...",

  "characters": [
    {
      "id": "char-1",
      "name": "小熊",
      "description": "勇敢的小熊探險家",
      "intro_sound_url": "https://cdn.example.com/sfx/bear_intro.mp3",
      "glow_color": "#FFD700"
    },
    {
      "id": "char-2",
      "name": "星星精靈",
      "description": "住在月亮上的精靈",
      "intro_sound_url": "https://cdn.example.com/sfx/fairy_intro.mp3",
      "glow_color": "#FF69B4"
    }
  ],

  "segments": [
    {
      "id": "seg-1",
      "type": "narrator",
      "text": "從前從前，在一個充滿星星的夜晚，小熊抬頭看著天空...",
      "start_time": 0.0,
      "end_time": 8.5
    },
    {
      "id": "seg-2",
      "type": "dialogue",
      "character_id": "char-1",
      "text": "哇！那顆星星好亮好亮，我好想去看看！",
      "start_time": 8.5,
      "end_time": 13.2
    },
    {
      "id": "seg-3",
      "type": "narrator",
      "text": "忽然，一道光從天空落下來...",
      "start_time": 13.2,
      "end_time": 17.0
    },
    {
      "id": "seg-4",
      "type": "dialogue",
      "character_id": "char-2",
      "text": "嗨嗨！小熊你好！我是星星精靈，你想跟我去太空玩嗎？",
      "start_time": 17.0,
      "end_time": 23.5
    }
  ],

  "interactive_elements": [
    {
      "id": "elem-1",
      "label": "小熊",
      "type": "character",
      "character_id": "char-1",
      "hitbox": {"x": 0.15, "y": 0.40, "w": 0.25, "h": 0.35},
      "tap_sound_url": "https://cdn.example.com/sfx/bear_hello.mp3",
      "tap_animation": "bounce",
      "speaking_glow_color": "#FFD700"
    },
    {
      "id": "elem-2",
      "label": "星星精靈",
      "type": "character",
      "character_id": "char-2",
      "hitbox": {"x": 0.55, "y": 0.20, "w": 0.20, "h": 0.30},
      "tap_sound_url": "https://cdn.example.com/sfx/fairy_hello.mp3",
      "tap_animation": "glow",
      "speaking_glow_color": "#FF69B4"
    },
    {
      "id": "elem-3",
      "label": "月亮",
      "type": "scene_object",
      "hitbox": {"x": 0.70, "y": 0.05, "w": 0.18, "h": 0.18},
      "tap_sound_url": "https://cdn.example.com/sfx/moon_glow.mp3",
      "tap_animation": "glow"
    },
    {
      "id": "elem-hidden",
      "label": "隱藏小星星",
      "type": "hidden_item",
      "hitbox": {"x": 0.88, "y": 0.75, "w": 0.06, "h": 0.06},
      "tap_sound_url": "https://cdn.example.com/sfx/sparkle.mp3",
      "tap_animation": "fly_away",
      "is_hidden": true,
      "discovery_reward": "你發現了隱藏的小星星！"
    }
  ]
}
```

---

## 五、UI/UX 詳細流程設計

### 5.1 使用者旅程圖

```
首次開啟 App
    │
    ▼
[歡迎動畫 — 星球從遠方飛來，角色們向你招手]
    │
    ▼
[家長設定]（家長閘門保護）
    ├── 建立帳號（Apple Sign In）
    ├── 建立孩子檔案（名字、年齡）
    ├── 選擇畫風（2-3 種預設，之後所有故事統一使用）
    ├── 選擇聲線（溫柔媽媽/活潑姐姐/穩重爸爸）
    ├── 建立小朋友化身（拍照 → AI 生成角色，可跳過）
    └── 收聽時間設定（可跳過）
    │
    ▼
[引導教學 — 3 步驟]
    ├── Step 1: 「告訴我你想聽什麼故事？」
    ├── Step 2: 「看！你的化身也在封面裡面，找到了嗎？」
    └── Step 3: 「點點角色看看會怎樣？」
    │
    ▼
[書架首頁] ←────────────────────────┐
    │                                │
    ├── 點「+ 新故事」─────→ [故事創作流程]
    │                                │
    ├── 點封面 ─────────→ [有聲書播放器] ←── 核心體驗
    │                                │
    └── 底部 Tab Bar ────────────────│
         ├── 🏠 首頁（推薦靈感）      │
         ├── 📚 書架（我的故事）       │
         ├── ✨ 創作（新故事入口）     │
         └── 👤 我的（家長區入口）     │
              └── [家長閘門] ─────────┘
```

### 5.2 有聲書播放器（核心體驗 — 詳細設計）

```
播放器主畫面（全螢幕）：

┌──────────────────────────────────┐
│ ← 返回                    ❤ ⚙   │  ← 導航列（半透明）
│                                  │
│  ┌────────────────────────────┐  │
│  │                            │  │
│  │                            │  │
│  │     ┌────┐     ┌────┐     │  │
│  │     │小熊│     │精靈│     │  │
│  │     │ ✨ │     │    │     │  │  ← 小熊正在說話（發光）
│  │     └────┘     └────┘     │  │
│  │                            │  │
│  │          ┌────┐            │  │
│  │          │月亮│            │  │
│  │          └────┘    🌟      │  │  ← 隱藏彩蛋（不明顯）
│  │                            │  │
│  │   🌲🌲     🌲🌲     🌲🌲   │  │
│  │                            │  │
│  └────────────────────────────┘  │
│                                  │
│  「哇！那顆星星好亮好亮！」        │  ← 當前台詞文字
│                                  │
│   ━━━━━━━━━━━━━●━━━━━━━━━━━━━  │  ← 播放進度
│   0:45                    3:00   │
│                                  │
│         ⏮    ▶    ⏭             │  ← 播放控制
│                                  │
│   🔊        🎙 錄我的聲音         │
└──────────────────────────────────┘

互動狀態說明：
- 故事播放中，當前說話角色會有發光邊框 + 輕微浮動動畫
- 用戶隨時可點擊任何角色，觸發獨立音效（不中斷故事播放）
- 進度條可拖曳跳轉
- ⏮ / ⏭ 以段落為單位前後跳轉
```

### 5.3 故事創作流程

```
Step 1: 選擇風格 + 輸入靈感
┌──────────────────────────────────┐
│ ← 取消                           │
│                                  │
│   今天想聽什麼樣的故事？           │
│                                  │
│   ┌──────────────────────────┐   │
│   │ 🌙 晚安溫柔風             │   │  ← 三選一（大按鈕）
│   │    輕輕柔柔，適合睡前聽    │   │
│   └──────────────────────────┘   │
│   ┌──────────────────────────┐   │
│   │ ⚡ 冒險精彩風      ✓     │   │  ← 選中狀態
│   │    刺激有趣，充滿驚喜！    │   │
│   └──────────────────────────┘   │
│   ┌──────────────────────────┐   │
│   │ 😄 趣味歡笑風             │   │
│   │    哈哈大笑，開心一整天    │   │
│   └──────────────────────────┘   │
│                                  │
│   ✨ 告訴我你想聽什麼？           │
│   ┌────────────────────────────┐ │
│   │ 🎤 說出你的關鍵字...        │ │  ← 語音/文字輸入
│   └────────────────────────────┘ │
│                                  │
│   或選擇靈感：                    │
│   [🐻 動物] [🚀 太空] [🧚 精靈]  │
│   [🌊 海洋] [🎂 生日] [🏠 家庭]  │
│                                  │
│   已選：恐龍、太空                │
│                                  │
│        [ ✨ 開始創作！ ]          │
└──────────────────────────────────┘

> 注意：畫風 & 聲線已在帳號設定中選好，創作流程不再選擇
> 小朋友化身（如已建立）會自動出現在封面中

Step 3: 生成中（等待動畫 — 關鍵！不能讓孩子覺得無聊）
┌──────────────────────────────────┐
│                                  │
│        ⭐ ⭐ ⭐                   │
│     ✨ 故事正在誕生中... ✨        │
│                                  │
│   ┌────────────────────────────┐ │
│   │                            │ │
│   │    [小星星正在畫畫動畫]      │ │  ← 可愛的等待動畫
│   │    不同階段切換不同動畫       │ │
│   │                            │ │
│   └────────────────────────────┘ │
│                                  │
│   📝 故事文字... 完成 ✓          │
│   🎨 繪製封面... 完成 ✓          │
│   🔊 配音中... (進行中)          │
│   ✨ 準備互動元素...              │
│                                  │
│   預計還需 20 秒                  │
│                                  │
└──────────────────────────────────┘
```

### 5.4 設計規範

**色彩系統：**
| 用途 | 色彩 | 說明 |
|------|------|------|
| 主色 | `#6C5CE7` (紫) | 夢幻、想像力 |
| 輔色 | `#FDCB6E` (暖黃) | 溫暖、歡樂 |
| 強調 | `#FF6B6B` (珊瑚紅) | 互動提示 |
| 背景 | `#FFF8F0` (暖白) | 柔和護眼 |
| 夜間背景 | `#2D1B69` (深紫) | 夜間模式 |
| 角色高亮 | `#FFD700` (金) | 說話角色預設發光色 |

**字體規範：**
- 故事標題：圓體, 24-28pt
- 台詞文字：圓體, 20-24pt（大字方便兒童辨識）
- UI 文字：系統圓體, 16-18pt
- WCAG AA 對比度標準

**互動設計原則：**
- 所有可點擊的角色最小 60x60pt（比標準 44pt 更大，適合幼兒手指）
- 點擊回饋延遲 < 100ms
- 角色高亮動畫：0.3s ease-in-out
- 音效與故事朗讀獨立通道播放（不互相干擾）
- 避免閃爍、突然的大聲音效

---

## 六、AI 故事生成 Pipeline 設計

### 6.1 生成流程

```
用戶輸入（關鍵字 + 風格 + 聲線）
        │
        ▼
┌────────────────────────┐
│ 1. 故事腳本生成          │  ← Claude API
│    - 故事文本            │     ~3-5 秒
│    - 角色定義            │
│    - 段落切分            │
│    - 封面描述 prompt      │
│    - 互動元素建議         │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ 2. 內容安全檢查          │  ← 關鍵字過濾 + AI 審核
│    - 文字安全性           │     ~1 秒
│    - 封面 prompt 安全性   │
└───────────┬────────────┘
            │
            ├─────────────────────┐
            ▼                     ▼
┌──────────────────┐   ┌─────────────────────┐
│ 3a. 封面圖生成    │   │ 3b. 語音合成         │  ← 並行
│   - 單張封面圖    │   │   - 完整故事語音      │
│   - 角色清晰     │   │   - 含旁白+角色台詞   │
│   - 可互動佈局   │   │   - 生成時間戳        │
│   ~10-20 秒      │   │   ~5-15 秒           │
└────────┬─────────┘   └──────────┬──────────┘
         │                        │
         ▼                        │
┌──────────────────┐              │
│ 4. 互動元素偵測   │              │
│   - AI 分析封面   │  ← ~3-5 秒  │
│   - 角色定位      │              │
│   - hitbox 生成   │              │
│   - 音效配對      │              │
└────────┬─────────┘              │
         │                        │
         └────────────┬───────────┘
                      ▼
┌────────────────────────┐
│ 5. 化身合成（若有）      │
│   - 將小朋友化身 PNG    │  ← ~1-2 秒
│     合成到封面隨機位置   │
│   - 生成化身的 hitbox   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ 6. 組裝與儲存           │
│   - 組合所有資料        │
│   - 上傳 CDN           │
│   - 回傳給 App         │
└────────────────────────┘

總生成時間目標：20-40 秒（比多頁繪本更快！）
```

**相較多頁繪本的優勢：**
- 只需生成 1 張圖（非 8-12 張），成本與時間大幅降低
- 語音是連續的一段，不需每頁分段
- 生成時間更短，用戶體驗更好

### 6.2 Prompt 設計策略

**故事腳本生成 Prompt：**
```
你是一位專業的兒童有聲書作家，專門為 3-6 歲的孩子創作故事。

任務：根據用戶的關鍵字和故事風格，創作一個適合語音朗讀的有聲書故事腳本。

## 故事風格指引

根據選定的風格調整敘事方式：

【晚安溫柔風】
- 節奏緩慢，句子短而溫柔
- 多用疊字和輕聲語氣（如「輕輕的」「慢慢的」「軟軟的」）
- 結尾導向安靜、睡眠（角色打呵欠、閉眼睛）
- 語音標記：旁白語速 slow、語調 soft、角色台詞 whisper-like
- 故事情緒弧線：平靜 → 微微起伏 → 回歸寧靜

【冒險精彩風】
- 節奏明快，有清晰的起承轉合
- 多用感嘆詞和緊張感（「天哪！」「快跑！」「不得了了！」）
- 角色面對挑戰、克服困難、達成目標
- 語音標記：旁白語速 normal-fast、語調 dynamic、角色台詞 expressive
- 故事情緒弧線：好奇 → 挑戰 → 緊張 → 勝利！

【趣味歡笑風】
- 語言誇張幽默，角色個性鮮明對比
- 多用擬聲詞和意想不到的轉折（「砰！」「噗通！」「咦？」）
- 角色做出搞笑的事、鬧出有趣的誤會
- 語音標記：旁白語速 normal、語調 playful、角色台詞 exaggerated
- 故事情緒弧線：有趣 → 更有趣 → 爆笑 → 溫馨收尾

## 格式要求
1. 故事長度：約 300-800 字，朗讀時間 2-5 分鐘
2. 故事結構：旁白與角色對話交替
3. 角色數量：2-4 個主要角色
4. 每個角色需有鮮明性格和至少 3 句台詞
5. 故事需有正向結局

## 同時請提供
- 封面圖描述（英文 prompt，包含所有角色的場景）
- 每個角色的簡述和建議高亮顏色
- 每段旁白/台詞的語音標記（語速、語氣、情緒）

## 安全規則
- 絕對禁止：暴力、恐怖、歧視、負面情緒、危險行為

## 輸出 JSON 格式
{
  "title": "故事標題",
  "cover_prompt": "英文圖片生成 prompt",
  "characters": [...],
  "segments": [
    {
      "type": "narrator|dialogue",
      "character_id": "...",
      "text": "...",
      "voice_direction": {
        "speed": "slow|normal|fast",
        "tone": "soft|dynamic|playful|whisper",
        "emotion": "calm|excited|funny|surprised"
      }
    }
  ]
}

用戶關鍵字：{keywords}
故事風格：{style}
```

**語音合成與風格對應：**

故事風格不只影響文本，也影響 TTS 語音合成的參數：

| 風格 | TTS 語速 | TTS 語調 | 停頓時長 | 背景音效 |
|------|---------|---------|---------|---------|
| 🌙 晚安溫柔風 | 0.8x | 低柔 | 長（1-2s） | 輕柔音樂盒、蟲鳴 |
| ⚡ 冒險精彩風 | 1.0-1.2x | 起伏大 | 短（0.3-0.5s） | 鼓點、風聲 |
| 😄 趣味歡笑風 | 1.0x | 活潑誇張 | 中（0.5-1s） | 卡通音效、彈簧聲 |

---

## 七、MVP 重新定義（v5 — 極簡驗證版，Claude Code 開發）

### 開發限制聲明
> **開發者使用 Claude Code 作為唯一開發工具。**
> 這代表：Claude Code 會撰寫所有程式碼、執行命令、處理部署。
> 開發者負責：提供 API Key、確認需求、在瀏覽器/手機上測試。
> 因此技術選型必須以「Claude Code 能一次寫對、出錯容易排查」為原則。

### MVP 目標
> 最快速度做出一個可以「生成故事 + 收聽故事」的網頁，
> 讓自己試用、讓有興趣的家長試用、可以錄製 demo 影片給聽眾看。

### MVP 只做兩件事
1. **生成故事**：輸入關鍵字 → AI 生成故事文字 + 封面圖 + 語音
2. **收聽故事**：看到封面 + 播放語音

### MVP 明確不做
| 功能 | 延後到 | 理由 |
|------|--------|------|
| 訂閱/付費 | Phase 2+ | 先驗證體驗再談錢 |
| 帳號系統/登入 | Phase 2+ | 多一步就多一個流失 |
| 家長控制/閘門 | Phase 2+ | 目前是自己和熟人試用 |
| 角色互動（點擊角色） | Phase 2+ | 錦上添花，不是核心 |
| 角色高亮同步 | Phase 2+ | 同上 |
| 家長錄音 | Phase 2+ | 同上 |
| 小朋友化身 | Phase 3+ | 需要更多 AI 整合 |
| 離線模式 | Phase 3+ | 網頁版不需要 |
| 多語言 | Phase 4+ | 先做好繁中 |

---

### 技術方案：為 Claude Code 開發最佳化

**技術選型原則：**
- Claude Code 最熟悉、最能產出正確程式碼的框架
- 盡量減少需要手動配置的服務（減少出錯機會）
- 部署步驟越少越好

**選擇 Next.js（App Router）的理由：**
- Claude Code 對 Next.js 的程式碼生成品質非常高
- 前後端一體化（不需要分別部署前端和後端）
- API Routes 就在同一個專案裡，不需額外設 CORS 或 server
- Vercel 一鍵部署（GitHub push 即上線）
- TypeScript + Tailwind CSS 是 Claude Code 最擅長的組合

**為什麼不選其他方案：**
| 方案 | 不選的理由 |
|------|-----------|
| 純 HTML/JS | 無法處理後端 API 呼叫（需要隱藏 API Key） |
| FastAPI + 另外的前端 | 需要部署兩個服務，增加複雜度 |
| Flask/Django | Claude Code 可以寫，但前端需要另外處理 |
| React SPA + serverless | 配置比 Next.js 多，更容易出錯 |

**極簡架構（全部在一個 Next.js 專案裡）：**
```
story-planet/                    ← 一個 repo，一個專案
├── app/
│   ├── page.tsx                 ← 書架首頁
│   ├── create/page.tsx          ← 建立故事頁
│   ├── story/[id]/page.tsx      ← 播放器頁面
│   └── api/
│       ├── stories/
│       │   ├── route.ts         ← GET 故事列表
│       │   └── [id]/route.ts    ← GET 故事詳情
│       └── generate/
│           └── route.ts         ← POST 觸發 AI 生成
├── lib/
│   ├── ai/
│   │   ├── story-generator.ts   ← Claude API 串接
│   │   ├── image-generator.ts   ← DALL-E 3 串接
│   │   └── voice-generator.ts   ← TTS 串接
│   ├── db.ts                    ← Supabase client
│   └── types.ts                 ← TypeScript 型別定義
├── components/
│   ├── StoryCard.tsx            ← 書架封面卡片
│   ├── AudioPlayer.tsx          ← 音訊播放器
│   └── GeneratingStatus.tsx     ← 生成進度顯示
├── .env.local                   ← API Keys（不上傳 git）
├── package.json
└── next.config.js
```

**外部服務清單（開發者需申請 API Key）：**

| 服務 | 用途 | 費用 | 申請位置 |
|------|------|------|---------|
| **Anthropic Claude** | 故事文字生成 | 按用量計費（~$0.02/故事） | console.anthropic.com |
| **OpenAI (DALL-E 3)** | 封面圖生成 | $0.04/張（1024x1024） | platform.openai.com |
| **ElevenLabs** | 語音合成 | 免費方案有 10,000 字/月 | elevenlabs.io |
| **Supabase** | 資料庫 + 檔案儲存 | 免費（500MB） | supabase.com |
| **Vercel** | 部署 | 免費（Hobby plan） | vercel.com |
| **GitHub** | 程式碼托管 | 免費 | github.com |

> 開發者在開始前需要準備好這 4 組 API Key：
> `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL` + `SUPABASE_KEY`

---

### MVP 頁面設計（3 個頁面，夠用就好）

**頁面 1：書架首頁** `app/page.tsx`
```
┌──────────────────────────────┐
│  故事星球                     │
│                    [+ 新故事] │
│                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ │
│  │ 封面  │ │ 封面  │ │ 封面  │ │
│  │  圖   │ │  圖   │ │  圖   │ │
│  │      │ │      │ │      │ │
│  │小熊的 │ │海底的 │ │月亮上 │ │
│  │冒險   │ │朋友   │ │的貓   │ │
│  │ 3:20 │ │ 2:45 │ │ 4:10 │ │
│  └──────┘ └──────┘ └──────┘ │
│                              │
│  （沒有故事時顯示）            │
│  「還沒有故事，來創作一個吧！」│
└──────────────────────────────┘
```

**頁面 2：建立故事** `app/create/page.tsx`
```
┌──────────────────────────────┐
│ ← 返回                       │
│                              │
│  建立新故事                   │
│                              │
│  故事風格：                   │
│  (🌙 晚安) (⚡ 冒險✓) (😄 搞笑)│
│                              │
│  輸入關鍵字（用逗號分隔）：    │
│  ┌──────────────────────────┐│
│  │ 恐龍, 太空, 友誼          ││
│  └──────────────────────────┘│
│                              │
│  [ 開始生成 ]                │
│                              │
│  --- 生成中 ---               │
│  📝 故事文字 ✓               │
│  🎨 封面圖 生成中...          │
│  🔊 語音 等待中...            │
└──────────────────────────────┘
```

**頁面 3：播放器** `app/story/[id]/page.tsx`
```
┌──────────────────────────────┐
│ ← 返回書架                    │
│                              │
│  ┌──────────────────────────┐│
│  │                          ││
│  │      AI 生成的封面圖      ││
│  │                          ││
│  └──────────────────────────┘│
│                              │
│  小熊的太空冒險               │
│                              │
│  ━━━━━━━━●━━━━━━━━━━━━━━━━  │
│  1:23                  3:20  │
│                              │
│         ▶ / ⏸               │
│                              │
│  ┌──────────────────────────┐│
│  │ 從前從前，在一個充滿星星的 ││ ← 故事文字（可捲動閱讀）
│  │ 夜晚，小熊抬頭看著天空...  ││
│  │ 「哇！那顆星星好亮好亮，  ││
│  │ 我好想去看看！」           ││
│  └──────────────────────────┘│
└──────────────────────────────┘
```

---

### MVP 後端 API（3 個 endpoint，全部在 Next.js API Routes）

```
POST /api/generate
  Body: { keywords: ["恐龍", "太空"], style: "adventure" }
  行為：呼叫 Claude → 呼叫 DALL-E + TTS（並行）→ 存入 Supabase → 回傳
  Response: { story_id, title, cover_url, audio_url, full_text, duration }
  注意：這是一個長時間請求（15-25 秒），前端需 loading 狀態

GET /api/stories
  行為：從 Supabase 查詢所有故事
  Response: [{ id, title, cover_url, audio_url, duration, created_at, style }]

GET /api/stories/[id]
  行為：從 Supabase 查詢單一故事
  Response: { id, title, full_text, cover_url, audio_url, duration, style, created_at }
```

> MVP 選擇同步 API（等 AI 全部完成再回傳），不做 polling/webhook。
> 理由：實作最簡單，Claude Code 一次寫對的機率最高。
> 代價：前端需要等待 15-25 秒，用 loading spinner 處理。
> 後續優化：改為非同步（先回 story_id，前端 polling 進度）。

---

### MVP AI Pipeline（極簡版）

```
POST /api/generate 收到請求
        │
        ▼
┌───────────────────┐
│ 1. Claude API     │  ~3-5 秒
│    輸入：keywords + style
│    輸出：故事文字 + 英文封面 prompt
└─────────┬─────────┘
          │
    ┌─────┴─────┐      ← Promise.all() 並行
    ▼           ▼
┌─────────┐ ┌─────────┐
│ DALL-E  │ │ TTS     │
│ 3 API   │ │ API     │
│ 封面圖  │ │ 語音    │
│ ~10-15s │ │ ~5-10s  │
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│上傳圖片  │ │上傳音訊  │   ← Supabase Storage
│到Storage│ │到Storage│
└────┬────┘ └────┬────┘
     └─────┬─────┘
           ▼
┌───────────────────┐
│ 寫入 DB 記錄       │   ← Supabase Database
│ 回傳結果給前端      │
└───────────────────┘

總時間：15-25 秒
```

**Claude Prompt 設計（MVP 簡化版）：**
```
你是兒童有聲書作家，為 3-6 歲孩子創作故事。

根據關鍵字「{keywords}」，以「{style}」風格創作故事。

風格說明：
- 晚安溫柔風：語氣輕柔，適合睡前，結尾導向安靜
- 冒險精彩風：情節緊湊，有挑戰和驚喜
- 趣味歡笑風：搞笑誇張，充滿擬聲詞

要求：
1. 300-600 字，2-4 分鐘朗讀時間
2. 2-3 個角色，簡單句型
3. 正向結局
4. 禁止暴力、恐怖內容

請以 JSON 格式回覆：
{
  "title": "故事標題",
  "full_text": "完整故事文字...",
  "cover_prompt": "英文圖片生成 prompt，描述包含所有角色的一個場景，兒童繪本卡通風格"
}
```

---

### Supabase 資料庫 Schema（一張表就夠）

```sql
CREATE TABLE stories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  keywords TEXT[] NOT NULL,
  style TEXT NOT NULL,
  full_text TEXT NOT NULL,
  cover_image_url TEXT NOT NULL,
  audio_url TEXT NOT NULL,
  duration FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

> 只有一張表。不需要 user 表、不需要 session 表。極簡。

---

### 開發步驟（Claude Code 執行）

**前置準備（開發者手動完成）：**
1. 申請 API Key（Anthropic、OpenAI、ElevenLabs）
2. 建立 Supabase 專案（免費方案）
3. 建立 GitHub repo
4. 建立 Vercel 帳號並連結 GitHub

**Claude Code 開發步驟：**

| 步驟 | Claude Code 執行的工作 | 驗證方式 |
|------|----------------------|---------|
| 1 | `npx create-next-app` 建立專案 + 安裝依賴 | `npm run dev` 能跑起來 |
| 2 | 建立 `.env.local` 模板 + `lib/types.ts` 型別 | 檔案存在 |
| 3 | 寫 `lib/db.ts` Supabase client | 能連上 Supabase |
| 4 | 寫 `lib/ai/story-generator.ts` | 呼叫 Claude API 能回傳故事 JSON |
| 5 | 寫 `lib/ai/image-generator.ts` | 呼叫 DALL-E 3 能回傳圖片 URL |
| 6 | 寫 `lib/ai/voice-generator.ts` | 呼叫 TTS 能回傳音訊檔 |
| 7 | 寫 `app/api/generate/route.ts` | curl POST 能觸發完整 pipeline |
| 8 | 寫 `app/api/stories/route.ts` + `[id]/route.ts` | curl GET 能回傳資料 |
| 9 | 寫 `app/page.tsx` 書架首頁 | 瀏覽器能看到故事列表 |
| 10 | 寫 `app/create/page.tsx` 建立故事頁 | 能輸入關鍵字並觸發生成 |
| 11 | 寫 `components/AudioPlayer.tsx` 音訊播放器 | 能播放/暫停音訊 |
| 12 | 寫 `app/story/[id]/page.tsx` 播放器頁面 | 能看封面 + 聽故事 + 看文字 |
| 13 | 手機端 RWD 基本調整 | 手機瀏覽器可正常使用 |
| 14 | push to GitHub → Vercel 自動部署 | URL 可訪問 |

> 每個步驟都是獨立可驗證的，出錯時 Claude Code 可以定位修復。

---

### MVP 預估成本

| 項目 | 費用 |
|------|------|
| Vercel 部署 | 免費（Hobby plan） |
| Supabase | 免費（Free tier, 500MB） |
| GitHub | 免費 |
| Claude API（每個故事） | ~$0.02 |
| DALL-E 3（每張封面） | ~$0.04 |
| ElevenLabs TTS | 免費方案 10,000 字/月（約 15-20 個故事） |
| **每個故事總計** | **~$0.06-0.10**（TTS 免費方案內）|
| **試用 20 個故事** | **~$1.2-2.0** |

> 初期驗證成本極低。ElevenLabs 免費方案夠測試 15-20 個故事/月。
> 超過免費額度後，付費方案 $5/月可生成約 30,000 字（50+ 個故事）。

---

### MVP 之後的演進路線

```
Phase 0 — MVP 驗證 ← 現在要做的
  └── 生成 + 收聽，部署到 Vercel
  └── 自己和家長試用，錄 demo 影片

Phase 1 — 體驗補完
  ├── 故事風格的語音差異化
  ├── 手機端 UI 優化（更大的播放按鈕、更好看的書架）
  ├── 刪除故事功能
  └── 簡易密碼保護（避免別人亂用 API 額度）

Phase 2 — 功能擴展
  ├── 封面角色互動（點擊播放音效）
  ├── 簡易帳號系統
  ├── 訂閱付費（Stripe）
  └── 小朋友化身

Phase 3 — 原生 App
  ├── iOS SwiftUI App（後端 API 共用）
  ├── 背景播放、離線模式
  └── Apple 審核上架
```

---

### 風險與應對

| 風險 | 影響 | 應對 |
|------|------|------|
| AI 生成的故事品質不穩定 | 用戶體驗差 | Prompt 反覆調教；加入「重新生成」按鈕 |
| DALL-E 封面圖風格不一致 | 書架看起來亂 | 在 prompt 中固定風格描述前綴 |
| TTS 中文發音不自然 | 聽起來像機器人 | 測試多家 TTS（ElevenLabs vs Azure vs Google），選最自然的 |
| Vercel 免費方案 function timeout | 生成 API 超時（預設 10s） | Vercel Hobby 可設到 60s；或改用非同步 |
| API Key 被濫用 | 產生意外帳單 | 部署時設定用量上限；加簡易密碼保護 |
| Supabase 免費空間不夠 | 500MB 約存 200-300 個故事 | 驗證階段夠用；超過後升級（$25/月） |

---

## 執行計畫 — 立即開始

### 開發者準備事項（在 Claude Code 開始寫 code 之前）

1. **申請 API Key**（約 30 分鐘）
   - Anthropic Console → 取得 `ANTHROPIC_API_KEY`
   - OpenAI Platform → 取得 `OPENAI_API_KEY`
   - ElevenLabs → 取得 `ELEVENLABS_API_KEY`
   - 每個服務都需要綁定付費方式（信用卡），但初期花費極低

2. **建立 Supabase 專案**（約 10 分鐘）
   - 到 supabase.com 建立免費專案
   - 取得 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY`
   - 建立 Storage bucket（命名為 `stories`）

3. **建立 GitHub repo**（約 5 分鐘）
   - 建立名為 `story-planet` 的 repo

4. **建立 Vercel 帳號**（約 5 分鐘）
   - 連結 GitHub
   - 後續 push 到 GitHub 即自動部署

### Claude Code 開始開發

準備好 API Key 之後，告訴 Claude Code：
> 「請開始開發故事星球 MVP，依照 docs/product-spec.md 的規劃執行。
> 這是我的 API Keys：（提供 .env.local 的內容）」

Claude Code 會按照上述 14 個步驟逐步建立專案並部署。
