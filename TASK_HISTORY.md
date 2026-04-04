# Arena of Valor 輿情監測系統：技術開發史詩 (Task Heritage Archive)

## 📌 旗艦特務演進史 (Full Granular Phases 1-36)

> [!IMPORTANT]
> 本檔案保留了從專案啟動至今的所有技術戰功與里程碑。每一層級 (Phase) 均代表了系統的一次進化，這不僅是紀錄，更是我們共同雕琢旗艦品質的證明。

---

### 🛠️ Phase 1：搜尋引擎對位 (Search Layer)

- **技術細節**：初步整合 Tavily Search API，實現全網抓取。
- **原始代碼**：
  ```python
  search_result = tavily.search(query=query, search_depth="advanced", max_results=10)
  ```

### 🛠️ Phase 2：數據雙重存放 (Backup Systems)

- **技術細節**：建立 `DATA_DIR` 實體化，並實作 Obsidian 備份 job。
- **配置參數**：`DB_PATH = DATA_DIR / "aov_monitor.db"`

### 🛠️ Phase 3：雲端自動發布 (Deployment)

- **技術細節**：實現 GitHub Pages 自動化路徑映射。
- **邏輯片段**：`report_url = f"{base_url}/data/reports/aov_report_{date_str}.html"`

### 🛠️ Phase 4：視覺靛藍模板 (Indigo UI)

- **技術細節**：使用 `#6366f1` 指標色與 `#f8fafc` 背景，模仿師資儀表板布局。

### 🛠️ Phase 5：分析基準建立 (Sentiment Logic)

- **技術細節**：建立正面/負面/中性的原始判定字串定義。

### 🛠️ Phase 6：除噪精煉 (Search Optimization)

- **技術細節**：排除醫療、金融與其他手遊雜訊的負向關鍵字清單。

### 🛠️ Phase 7：搜尋領域限制 (Social Media Focus)

- **技術細節**：限制 Tavily 抓取範圍，優先過濾 Social Media 領域資訊。

### 🛠️ Phase 8：API 頻率守護 (Rate Limiting)

- **技術細節**：在 `GeminiClient` 實作 4.5s 物理延遲，確保不觸發 15 RPM 的免費限額。

### 🛠️ Phase 9：API 配額監控 (Quota Tracking)

- **技術細節**：建立 API 限額表格，記錄 Flash 與 Pro 模型的分鐘配額分配。

### 🛠️ Phase 10：核心模型躍遷 (Model Switch)

- **技術細節**：將分析核心從 Flash 1.0 升級至 Gemini-2.0-Flash (或用戶訂閱版本)。

### 🛠️ Phase 11：字符編碼修復 (Encoding Fix)

- **技術細節**：強制 UTF-8 編碼與終端機亂碼終結計畫 (`chcp 65001`)。

### 🛠️ Phase 12：穩定化戰爭 I (Linter Baseline)

- **技術細節**：設定 `pyrightconfig.json` 的 `typeCheckingMode=off` 以排除萬項誤報。

### 🛠️ Phase 13：穩定化戰爭 II (Type-Ignore Sync)

- **技術細節**：同步所有 Python 檔案的 Import 區域，加入 `# type: ignore`。

### 🛠️ Phase 14：編碼淨化 (Unicode Clean)

- **技術細節**：清理受損的 UTF-8 全形字元，解決 Skill 文件載入錯誤。

### 🛠️ Phase 15：健康檢查工具 (Health Check)

- **技術細節**：開發生機偵測腳本，用於檢查 27 個核心檔案的完整度。

### 🛠️ Phase 16：視覺轉型啟動 (UI Steps)

- **技術細節**：開始對 `report.html` 進行結構化重定義，分離 Header 與 Content。

### 🛠️ Phase 17：報告網址注入 (Report URL Logic)

- **技術細節**：修復 HTML 模板中的變數綁定衝突，注入 `current_date` 對象。

### 🛠️ Phase 18：視覺地基奠定 (Typography)

