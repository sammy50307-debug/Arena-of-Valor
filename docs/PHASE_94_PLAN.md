# Phase P94 計畫書 — Doctor / SLO Reclassification（凍結版）

> 狀態：FROZEN。主公已於 2026-05-23 核准 P94 plan freeze；本 Phase 只凍結 doctor / SLO / cost governance 重分類計畫，不改 runtime code。P94 runtime 必須另行取得主公明確核准後才能動工。R-016 仍 Open，不得因 P94 plan 凍結而關閉。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P94 |
| **Phase 名稱** | Doctor / SLO Reclassification |
| **草案日期** | 2026-05-23 |
| **凍結日期** | 2026-05-23 |
| **影響半徑** | Plan-only 標準 (5 檔文件)；runtime 預估標準到重大，依實作是否同時動 `slo_checker` / `system_doctor` / `cost_cache_governance` / tests 判定 |
| **預估投入時數** | Plan-only 1-2 小時；runtime 4-7 小時 |
| **Token budget** | Plan-only 20K-35K；runtime 45K-75K |
| **負責模型** | GPT-5.3-Codex 高；若 SLO / doctor 分級同題修 3 次仍不自洽，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P94 plan | NEW | FROZEN | 計畫邊界已固定，但 runtime 尚未核准 | 主公回覆「核准」後，本檔建立並同步 handoff / active / risk / history | 主公核准，AI 執行 |
| P94 runtime | NOT_STARTED | PENDING_APPROVAL | 只能等主公另行核准，不得修改 scripts / tests / runtime docs | 本計畫 lint / governance 檢查通過並 commit 後，由主公決定是否動工 | 主公 |
| SLO classification | P84.2 baseline | P94 proposed reclassification | 既有 SLO001/SLO002/SLO003 保留，新增或調整分類需 runtime 另審 | P94 runtime 需以 2026-05-20 至 2026-05-23 production 證據校正 | AI 實作，主公核准 |
| R-016 | Open | Open | R-016 是跨 Phase 風險；P94 只處理判讀與分類，不能 closeout | P95 才能做 R-016 closeout verification | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

凍結 P94 runtime 計畫：把 P86-P93 之後的 doctor / SLO / cost governance 訊號重新分類，讓系統能清楚區分「真正阻塞 production」、「已恢復 production 但仍有 advisory」、「歷史窗口造成的成本/品質噪音」，並為 P95 R-016 closeout verification 準備可驗證入口。

## 2. 觸發背景 (Why Now)

P93 runtime push 後，主公要求手動 dispatch AoV Daily Monitor。2026-05-23 實跑結果已產生新的雲端證據：

| 證據 | 結果 |
|---|---|
| GitHub Actions run | `26299079187` success，head SHA `eeefa28` |
| Auto-sync commit | `7da4605 docs: 戰略報告自動同步 2026-05-22 16:19:00 [mode:production l1:0 l2:8 hit:62%]` |
| Run manifest | `data/runs/2026-05-23/run_manifest.json` |
| Report | `data/reports/aov_report_2026-05-23.html`，mode `production` |
| P93 provider routing | `router_enabled=false`、`route_status=router_disabled_legacy_default`、Groq / Cloudflare / GitHub Models 全部 `disabled_by_default`、`attempts=[]` |
| Actions permissions | `Contents: write`、`Metadata: read`；沒有 `models: read` |
| Health check | metadata / quality tier / core contract / landing main link / git clean 全 PASS |
| System doctor | 只有 DOC007 / DOC018 / DOC019 advisory，無 DOC020，無 blocking |
| Enrichment artifact | `eligible_count=0`、`skipped_count=7`，全部 `duplicate_url`，replay 不消耗 LLM |

同時，P94 前置探針顯示：

```powershell
py scripts\slo_checker.py --repo-root . --date 2026-05-23 --window-days 5 --json
```

輸出關鍵值：

```text
consecutive_no_production=0
missing_manifest_count=0
doctor_blocking_days=0
doctor_degraded_days=1
issues=[]
```

代表 R-016 最初的「連續無 production / manifest gap / doctor blocking」已明顯收斂；但 cost/cache governance 三日視窗仍會因 2026-05-21 pre-P91 `llm_calls=28` 產生 `CCG005 total_llm_calls=35 threshold=20`。P94 的真正問題不是再接 provider，而是把「歷史窗口污染」與「當前 production 仍健康」分開，避免 P95 closeout 前的判讀混雜。

