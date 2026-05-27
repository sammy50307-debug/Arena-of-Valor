# Phase P98 計畫書 — Project Flywheel Audit Plan（CLOSED）

> 狀態：CLOSED / REPORT ONLY。主公於 2026-05-27 選取並要求「開 P98 Project Flywheel Audit Plan」，核准 `P98 plan freeze` 後又核准 `P98 audit runtime`。本 Phase 已完成 repo metadata audit 與 P99+ 候選排序；未清理檔案、未搬移 generated reports、未改 runtime code、未改 GitHub Actions、未導入 RTK。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P98 |
| **Phase 名稱** | Project Flywheel Audit Plan |
| **建立日期** | 2026-05-27 |
| **影響半徑** | 標準 (plan 5 檔；runtime 仍需另核准) |
| **預估投入時數** | plan 0.8h；audit runtime 2.5-4h |
| **Token budget** | plan 18K；audit runtime 45K |
| **負責模型** | GPT-5.3-Codex（repo 盤點 / 文件 / 檢查）；若涉及架構裁決或規則瘦身衝突，升 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| R-019 Project Self-Optimization Flywheel | New | Open | 專案結構、生成物、治理文件、known issue 與工具導入流程進入盤點計畫 | 主公開 P98 plan | AI 建帳，主公審核 |
| P98 plan | DRAFT | FROZEN | audit 計畫已凍結，尚不可執行清理或 runtime 改動 | 主公核准 `P98 plan freeze` | 主公 / AI |
| P98 audit runtime | Pending approval | CLOSED | 已完成盤點與報告，不做清理 | 主公核准 `P98 audit runtime` 後完成 `docs/PHASE_98_AUDIT.md` | 主公 / AI |
| Cleanup / refactor actions | Not allowed | Blocked by default | 任何搬檔、刪檔、gitignore 大改、checker 升級都不屬 P98 plan | 需依 audit 結果另開 P99+ | 主公 |

---

## 1. 目標 (Objective)

建立一份可執行的 AOV 專案自我優化飛輪 audit 計畫，將「核心程式、生成物、治理文件、known issue、防復發檢查、工具導入流程」分層盤點，產出下一批高 ROI phase 候選，而不在 P98 plan 階段改 runtime code。

## 2. 觸發背景 (Why Now)

P97 已完成 RTK 評估並裁決不全域部署；主公接著追問專案方法是否存在問題，並要求用飛輪式優化方法改善。AOV 專案目前客觀上不是單純程式碼大，而是跨爬蟲、LLM、報告、GitHub Actions、內容可信度、治理文件、skills 與 generated artifacts 的中型偏大系統。若不先 audit，直接清理或重構容易把核心程式、生成物與治理狀態混在一起，造成新的漂移。

## 2.1 問題定義

P98 要解的不是單一 bug，而是「返工成本高、AI 接手容易迷路、生成物與治理文件淹沒核心程式」的系統性問題。P98 runtime 的任務是盤點與排序，不是執行大清理。

| 問題面 | 目前現象 | P98 audit 要回答 |
|---|---|---|
| Core vs generated | `data/`、`ui_previews/`、reports、scratch 量大 | 哪些應留 repo，哪些應改 artifact / git-ignored |
| Known issue memory | P96 才開始把錯標 / 舊文變成 checker | 還有哪些復發型 bug 只有人腦記得 |
| Governance cost | handoff / active / risk / history 多檔同步 | 哪些真相應集中，哪些可引用而非重複 |
| Verification ladder | 有 full pytest，也有多個 checker | 哪些任務跑 focused，哪些必須 cloud evidence |
| Tool ROI | RTK 顯示工具不能只看 star / 宣稱 | 新工具導入需要固定 ROI / fidelity / rollback gate |

## 2.2 方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 直接清理 generated files | 立刻搬 reports / scratch / previews | 看起來最快變乾淨 | 可能刪到歷史證據或破壞 Pages / report link | 不採用 |
| B. 直接大重構 | 同時重整 analyzer / reporter / docs | 可能一次處理很多痛點 | blast radius 過大，難驗證 | 不採用 |
| C. Project Flywheel Audit | 只盤點、分層、量化、排序下一批 phase | 低風險，能避免誤刪誤修 | 需要多一道計畫 / audit runtime | 採用 |
| D. 只靠新增全域規則 | 把飛輪寫進 AGENTS / CLAUDE / GEMINI | 跨專案有效 | 無法處理 AOV 具體生成物與 known issue | 已補，但不足以替代 P98 |

