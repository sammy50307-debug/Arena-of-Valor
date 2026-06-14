# Phase 118 — 整站重設計 ①設計系統地基（芽芽品牌色 + 儀表板結構，用 ui-ux-pro-max）（草案 v1，待阿喜核准）

> 狀態：**v1 已凍結（2026-06-15，阿喜核准飛輪版 + lint M1/M2 PASS；交接下個視窗執行）**
> 戰線：**前端 / UX（設計系統）+ 治理/測試（防復發強制層）**——整站重設計 4-Phase 計畫（P118 地基 → P119 報告視覺+token-lint上線 → P120 響應式/LINE/A11y → P121 Landing）的第一棒。
> 美學方向（阿喜 2026-06-15 拍板）：**混搭——保留「芽芽」粉櫻品牌色 + 吉祥物識別，採儀表板的清晰結構/資訊層級/專業間距。**
>
> **🌀 飛輪升級（阿喜 2026-06-15「直接飛輪優化」核准）**：原 P118-121 是「重漆一次」的穩修，會再飄。飛輪版加**防復發脊椎**，讓設計系統成為 machine-enforced 契約：
> - **tokens 為唯一真相源**：`design-system/tokens.css` 是全站色/間距/字級的單一來源，report.html/index.html 一律 `var(--token)`，禁硬編碼。
> - **token-lint 進 gov.preflight（復用 P117 總指揮）**：`scripts/check_design_tokens.py` flag report.html/index.html 的硬編碼 `#hex`/任意 px → 註冊進 gov.preflight `full` profile（**P119 上線、advisory**）。設計債硬編碼 re-creep 自動被擋（解今天 #1/#2/#3 無聲累積的根因）。
> - **preview-driven 可重複視覺驗證**：P119-121 用 `preview_*` 工具 render→截圖 375/768/1440 + LINE WebView UA，取代一次性肉眼。
> - **反膨脹（停損）**：不做 component-partial 大重構（架構層、0 需求）；不做重型 Playwright visual-regression CI（單人專案 ROI 不足）；token-lint 先 advisory。
> 鐵律：`py` 不用 `python`；TASK_HISTORY 禁全讀；改動前計畫書等同意；push 前問阿喜；**P118 不動 live report.html / index.html / generate()（純地基 + sandbox mockup，零管線風險）**。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P118（整站重設計 1/4）|
| **Phase 名稱** | 設計系統地基 + mockup 定案 |
| **影響半徑** | **標準（新增 design-system/ 數檔 + sandbox mockup；不動 live 模板）─ META3** |
| **預估投入** | 3-5 h |
| **負責模型** | Opus 4.8（設計系統決策 + 品牌色保留 + ui-ux-pro-max 整合）|
| **後續 Phase** | P119 報告視覺重構 / P120 響應式+LINE+A11y / P121 Landing（各自凍結計畫書）|

---

## 1. 目標 (Objective)

用 **ui-ux-pro-max** 為「芽芽品牌色 + 儀表板結構」產出一套**可落地的設計系統**，並在**動 live 模板之前**先以 sandbox mockup 取得阿喜的 LOOK 定案：

1. `search.py --design-system --persist` 產出 `design-system/MASTER.md`（pattern/style/color/typography/effects + anti-patterns）。
2. **保留芽芽品牌色**（從 report.html `:root` 萃取現值：粉 `#be185d`/`#db2777`、粉→薄荷漸層 `#fdf2f8→#f0fdf4`、glass 半透白+粉邊、mint `#10b981`、sakura），與 ui-ux-pro-max 的儀表板結構/間距/字體規範**融合**，產出 `design-system/tokens.css`（color / type-scale / spacing-scale / radii / shadow / z-index 一套 CSS 變數）。
3. 產出 `design-system/mockup.html`（**獨立 sandbox、非 live 報告**），用真實元件形狀（區塊卡片 + 真實熱詞統計 + 文章 feed/滾輪）展示新設計，給阿喜定案。

量化：產出 1 套設計 tokens + 1 份 MASTER 設計系統 + 1 個可視 mockup；阿喜簽核 LOOK 後才進 P119。

## 2. 觸發背景 (Why Now)

跨專案盤點揭露 AOV 從未用過 ui-ux-pro-max（網站設計全靠手刻、累積 #1/#2/#3 等 UX 債）。skill 已修復+註冊。阿喜決定整站用 ui-ux-pro-max 重設計，定案混搭方向。設計系統是地基——**先定 tokens + LOOK，後續 3 Phase 才有一致依據**，避免邊改邊飄。

## 3. Entry Criteria