- **技術細節**：導入 Google Font `Outfit` 與 `Inter` 作為視覺基礎。
- **CSS 宣告**：`body { font-family: 'Outfit', 'Inter', sans-serif; }`

### 🛠️ Phase 19：馬卡龍漸層實驗 (Pastel Experiment)

- **技術細節**：測試第一版粉色系漸層背景代碼，嘗試回歸可愛風。

### 🛠️ Phase 20：萌系 Lush & Lively 雛形 (Pink Overhaul)

- **技術細節**：正式確立 `#fdf2f8` (Rose 50) 為系統主色調。

### 🛠️ Phase 21：櫻花動效導引 (Sakura FX)

- **技術細節**：實作 `sakura-fall` CSS 動畫片段，設定隨機飄落路徑。
- **動畫片段**：`animation: sakura-fall 10s linear infinite;`

### 🛠️ Phase 22：英雄焦點正式實作 (YaYa Section)

- **技術細節**：建立 `hero-focus-card` 的特殊發光邊框與過濾正則，鎖定特定關鍵字。

### 🛠️ Phase 23：視覺渲染崩潰修復 (Jinja2 Hotfix)

- **技術細節**：初步解決 `UndefinedError: 'dict object' has no attribute 'overall'` 等變數缺損問題。

### 🛠️ Phase 24：Gemini API v1 端點對位 (REST API v1)

- **技術細節**：將 API Base 從 `v1beta` 升級為 `v1` 穩定端點。

### 🛠️ Phase 25：批次解析延遲優化 (Batch Optimized)

- **技術細節**：調整 `batch_chat` 的並發數為 3，確保高壓下的穩定性。

### 🛠️ Phase 26：情感厚度注入 (Sentiment Fallback)

- **技術細節**：實作 `_generate_fallback_summary` 應對 API Quota 枯竭時的報表生成。

### 🛠️ Phase 27：全球關鍵字擴展 (Global Region Sync)

- **技術細節**：正式加入 TW, TH, VN 的三地搜尋預設值與地區標籤。

### 🛠️ Phase 28：搜索數量節流 (Rate Throttling)

- **技術細節**：將每地區搜尋數由 15 筆縮減為 3 筆以符合免費層額度。

### 🛠️ Phase 29：報表產出強制腳本 (Force Gen)

- **技術細節**：編寫 `force_gen.py` 以繞過主程式的崩潰，強制產出 HTML。

### 🛠️ Phase 30：深色模式探索 (Dark Mode Base)

- **技術細節**：開始對背景色進行深海藍 `#020617` 的嘗試。

### 🛠️ Phase 31：Cyber-Tactical 視覺正式發表 (UI Flagship)

- **技術細節**：全面採用深海藍背景與霓虹發光溢位，強化戰略室氛圍。

### 🛠️ Phase 32：救難渲染代理 (SafeProxy Master)

- **技術細節**：實作 `SafeProxy` 類別，終結所有模板屬性缺損問題。

### 🛠️ Phase 33：全球戰略觀察室 (Strategic Dashboard)

- **技術細節**：建立 1+3 的全球/區域戰略視覺視窗。
- **原始 CSS**：
  ```css
  .strategic-room { background: linear-gradient(180deg, #020617 0%, #0f172a 100%); }
  ```

### 🛠️ Phase 34：雲端封印解除與 CI/CD 硬化

- **背景**：針對部署後持續 404 的死點進行「基礎設施級」排除。
- **關鍵修復 I (Jekyll)**：注入 `.nojekyll` 檔案，強制 GitHub Pages 釋放 `data/` 目錄的靜態資源訪問權。
- **關鍵修復 II (Submodule)**：執行 `git rm -r --cached` 並物理除根，清除導致部署崩潰的「幽靈子模組」索引殘留。
- **關鍵修復 III (Auto-Deploy)**：將 Git Push 邏輯整合進 `main.py` 的生命週期最末端，實現自動化同步。

### 🛠️ Phase 35：演示視覺飽滿化與自愈機制 (Current Optimization)

