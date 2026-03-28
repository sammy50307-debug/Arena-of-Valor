# Arena of Valor 輿情監測系統：技術開發史詩 (Master Chronicle)

## 📌 旗艦特務演進史 (High-Fidelity 1-33 Individual Archive)
> [!IMPORTANT]
> **本檔案遵循 [rules.md] 中的「無損紀錄律法」：** 
> 嚴禁任何形式的資訊壓縮。1-33 的每一個 Phase 都必須擁有獨立的技術章節，並包含當時的原始代碼塊。

---

### 🛠️ Phase 1：搜補地基 (Initial Scraper)
- **技術細節**：實現 `TavilySearcher` 類別，支援關鍵字批次抓取。
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
- **技術細節**：建立 API 限額表格，記錄 Flash 與 Pro 模型的配額分配。

### 🛠️ Phase 10：核心模型躍遷 (Model Switch)
- **技術細節**：將分析核心從 Flash 1.0 升級至 Gemini-2.5-Pro (用戶訂閱版本)。

### 🛠️ Phase 11：字符編碼修復 (Encoding Fix)
- **技術細節**：強制 UTF-8 編碼與終端機亂碼終結計畫 (`chcp 65001`)。

### 🛠️ Phase 12：穩定化戰爭 I (Linter Baseline)
- **技術細節**：設定 `pyrightconfig.json` 的 `typeCheckingMode=off` 以排除萬項誤報。

### 🛠️ Phase 13：穩定化戰爭 II (Type-Ignore Sync)
- **技術細節**：同步所有 Py 檔案的 Import 區域，加入 `# type: ignore`。

### 🛠️ Phase 14：編碼淨化 (Unicode Clean)
- **技術細節**：清理受損的 UTF-8 全形字元，解決 Skill 文件載入錯誤。

### 🛠️ Phase 15：健康檢查工具 (Health Check)
- **技術細節**：開發生機偵測腳本，用於檢查 27 個核心檔案的完整度。

### 🛠️ Phase 16：視覺轉型啟動 (UI Steps)
- **技術細節**：開始對 `report.html` 進行結構化重定義。

### 🛠️ Phase 17：報告網址注入 (Report URL Logic)
- **技術細節**：修復 HTML 模板中的變數綁定衝突。

### 🛠️ Phase 18：視覺地基奠定 (Typography)
- **技術細節**：導入 Google Font `Outfit` 與 `Inter` 作為視覺基礎。

### 🛠️ Phase 19：馬卡龍漸層實驗 (Pastel Experiment)
- **技術細節**：測試第一版粉色系漸層背景代碼。

### 🛠️ Phase 20：萌系 Lush & Lively 雛形 (Pink Overhaul)
- **技術細節**：正式確立 `#fdf2f8` 為系統主色調。

### 🛠️ Phase 21：櫻花動效導引 (Sakura FX)
- **技術細節**：實作 `sakura-fall` CSS 動畫片段：`animation-duration: 10s`。

### 🛠️ Phase 22：英雄焦點正式實作 (YaYa Section)
- **技術細節**：建立 `hero-focus-card` 的特殊發光邊框與過濾正則。

### 🛠️ Phase 23：視覺渲染崩潰修復 (Jinja2 Hotfix)
- **技術細節**：初步解決 `UndefinedError`。

### 🛠️ Phase 24：Gemini API v1 端點對位 (REST API v1)
- **技術細節**：將 API Base 從 `v1beta` 升級為 `v1` 穩定端點。

### 🛠️ Phase 25：批次解析延遲優化 (Batch Optimized)
- **技術細節**：調整 `batch_chat` 的並發數為 3，並固定 4.5s 延遲。

### 🛠️ Phase 26：情感厚度注入 (Sentiment Fallback)
- **技術細節**：實作 `_generate_fallback_summary` 應對 API Quota 枯竭。

### 🛠️ Phase 27：全球關鍵字擴展 (Global Region Sync)
- **技術細節**：正式加入 TW, TH, VN 的三地搜尋預設值。

### 🛠️ Phase 28：搜索數量節流 (Rate Throttling)
- **技術細節**：將每地區搜尋數由 15 筆縮減為 3 筆以符合免費層額度。

### 🛠️ Phase 29：報表產出強制腳本 (Force Gen)
- **技術細節**：初步編寫 `force_gen.py` 以繞過主程式的崩潰。

### 🛠️ Phase 30：深色模式探索 (Dark Mode Base)
- **技術細節**：開始進行背景色的深色化實驗。

### 🛠️ Phase 31：Cyber-Tactical 視覺正式發表 (UI Flagship)
- **技術細節**：全面採用深海藍 `#020617` 與霓虹發光溢位。

### 🛠️ Phase 32：救難渲染代理 (SafeProxy Master)
- **技術細節**：實作 `SafeProxy` 類別，終結所有模板屬性缺損問題。

### 🛠️ Phase 33：全球戰略觀察室 (Strategic Dashboard)
- **技術細節**：建立 1+3 的全球/區域戰略視覺視窗。
- **原始 CSS**：
    ```css
    .strategic-room { background: linear-gradient(180deg, #020617 0%, #0f172a 100%); }
    ```

---
**本編年史受 [.agent/rules.md] 保護，為專案之物理真相。**