- [x] ui-ux-pro-max 已修復可用（P-fix 3ba25b2，search.py --design-system 正常輸出）
- [x] 美學方向已定（混搭：芽芽品牌色 + 儀表板結構）
- [x] 現有芽芽品牌色已萃取（report.html :root）
- [ ] **驗證盲區群（B-023/024/027）**：本 Phase 不動 live 模板，但 mockup 須用「真實元件形狀/變數」對齊 report.html 結構，避免 mockup 美但套不進真模板。
- [ ] 阿喜核准本計畫書凍結

## 4. Exit Criteria

- [ ] **A**：`design-system/MASTER.md`（ui-ux-pro-max --persist 產出 + 芽芽品牌 override 區段）
- [ ] **B**：`design-system/tokens.css`——一套 CSS 變數：色票（芽芽粉系 primary + 儀表板中性灰階 + 語意色 pos/neg/neu + glass）、type-scale（字級階梯）、spacing-scale（4/8px 基準間距階梯，解 #3 鬆散/貼太近根因）、radii、shadow、z-index
- [ ] **C**：`design-system/mockup.html`——獨立 sandbox（**不依賴 generate()**），呈現新設計的 3 個關鍵元件：(1) 區塊卡片（header+content）(2) 真實熱詞統計區（含 #1 連結態的視覺處理）(3) 文章 feed + 滾輪詳情（含 #3 呼吸空間）。用真實資料形狀的假資料。
- [ ] **D（阿喜定案）**：阿喜看 mockup 截圖簽核 LOOK；不滿意則迭代 mockup（不進 P119）
- [ ] **E**：tokens 與品牌色一致性自檢（萃取的芽芽色值有出現在 tokens.css）；mockup 元件結構對齊 report.html 既有 Jinja 區塊（為 P119 鋪路）
- [ ] **F**：收官件套（TASK_HISTORY + memory）+ P119 計畫書預告

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 3-5 h |
| 收益等級 | **高**（整站重設計的地基；先 mockup 定案＝後續 3 Phase 零返工的關鍵；首次真正用 ui-ux-pro-max）|
| ROI | ✅ 高（地基一次定對，省掉「在 live 報告上反覆試錯」的代價；品牌色保留＝零品牌風險）|

---

## 6. 17 層稽核表 ─ META2

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | tokens.css（CSS 變數）+ mockup.html（靜態）；不動 live 模板 | tokens 命名/結構難維護 | 用語意化變數名 + 對齊 ui-ux-pro-max MASTER；mockup 純靜態無邏輯 |
| **2. 邏輯** | 設計系統＝宣告式 tokens，無業務邏輯 | N/A | 純樣式層 |
| **4. 測試** | mockup 視覺定案（人工）+ tokens 一致性自檢 | 視覺無法單元測 | mockup 截圖人工簽核（X4-J 設計類本就人工）；品牌色出現自檢可機械驗 |
| **10. 安全** | 純前端靜態，零後端/機敏/外呼 | mockup 引外部 CDN 字體？ | 字體用 Google Fonts（既有作法）；不引入未知第三方資源 |

### A 級（提示填）
| 層 | 採用/N-A | 風險 | 緩解 |
|---|---|---|---|
| **3. 架構** | design-system/ 集中管理 tokens（單一真相源），後續 Phase 引用 | tokens 與 live CSS 雙軌漂移 | P119 把 report.html 改成引用 tokens；P118 先建源 |
| **9. UX（核心）** | ui-ux-pro-max 設計系統 + Pre-Delivery Checklist；spacing-scale 解 #3 根因 | 設計脫離真實內容 | mockup 用真實元件形狀；對齊 report.html 結構 |
| **13. 可維護性** | tokens 集中 + MASTER 文件化 | 接手者不懂 tokens | MASTER.md 寫明每個 token 用途 + 芽芽 override 理由 |
| **14. 文件** | 計畫書 + MASTER.md + TASK_HISTORY + memory | — | 收官件套 |
| **15. 流程** | 整站重設計 4-Phase 第一棒；mockup gate | — | 每 Phase 凍結計畫書 + 阿喜核准 |

### B 級（條件式）
| 層 | 觸發 | 採用 | 風險 | 緩解 |
|---|---|---|---|---|
| **17. i18n** | 報告繁中 | tokens 對中文字體/行高友善 | 字體配對偏英文 | typography token 含中文 fallback（思源/Noto） |
| **8 效能/11 部署/12 成本/16 隱私** | 未觸發（P118 不動 live/CI）| — | — | N/A |

### 層級互鎖 ─ META5
- [x] UX→Documentation（設計系統動 UX→文件）｜[x] Architecture→Documentation｜[ ] Logic→Testing N/A（無邏輯）

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| 新增 design-system/（MASTER/tokens/mockup）| 完全可逆（純新增，不動 live）| git rm |
| ui-ux-pro-max --persist 寫 design-system/ | 可逆 | — |

