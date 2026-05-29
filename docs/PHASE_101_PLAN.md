# Phase P101 計畫書 — Known Issue Guard Index（CLOSED）

> 狀態：CLOSED。主公於 2026-05-29 指定「P101 Known Issue Guard Index」，同日核准 `P101 plan freeze` 與 `P101 runtime`。本 Phase 已完成 known issue guard index、advisory-only checker 與 focused tests；未改既有 checker、未升 strict gate、未清理檔案、未新增自動化 gate。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P101 |
| **Phase 名稱** | Known Issue Guard Index |
| **建立日期** | 2026-05-29 |
| **所屬 Program** | R-019 Project Self-Optimization Flywheel Program |
| **新風險帳** | R-022 Known issue guard index drift / false confidence |
| **影響半徑** | 標準（plan 5 檔；future runtime 約 3-5 檔，仍需另核准） |
| **預估投入時數** | plan 0.8h；runtime 2-3h |
| **Token budget** | plan 16K；runtime 35K |
| **負責模型** | GPT-5.3-Codex（docs / metadata index / checker plan）；若 runtime 要修改多個既有 checker，升 GPT-5.5 高並另開 gate |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P100 runtime | CLOSED / pushed | Reference only | P100 root hygiene guard 作為 P101 index source，不再修改 | `6e3919d` 已推送 | AI / 主公 |
| P101 plan | DRAFT | FROZEN | known issue guard index 計畫已凍結，不實作 index/checker | 主公核准 `P101 plan freeze` | 主公 / AI |
| P101 runtime | Pending approval | CLOSED | 已新增 index doc / advisory checker / focused tests | 主公核准 `核准 P101 runtime` 後完成驗證 | 主公 / AI |

---

## 1. 目標 (Objective)

把 AOV 已知問題的防線整理成單一索引：每個 risk / known issue 都要能追到「人類文件、機器 guard、驗證指令、狀態、下一步」。P101 的目標不是再新增一堆規則，而是讓未來 AI 不用靠聊天記憶猜「這個問題以前怎麼防復發」。

目標索引形狀：

```text
Known issue / risk -> human doc -> machine guard -> focused check -> state -> owner / next action
```

## 2. 觸發背景 (Why Now)

P98 audit 指出專案已經有多條 guard，但散在 risk registry、phase plan、runbook、checker、tests、config 與 handoff 中。P99/P100 已把 generated artifacts 與 root debris 轉成 guard；下一步需要一張總索引避免防線散落。

| Evidence | 目前位置 | P101 要處理的問題 |
|---|---|---|
| R-017 content trust | `docs/CONTENT_TRUST_KNOWN_ISSUES.md`、`configs/content_trust_known_issues.yaml`、`scripts/check_report_content_trust.py`、tests | 有人類/機器 guard，但沒有總索引 |
| R-016 production SLO | `scripts/slo_checker.py`、`scripts/system_doctor.py`、`scripts/cost_cache_governance.py`、tests、runbook | guard 很強，但散在多檔 |
| R-018 RTK | `docs/PHASE_97_RTK_EVALUATION.md`、risk registry | 有 evaluation 裁決，但尚無 repo-level checker |
| R-020 generated artifact hygiene | `docs/GENERATED_ARTIFACT_POLICY.md`、`scripts/check_generated_artifact_hygiene.py`、tests | guard 已建立，需納入 index |
| R-021 root legacy hygiene | `docs/ROOT_LEGACY_QUARANTINE.md`、`scripts/check_root_legacy_hygiene.py`、tests | guard 已建立，需納入 index |
| Older open risks | `docs/RISK_REGISTRY.md` | 有些只有人工 SOP，沒有機器 guard；需清楚標示 |

## 2.1 問題定義

P101 解的是「known issue guard discoverability」問題，不是新增所有 missing checker。

| 不解的事 | 原因 | 轉交 |
|---|---|---|
| 立刻補齊所有 missing guards | 會膨脹成多戰線 runtime | P102+ 或各 risk follow-up |
| 關閉 R-016 / R-017 monitoring | 需要觀察期到期與 production evidence | 到期裁決另開 |
| 清理 generated/root artifacts | 已由 P99/P100 guard 管邊界，cleanup 另開 | P100.1 / future cleanup |
| 安裝 RTK | P97 裁決 install blocked | future isolated pilot |
| 改 existing checkers | P101 plan 不改 runtime | runtime 另核准 |

