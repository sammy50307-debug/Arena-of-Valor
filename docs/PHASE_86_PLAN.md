# Phase P86 計畫書 — Gemini Model & Schedule Modernization（凍結版）

> 草案日期：2026-05-19
> 凍結日期：2026-05-19
> 狀態：FROZEN
> 核准狀態：待主公核准後才可進入 APPROVED / IN_PROGRESS

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P86 |
| Phase 名稱 | Gemini Model & Schedule Modernization |
| 凍結日期 | 2026-05-19 |
| 影響半徑 | 標準（預估 5-8 檔：Gemini client、workflow、tests、handoff/docs/history） |
| 預估投入時數 | 2-4 h |
| Token budget | 25K-45K tokens |
| 負責模型 | GPT-5.3-Codex 高；若同一錯誤修 3 次仍失敗，提醒切 GPT-5.5 高/超高 |

## 0.1 官方查證快照（2026-05-19）

> P86 開工前已按 P85 要求重新查官方文件。本表是 P86 凍結依據；若實際動工日期超過 2026-06-02，需再次查證。

| 主題 | 官方來源 | P86 判斷 |
|---|---|---|
| Rate limit 維度 | Google Gemini rate limits：RPM、TPM、RPD 三維；超任一限制會觸發 rate limit error | P86 不把 429 當單純 retry 問題；需避開舊 RPD window |
| Rate limit 範圍 | Google Gemini rate limits：limits applied per project, not per API key；RPD reset at midnight Pacific time | 多 API key 輪替不是主線；schedule 可改到 Pacific midnight 後 |
| Active limits | Google Gemini rate limits：實際 limits 需在 AI Studio 查看，specified limits not guaranteed | P86 不硬編每日可用額度；P90 才做 budget ledger |
| 2.0 deprecation | Google Gemini deprecations：`gemini-2.0-flash` / `gemini-2.0-flash-lite` shutdown date 2026-06-01 | P86 必須移除 2.0 model names |
| 2.0 replacement | Google Gemini deprecations：2.0 Flash -> `gemini-2.5-flash`，2.0 Flash-Lite -> `gemini-2.5-flash-lite` | P86 採官方 replacement 作為保守落地 |
| 3.1 Flash-Lite | Google Gemini models：`gemini-3.1-flash-lite` 為 Gemini 3 stable；deprecations 顯示 shutdown 2027-05-07 | P86 先列候選，不直接設為 primary，避免新 endpoint/schema 風險混入本 Phase |
| Free tier | Gemini pricing：多個文字模型仍有 free tier，但 free tier data may be used to improve products | P86 不新增付費；不處理 privacy policy 改版，P92/P93 再審 |

官方來源：

- `https://ai.google.dev/gemini-api/docs/rate-limits`
- `https://ai.google.dev/gemini-api/docs/deprecations`
- `https://ai.google.dev/gemini-api/docs/models`
- `https://ai.google.dev/gemini-api/docs/pricing`

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P86 計畫 | DRAFT_PENDING_APPROVAL | FROZEN | P86 詳細計畫已通過稽核，但尚不可改 runtime code | 主公明確要求「凍結P86」，且官方查證完成 | AI 建立，主公核准後才動工 |
| `GEMINI_MODELS` | 待更新 | 待 APPROVED 後更新 | 現行仍含 2.0 deprecated models；P86 核准後才改 | P86 從 FROZEN 轉 APPROVED | 主公核准，AI 執行 |
| GitHub Actions cron | 待評估 | 待 APPROVED 後更新 | 現行 UTC 00:00 / 台北 08:00；P86 核准後才可改 | P86 從 FROZEN 轉 APPROVED | 主公核准，AI 執行 |

## 1. 目標

在不新增付費 provider、不接免費 provider 插槽的前提下，移除即將 shutdown 的 Gemini 2.0 model 依賴，並把每日排程調整到更接近 Gemini RPD 重置後的安全窗口，降低因過期模型與舊配額窗口造成的 `showcase_forced` 機率。

## 2. 觸發背景

P85 已凍結 R-016 的 zero-cost evidence-first 主線。P86 是第一個可動工的細項 Phase，原因有兩個：

1. `analyzer/gemini_client.py` 目前 `GEMINI_MODELS` 仍包含 `gemini-2.0-flash` 與 `gemini-2.0-flash-lite`。
2. 官方 deprecations 顯示 Gemini 2.0 Flash / Flash-Lite 最早 shutdown date 為 2026-06-01，距離今天 2026-05-19 只剩不到兩週。
3. `.github/workflows/daily_report.yml` 目前 UTC 00:00（台北 08:00）執行；官方 rate limit 文件寫 RPD reset at midnight Pacific time，因此台北早上 8 點可能仍落在舊 RPD window。

