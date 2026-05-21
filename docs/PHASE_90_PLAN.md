# Phase P90 計畫書 — Budget Ledger / Cooldown（收官版）

> 狀態：CLOSED。P90 runtime 已由主公於 2026-05-21 核准動工並完成；budget ledger / cooldown 已接入 runtime、manifest、doctor、cost governance 與 tests。R-016 仍 Open，不得把 P90 收官解讀為總風險關閉。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P90 |
| **Phase 名稱** | Budget Ledger / Cooldown |
| **凍結日期** | 2026-05-21 |
| **影響半徑** | 標準 (3-9 檔) — runtime 預計新增 budget helper，並接入 provider/client、manifest、governance scripts、tests、docs |
| **預估投入時數** | 4-7 小時 |
| **Token budget** | 45K-75K tokens |
| **負責模型** | GPT-5.3-Codex 高；若同一 budget/cooldown trace 修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P90 plan | DRAFT | FROZEN | 計畫邊界已固定，但 runtime 尚不可施工 | 本檔建立，handoff / active / risk / history 同步，plan lint 通過 | 主公要求繼續，AI 執行 |
| P90 runtime | PENDING_APPROVAL | APPROVED | 主公已核准 runtime 動工 | 主公明確說「核准P90 runtime 動工」 | 主公核准 |
| P90 runtime | APPROVED | CLOSED | budget ledger / cooldown runtime 已完成並通過驗證 | focused tests、full pytest、doctor/governance/lint/handoff truth/diff check 通過 | AI 執行 |
| R-016 | Open | Open | R-016 仍是跨 Phase 風險；P90 只處理 budget / cooldown 子問題 | P90 runtime 收官也不得直接關閉 R-016，需等 P95 closeout | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

建立每日 LLM budget ledger 與 429 cooldown 決策，讓 pipeline 在已超出本日預算或剛撞到 quota 時，停止繼續打 Gemini API，改走 P88/P89 已建立的真實資料 local baseline 與 `production_local_only` 品質分級，避免每日排程反覆雪崩成 429。

## 2. 觸發背景 (Why Now)

P86 已更新 Gemini model / schedule，P87 已建立 report core contract，P88 已能在 LLM 掛掉時產出 deterministic local baseline，P89 已讓 `production_local_only` 可被 promotion gate 接受。剩下的問題是：系統目前仍是「先撞 provider，再 fallback」，如果 Gemini 配額或短期 rate limit 沒恢復，每次 Actions 都可能重複打到 429。P90 要把 429 從 reactive failure 改成 recorded cooldown state，讓下一次 run 可以先看帳本再決定要不要呼叫 LLM。

## 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Repo 內小型 budget state + manifest snapshot | 新增 raw-free budget helper，寫入 `data/llm_budget_state.json`，並在 run manifest 中鏡像本次 budget / cooldown snapshot | 不依賴 provider billing API；可被 tests / doctor / Actions 讀取；符合零額外付費主線 | 只是 pipeline proxy，不是真實 Google 帳單；需定義 retention 與 atomic write | 採用 |
| B. 只靠 `scripts/cost_cache_governance.py` 事後檢查 | 不新增 runtime state，只在 run 後用 manifest 判斷 llm_calls / cache_hit | 改動小，已有 P84.5 基礎 | 事後才知道超量，無法阻止下一次繼續撞 429 | 不採用 |
| C. 查 provider quota / billing API | 以 Google Cloud quota 或 billing 作真實預算來源 | 最接近真實帳單與配額 | 需要額外權限、雲端設定與 provider 差異，會把主線拉回外部依賴 | 不採用 |
| D. 本日第一次 429 後硬關全部 LLM | 只要撞一次 429，當日後續完全不打 LLM | 實作最簡單，能快速止血 | 太粗暴；無法支援少量 budget、冷卻過期、手動重跑證據 | 不採用 |

