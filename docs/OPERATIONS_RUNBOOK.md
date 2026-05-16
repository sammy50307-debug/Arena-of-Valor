# Operations Runbook（P79.2）

> 更新日期：2026-05-16  
> 用途：提供 `scripts/system_doctor.py` 的 issue code 對應處置步驟，供本地與 CI 機械化引用。

## 使用方式

執行 doctor 後，直接用輸出的 `code` 對照本檔相同代碼段落執行處置，不需再人工猜測。

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
