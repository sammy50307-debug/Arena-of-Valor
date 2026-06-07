# 📋 Phase 109 計畫書（草案，待凍結）

> 狀態：**✅ 已凍結（2026-06-07，lint PASS + 阿喜核准）｜動工：Antigravity + Gemini 3.5 Pro (High)，執行者動工前必讀 §13 交接指引**
> 來源：R-031（P108 阿喜驗收 2026-06-06 提出）；P108.4 收官後待辦盤點，阿喜 2026-06-07 選定 ①、飛輪修正後聚焦 #4a
> 戰線：前端呈現層 UX（獨立於 P108 系列「報告數據可信度」）
> 鐵律提醒（執行者必讀）：`py` 不用 `python`；TASK_HISTORY 禁全讀（grep 錨點+Read offset）；改動前給阿喜計畫書等同意；push 前問阿喜

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P109 |
| **Phase 名稱** | 報告「最新動態」獨立滾輪 + 防復發 guard（R-031 #4a 收斂） |
| **凍結日期** | （待核准）2026-06-07 |
| **影響半徑** | 微（2 檔：`reporter/templates/report.html` +2 行 CSS、新增 1 支 anti-regression test） |
| **預估投入時數** | 0.5–1 h |
| **Token budget** | ~30K |
| **負責模型** | **Gemini 3.5 Pro (High) @ Antigravity**（阿喜指定動工環境）；計畫由 Opus 4.8 凍結 |

## 0.5 狀態轉換清單

**N/A**：本 Phase 不涉及 skill / module / workflow 生命週期狀態轉換。唯一狀態變動為風險 R-031：`Open` → `部分收斂`（#4a 解、#3 待 P106-5 PNG 化），由阿喜收官時拍板，非 skill/module 生命週期，不適用本表。

---

## 1. 目標 (Objective)

`reporter/templates/report.html` 的 `.feed-container`（line 331）加 `max-height: 70vh` + `overflow-y: auto`，讓「最新動態詳情」區可獨立滾動（不再把整頁撐長）；同時新增 1 支 anti-regression test 鎖定該 CSS，防未來 template 重構又弄丟此屬性。

## 2. 觸發背景 (Why Now)

R-031 為 P108 阿喜驗收（2026-06-06）發現的兩個報告 UX 缺陷之一（#3 24H 圖無圖例、#4a 最新動態無法獨立滾輪）。P108.4 收官後盤點待辦，阿喜選 ① 報告 UX 兩修。飛輪二次審視坐實 **#3 圖例靠 echarts CDN（`report.html:9`），而阿喜主要看的 LINE webview 載不到 CDN（P106-5 已知）→ #3 在 LINE 上恐無效**；阿喜裁示 #3 暫擱（待 P106-5 PNG 化根治），本 Phase 聚焦 LINE 必有效的 #4a（純 CSS）+ 防復發 guard。

## 3. Entry Criteria（入口條件）

- [x] 前置 Phase 已收官：P108.4（2026-06-07 已 push origin/main `717f3c4`）
- [x] 資料/依賴已備：`reporter/templates/report.html` 存在；本地可生成報告（P108.4 dry-run 已驗 66.3s 跑通）
- [x] 主公已核准：2026-06-07 阿喜選 ①、要求寫獨立計畫書（核准動工待本計畫書凍結後）
- [x] 風險登記簿無未解高風險阻擋：R-029（高風險，安全）屬不同戰線，不阻擋純前端 UX

## 4. Exit Criteria（退出條件）

