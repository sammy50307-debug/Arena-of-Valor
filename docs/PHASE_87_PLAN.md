# Phase P87 計畫書 — Report Core Contract（凍結版）

> 狀態：CLOSED。P87 runtime 已完成；本 Phase 只建立 shadow/advisory core contract，不改 promotion gate。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P87 |
| **Phase 名稱** | Report Core Contract |
| **凍結日期** | 2026-05-20 |
| **影響半徑** | 標準 (3-9 檔) — 預計 runtime 實作會碰 manifest / doctor / health / tests / docs |
| **預估投入時數** | 2-4 小時 |
| **Token budget** | 35K-60K tokens |
| **負責模型** | GPT-5.3-Codex 高；若同一 trace 修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P87 plan | DRAFT_PENDING_PLAN | FROZEN | 計畫可讀、邊界固定、尚不可改 runtime code | `docs/PHASE_87_PLAN.md` 通過 lint 並完成 handoff / risk / history 更新 | AI 建立，主公核准後進 APPROVED |
| Report Core Contract runtime | 待 APPROVED | CLOSED | manifest 會產生 `quality.core_contract`，doctor/health 可讀取並報告狀態 | 主公已核准 P87 runtime，focused/full tests 與 doctor/health 驗證通過 | 主公核准，AI 執行 |

---

## 1. 目標 (Objective)

建立一份機械可驗證的 `report_core_contract` 規格，讓每日報告能判斷「真實資料是否足以發布 production」，並把這個判斷寫入 manifest / doctor / health check；P87 只定義與驗證 core contract，不改品質分級名稱，也不把 promotion gate 改成 blocking。

## 2. 觸發背景 (Why Now)

R-016 的白話根因不是只有 Gemini 429，而是「production 成敗太依賴 LLM 完整成功」。P86 已證明更換 Gemini 3 model 與排程後可以跑出 production，但那只是降低踩 quota 的機率；要讓系統少壞，需要先定義不靠 LLM 也能成立的真實報告核心資料契約，後面的 P88 deterministic analyzer、P89 quality tier、P90 budget ledger 才有同一把尺。

## 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Shadow/advisory core contract | P87 先產出與驗證 contract，doctor/health 可報告狀態，但不直接阻擋首頁 promotion | 風險低，不會突然讓 Actions 因新規則失敗；利於先蒐集證據 | 不能在 P87 當下完全阻止低品質報告上首頁 | 採用 |
| B. Immediate blocking gate | P87 直接讓 core contract fail 時阻擋 production / landing | 保護力立即最大 | 可能把尚未校準的規格變成新 outage；與 P89 promotion gate 職責重疊 | 不採用，留到 P89 |

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] 前置 Phase 已收官：P86 CLOSED，遠端 Actions 已產出 `mode=production` report。
- [x] 資料/依賴已備：`analyzer/run_manifest.py` 已有 `quality.source_health` 與 `eligibility` baseline。
- [x] 主公已核准計畫凍結：2026-05-20 主公要求「push 然後開始 P87」。
- [x] 主公另行核准 runtime 動工：2026-05-20 主公回覆「照你的建議走第一個」。
- [x] 風險登記簿無未解新高風險：R-016 仍 Open，但它正是 P87-P95 主線；P87 不新增不可逆操作。

## 4. Exit Criteria（退出條件）

P87 runtime 收官需全部達成：
- [x] Manifest 產生 `quality.core_contract`，至少含 `version`、`status`、`total_posts`、`platform_count`、`source_count`、`has_report`、`has_analysis`、`min_posts`、`min_platforms`、`min_sources`、`reasons`。
- [x] `validate_manifest()` 會拒絕格式錯誤的 core contract，且保留舊 manifest 的合理相容策略。
- [x] `scripts/system_doctor.py` 能報告 core contract pass/warn/fail；fail 在 P87 只作 degraded/advisory，不直接關閉 promotion。
- [x] `scripts/check_daily_report_health.py` 可在有 manifest 時檢查 core contract；沒有 manifest 時維持既有報告健康檢查行為。
- [x] Focused tests 覆蓋正常、缺資料、單平台、缺 report path、缺 analysis path、舊 manifest 相容。
- [x] `py -m pytest -q` 通過；若有 pre-existing failure，需依 B-008 記錄，不可靜默放行。
- [x] `py scripts\system_doctor.py --repo-root . --date 2026-05-20 --profile ci --require-production` 可清楚顯示 core contract 狀態。
- [x] `TASK_HISTORY.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md` 更新；R-016 仍不得關閉。

