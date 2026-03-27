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

### 📊 各大語言模型免費版配額完整對照表

> 資料來源：[Google AI for Developers](https://ai.google.dev/pricing)、[OpenAI Platform](https://platform.openai.com/docs/guides/rate-limits)、[Anthropic Docs](https://docs.anthropic.com/en/docs/about-claude/models)
> 最後更新：2025 年 12 月

#### Google Gemini 家族（免費版，無需信用卡）

| 限制項目 | **2.5 Flash** | **2.5 Flash-Lite** | **2.5 Pro** 🟢 目前使用 |
|---|---|---|---|
| 每分鐘請求數 (RPM) | **10** | **15** | **5** |
| 每日請求數 (RPD) | **250** | **1,000** | **100** |
| 每分鐘 Token (TPM) | 25 萬 | 25 萬 | 25 萬 |
| Context Window | 100 萬 | 100 萬 | 100 萬 |
| 額度重置 | 每日 PT 00:00（台灣約 15:00~16:00） | 同左 | 同左 |
| **本專案一天可跑幾次** | **~16 次** ✅ | **~66 次** ✅✅ | **~6 次** ⚠️ |

#### OpenAI GPT 家族（❌ 無免費 API 額度）

| 限制項目 | **GPT-4o** | **GPT-4o mini** |
|---|---|---|
| 免費額度 | ❌ **無** — 需綁信用卡付費 | ❌ **無** — 需綁信用卡付費 |
| 付費價格 (Input) | $2.50 / 百萬 Token | $0.15 / 百萬 Token |
| 付費價格 (Output) | $10.00 / 百萬 Token | $0.60 / 百萬 Token |
| Tier 1 RPM | 500 | 500 |
| Context Window | 12.8 萬 | 12.8 萬 |
| **本專案每日成本估算** | 約 NT$1~2 / 天 | 約 NT$0.1 / 天 |

#### Anthropic Claude 家族（❌ 無免費 API 額度）

| 限制項目 | **Claude Sonnet 4** | **Claude Haiku 3.5** |
|---|---|---|
| 免費額度 | ❌ **無** — 最低需預存 $5 美金 | ❌ **無** — 最低需預存 $5 美金 |
| 付費價格 (Input) | $3.00 / 百萬 Token | $0.25 / 百萬 Token |
| 付費價格 (Output) | $15.00 / 百萬 Token | $1.25 / 百萬 Token |
| Tier 1 RPM | 50 | 50 |
| Context Window | 20 萬 | 20 萬 |
| **本專案每日成本估算** | 約 NT$2~3 / 天 | 約 NT$0.2 / 天 |

#### 💡 總結建議

| 考量因素 | 最佳選擇 |
|---|---|
| 🆓 完全免費、零成本 | **Gemini 2.5 Flash**（目前方案）或 **Flash-Lite**（額度更大） |
| 🧠 推理品質最強 | **Gemini 2.5 Pro**（免費但額度極少）或 **GPT-4o**（付費） |
| 💰 付費但超便宜 | **GPT-4o mini** 或 **Claude Haiku 3.5** |
| 🔄 額度重置週期 | Gemini = **每日重置** / OpenAI & Claude = **每月帳單制** |

* *切換模型請修改 `analyzer/gemini_client.py` 中的 `GEMINI_MODEL` 常數。若切換至 OpenAI 或 Claude 則需重寫 client 模組。*

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

### 🧠 Antigravity 內建模型策略指南 (您的強大武器庫)

這些模型是您在 Antigravity 介面中直接選用的推理大腦，根據專案進度，您可以靈活切換：

| 模型類別 | 推薦型號 | 專長領域 | 建議用途 |
|---|---|---|---|
| **最強除錯大腦** | **Claude Sonnet 4.6 (Thinking)** | **細膩邏輯與跨檔案關聯** | 遇到「明明沒改卻報錯」的靈異 Bug。 |
| **最強架構大腦** | **Gemini 3.1 Pro (High)** | **大規模重構與 1M Token 胃口** | 全專案架構調整、新增重大模組。 |
| **日常開發首選** | **Gemini 3.1 Pro (Low) / Flash** | **極速延遲與點數極低** | 語法諮詢、單一檔案小修小補。 |
| **開源替代方案** | **GPT-OSS 120B (Medium)** | **平衡性與多樣化** | 需要不同的 LLM 觀點進行交叉驗證。 |

---

### 🕒 點數刷新機制 (5 小時沙漏補點)

Antigravity 的點數是「滾動式」刷新的，不是每天定時歸零：

*   **5 小時滾動沙漏 (Rolling 5-Hour Units)**：
    *   **規則**：每一分鐘，系統會釋放回您「5 小時前」所消耗的點數。
    *   **特性**：若您剛進行過大工程，只需「休息 1-2 小時」，額度就會慢慢補回來。不必等到隔天！
*   **每週基礎上限 (Weekly Baseline)**：
    *   **重置時間**：每週固定重置一次。
    *   **特性**：長期消耗的底線，穩定使用的保證。

---

### 💡 開發建議與情境調度

*   **平時**：切換到 `Gemini 3.1 Pro (Low)` 或 `Gemini 3 Flash` 做基層建設。
*   **遇到瓶頸**：存檔後，切換到 `Claude Sonnet 4.6 (Thinking)` 專攻難點。
*   **緊急情況**：如果您配額用光了，可以跟我說，我會優先調整那些最節省點數的指令來幫您度過難關。

---

### 💡 專家節點密技 (省點數心法)

1.  **先規劃 (Planning)，後動手**：讓我先寫 `implementation_plan.md`，確認沒問題再叫我動工。這比讓我盲目嘗試要省下 **5 倍以上** 的點數。
2.  **平常開 `Low` / `Flash`**：這兩個模型幾乎扣不動點數，適合 90% 的開發環節。
3.  **大工程切 `High`**：當我們要動到整個 `analyzer/` 或 `scrapers/` 的底層時，再祭出頂尖大腦。

## 🛠️ 專案開發與維護

### 📋 專案健康檢查工具 (Health Check)
如果您在 IDE 左下角看到大量的紅叉叉或錯誤標示，請不要驚慌，那是 Linter 引擎的路徑偵測誤報。
請執行以下指令來驗證專案的「真實健康度」：

#### 🛠️ 執行方法
1. **開啟終端機**：在下方找到 **Terminal** 面板。
2. **輸入指令並執行**：

```powershell
py check_health.py
```

3. **等待結果**：約 1 秒鐘即可看到報告。

#### 📊 報告解讀指南
*   **✅ 恭喜！專案處於【完美健康】狀態**：代表程式語法 100% 正確。請**直接忽略左下角的所有紅字**，您可以放心執行程式或進行開發。
*   **❌ 警告：專案目前存有些微問題**：代表有檔案缺失或語法錯誤。請向上捲動查看標註 `[!!]` 的具體原因。
*   **⚠️ 出現 Unicode 亂碼**：代表您的終端機編碼設定特殊。若發生此情況，請截圖通知開發 AI，我會為您調整輸出格式。

### ⚙️ 其他操作
* **調整關鍵字**：於 `.env` 檔案中的 `SEARCH_KEYWORDS` 增加新英雄或活動名稱（用逗號分隔）。
* **新增爬蟲來源**：可於 `scrapers/` 目錄下繼承 `BaseScraper` 並實作 `scrape` 方法，最後於 `main.py` 內註冊即可彈性擴充系統！
* **報告樣板**：如果想修改視覺介面，請編輯 `reporter/templates/report.html`。