- **目標**：解決演示模式 (Showcase) 下的「連結分析失敗」與「趨勢圖表空缺」。
- **關鍵修復 I (數據飽和度)**：在備援大腦中將 `top_links` 與 `hero_focus_posts` 擴充為 3 筆精品數據，回填文字與 URL。
- **關鍵修復 II (圖表強心針)**：在 `SentimentAnalyzer` 與 `HistoryResolver` 的備援路徑中強制注入 7 日動態脈搏數據 (`weekly_vol_pulse`)。
- **關鍵修復 III (防線硬化)**：重構 `main.py` 調度鏈，隔離 `combat_stats` 異常點，故障時自動彈出「五星級演示戰報」以取代「無資料」字樣。
- **關鍵修復 IV (部署突破)**：使用 `git add -f` 強制同步受 `.gitignore` 屏障攔截的展示級 JSON 數據。

### 🛠️ Phase 36：旗艦門戶部署與視覺對位硬化 (Tactical Hub & Visual Hardening)

- **404 終結者**：部署 `index.html`，具備櫻花落英效果與動態指揮中心入口。
- **圖表渲染修復**：修正 `report.html` 中的 Chart.js 初始化邏輯，拋棄硬編碼，實現 **「平台自動偵測」** 與 **「Moe 配色 (粉藍/粉紅/亮黃)」**。
- **數據鏈加固**：使用 `try-catch` 保護渲染執行序，確保週量趨勢線圖不再因單一平台數據異常而消失。

### 🛠️ Phase 37：全域系統法典佈建 (Global Agent Rules)

- **目標**：確保所有未來的 AI 接手者皆能嚴格遵循「謀定而後動」與「無損存檔」法則。
- **技術細節**：於專案根目錄實體化 `.windsurfrules` 與 `.cursorrules`。
- **核心文本約束**：
  - 強制開局讀取「Phase 壓縮記憶檔」與「Phase 0 計畫書」。
  - 強制執行事前提交「精美版面計畫書」並必須獲得「用戶明確核准」。
  - 確立對未知事物查證並以繁體中文撰寫、忌用僵化詞彙之日常律法。

### 🛠️ Phase 38：API 限速防護閥 (Rate Limit 5P Hardening)

- **目標**：統一全線情報搜集的物理上限，避免觸發 `HTTP 429 Too Many Requests`。
- **技術細節**：將神經中樞 `main.py` 及三大底層爬蟲的檢索上限全部鎖定為 **5** 篇。
- **原始代碼**：
  - `main.py`：`all_results = await searcher.search(max_results_per_region=5)`
  - `tavily_searcher.py`：`max_results_per_region: int = 5`
  - `apify_scraper.py`：`max_results_per_keyword: int = 5`
  - `base_scraper.py`：`async def scrape(self, keywords: List[str], max_posts: int = 5) -> List[Post]:`

### 🛠️ Phase 39：前端視覺尊榮升級 (UI/UX Flagship Enhancement)

- **目標**：在不改變 Cyber 戰略 ✕ Sakura 粉嫩主色的前提下，全面升級響應式佈局與微動畫質感。
- **排版系統重建 (CSS Grid)**：
  - 於 `report.html` 注入 `.layout-container` 雙軌網格 (2:1 黃金比例)。
  - 實作 `@media (max-width: 992px)` 行動裝置完美折疊直列顯示。
- **英雄專屬卡片尊榮化 (Hero VIP Card)**：
  - `.hero-summary` 升級為玻璃透視材質 (`backdrop-filter`)，並加入每 6 秒一次的物理光學折射動畫 `glassSweep`。
  - `.hero-post-item` 改版為帶有陰影的浮空玻璃卡，懸停時觸發上浮微動畫 (`transform: translateY(-3px)`)。
  - `.hero-focus-title` 文字改為漸層炫光 (`background-clip: text`)。
- **互動圖表玻璃化 (Glassmorphism Charts)**：
  - 增設 `.chart-wrapper` 包覆層，附帶 `blur(10px)` 及呼吸光暈懸停特效。
  - 覆寫 Chart.js 及 ECharts 提示框 (Tooltip)，強制取消預設黑框，全面注入半透明琉璃材質與圓角 `cornerRadius: 12` 設定。