P87 plan-only 凍結需全部達成：
- [x] 新增本檔 `docs/PHASE_87_PLAN.md`。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_87_PLAN.md` 通過。
- [x] handoff / active / risk / history 更新成 P87 FROZEN。
- [x] `git diff --check` 通過。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 2-4 h |
| 預估收益等級 | 高 |
| 收益描述 | 把「可否 production」從模糊的 LLM 成敗，改成真實資料契約；後續 P88-P95 都可沿用同一判準 |
| ROI 結論 | 值得做；這是 R-016 零額外付費路線的地基 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 小函式建 contract、normalize、validate；沿用 `run_manifest.py` 現有風格 | 為一個 contract 寫過度抽象 | 只新增 P87 需要的 helper，不做 provider / promotion refactor |
| **2. 邏輯層 (Logic)** | 明確分開 source health、core contract、publish eligibility | 把 core contract 與 P89 quality tier 混在一起，造成 Phase 越界 | P87 只輸出 pass/warn/fail 與 reasons；tier 名稱留 P89 |
| **4. 測試層 (Testing)** | 新增/擴充 manifest、doctor、health focused tests，再跑全套 pytest | contract 門檻寫錯卻沒有測到缺資料路徑 | 必測 0 posts、單平台、缺 report、缺 analysis、舊 manifest |
| **10. 安全層 (Security)** | 不新增 secret，不新增外部 provider，不輸出原始貼文內容到 manifest | manifest 可能把 PII 或原文片段寫入 repo | contract 只允許 counts / bool / reason code，不存 raw content |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / 不適用理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 把 core contract 放在 manifest quality 區，doctor/health 只讀契約 | 健康規則散落在多個腳本，未來不一致 | `run_manifest.py` 作契約來源，腳本只解讀 |
| **5. 資料層 (Data)** | schema version / contract version 明列，reasons 使用穩定 code | 舊 manifest 缺 core contract 導致 doctor 誤判 | validate 採相容策略；doctor 對缺欄位明確 advisory |
| **6. 可觀察性層 (Observability)** | doctor issue 顯示 status、counts、reason codes | 壞了只看到 production fail，不知道缺哪個條件 | issue detail 必含 posts/platforms/sources/report/analysis |
| **7. 韌性層 (Resilience)** | LLM 失敗時仍可判斷 core data 是否夠 | 429 仍被誤解為整份報告不可用 | core contract 不依賴 LLM calls；LLM enrichment 留後續 |
| **13. 可維護性層 (Maintainability)** | 欄位名稱固定、測試鎖住、runbook 後續可接 issue code | 半年後不知道門檻在哪裡 | 門檻集中在 helper / constants，文件列出定義 |
| **14. 文件層 (Documentation)** | plan、handoff、history 記錄 P87 邊界與不得越界事項 | 新視窗誤以為 P87 要改 promotion gate | Forbidden Work 明列 P89/P90/P93 不得混入 |
| **15. 流程層 (Process)** | FROZEN -> APPROVED -> IN_PROGRESS；runtime 改動前需主公核准 | plan 凍結後 AI 直接動程式碼 | handoff/active 把 Mode 寫成 FROZEN，Allowed Files 限制清楚 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | Manifest / doctor 每日跑 | 讀報告或 manifest 過度掃描目錄 | 只讀當日 manifest/report；不用全 repo 掃描 |
| **9. UX/A11y 層** | 報告品質對使用者可見 | 使用者看到 production 但其實只是低資料量 | P87 先讓 doctor/health 可見；P89 再改前端 tier 呈現 |
| **11. 部署層 (DevOps)** | GitHub Actions daily health | 新 doctor 規則讓 CI 突然阻塞 | P87 採 shadow/advisory，不把 core fail 變 blocking gate |
| **12. 成本層 (Cost)** | R-016 零額外付費主線 | 因 contract 不足又回頭加 OpenAI paid fallback | P87 不加 API；只用既有資料做本地判斷 |
| **16. 隱私/合規層 (Privacy)** | 第三方論壇資料進 manifest | raw title/content 被持久化到品質欄位 | 只存聚合 counts 與 reason code |
| **17. i18n/在地化層** | 台北日報與 GitHub UTC 排程 | date / timezone 混淆導致讀錯 manifest | 沿用 `run_date_taipei`、`timezone`、`scheduled_utc`，不新增模糊日期 |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已規劃 Testing 層。
- [x] 動 Architecture 層 → 已規劃 Documentation 層。
- [x] 動 Data 層 → 已規劃 Maintainability 層。
- [x] 動 Security 層 → 已規劃 Testing 層。
- [x] 動 Performance 層 → 已規劃 Observability 層。

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_87_PLAN.md` | 可逆 | 已核准開始 P87 plan |
| 更新 handoff / active / risk / history | 可逆 | 已核准開始 P87 plan |
| P87 runtime 實作 commit | 可逆 | 尚未核准，需主公下一步確認 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：doctor 可能新增 advisory / degraded issue，這是可觀察性，不是新 runtime 失敗。
- [x] 中間檔產出：manifest 會多出 core contract 欄位；不應寫入 raw content。
- [x] 系統狀態變更：P87 不改 promotion gate，所以短期不會改首頁發布決策。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-20。
- 本計畫過期日期：2026-06-20；若 P88/P89 已先改完，P87 需重審。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：這份計畫把「現在不是再追 API，而是先定真實報告最低標準」講清楚，避免 P87 被誤解成 provider 優化。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面主要是 manifest 汙染與 CI 訊號偽造；最小緩解是 validate type / enum / bool，且不存 raw content 或 secret。
- **接手者視角**：半年後接手者應能從 `quality.core_contract`、tests、doctor issue detail 追到 production 判斷依據。
- **X4-J 自動化建議性工具邊界**：core contract 是規則判斷，不是內容真偽判定；它能指出資料量不足，不能證明輿情分析品質完整。
- **X4-K 使用者端審查官 / Patric 型人格**：P87 不應讓主公以為 R-016 已解；handoff 必須明寫 R-016 仍 Open，production tier 要等 P89。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | Contract 門檻太低，低品質資料仍被視為 pass | 中 | 高 | 邏輯 | P87 只 shadow/advisory；P89 前用實跑資料校準 |
| R2 | Contract 門檻太高，正常 production 被誤判 warn/fail | 中 | 中 | 邏輯 | focused tests + 5/20 production manifest 當 baseline |
| R3 | 舊 manifest 缺欄位導致 doctor 噴錯 | 中 | 中 | 資料 | 缺 contract 時顯示 advisory，不丟例外 |
| R4 | P87 越界改 quality tier / promotion gate | 中 | 高 | 流程 | Forbidden Work 明列 P89 才改 gate / tier |
| R5 | 寫入 raw post content 到 manifest | 低 | 高 | 安全 / 隱私 | 欄位白名單只存 counts / bool / reason code |

