# Phase P102 計畫書 — Missing Guard Backlog / Monitoring Review（DRAFT）

> 狀態：DRAFT。主公於 2026-05-29 指定「P102 Missing Guard Backlog / Monitoring Review Plan」。本 Phase 只建立計畫：不關閉 R-016 / R-017、不補所有 missing guards、不修改既有 checker、不接 strict gate、不清理檔案。Runtime 需主公另行核准。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P102 |
| **Phase 名稱** | Missing Guard Backlog / Monitoring Review |
| **建立日期** | 2026-05-29 |
| **所屬 Program** | R-019 Project Self-Optimization Flywheel Program |
| **新風險帳** | R-023 Monitoring review false closure / missing guard prioritization drift |
| **影響半徑** | 標準（plan 約 6 檔；future runtime report-only 約 4-6 檔，另需核准） |
| **預估投入時數** | plan 0.8h；runtime 1.5-2.5h |
| **Token budget** | plan 16K；runtime 30K |
| **負責模型** | GPT-5.3-Codex（evidence review / docs）；若 runtime 要實作新 checker，另開小 Phase |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P101 runtime | CLOSED / pushed | Reference only | Known issue guard index 作為 P102 backlog source | `94292e4` 已推送 | AI / 主公 |
| P102 plan | Not started | DRAFT | 只建立 monitoring review / missing guard backlog 計畫 | 主公指定 P102 | 主公 / AI |
| P102 runtime | Not started | Pending approval | 未來可做 report-only monitoring review 與 backlog ranking | 需主公另行核准 `P102 plan freeze` 後再核准 runtime | 主公 |

---

## 1. 目標 (Objective)

P102 的目標是把 P101 索引中「還只是 human-only / missing-machine-guard」的問題排出優先順序，並同時檢查 R-016 / R-017 monitoring 是否有足夠證據進入下一個裁決。

成功輸出應該回答三個問題：

```text
1. R-016 / R-017 現在能不能關？如果不能，卡在哪個證據？
2. P101 human-only backlog 裡，哪 1-2 個最值得下一個小 Phase 機器化？
3. 哪些問題應該繼續觀察，不該現在動？
```

## 2. 觸發背景 (Why Now)

P101 已建立 `docs/KNOWN_ISSUE_GUARD_INDEX.md`，但索引明確揭露仍有多個 human-only / partial guard 項。另一方面，R-016 / R-017 仍在 monitoring window：

- R-016 observation window：2026-05-25 到 2026-06-01。
- R-017 observation window：2026-05-26 到 2026-06-02。
- 目前日期：2026-05-29，尚未到兩者收官日。

P102 因此不是 closeout，而是「證據盤點 + missing guard 排序」。

## 2.1 目前證據（2026-05-29 local）

| Evidence | 結果 | P102 解讀 |
|---|---|---|
| Latest pushed commit | `94292e4 feat: 新增 known issue guard index` 已在 `origin/main` | P101 已可作為 P102 source |
| Latest production report | `data/reports/aov_report_2026-05-29.html` exists | 可做 R-017 content trust review |
| Latest manifest | `data/runs/2026-05-29/run_manifest.json` exists | 可做 R-016 monitoring evidence |
| 5/29 manifest | mode=`production`, publish_eligible=`true`, quality tier=`production_local_only`, analysis_source=`mixed`, llm_calls=`9`, budget cooldown=`false`, provider routing disabled | 5/29 本日 production 看起來可發布，但不代表 7 日窗全過 |
| SLO checker | `SLO002` current blocking：2026-05-27 manifest gap；`SLO003` current blocking：blocking_days=1 | R-016 不可 close，只能列為 monitoring still open |
| System doctor | no blocking/degraded；current DOC007 advisory，DOC018/DOC019 residual advisory | 本日 doctor 可接受，但 coverage advisory 仍需觀察 |
| Cost/cache governance | `CCG005` current degraded：total_llm_calls=31 threshold=20 latest_llm_calls=9；CCG006 current advisory；CCG007/CCG008 residual | 成本 / LLM call 仍有 current degraded，不可忽略 |
| Content trust checker | 2026-05-29 focus title PASS、forbidden focus title PASS、unknown dates PASS、focus recent section PASS/absent | R-017 最新報告沒有重現芽芽/圖倫與舊文顯性錯誤 |
| Guard index checker | no advisories | P101 index 本身目前一致 |

