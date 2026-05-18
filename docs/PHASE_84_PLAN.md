# Phase P84 計畫書 — Long-Term Governance（核准版）

> 草案日期：2026-05-17
> 凍結日期：2026-05-17
> 核准日期：2026-05-17
> 狀態：APPROVED（P84.3 已完成；下一步 P84.4 Risk registry / runbook governance）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P84 |
| 名稱 | Long-Term Governance |
| 影響半徑 | 重大（預估 10+ 檔，治理腳本、CI、文件、runbook、handoff 皆可能受影響） |
| 預估投入時數 | 4-7 h |
| Token budget | 55K-85K tokens |
| 負責模型 | GPT-5.3-Codex 高；若治理規則互相矛盾或連 3 輪無進展，提醒切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P84 計畫 | DRAFT | FROZEN | 計畫已完成並通過 pre-flight，尚不可動工 | 本文件建立、17 層/M1/M2 完成、狀態文件同步 | AI 建立，主公核准後才進 APPROVED |
| P77-P84 program | P84 DRAFT | P84 FROZEN | 總戰役進入最後治理 Phase 的待核准狀態 | `docs/PHASE_84_PLAN.md` 凍結 | AI 更新，主公核准後動工 |
| P84 實作 | FROZEN | APPROVED | 可依本計畫做 retention/SLO/handoff truth 等實作 | 主公已明確核准 P84（2026-05-17） | 主公核准，AI 執行 |

## 1. 目標

把 P77-P83 建好的可靠性能力收束成可長期維護的治理層：retention 不爆倉、SLO 會升級、handoff truth 可機械驗證、風險/runbook 可持續更新、成本/cache hit 可觀測，讓系統半年後仍能被新視窗與接手者正確操作。

## 2. 觸發背景

P77-P83 已完成主鏈路止血、manifest、doctor、promotion、replay/backfill、timezone/idempotency、data quality/security。現在剩下的風險不是單點 bug，而是長期熵增：報告與 debug bundle 堆積、連續無 production 沒有人升級、handoff 被舊 archive 誤導、risk registry/runbook 漂移、LLM 成本/cache hit 失控。P84 必須建立治理機制，但不能在未核准前直接改程式碼。

## 3. Entry Criteria

開工前必須全部達成：

- [x] P83 已收官並推上遠端：`3c80129 feat: 完成 P83 data quality security`。
- [x] P77-P83 狀態在總戰役計畫中皆為 CLOSED。
- [x] P84 目前只處於 DRAFT/FROZEN 計畫階段，不允許直接改 production code。
- [x] 本計畫完成 17 層、X1-X4、M1/M1.5/M2。
- [x] 主公核准 P84 從 FROZEN 轉 APPROVED（2026-05-17）。

## 4. Exit Criteria

達成全部才算 P84 收官：

- [x] retention policy 明文化，涵蓋 `data/reports/`、`data/runs/`、`data/debug_bundles/`、`data/quarantine/`、LLM cache；若有清理腳本，預設必須 dry-run。（P84.1）
- [x] SLO/escalation 明文化並可由 doctor 或獨立腳本檢查：連續 N 天無 production report、manifest 缺失、doctor blocking/degraded 達門檻時輸出明確 issue。（P84.2）
- [x] handoff truth check 可機械驗證：active bootstrap marker、Current Phase/Step/Mode、archive 禁用提示、Allowed/Forbidden/Exit/Resume 六欄位一致。（P84.3）
- [ ] risk registry / runbook 更新 SOP 明文化，新增 issue code 時能找到對應 runbook anchor。
- [ ] LLM cost / cache hit / run metrics 監控規則明文化，至少能從 manifest 或現有 cache stats 讀到趨勢輸入。
- [ ] P84 新增/更新測試覆蓋 retention dry-run、SLO 判定、handoff truth、runbook issue-code mapping。
- [ ] `py -m pytest -q` 通過，Python 3.8 import guard 不回歸。
- [ ] handoff / active / TASK_HISTORY / 總戰役計畫同步 P84 CLOSED，並給出 P77-P84 總收官狀態。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 4-7 h |
| 預估收益等級 | 高 |
| 收益描述 | 降低長期資料堆積、沉默失敗、交接偏航、runbook 漂移與成本失控風險 |
| ROI 結論 | 值得做；P77-P83 讓系統可靠，P84 讓可靠性不隨時間腐化 |

