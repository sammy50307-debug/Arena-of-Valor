# Arena of Valor 傳說對決：自動化輿情監視系統

這是一套基於 AI 分析建立的**社群輿情自動監測管線**。系統會每日自動搜尋網路討論區及社群媒體（包含 Instagram、Threads），透過超強語言模型（Google Gemini）萃取關鍵字、分析玩家正負面情緒，最終生成圖文並茂的 HTML 網頁報表，並透過 **LINE / Telegram** 雙管齊下進行晨報推播。

## 🎯 系統架構與流程

1. **收集情報**：使用 Tavily 全網搜尋引擎與 Apify 雲端爬蟲，雙引擎挖掘有關「傳說對決」的貼文與文章。
2. **AI 分析**：串接 Gemini 2.5 Flash API，自動判讀每篇情報的情緒傾向（正面/負面/中立），並萃取熱門話題與近期活動。
3. **網頁成報**：依賴 Jinja2 動態生成報告網頁（儲存於 `data/reports/`），並以 Chart.js 畫出圓餅圖、長條圖。
4. **即時推播**：透過 `Line Messaging API` (Flex Message) 以及 `Telegram Bot` 遞送每日濃縮摘要卡片。
5. **完全自動化**：內建 `APScheduler` 定時任務，預設每日早上 09:00 自動巡邏、分析、發報。

---

## ⚠️ API 額度與用量評估 (Token 消耗)

本專案高度依賴免費版 API 服務。為了避免額度枯竭觸發 `429 拒絕服務` 錯誤，請隨時留意以下各節點的額度消耗狀況：

### 1. Google Gemini (AI 情緒與事件分析)

這是全系統最耗費 Token 的大腦，核心消耗位於 `analyzer/sentiment.py`。

* **單篇分析 (`analyze_posts`)**
  * **消耗方式**：將每篇社群貼文連同 Prompt 拋給 AI 評估。
  * **平均消耗**：每篇約 500 ~ 1,000 Input Tokens / 100 Output Tokens。
  * **總計**：若一日搜集 12 篇貼文，約消耗 **10,000 ~ 15,000 Tokens** 與 **12 次 Request**。
* **每日總結 (`generate_daily_summary`)**
  * **消耗方式**：將 12 篇貼文的分析結果串成一大包文字，要求 AI 產生總結與熱度排名。
  * **平均消耗**：一次約 3,000 ~ 5,000 Input Tokens / 500 Output Tokens。
* **免費版配額對照表（2025 年 12 月更新後生效）**

  | 限制項目 | **Gemini 2.5 Flash** (目前使用) | **Gemini 2.5 Pro** |
  |---|---|---|
  | 每分鐘請求數 (RPM) | **10 次** | **5 次** |
  | 每日請求數 (RPD) | **250 次** | **100 次** |
  | 每分鐘 Token (TPM) | 25 萬 | 25 萬 |

* **以本專案實際用量換算（4 組關鍵字、每組抓 3 篇，一趟約 13~15 次 Request）**

  | 使用的模型 | 一天可跑幾次 `main.py` | 適用場景 |
  |---|---|---|
  | **2.5 Flash** | 約 **16 ~ 19 次** | ✅ 日常排程 + 偶爾手動測試，綽綽有餘 |
  | **2.5 Pro** | 約 **6 ~ 7 次** | ⚠️ 額度吃緊，僅適合每天排程自動跑 1 次 |

* **額度重置時間**：每日配額在**太平洋時間午夜 (PT 00:00)** 自動重置，換算台灣時間約為**下午 15:00（夏令）或 16:00（冬令）**。
* *註：若單日為除錯瘋狂測試導致鎖卡，請更換 API Key 或等待上述時間重置。切換模型請修改 `analyzer/gemini_client.py` 中的 `GEMINI_MODEL` 常數。*

### 2. Tavily Search (搜尋引擎爬蟲)

負責潛入各大論壇與社群抓取原始貼文，位於 `scrapers/tavily_searcher.py`。

* **消耗方式**：依據 `.env` 裡的 `SEARCH_KEYWORDS` 數量扣除。目前預設為 4 個精準關鍵字，**每次執行固定消耗 4 個 Credits**。
* **你的免費版剩餘額度**
  * Tavily 每個免費帳號**終身只有 1,000 個 Credits**（非每月重置）。
  * 以一天執行 1 次排程計算：每天耗費 4 Credit，**一組免費帳號大約可穩定運作 250 天（約 8 個半月）**。
  * *註：若未來停止撈取資料，請至 [Tavily](https://tavily.com/) 註冊新帳號並替換 `.env`。*

---

## 🚀 快速開始

### 1. 安裝套件

請確認你的電腦已安裝 Python 3.8 或以上版本，並執行以下指令：

```bash
pip install -r requirements.txt
```

### 2. 環境變數設定

請複製 `.env.example` 並重新命名為 `.env`，填妥以下 API 金鑰：

* `GEMINI_API_KEY`: 提供給 AI 大腦分析的金鑰
* `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_USER_ID`: 請至 LINE Developers 申請 Messaging API
* `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`: Telegram 推播機器人設定
* `TAVILY_API_KEY`: 搜尋引擎 API
* `APIFY_TOKEN`: Apify 雲端爬蟲金鑰

### 3. 操作指令

**啟動自動排程模式（讓它常駐於背景）：**

```bash
python main.py
```

> 系統將隨時待命，並於每日 `SCHEDULE_HOUR` / `SCHEDULE_MINUTE` 自動啟動流程。

**手動立即執行模式（適合測試）：**

```bash
python main.py --run-now
```

> 系統將立刻執行一次完整的「挖掘->分析->建檔->推播」流程。

---

## 🛠️ 開發與維護

* **調整關鍵字**：於 `.env` 檔案中的 `SEARCH_KEYWORDS` 增加新英雄或活動名稱（用逗號分隔）。
* **新增爬蟲來源**：可於 `scrapers/` 目錄下繼承 `BaseScraper` 並實作 `scrape` 方法，最後於 `main.py` 內註冊即可彈性擴充系統！
* **報告樣板**：如果想修改視覺介面，請編輯 `reporter/templates/report.html`。