## 2.2 不解的事（Out of Scope）

| 不解的事 | 原因 | 轉交 |
|---|---|---|
| 直接關閉 R-016 / R-017 | monitoring window 未到，且 SLO/CCG 還有 current issue | 2026-06-01 / 2026-06-02 後另做裁決 |
| 一次補完所有 human-only guards | 會膨脹成多戰線大包 | P103+ 小 Phase |
| 把 P101 checker 接成 strict gate | P101 明確 blocked；false positive 尚未觀察 | future promote review |
| 修 CCG005 成本 degraded | 需要另看 selection / cache / budget 根因 | future cost follow-up |
| 清理 generated/root/scratch | 已由 P99/P100 guard 管邊界；cleanup 另開 | P100.1 / cleanup phase |
| RTK pilot | P97 裁決 install blocked | future isolated pilot |

## 2.3 方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 直接 close R-016/R-017 | 根據 5/29 最新 report PASS 就關 | 快 | 忽略 observation window / SLO002 / CCG005 | 不採用 |
| B. 只做 missing guard backlog | 不看 production evidence | 專注 | 會錯過 monitoring 現況 | 不採用 |
| C. Monitoring review + backlog ranking | 同時看 R-016/R-017 evidence 與 P101 backlog | 保守、可決策 | 不能立即修所有問題 | 採用 |
| D. Runtime 直接補 top guard | P102 直接寫 checker | 推進快 | 還沒排序，容易選錯 | P102 不採用 |

---

## 3. Entry Criteria（入口條件）

- [x] P101 runtime 已完成並推送：`94292e4` 已在 origin/main。
- [x] `docs/KNOWN_ISSUE_GUARD_INDEX.md` 已列出 R-016 / R-017 / R-018 / R-019 / R-020 / R-021 / R-022 / human-only backlog。
- [x] 2026-05-29 production report 與 manifest 已存在。
- [x] 2026-05-29 content trust checker PASS。
- [x] 2026-05-29 SLO / cost governance 仍有 current issue，不能 close monitoring。
- [x] 主公指定：`P102 Missing Guard Backlog / Monitoring Review Plan`。

## 4. Exit Criteria（退出條件）

P102 plan draft 退出條件：
- [x] `docs/PHASE_102_PLAN.md` 建立並通過 `scripts/lint_phase_plan.py`。
- [x] `docs/RISK_REGISTRY.md` 建立 R-023 Open 風險。
- [x] `docs/KNOWN_ISSUE_GUARD_INDEX.md` 納入 R-023，且明確標 `human-only` / `plan-only`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 P102 DRAFT。
- [x] `TASK_HISTORY.md` 追加 P102 plan draft 物理真相。
- [x] focused governance / hygiene checks PASS。

P102 plan freeze 未來退出條件：
- [ ] 主公核准 `P102 plan freeze`。
- [ ] `docs/PHASE_102_PLAN.md` 狀態改為 FROZEN。
- [ ] handoff / active / risk / history 同步 P102 FROZEN。
- [ ] 不新增 runtime report / checker。