**高風險加權檢查（META4）**：
- 高風險數量：3 項（R1/R4/R5 影響高）。
- 加權分數：4.5 分。
- 是否 ≥ 5 須請示主公：否；但 runtime 動工仍需主公核准，因目前是 FROZEN。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P87.0 Plan Freeze** | 建立本檔，更新 handoff / active / risk / history | 防偏航、避免直接動 runtime | lint plan / handoff truth / governance doctor |
| **P87.1 Contract Builder** | 在 manifest helper 建立 `quality.core_contract` normalization | source health 與 production 判斷缺共同標準 | focused tests 驗證 pass/warn/fail |
| **P87.2 Manifest Validation** | `validate_manifest()` 檢查 core contract shape，舊 manifest 相容 | 壞 manifest 混入 CI | invalid contract tests |
| **P87.3 Doctor / Health Integration** | doctor / health check 顯示 core contract 狀態 | 壞了不易定位 | CLI output 與 issue code 測試 |
| **P87.4 Closeout** | 跑 full pytest、doctor、handoff truth、governance doctor，更新歷史 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

---

## 9.5 收官證據

| 項目 | 結果 |
|---|---|
| Focused tests | `py -m pytest -q tests\test_run_manifest.py tests\test_daily_report_health.py tests\test_system_doctor.py` → 41 passed |
| Full tests | `py -m pytest -q` → 221 passed |
| Health check | `py scripts\check_daily_report_health.py --date 2026-05-20 --expected-mode production` → production PASS，舊 manifest 顯示 `core contract` WARN |
| System doctor | `py scripts\system_doctor.py --repo-root . --date 2026-05-20 --profile ci --require-production` → 無 blocking / degraded，僅 DOC007、DOC015 advisory |
| Governance doctor | `py scripts\governance_doctor.py --repo-root .` → GOV000 PASS |