## 2.2 方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 只靠 RISK_REGISTRY | 不新增 index | 零成本 | guard / test / command 不集中，未來仍要翻多檔 | 不採用 |
| B. 新增人工 index doc | 建 `docs/KNOWN_ISSUE_GUARD_INDEX.md` | 低風險、可讀 | 可能漂移 | runtime 候選 |
| C. 人工 index + advisory checker | index doc 加 `scripts/check_known_issue_guard_index.py` | 可防 drift | 需維護 schema / fixture | P101 runtime 建議 |
| D. Strict gate | index 漏項即阻擋 commit | 最強 | false positive 高，會拖慢治理 | P101 不採用 |

---

## 3. Entry Criteria（入口條件）

- [x] P100 runtime 已完成並推送：`6e3919d` 已在 origin/main。
- [x] P99 / P100 已建立 artifact / root hygiene advisory guards。
- [x] R-017 / R-016 已有內容可信度與 production SLO 類 guard。
- [x] P98 audit 將 `P101 Known Issue Guard Index` 列為 P100 後的高 ROI 候選。
- [x] 主公指定：`P101 Known Issue Guard Index`。
- [x] P101 plan 限制為計畫，不新增 runtime index/checker、不改既有 checker。

## 4. Exit Criteria（退出條件）

P101 plan draft 退出條件：
- [x] `docs/PHASE_101_PLAN.md` 建立並通過 `scripts/lint_phase_plan.py`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 R-019 / R-022 / P101 DRAFT，並校正 P100 latest commit 為 `6e3919d` 已推送。
- [x] `docs/RISK_REGISTRY.md` 建立 R-022 Open 風險。
- [x] `TASK_HISTORY.md` 追加 P101 plan draft 物理真相。
- [x] `git diff --check`、handoff truth、governance doctor、P99/P100 hygiene staged checks 通過。

P101 plan freeze 退出條件：
- [x] 主公核准 `P101 plan freeze`。
- [x] `docs/PHASE_101_PLAN.md` 狀態改為 FROZEN。
- [x] handoff / active / risk / history 同步 P101 FROZEN。
- [x] 不新增 runtime index/checker。