### 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. 重分類 SLO / doctor / cost governance | 保留現有 issue codes，補充 reason taxonomy、post-remediation window、歷史污染判讀 | 最符合 P85 P94 路線；可支援 P95 closeout | 需要謹慎避免把真風險降級 | 採用 |
| B. 直接關閉 R-016 | 看到 5/23 production success 後直接 close | 速度最快 | 忽略 P95 closeout、忽略 5-day evidence 與 governance residue | 不採用 |
| C. 直接接 provider 或加 smoke | 用 P93 slots 做 live provider 試跑 | 可探索替代模型 | 偏離 P94；新增 secret / privacy / cost 面 | 不採用 |
| D. 不改任何分類，直接進 P95 | P95 人工解讀既有訊號 | 少改 code | P95 會被 CCG005 / DOC advisory 噪音拖住，容易誤關或誤擋 | 不採用 |

採用 A。P94 的思路是「把觀測儀表校準」，不是再碰 provider，也不是提早關 R-016。

## 3. Entry Criteria（入口條件）

P94 plan-only 開工前必須全部達成：
- [x] P93 runtime 已 CLOSED，commit `eeefa28` 已 push。
- [x] 主公已要求手動 dispatch AoV Daily Monitor，run `26299079187` 已 success。
- [x] Actions auto-sync commit `7da4605` 已 fast-forward 到本地。
- [x] 2026-05-23 manifest 顯示 P93 `provider.routing` 預設關閉，沒有 DOC020 / CCG009 provider enabled 訊號。
- [x] 2026-05-23 SLO checker 五日視窗 `issues=[]`，但 R-016 仍 Open。
- [x] 主公於 2026-05-23 回覆「核准」，允許 P94 plan freeze。

P94 runtime 開工前尚需另行達成：
- [ ] 本檔由 FROZEN 轉 APPROVED。
- [ ] 主公明確說「核准 P94 runtime 動工」或等價指令。
- [ ] runtime 前重跑 `slo_checker` / `system_doctor` / `cost_cache_governance`，確認 2026-05-23 之後是否又有新 Actions commit。
- [ ] 若 runtime 要新增 issue code，先確認 `docs/OPERATIONS_RUNBOOK.md` anchor 與 `scripts/governance_doctor.py` 規則。

## 4. Exit Criteria（退出條件）

P94 plan-only 凍結需全部達成：
- [x] `docs/PHASE_94_PLAN.md` 建立完成。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_94_PLAN.md` 通過。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` / `docs/RISK_REGISTRY.md` / `TASK_HISTORY.md` 同步 P94 FROZEN。
- [x] `py scripts\check_handoff_truth.py --repo-root .` 通過。
- [x] `py scripts\governance_doctor.py --repo-root .` 通過。
- [x] `git diff --check` 通過。
- [x] 不修改 runtime code、workflow、provider flags、secrets 或 data reports。

