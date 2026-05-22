# Operations Runbook（P79.2 / P84.2 / P84.3 / P84.4）

> 更新日期：2026-05-22
> 用途：提供 `scripts/system_doctor.py` / `scripts/slo_checker.py` / `scripts/check_handoff_truth.py` / `scripts/governance_doctor.py` 的 issue code 對應處置步驟，供本地與 CI 機械化引用。

## 使用方式

執行 doctor 後，直接用輸出的 `code` 對照本檔相同代碼段落執行處置，不需再人工猜測。新增任何 `DOC###` / `SLO###` / `HND###` / `GOV###` 時，同一個 commit 必須補對應 anchor，並跑 `py scripts\governance_doctor.py --repo-root .`。

## Issue Code 對照

### <a id="doc000"></a>DOC000 — no issue
- 意義：doctor 未檢出異常。
- 處置：無需動作。

### <a id="doc001"></a>DOC001 — manifest missing
- 意義：`data/runs/<date>/run_manifest.json` 不存在。
- 處置：
  1. 先重跑當日流程：`py main.py --run-now --force`
  2. 若仍缺失，改用 replay/backfill：`py scripts/replay_run.py --date <date> --check-health --expected-mode any --debug-bundle`

### <a id="doc002"></a>DOC002 — manifest invalid json
- 意義：manifest 檔案損毀或非合法 JSON。
- 處置：
  1. 開啟該 manifest 檢查是否寫入中斷。
  2. 以 replay/backfill 重建 manifest。

### <a id="doc003"></a>DOC003 — manifest contract
- 意義：manifest 欄位不符合合約。
- 處置：
  1. 執行：`py -m pytest -q tests/test_run_manifest.py`
  2. 檢查 `analyzer/run_manifest.py` 與呼叫端是否欄位漂移。

### <a id="doc004"></a>DOC004 — run status
- 意義：run status 非 `ok`。
- 處置：
  1. 讀最新 debug bundle：`data/debug_bundles/<date>/debug_bundle_*.json`
  2. 依 bundle `error` 欄位定位上游失敗點。

### <a id="doc005"></a>DOC005 — run mode
- 意義：當日輸出非 `production`。
- 處置：
  1. 檢查配額與外部 API（Gemini/OpenAI/Tavily/Apify）。
  2. 若為外部阻塞，記錄為 degraded 並進入 P81 backfill/replay 流程。

### <a id="doc006"></a>DOC006 — eligibility decision
- 意義：publish eligibility 判定為 `ineligible`。
- 處置：
  1. 查看 manifest `eligibility.reasons`。
  2. 按 reason 修正後重跑 doctor 驗證。

### <a id="doc007"></a>DOC007 — history source coverage
- 意義：history `source_dates` 為空且存在缺檔日。
- 處置：
  1. 補齊缺失 `analysis_YYYYMMDD.json`。
  2. 跑 backfill/replay 生成可用歷史資料。

### <a id="doc008"></a>DOC008 — health canonical report
- 意義：當日 canonical report 缺失。
- 處置：
  1. 檢查 `data/reports/aov_report_<date>.html` 是否產生。
  2. 若缺失，執行 replay/backfill 重建。

### <a id="doc009"></a>DOC009 — health landing main link
- 意義：`index.html` 主按鈕未對到當日報告。
- 處置：
  1. 修正 landing link 指向。
  2. 重跑 `py scripts/check_daily_report_health.py --date <date> --expected-mode any`。

### <a id="doc010"></a>DOC010 — health generic
- 意義：其他 health check 失敗（例如 metadata mode / landing target mode / git clean）。
- 處置：
  1. 依 detail 指向的 check 名稱逐項處理。
  2. 每修一項就重跑 health + doctor。

### <a id="doc011"></a>DOC011 — debug bundle linked
- 意義：doctor 在失敗時已關聯最新 debug bundle。
- 處置：
  1. 直接打開 doctor 顯示的 bundle path。
  2. 以 bundle 的 `status/error/health.checks` 作為第一層根因線索。

### <a id="doc012"></a>DOC012 — debug bundle missing
- 意義：doctor 失敗時找不到當日 debug bundle。
- 處置：
  1. 先補產 bundle：`py scripts/replay_run.py --date <date> --check-health --expected-mode any --debug-bundle`
  2. 再重跑 doctor，確認可關聯最新 bundle。