---

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] P97 已收官並推送：`e883117` 已在 origin/main。
- [x] P98 plan draft 已推送：`ae74f4e` 已在 origin/main。
- [x] AOV 專案版自我優化飛輪已寫入 `AGENTS.md`。
- [x] 全域自我優化飛輪已同步至 Codex / Claude / Gemini 全域規則。
- [x] 主公已要求：`開 P98 Project Flywheel Audit Plan`。
- [x] 本 Phase 明確限制為 plan，不執行清理 / 搬檔 / runtime code 改動。
- [x] 主公核准 `P98 plan freeze`。
- [x] 主公另行核准 `P98 audit runtime`。

## 4. Exit Criteria（退出條件）

P98 plan draft 退出條件：
- [x] `docs/PHASE_98_PLAN.md` 通過 `scripts/lint_phase_plan.py`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 R-019 / P98 DRAFT。
- [x] `docs/RISK_REGISTRY.md` 建立 R-019 Open 風險。
- [x] `TASK_HISTORY.md` 追加 P98 plan 物理真相。
- [x] `git diff --check`、handoff truth、governance doctor 通過。

P98 plan freeze 退出條件：
- [x] 主公核准 `P98 plan freeze`。
- [x] `docs/PHASE_98_PLAN.md` 狀態改為 FROZEN。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 R-019 / P98 FROZEN。
- [x] `docs/RISK_REGISTRY.md` 標記 R-019 為 P98 FROZEN / audit runtime 未開始。
- [x] `TASK_HISTORY.md` 追加 P98 plan freeze 物理真相。
- [x] `git diff --check`、phase plan lint、handoff truth、governance doctor 通過。

P98 audit runtime 退出條件：
- [x] 產出 repo 分層 inventory：core / tests / scripts / governance docs / generated outputs / skills / scratch。
- [x] 產出 known issue memory gap 表：至少列出已機器化、未機器化、建議落點。
- [x] 產出 generated artifact hygiene 表：保留、gitignore、artifact、需主公裁決四類。
- [x] 產出 verification ladder：focused / full / cloud / manual acceptance 的觸發規則。
- [x] 產出 top 5 下一步 phase 候選，含 ROI、風險、預估投入與是否需主公裁決。
- [x] 明確裁決：建議 P99 先做 `Generated Artifact Hygiene Policy / Stage Guard`。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 2.5-4h |
| 預估收益等級 | 高 |
| 收益描述 | 降低後續 Phase 迷路、誤 stage generated files、重複修 bug、文件同步過重與新工具誤導入的風險 |
| ROI 結論 | ✅ 值得做；先 audit 再決定清理與 guard，避免大重構 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | P98 plan 不改 runtime code；audit runtime 只允許讀取與分類 | 把 audit 偷渡成重構 | Forbidden Work 明列不搬檔、不刪檔、不改 app logic |
| **2. 邏輯層 (Logic)** | 建立分層邏輯：core / generated / governance / skill / scratch / checks | 分類錯誤導致後續 phase 誤刪或誤降級 | runtime 需保留 evidence table 與主公裁決欄 |
| **4. 測試層 (Testing)** | 設計 verification ladder 與 known issue gap | audit 只寫漂亮文件，沒有防復發效果 | runtime exit criteria 必含 next checker / test 候選 |
| **10. 安全層 (Security)** | 不動 secrets、不動 `.env`、不下載新工具、不改 CI 權限 | 盤點時暴露敏感檔名或把 raw artifact 納入 docs | raw-free 摘要；敏感資訊只記類型與路徑模式 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | P98 盤點 module ownership 與 artifact boundary | 把治理文件當架構本體，導致設計失焦 | inventory 拆成產品、工具、治理、輸出四類 |
| **5. 資料層 (Data)** | 盤點 generated reports / CSV / JSON / raw artifacts 的保留政策 | 誤把歷史報告視為可刪，或把 raw data 推上 repo | 只做分類，不刪；需主公裁決才動 |
| **6. 可觀察性層 (Observability)** | 產出 audit matrix、known issue gap、verification ladder | 沒有量化，只靠感覺排序 | 每項候選需有 evidence、ROI、風險 |
| **7. 韌性層 (Resilience)** | 建立「下次不再靠人記」的 guard 候選 | 飛輪規則太多反而變成負擔 | 定期復盤列 keep / revise / remove |
| **13. 可維護性層 (Maintainability)** | 降低 AI 接手成本與 Phase 同步成本 | 文件越補越厚，維護成本更高 | P98 明列文件瘦身與 single source of truth 候選 |
| **14. 文件層 (Documentation)** | 新增 P98 plan，handoff / active / risk / history 同步 | 下一窗誤以為已開始清理 runtime | FROZEN / runtime not started 明確標記 |
| **15. 流程層 (Process)** | Plan -> freeze -> audit runtime -> P99+ execution | audit 與清理混在一起 | P98 只盤點與排序，清理由 P99+ 承接 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | repo 盤點可能掃大量檔案 | 使用 `git ls-files` / `rg --files`，不全讀大檔 | 全讀 TASK_HISTORY 或 reports 爆 token | 僅統計 metadata / line count，必要時抽樣 |
| **9. UX/A11y 層** | 間接影響 report / 前台內容信任 | audit 只列 UX/content trust gap | 誤把內容問題當 UI 問題 | 跨戰線分流表拆清楚 |
| **11. 部署層 (DevOps)** | GitHub Actions / Pages / artifact policy 可能入候選 | 只盤點，不改 workflow | 清理 generated files 破壞 Pages | P99+ 才可變更部署 |
| **12. 成本層 (Cost)** | LLM / token / CI 時間 | 建立工具 ROI 與 verification ladder | 花太多時間做治理不產生收益 | top 5 候選必填 ROI |
| **16. 隱私/合規層 (Privacy)** | 盤點資料與 logs | raw-free inventory | 把 raw post / secret / token 寫入 docs | 只記路徑模式與統計 |
| **17. i18n/在地化層** | AOV report 含繁中與遊戲詞 | 確認 checker / docs 使用 UTF-8 與繁中命名 | 中文路徑/內容造成腳本亂碼 | 沿用 PYTHONUTF8 / PYTHONIOENCODING 規則 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：P98 audit 要產出 verification ladder / known issue gap。
- [x] 動 Architecture 層 -> 已動 Documentation 層：inventory 與 boundary 只記 docs，不改 code。
- [x] 動 Data 層 -> 已動 Maintainability 層：generated artifact policy 以可維護性為目標。
- [x] 動 Security 層 -> 已動 Testing 層：raw-free / no-secrets 規則需在 audit checklist 驗證。
- [x] 動 Performance 層 -> 已動 Observability 層：大量掃描只做 metadata，並記錄 evidence。