P94 runtime 收官需全部達成：
- [ ] SLO / doctor / cost governance 可以分清「current blocking」、「historical advisory」、「post-remediation residual」。
- [ ] 2026-05-23 類型的 healthy production run 不被 pre-P91 歷史成本尖峰誤判成當前阻塞。
- [ ] 新增或調整的 issue code 均有 runbook anchor、tests 與 governance doctor 覆蓋。
- [ ] Focused tests、full `py -m pytest -q`、py_compile、doctor / SLO / cost governance 實跑通過。
- [ ] R-016 保持 Open，交給 P95 closeout verification。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | Plan-only 1-2 h；runtime 4-7 h |
| 預估收益等級 | 高 |
| 收益描述 | 避免 P95 closeout 被舊 cost spike、duplicate-only replay、advisory 訊號混淆；讓主公看到 production 是否真的恢復 |
| ROI 結論 | 值得做；P94 是 P95 關閉或降級 R-016 前的儀表校準層 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | Plan-only 不改 code；runtime 只允許小步修改 `slo_checker` / `system_doctor` / `cost_cache_governance` 與 tests | 分類邏輯散落多腳本，導致同一日期在不同工具結論不同 | runtime 需抽出共用 reason taxonomy 或至少以 tests 固定同一資料集輸出 |
| **2. 邏輯層 (Logic)** | 區分 blocking / degraded / advisory / historical residual / post-remediation window | 把真 blocking 降成 advisory，或把舊資料污染當成新故障 | 以 2026-05-19 至 2026-05-23 實際 manifests 做 fixture，保留 SLO001/002/003 原始嚴格語意 |
| **4. 測試層 (Testing)** | runtime 必補 focused tests：healthy post-P93、pre-P91 spike、duplicate-only replay、provider disabled、manifest gap | 分類規則只靠人工看表，下一次改 script 就漂移 | tests 覆蓋正常與反例；full pytest 作收官門檻 |
| **10. 安全層 (Security)** | 不新增 secrets、不讀 provider token、不輸出 raw queue content；只讀 manifest raw-free 欄位 | governance 工具若讀 artifact / raw queue，可能把 raw post 打到 log | P94 runtime 只讀 repo-safe manifest / report metadata；raw artifact 只作人工觀察，不進 repo |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 將 P94 限定為觀測分類層，不碰 daily analysis / provider routing | 將分類修正混入 runtime pipeline，擴大回歸面 | Allowed Files 明確排除 `main.py` / provider clients / workflow |
| **5. 資料層 (Data)** | 使用 `data/runs/<date>/run_manifest.json`、report metadata、cache metrics；不讀 raw reports 內容 | 舊 manifest schema 缺欄位導致新分類誤判 | runtime 需兼容舊 schema，缺欄位以 explicit unknown/advisory 表示 |
| **6. 可觀察性層 (Observability)** | 新增或調整輸出需能說明 issue 是 current / historical / residual | 主公只看到 CCG005 或 DOC018，不知道該不該阻擋 P95 | CLI detail 要包含日期窗口與分類理由 |
| **7. 韌性層 (Resilience)** | SLO checker 保留 blocking 對缺 manifest / 無 production 的嚴格判定 | 重分類後系統過度樂觀，漏掉真正連續故障 | 不降低 SLO001/SLO002/SLO003 blocking 門檻；只新增歷史污染標註 |
| **13. 可維護性層 (Maintainability)** | 文件化 classification taxonomy 與 P95 closeout entry criteria | 半年後接手者不知道哪些 advisory 可接受 | 更新 `docs/SLO_POLICY.md`、runbook、P94 plan |
| **14. 文件層 (Documentation)** | handoff / active / risk / history 同步 P94 FROZEN 與雲端證據 | 新視窗仍停在 P93 commit/push 或以為要接 provider | L1 bootstrap 指向 P94 plan；Forbidden Work 明寫不接 provider |
| **15. 流程層 (Process)** | plan freeze 與 runtime approval 分離；push 仍需主公確認 | AI 因 plan 已核准就直接改 scripts | 狀態機寫 P94 runtime `PENDING_APPROVAL`；runtime 另需主公核准 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | SLO / governance 掃多日 window | window 過大導致 local/CI 慢 | runtime 預設仍用小 window；tests 用 tmp fixtures |
| **9. UX/A11y 層** | CLI / docs 顯示分類語意 | 表格文字太像錯誤，讓主公誤以為 production 壞了 | 用 current/historical/residual 詞彙，detail 說明「是否阻擋 P95」 |
| **11. 部署層 (DevOps)** | 可能涉及 future CI gate / strict doctor | 把 advisory 變 blocking 造成 workflow 誤 fail | P94 不接 CI blocking；若後續要接，另開 Phase |
| **12. 成本層 (Cost)** | cost/cache governance 會判讀 LLM call proxy | 把 pipeline proxy 誤當供應商帳單，或忽略 pre-P91 spike | policy 保留「not provider billing truth」；分類只標 proxy window |
| **16. 隱私/合規層 (Privacy)** | manifest / artifact 可能涉及 raw queue | raw artifact 內含 raw_post，不可進 repo 或 CLI 長輸出 | P94 runtime 不讀 raw artifact；只用 manifest enrichment snapshot |
| **17. i18n/在地化層** | Asia/Taipei 日期與 GitHub UTC run timestamp | 5/22 UTC run 對應 5/23 Taipei report，日期誤判 | 所有 CLI 使用 manifest `run_date_taipei` 或既有 run_context 日期 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 Performance 層 -> 已規劃 Observability 層。

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_94_PLAN.md` | 可逆 | 主公 2026-05-23 回覆「核准」 |
| 同步 handoff / active / risk / TASK_HISTORY | 可逆 | 主公核准 P94 plan freeze |
| P94 runtime 修改 scripts / tests | 可逆 | 未執行；需另行核准 |
| 調整 SLO blocking 門檻 | 半可逆 | P94 plan 不允許；若 runtime 提出需主公單獨裁決 |
| 關閉 R-016 | 半可逆但治理風險高 | P94 禁止；P95 才能裁決 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：SLO / cost governance 的 exit code 可能讓人誤以為 daily failure；P94 需把阻擋性與 advisory 語意拆清楚。
- [x] 中間檔產出：P94 plan-only 不產生資料檔；runtime tests 若建立 fixtures，需放 tests tmp，不碰 `data/reports`。
- [x] 系統狀態變更：P94 若調整 issue severity，可能影響 P95 closeout 判斷；需文件與 tests 同步。

### X3 時間敏感性 (Time Decay)

- 本計畫草案日期：2026-05-23。
- 本計畫凍結日期：2026-05-23。
- 本計畫過期日期：2026-06-06；若 2026-05-24 之後 Actions 又出現 blocking / failed production，P94 runtime 前必須重新取最新 evidence。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：P94 必須回答「現在到底是好了、還是只是綠燈假象？」並且把 P95 能不能關 R-016 的判斷資料先排整齊。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面不是外部入侵，而是治理訊號被過度降級導致真故障被掩蓋；最小緩解是保留原 blocking 門檻、增加分類理由而不是刪除 issue。
- **接手者視角**：接手者要能從 P94 plan 看懂為什麼 5/23 SLO OK 但 R-016 還沒關，並知道 P95 才是 closeout 裁決點。
- **X4-J 自動化建議性工具邊界**：SLO / doctor / cost governance 都是建議性分類工具，false-negative 可能來自舊 manifest schema、報告 metadata 缺欄位、GitHub UTC 與台北日期錯位；人工審核仍必要。
- **X4-K 使用者端審查官 / Patric 型人格**：CLI 若只印 `DEGRADED` 會讓主公焦慮，但若只印 `OK` 又會掩蓋歷史成本尖峰；輸出應說明是否阻擋 P95，而不是只有紅黃綠。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | P94 重分類把真正 production failure 降級成 advisory | 中 | 高 | 邏輯/治理 | 不降低 SLO001/SLO002/SLO003 blocking 門檻，只新增 current/historical/residual 標註 |
| R2 | pre-P91 `llm_calls=28` 長期污染 cost governance，讓 P95 被誤擋 | 高 | 中 | 資料/成本 | runtime 加 post-remediation window 或 per-day detail，讓舊 spike 可見但不混成當前阻塞 |
| R3 | duplicate-only enrichment `no_eligible` 被誤解成 replay 失敗 | 中 | 中 | 可觀察性 | DOC019 / CCG008 detail 明列 skipped reason 與 no-op 語意 |
| R4 | provider routing disabled 被誤解為 provider failure | 低 | 中 | 文件/流程 | P94 延續 P93 文案：disabled slot 不是 failure，不觸發 DOC020 |
| R5 | P94 runtime 改太多治理腳本，破壞既有 P84-P93 tests | 中 | 中 | 代碼/測試 | focused tests + full pytest；每個 issue code 保留向後相容 |
| R6 | R-016 被過早關閉，後續 Actions 再失敗時失去追蹤主線 | 中 | 高 | 流程 | P94 forbidden work 明確禁止 close R-016；P95 才能 closeout |

**高風險加權檢查（META4）**：
- 高風險數量：2 項（R1/R6）。
- 加權分數：7 分。
- 是否 >= 5 須請示主公：是；P94 runtime 不得自動開工，需主公明確核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P94.0 Plan Freeze** | 建立本檔，同步 handoff / active / risk / history | 避免 P94 直接改 scripts 或誤接 provider | phase lint / handoff truth / governance doctor / diff check |
| **P94.1 Evidence Baseline** | 固定 2026-05-19 至 2026-05-23 fixture / 實跑判讀 | 分類沒有物理依據 | tests 或 fixture comments 明列 run manifest truth |
| **P94.2 SLO Classification** | 調整 SLO output，標 current / historical / residual，不降低 blocking 門檻 | SLO OK 與歷史問題混淆 | focused SLO tests |
| **P94.3 Doctor / Cost Governance Classification** | DOC018/DOC019/CCG005/CCG007/CCG008 detail 顯示是否阻擋 P95 | cost spike / duplicate-only no-op 誤判 | doctor + cost governance tests |
| **P94.4 Documentation + Runbook** | 更新 SLO policy、cost policy、runbook、handoff | 接手者看不懂分類 | governance doctor |
| **P94.5 Closeout Verification** | focused tests、full pytest、py_compile、doctor/SLO/cost 實跑、history/handoff 更新 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

---

## 10. 影響檔案清單 ─ STR7

**新增**：
- `docs/PHASE_94_PLAN.md`：P94 FROZEN 計畫書。

**Plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：ACTIVE_BOOTSTRAP 同步 P94 FROZEN。
- `docs/ACTIVE_OPERATION.md`：L2 作戰狀態同步 P94 FROZEN。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P94 FROZEN，但 R-016 仍 Open。
- `TASK_HISTORY.md`：追加 P94 plan freeze 無損紀錄。

**P94 runtime 預計允許修改**：
- `scripts/slo_checker.py`
- `scripts/system_doctor.py`
- `scripts/cost_cache_governance.py`
- `docs/SLO_POLICY.md`
- `docs/COST_CACHE_GOVERNANCE_POLICY.md`
- `docs/OPERATIONS_RUNBOOK.md`
- tests：`tests/test_slo_checker.py`、`tests/test_system_doctor.py`、`tests/test_cost_cache_governance.py`、必要時新增 fixture helper。

**P94 runtime 明確不修改**：
- `.github/workflows/daily_report.yml`
- `main.py`
- `analyzer/provider_router.py`
- `analyzer/gemini_client.py`
- `config.py` provider flags / secrets
- `data/reports/` 既有報告

**刪除**：
- 無。

**影響但未直接修改**：
- P95 closeout：P94 的分類結果會成為 P95 是否關閉或降級 R-016 的入口證據。
- R-016：保持 Open。

---

## 11. Forbidden Work（P94 邊界）

- 不接 Groq / Cloudflare / GitHub Models。
- 不新增 provider key、PAT、Cloudflare token、Groq key。
- 不加入 GitHub Actions `models: read`。
- 不修改 daily default LLM route。
- 不調高 `LLM_DAILY_BUDGET` 來掩蓋成本訊號。
- 不把 raw queue / raw post content 寫進 repo 或 CLI 長輸出。
- 不降低 SLO001 / SLO002 / SLO003 blocking 門檻；只能新增分類說明。
- 不把 DOC007 / DOC018 / DOC019 / CCG005 的存在直接等同 production failure。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P94 分類讓真正 failed production 被誤判成 OK。
- [ ] P94 分類讓 healthy production 被誤判成 blocking，造成 P95 無法推進。
- [ ] P94 runtime 不小心修改 daily workflow / provider route。
- [ ] P94 關閉 R-016 或暗示 R-016 已可關閉。
- [ ] CLI 輸出 raw artifact / raw post content。
- [ ] 出現「我以為 5/23 SLO OK 就代表 R-016 已關」的決策錯誤。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-94-slo-reclassification.md`。

