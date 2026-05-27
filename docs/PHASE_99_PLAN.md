# Phase P99 計畫書 — Generated Artifact Hygiene Policy / Stage Guard（DRAFT）

> 狀態：DRAFT。主公於 2026-05-27 要求「開 P99 Generated Artifact Hygiene Policy / Stage Guard」。本 Phase 只建立 generated artifact hygiene policy 與 stage guard 的計畫；不刪檔、不搬檔、不 rename、不改 `.gitignore`、不改 runtime code、不改 GitHub Actions / Pages、不清理既有 tracked reports。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P99 |
| **Phase 名稱** | Generated Artifact Hygiene Policy / Stage Guard |
| **建立日期** | 2026-05-27 |
| **所屬 Program** | R-019 Project Self-Optimization Flywheel Program |
| **新風險帳** | R-020 Generated artifact hygiene / stage guard false positives |
| **影響半徑** | 標準（plan 5 檔；future runtime 約 3-5 檔，仍需另核准） |
| **預估投入時數** | plan 0.8h；runtime 1.5-2.5h |
| **Token budget** | plan 16K；runtime 35K |
| **負責模型** | GPT-5.3-Codex（metadata / docs / checker plan）；若涉及刪檔或 `.gitignore` 變更，升 GPT-5.5 高並另開 Phase |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P98 audit | CLOSED / report-only | Reference only | P98 只作為 P99 證據來源，不再修改 | `84012c0` 已推送 | AI / 主公 |
| P99 plan | Not started | DRAFT | 建立 stage guard 計畫，不實作 checker | 主公開 P99 | AI |
| P99 runtime | Not started | Pending approval | 未來可新增 policy doc / advisory checker / tests，但仍不得刪檔 | 主公核准 P99 plan freeze 後另行核准 runtime | 主公 |
| Cleanup actions | Blocked | Blocked | 任何刪除、搬移、rename、`.gitignore` 改動都不屬 P99 plan | 需另開 P100+ 或 P99.x cleanup plan | 主公 |

---

## 1. 目標 (Objective)

把 P98 audit 發現的 generated/deploy artifacts 混線風險，轉成一套可重跑、低風險、advisory-first 的 policy + stage guard 計畫。P99 的核心不是清理，而是讓未來 commit 前能看見「這次是不是誤 stage 了 reports / previews / scratch / backups / local artifact」。

## 2. 觸發背景 (Why Now)

P98 audit 顯示：

| Evidence | 數值 / 現象 | P99 要處理的問題 |
|---|---|---|
| Generated / deploy artifacts | 123 tracked files / 22.18 MB | reports、previews、backups、landing 混在 repo 視野 |
| `data/reports` | tracked 88 files；另有多個 untracked preview / old report | AI 容易誤 stage 或讀錯版本 |
| `ui_previews` | tracked 27 files，但 `.gitignore` 已忽略新產物 | 歷史 preview 與 future scratch 邊界不清 |
| `scratch/` | local 66 files / 12.31 MB；已 ignored | 不會進 git，但 AI 仍可能拿來當證據 |
| root debug files | `run_log.txt`、`full_diff.txt`、`diff_result.txt` 等 tracked | 不是 P99 主線；留給 P100 quarantine |

## 2.1 問題定義

P99 解的是「commit hygiene / artifact boundary」問題，不是「網站內容 bug」或「報告刪減」問題。

| 不解的事 | 原因 | 轉交 |
|---|---|---|
| 刪掉 tracked old reports | 可能破壞 Pages / history evidence | P100+ cleanup with rollback |
| 移動 `ui_previews` | 可能破壞 golden preview evidence | P100+ |
| 清根目錄 debug logs | 不是 generated artifact 主線 | P100 Root Legacy Quarantine |
| 修芽芽 / 舊文內容 | 屬 R-017 content trust | P104 或 R-017 follow-up |
| 整理 `.agents` | skill-layer hygiene | P102 |

## 2.2 方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 直接刪 old reports / previews | 立刻讓 repo 變小 | 快速降噪 | 高風險，可能刪到部署或歷史證據 | 不採用 |
| B. 直接改 `.gitignore` | 防新檔進來 | 看似簡單 | 可能改壞 production / Pages / report commit 流程 | 不採用於 P99 |
| C. Advisory stage guard | 建 policy + checker，commit 前提示風險，不阻擋 | 低風險，可驗證，可逐步升級 | 初期不能自動清理 | 採用 |
| D. Strict pre-commit gate | 直接 blocking | 防誤 stage 強 | false positive 會拖慢 Phase | P99 不採用；未來穩定後再評估 |

---

## 3. Entry Criteria（入口條件）

