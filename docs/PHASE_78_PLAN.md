# Phase P78 計畫書 — Run Manifest 合約化（凍結版）

> 草案日期：2026-05-16
> 凍結日期：2026-05-16
> 狀態：CLOSED（已完成 P78.0 + P78.1 + P78.2 + P78.3）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P78 |
| 名稱 | Run Manifest 合約化 |
| 影響半徑 | 標準（3-6 檔） |
| 負責模型 | GPT-5.3-Codex 高 |

## 1. 目標

建立 daily run 的權威狀態檔，讓每次執行都可追溯 `mode/status/metrics/paths/history`，供後續 doctor 與 promotion gate 使用。

## 1.5 Entry Criteria

- [x] P77 已以外部配額阻塞收官，runtime 止血不再擴散到本 Phase。
- [x] P78 只處理 manifest / eligibility 合約，不改報告版面與 promotion atomic write。
- [x] `main.py` 已有 run 結尾可接入 manifest 的穩定位置。
- [x] `scripts/check_daily_report_health.py` 已可提供 production / landing health 訊號。
- [x] 不全讀 `TASK_HISTORY.md`；歷史只用尾端與 anchor search。

## 2. 已落地（P78.0）

- 新增 `analyzer/run_manifest.py`：
  - `build_manifest()`
  - `manifest_path()`
  - `write_manifest()`
- `main.py` 已在流程結尾寫入：
  - `data/runs/YYYY-MM-DD/run_manifest.json`
- 實測已生成 `data/runs/2026-05-16/run_manifest.json`。

## 2.1 已落地（P78.1）

- `analyzer/run_manifest.py` 新增 manifest contract 驗證：
  - `validate_manifest()`
  - `write_manifest()` 寫檔前先驗證，不符合即 `ValueError`
- contract 包含：
  - `schema_version/run_date/status/mode/publish_eligible` 一致性
  - `paths/metrics/history` 型別與欄位完整性
  - `replay_source/is_backfill` 可追溯欄位
- 測試：
  - `tests/test_run_manifest.py` 補 invalid/valid contract case

## 3. 後續子階段

| 子階段 | 內容 |
|---|---|
| P78.1 | 補 schema 驗證器（manifest schema contract） |
| P78.2 | 補 history source dates/missing dates |
| P78.3 | publish eligibility 升級規則（shadow->blocking） |

## 3.1 已落地（P78.3）

- `config.py` 新增 `PUBLISH_GATE_MODE`（`off` / `shadow` / `blocking`，預設 `shadow`）。
- `main.py` 新增 `evaluate_publish_gate()`：
  - production 模式下使用 `check_daily_report_health.run_checks()` 評估 gate。
  - 非 production 直接標記不合格原因（誠實揭露）。
- `analyzer/run_manifest.py` 擴充 `eligibility` 欄位：
  - `gate_mode` / `decision` / `reasons` / `blocking_enforced` / `shadow_blocked`
  - `publish_eligible` 改為綜合 `(mode/status/eligibility.reasons)` 判定。
- `main.py` 發布決策：
  - `shadow`：只記錄不合格，不阻擋同步。
  - `blocking`：不合格時阻擋 `github_backup_job`。

## 3.2 已落地（P78.2）

- `analyzer/history.py` 新增 history diagnostics：
  - `source_dates`：成功讀到的歷史日期（YYYY-MM-DD）
  - `missing_dates`：缺檔或壞檔日期（YYYY-MM-DD）
  - `status`：`ok` / `partial` / `degraded` / `showcase`
- `resolve_trends()` 在一般模式與 fallback 模式都會輸出 diagnostics。
- `run_manifest` 透過既有 `history_delta.diagnostics` 寫入 `history.source_dates` / `history.missing_dates`。
- 測試：
  - `tests/test_history_resolver.py` 補 source/missing dates case。

## 4. Exit Criteria

- [x] 主流程每次 run 都寫入 manifest（P78.0）
- [x] manifest 含 `mode/status/publish_eligible/metrics/paths/history`
- [x] schema 驗證（P78.1）
- [x] history source 可追溯（P78.2）
- [x] eligibility 規則升級（P78.3）

## 5. 17 層稽核表