---

## Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 最大攻擊面是治理分類被濫用，把真正 production failure 降級成 advisory；最小緩解是保留 SLO blocking 門檻，只增加分類理由與測試覆蓋。 |
| **X4-B 接手者** | 接手者需要知道 P94 不是修 provider，也不是 closeout；它只校準 SLO/doctor/cost 訊號，讓 P95 能判斷 R-016 是否可關。 |
| **X4-C 災難情境** | 情境：未來 Actions 連續兩天無 production，但 P94 新分類仍輸出 OK；緩解：SLO001/SLO002/SLO003 原 blocking 條件不得降低，反例測試必寫。 |
| **X4-D 5 年後** | 5 年後 provider、模型與報告格式都可能變，但 current/historical/residual 的治理分類仍有價值；文件需保留判讀原理而非只寫當日數字。 |
| **X4-E 終端 vs IDE** | 終端執行需要輸出清楚 exit code 與表格；IDE 讀 JSON 時也要能看到 severity、classification、date window，避免只看文字顏色。 |
| **X4-F 跨平台 Win/Mac/Linux** | P94 runtime 不能依賴 PowerShell-only parsing；測試要用 Python fixtures，Windows 本機與 Linux Actions 都能得到同樣分類。 |
| **X4-G 主公個人視角** | 主公真正要知道的是「是否能進 P95 關 R-016」，不是多一堆縮寫；P94 輸出必須說明哪些訊號阻擋，哪些只是觀察。 |
| **X4-H 觀測 / 治理** | 目前 5/23 SLO 已 OK，但 cost governance 三日窗仍受 5/21 pre-P91 spike 影響；P94 必須把歷史污染與當前風險拆開。 |
| **X4-I 主公可見性** | 主公看不到 manifest schema 與日期窗口細節；計畫需把 run id、commit、manifest、provider routing、SLO 五日輸出列為入口證據。 |
| **X4-J 自動化建議性工具邊界** | SLO / doctor / cost governance 是輔助判讀，不是自動裁決；false-negative 可能來自舊 schema、缺 metadata、時區錯位，人工審核仍必要。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 若 CLI 同時出現 OK 與 DEGRADED，使用者會困惑；輸出應用 current/historical/residual 分類說明，不要只丟 issue code。 |