採用 A，但明確標註 budget ledger 是「pipeline proxy」，不是 provider billing truth。P90 不新增 OpenAI API key，不接免費 provider，不改 P91 cache/dedupe，不做 P92 replay/backfill。

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] 前置 Phase 已收官：P89 Quality Tier / Promotion Gate CLOSED，commit `95f1207` 已推上 `origin/main`。
- [x] 資料/依賴已備：manifest 已有 `provider.quota_error`、`metrics.llm_calls`、`quality.tier`、`quality.analysis_source`、`quality.llm_coverage`。
- [x] 主公已核准計畫凍結：2026-05-21 主公要求「請繼續」。
- [x] 主公已核准 runtime 動工：2026-05-21 主公明確說「核准P90 runtime 動工」。
- [x] 風險登記簿無未解新高風險：R-016 仍 Open，但 P90 是既定修復主線；不新增不可逆操作。

## 4. Exit Criteria（退出條件）

P90 runtime 收官需全部達成：
- [x] 新增 machine-readable budget state，至少記錄 `date`、`max_daily_llm_calls`、`llm_calls_used`、`cooldown_active`、`cooldown_reason`、`cooldown_until_utc`、`quota_error_count`、`last_quota_error_at_utc`。
- [x] Budget state 不含 raw prompt、raw post、provider secret、API response body；只寫計數、狀態、時間與原因碼。
- [x] Runtime 在呼叫 LLM 前檢查 budget / cooldown；超預算或 cooldown active 時，不打 provider，改走 P88 local deterministic baseline。
- [x] 429 / quota 類 provider error 會寫入 cooldown state，下一次 run 可先阻擋 LLM 呼叫。
- [x] Run manifest 寫入 `budget` snapshot，並能讓 doctor / governance 顯示 cooldown 狀態。
- [x] `production_local_only` 在 budget/cooldown skip 情境仍可由 P89 gate 發布，但 metadata 會顯示 `analysis_source=local_deterministic` / `llm_coverage=none` 或等價欄位。
- [x] Tests 覆蓋 under budget、over budget、active cooldown、expired cooldown、429 writes cooldown、malformed state fail-safe、no raw content leakage。
- [x] Focused tests、full `py -m pytest -q`、health、doctor、cost/cache governance 全部通過；2026-05-21 health 仍為既有 production baseline。
- [x] `TASK_HISTORY.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md` 更新；R-016 仍不得關閉。