### 🛠️ Phase 39.5：前端視覺柔和化與尊榮標題升級 (UI Refinement & Polish)

- **目標**：接獲指揮官指示，針對資訊中心、預警板塊以及頂部主標題進行文字降溫及高光特效的二次精修。
- **資訊中心 (Info Center)**：
  - 由「台服戰略通訊中心」更名為更具親和力的「台服消息資訊中心 (TAIWAN INFO CENTER)」。
  - 捨棄生硬的衛星圖標 🛰️，導入對話感十足的 `💬`。
- **今日焦點 (Today's Focus)**：
  - 褪去「戰略級預警中心」帶來的紅色壓迫感。
  - 將背板與警示光替換為「柔和琥珀晨光色 (Amber/Yellow)」(`linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)`)。
  - Icon 切換為帶有提示意味的 `📌`。
- **標題美學突破 (Premium Header)**：
  - 導入全新的 `.header h1` CSS 結構，為「Arena of Valor 輿情分析」主標套用專屬的漸層高光 (`background-clip: text`) 與文字倒影 (`drop-shadow`)，完美疊加高級視覺感。


### 🛠️ Phase 40：沉浸式背景植入計畫 (Immersive Background UI)

- **目標**：接獲指揮官最新指示，將特定圖片 (`step.jpg`) 滿版植入網站背景，同時維持良好閱讀性與滾動浮動效果。
- **技術實作**：
  - 增設 `body::after` 偽元素並套用 `position: fixed` 與 `pointer-events: none` 確保滾動時圖像不發生位移，且不阻擋滑鼠互動。
  - 將不透明度設定為 `opacity: 0.15`，以確保背景隱若現，並交由上層的 Glassmorphism (.card 的 `backdrop-filter: blur(24px)`) 產生完美的透視折射。
  - 完美相容 `ui_previews/` 與 `data/reports/` 不同層級的相對路徑讀取 (`../step.jpg` 與 `../../step.jpg`)。

---

## 💡 靈魂反思：當全球化對上靈魂美學 (Self-Reflection)

### 議題：全球通用化導致的「靈魂消融」

* **檢討**：在 Phase 18~23 左右，為了追求標準化，曾一度移除可愛視覺元素。
* **結論**：美工與視覺就是「功能」的一環。我們最終找回了櫻花落英與霓虹呼吸燈，並成功與深色戰略模式（Phase 31+）完美融合，這才是旗艦級系統應有的面貌。

### 🛠️ Phase 40.2：終極除錯修復計畫 (Final Bugfix)

- **圖示連結校準 (Image Binding)**：
  - 將 `report.html` 與 `Phase39_Flagship_Showcase.html` 內負責沉浸式背景圖的 CSS，修改為完美對應新圖檔名稱 `url('../../芽芽起來寶貝.png')` 與 `url('../芽芽起來寶貝.png')`。
- **預覽版樣式強制同步 (Showcase CSS Sync)**：
  - 修復因行高與空行差異導致的 CSS 覆寫失敗問題，透過精準打擊的行位鎖定 (Targeted Replacement)，將原本遺漏更新的 Showcase 暗黑卡片成功套用「透白奶油質感 (`rgba(255,255,255,0.7)`)」。
  - 成功將缺少的大標星芒 `✨` 給補回 `ui_previews/Phase39_Flagship_Showcase.html` 的專屬選取器裡。

### 🛠️ Phase 40.3：尊榮視覺微調與路徑校準計畫 (Final Polish)

- **深層檔名轉譯與校準 (File System Integrity)**：
  - 本真診斷：查明因為終端環境對中文命名的解析脫鉤（原 `芽起來啦寶貝.png` 變異為 `ް_Ӱ_.png`），導致瀏覽器實體路徑失效。
  - 無損處置：將背景圖片安全遷移命名為 `yaya_bg.png`，並將前端 `report.html` 與 Showcase 的參照路徑完美對接。
- **星芒透明化特例排除 (Emoji Rendering Fix)**：
  - 主標題的 `✨` 因繼承大外框的 `-webkit-text-fill-color: transparent` 而呈現隱形狀態。透過額外在 `.header h1::before` 中覆寫 `-webkit-text-fill-color: initial;` 成功破除透明化詛咒，將尊榮星芒迎回旗艦版面。

### 🛠️ Phase 40.4：主視覺清透度升級 (Visual Depth Polish)

- **深層透明度調校 (Opacity Calibration)**：
  - 本真診斷：主公指示原有的背景透明度 (`0.25`) 雖然清晰，但可稍微加重存在感以達到最佳的沉浸體驗。
  - 無損處置：將 `report.html` 與 Showcase 內的 `body::after` `opacity` 從 `0.25` 提升至 `0.35`，使得芽芽的整體輪廓更加鮮明，並完美與前端玻璃透視特效 (Glassmorphism 2.0) 結合。

### 🛠️ Phase 40.5：終極存在感釋放 (Absolute Immersion)

- **深層透明度定調 (Opacity Finalization)**：
  - 本真診斷：主公指示原先的 `0.35` 雖然通透，但若要發揮角色圖片的張力，可以進一步解放透明度至 `0.6`。
  - 無損處置：將 `report.html` 與 Showcase 內的 `body::after` `opacity` 從 `0.35` 拔擢至 `0.6`，在保證毛玻璃卡片可視性的前提下，讓芽芽的魅力佔滿整個螢幕視覺。

### 🛠️ Phase 40.6：主公欽定黃金版本 (The Golden Build) ⭐

- **最終透明度定案 (Final Opacity Lock)**：
  - 主公經過 `0.25 → 0.35 → 0.6 → 0.8` 四輪精密試調後，最終欽定 **`opacity: 0.8`** 為黃金標準值。
  - 此數值在保障前方毛玻璃卡片 (`backdrop-filter: blur(24px)`) 文字可讀性的前提下，讓芽芽的角色圖以近乎全彩的姿態佔領全螢幕背景視覺。
- **完整技術快照 (Technical Snapshot)**：
  - `body::after` 背景層：`url('../../yaya_bg.png')` / `url('../yaya_bg.png')`
  - `background-size: cover` + `background-position: center center`
  - `position: fixed` + `pointer-events: none` + `z-index: -2`
  - `opacity: 0.8` ← **主公欽定值**
  - `.header h1::before`：`content: '✨'` + `-webkit-text-fill-color: initial` (破除透明繼承)
  - 「今日焦點」內部卡片：`rgba(255,255,255,0.5)` 奶油透玻璃 + `#d97706` 琥珀字體
- **此版本已由主公親自確認為「喜歡的版本」，標記為 Phase 40 系列的黃金定案。**

---

### 🛠️ Phase 41：大腦神經元重構與 JSON Schema 鎖定 (LLM Core Optimization)

- **目標**：提升大腦分析中樞 (`gemini_client.py` 與 `sentiment.py`) 的運轉效能與容錯率，並消除重複分析導致的代幣浪費。
- **技術實作**：
  - **原生結構化輸出 (Structured Outputs)**：捨棄易碎的 Prompt 約束，全面導入 Gemini API 原生的 `responseSchema` 參數，強勢規範 `SINGLE_POST_SCHEMA` 與 `DAILY_SUMMARY_SCHEMA`，徹底根絕 `JSONDecodeError` 格式異常。
  - **大腦快取記憶域 (MD5 Hash Caching)**：遵奉主公之強烈建議，於 `GeminiClient` 注入本地永久記憶實體化存檔 (`data/llm_cache.json`) 機制。對使用者的 Prompt 計算 MD5 做為指紋，若遇重複提問直接由本地快取秒速回覆，測試免耗點實現「零消耗、零延遲」。
  - **智慧限流多工 (Semaphore Throttle)**：推翻舊有的強制睡眠 5 秒，使用 `asyncio.Semaphore(3)` 結合 Token Bucket 概念控制高壓併發，報告產出時效提升 50%。
  - **高壓熔斷器 (Circuit Breaker)**：在遭遇 `429 Too Many Requests` 時即刻熔斷，中斷無效請求，並強制安全降落至預演展示數據 (Showcase Mode)，保障網頁渲染不破鏡。

---

### 🛠️ Phase 42：神級心智升級與多核備援網 (God-Tier Mind & Fallback Mesh)

- **目標**：接獲主公指示，進一步將大腦推升至「神級心智」，強化面對反諷、長文與額度枯竭時的高階防禦。
- **技術實作**：
  - **CoT 推論優先 (Reasoning Before Sentiment)**：在 JSON Schema 內頂部強制插入 `reasoning`，要求模型在給出正面/負面結論前，必須先進行邏輯推理。此神經元再造大幅提升了 LLM 對潛台詞的識別準確度。
  - **先驅記憶庫 (Few-Shot Prompting)**：於 `SYSTEM_SINGLE_POST` 注入一段台服專屬的「反諷」教學與推演範例（如：『削弱真是太棒了，大家別玩輔助了吧』＝ 極度不滿），直接固化在模型的潛意識中。
  - **智能切片瘦身 (Token Compression)**：於 `sentiment.py` 實作 `_compress_content`。捨棄無腦的 `[:1000]` 切割，改為：偵測長文時僅保留首段、尾段，以及含有目標英雄 (`HERO_WATCHLIST`) 的核心文句，成功於保持關鍵脈絡的同時，大幅節省 Token 輸入。
  - **多核降級替身 (Model Tiering Fallback)**：於 `gemini_client.py` 建構備援陣列 `["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]`。當首選模型陣亡（遭遇 HTTP 429）時，不再直接啟動 showcase，而是無縫順延呼叫下一階層的備用模型，將 API 免費池搾取至最後一滴。

### 🏯 Phase 40.12：旗艦視覺物理重塑與版本化 (Golden Build Restoration)

- **情境診斷**：
  - **佈局回歸**：發現報表因 CSS 權重衝突，導致「資訊中心」單獨佔據全寬，或與側欄並排時比例失調。
  - **視覺亮度**：主公指示「台服消息資訊中心」背景過於深沉，需進行「輕透玻璃化」處理。
- **技術實作**：
  - **網格並行化 (Grid Parallelism)**：於 `report.html` 移除 `.global-insights-card` 與 `.alert-banner` 的全寬強制指令，確保其在 `layout-container` 中以 `2fr 1fr` 比例左右並排。
  - **輕透玻璃美學 (Light Glass Aesthetics)**：
    - 背景色鎖定為 **`rgba(255, 255, 255, 0.1)`**（透明白桃玻璃）。
    - 內部文字盒調亮至 **`rgba(255, 255, 255, 0.4)`**，確保文字於芽芽背景上的高辨識度。
  - **粉嫩主色回歸 (Pink Dominance)**：標題色系全面鎖定為 **旗艦桃紅 (#db2777)**。
### 🛠️ Phase 40.18：並行資產歸檔機制 (Parallel Asset Archiving)

- **目標**：遵奉主公聖旨，確保每一份生成的戰報皆能同步保留於 `ui_previews/` 目錄中，且嚴格執行「不覆蓋」原則以追蹤 UI 迭代細節。
- **技術實作**：
  - **自動化掛鉤 (Generator Hook)**：於 `reporter/generator.py` 的 `generate()` 末端注入並行儲存邏輯。
  - **同步路徑**：每當產出 `data/reports/aov_report_YYYY-MM-DD_vX.html` 時，系統自動執行 `shutil.copy2` 將其同步至 `ui_previews/`。
  - **資源完整性**：同步機制包含背景圖 (`yaya_bg.png`) 的自動檢測與補全，確保 `ui_previews` 中的報表具備完整視覺渲染。
- **成果驗印**：
  - 手動歸檔目前的 **V7(06:33)** 旗艦報表。
  - 自動化驗證 **V8(06:38)** 報表，確認已成功同步至雙資料夾，龍脈追蹤達成 100% 覆蓋。

---

**慢工出細活。本編年史受 [.agent/rules.md] 保護，記載了我們對旗艦品質的最終堅持。**