> 主公人工裁決錨點：P94 runtime 至少有 3 個裁決點，每點預估 3-5 分鐘：是否核准 runtime、是否接受新增分類 taxonomy、是否允許 P95 使用 P94 結果作 closeout entry。AI 應在 runtime 收官時列出 SLO / doctor / cost 三張表與是否阻擋 P95 的結論。

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚；結論是否先行 | 觸發；P94 只做觀測分類計畫，不做 runtime、不關 R-016。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；主要風險是 severity 降級濫用與 raw artifact 洩漏，不是 provider token。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；OK 與 advisory 並存時必須說清是否阻擋 P95。 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；P94 計畫需記錄 run id、commit、manifest 與 SLO 證據。 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；5/23 五日 SLO OK 與三日 CCG005 degraded 要分開解讀。 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | N/A；P94 plan-only 不改報告 UI，runtime 也只預計 CLI / docs。 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；CCG005 是 pipeline proxy，不是供應商帳單，P94 需避免成本恐慌與成本麻痺兩端。 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；P94 不接 CI blocking gate，不改 workflow，runtime 若改 CLI 要保留 JSON 輸出。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 重分類最容易被拿來粉飾太平，把真 blocking 改成 advisory。 | **S 級** | 0 | P94 禁止降低 SLO001/SLO002/SLO003 blocking 門檻，只允許新增分類理由。 | 入計畫 |
| 2 | 5/23 SLO OK 不代表明天仍 OK，若 P94 計畫過期還照做會誤判。 | A 級 | 0 | X3 設 2026-06-06 過期；runtime 前必須重跑最新 evidence。 | 入計畫 |
| 3 | CCG005 三日窗含 5/21 pre-P91 spike，若直接忽略可能掩蓋成本問題。 | A 級 | 0 | 不刪 CCG005；新增 historical / post-remediation 分類與 per-day detail。 | 入計畫 |
| 4 | duplicate-only enrichment `no_eligible` 可能被誤解成 replay 沒工作。 | A 級 | 0 | DOC019 / CCG008 detail 明列 skipped reason，P94 runtime 補 no-op 語意。 | 入計畫 |
| 5 | P94 如果讀 raw artifact 來判斷 replay，可能把 raw post content 打進 log。 | **S 級** | 0 | runtime 僅讀 repo-safe manifest enrichment snapshot，不讀 raw artifact。 | 入計畫 |
| 6 | 時區錯位會讓 5/22 UTC run 被算成 5/22 report，而不是 5/23 台北日。 | A 級 | 0 | 使用 manifest `run_date_taipei` / run_context，不用 GitHub created_at 當報告日。 | 入計畫 |
| 7 | P94 plan freeze 後 AI 可能直接改 scripts，違反 plan-first。 | **S 級** | 0 | 狀態機寫 runtime PENDING_APPROVAL，Forbidden Work 禁止未核准改 code。 | 入計畫 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增、不更新 skill。若 runtime 階段臨時涉及 skill，需另開補遺並補 STR9 表。

---

## 13. 凍結戳記

- **凍結人**：主公核准，AI 執行。
- **凍結時間**：2026-05-23 Asia/Taipei。
- **凍結後變更**：禁止；如需修改，新增章節「Phase P94.x 補遺」並引用本檔。