> 影響半徑：標準 Phase（3-6 檔）。依新規則採全 17 層逐層列示；B 級未觸發者明列 N/A 理由。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | 新增 `run_manifest` contract helper，`main.py` 只接既有流程尾端 | manifest 欄位散落造成難維護 | 集中在 `analyzer/run_manifest.py` |
| 2 | 邏輯層 (Logic) | `publish_eligible` 由 mode/status/eligibility reasons 綜合判定 | showcase 被誤判 production | 非 production 一律 ineligible |
| 3 | 架構層 (Architecture) | manifest 作為 P79/P80 的 shared truth source | 過早把 doctor/promotion 混進 P78 | P78 只產生 contract，不做 P80 promote |
| 4 | 測試層 (Testing) | `tests/test_run_manifest.py` 覆蓋 schema、gate、backfill 欄位 | contract 漂移但測不出 | `write_manifest()` 寫前驗證 |
| 5 | 資料層 (Data) | `schema_version`、paths、metrics、history、eligibility 明文化 | 舊 manifest 無法遷移 | schema version 留演進入口 |
| 6 | 可觀察性層 (Observability) | manifest 明列 mode / publish_eligible / reasons | 線上壞了只能翻 log | debug bundle / doctor 後續讀 manifest |
| 7 | 韌性層 (Resilience) | gate 預設 shadow，先觀測不阻斷 | blocking 過早導致發布停擺 | `PUBLISH_GATE_MODE=shadow` 預設 |
| 8 | 效能層 (Performance) | N/A，manifest 為小型 JSON 寫入 | 無顯著效能風險 | 保持單檔 atomic write |
| 9 | UX/A11y 層 | N/A，不改 UI / template | 無 | 報告視覺留 P80/P83 後續 |
| 10 | 安全層 (Security) | manifest 不寫 raw 原文、不寫 secrets | debug / manifest 泄漏敏感內容 | 僅寫路徑與統計 |
| 11 | 部署層 (DevOps) | N/A，不改 workflow / deployment | 無 | P79/P80 再接 CI / promotion |
| 12 | 成本層 (Cost) | 記錄 llm_calls/cache hit，先觀測成本 | API 成本失控不可見 | manifest metrics 提供後續 doctor |
| 13 | 可維護性層 (Maintainability) | contract 驗證集中化 | 多處手刻欄位檢查 | `validate_manifest()` 作單一入口 |
| 14 | 文件層 (Documentation) | 本計畫、handoff、TASK_HISTORY 同步 | 新視窗接手誤判 P78 狀態 | L1/L2/L4 狀態同步 |
| 15 | 流程層 (Process) | P78.0/P78.1/P78.3 小步落地，P78.2 保留 | 子階段跳躍後漏項 | Exit Criteria 保留 P78.2 未完成 |
| 16 | 隱私/合規層 (Privacy) | N/A，不新增抓取與個資處理 | 無 | manifest 不存 raw content |
| 17 | i18n/在地化層 | N/A，不改文字渲染與日期顯示規則 | 無 | P82 處理 timezone/idempotency |

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| X4-A 攻擊者視角 | manifest 若寫入 raw 內容可能洩漏資料，因此只能寫路徑與統計，不寫原文。 |
| X4-B 接手者視角 | 接手者需可從單一 manifest 知道今天是 production 還是 showcase_forced。 |
| X4-C 災難情境 | 若執行途中失敗但沒 manifest，會再回到「看 log 猜狀態」。 |
| X4-D 5 年後視角 | schema version 必須存在，不然後續欄位演化會斷裂。 |
| X4-E 終端 vs IDE | manifest 需純 JSON，終端/IDE/CI 都能讀。 |
| X4-F 跨平台 | 路徑字串僅供追蹤，不應作 OS 相依解析判斷。 |
| X4-G 主公個人視角 | 主公要看到每天是否可發布，不想再從多檔拼狀態。 |
| X4-H 觀測 | doctor 將以 manifest 為主輸入來源，這是 P79 前置。 |
| X4-I 主公可見性 | run manifest 應明確標示 mode 與 publish_eligible，避免暗箱降級。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | manifest 寫了但沒 schema，可能越改越亂。 | **S** | 0 | P78.1 直接補 schema validator。 | 入計畫範圍 |
| 2 | publish_eligible 若只看 mode，可能漏掉關鍵錯誤。 | **S** | 0 | 後續納入 status/error/health 結果。 | 入計畫範圍 |
| 3 | history 目前只有點數，無來源日期，追溯力不足。 | A | 0 | P78.2 補 source dates/missing。 | 入計畫範圍 |
| 4 | manifest 寫入失敗目前只 warning，可能被忽略。 | A | 0 | P79 doctor 納入強檢。 | 入計畫範圍 |
| 5 | 路徑寫絕對路徑在跨機器比對時不穩。 | A | 0 | 可在 P78.1 加 relpath 欄位並存。 | 入計畫範圍 |
| 6 | 外部 429 時 manifest 仍為 ok，可能被誤解。 | A | 0 | mode=showcase_forced + publish_eligible=false 已區分。 | 入計畫範圍 |