本 Phase 不是 P87-P95 的 production 定義重構；P86 只處理 model list 與 schedule。

## 3. Entry Criteria

開工前必須全部達成：

- [x] P85 已凍結，且主線明確排除 OpenAI paid fallback。
- [x] 主公已明確要求凍結 P86。
- [x] Gemini rate limit / models / deprecations / pricing 官方資料已於 2026-05-19 重新查證。
- [x] 本計畫完成 17 層稽核、M1、M1.5、M2。
- [ ] 主公後續明確核准 P86 從 FROZEN 轉 APPROVED。
- [ ] P85 / P86 本地 commits push 與否由主公另行決定；push 不是 P86 動工前置條件，但推前必問。

## 4. Exit Criteria

P86 實作收官需全部達成：

- [ ] `analyzer/gemini_client.py` 的 `GEMINI_MODELS` 不含 `gemini-2.0-flash`、`gemini-2.0-flash-lite` 或其他官方已 shutdown/deprecated model。
- [ ] 預設 model order 採官方 replacement：`gemini-2.5-flash-lite` -> `gemini-2.5-flash`。
- [ ] `gemini-3.1-flash-lite` 只列為後續候選或明確 comment，不在未實測前直接設為 primary。
- [ ] `.github/workflows/daily_report.yml` cron 從 UTC 00:00 改為 UTC 08:30（台北 16:30），並更新註解說明：避開 Pacific midnight RPD reset 前的舊配額窗口。
- [ ] workflow 保留 `workflow_dispatch`，方便主公手動跑早報或驗證。
- [ ] 測試覆蓋：
  - model policy：禁止 deprecated model names。
  - 429 retry：仍依 `GEMINI_MODELS` 全部輪替後再 wait 60/300/900。
  - workflow schedule：cron 與註解符合 P86 policy。
- [ ] `py -m pytest -q tests/test_429_retry.py <新增測試>` 通過。
- [ ] `py -3.8 -c "import analyzer.gemini_client; print(analyzer.gemini_client.GEMINI_MODELS)"` 通過。
- [ ] `git diff --check` 通過。
- [ ] P86 收官時更新 handoff / active / risk / TASK_HISTORY。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 2-4 h |
| 預估收益等級 | 高 |
| 收益描述 | 避免 2026-06-01 後因 Gemini 2.0 endpoint shutdown 造成新故障，並降低每天早上撞舊 RPD window 的機率 |
| ROI 結論 | 值得做；P86 是 P85 戰役中最低風險、最高時效性的止血 Phase |

## 6. 方案比較

| 方案 | 做法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. 只刪 2.0，保留 2.5 Flash | 最小改動，`gemini-2.5-flash` 單 model | 最安全 | 沒有 lite fallback，可能較耗 quota | 不採 |
| B. 2.5 Flash-Lite -> 2.5 Flash | 官方 replacement，保守且低成本 | blast radius 小，貼合現行 REST/JSON schema | 2.5 系列 2026-10-16 也有 shutdown date | 採用 |
| C. 3.1 Flash-Lite -> 2.5 Flash-Lite -> 2.5 Flash | 更長 deprecation horizon | 可能更前沿 | 新 endpoint/schema/rate-limit 未在本 repo 實測 | 暫列候選，P86 不直接 primary |
| D. 不改 cron，等 P90 budget ledger | 保持早上報告習慣 | 不影響主公作息 | 仍可能每天撞舊 RPD window | 不採 |
| E. cron 改 UTC 08:30 | 台北 16:30，安全落在 Pacific midnight 後 | 降低舊 RPD window 風險 | 早上不自動出報告 | 採用；早報/雙段發布留 P90/P92 |

## 7. 17 層稽核表

> P86 是標準 Phase（3-9 檔）且觸發 DevOps / Cost / i18n，因此列全 17 層。