P90 plan-only 凍結需全部達成：
- [x] 新增本檔 `docs/PHASE_90_PLAN.md`。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_90_PLAN.md` 通過。
- [x] handoff / active / risk / history 更新成 P90 FROZEN。
- [x] `py scripts\check_handoff_truth.py --repo-root .` 通過。
- [x] `py scripts\governance_doctor.py --repo-root .` 通過。
- [x] `git diff --check` 通過。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 4-7 h |
| 預估收益等級 | 高 |
| 收益描述 | 把 429 從「每次 run 都先撞牆」改成「一次撞到後進入可觀測 cooldown」，降低 Actions 重跑成本與錯誤噪音 |
| ROI 結論 | 值得做；這是 R-016 零額外付費主線中防止 provider quota 雪崩的關鍵環節 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增小型 budget helper，集中讀寫 state、判斷 cooldown、產生 manifest snapshot | 把 budget 判斷散落在 `main.py` / provider client 後難以定位 | 單一 helper + focused unit tests；integration 只接決策結果 |
| **2. 邏輯層 (Logic)** | 呼叫 LLM 前先看 budget/cooldown；429 後寫入 cooldown；過期後恢復嘗試 | 錯把 cooldown 當永久停用，或過期後仍不打 LLM | state 欄位包含 `cooldown_until_utc`，tests 覆蓋 active / expired |
| **4. 測試層 (Testing)** | 建立 budget matrix tests，覆蓋 under/over/cooldown/expired/malformed/no raw leakage | 429 只在 Actions 才出現，本地測不到 | 用 fake clock / fake provider error 測狀態轉換，不依賴真 API |
| **10. 安全層 (Security)** | ledger 僅寫 count/status/time/reason，不寫 prompt、貼文、API key、provider response body | state 檔被 commit 後洩漏原始資料或 secret | 新增 no-raw-content test，文件明列禁止欄位 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | Budget decision 獨立於 provider client 與 report generator；manifest 只收 snapshot | provider 切換或 P93 免費 provider 會重寫太多邏輯 | helper 對外只暴露 `should_call_llm` / `record_quota_error` / `snapshot` 類似邊界 |
| **5. 資料層 (Data)** | `data/llm_budget_state.json` 作小型 raw-free state，manifest 保存本次 snapshot | append-only 或無 cap 讓 state 膨脹；日期跨台北/UTC 混亂 | state 只保留 rolling 14 天或最近 N 筆；run_date 用 Asia/Taipei，cooldown_until 用 UTC |
| **6. 可觀察性層 (Observability)** | doctor / cost governance / manifest 顯示 budget status、cooldown reason、quota count | 主公只看到 Actions 綠或紅，不知道是否因 cooldown 跳過 LLM | CLI row 與 manifest `budget` snapshot 明確印出 |
| **7. 韌性層 (Resilience)** | Budget/cooldown active 時走 P88 local baseline，不讓整份報告失敗 | fallback 階段又被舊 showcase/error mode 污染 | 依賴 P89 publishable tier，tests 固定 `production_local_only` |
| **13. 可維護性層 (Maintainability)** | budget state schema 版本化，reason code 固定 enum | 後續 P91/P92/P93 接入時 reason 字串亂長 | 集中 reason codes 並在 docs policy 記錄 |
| **14. 文件層 (Documentation)** | 更新 handoff / active / cost policy / runbook，說明 budget proxy 不是真實帳單 | 接手者把 ledger 當 Google billing truth | 文件與 CLI 都標註 pipeline proxy |
| **15. 流程層 (Process)** | FROZEN -> APPROVED -> IN_PROGRESS；runtime 前需主公核准 | plan 凍結後 AI 直接改 provider/client | handoff/active 寫明 P90 FROZEN 與 Forbidden Work |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 每日 pipeline 會讀 budget state | state 讀寫掃整個 `data/runs` 或大 cache 導致慢 | 固定小 state 檔，O(1) 讀寫，不掃 full cache |
| **9. UX/A11y 層** | 報告 metadata / health output 會露出 cooldown | cooldown 文案讓使用者以為報告壞掉 | 用「LLM 深讀暫停，真實資料 baseline 已發布」的白話文案 |
| **11. 部署層 (DevOps)** | GitHub Actions daily run 會讀寫 budget state | concurrent run 同時寫 state 造成覆蓋 | 使用 atomic write；若偵測衝突，fail-safe 走 local baseline 並記錄 advisory |
| **12. 成本層 (Cost)** | LLM 呼叫與 quota 直接相關 | budget 上限太高仍撞 quota，太低則過度 local-only | 初版使用保守 default，並把實際 llm_calls/cooldown 顯示給後續 P91/P92 調整 |
| **16. 隱私/合規層 (Privacy)** | 第三方玩家貼文與 LLM 分析結果存在 pipeline | budget state 不該保存任何可識別內容 | schema 禁止 raw text/url/title/author，只存 aggregated counts/reasons |
| **17. i18n/在地化層** | Actions UTC 與台北日報日期不同 | cooldown 期限與 report date 錯位 | `date` 以 Asia/Taipei daily report 為準，`cooldown_until_utc` 明確 UTC |

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
| 新增 `docs/PHASE_90_PLAN.md` | 可逆 | 主公要求繼續，本階段只凍結計畫 |
| 更新 handoff / active / risk / history | 可逆 | 主公要求繼續，本階段只凍結計畫 |
| P90 runtime 實作 commit | 可逆 | 主公於 2026-05-21 核准 P90 runtime 動工 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：cooldown active 時 LLM 不會被呼叫，需在 log / manifest 說明是刻意停損。
- [x] 中間檔產出：會新增或更新 `data/llm_budget_state.json`，runtime 收官時必須確認內容 raw-free。
- [x] 系統狀態變更：P90 後同一天重跑可能因 budget/cooldown 直接 local-only，而不是每次嘗試 LLM。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-21。
- 本計畫過期日期：2026-06-21；若 Gemini quota 行為、model list、P91 cache policy 或 P92 replay 架構先改，P90 runtime 需重審。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：P90 的價值是少壞與好定位，不是讓主公再買 OpenAI；每天若 API 不夠，系統要說清楚「我先停損」。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面是惡意內容或 provider error 污染 state，或利用 state 讓系統永久停用 LLM；最小緩解是 state 只接受內部 reason enum 與時間欄位，並測 expired cooldown。
- **接手者視角**：接手者要能從 budget helper、manifest `budget` snapshot、doctor output 三處快速知道為何沒有打 LLM。
- **X4-J 自動化建議性工具邊界**：budget ledger 是 pipeline proxy，不是 Google billing truth；false negative 包含 provider 端未回 429 但實際接近配額、Actions 外部手動呼叫未進 ledger。
- **X4-K 使用者端審查官 / Patric 型人格**：最容易誤解的是 cooldown 等於報告失敗；報告與 health output 必須說明 local baseline 仍是基於真實資料。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | Cooldown 寫壞後永久不打 LLM | 中 | 高 | 邏輯 | `cooldown_until_utc` + expired tests + manual state inspection runbook |
| R2 | Budget ledger 被誤認為 provider 真實帳單 | 中 | 中 | 文件/流程 | 文件、CLI、manifest 都標註 pipeline proxy |
| R3 | State 檔寫入 raw prompt / raw post 造成資料洩漏 | 低 | 高 | 安全 | schema 禁 raw 欄位，no raw leakage tests |
| R4 | Concurrent Actions 或手動重跑同時寫 state | 低 | 中 | DevOps | atomic write；衝突時 fail-safe local-only 並 advisory |
| R5 | Budget 上限設錯導致過度 local-only 或仍撞 429 | 中 | 高 | 成本/邏輯 | 初版保守 default，doctor/cost governance 顯示實際數字，後續 P91/P92 調參 |
| R6 | P90 被誤解成 R-016 已解完 | 中 | 高 | 流程 | handoff/risk/history 明確寫 R-016 仍 Open，P91-P95 尚待做 |

**高風險加權檢查（META4）**：
- 高風險數量：4 項（R1/R3/R5/R6 影響高）。
- 加權分數：6.5 分。
- 是否 >= 5 須請示主公：是；主公已於 2026-05-21 核准 runtime，收官後 R-016 仍保持 Open。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P90.0 Plan Freeze** | 建立本檔，更新 handoff / active / risk / history | 防止直接改 budget runtime | lint plan / handoff truth / governance doctor |
| **P90.1 Budget State Contract** | 定義 schema、reason enum、rolling retention、atomic write helper | state 洩漏或膨脹 | schema tests + no raw leakage tests |
| **P90.2 Cooldown Decision** | 呼叫 LLM 前判斷 under budget / over budget / active cooldown / expired cooldown | 重複撞 429 或永久停用 LLM | fake clock tests |
| **P90.3 Provider Error Recording** | 429 / quota 類錯誤寫入 cooldown state | reactive failure 無法傳遞到下一 run | fake provider error tests |
| **P90.4 Pipeline + Manifest Integration** | main/provider 接 budget decision，manifest 寫 budget snapshot | 主公看不到為何 local-only | health/doctor/cost governance tests |
| **P90.5 Closeout Verification** | focused tests、full pytest、health、doctor、governance、history/handoff 更新 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

目前狀態：P90.0-P90.5 已完成；下一步不得直接動 P91 runtime，需先建立/凍結 P91 cache/dedupe/top-N 計畫。

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_90_PLAN.md`：本 Phase 計畫與收官證據。
- `analyzer/llm_budget.py`：raw-free budget/cooldown state helper。
- `tests/test_llm_budget.py`：budget/cooldown matrix tests。