- [ ] **A**：生成的報告 HTML 的 `.feed-container` 含 `max-height` + `overflow-y`（grep 生成 HTML 證）
- [ ] **B**：新 anti-regression test 存在且通過（鎖定生成 HTML 的 feed-container CSS）
- [ ] **C**：重生成報告 + preview 截圖確認「最新動態」可獨立滾輪、內容未被切掉（視覺驗收）
- [ ] **D**：全套 488 passed + 新 test 零回歸

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 0.5–1 h |
| 預估收益等級 | 中 |
| 收益描述 | 解阿喜 LINE 手機看報告「最新動態太長要滾整頁」的實際痛點；+ 永久防復發 guard |
| ROI 結論 | ✅ 值得做（低成本、實際體驗改善、機械化防復發） |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 純 CSS 加 2 屬性，match 既有 style 縮排 | max-height 破壞既有佈局 | S1 動工先讀 feed-container 佈局 context；用 vh 相對單位 |
| **2. 邏輯層 (Logic)** | N/A — 無演算法/業務規則改動，純呈現屬性 | 無 | — |
| **4. 測試層 (Testing)** | 新增 anti-regression test 鎖定生成 HTML 的 CSS 結構 | CSS 視覺效果難單測 | 測「生成 HTML 含 max-height/overflow-y」結構，視覺層靠 S3 preview |
| **10. 安全層 (Security)** | N/A — 純前端 CSS，無輸入處理、無 secrets、無資料流、無 auth | 無 | — |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層** | N/A — 不改模組分工，單檔 template CSS 異動 | 無 | — |
| **5. 資料層** | N/A — 不碰任何資料 | 無 | — |
| **6. 可觀察性層** | N/A — 不新增 log/metrics/append-only 檔 | 無 | — |
| **7. 韌性層** | N/A — 純呈現，無外部依賴 | 無 | — |
| **13. 可維護性層** | anti-regression test 提升可維護性（防復發） | 無 | — |
| **14. 文件層** | TASK_HISTORY 收官章節 + R-031 部分收斂更新 | 文件漏記 #3 暫擱理由 | 明記 #3 待 P106-5 PNG 依賴 |
| **15. 流程層** | 本計畫書 + 標準收官流程（test→TASK_HISTORY→commit→push 問阿喜） | 無 | — |

### B 級層（條件式 — 僅填觸發的）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **9. UX/A11y 層** | ✅ 涉及前端 | 最新動態獨立滾輪、滾動體驗 | 滾動條在 LINE webview 不明顯 / 使用者不知可滾 | 標準 overflow-y:auto（溢出才顯條）；避免 deprecated `-webkit-overflow-scrolling`（R-005）；滾輪可見性列 M2 質疑 |

> 未觸發：效能（資料量小）/ 部署（不碰 CI）/ 成本（dry-run 快取多、燒費極低）/ 隱私（不碰第三方資料）/ i18n（不涉跨區）— 整段不適用。

### 層級互鎖驗證 ─ META5

- [x] 動 Logic 層 → 已動 Testing 層：本 Phase **不動 Logic**（純 CSS），但仍主動加 test ✅
- [x] 動 Architecture 層 → N/A（不動架構）
- [x] 動 Data 層 → N/A（不動資料）
- [x] 動 Security 層 → N/A（不動安全）
- [x] 動 Performance 層 → N/A（不動效能）

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 改 `report.html`（+2 行 CSS） | 可逆（git 還原） | — |
| 新增 test 檔 | 可逆 | — |
| 重生成報告（dry-run）動本地 index.html/llm_cache | 可逆（git checkout 還原，同 P108.4） | — |
| commit / push | 半可逆（push 需阿喜核准） | **push 前問阿喜** |

### X2 盲區掃描

- log 副作用：無
- 中間檔產出：重生成報告會產生 `data/reports/aov_report_*.html`（untracked）+ 本地 promote 動 `index.html`（同 P108.4 dry-run 副作用）
- 系統狀態變更：本地 `index.html`/`llm_cache.json` 被 dry-run 改動 → S3 收尾 git checkout 還原

### X3 時間敏感性

- 凍結日期：2026-06-07
- 過期日期：2026-09-07（3 個月後重審）；**或 P106-5 PNG 化動工時**，#3 圖例須回來與本 Phase 一併評估
- 風險記錄帶日期：✅

### X4 多角度同行審查