### <a id="doc013"></a>DOC013 — quality no posts
- 意義：manifest `quality.source_health` 顯示當日 source ingress 抓到 0 posts。
- 處置：
  1. 先判斷外部來源是否全掛：Tavily、Dcard、巴哈或網路連線。
  2. 修復來源後重跑：`py main.py --run-now --force`
  3. 若外部來源短暫阻塞，記錄 degraded，不要把 0 posts 解讀成「社群完全無聲量」。

### <a id="doc014"></a>DOC014 — quality source health
- 意義：manifest `quality.source_health` 顯示來源覆蓋不足，例如單一平台或單一來源。
- 處置：
  1. 查看 manifest `quality.source_health.platform_counts` 與 `reasons`。
  2. 若只剩單一平台，檢查其餘平台 scraper/API 是否失敗。
  3. 修正後重跑 doctor；本代碼預設為 advisory，不直接代表報告不可發布。

### <a id="doc015"></a>DOC015 — quality core contract
- 意義：manifest `quality.core_contract` 顯示報告核心契約缺失、未知、警告或失敗。P87 階段此訊號只用來定位與觀察，不直接改 promotion gate。
- 處置：
  1. 查看 manifest `quality.core_contract.status` 與 `reasons`。
  2. 若為 `missing_report` 或 `missing_analysis`，先檢查 report / analysis 產物是否真的生成。
  3. 若為 `insufficient_posts`、`insufficient_platforms`、`insufficient_sources`，回頭檢查來源搜集與 scraper/API 狀態。
  4. 修正後重跑：`py scripts\system_doctor.py --repo-root . --date <date> --profile local --require-production`。

### <a id="doc016"></a>DOC016 — quality tier
- 意義：manifest `quality.tier` 缺失、非法，或落在不可發布 tier（`showcase_manual` / `error_fallback`）。
- 處置：
  1. 查看 manifest `quality.tier`、`quality.analysis_source`、`quality.llm_coverage` 與 `eligibility.reasons`。
  2. 若 tier 是 `production_local_only`，代表真實資料與本地 baseline 可發布，但 LLM 深讀未完整覆蓋；這不是 blocking。
  3. 若 tier 是 `showcase_manual`，確認是否主公手動 `--showcase`，不可 promotion。
  4. 若 tier 是 `error_fallback`，依 `quality.core_contract.reasons` 或 `status/error` 修復後重跑 doctor。

### <a id="doc017"></a>DOC017 — budget cooldown
- 意義：manifest `budget` 顯示本次 run 因 LLM budget/cooldown 停損，或本日 budget 已耗盡。這是 pipeline proxy，不是 Google provider billing truth。
- 處置：
  1. 查看 manifest `budget.decision`、`budget.decision_reason`、`llm_calls_used`、`max_daily_llm_calls`、`cooldown_until_utc`。
  2. 若 reason 是 `cooldown_active` 或 `quota_error`，等待 cooldown 過期後重跑；不要補 OpenAI API key 當主線。
  3. 若 reason 是 `budget_exhausted`，代表本日 pipeline 呼叫額度已用完；後續應走 `production_local_only` 或等下一個業務日。
  4. 若 reason 是 `budget_state_malformed`，檢查 `data/llm_budget_state.json` JSON 格式；確認不含 raw prompt / raw post 後修復或重建。

### <a id="doc018"></a>DOC018 — selection throttle
- 意義：manifest `selection` 顯示 P91 已將部分來源留在 local deterministic baseline，或 duplicate/top-N 節流正在生效。
- 處置：
  1. 查看 manifest `selection.llm_selected_posts`、`local_only_posts`、`duplicate_posts`、`reason_counts`。
  2. 若為 advisory，代表節流正常生效；用 report 與 local baseline 檢查洞察品質即可。
  3. 若 selected 超過 `max_llm_items`，先跑 `py -m pytest -q tests\test_source_selection.py tests\test_run_manifest.py`，再檢查 `analyzer/source_selection.py` 是否計算 cap 漂移。
  4. 不要因本 issue 直接開 OpenAI fallback；P91 的主線是減少 LLM 深讀候選數。