P101 runtime 退出條件：
- [x] 產出 `docs/KNOWN_ISSUE_GUARD_INDEX.md`。
- [x] 至少列入 R-016 / R-017 / R-018 / R-020 / R-021 / governance drift 類風險。
- [x] 每列包含：risk id、issue name、human doc、machine guard、focused command、state、gap、next action。
- [x] 若新增 checker，必須 advisory-only 並補 tests。
- [x] 明確標記「human-only / missing machine guard」項，不能營造 false confidence。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 2-3h |
| 預估收益等級 | 高 |
| 收益描述 | 降低 future AI 找不到 guard、重修已解問題、或誤以為某風險已有機器防線的成本 |
| ROI 結論 | 值得做；先 index，後續再針對 missing guard 拆小 phase |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | plan 不改 code；future runtime 可新增小型 index checker | 把 P101 偷渡成大改多個 checker | Forbidden Work 明列不改既有 checker |
| **2. 邏輯層 (Logic)** | 建 index schema：risk -> human doc -> machine guard -> command -> state -> gap | 漏列或誤列 guard 造成 false confidence | runtime 需標 missing / human-only |
| **4. 測試層 (Testing)** | future checker 必補 fixture tests；plan 只跑 lint/governance | index 漂移不會被抓 | runtime 才決定 checker ROI |
| **10. 安全層 (Security)** | index 不讀 raw reports/logs，只列 path / command / status | raw content 外洩 | metadata-only |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 把 guard discoverability 與 product runtime 分離 | index 變成 runtime dependency | 放 docs/scripts，不進 analyzer/reporter |
| **5. 資料層 (Data)** | 索引 guard path 與 command，不複製 raw data | 舊資料/舊報告被誤當 current | 只列 evidence source |
| **6. 可觀察性層 (Observability)** | index 顯示 guard state / gap / next action | 防線存在但不可見 | table schema |
| **7. 韌性層 (Resilience)** | missing guard 標清楚，不阻擋 release | false gate 卡住流程 | advisory-first |
| **13. 可維護性層 (Maintainability)** | 建 single source of guard map | 新人接手仍翻多檔 | `docs/KNOWN_ISSUE_GUARD_INDEX.md` runtime 候選 |
| **14. 文件層 (Documentation)** | P101 plan / risk / handoff / history 同步 | 文檔漂移 | handoff truth / governance doctor |
| **15. 流程層 (Process)** | Plan -> freeze -> runtime index -> optional checker -> observe | index 後馬上大修 | follow-up phase |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | runtime 可能掃多檔 | 只讀 metadata / small docs | 慢或 token 高 | 不全讀 TASK_HISTORY |
| **9. UX/A11y 層** | N/A | 不改前台 UI | 誤以為修網站 | 明列非網站 phase |
| **11. 部署層 (DevOps)** | guard commands 含 CI / Daily Monitor | 不改 workflows | 誤影響 GHA | plan 不改 Actions |
| **12. 成本層 (Cost)** | 降低返工與讀檔成本 | 少翻多檔、少重修 | index 維護成本 | runtime 才評估 checker ROI |
| **16. 隱私/合規層 (Privacy)** | known issues 可能指向 raw reports/logs | 不複製 raw content | 泄漏 raw post/log | path-only |
| **17. i18n/在地化層** | 中文 issue / 英文 checker 混用 | 表格用繁中說明，保留 command 原文 | 名稱混亂 | risk id + command path |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：future checker 必補 tests。
- [x] 動 Documentation 層 -> 已動 Process 層：handoff / active / risk / history 同步。
- [x] 動 Security 層 -> 已動 Privacy 層：metadata-only，不複製 raw content。

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_101_PLAN.md` | 可逆 | 主公指定 P101 |
| 更新 handoff / active / risk / history | 可逆 | 本次只同步 DRAFT |
| 新增 index doc / checker / tests | 可逆 | 主公已核准 P101 runtime |
| 修改既有 checker / strict gate | 半可逆 | P101 plan 禁止 |

### X2 盲區掃描

- [x] 有人類文件不代表有機器 guard。
- [x] 有 checker 不代表 cloud / production evidence 一定通過。
- [x] 已 CLOSED 的 phase 仍可能有 Open risk。
- [x] R-016 / R-017 monitoring 有日期，到期需裁決，不可長期懸空。
- [x] P99/P100 advisory guards 不等於 cleanup 已批准。

### X3 時間敏感性

- 本計畫建立日期：2026-05-29。
- 本計畫過期日期：2026-06-05；若一週內未 freeze，需重新確認 RISK_REGISTRY 與 latest checker list。
- R-016 monitoring 至 2026-06-01；R-017 monitoring 至 2026-06-02。

### X4 多角度同行審查

- **主公視角**：P101 要讓「以前修過什麼、靠什麼防復發」一眼看懂。
- **紅隊 / 技術長視角**：最大風險是 index 讓人誤以為風險都有 guard；missing guard 必須明標。
- **接手者視角**：需要從 risk id 直接找到 doc、checker、test、command。
- **X4-J 自動化工具邊界**：future checker 只能 advisory；不能因 index 漏項直接 block。
- **X4-K 使用者端審查官**：P101 不修網站內容；它降低 future debug 返工。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | index 漏列重要 guard，未來 AI 仍找不到防線 | 中 | 中 | 文件 / 流程 | runtime 從 RISK_REGISTRY + known docs + scripts/tests 交叉建立 |
| R2 | index 誤列 human-only SOP 為 machine guard | 中 | 高 | 邏輯 / 治理 | schema 必含 `guard_status` / `gap` |
| R3 | index 很快漂移 | 中 | 中 | 維護性 | optional checker / review cadence |
| R4 | P101 膨脹成補所有 checker | 中 | 中 | Scope | missing guard 只登記，另開 phase |
| R5 | raw report/log 被複製進 index | 低 | 高 | 隱私 / 安全 | metadata-only，僅列 path/command/status |

**高風險加權檢查（META4）**：
- 高風險數量：2 項。
- 加權分數：6 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；P101 plan 可建立，但 runtime / checker 實作需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 Plan / Boundary Lock** | 建立 P101 plan、R-022、handoff、active、history | 避免 plan 變 runtime | plan lint / governance checks PASS |
| **S1 Guard Source Inventory（future）** | 掃 RISK_REGISTRY / known docs / scripts / tests | guard 散落 | source list |
| **S2 Index Schema（future）** | 定欄位：risk id / human doc / machine guard / command / gap | false confidence | schema |
| **S3 Index Runtime（future）** | 建 `docs/KNOWN_ISSUE_GUARD_INDEX.md` | 接手成本高 | index doc |
| **S4 Optional Advisory Checker（future）** | 檢查 index 是否漏掉 known risk / guard path | 漂移 | tests + advisory output |

---

## 10. 影響檔案清單

**P101 plan draft 新增**：
- `docs/PHASE_101_PLAN.md`

**P101 plan draft 修改**：
- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`

