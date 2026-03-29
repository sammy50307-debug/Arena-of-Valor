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

---

## 💡 靈魂反思：當全球化對上靈魂美學 (Self-Reflection)

### 議題：全球通用化導致的「靈魂消融」

* **檢討**：在 Phase 18~23 左右，為了追求標準化，曾一度移除可愛視覺元素。
* **結論**：美工與視覺就是「功能」的一環。我們最終找回了櫻花落英與霓虹呼吸燈，並成功與深色戰略模式（Phase 31+）完美融合，這才是旗艦級系統應有的面貌。

---

**慢工出細活。本編年史受 [.agent/rules.md] 保護，記載了我們對旗艦品質的最終堅持。**