| # | 層級 | 採用優化項 / 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | 只改 model list 與 workflow cron，不重構 Gemini client | 小改誤動 retry / cache 行為 | focused tests 鎖 429 retry 與 import |
| 2 | 邏輯層 (Logic) | model order 改為官方 replacement；schedule 依 RPD reset | 把 preview/new model 當 stable 使用 | P86 不直接 primary 3.1，先保守 2.5 |
| 3 | 架構層 (Architecture) | 不引入 provider abstraction，保持 Gemini-only | 提早引入 P93 provider 插槽造成範圍外擴張 | Forbidden Work 明列不接 provider |
| 4 | 測試層 (Testing) | 新增 model policy / workflow schedule tests | 只跑現有 tests 會漏 model name 回歸 | 測試明確 grep deprecated names |
| 5 | 資料層 (Data) | N/A：不改 manifest/data schema | schedule 改後報告日期跨日誤判 | 保留 P82 Asia/Taipei run context，workflow health 用 TZ=Asia/Taipei |
| 6 | 可觀察性層 (Observability) | workflow 註解與 tests 顯示新 cron 意圖 | 主公只看 Actions 時不知為何下午跑 | 註解明寫 Pacific reset / Taipei 16:30 |
| 7 | 韌性層 (Resilience) | 移除 2.0 shutdown endpoint；避開舊 quota window | 2.5 仍可能 429 | P86 只降低風險，P90 才做 budget/cooldown |
| 8 | 效能層 (Performance) | Flash-Lite 優先，降低 token/cost 壓力 | Lite 品質可能比 Flash 弱 | Flash 作 second fallback；品質分級留 P89 |
| 9 | UX/A11y 層 | 不改報告 UI | 下午自動報告可能影響主公早上習慣 | 保留 workflow_dispatch；雙段發布留 P90/P92 |
| 10 | 安全層 (Security) | 不新增 secrets，不印 API key | schedule 或 model log 洩漏 key | `_masked_url` 不動；workflow secret preflight 只印 configured/missing |
| 11 | 部署層 (DevOps) | cron 從 UTC 00:00 改 UTC 08:30 | GitHub cron 延遲或錯過排程 | workflow_dispatch 保留；收官要求 Actions 實跑 |
| 12 | 成本層 (Cost) | 不新增付費 provider；Lite first | 2.5 Flash 仍消耗免費額度 | P90 budget ledger 承接；P86 不擴呼叫量 |
| 13 | 可維護性層 (Maintainability) | 用測試防 deprecated model 回流 | 未來 2.5 shutdown 又忘記更新 | P86 文件記錄 2026-10-16 review trigger |
| 14 | 文件層 (Documentation) | handoff / active / history / risk 同步 | 新視窗不知 P86 已凍結 | ACTIVE_BOOTSTRAP 改成 P86 FROZEN |
| 15 | 流程層 (Process) | FROZEN 不動 code；APPROVED 才實作 | 凍結時偷改 runtime | 本次只建計畫與文件，runtime 留下一步 |
| 16 | 隱私/合規層 (Privacy) | 不新增資料傳送方 | Gemini free tier data policy 仍存在 | P86 不改 provider；privacy 深審留 P92/P93 |
| 17 | i18n/在地化層 | cron 註解同時標 UTC / Asia/Taipei / Pacific reset | DST 導致 Pacific midnight UTC 07/08 差異 | 用 UTC 08:30，落在 PDT/PST midnight 之後 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 Performance 層 -> 已規劃 Observability 層。

## 8. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 P86 計畫文件 | 可逆 | 主公已要求凍結 P86 |
| 後續修改 `GEMINI_MODELS` | 可逆 | P86 APPROVED 後才可做 |
| 後續修改 cron | 可逆 | P86 APPROVED 後才可做；可用 commit revert |
| 後續 push | 半可逆 | push 前必問主公 |

### X2 盲區掃描

- log 副作用：model order 改後 log 中第一個 preflight model 會變成 Flash-Lite。
- 中間檔產出：P86 不新增資料檔。
- 系統狀態變更：cron 改到 UTC 08:30 後，自動報告會變台北下午產出。
- 主公看不到的風險：GitHub scheduled workflow 可能本身延遲，不能精準保證 16:30 立刻跑。

### X3 時間敏感性

- 本計畫凍結日期：2026-05-19。
- 本計畫過期日期：2026-06-02；超過需重查 Gemini deprecations / rate limits。
- 下次必看日期：2026-10-01 前需重新檢查 Gemini 2.5 deprecation，避免 2026-10-16 shutdown 前又壓線。

### X4 多角度同行審查