## 6. 動工範疇（凍結）

1. Retention policy：制定各資料目錄保留策略、dry-run 清理規則、不可刪資料邊界。
2. SLO / escalation：定義 production freshness、consecutive failure、doctor severity 聚合與升級條件。
3. Handoff truth check：驗證 `NEXT_SESSION_HANDOFF.md` active bootstrap 與 phase 狀態一致，不被 archive 汙染。
4. Runbook / risk registry governance：issue code、risk state、runbook anchor 的一致性檢查。
5. Cost / cache hit governance：從 manifest / cache stats 取得成本與命中率訊號，先 advisory。
6. P77-P84 closeout：總戰役收官狀態、後續維護 SOP、接手者最小讀取規則。

## 7. 非範疇（避免偏航）

- 不更換 LLM provider。
- 不新增爬蟲平台。
- 不重寫 P80 promotion gate。
- 不刪除任何歷史資料，除非主公另行明確核准；P84 預設只做 dry-run / policy / advisory。
- 不把 P84 擴成 P85+ 大戰役；若發現新重大治理需求，先列 backlog，不直接開工。

## 8. 17 層稽核表

> 影響半徑：重大 Phase（預估 10+ 檔）。依規則列全 17 層。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | 小型治理腳本與既有 doctor/runbook helper 優先，不建立大型框架 | 治理邏輯分散或過度抽象 | 每項治理先做最小 checker，測試鎖行為 |
| 2 | 邏輯層 (Logic) | retention/SLO/handoff truth 都用明確規則與閾值 | 規則太嚴造成誤報，太鬆造成沉默失敗 | 先 advisory，門檻寫入 plan/runbook |
| 3 | 架構層 (Architecture) | 治理層只觀測與建議，不改 P80/P83 核心路徑 | 把 governance 混進 runtime 導致主鏈路複雜 | checker/script 與 runtime 分離 |
| 4 | 測試層 (Testing) | retention dry-run、SLO、handoff truth、issue-code mapping 都要測 | 只靠文件導致治理退化 | 加聚焦測試與全套 pytest |
| 5 | 資料層 (Data) | 明列 reports/runs/debug/quarantine/cache retention | 誤刪可追溯資料或資料無限堆積 | 預設 dry-run，不做實刪；刪除需主公另核 |
| 6 | 可觀察性層 (Observability) | doctor/SLO/manifest/cache stats 給治理訊號 | 壞了仍需人工翻多檔 | issue code、summary table、runbook anchor |
| 7 | 韌性層 (Resilience) | 連續無 production report 要升級，不沉默 | 外部 API 壞多天仍無人處理 | SLO escalation 明確化 |
| 8 | 效能層 (Performance) | checker 只掃必要檔名/manifest，不讀大歷史全文 | 掃描 reports/debug bundle 太慢 | 限制目錄與天數，避免全量 heavy parse |
| 9 | UX/A11y 層 | N/A：不改前端 UI；只改 CLI/文件輸出 | CLI 輸出難懂會讓主公誤判 | 輸出用表格與 issue code |
| 10 | 安全層 (Security) | retention/dry-run 避免誤刪，debug/secret 不外洩 | 清理腳本或 log 暴露 raw/secret | 不輸出 raw content，刪除動作另需核准 |
| 11 | 部署層 (DevOps) | 若接 CI，先 advisory，不 blocking daily | 太早 blocking 造成 daily 停擺 | P84 先本地/CI advisory，升 blocking 另議 |
| 12 | 成本層 (Cost) | LLM/cache hit 監控，避免長期成本失控 | 成本資料不足或誤判 | 先從 manifest/cache stats 建 baseline |
| 13 | 可維護性層 (Maintainability) | runbook/risk/handoff 規則集中 | 半年後沒人知道怎麼治理 | SOP + tests + minimal reads |
| 14 | 文件層 (Documentation) | P84 plan、runbook、handoff、TASK_HISTORY 同步 | 文件漂移變成新 bug | handoff truth checker 與收官紀錄 |
| 15 | 流程層 (Process) | DRAFT -> FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED | 未核准先做治理實作 | FROZEN 前只改文件狀態 |
| 16 | 隱私/合規層 (Privacy) | raw 原文與 debug bundle retention 要保守 | 長期保存玩家原文或 raw dump | retention policy 標明 raw 類資料處置 |
| 17 | i18n/在地化層 | Asia/Taipei 與繁中 runbook 保持一致 | SLO 日期跨 UTC/台北誤判 | 使用 P82 run context 與明確時區 |