**P90 plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：Current Phase 改 P90 FROZEN。
- `docs/ACTIVE_OPERATION.md`：短版狀態同步。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P90 plan frozen。
- `TASK_HISTORY.md`：追加 P90 plan freeze 物理紀錄。

**P90 runtime 已修改**：
- `analyzer/llm_budget.py`：新增 budget/cooldown state helper。
- `main.py` 或 provider 呼叫入口：在 LLM 呼叫前接入 budget decision。
- `analyzer/gemini_client.py`、`analyzer/sentiment.py`：記錄 429 / quota 類錯誤並觸發 cooldown；budget skip 直接轉 local deterministic baseline。
- `analyzer/run_manifest.py`：新增 manifest `budget` snapshot。
- `scripts/cost_cache_governance.py`：延伸 budget/cooldown 檢查與 JSON output。
- `scripts/system_doctor.py`：顯示 budget/cooldown advisory。
- `docs/COST_CACHE_GOVERNANCE_POLICY.md`、`docs/OPERATIONS_RUNBOOK.md`：補 budget proxy / cooldown runbook。
- `tests/test_llm_budget.py`、既有 manifest / doctor / governance tests：新增矩陣測試。

**刪除**：
- 無。

**影響但未直接修改**：
- `.github/workflows/daily_report.yml`：P90 runtime 後會受 budget/cooldown 行為影響，但本 Phase 不改 schedule。
- P91/P92/P93：依賴 P90 budget state，但不得混入 P90。