### <a id="doc019"></a>DOC019 — enrichment replay
- 意義：manifest `enrichment` 顯示 P92 replay queue 狀態。`no_eligible` 多半代表 local-only 來源全為 duplicate / low-signal，這是 expected no-op；`pending` 代表有可補深讀貼文但尚未手動 replay；`failed` 才是需要處理的錯誤。
- 處置：
  1. 查看 manifest `enrichment.queue_available`、`eligible_posts`、`skipped_posts`、`enriched_posts`、`replay_status`、`skipped_reason_counts`。
  2. 若 `replay_status=no_eligible` 且 skipped reason 是 `duplicate_url` / `duplicate_signature`，不要重送 LLM，這表示 P91 節流成功。
  3. 若 `replay_status=pending` 且有剩餘 budget，可下載 Actions artifact 或使用本機 `data/enrichment_queue/<date>/enrichment_queue.json` 後執行 `py scripts\enrichment_replay.py --date <YYYY-MM-DD>` 先 dry-run。
  4. 若 dry-run 確認會補深讀，再執行 `py scripts\enrichment_replay.py --date <YYYY-MM-DD> --apply`；若要產候選報告才加 `--write-report`。
  5. 若 `replay_status=skipped_budget`，先看 `DOC017`，不得繞過 P90 budget/cooldown。

### <a id="doc999"></a>DOC999 — unknown doctor issue
- 意義：doctor 產生未登記於 `ISSUE_CATALOG` 的 fallback issue code。
- 處置：
  1. 檢查 `scripts/system_doctor.py` 新增的 `_add_issue(...)` key 是否漏補 `ISSUE_CATALOG`。
  2. 若是新類型，新增正式 `DOC###` code 與本 runbook anchor。
  3. 重跑 `py scripts\governance_doctor.py --repo-root .`。

### <a id="slo000"></a>SLO000 — no SLO issue
- 意義：SLO checker 未檢出 freshness / manifest / doctor severity 異常。
- 處置：無需動作。

### <a id="slo001"></a>SLO001 — production freshness
- 意義：尾端連續無 `production` canonical report 超過門檻。
- 處置：
  1. 先確認當日 workflow 是否有成功 run。
  2. 執行：`py scripts\slo_checker.py --repo-root . --date <date> --json`
  3. 若最新 run 是 showcase / error fallback，依 `DOC005` / `DOC006` 修復來源或配額問題。
  4. 修復後用 replay/backfill 補 production report，再重跑 SLO checker。

### <a id="slo002"></a>SLO002 — manifest gap
- 意義：SLO window 內缺少 `data/runs/<date>/run_manifest.json`。
- 處置：
  1. 檢查缺失日期的 GitHub Actions log 或本地 run log。
  2. 若該日有 analysis/report，可用 replay 重建：`py scripts\replay_run.py --date <date> --check-health --expected-mode any --debug-bundle`
  3. 重跑：`py scripts\slo_checker.py --repo-root . --date <date> --json`

### <a id="slo003"></a>SLO003 — doctor severity budget
- 意義：SLO window 內 doctor blocking day > 0，或 degraded day 超過門檻。
- 處置：
  1. 查看 SLO JSON 的 `days[]`，找出 `doctor_blocking` / `doctor_degraded` 非 0 的日期。
  2. 對那些日期跑：`py scripts\system_doctor.py --repo-root . --date <date> --profile local --require-production --skip-landing`
  3. 依 doctor 輸出的 `DOCxxx` code 回到本 runbook 處理。

### <a id="hnd000"></a>HND000 — handoff truth verified
- 意義：`NEXT_SESSION_HANDOFF.md` active bootstrap 通過 handoff truth check。
- 處置：無需動作。

### <a id="hnd001"></a>HND001 — active bootstrap markers
- 意義：`ACTIVE_BOOTSTRAP_START` / `ACTIVE_BOOTSTRAP_END` marker 缺失、重複或位置錯誤。
- 處置：
  1. 只修 `NEXT_SESSION_HANDOFF.md` 頂部 marker，不改 archive 舊段落。
  2. 重跑：`py scripts\check_handoff_truth.py --repo-root .`

### <a id="hnd002"></a>HND002 — bootstrap required fields
- 意義：active bootstrap 頂部狀態表缺少必要欄位。
- 處置：
  1. 補齊 Status / Program / Current Phase / Current Step / Mode / Latest Verified Commit / Updated At。
  2. 確認 `Mode` 與狀態機一致。