- **主公視角**：解 LINE 手機看報告「最新動態撐長整頁、滾很久」痛點，目標單純好懂
- **紅隊攻擊者視角**：純 CSS，max-height/overflow-y 為 hardcoded 常數（非使用者輸入）→ 無 injection / XSS / 注入面；唯一濫用前提是未來改成讀使用者可控值，本 Phase 不涉及
- **接手者視角**：anti-regression test + TASK_HISTORY 記錄 #4a 解、#3 為何暫擱（CDN/LINE），半年後可懂修法與 #3 待 PNG 依賴
- **X4-J 自動化工具邊界**：本 Phase 無啟發式/字面比對/推薦工具；anti-regression test 為精確字串比對（非啟發式），false-negative 模式＝只驗 CSS 字串存在、不驗視覺渲染，故仍需 S3 preview 人工視覺覆核
- **X4-K 使用者端審查官**：使用者可能誤解＝若滾動條不明顯，誤以為 feed 內容只有可見那些（不知可滾）→ overflow-y:auto 溢出才顯條 + S3 評估是否需視覺暗示

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | max-height:70vh 在 feed-container 父容器佈局下不生效（滾輪沒出來） | 低 | 中 | 代碼可控 | max-height+overflow-y 為自包含約束（不依賴父容器高度）；S1 讀 context 確認、S3 preview 實證 |
| R2 | 滾動條在 LINE webview 樣式醜/不明顯 | 中 | 低 | 環境依賴 | 標準 overflow-y:auto；S3 preview 驗，必要時 follow-up 視覺暗示 |
| R3 | 重生成報告本地副作用（index.html/llm_cache）誤入 commit | 低 | 低 | 代碼可控 | S3 git checkout 還原（P108.4 已驗此流程） |
| R4 | 70vh 在超小手機過矮 / 大桌面過高 | 低 | 低 | 環境依賴 | vh 相對單位本就自適應；S3 preview resize 多尺寸驗 |

**高風險加權檢查（META4）**：高風險 0 項；加權分數 ≈ 0.5×2 + 1×2 = 3 分（< 5）→ 不需請示阿喜（但 push 仍依約問）

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1** | 讀 `.feed-container` 父容器佈局 context → 加 `max-height: 70vh` + `overflow-y: auto`（match 既有縮排） | R1 | grep template 確認 2 屬性注入 |
| **S2** | 新增 `tests/test_report_ux_scroll.py`：跑 generator 產出報告 → 斷言生成 HTML 的 `.feed-container` 含 max-height + overflow-y | 防復發 | 新 test 綠 |
| **S3** | 重生成報告（dry-run）+ preview 截圖驗滾輪（含 resize 多尺寸）+ 全套零回歸 + git checkout 還原 dry-run 副作用 | R2/R3/R4 | 488+1 passed、截圖、working tree 乾淨 |

---

## 10. 影響檔案清單 ─ STR7

**新增**：
- `tests/test_report_ux_scroll.py`（~30 行，anti-regression test）

**修改**：
- `reporter/templates/report.html`（`.feed-container` +2 行 CSS）

**刪除**：無

**影響但未直接修改**：
- 生成的報告 HTML（呈現變化：最新動態區可滾）

---

## 11. Postmortem 預埋點 ─ G6

收官後若觸發必寫 Postmortem：
- [ ] 主公中途否決重來
- [ ] S1 發現 max-height 無法生效需改設計
- [ ] 上線後 LINE webview 滾輪行為異常
- [ ] 任何「我以為…結果不是」事件

Postmortem 位置：`docs/postmortems/2026-06-07-phase-109-feed-scroll.md`

---

## ✈️ Pre-flight 多視角體檢 ─ STR10 ─ 凍結前必過