## 9. 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 Performance 層 -> 已規劃 Observability 層。

## 10. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 P84 計畫文件 | 可逆 | 不需不可逆確認 |
| 後續新增 checker / tests | 可逆 | P84 APPROVED 後才可做 |
| 後續新增 dry-run retention script | 可逆 | 不做實刪；實刪需另行確認 |
| 後續 CI advisory 接入 | 可逆 | 先 advisory，blocking 另議 |
| 後續 push | 半可逆 | push 前依規則問主公 |

### X2 盲區掃描

- log 副作用：SLO checker 可能讓原本「看起來還好」的 run 顯示 degraded。
- 中間檔產出：retention dry-run 可能產生報告檔，需避免寫進 data/reports。
- 系統狀態變更：P84 若接 CI advisory，GitHub Actions 會多一段診斷輸出。
- 主公看不到的風險：handoff truth checker 若規則太死，可能阻擋合理文件改版。

### X3 時間敏感性

- 本計畫凍結日期：2026-05-17
- 本計畫過期日期：2026-05-24，超過需重看 P83 manifest/doctor/runbook 是否已變。
- 風險記錄帶日期：已在本文件與 TASK_HISTORY 補錄。

### X4 多角度同行審查

- 主公視角：主公需要知道 P84 不是再修某個 bug，而是建立半年後少壞、壞了好定位、資料不爆倉的治理層。
- 世界頂尖駭客 / 紅隊攻擊者視角：最危險是 retention 或 debug 工具誤刪、誤公開 raw content、CI token 被濫用；最小緩解是 dry-run 預設、白名單輸出、不可逆動作另核。
- 接手者視角：接手者要能從 handoff、runbook、doctor/SLO issue code 知道該查哪個檔，不必讀整份 TASK_HISTORY。
- X4-J 自動化建議性工具邊界：SLO/retention/risk check 都是規則式建議，不等於真實業務健康；CLI 應輸出「advisory」語義與人工覆核點。
- X4-K 使用者端審查官 / Patric 型人格：最容易誤解的是 retention dry-run 看起來像會刪檔；輸出必須明確標示 dry-run，不可讓主公以為資料已被刪。

## 11. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | retention 規則誤刪可追溯資料 | 中 | 高 | 安全/資料 | 預設只 dry-run；實刪另需主公確認 |
| R2 | SLO 門檻太嚴造成警報疲勞 | 中 | 中 | 業務 | 先 advisory，門檻寫清楚，可調 |
| R3 | SLO 門檻太鬆，連續失敗仍沉默 | 中 | 高 | 代碼可控 | 連續無 production report 必須升級 |
| R4 | handoff truth checker 過度僵硬，阻礙正常文件演進 | 中 | 中 | 流程 | 只驗 active bootstrap 必備欄位，不管 archive |
| R5 | 成本/cache hit 監控被誤解為精準帳單 | 中 | 中 | 業務 | 標為 pipeline 指標，不等於供應商帳單 |
| R6 | P84 範圍膨脹成大重構 | 中 | 高 | 流程 | 每個 checker 小步交付，新增需求列 backlog |

**高風險加權檢查（META4）**：
- 高風險數量：3 項。
- 加權分數：R1 2 + R2 1 + R3 2 + R4 1 + R5 1 + R6 2 = 9。
- 是否 >= 5 須請示主公：是；本文件先 FROZEN，等主公核准後才可動工。