---

## 7. 跨切面檢查

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_98_PLAN.md` | 可逆 | 主公已要求開 plan |
| 更新 handoff / active / risk / history | 可逆 | 本次同步 FROZEN 狀態 |
| audit runtime 讀取 repo metadata | 可逆 | 未來需主公核准 runtime |
| 搬移 / 刪除 generated files | 半可逆到不可逆 | P98 禁止，需 P99+ 明文核准 |
| 改 `.gitignore` 或 GitHub Actions | 半可逆 | P98 禁止，需另開 phase |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] repo 看起來大，可能主要是 generated HTML / data，不代表核心程式碼巨大。
- [x] 文件越補越多也可能成為成本，P98 需要找 single source of truth。
- [x] known issue 若只寫在 `TASK_HISTORY.md`，下一個 AI 仍可能因禁止全讀而看不到。
- [x] generated reports 可能同時是歷史證據與部署依賴，不能直接刪。
- [x] 新工具導入若沒 ROI gate，會增加 debug 變因。

### X3 時間敏感性 (Time Decay)

- 本計畫建立日期：2026-05-27。
- 本計畫過期日期：2026-06-03；若一週內未開始 audit runtime，需重新確認 P97/P98 handoff 與 R-016/R-017 monitoring 狀態。
- R-016 monitoring 至 2026-06-01；R-017 monitoring 至 2026-06-02。
- 風險記錄帶日期：✅。

### X4 多角度同行審查

- **主公視角**：這份計畫要把「為什麼一直返工」拆成可看懂的清單，而不是用更多術語堆高壓力。
- **世界頂尖駭客 / 紅隊攻擊者視角**：風險在於 audit 誤碰 secrets、raw user data、CI permissions 或刪除部署依賴；P98 只讀 metadata 且禁止清理。
- **接手者視角**：接手者需要看到 P98 是 FROZEN / audit runtime not started，不是已經開始移檔或重構。
- **X4-J 自動化建議性工具邊界**：line count / file count / grep inventory 只能輔助排序，不能單獨判定可刪或可降級。
- **X4-K 使用者端審查官 / Patric 型人格**：主公最容易誤解的是「audit 等於馬上清理」；計畫需明說 P98 不做清理，清理由 P99+ 承接。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | P98 audit 被誤用成大清理或大重構 | 中 | 高 | 流程 | Forbidden Work 明列不搬檔、不刪檔、不改 runtime |
| R2 | generated report / preview 被誤判為垃圾，實際是部署或歷史證據 | 中 | 高 | 資料 / 部署 | runtime 只分類，刪除需 P99+ 與主公裁決 |
| R3 | 文件瘦身過頭，破壞 handoff / TASK_HISTORY 可追溯性 | 中 | 中 | 治理 | 只提出候選，不在 P98 runtime 直接刪 |
| R4 | known issue inventory 變成主觀列表，沒有機器化落點 | 中 | 中 | 測試 / 流程 | 每項缺口需列 docs / test / checker / config 建議 |
| R5 | audit 掃描過量檔案造成 token 浪費 | 中 | 中 | 成本 | 用 `git ls-files`、line count、metadata，不全讀大檔 |
| R6 | P98 與 RTK future pilot 編號混線 | 低 | 中 | 治理 | R-018 future RTK pilot 改稱 P99+ 或另開 phase |

**高風險加權檢查（META4）**：
- 高風險數量：2 項。
- 加權分數：7 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；P98 plan 只建立路線，runtime / 清理 / refactor 需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 Plan / Boundary Lock** | 建立 P98 plan、R-019、handoff、active、history | 避免 audit 和清理混線 | plan lint / governance checks PASS |
| **S1 Repo Layer Inventory** | 用 `git ls-files` / metadata 分層 core、tests、scripts、docs、data、skills、scratch | 避免被 repo 體積誤導 | inventory table |
| **S2 Known Issue Memory Gap** | 盤點 R-016/R-017/P96/P97 類 known issues 的機器化程度 | 防復發能力不足 | gap matrix |
| **S3 Generated Artifact Hygiene** | 分類 reports/previews/backups/scratch 的保留政策 | generated outputs 淹沒核心 | keep / ignore / artifact /裁決表 |
| **S4 Governance Slimdown Audit** | 找 handoff / active / risk / history 重複與 source of truth 候選 | 文件同步成本過高 | slimdown candidates |
| **S5 Verification Ladder** | 定義 focused/full/cloud/manual acceptance 觸發 | 測試跑太多或跑太少 | verification decision table |
| **S6 Next Phase Ranking** | 排 top 5 P99+ 候選，標 ROI / risk / effort | 下一步失焦 | 主公裁決矩陣 |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_98_PLAN.md`
- `docs/PHASE_98_AUDIT.md`