### M1 強制填表（十一視角）

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊** | 攻擊面：純 CSS 常數無 injection 點；max-height/overflow-y 非使用者輸入，無 XSS/注入/路徑穿越；濫用前提僅在未來改讀使用者可控值才成立，本 Phase 不涉及；嚴重度低，最小緩解＝維持 hardcoded 常數 |
| **X4-B 接手者** | anti-regression test 留下意圖、TASK_HISTORY 記 #4a 解與 #3 暫擱理由（CDN/LINE 依賴），半年後接手能懂修法與 #3 待 P106-5 PNG 的關聯 |
| **X4-C 災難情境** | 情境：max-height 太小切掉 feed 文章使用者看不到 / 緩解：用 70vh 相對單位 + S3 preview 截圖驗證內容未被截斷 |
| **X4-D 5 年後** | 純 CSS 標準屬性（max-height/overflow-y）5 年後仍通用；刻意避開 deprecated `-webkit-overflow-scrolling` 確保長期不腐化 |
| **X4-E 終端 vs IDE** | 報告於瀏覽器/LINE webview 開啟非終端；preview 截圖在桌面瀏覽器，需留意與 LINE webview 滾動條外觀差異（功能一致） |
| **X4-F 跨平台 Win/Mac/Linux** | CSS overflow-y 跨 Win/Mac/Linux 及 iOS/Android webview 通用；滾動條外觀各 OS 不同但滾動功能一致，不影響核心目標 |
| **X4-G 主公個人視角** | 阿喜主要用 LINE 手機看報告，最新動態太長需滾整頁很煩，獨立滾輪直接命中此日常痛點 |
| **X4-H 觀測 / 治理** | anti-regression test 為治理 guard 防 template 重構復發；R-031 由 Open 更新為部分收斂並追蹤 #3 殘留 |
| **X4-I 主公可見性** | 主公看不到的自動行為：重生成報告動本地 index.html/llm_cache → S3 明列並 git checkout 還原；preview 截圖把效果攤給主公看 |
| **X4-J 自動化建議性工具邊界** | 無啟發式/推薦工具；anti-regression test 為精確比對非啟發式，false-negative＝只驗 CSS 存在不驗視覺，故 S3 preview 人工覆核仍必要 |
| **X4-K 使用者端審查官 / Patric** | 使用者可能在「滾動條不明顯」處誤判 feed 內容只有可見部分（不知可滾）；overflow-y:auto 溢出才顯條 + S3 評估視覺暗示需求 |

> **主公人工裁決錨點（B-005）**：裁決點 1 個（凍結核准）+ 1 個（S3 後 push 核准）；每點預估 < 2 分鐘；AI 提供格式＝計畫書摘要 + preview 截圖。

### M1.5 八人格顧問團

| 人格 | 觸發 | 是否觸發 / 發現 |
|---|---|---|
| **Jarvis 型總控** | 固定 | ✅ 目標單一（#4a 滾輪+test）、邊界明確（#3 暫擱待 PNG）、下一步清楚 |
| **Ken 型紅隊** | 固定 | ✅ 純 CSS 無 secrets/CI/不可逆；唯一注意 push 需阿喜核准 |
| **Patric 型使用者審查** | 固定 | ✅ 滾動條可見性風險（見 X4-K），S3 評估 |
| **Jimmy 型文件主筆** | ✅ 改 template + TASK_HISTORY | 計畫書明記 #3 暫擱理由（CDN/LINE）可追溯 |
| **Marcus 型數據分析師** | N/A | 不涉數據分析/趨勢判斷 |
| **Oliver 型設計審查** | ✅ 涉報告視覺 | max-height 70vh 資訊密度、滾輪可讀性、不切內容 |
| **Penny 型 CFO** | ✅ S3 重生成燒 LLM | 成本極低（dry-run L2 快取多，P108.4 實測僅 8 calls）；無預算風險 |
| **Jason 型 DevOps** | ✅ 重生成+可能 commit/push | rollback：git 還原 template + 還原本地副作用；push 前問阿喜 |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | max-height:70vh 若父容器無高度約束，overflow-y 可能不生效→滾輪沒出來 | **S** | 0 | max-height+overflow-y 為自包含約束（容器內容超過 70vh 即觸發 overflow，不依賴父容器高度）；仍 S1 讀 context + S3 preview 實證 | 入計畫（S1 查證 + S3 驗證） |
| 2 | anti-regression test 若只 grep template 原始碼，template 條件渲染變動時會假綠 | **S** | 0 | test 驗「生成的報告 HTML」（跑 generator 產出後檢查），非 template 原始碼 | 入計畫（test 鎖定 generated output） |
| 3 | #3 暫擱會讓阿喜誤以為 R-031 全解、未來忘記 #3 | 中 | 0 | R-031 不全 close，標「#4a 解、#3 待 P106-5 PNG」；TASK_HISTORY + RISK 明記殘留 | 入 RISK（R-031 部分收斂 + 明確待辦） |
| 4 | 70vh 單一值大桌面過高、小手機過矮 | 低 | 0 | vh 相對單位本就隨視窗自適應；S3 preview resize 多尺寸驗 | 入計畫（S3 resize 驗證） |
| 5 | 重生成報告本地副作用沒還原→污染下次 commit | 中 | 0 | S3 明列副作用 + git checkout 還原（P108.4 已驗此流程） | 入計畫（S3 收尾還原） |
| 6 | 滾動條不明顯→使用者不知可滾（UX 半套） | 中 | 0 | overflow-y:auto 溢出才顯條；視覺暗示屬 enhancement，本次先標準做法 | 入 RISK（S3 不足則登記 follow-up） |