## 12. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| P84.0 | 凍結本計畫，等待主公核准 | R6 | `docs/PHASE_84_PLAN.md` 完成 17 層/M1/M2，狀態 FROZEN |
| P84.1 | Retention policy / dry-run inventory | R1 | DONE：policy 明列各資料目錄；dry-run 不刪資料 |
| P84.2 | SLO / escalation checker | R2/R3 | DONE：可檢查連續無 production report、manifest/doctor 異常 |
| P84.3 | Handoff truth checker | R4 | DONE：active bootstrap 必備欄位與 archive 邊界可驗 |
| P84.4 | Risk registry / runbook issue-code governance | R4/R6 | issue code 對應 runbook anchor，risk state SOP 明確 |
| P84.5 | Cost / cache hit governance | R5 | manifest/cache stats 可輸出 advisory 指標 |
| P84.6 | P77-P84 總收官驗證 | 全部 | pytest / diff check / TASK_HISTORY / handoff / total program 全同步 |

## 13. 影響檔案清單

**新增**：
- `docs/PHASE_84_PLAN.md`
- `docs/DATA_RETENTION_POLICY.md`（P84.1）
- `scripts/retention_policy.py`（P84.1）
- `tests/test_retention_policy.py`（P84.1）
- `docs/SLO_POLICY.md`（P84.2）
- `scripts/slo_checker.py`（P84.2）
- `tests/test_slo_checker.py`（P84.2）
- `docs/HANDOFF_TRUTH_POLICY.md`（P84.3）
- `scripts/check_handoff_truth.py`（P84.3）
- `tests/test_handoff_truth.py`（P84.3）
- 後續可能新增：`scripts/governance_doctor.py` 或同等小型 checker。
- 後續可能新增：`tests/test_governance_*.py`。

**修改（主公核准後才可動）**：
- `scripts/system_doctor.py`：可能接入 SLO/governance advisory issue。
- `docs/OPERATIONS_RUNBOOK.md`：新增治理 issue code。
- `docs/RISK_REGISTRY.md`：更新 P77-P84 收官風險狀態。
- `.github/workflows/daily_report.yml`：若接 CI advisory，僅新增非 blocking 檢查。
- `NEXT_SESSION_HANDOFF.md`, `docs/ACTIVE_OPERATION.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`：狀態同步。

**刪除**：
- 無預期刪除；P84 預設不刪歷史資料。

**影響但未直接修改**：
- P79 doctor / runbook。
- P78/P82 manifest。
- P80 promotion gate。
- P81 debug bundle / quarantine。