P87 實作後，未來新 manifest 會帶 `quality.core_contract`；2026-05-20 既有 manifest 是 P87 前產物，因此顯示 `DOC015 quality.core_contract missing` advisory，這是預期相容行為。

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_87_PLAN.md`：本 Phase 凍結計畫。

**P87 plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：Current Phase 改 P87 FROZEN。
- `docs/ACTIVE_OPERATION.md`：短版狀態同步。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P87 plan frozen。
- `TASK_HISTORY.md`：追加 P87 plan freeze 物理紀錄。

**P87 runtime 修改**：
- `analyzer/run_manifest.py`：新增 core contract helper / manifest 欄位 / validation。
- `scripts/check_daily_report_health.py`：讀取 manifest contract 並輸出 health result。
- `scripts/system_doctor.py`：新增 DOC015 顯示 contract 狀態。
- `docs/OPERATIONS_RUNBOOK.md`：新增 DOC015 runbook anchor。
- `tests/test_run_manifest.py`：manifest contract focused tests。
- `tests/test_daily_report_health.py`：health contract focused tests。
- `tests/test_system_doctor.py`：doctor contract tests。

**刪除**：
- 無。

**影響但未直接修改**：
- `reporter/`：P87 不直接改模板；若後續發現 report metadata 必須補欄位，需在 APPROVED 後另明列。
- P88 / P89 / P90：依賴 P87 contract，但不得混入 P87。

---

## 11. Forbidden Work（P87 邊界）

- 不加 `OPENAI_API_KEY`，不要求主公花 OpenAI API 錢。
- 不接 Groq / Cloudflare / GitHub Models 等免費 provider；P93 才能 disabled-by-default 設計。
- 不改 Gemini model list 或 schedule；P86 已 CLOSED。
- 不改 quality tier enum 或 landing promotion gate；P89 才處理。
- 不實作 deterministic analyzer；P88 才處理。
- 不做 LLM budget ledger / cooldown；P90 才處理。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 主公中途否決 core contract 欄位設計並要求重來。
- [ ] focused tests 顯示既有 manifest schema 無法相容。
- [ ] GitHub Actions 因 P87 advisory 規則意外阻塞 daily workflow。
- [ ] 發生「我以為 production 等於 LLM 完整成功，結果不是」的判斷錯誤。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-87-report-core-contract.md`。

---