P102 runtime 未來退出條件：
- [ ] 產出 report-only monitoring/backlog review（候選：`docs/MISSING_GUARD_BACKLOG.md`）。
- [ ] R-016 / R-017 明確裁決：keep monitoring / escalate / ready for closeout date。
- [ ] human-only backlog 排出 top 1-3 候選與不做項。
- [ ] 不修改既有 checker、不接 strict gate、不 cleanup。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 1.5-2.5h |
| 預估收益等級 | 高 |
| 收益描述 | 避免誤關 monitoring；避免亂補低 ROI guard；把下一個小 Phase 選準 |
| ROI 結論 | 值得做；P102 是 P101 後的決策節點，不是大修 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | plan 不改 code；runtime 優先 report-only | 偷渡補 checker | 明列 P102 不直接實作 top guard |
| **2. 邏輯層 (Logic)** | 分開 monitoring evidence 與 missing guard priority | 把 latest PASS 誤當可 close | 明列 R-016/R-017 observation windows |
| **4. 測試層 (Testing)** | plan 跑現有 focused checks；runtime 若選 guard 再另開 test phase | 沒有新測試就宣稱修復 | P102 只排序，不宣稱修復 |
| **10. 安全層 (Security)** | 只讀 manifest/checker summaries，不複製 raw content | raw report/log/post 泄漏 | metadata-only |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / 不適用理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 讓 P102 作決策節點，不混進 runtime systems | scope 膨脹 | future guard 另開 P103+ |
| **5. 資料層 (Data)** | 只引用 5/29 manifest/report existence 與 checker output | 誤解資料缺口 | SLO002 manifest gap 保留 |
| **6. 可觀察性層 (Observability)** | 列出 SLO / doctor / cost / content trust / guard index evidence | 只看單一 PASS | 多證據矩陣 |
| **7. 韌性層 (Resilience)** | current degraded 不硬修，先判斷是否需 follow-up | 反覆成本回歸 | CCG005 入 runtime review |
| **13. 可維護性層 (Maintainability)** | backlog ranking 成為下一 phase 選題依據 | human-only 清單老化 | P101 index 更新 R-023 |
| **14. 文件層 (Documentation)** | P102 plan / risk / index / handoff / history 同步 | 文件漂移 | handoff truth / governance doctor |
| **15. 流程層 (Process)** | Plan -> freeze -> runtime report -> next phase selection | 一邊 review 一邊動工 | runtime 需另核准 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 涉及 cost governance | 記錄 CCG005 current degraded | 忽略 LLM calls | P102 不直接調參 |
| **9. UX/A11y 層** | R-017 涉及前台內容可信度 | 只查內容 trust，不改 UI | 誤以為修前端 | 明列不改 template |
| **11. 部署層 (DevOps)** | SLO/GHA/report/manifest | 不改 workflows | 影響 daily monitor | 只讀 evidence |
| **12. 成本層 (Cost)** | CCG005 current degraded | 保留為 review signal | 成本問題被忽略 | 可排 P103 cost follow-up |
| **16. 隱私/合規層 (Privacy)** | 可能接觸 reports/logs | 不複製 raw content | raw post 泄漏 | metadata-only |
| **17. i18n/在地化層** | 中文內容 trust | 保留繁中 issue 名稱與英文 command | 語意混亂 | risk id + command path |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：使用現有 checker outputs 作 evidence。
- [x] 動 Documentation 層 -> 已動 Process 層：handoff / active / risk / history 同步。
- [x] 動 Security 層 -> 已動 Privacy 層：metadata-only。

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_102_PLAN.md` | 可逆 | 主公指定 P102 |
| 新增 R-023 風險 | 可逆 | P102 plan 需要風險帳 |
| 更新 known issue guard index R-023 row | 可逆 | 防止 index 漂移 |
| future 產出 missing guard backlog report | 可逆 | runtime 需另核准 |
| close R-016 / R-017 | 半可逆 | P102 plan 禁止 |

### X2 盲區掃描

- [x] 5/29 report PASS 不代表 R-016 可關。
- [x] R-017 content trust PASS 不代表所有文章品質永久穩定。
- [x] SLO002 5/27 gap 是 current blocking，不能被 5/29 production 蓋掉。
- [x] CCG005 current degraded 表示 LLM call 成本仍要被看見。
- [x] Human-only backlog 不等於下一步全部要做。

### X3 時間敏感性

- 本計畫建立日期：2026-05-29。
- P102 plan 過期日期：2026-06-03；若 R-016 / R-017 window 到期後才 runtime，需重新跑 evidence。
- R-016 monitoring 到 2026-06-01。
- R-017 monitoring 到 2026-06-02。

### X4 多角度同行審查

- **主公視角**：主公需要知道現在能不能安心關 bug 主線；P102 會說清楚「不能關的證據」。
- **紅隊 / 技術長視角**：最大風險是拿最新 PASS 掩蓋 window 內 current blocking；P102 必須保留 SLO002/CCG005。
- **接手者視角**：接手者需要看到下一個 guard 候選排序，而不是一長串未整理 backlog。
- **X4-J 自動化工具邊界**：P102 不 promote P101 checker，不新增 strict gate。
- **X4-K 使用者端審查官**：P102 不修網站 UI，但要保留 R-017 最新可見結果。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 誤把 5/29 content trust PASS 當成 R-017 可關 | 中 | 高 | 監控 / 內容可信度 | 明列 monitoring 到 2026-06-02 |
| R2 | 忽略 SLO002 / SLO003 current blocking 而關 R-016 | 中 | 高 | 後端 / 部署 | 明列 R-016 不 close |
| R3 | 一次補所有 missing guard 造成大 scope | 中 | 中 | 流程 | P102 runtime report-only |
| R4 | Backlog 排序只靠主觀印象 | 中 | 中 | 治理 | 使用 impact / recurrence / machine-ability / cost 四維度 |
| R5 | 複製 raw report/log 進 plan | 低 | 高 | 隱私 / 安全 | metadata-only |

**高風險加權檢查（META4）**：
- 高風險數量：3 項。
- 加權分數：7 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；P102 plan 可建立，但 runtime / closeout / checker 實作需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 Plan / Boundary Lock** | 建 P102 plan、R-023、index R-023 row、handoff、active、history | 避免 review 變 runtime | lint / governance PASS |
| **S1 Evidence Refresh（future）** | 重跑 latest SLO / doctor / cost / content trust / index checker | 單點證據誤導 | evidence table |
| **S2 Monitoring Review（future）** | 判斷 R-016 / R-017 keep monitoring / escalate / ready for closeout date | false closure | explicit decision |
| **S3 Missing Guard Ranking（future）** | 對 P101 human-only backlog 打分排序 | 亂補 guard | top 1-3 list |
| **S4 Next Phase Recommendation（future）** | 指定下一個小 Phase 候選與不做項 | scope 膨脹 | 主公可裁決 |

---

## 10. 影響檔案清單

**P102 plan draft 新增**：
- `docs/PHASE_102_PLAN.md`

**P102 plan draft 修改**：
- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `docs/KNOWN_ISSUE_GUARD_INDEX.md`
- `TASK_HISTORY.md`

**P102 future runtime 候選，不在 plan draft 實作**：
- `docs/MISSING_GUARD_BACKLOG.md`
- `docs/PHASE_102_PLAN.md` runtime status update
- `docs/RISK_REGISTRY.md` monitoring evidence update
- `docs/KNOWN_ISSUE_GUARD_INDEX.md` gap/next action update

**明確不修改**：
- existing checkers under `scripts/`
- existing tests under `tests/`
- `.gitignore`
- `.github/workflows/*`
- product runtime under `analyzer/`, `reporter/`, `scrapers/`
- generated reports / manifests / scratch / root cleanup candidates

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P102 誤關 R-016 / R-017。
- [ ] P102 忽略 SLO002 / CCG005 current issue。
- [ ] P102 runtime 偷渡實作 checker 或 strict gate。
- [ ] P102 將 raw report/log/post 內容寫入 docs。
- [ ] P102 backlog 排序導致下一 Phase 選錯且返工。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-102-missing-guard-monitoring-review.md`

---

## 12. Forbidden Work（P102 邊界）

- 不關閉 R-016 / R-017。
- 不補所有 missing guards。
- 不新增或修改 existing checker/tests。
- 不接 strict gate。
- 不清理 root/generated/scratch/untracked files。
- 不搬檔、不 rename、不刪檔。
- 不改 `.gitignore`。
- 不改 runtime code。
- 不改 GitHub Actions / Pages。
- 不讀 raw report/log/post content。
- 不導入 RTK 或新工具。

---

## Pre-flight 多視角體檢（M1+M1.5+M2）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊者會利用最新 PASS 掩蓋 window 內 gap；P102 必須保留 SLO002 與 CCG005。 |
| **X4-B 接手者** | 接手者需要知道哪些 guard 缺口排在前面，不該只看到 human-only 長表。 |
| **X4-C 災難情境** | 災難是 R-016/R-017 被太早 close，幾天後同類 bug 復發卻沒有 active risk。 |
| **X4-D 5 年後** | 五年後應能看出當時為什麼沒有關閉 monitoring，以及下一個 guard 為何被選中。 |
| **X4-E 終端 vs IDE** | 終端負責跑 SLO/doctor/cost/content checker；IDE 或 docs 負責閱讀 backlog ranking。 |
| **X4-F 跨平台 Win/Mac/Linux** | P102 指令以專案現有 PowerShell / Python style 表示，避免只在單一 shell 成立。 |
| **X4-G 主公個人視角** | 主公不需要自己分辨後端 monitoring 與前台內容可信度；P102 會分流說清楚。 |
| **X4-H 觀測 / 治理** | 成功訊號不是新增很多程式，而是產生可裁決的 evidence matrix 與 top guard 候選。 |
| **X4-I 主公可見性** | 主公看不到的是 5/27 manifest gap 與 CCG005 current degraded；P102 要把它們攤開。 |
| **X4-J 自動化工具邊界** | 任何 checker promotion 都不在 P102；strict gate 需另開 Phase。 |
| **X4-K 使用者端審查官** | P102 不修網站畫面，但會用 content trust checker 保護芽芽/圖倫與舊文問題不要被遺忘。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步 | 觸發；P102 是 decision phase。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | false close / evidence gap | 觸發；R-016/R-017 不可早關。 |
| **Patric 型使用者端審查官** | 固定必看 | 使用者可見內容可信度 | 觸發；5/29 content trust PASS 但仍 monitoring。 |
| **Jimmy 型文件主筆** | 改 docs / handoff 時觸發 | 文件可追溯 | 觸發；handoff / active / risk / history 同步。 |
| **Marcus 型數據分析師** | 涉及 evidence matrix 時觸發 | SLO / cost / checker outputs | 觸發；保留 SLO002/CCG005。 |
| **Oliver 型設計審查** | 涉及前台內容時觸發 | 是否誤改 UI | 觸發；P102 不改 template。 |
| **Penny 型 CFO** | 涉及成本時觸發 | CCG005 / LLM calls | 觸發；成本 degraded 進 review。 |
| **Jason 型執行 / DevOps** | 涉及 GitHub Actions / reports 時觸發 | manifest / deployment evidence | 觸發；不改 workflow，只讀 evidence。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 5/29 content trust PASS，很容易被誤用成 R-017 可以 close。 | **S 級** | 0 | R-017 monitoring 到 2026-06-02，不在 P102 plan close。 | 入計畫範圍 |
| 2 | SLO checker 已有 current blocking，若 P102 不記錄會造成 R-016 false close。 | **S 級** | 0 | SLO002/SLO003 明列入 evidence。 | 入 RISK_REGISTRY |
| 3 | CCG005 current degraded 代表成本面尚未穩定，P102 若只看 production PASS 會漏掉。 | **S 級** | 0 | CCG005 入 monitoring review，不直接修。 | 入計畫範圍 |
| 4 | Human-only backlog 很長，可能被主觀挑錯下一個 Phase。 | A 級 | 0 | Runtime 用 impact / recurrence / machine-ability / cost 排序。 | 入計畫範圍 |
| 5 | P102 可能偷渡補 checker，讓 plan 變大包。 | A 級 | 0 | 明列 report-only；任何 checker 另開小 Phase。 | 入計畫範圍 |
| 6 | 新增 R-023 後若不更新 index，P101 index 立刻漂移。 | A 級 | 0 | P102 plan draft 同步新增 R-023 row。 | 入計畫範圍 |
| 7 | P102 可能讀 raw report/log 造成隱私與 token 成本。 | **S 級** | 0 | metadata-only，只引用 checker output 與 manifest summary。 | 入 RISK_REGISTRY |