## 14. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] retention dry-run 估算會影響主公認為不可刪的資料。
- [ ] SLO checker 造成大量 false positive。
- [ ] handoff truth checker 誤判正常 handoff。
- [ ] 有任何「我以為只是 advisory，結果阻斷 daily」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-84-long-term-governance.md`

## 15. Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是 retention / debug / CI 治理腳本誤刪資料、暴露 raw content、濫用 token；最小緩解是 dry-run 預設、白名單輸出、不可逆動作另核。 |
| **X4-B 接手者** | 接手者半年後需要從 handoff、runbook、doctor/SLO issue code 直接知道查哪裡，而不是讀整份 TASK_HISTORY。 |
| **X4-C 災難情境** | 情境：連續 7 天沒有 production report，但 landing 仍指向舊報告；緩解：SLO checker 將 stale production 升級為 degraded/blocking advisory。 |
| **X4-D 5 年後** | 五年後資料目錄會變大、供應商會換、規則會老化；P84 必須留下 retention/SLO/handoff truth 的可調規則與文件位置。 |
| **X4-E 終端 vs IDE** | 治理驗證必須能在 PowerShell/CI 跑，不依賴 IDE 或人工視覺比對；輸出要能被新視窗複述。 |
| **X4-F 跨平台 Win/Mac/Linux** | 路徑掃描與日期判定應使用 Python 標準庫與 P82 run context，避免 shell-specific glob 或 UTC/台北誤判。 |
| **X4-G 主公個人視角** | 主公要的是少壞、壞了好定位；P84 的輸出要講清楚「要不要處理、處理哪裡、會不會刪資料」。 |
| **X4-H 觀測 / 治理** | 若 retention/SLO/handoff truth 只寫文件，不做 checker，長期會退化；至少要有 advisory checker 與測試。 |
| **X4-I 主公可見性** | retention dry-run、SLO 門檻、cost/cache 指標都是主公平常看不到的自動行為，收官時要列表攤開。 |
| **X4-J 自動化建議性工具邊界** | P84 checker 多為規則式啟發，不代表完整真相；CLI/文件必須標明 advisory 與人工覆核點。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 最容易卡住的是把 dry-run 誤看成已刪檔、把 advisory 誤看成 blocking；輸出文案必須明確分層。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| Jarvis 型總控 | 固定必看 | 目標、邊界、下一步 | 已觸發；P84 只做治理，先 FROZEN，不直接改 production code。 |
| Ken 型紅隊 / 技術長 | 固定必看 | 技術假設、安全邊界 | 已觸發；retention 誤刪、debug raw leak、CI 濫用是主要風險。 |
| Patric 型使用者端審查官 | 固定必看 | 是否誤解或死路 | 已觸發；dry-run/advisory/blocking 文案必須避免誤導。 |
| Jimmy 型文件主筆 | 改 docs / handoff | 可追溯與來源 | 已觸發；P84 將同步 handoff、active、TASK_HISTORY、總戰役計畫。 |
| Marcus 型數據分析師 | 涉及數據判斷 | 定量/定性分清 | 已觸發；SLO/cost/cache hit 是 pipeline 指標，不是精準帳單或全網健康真相。 |
| Oliver 型設計審查 | 涉及 UI | 視覺與 A11y | N/A；P84 不改前端 UI，只要求 CLI/文件輸出清楚。 |
| Penny 型 CFO | 涉及成本 | API 成本與停損 | 已觸發；P84 納入 LLM cost / cache hit governance。 |
| Jason 型執行 / DevOps | 涉及 CI/Git | 可執行性與 rollback | 已觸發；CI 先 advisory，dry-run 預設，push 前仍需主公確認。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | retention checker 若未來做實刪，可能刪掉仍需 replay/backfill 的 raw 或 analysis 資料。 | **S** | 0 | P84 預設只做 dry-run/policy；實刪必須另行主公核准。 | 入計畫範圍 |
| 2 | 連續無 production report 如果只寫文件，系統仍會沉默失敗。 | **S** | 0 | P84 必須做 SLO/escalation checker，至少 advisory。 | 入計畫範圍 |
| 3 | handoff truth checker 太僵硬，會因文件格式小改就報錯。 | A | 0 | 只驗 active bootstrap marker 與六硬欄位，不解析 archive 歷史段落。 | 入計畫範圍 |
| 4 | cost/cache hit 指標可能被誤解成供應商帳單，造成錯誤決策。 | A | 0 | 文件與 CLI 標明是 pipeline 指標，不是 billing truth。 | 入計畫範圍 |
| 5 | runbook issue code 若沒有測試，新增 DOC code 時會忘記 anchor。 | A | 0 | P84 納入 issue-code -> runbook anchor checker。 | 入計畫範圍 |
| 6 | P84 太像大雜燴，可能把 P77-P83 全部重構一遍。 | **S** | 0 | 非範疇禁止重寫 provider/promotion/runtime；每個治理能力小步 checker。 | 入計畫範圍 |

## 16. 狀態機

`DRAFT -> FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED`

目前狀態：`APPROVED`。P84.3 已完成；下一步為 P84.4 Risk registry / runbook governance，待主公指示後再動工。不可實刪歷史資料。

## 17. P84.1 實作紀錄

**新增檔案**：
- `docs/DATA_RETENTION_POLICY.md`
- `scripts/retention_policy.py`
- `tests/test_retention_policy.py`

**治理邊界**：
- `scripts/retention_policy.py` 只做 dry-run inventory。
- CLI 明確輸出 `dry_run: true` 與 `will_delete: false`。
- 程式不提供 delete / move / archive 執行參數。
- `raw_*.json` / `analysis_*.json` 只列入 protected inventory，不列自動候選。

**實跑結果（2026-05-17）**：
- `policy_count`: 9
- `candidate_count`: 17
- 17 個候選皆為 `reports_variants`，原因是舊版/preview report 超過 30 天。
- `reports_canonical`: 23 items, 0 candidates。
- `run_manifests`: 1 item, 0 candidates。
- `debug_bundles`: 1 item, 0 candidates。
- `llm_cache`: 1 item, 0 candidates。
- `raw_analysis_snapshots`: 16 items, 0 candidates。

**驗證**：
- `py -m pytest -q tests/test_retention_policy.py` -> 4 passed
- `py scripts\retention_policy.py --repo-root . --today 2026-05-17 --max-candidates 10` -> passed
- `py scripts\retention_policy.py --repo-root . --today 2026-05-17 --json --max-candidates 3` -> passed

## 18. P84.2 實作紀錄

**新增檔案**：
- `docs/SLO_POLICY.md`
- `scripts/slo_checker.py`
- `tests/test_slo_checker.py`

**修改檔案**：
- `scripts/system_doctor.py`
  - `run_doctor(..., check_landing=True)` 新增可選參數，預設維持舊行為。
  - CLI 新增 `--skip-landing`，供 SLO 掃歷史日期時避免 landing false positive。
- `docs/OPERATIONS_RUNBOOK.md`
  - 新增 `SLO000` / `SLO001` / `SLO002` / `SLO003` runbook anchor。

**SLO issue code**：
- `SLO001`: production freshness，尾端連續無 production report 超過門檻。
- `SLO002`: manifest gap，SLO window 內缺 manifest。
- `SLO003`: doctor severity budget，doctor blocking/degraded 天數超過門檻。

**實跑結果（2026-05-18）**：
- `py scripts\slo_checker.py --repo-root . --date 2026-05-18 --window-days 3 --json` -> exit 1（預期，因檢出 blocking SLO）
- 檢出 `SLO001`：`consecutive_no_production=3 threshold=1`
- 檢出 `SLO002`：`missing_manifest_count=2 threshold=0 window=2026-05-16,2026-05-17,2026-05-18`
- 檢出 `SLO003`：`blocking_days=2 degraded_days=2 degraded_threshold=2`

**驗證**：
- `py -m pytest -q tests/test_slo_checker.py tests/test_system_doctor.py` -> 12 passed
- `py scripts\system_doctor.py --repo-root . --date 2026-05-16 --profile local --require-production --skip-landing` -> passed（輸出 DOC005/DOC006/DOC007/DOC010，無 landing false positive）

## 19. P84.3 實作紀錄

**新增檔案**：
- `docs/HANDOFF_TRUTH_POLICY.md`
- `scripts/check_handoff_truth.py`
- `tests/test_handoff_truth.py`

**修改檔案**：
- `docs/OPERATIONS_RUNBOOK.md`
  - 新增 `HND000` / `HND001` / `HND002` / `HND003` / `HND004` / `HND005` / `HND006` / `HND007` runbook anchor。

**handoff issue code**：
- `HND001`: active bootstrap marker layout。
- `HND002`: active bootstrap required fields。
- `HND003`: invalid Mode state。
- `HND004`: Six Anti-Drift Fields missing。
- `HND005`: bootstrap top table vs anti-drift consistency。
- `HND006`: archive boundary。
- `HND007`: `docs/ACTIVE_OPERATION.md` consistency。

**實跑結果（2026-05-18）**：
- `py scripts\check_handoff_truth.py --repo-root .` -> passed，輸出 `HND000`。
- `py scripts\check_handoff_truth.py --repo-root . --json` -> passed，`issues=[]`。

**驗證**：
- `py -m pytest -q tests/test_handoff_truth.py` -> 6 passed