| 視角 | 發現 |
|---|---|
| 主公視角 | 主公要的是少看到 429 showcase，不是下午突然沒報告；P86 必須清楚說 cron 變晚的 tradeoff。 |
| 世界頂尖駭客 / 紅隊攻擊者視角 | P86 不新增 secret 與外部 provider，攻擊面主要是 CI/CD 誤改與 secret log；維持 configured/missing，不印 key。 |
| 接手者視角 | 接手者需要從測試知道哪些 Gemini model 名稱被禁止，而不是靠讀 Google docs 記憶。 |
| X4-J 自動化建議性工具邊界 | model policy test 只能防文字回歸，不能證明 Google endpoint 當天一定可用；Actions 實跑仍必要。 |
| X4-K 使用者端審查官 / Patric 型人格 | 下午自動報告可能讓主公早上以為系統沒跑；handoff 與 runbook 必須說明 `workflow_dispatch` 可手動跑。 |

## 9. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | `gemini-2.5-flash-lite` 在現有 JSON schema 行為與 2.0 不完全一致 | 中 | 中 | 外部依賴 | focused import + mocked schema tests；Actions 實跑觀察 |
| R2 | cron 改晚讓主公早上看不到新報告 | 中 | 中 | UX / DevOps | 保留 workflow_dispatch；P90/P92 評估早報 local-only + 下午 enrichment |
| R3 | 只換 model 無法根治 429 | 高 | 中 | 架構 | P86 明確只止血；P90 budget ledger 承接根治 |
| R4 | 2.5 models 也有 2026-10-16 shutdown date | 中 | 高 | 外部依賴 | 文件設 2026-10-01 review trigger；P93/Pfuture 評估 3.1 |
| R5 | GitHub cron 不是精準排程，改到 UTC 08:30 仍可能延遲 | 中 | 低 | DevOps | Actions 實跑記錄實際 start time；不把分鐘精準當 SLO |
| R6 | P86 凍結被誤解成已改程式碼 | 低 | 中 | 流程 | handoff 明寫 FROZEN，不可動 runtime |

高風險加權檢查（META4）：

- 高影響風險：R4。
- 加權分數：5.5 分。
- 是否 >= 5 須請示主公：是；P86 目前只凍結計畫，實作需主公另行核准。

## 10. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| P86.0 | 計畫凍結與官方查證 | 過期資料導致錯誤計畫 | `lint_phase_plan` PASS |
| P86.1 | Model list 現代化 | 2.0 shutdown endpoint | model policy tests |
| P86.2 | Workflow schedule 現代化 | 舊 RPD window 429 | schedule tests + workflow comment |
| P86.3 | 驗證與收官 | 回歸 / 交接偏航 | focused tests + py38 import + handoff/history |

## 11. 影響檔案清單

P86 凍結階段新增：

- `docs/PHASE_86_PLAN.md`

P86 凍結階段修改：

- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`（append only）

P86 實作核准後預計修改：

- `analyzer/gemini_client.py`
- `.github/workflows/daily_report.yml`
- `tests/test_429_retry.py`（如需調整 model count assumptions）
- `tests/test_gemini_model_policy.py`（新增）
- `tests/test_daily_report_schedule.py`（新增）

P86 明確不修改：

- `analyzer/fallback_llm_client.py`
- `analyzer/sentiment.py`
- `main.py`
- `reporter/**`
- `scripts/system_doctor.py`
- `data/**`

## 12. Forbidden Work

- 不新增 `OPENAI_API_KEY`。
- 不接 Groq / Cloudflare / GitHub Models。
- 不建立 provider abstraction。
- 不做 P87 report core contract。
- 不做 P89 quality tier / promotion gate。
- 不做 P90 budget ledger / cooldown。
- 不刪除任何 report / run / cache 資料。
- 不 git push；push 前必問主公。

## 13. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] P86 改 model 後 Actions 出現非 429 provider error。
- [ ] P86 改 cron 後主公誤以為 daily job 沒跑。
- [ ] P86 後仍連續 3 次 429，且無法由 P90 前置指標解釋。
- [ ] 有任何「我以為官方 replacement 就完全相容」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-86-gemini-model-schedule.md`

## 14. Pre-flight 多視角體檢（STR10）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| X4-A 世界頂尖駭客 / 紅隊攻擊者 | P86 不新增 secrets 或 provider，因此主要攻擊面是 CI/CD 誤改、workflow log 洩漏與模型錯誤造成 fallback 行為；最小緩解是只印 configured/missing、不動 secret handling。 |
| X4-B 接手者視角 | 接手者需要知道 P86 只處理 model list 與 cron，不處理 quality tier；禁止 model test 會防止 2.0 名稱回流。 |
| X4-C 災難情境 | 情境：改成 2.5 後 Actions 因 schema 差異失敗；緩解：保留 workflow_dispatch、focused tests、收官要求實跑 evidence。 |
| X4-D 5 年後視角 | 五年後 Gemini 版本必然不同，P86 的真正價值是建立 model deprecation policy test，而不是只換一次字串。 |
| X4-E 終端 vs IDE | Windows 本機不會跑 cron，Ubuntu Actions 才會；P86 必須靠 workflow text test 與 Actions 實跑，而不是本機推測。 |
| X4-F 跨平台 Win/Mac/Linux | Python 測試可跨平台，但 cron 與 `TZ=Asia/Taipei` 是 Linux workflow 語境；P86 不把 shell date 搬進核心邏輯。 |
| X4-G 主公個人視角 | 主公不想花錢，也不想系統一直 showcase；P86 是先避開 shutdown 與舊 quota window，不承諾單獨根治所有 429。 |
| X4-H 觀測 / 治理 | P86 後若仍 429，需要 manifest/provider diagnostics 與 P90 budget ledger 接手，不能把 P86 宣稱為 R-016 關閉。 |
| X4-I 主公可見性 | 主公看不到 GitHub cron 與 Pacific reset 的時間差；handoff 必須把台北 16:30 的 tradeoff 寫清楚。 |
| X4-J 自動化建議性工具邊界 | 測試只能驗證 repo 裡沒有 deprecated model 字串，不能驗證 Google 當天 quota 或 endpoint 可用；需 Actions 實跑。 |
| X4-K 使用者端審查官 / Patric 型人格 | 使用者最可能困惑的是「為什麼報告下午才跑」；文件要說這是為了避開 RPD reset 前的舊配額窗口。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| Jarvis 型總控 | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P86 只做 model/schedule，不做 P87-P95 |
| Ken 型紅隊 / 技術長 | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD | 觸發；workflow secret handling 不動 |
| Patric 型使用者端審查官 | 固定必看 | 主公 / 使用者 / 接手者是否會誤解 | 觸發；cron 改晚的使用體感需明列 |
| Jimmy 型文件主筆 | 改 docs / TASK_HISTORY / handoff 時觸發 | 文字可追溯、有來源、避免空泛 | 觸發；官方來源與日期寫入本計畫 |
| Marcus 型數據分析師 | 涉及數據、趨勢、判斷依據時觸發 | 沒數據時是否明說 | 觸發；P86 不宣稱已量化降低 429，只做根據官方 reset 的風險降低 |
| Oliver 型設計審查 | 涉及 UI、報告、圖表時觸發 | 視覺層級、可讀性、A11y | 不觸發；P86 不改報告 UI |
| Penny 型 CFO | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量 | 觸發；不新增付費 API，Lite first |
| Jason 型執行 / DevOps | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell | 觸發；cron 改動與 Actions 實跑是 P86 驗收核心 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 只換 2.5 model 可能仍 429，是否浪費 Phase？ | **S** | 0 | P86 目標是移除 shutdown 風險與排程舊窗口，不承諾單獨根治 429；P90 承接 budget | 入計畫範圍 |
| 2 | cron 改到台北下午會不會讓主公早上失去每日情報？ | **S** | 0 | P86 保留 workflow_dispatch；早報 local-only / 下午 enrichment 放 P90/P92 評估 | 入計畫範圍 |
| 3 | `gemini-3.1-flash-lite` 看起來更長壽，為什麼不直接 primary？ | A | 0 | P86 選最小風險官方 2.0 replacement；3.1 先候選，需 Actions endpoint/schema 實測 | 入計畫範圍 |
| 4 | model policy test 只是字串測試，無法保證 endpoint 可用。 | A | 0 | 正確；收官需 workflow_dispatch 或 scheduled Actions evidence，不靠字串測試宣稱可用 | 入計畫範圍 |
| 5 | 2.5 也會 2026-10 shutdown，是否只是把問題往後拖？ | A | 0 | P86 增加 2026-10-01 review trigger，後續 P93/Pfuture 評估 3.1 migration | 入計畫範圍 |
| 6 | schedule 根據 Pacific reset 推論，但 GitHub cron 延遲與 Google 實際容量不保證，會不會假安全？ | **S** | 0 | P86 只降低舊 window 風險，不保證容量；P90 budget ledger 才處理可用量判斷 | 入計畫範圍 |

## 15. 狀態機與下一步

```text
P86: FROZEN
Next: 主公核准 P86 APPROVED -> 才能改 analyzer/gemini_client.py 與 daily_report.yml
```

新視窗最小讀取：

1. `NEXT_SESSION_HANDOFF.md` active bootstrap
2. `docs/PHASE_86_PLAN.md`
3. 若要動工，先確認主公已明確核准 P86