---

## 11. Forbidden Work（P90 邊界）

- 不加 `OPENAI_API_KEY`，不要求主公花 OpenAI API 錢。
- 不接 Groq / Cloudflare / GitHub Models 等免費 provider；P93 才能 disabled-by-default 設計。
- 不改 Gemini model list 或 schedule；P86 已 CLOSED。
- 不做 P91 cache/dedupe/top-N 策略。
- 不做 P92 enrichment queue / replay / backfill。
- 不做 P93 provider abstraction 或任何新 provider runtime。
- 不把 budget ledger 說成 provider billing truth。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] Cooldown active 超過預期，造成連續 3 天都沒有 LLM coverage。
- [ ] Budget state 寫入 raw prompt、raw post、URL、作者或任何不該 commit 的內容。
- [ ] Actions concurrency 或手動重跑讓 budget state 遺失 / 覆蓋。
- [ ] 主公或接手者誤以為 budget ledger 是 Google provider billing truth。
- [ ] 有任何「我以為 cooldown 會過期，結果永久停用」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-90-budget-ledger-cooldown.md`。

---

## 13. Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是惡意資料或錯誤訊息污染 budget state，讓系統永久停用 LLM；最小緩解是 reason enum、UTC 過期時間、no raw leakage tests。 |
| **X4-B 接手者** | 接手者需要從 `analyzer/llm_budget.py`、manifest budget snapshot、doctor row 三處定位跳過 LLM 的理由，不該回去猜 provider 行為。 |
| **X4-C 災難情境** | 情境：第一次 429 寫入錯誤 cooldown，之後每日都 local-only；緩解：fake clock 測 active/expired，runbook 說明如何檢查 state。 |
| **X4-D 5 年後** | 五年後 provider 可能換掉，但 budget ledger 仍應只描述 pipeline 呼叫策略，不綁死 Gemini 或 OpenAI 特定欄位。 |
| **X4-E 終端 vs IDE** | 終端輸出必須能直接看出 budget/cooldown 狀態，不能要求接手者打開 HTML 或 IDE 才知道為何沒呼叫 LLM。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows 本機與 Linux Actions 都會讀寫 JSON state；需使用標準 `Path`、UTF-8、atomic replace，避免 shell-specific 寫法。 |
| **X4-G 主公個人視角** | 主公要的是少壞、壞了好定位、不要多花 OpenAI 錢；P90 必須把「省呼叫」與「可發布真實資料」一起交代清楚。 |
| **X4-H 觀測 / 治理** | 若 cooldown 只存在 memory 或 log，下一視窗和下一次 Actions 都無法定位；manifest / doctor / governance 必須能讀到狀態。 |
| **X4-I 主公可見性** | 主公看不到的是 pipeline 可能主動不打 LLM；報告 metadata、health、handoff 要攤開這是 budget/cooldown 停損，不是隱性壞掉。 |
| **X4-J 自動化建議性工具邊界** | Budget/cooldown 是規則式停損工具，不是 provider quota oracle；false negative 包含外部手動呼叫、provider 未回 429、billing dashboard 與 proxy 不一致。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者可能把 local-only 看成報告降級或壞掉；文案要說明仍是最新真實資料，只是 LLM 深讀暫停。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P90 只處理 budget/cooldown，不混 P91/P92/P93 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；state 禁 raw content/secrets，cooldown 需可過期 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；cooldown 文案必須避免被看成報告壞掉 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase 需更新 handoff、active、history、risk |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；ledger 是 pipeline proxy，不能當 provider billing truth |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 條件觸發；若 runtime 改 report metadata，需避免干擾核心報告閱讀 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P90 是零額外付費停損，不導回 OpenAI paid fallback |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；atomic write、Actions concurrency、Windows/Linux JSON path 都要驗證 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | Cooldown 寫錯後可能讓 LLM 永久停用，連配額恢復也不再嘗試。 | **S** | 0 | 必須用 `cooldown_until_utc` 與 fake clock tests 覆蓋 active/expired。 | 入計畫範圍：P90.2 |
| 2 | Budget state 若寫入 raw prompt 或貼文，commit 後會造成資料洩漏。 | **S** | 0 | schema 禁止 raw 欄位，新增 no raw leakage tests。 | 入計畫範圍：P90.1 |
| 3 | Ledger 只是 pipeline proxy，若被當成真實 Google 帳單會誤導主公。 | A | 0 | 文件、CLI、manifest 都標註不是 provider billing truth。 | 入計畫範圍：P90.4 |
| 4 | Concurrent Actions 同時寫 state，可能覆蓋 quota_error_count 或 cooldown_until。 | A | 0 | 使用 atomic write；衝突時 fail-safe local-only 並 advisory。 | 入計畫範圍：P90.1/P90.3 |
| 5 | Budget/cooldown active 後 local-only 仍可發布，可能掩蓋 LLM 長期缺席。 | A | 0 | manifest/health/doctor 顯示 `llm_coverage=none` 與 cooldown reason，R-016 仍 Open。 | 入計畫範圍：P90.4 |
| 6 | P90 若順手做 cache/dedupe 或 replay，會讓 bug 面積過大且難定位。 | B | 0 | Forbidden Work 明列 P91/P92/P93 不得混入。 | 入計畫範圍：P90.0 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增或修改 skill，STR9 不觸發；若後續臨時新增 skill，必須另開 Phase 或修訂計畫並重新凍結。

---

## 15. Plan Freeze 實跑證據（2026-05-21）

| 指令 | 結果 |
|---|---|
| `py scripts\lint_phase_plan.py docs\PHASE_90_PLAN.md` | PASS：通過 Pre-flight 體檢（M1 + M2） |
| `py scripts\check_handoff_truth.py --repo-root .` | PASS：HND000 active bootstrap truth verified |
| `py scripts\governance_doctor.py --repo-root .` | PASS：GOV000 runbook and risk registry governance verified |
| `git diff --check` | PASS；僅 CRLF warning |

### 凍結後下一步

P90 plan 凍結後，主公已於 2026-05-21 核准 runtime 動工；runtime 收官證據見下節。R-016 仍 Open。

---

## 16. Runtime 收官證據（2026-05-21）

### 16.1 實作真相

- 新增 `analyzer/llm_budget.py`：raw-free budget ledger / cooldown helper，包含 schema version、reason enum、rolling retention、atomic JSON write、malformed state fail-safe。
- 更新 `config.py`：新增 `LLM_BUDGET_STATE_FILE`、`LLM_DAILY_BUDGET`、`LLM_BUDGET_COOLDOWN_MINUTES`、`LLM_BUDGET_RETENTION_DAYS`。
- 更新 `.gitignore`：允許追蹤 raw-free `data/llm_budget_state.json`，讓 Actions 的 cooldown state 可跨 run 延續。
- 更新 `analyzer/gemini_client.py`：LLM 呼叫前檢查 budget / cooldown；provider 429 寫入 cooldown；preflight 只檢查停損狀態、不消耗 daily budget；batch 內 budget skip 會整批冒泡給上層 local baseline。
- 更新 `analyzer/sentiment.py`：`LLMBudgetSkip` 轉成 `analysis_source=local_deterministic`，且 `is_showcase=False`，避免 budget 停損被誤標為展演。
- 更新 `main.py`：manifest meta 寫入 `budget` snapshot；local deterministic analysis 直接產生 local summary，不再額外呼叫 LLM；cache metrics 改為本次 run delta；GitHub backup 會同步 budget state。
- 更新 `analyzer/run_manifest.py`：manifest 支援 `budget` snapshot normalize / validate。
- 更新 `scripts/system_doctor.py` 與 `scripts/cost_cache_governance.py`：新增 DOC017 / CCG006 advisory，顯示 budget/cooldown 狀態但不把 local-only 停損視為 blocking。
- 更新 `docs/OPERATIONS_RUNBOOK.md` 與 `docs/COST_CACHE_GOVERNANCE_POLICY.md`：標註 budget ledger 是 pipeline proxy，不是 provider billing truth。

### 16.2 測試證據

| 指令 | 結果 |
|---|---|
| `py -m pytest -q tests\test_llm_budget.py tests\test_sentiment_contract.py tests\test_run_manifest.py tests\test_system_doctor.py tests\test_cost_cache_governance.py` | PASS：64 passed |
| `py -m py_compile analyzer\llm_budget.py analyzer\gemini_client.py analyzer\sentiment.py analyzer\run_manifest.py main.py scripts\system_doctor.py scripts\cost_cache_governance.py` | PASS |
| `py -m pytest -q tests\test_429_retry.py tests\test_showcase_modes.py tests\test_sentiment_contract.py tests\test_openai_fallback.py` | PASS：19 passed |
| `py scripts\cost_cache_governance.py --repo-root . --date 2026-05-20 --window-days 1` | PASS：exit code 0；既有 2026-05-20 manifest 無 budget 欄位，因此沒有 CCG006 |
| `py scripts\governance_doctor.py --repo-root .` | PASS：GOV000 |
| `py scripts\lint_phase_plan.py docs\PHASE_90_PLAN.md` | PASS：通過 Pre-flight 體檢（M1 + M2） |
| `py scripts\check_handoff_truth.py --repo-root .` | PASS：HND000 active bootstrap truth verified |
| `git diff --check` | PASS；僅 CRLF warning |
| `py scripts\check_daily_report_health.py --date 2026-05-21 --expected-mode production` | PASS：exit code 0；metadata quality tier / manifest quality tier 為舊產物相容 WARN |
| `py scripts\system_doctor.py --repo-root . --date 2026-05-21 --profile ci --require-production` | PASS：exit code 0；僅 DOC007 / DOC016 advisory |
| `py -m pytest -q` | PASS：254 passed |

### 16.3 邊界確認

- R-016 仍 Open：P90 只處理 budget ledger / cooldown，不代表 R-016 closeout。
- P91 cache/dedupe/top-N、P92 enrichment replay、P93 provider abstraction 尚未開始；下一步必須先建立/凍結 P91 plan。
- Budget ledger 仍是 pipeline proxy：它只記錄本 pipeline 的 LLM 呼叫決策與 cooldown 狀態，不等於 Google provider 真實 billing / quota dashboard。