## 13. Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 主要攻擊面是偽造 manifest 欄位讓低品質報告看似合格，最小緩解是 enum/type validation 與不信任 raw-free counts 以外欄位。 |
| **X4-B 接手者** | 接手者需要一眼知道 production 判斷不是散在 doctor、health、reporter，而是集中由 manifest core contract 提供。 |
| **X4-C 災難情境** | 情境：core contract 門檻放太寬導致 local-only 低品質報告上首頁；緩解：P87 只 shadow/advisory，P89 才 blocking。 |
| **X4-D 5 年後** | 五年後 provider 與 model 都可能換掉，但真實資料足不足仍要可判斷，所以 contract 應避免綁死特定 LLM。 |
| **X4-E 終端 vs IDE** | 終端執行 doctor/health 時必須能看到清楚 reason code，不能只靠 IDE 打開 JSON 才能定位。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows PowerShell 與 Linux Actions 都會跑同一批 Python 腳本，輸出要避免平台限定路徑與編碼假設。 |
| **X4-G 主公個人視角** | 主公真正要的是少壞且壞了好定位；P87 要用白話欄位說明缺資料、缺平台或缺報告，不丟一串抽象錯誤。 |
| **X4-H 觀測 / 治理** | Doctor 需要把 core contract 狀態列成可追蹤 issue，否則 P87 只是在 manifest 多塞欄位，定位速度不會變快。 |
| **X4-I 主公可見性** | 主公看不到的是 P87 不會立即改首頁發布邏輯；handoff 必須明寫這只是 contract 地基，promotion 要等 P89。 |
| **X4-J 自動化建議性工具邊界** | Core contract 是規則式健康檢查，只能指出資料與產物是否足夠，不能替代人工判斷報告內容是否精彩或正確。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 最容易誤解的是看到 production 就以為 LLM 全成功；P87 要把 core data 與 LLM enrichment 分開命名，避免承諾不實。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P87 先 contract，P88/P89/P90 不混入 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；不新增 secrets，manifest 只存 raw-free aggregate |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；需避免主公誤以為 P87 完成就能關 R-016 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase 需更新 handoff、active、history |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；P87 門檻需用 counts，不憑印象判斷品質 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 條件觸發；P87 不改 UI，若動 report metadata 才補 UI 檢查 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P87 不花 API 錢，支援零額外付費主線 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；P87 doctor/health 在 CI 先 advisory，避免新 gate 造成 outage |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 如果 core contract 只看 posts > 0，單一平台灌水也會被當成 production 地基。 | **S** | 0 | contract 必含 platform_count / source_count 與 reasons，不只看 total_posts。 | 入計畫範圍：P87.1 / P87.2 |
| 2 | 如果 P87 直接 blocking，校準不準會讓原本可用的 daily workflow 變成新 outage。 | **S** | 0 | P87 採 shadow/advisory，blocking 留到 P89 quality tier / promotion gate。 | 入計畫範圍：P87 Forbidden Work |
| 3 | 舊 manifest 缺 core_contract 時 doctor 可能報錯，反而降低定位速度。 | A | 0 | 缺欄位要變成 advisory detail，不能丟例外。 | 入計畫範圍：P87.2 / P87.3 |
| 4 | contract 欄位若寫入 raw content，會把第三方內容與個資風險擴大到 repo。 | A | 0 | 欄位白名單只允許 counts、bool、status、reason code。 | 入計畫範圍：安全層與 P87.1 |
| 5 | P87 若順手改 reporter UI 或 promotion gate，會與 P88/P89 邊界衝突。 | A | 0 | 文件明列 forbidden work；handoff 把下一步限定在 core contract。 | 入計畫範圍：流程層 |
| 6 | 只加 manifest 欄位但不接 doctor/health，壞了仍然要人工翻 JSON。 | A | 0 | P87 exit criteria 要求 doctor/health 顯示狀態與 reason。 | 入計畫範圍：P87.3 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增或修改 skill，STR9 不觸發；若後續臨時新增 skill，必須另開 Phase 或修訂計畫並重新凍結。
