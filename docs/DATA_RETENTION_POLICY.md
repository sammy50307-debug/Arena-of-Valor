# Data Retention Policy（P84.1）

> 狀態：ACTIVE（2026-05-17）
> 原則：本政策與 `scripts/retention_policy.py` 只做 dry-run / advisory；不刪除、不搬移、不改寫任何歷史資料。

## 1. 安全邊界

- 預設行為：只盤點、只輸出候選清單。
- `scripts/retention_policy.py` 不提供刪除參數。
- 任何實刪、搬移、壓縮、改寫歷史資料，都必須另開 Phase 並由主公明確核准。
- raw / analysis 原始快照不納入自動清理，只列入 protected inventory。

## 2. 保留策略

| Policy | 路徑 | 保留規則 | dry-run 候選條件 | 自動刪除 |
|---|---|---|---|---|
| `reports_canonical` | `data/reports/aov_report_YYYY-MM-DD.html` | 保留至少 180 天 | 檔名日期超過 180 天 | 否 |
| `reports_variants` | `data/reports/*_v*.html`, `data/reports/PREVIEW_*.html` 等 | 保留至少 30 天 | 日期或 mtime 超過 30 天 | 否 |
| `run_manifests` | `data/runs/YYYY-MM-DD/` | 保留至少 180 天 | 目錄日期超過 180 天 | 否 |
| `debug_bundles` | `data/debug_bundles/YYYY-MM-DD/` | 保留至少 30 天 | 目錄日期超過 30 天 | 否 |
| `quarantine` | `data/quarantine/`, `data/_quarantine/` | 保留至少 90 天 | 檔案 mtime 超過 90 天 | 否 |
| `llm_cache` | `data/llm_cache.json` | 由 `CacheManager` TTL + max entries 管理 | 只警示，不列刪除候選 | 否 |
| `llm_cache_backup` | `data/llm_cache.json.bak` | 保留至少 30 天 | mtime 超過 30 天 | 否 |
| `raw_analysis_snapshots` | `data/raw_*.json`, `data/analysis_*.json` | 人工複核 | 不列自動候選 | 否 |

## 3. 指令

```powershell
py scripts\retention_policy.py --repo-root .
py scripts\retention_policy.py --repo-root . --json
py scripts\retention_policy.py --repo-root . --today 2026-05-17 --max-candidates 100
```

輸出必須包含：

- `mode: dry-run`
- `dry_run: true`
- `will_delete: false`

## 4. 解讀方式

- `candidate_count > 0` 不代表可以刪，代表可以進入人工 archive review。
- `data/llm_cache.json` 是跨日節省 LLM 呼叫的持久化狀態，不由 retention checker 刪除。
- `data/_quarantine/` 是舊 quarantine 位置；`data/quarantine/` 是 P81 replay/quarantine 位置，兩者都納入盤點。
- `raw_*.json` 與 `analysis_*.json` 可能是 replay/backfill 與 debug 的來源，P84.1 只保護與列數量。