**修改**：
- `NEXT_SESSION_HANDOFF.md`：切到 R-019 / P98 CLOSED。
- `docs/ACTIVE_OPERATION.md`：切到 R-019 / P98 CLOSED。
- `docs/RISK_REGISTRY.md`：新增 R-019 Open，並避免 R-018 future RTK pilot 與 P98 編號混線。
- `TASK_HISTORY.md`：追加 P98 plan draft / freeze / runtime audit 物理真相。

**刪除**：
- 無。

**影響但未直接修改**：
- `AGENTS.md`：P98 使用剛新增的 AOV 自我優化飛輪規則，但本 Phase 不再修改。
- generated reports / `scratch/` / skills：P98 runtime 只讀 metadata，不 stage。
- GitHub Actions / Pages：P98 plan 不改。

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P98 未核准 runtime 卻移動、刪除或 stage generated artifacts。
- [ ] audit 造成 secrets、raw posts 或敏感路徑外洩到 docs。
- [ ] P98 把 R-016 / R-017 monitoring 狀態誤標 Closed。
- [ ] P98 建議的 P99+ 候選沒有 evidence 或 ROI 仍被推進。
- [ ] 有任何「我以為...結果不是」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-98-project-flywheel-audit.md`

---

## 12. Forbidden Work（P98 邊界）

- 不搬移、不刪除、不 rename 檔案。
- 不改 `.gitignore`。
- 不改 runtime code。
- 不改 GitHub Actions / Pages deployment。
- 不 stage generated reports、scratch、raw artifact、舊 untracked skill 暫存。
- 不導入 RTK 或任何新工具。
- 不把 R-016 / R-017 monitoring 標 Closed。
- 不把 P98 改成 RTK pilot；RTK 若要繼續，另開 P99+ 或獨立 phase。

---

## ✈️ Pre-flight 多視角體檢（M1+M1.5+M2）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是 audit 誤讀 secrets、raw data、CI 權限與部署依賴；P98 禁止清理並採 raw-free metadata。 |
| **X4-B 接手者** | 接手者需要知道 P98 只建立 audit 路線，不代表 generated reports、scratch 或 governance docs 已被清理。 |
| **X4-C 災難情境** | 災難情境是把部署需要的 report 或歷史證據當垃圾刪除；緩解是 P98 只分類並把刪除留給 P99+。 |
| **X4-D 5 年後** | 五年後接手者需要的是 project map 與機器化 guard，而不是更長的對話記憶；P98 要把規則變成可查文件。 |
| **X4-E 終端 vs IDE** | 終端適合 metadata 掃描與 line count；IDE 適合局部閱讀。P98 禁止全讀大型 history 或 reports。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows PowerShell 是當前主環境，但 audit 產物應避免依賴 Windows-only path；命令需保留跨平台替代思路。 |
| **X4-G 主公個人視角** | 主公需要白話知道專案哪裡大、哪裡亂、哪裡先修最划算，而不是被更多規則壓住。 |
| **X4-H 觀測 / 治理** | 觀測重點是 inventory、known issue gap、artifact hygiene 與 verification ladder；每個候選需有 evidence 和 ROI。 |
| **X4-I 主公可見性** | 主公看不到 AI 是否誤 stage 舊暫存或全讀大檔；P98 明列 untracked/scratch 禁止納入並保留 status checks。 |
| **X4-J 自動化建議性工具邊界** | file count、line count、grep 命中只代表盤點訊號，不代表可刪、可合併或可降級，仍需人工裁決。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 最容易誤解的是 audit 等於清理完成；計畫要把 plan、runtime、cleanup phase 三者切開。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步 | 觸發；P98 只做 audit plan，runtime / cleanup 分門處理。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | secrets、CI、不可逆操作 | 觸發；禁止刪檔、搬檔、改 workflow。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公是否誤解流程 | 觸發；文件明說 audit 不是清理。 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff 時觸發 | 文件可追溯與 source of truth | 觸發；handoff / active / risk / history 同步 FROZEN。 |
| **Marcus 型數據分析師** | 涉及數據、判斷依據時觸發 | 定量 / 定性是否分清 | 觸發；runtime 需產出 inventory 與 ROI。 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表時觸發 | 報告與內容信任 | 條件觸發；P98 只盤點 report artifacts，不改 UI。 |
| **Penny 型 CFO** | 涉及成本、付費工具時觸發 | ROI、token、CI 成本 | 觸發；P98 建立工具 ROI gate 與治理成本排序。 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、環境差異時觸發 | rollback、artifact、Git hygiene | 觸發；不改 Pages / Actions，先盤點部署依賴。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | P98 可能變成包山包海的大重構入口，最後比現在更亂。 | **S 級** | 0 | P98 只允許 audit 與排序，所有清理 / 重構移到 P99+。 | 入計畫範圍 |
| 2 | generated reports 可能是 Pages 或歷史證據，誤刪會破壞站台或追溯。 | **S 級** | 0 | P98 禁止刪除，只產出 keep / ignore / artifact /裁決分類。 | 入計畫範圍 |
| 3 | known issue gap 若只寫表格不補 checker，無法真正防復發。 | A 級 | 0 | runtime exit criteria 要列機器化落點與 P99+ 候選。 | 入計畫範圍 |
| 4 | 文件瘦身可能讓交接資訊不足，下一窗反而更迷路。 | A 級 | 0 | 只提出 source of truth 候選，不在 P98 刪內容。 | 入計畫範圍 |
| 5 | audit 掃描大量檔案會浪費 token，違背省成本目標。 | B 級 | 0 | 使用 metadata / line count / `rg`，禁止全讀大檔。 | 入計畫範圍 |
| 6 | P98 名稱被 RTK future pilot 佔用，會造成 R-018/R-019 混線。 | A 級 | 0 | P98 固定為 Project Flywheel Audit，RTK future pilot 改 P99+ 或獨立 phase。 | 入計畫範圍 |