- [x] P98 runtime audit 已完成並推送：`84012c0` 已在 origin/main。
- [x] P98 明確裁決：下一個最高 ROI 候選為 P99 Generated Artifact Hygiene Policy / Stage Guard。
- [x] 主公已要求：`開 P99 Generated Artifact Hygiene Policy / Stage Guard`。
- [x] P99 plan 明確限制為 plan，不執行刪檔 / 搬檔 / `.gitignore` / runtime code 改動。
- [ ] 主公核准 `P99 plan freeze` 後，才可進下一門 runtime。

## 4. Exit Criteria（退出條件）

P99 plan draft 退出條件：
- [x] `docs/PHASE_99_PLAN.md` 建立並通過 `scripts/lint_phase_plan.py`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 R-019 / P99 DRAFT。
- [x] `docs/RISK_REGISTRY.md` 建立 R-020 Open 風險。
- [x] `TASK_HISTORY.md` 追加 P99 plan draft 物理真相。
- [x] `git diff --check`、handoff truth、governance doctor 通過。

P99 runtime 未來退出條件：
- [ ] 產出 generated artifact policy：分清 keep / generated / scratch / artifact / quarantine / requires主公裁決。
- [ ] 產出 advisory stage guard design：先只檢查 staged diff，不改 stage、不 auto delete。
- [ ] 覆蓋最小測試：誤 stage `scratch/`、`data/reports/PREVIEW_*.html`、root debug logs 時能提示；正常 docs/code commit 不吵。
- [ ] 明確不升 strict gate；只列未來 promote 條件。
- [ ] P99 runtime 收官時不產生任何 file deletion / move / `.gitignore` diff。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 1.5-2.5h |
| 預估收益等級 | 高 |
| 收益描述 | 降低誤 stage generated reports / scratch / backups 的風險，讓每次 commit 前能快速看見 artifact boundary |
| ROI 結論 | 值得做；先 advisory checker，再視穩定度決定是否升級 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | plan 不改 code；future runtime 只可新增小型 checker / tests | 把 plan 偷渡成刪檔工具 | Forbidden Work 明列不刪、不移、不改 `.gitignore` |
| **2. 邏輯層 (Logic)** | 建 artifact classification：keep / generated / scratch / artifact / quarantine / decision | 分類錯誤造成誤報或漏報 | 先 advisory，且每類需例外清單 |
| **4. 測試層 (Testing)** | runtime 必補 staged-path fixture tests | checker 太吵或抓不到真問題 | 測試同時覆蓋 positive / negative cases |
| **10. 安全層 (Security)** | checker 不讀 raw file content，只看 staged path / git status metadata | raw report / queue / secret 被輸出 | raw-free output；只列 path pattern 與 reason |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 將 artifact policy 與 product runtime 分離 | stage guard 變成 product logic | 放 `scripts/` + docs，不進 analyzer/reporter |
| **5. 資料層 (Data)** | 區分 production manifests、canonical reports、preview/scratch | 誤把 production truth 當垃圾 | policy 明列 keep classes |
| **6. 可觀察性層 (Observability)** | checker 輸出 reason / severity / path pattern | 只說 fail 不說原因 | machine-readable JSON optional |
| **7. 韌性層 (Resilience)** | advisory-first，不阻斷既有 release | false positive 造成工作停擺 | runtime 不接 pre-commit blocking |
| **13. 可維護性層 (Maintainability)** | policy 成為 single source of truth | 例外散落 handoff | 例外集中在 policy / checker constants |
| **14. 文件層 (Documentation)** | 新增 P99 plan，future runtime 新增 policy doc | 未來 AI 還是不知道哪些能 stage | handoff / active / risk 同步 |
| **15. 流程層 (Process)** | Plan -> freeze -> runtime -> observe -> promote | plan 後直接刪檔 | cleanup 明確移到 P100+ |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | checker 可能常跑 | 只看 staged paths / git status，不掃大檔內容 | 慢、吃 token | metadata-only |
| **9. UX/A11y 層** | N/A | 不改前台 UI | 誤解為網站修復 | 標明非 content trust |
| **11. 部署層 (DevOps)** | reports / Pages 相關 | 不改 GitHub Actions / Pages | 破壞部署 | P99 只 advisory |
| **12. 成本層 (Cost)** | 減少 AI 誤讀 / 誤 stage | 少跑不必要 diff/read | checker 過度複雜 | 最小 script |
| **16. 隱私/合規層 (Privacy)** | raw artifacts / queues 風險 | 不讀內容、不輸出 raw post | path 洩漏可接受但需最小化 | 只列相對路徑 |
| **17. i18n/在地化層** | 中文路徑 / report 名稱 | UTF-8 output | Windows encoding | 沿用 PYTHONUTF8 / PYTHONIOENCODING |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：future runtime 必補 checker fixture tests。
- [x] 動 Data 層 -> 已動 Documentation 層：artifact classes 必寫入 policy。
- [x] 動 DevOps 層 -> 已動 Process 層：不改 Actions / Pages，只列 advisory。
- [x] 動 Security 層 -> 已動 Observability 層：raw-free path-only output。

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_99_PLAN.md` | 可逆 | 主公已要求開 plan |
| 更新 handoff / active / risk / history | 可逆 | 本次只同步 DRAFT |
| future 新增 policy doc / checker / tests | 可逆 | runtime 需另核准 |
| 刪除 / 移動 reports | 半可逆到不可逆 | P99 禁止 |
| 改 `.gitignore` / Actions | 半可逆 | P99 禁止 |

### X2 盲區掃描

- [x] `data/reports` 有些是 production truth，不是垃圾。
- [x] `ui_previews` 既有 tracked 檔可能是 golden evidence，不可直接清。
- [x] `scratch/` 已 ignored，但 AI 仍可能讀它當作當前真相。
- [x] advisory guard 若太吵，會讓使用者忽略它。
- [x] stage guard 不能讀 raw post / report content，只能看 metadata。

### X3 時間敏感性

- 本計畫建立日期：2026-05-27。
- 本計畫過期日期：2026-06-03；若一週內未 freeze，需重新確認 `git status`、untracked reports 與 P98 audit 是否仍準。
- R-016 monitoring 至 2026-06-01；R-017 monitoring 至 2026-06-02。

### X4 多角度同行審查

- **主公視角**：P99 要讓「哪些檔案不該不小心推上去」變成機器會提醒，而不是要主公記一堆路徑。
- **紅隊 / 技術長視角**：最大災難是誤刪 production report 或讓 checker 輸出 raw data；P99 只 advisory + raw-free。
- **接手者視角**：下一個 AI 要一眼知道 P99 是 DRAFT，不是 cleanup runtime。
- **X4-J 自動化工具邊界**：stage guard 只能指出風險，不可自動 unstage / delete。
- **X4-K 使用者端審查官**：P99 不是網站品質修復，不會直接修芽芽/舊文章；那是 R-017/P104 線。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | checker false positive 讓每次 commit 都變吵 | 中 | 中 | 流程 | P99 runtime advisory-only，不接 blocking hook |
| R2 | policy 分類錯，把 production report 誤列為可清理 | 中 | 高 | 資料 / 部署 | P99 不刪，只分類；cleanup 另開 |
| R3 | checker 讀檔內容造成 raw data / secret 外洩 | 低 | 高 | 安全 / 隱私 | metadata-only，不讀內容 |
| R4 | P99 scope 漂移成 root debris 或 skill cleanup | 中 | 中 | Scope | root legacy 留 P100；skill 留 P102 |
| R5 | `.gitignore` 變更破壞 daily report commit | 低 | 高 | DevOps | P99 禁止 `.gitignore` 變更 |

**高風險加權檢查（META4）**：
- 高風險數量：2 項。
- 加權分數：6 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；P99 plan 可建立，但 runtime / cleanup 需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 Plan / Boundary Lock** | 建立 P99 plan、R-020、handoff、active、history | 避免和 cleanup 混線 | plan lint / governance checks PASS |
| **S1 Artifact Policy Draft** | 定義 keep/generated/scratch/artifact/quarantine/decision classes | 路徑判斷靠人腦 | policy table |
| **S2 Stage Guard Design** | 設計只看 staged paths 的 advisory checker | 誤 stage 無提醒 | checker spec |
| **S3 Runtime Guard Implementation（future）** | 新增小型 script + tests | 防復發 | tests + sample output |
| **S4 Observation / Promote Criteria（future）** | 定義何時 advisory 可升級 | checker 過早 blocking | promotion criteria |

---

## 10. 影響檔案清單

**P99 plan draft 新增**：
- `docs/PHASE_99_PLAN.md`

**P99 plan draft 修改**：
- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`