### X2 盲區掃描
- [x] mockup 美但套不進真模板 → mockup 用 report.html 真實元件結構/Jinja 區塊形狀
- [x] tokens 與既有 live CSS 衝突 → P118 只建源不套用；P119 才整合（屆時驗）
- [x] 品牌色被 ui-ux-pro-max 推薦色蓋掉 → 萃取現值 + override 區段強制保留

### X3 時間敏感性
- 草案 2026-06-15；設計系統定案後，後續 P119-121 以此為唯一依據；ui-ux-pro-max 為快照（升級需重產 MASTER）

### X4 多角度審查
- **主公**：阿喜要整站專業化但保芽芽識別。混搭＝品牌色留、結構升級。mockup 先定案降風險。
- **紅隊**：見 M2。
- **接手者**：tokens.css 單一真相源 + MASTER.md 寫明每 token 用途；後續 Phase 引用不重造。
- **X4-J 自動化邊界**：ui-ux-pro-max 為設計顧問（規則型啟發式，召回率僅供參考）；最終 LOOK 由阿喜人工簽核，非 skill 拍板。
- **X4-K 使用者端審查官**：明告「P118 只產設計系統 + mockup，live 報告尚未變；報告外觀改變在 P119 才上線」。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| RP1 | mockup 定案了但 P119 套進真模板才發現結構套不上 | 中 | 中 | UX | mockup 用 report.html 真實 Jinja 區塊結構/元件形狀，非憑空設計 |
| RP2 | ui-ux-pro-max 推薦色/風格蓋掉芽芽品牌識別 | 中 | 中 | 設計 | 萃取現有品牌色 + tokens.css 設 override 區段強制保留粉櫻/sakura/mint |
| RP3 | spacing/type tokens 訂太細碎、後續難一致套用 | 低 | 低 | 可維護 | 用標準 4/8px spacing scale + 有限字級階梯（非任意值）|
| RP4 | 設計脫離真實內容（資料密度/中文長度）| 中 | 低 | UX | mockup 用真實資料形狀（長中文標題、真實熱詞數）壓測版面 |
| RP5 | 範圍蔓延到改 live 模板（越界 P119）| 中 | 中 | 流程 | P118 Exit 明定不動 live；只 design-system/ + mockup |

**META4 加權**：無 S 級高風險（P118 不動 live/CI/後端）。<5，無須請示（阿喜已核准方向）。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 驗收 |
|---|---|---|
| **S1 設計系統產出** | `ui-ux-pro-max search.py --design-system --persist`（混搭關鍵字）→ MASTER.md；萃取 report.html 現有品牌色；查 --domain style/typography/ux 補細節（間距/字體/卡片）| MASTER.md 產出 + 品牌色清單 |
| **S2 tokens 定義** | `design-system/tokens.css`——融合芽芽品牌色 + 儀表板中性階 + spacing/type/radii/shadow scale（Ultracode：可並行 judge panel 產 2-3 token 方向→評分→綜合）| tokens.css + 品牌色一致性自檢 |
| **S3 mockup** | `design-system/mockup.html` 獨立 sandbox，3 關鍵元件（卡片/熱詞/feed+滾輪）套 tokens，真實資料形狀 | mockup 可開、結構對齊 report.html |
| **S4 定案** | 截圖給阿喜簽核 LOOK；不滿意迭代 | 阿喜簽核 |
| **S5 收官** | TASK_HISTORY + memory + P119 計畫書預告 | 件套齊 |

---

## 10. 影響檔案清單 ─ STR7

**新增**：`design-system/MASTER.md`、`design-system/tokens.css`、`design-system/mockup.html`（+ ui-ux-pro-max --persist 的 pages/ 若有）
**收官**：`TASK_HISTORY.md` / memory
**不碰（P118）**：`reporter/templates/report.html`、`index.html`、`reporter/generator.py`、CI、後端（這些在 P119+ 才動）

---

## 11. Postmortem 預埋點 ─ G6

位置：`docs/postmortems/2026-06-15-phase-118-design-system.md`（若觸發）

> **通則1（地基先於施工）**：大規模 UI 重設計，先產設計系統 tokens + sandbox mockup 取得 LOOK 定案，再動 live 模板——避免「在生產報告上反覆試錯」的高代價返工。
> **通則2（品牌保留）**：用設計 skill 重設計時，先萃取並 override 鎖定既有品牌識別（色/吉祥物），不讓通用推薦蓋掉品牌資產。
> **通則3（設計系統＝強制契約，非一次性重漆，飛輪核心）**：重設計後若無機器強制（token-lint）+ 可重複視覺驗證，UX 債會無聲復發（今天 #1/#2/#3 即此下場）。設計系統必須有 tokens 唯一真相源 + 硬編碼 re-creep 的 lint guard（接進既有 preflight 總指揮）+ 可重複的 render/screenshot 驗證，才算「不壞」。