> 未解殘留入 RISK：質疑 1（context 生效）動工 S1/S3 驗證；質疑 6（滾輪可見性）若 S3 判定不足 → 登記為 follow-up。無 pre-existing failing test 牽涉。

---

## 12. 凍結戳記

- **凍結人**：阿喜核准 + Opus 4.8 執行（lint PASS：`py scripts/lint_phase_plan.py docs/PHASE_109_PLAN.md` ✅）
- **凍結時間**：2026-06-07 15:54
- **動工環境**：Antigravity + Gemini 3.5 Pro (High)（見 §13 交接指引）
- **凍結後變更**：禁止；如需修改，新增章節「Phase 109.X 補遺」並引用本檔

---

## 13. 🤝 跨工具交接指引（給 Antigravity / Gemini 3.5 Pro High 執行者 — 動工前必讀）

> ⚠️ 你（Gemini @ Antigravity）**不會**繼承本專案 `CLAUDE.md` 全域守則與此前對話脈絡。動工前請讀本區 + 計畫書全文（特別 §4 Exit、§9 Stages）。

### 環境鐵律
- **Windows 環境；跑 Python 一律 `py` 不用 `python`**（例：`py -m pytest`、`py main.py --dry-run`）
- `TASK_HISTORY.md` 4000+ 行**禁全讀**：查歷史用 `grep -n "^### " TASK_HISTORY.md` 找錨點 + 部分讀；寫新章節用 `cat >> TASK_HISTORY.md << 'EOF'`（不用編輯器全開）
- 偏離本計畫書前先問阿喜；**commit/push 前必問阿喜**

### 動工順序（照 §9）
- **S1**：`reporter/templates/report.html` 找 `.feed-container`（約 line 331，**先 grep 確認當前行號**）→ 加 `max-height: 70vh;` + `overflow-y: auto;`（match 既有縮排）。先讀該 selector 上下文，確認佈局不被破壞。
- **S2**：新增 `tests/test_report_ux_scroll.py` —— **跑 generator 產出報告 HTML 後**斷言 feed-container 區塊含 `max-height` + `overflow-y`（驗**生成輸出**，**非** template 原始碼；否則 Jinja 條件渲染變動會假綠）。
- **S3**：`py main.py --dry-run` 重生成 → 開 `data/reports/aov_report_<date>.html` 視覺確認最新動態可獨立滾輪、內容未被切掉（resize 多尺寸）→ `py -m pytest` 全套需 **488+1 passed** → **`git checkout -- index.html data/llm_cache.json` 還原 dry-run 副作用**（非本 Phase 改動，dry-run 會動到）。

### 禁區（surgical changes）
- ❌ 不動 #3 圖例（`report.html` visualMap `show:false`）—— 本 Phase 暫擱，待 P106-5 PNG 化
- ❌ 不重構無關 code / 不順手改格式 —— 只動 `.feed-container` + 新 test
- ❌ 不用 `--allow-skip` 繞 lint、不改既有測試讓它過

### 防幻覺
- 改前先確認檔案/行號存在（行號會漂移，**以 grep 為準，不信本計畫書的行號數字**）
- 不確定就明說，不臆測

### 收官流程
test 綠 → TASK_HISTORY 追加 P109 章節（`cat >> heredoc`）→ commit → push（**問阿喜**）→ `docs/RISK_REGISTRY.md` 更新 R-031（#4a 解、#3 待 P106-5 PNG）

---

*本計畫書受 17 層品質框架 v3.1 + STR1/STR10 保護。樣板版本 v1.2。*