### <a id="hnd003"></a>HND003 — mode state
- 意義：`Mode` 不是允許的狀態值。
- 處置：
  1. 只能使用 DRAFT / FROZEN / APPROVED / IN_PROGRESS / VERIFYING / CLOSED。
  2. 若 Phase 已完成，切到下一個合法狀態，不要自創狀態詞。

### <a id="hnd004"></a>HND004 — six anti-drift fields
- 意義：Six Anti-Drift Fields 缺少必要欄位。
- 處置：
  1. 補齊 Current Phase / Current Step / Allowed Files / Forbidden Work / Exit Criteria / Resume Rule。
  2. 確認 Allowed / Forbidden 不會允許跨 Phase 或 stage。

### <a id="hnd005"></a>HND005 — bootstrap field consistency
- 意義：active bootstrap 頂部狀態表與 Six Anti-Drift Fields 的 Phase / Step / Mode 不一致。
- 處置：
  1. 以頂部 active bootstrap 的當前真相為準。
  2. 同步 Six Anti-Drift Fields 後重跑 checker。

### <a id="hnd006"></a>HND006 — archive boundary
- 意義：archive marker 缺失、重複或不在 active bootstrap 之後。
- 處置：
  1. 確保 `ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION` 只出現一次。
  2. 確保它位於 `ACTIVE_BOOTSTRAP_END` 後方。

### <a id="hnd007"></a>HND007 — active operation consistency
- 意義：`docs/ACTIVE_OPERATION.md` 的 Current Phase / Step / Mode 與 handoff 不一致。
- 處置：
  1. 先以 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 為準。
  2. 同步 `docs/ACTIVE_OPERATION.md` 的 Current State 與 Six Anti-Drift Fields。

### <a id="gov000"></a>GOV000 — governance verified
- 意義：runbook issue-code mapping 與 risk registry section/status 檢查通過。
- 處置：無需動作。

### <a id="gov001"></a>GOV001 — runbook missing anchor
- 意義：治理腳本中出現 `DOC###` / `SLO###` / `HND###` / `GOV###` / `CCG###`，但 `docs/OPERATIONS_RUNBOOK.md` 沒有對應 anchor。
- 處置：
  1. 確認該 issue code 是否真的會輸出給操作者。
  2. 若會輸出，在本檔新增該 code 的 lowercase anchor 段落與處置步驟。
  3. 重跑 `py scripts\governance_doctor.py --repo-root .`。

### <a id="gov002"></a>GOV002 — runbook duplicate anchor
- 意義：同一個 runbook anchor 被定義超過一次，可能讓 issue code 對應到錯誤處置段落。
- 處置：
  1. 搜尋重複的 `<a id="..."></a>`。
  2. 保留唯一權威段落，合併或移除重複段落。
  3. 重跑 governance doctor。

### <a id="gov003"></a>GOV003 — risk registry state mismatch
- 意義：`docs/RISK_REGISTRY.md` 的風險條目所在 section 與 `狀態` 欄位不一致。
- 處置：
  1. 若仍需觀察，放在 `開放風險（Open）` 並讓狀態包含 `Open`。
  2. 若已修補或已關閉，放在 `已關閉風險（Closed）` 並讓狀態包含 `已` 或 `Closed`。
  3. 重跑 governance doctor。

### <a id="gov004"></a>GOV004 — risk registry duplicate id
- 意義：`docs/RISK_REGISTRY.md` 重複使用同一個 `R-###`，會讓跨 Phase 風險追蹤失真。
- 處置：
  1. 找出重複的 `R-###` heading。
  2. 若是同一風險，合併成一筆；若是不同風險，重新編號較新的條目。
  3. 重跑 governance doctor。

### <a id="ccg000"></a>CCG000 — cost/cache governance verified
- 意義：P84.5 cost/cache governance 檢查通過；可從 manifest、report metadata 或 cache stats 讀到成本代理訊號。
- 處置：無需動作。