**P99 future runtime 候選，不在 plan draft 實作**：
- `docs/GENERATED_ARTIFACT_POLICY.md`
- `scripts/check_generated_artifact_hygiene.py`
- `tests/test_generated_artifact_hygiene.py`
- `docs/OPERATIONS_RUNBOOK.md`（只有新增 issue code 時）

**明確不修改**：
- `.gitignore`
- `.github/workflows/*`
- `data/reports/*`
- `ui_previews/*`
- `scratch/*`
- runtime code under `analyzer/`, `reporter/`, `scrapers/`

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P99 plan 或 runtime 刪除 / 移動 / rename 檔案。
- [ ] P99 改了 `.gitignore` 或 GitHub Actions。
- [ ] stage guard 讀出 raw report / raw post content。
- [ ] checker false positive 太高，造成主公無法順利 commit。
- [ ] 有任何「我以為這只是 generated，結果是 production truth」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-99-generated-artifact-hygiene.md`

---

## 12. Forbidden Work（P99 邊界）

- 不刪檔。
- 不搬檔。
- 不 rename。
- 不改 `.gitignore`。
- 不改 runtime code。
- 不改 GitHub Actions / Pages deployment。
- 不 stage generated reports、scratch、raw artifact、舊 untracked skill 暫存。
- 不導入 RTK 或新工具。
- 不把 advisory guard 升 strict gate。

---

## Pre-flight 多視角體檢（M1+M1.5+M2）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | stage guard 若讀內容會外洩 raw data；P99 限定 path metadata。 |
| **X4-B 接手者** | 接手者需要看到 P99 是 DRAFT / policy plan，不是 cleanup 已開始。 |
| **X4-C 災難情境** | 災難是誤刪 Pages 需要的 report；P99 禁止刪檔。 |
| **X4-D 5 年後** | 五年後需要 policy + checker，比手動記路徑可靠。 |
| **X4-E 終端 vs IDE** | 終端適合 staged-path checker；IDE 適合看 policy。 |
| **X4-F 跨平台 Win/Mac/Linux** | path matching 必須用 `/` normalized path，不依賴 Windows-only 分隔符。 |
| **X4-G 主公個人視角** | 主公不需要分辨什麼能 stage；checker 要用白話提示風險。 |
| **X4-H 觀測 / 治理** | P99 觀測是 checker warning 數、false positive、是否誤 stage 下降。 |
| **X4-I 主公可見性** | 主公看不到 AI 是否把 old reports 放進 commit；P99 guard 要把它亮出來。 |
| **X4-J 自動化建議性工具邊界** | guard 只能 advisory；不能自動 unstage / delete。 |
| **X4-K 使用者端審查官** | 不要把 P99 誤講成網站 bug 修復；它是 commit hygiene。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步 | 觸發；P99 只建 policy/guard plan。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | raw data / irreversible action | 觸發；metadata-only，不刪檔。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公是否誤解效果 | 觸發；P99 不修前台內容。 |
| **Jimmy 型文件主筆** | 改 docs / handoff 時觸發 | 文件可追溯 | 觸發；handoff / active / risk / history 同步 DRAFT。 |
| **Marcus 型數據分析師** | 涉及 inventory 時觸發 | P98 evidence | 觸發；使用 P98 metadata，不重跑重掃大檔。 |
| **Oliver 型設計審查** | 涉及 UI previews 時觸發 | golden preview 風險 | 條件觸發；P99 不搬 previews。 |
| **Penny 型 CFO** | 涉及成本時觸發 | 減少返工成本 | 觸發；advisory guard 低成本高 ROI。 |
| **Jason 型執行 / DevOps** | 涉及 deploy artifacts 時觸發 | Pages / Actions | 觸發；P99 不改 deploy。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | policy 可能變成「刪報告」的包裝。 | **S 級** | 0 | P99 禁止刪檔，cleanup 另開。 | 入計畫範圍 |
| 2 | production report / Pages artifact 被 checker 誤判為垃圾，導致未來 cleanup 誤刪。 | **S 級** | 0 | P99 只 advisory，不標任何 tracked production report 為可刪；cleanup 另開且需 rollback policy。 | 入 RISK_REGISTRY |
| 3 | checker false positive 會讓 commit 變痛苦。 | A 級 | 0 | runtime 只 advisory，不接 strict gate。 | 入 RISK_REGISTRY |
| 4 | path-only checker 可能漏掉內容型 raw secret。 | A 級 | 0 | P99 目標是 artifact boundary，不取代 secret scan。 | 入計畫範圍 |
| 5 | `.gitignore` 不改，是否沒效果？ | B 級 | 0 | 先讓風險可見，穩定後才談 ignore/promotion。 | 入計畫範圍 |
| 6 | report variants 可能該刪，但 P99 不刪會太慢。 | B 級 | 0 | P99 防誤動；P100+ 再做可回滾 cleanup。 | 入計畫範圍 |
| 7 | P99 會不會跟 R-017 content trust 打架？ | A 級 | 0 | 不處理報告內容，只處理 commit hygiene。 | 入計畫範圍 |