**P101 runtime 新增**：
- `docs/KNOWN_ISSUE_GUARD_INDEX.md`
- `scripts/check_known_issue_guard_index.py`
- `tests/test_known_issue_guard_index.py`

**明確不修改**：
- existing checkers under `scripts/`
- existing tests under `tests/`
- `.gitignore`
- `.github/workflows/*`
- product runtime under `analyzer/`, `reporter/`, `scrapers/`
- generated reports / scratch / root cleanup candidates

---

## 10.5 Runtime Physical Truth（2026-05-29）

P101 runtime 已完成：

- `docs/KNOWN_ISSUE_GUARD_INDEX.md`
  - 建立 metadata-only guard map。
  - 主表欄位：risk id / issue / human doc / machine guard / focused command / state / gap / next action。
  - 納入 R-016 / R-017 / R-018 / R-019 / R-020 / R-021 / R-022 / GOV-HANDOFF。
  - R-018 明確標 `missing-machine-guard` / `human-only`，避免誤稱已有 guard。
  - 另列 Human-only Backlog：R-001 / R-002 / R-003 / R-004 / R-006 / R-011 / R-012 / R-013。
- `scripts/check_known_issue_guard_index.py`
  - advisory-only。
  - 預設只讀 `docs/KNOWN_ISSUE_GUARD_INDEX.md`。
  - 檢查 required columns / required rows / required guard tokens / human-only gap markers。
  - default findings exit 0；顯式 `--strict` 才在 findings 時 exit 1。
  - 不讀 raw reports、raw logs、raw queues、generated report bodies 或 secrets。
- `tests/test_known_issue_guard_index.py`
  - 覆蓋 actual index clean。
  - 覆蓋 missing required entry。
  - 覆蓋 human-only row 未標 gap。
  - 覆蓋 CLI JSON 與 strict/default exit behavior。

P101 runtime 未做：

- 未修改既有 P96/P99/P100/R-016 checkers。
- 未改 GitHub Actions / Pages。
- 未接 pre-commit / CI strict gate。
- 未清理、搬移、rename、刪除任何 root/generated/scratch 檔。
- 未導入 RTK 或新工具。

Runtime focused verification：