---

## ✈️ Pre-flight 多視角體檢 ─ STR10

### M1 強制填表（十一視角）

| 視角 | 發現 |
|---|---|
| **X4-A 紅隊** | 見 M2。核心：mockup 套不進真模板（用真結構）、品牌色被蓋（override 鎖）、範圍越界改 live（Exit 鎖不動 live）、設計脫離真實資料（真實形狀壓測）。 |
| **X4-B 接手者** | tokens.css 單一真相源 + MASTER.md 寫明每 token 用途與芽芽 override 理由；後續 3 Phase 引用不重造。 |
| **X4-C 災難** | P118 純新增 design-system/，最壞＝mockup 不被採用，git rm 即可，零 live 影響。 |
| **X4-D 5 年後** | 設計系統 tokens 文件化＝未來改版有依據；ui-ux-pro-max 快照升級需重產 MASTER（X3）。 |
| **X4-E 終端 vs IDE** | 本地 py 跑 ui-ux-pro-max + 瀏覽器看 mockup；無終端互動。 |
| **X4-F 跨平台** | mockup 須在 Chrome + 手機寬度可看（P120 才正式做 LINE WebView，但 mockup 先顧手機寬度）。 |
| **X4-G 主公視角** | 阿喜要專業化保芽芽。混搭方向已定；mockup 先給看，不滿意先迭代不進 live。 |
| **X4-H 觀測/治理** | 設計系統 MASTER 進版控、可追溯；tokens 一致性可機械自檢。 |
| **X4-I 主公可見性** | P118 不改 live 報告；明告外觀變更 P119 才上線，這 Phase 只給 mockup 預覽。 |
| **X4-J 自動化邊界** | ui-ux-pro-max 是設計顧問（啟發式、召回率僅供參考）；LOOK 最終人工簽核。 |
| **X4-K 使用者端審查官** | 誤解「P118 報告就變漂亮了」→明界定 P118 只產 tokens+mockup，live 報告 P119 才變。 |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | 藍隊回應 | 處置 |
|---|---|---|---|---|
| 1 | **【S 級】** 在 sandbox 把 mockup 做漂亮，但 P119 套進 report.html（2100 行、複雜 Jinja）才發現結構/變數套不上，等於白做 mockup？ | S | mockup **必用 report.html 的真實 Jinja 區塊結構與元件形狀**（卡片/熱詞/feed 對應現有 DOM），非憑空設計；Exit E 要求 mockup 元件結構對齊 report.html，為 P119 鋪路。 | 入計畫（RP1+S3/Exit E）|
| 2 | **【S 級】** ui-ux-pro-max 對 gaming 推 Retro-Futurism 霓虹色，會把芽芽粉櫻品牌識別蓋掉、變成另一個品牌？ | S | 萃取現有品牌色（#be185d/#db2777/sakura/mint）寫入 tokens.css **override 區段強制保留**；混搭＝只取 dashboard 的「結構/間距/層級」，色彩用芽芽品牌色；RP2 緩解。 | 入計畫（RP2）|
| 3 | P118 範圍蔓延去改 live report.html？ | A | Exit 明定不碰 live 模板/generate()/CI；只 design-system/ + mockup。 | 入計畫（RP5）|
| 4 | 設計在 mockup 美、但真實資料（超長中文標題、熱詞 10+ 個、芽芽舊文）撐爆版面？ | A | mockup 用真實資料形狀壓測（長標題/多熱詞/真實密度）。 | 入計畫（RP4）|
| 5 | tokens 訂太細碎/任意值，P119 難一致套用？ | B | 用標準 4/8px spacing scale + 有限字級階梯，非任意 px；MASTER 文件化。 | 入計畫（RP3）|
| 6 | mockup 視覺無法自動驗、會不會假定案？ | B | 設計類本就人工簽核（X4-J）；阿喜看截圖定案 + 品牌色一致性機械自檢補強。 | 入計畫（Exit D/E）|

> 未解質疑：無。

---

## 12. 凍結戳記（待填）

- **凍結人**：阿喜核准（2026-06-15，飛輪版）+ Claude（Opus 4.8 1M）
- **凍結時間**：2026-06-15
- **凍結依據**：lint M1/M2 PASS + 阿喜核准混搭方向 + 飛輪升級（tokens 唯一真相源 + token-lint 進 gov.preflight + preview 驗證）+ 整站重設計 4-Phase 藍圖
- **執行**：交接下個視窗（本對話極長，context 衛生）；下個視窗讀 PHASE_118_HANDOFF.md + 本計畫書即可動工

---

*狀態：草案 v1，待阿喜核准。受 17 層框架 v3.1 + STR10 保護。整站重設計 1/4。建立 2026-06-15（ui-ux-pro-max 修復後首個重設計 Phase，混搭方向）。*
