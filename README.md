# Arena of Valor 傳說對決：自動化輿情監視系統

這是一套基於 AI 分析建立的**社群輿情自動監測管線**。系統會每日自動搜尋網路討論區及社群媒體（包含 Instagram、Threads），透過超強語言模型（Google Gemini）萃取關鍵字、分析玩家正負面情緒，最終生成圖文並茂的 HTML 網頁報表，並透過 **LINE / Telegram** 雙管齊下進行晨報推播。

## 🎯 系統架構與流程
1. **收集情報**：使用 Tavily 全網搜尋引擎與 Apify 雲端爬蟲，雙引擎挖掘有關「傳說對決」的貼文與文章。
2. **AI 分析**：串接 Gemini 2.5 Flash API，自動判讀每篇情報的情緒傾向（正面/負面/中立），並萃取熱門話題與近期活動。
3. **網頁成報**：依賴 Jinja2 動態生成報告網頁（儲存於 `data/reports/`），並以 Chart.js 畫出圓餅圖、長條圖。
4. **即時推播**：透過 `Line Messaging API` (Flex Message) 以及 `Telegram Bot` 遞送每日濃縮摘要卡片。
5. **完全自動化**：內建 `APScheduler` 定時任務，預設每日早上 09:00 自動巡邏、分析、發報。

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