### <a id="ccg001"></a>CCG001 — metrics source missing
- 意義：指定 window 內找不到 `run_manifest.json` metrics，也找不到 report HTML metadata，無法建立成本/cache 趨勢輸入。
- 處置：
  1. 檢查 `data/runs/<date>/run_manifest.json` 是否產生。
  2. 若 manifest 缺失但 report 存在，確認報告首行仍含 `cache_hit` / `llm_calls` metadata。
  3. 若兩者都缺，先依 `SLO002` / `DOC001` 補 manifest 或重跑 replay/backfill。

### <a id="ccg002"></a>CCG002 — metrics invariant
- 意義：成本/cache 指標格式不合法，例如 `cache_hit` 或 `llm_calls` 大於 `total_calls`。
- 處置：
  1. 檢查 manifest `metrics` 或 report metadata 是否被手動寫壞。
  2. 修正產生端後重跑 `py scripts\cost_cache_governance.py --repo-root . --date <date>`。

### <a id="ccg003"></a>CCG003 — cache hit rate low
- 意義：window 內 aggregate cache hit rate 低於 advisory 門檻；這是成本代理訊號，不是供應商帳單。
- 處置：
  1. 先確認是否為外部配額恢復後的正常冷啟動。
  2. 若連續多日低命中，檢查 cache key dimensions、TTL、`CACHE_MAX_ENTRIES` 是否過小。
  3. 不要只因本 issue 直接刪 cache 或更換 provider。

### <a id="ccg004"></a>CCG004 — cache store stats
- 意義：`data/llm_cache.json` 缺失、損毀或 stats 欄位不可讀。
- 處置：
  1. 不要輸出 cache entries 內容；只檢查 schema、entry count、stats。
  2. 若 cache 檔損毀，保留備份後讓 `CacheManager` 重建。
  3. 重跑 cost/cache governance。

### <a id="ccg005"></a>CCG005 — llm call budget
- 意義：window 內 LLM call proxy 超過設定門檻，可能代表成本或配額壓力升高。
- 處置：
  1. 先確認 `total_llm_calls` 來源是 manifest 還是 report metadata。
  2. 對照 `CCG003` 判斷是否 cache hit 低造成。
  3. 若真實 API 費用需確認，另查供應商帳單；本 checker 不代表 billing truth。

### <a id="ccg006"></a>CCG006 — budget cooldown
- 意義：window 內至少一天 manifest `budget` 顯示 `skip_llm`、cooldown active、budget exhausted 或 malformed state。這是成本 / 配額停損訊號，不代表報告本身不可發布。
- 處置：
  1. 查看 cost/cache governance 輸出的 `budget_decision` 與 `budget_reason`。
  2. 若 reason 是 `cooldown_active`，等待 `cooldown_until_utc` 過期後再重跑。
  3. 若 reason 是 `budget_exhausted`，確認是否需要調整 `LLM_DAILY_BUDGET`；調整前先看 cache hit rate 與 P91/P92 是否尚未完成。
  4. 不要把本 issue 當成 provider billing truth；真實費用仍需查供應商帳單。

### <a id="ccg007"></a>CCG007 — selection throttle
- 意義：window 內 manifest `selection` 顯示 P91 節流正在生效，或 selected 數量超過 cap。
- 處置：
  1. 查看輸出列的 `selected` / `local_only` / `duplicate`。
  2. 若為 advisory，代表 Top-N / dedupe 正常降低 LLM call 壓力。
  3. 若為 degraded，檢查 `selection.llm_selected_posts > selection.max_llm_items` 的日期，修正 source selection 後重跑。
  4. 若 local-only 比例連續過高，後續走 P92 replay/backfill 補深讀，不在 P91 直接引入新 provider。

### <a id="ccg008"></a>CCG008 — enrichment replay
- 意義：window 內 manifest `enrichment` 顯示 P92 replay queue 有 pending / no-op / budget skip / partial / failed 狀態。
- 處置：
  1. advisory 的 `pending` 表示有 eligible queue 尚未補深讀；先用 `scripts\enrichment_replay.py` dry-run 看 budget 與候選數。
  2. advisory 的 `no_eligible` 表示 queue 存在但本批多為 duplicate / low-signal，不需補深讀。
  3. advisory 的 `skipped_budget` 依 `CCG006` 檢查 budget/cooldown。
  4. degraded 的 `failed` 才需要檢查 queue schema、provider error 或 replay merge 失敗；不要用調高 `LLM_DAILY_BUDGET` 當第一反應。