- `py scripts\check_known_issue_guard_index.py --repo-root .`：PASS / no advisories。
- `py scripts\check_known_issue_guard_index.py --repo-root . --json`：PASS / `[]`。
- `py -m pytest -q tests\test_known_issue_guard_index.py`：`4 passed`。
- `py -m pytest -q tests\test_known_issue_guard_index.py tests\test_generated_artifact_hygiene.py tests\test_root_legacy_hygiene.py`：`14 passed`。
- `py scripts\check_known_issue_guard_index.py --repo-root . --strict`：PASS / no advisories。
- `git diff --check`：PASS（僅 CRLF/LF 工作樹提示，無 whitespace error）。
- `py scripts\lint_phase_plan.py docs\PHASE_101_PLAN.md`：PASS。
- `py scripts\check_handoff_truth.py --repo-root .`：PASS / `HND000`。
- `py scripts\governance_doctor.py --repo-root .`：PASS / `GOV000`。
- P99/P100 hygiene explicit-path checks：PASS / no advisories。

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P101 把 human-only SOP 誤標為 machine guard。
- [ ] P101 漏列 R-016 / R-017 / R-020 / R-021 這類 active guard。
- [ ] P101 runtime 修改既有 checker 造成回歸。
- [ ] P101 index 複製 raw report / raw log content。
- [ ] P101 checker 被接成 strict gate。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-101-known-issue-guard-index.md`

---

## 12. Forbidden Work（P101 邊界）

- 不改 existing checkers。
- 不改 runtime code。
- 不改 GitHub Actions / Pages deployment。
- 不改 `.gitignore`。
- 不清理、不搬檔、不 rename、不刪檔。
- 不讀 raw report / raw log content。
- 不全讀 `TASK_HISTORY.md`。
- 不把 advisory guard 升 strict gate。
- 不補所有 missing guard；只登記 gap。
- 不導入 RTK 或新工具。

---

## Pre-flight 多視角體檢（M1+M1.5+M2）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | index 不能複製 raw content；只能列 path / command / state。 |
| **X4-B 接手者** | 接手者需要從 risk id 直接找到防線與驗證命令。 |
| **X4-C 災難情境** | 災難是 index 誤稱已防住，實際只有人工 SOP。 |
| **X4-D 5 年後** | 五年後能靠 index 找到 guard，而不是翻 TASK_HISTORY。 |
| **X4-E 終端 vs IDE** | 終端適合跑 checker / rg source inventory；IDE 適合讀 index。 |
| **X4-F 跨平台 Win/Mac/Linux** | commands 要用專案現行 PowerShell / Python style，避免 shell-only 路徑。 |
| **X4-G 主公個人視角** | 主公不需要記 checker 名稱；index 要把「要跑哪條」寫清楚。 |
| **X4-H 觀測 / 治理** | P101 成功訊號是每個重要 risk 有 guard status，而不是新增多少程式。 |
| **X4-I 主公可見性** | 主公看不到哪些防線其實只存在對話裡；P101 要揭露 gap。 |
| **X4-J 自動化建議性工具邊界** | optional checker 只能 advisory，不能直接 block。 |
| **X4-K 使用者端審查官** | P101 不修前台內容；它避免未來內容 bug 重修時找不到防線。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步 | 觸發；P101 只開 guard index plan。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | false confidence / raw content | 觸發；missing guard 必須標 gap。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公是否誤解效果 | 觸發；P101 不修網站，只修防線可見性。 |
| **Jimmy 型文件主筆** | 改 docs / handoff 時觸發 | 文件可追溯 | 觸發；handoff / active / risk / history 同步 DRAFT。 |
| **Marcus 型數據分析師** | 涉及 inventory 時觸發 | risk/checker source inventory | 觸發；只做 metadata source list。 |
| **Oliver 型設計審查** | 涉及 UI content risk 時觸發 | R-017 index coverage | 條件觸發；只索引，不修 UI。 |
| **Penny 型 CFO** | 涉及成本時觸發 | 降低返工成本 | 觸發；少翻多檔，少重修。 |
| **Jason 型執行 / DevOps** | 涉及 check commands 時觸發 | command 可重跑性 | 觸發；commands 用現有 scripts。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | P101 可能把「只有文件」誤寫成「有機器 guard」。 | **S 級** | 0 | index schema 必含 guard status / gap。 | 入 RISK_REGISTRY |
| 2 | P101 可能變成補完所有 checker 的大包。 | **S 級** | 0 | plan 明列 missing guard 只登記，另開 phase。 | 入計畫範圍 |
| 3 | index 會漂移，過幾週又不準。 | A 級 | 0 | runtime 評估 advisory checker / review cadence。 | 入 RISK_REGISTRY |
| 4 | raw report/log 被複製到 index。 | **S 級** | 0 | metadata-only，只列 path/command/status。 | 入 RISK_REGISTRY |
| 5 | P101 是否重複 RISK_REGISTRY？ | A 級 | 0 | RISK_REGISTRY 是風險帳；P101 index 是 guard map。 | 入計畫範圍 |
| 6 | P101 會不會修網站內容？ | B 級 | 0 | 不修；R-017/P104 另線。 | 入計畫範圍 |
| 7 | 沒有 runtime index 時 plan 有何價值？ | B 級 | 0 | 先鎖 schema / scope，避免 runtime 膨脹。 | 入計畫範圍 |
