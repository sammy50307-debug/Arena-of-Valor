# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P83（Data Quality / Security） |
| **Current Step** | P83.0 inventory：盤點 source/LLM/report/manifest/debug bundle 的 raw/sanitized 邊界 |
| **Mode** | APPROVED |
| **Latest Verified Commit** | `88f9ba5 docs: 凍結 P83 data quality security 計畫` |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-17 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_83_PLAN.md`
4. 總戰役計畫：`docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P83（APPROVED） |
| **Current Step** | P83.0 inventory：source/LLM/report/manifest/debug bundle raw/sanitized 邊界 |
| **Allowed Files** | `analyzer/run_manifest.py`, `analyzer/data_writer.py`, `analyzer/sentiment.py`, `reporter/generator.py`, `reporter/templates/*`, `scripts/system_doctor.py`, `scripts/debug_bundle.py`, `docs/OPERATIONS_RUNBOOK.md`, `tests/*`, `docs/PHASE_83_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage untracked reports；不跳做 P84；不重寫 P80 promotion 架構；不更換 LLM provider |
| **Exit Criteria** | 完成 P83.0 inventory 後，再進 P83.1 source health / 0 posts anomaly |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap，再依 P83 計畫從 P83.0 接續 |

## State Machine

```text
DRAFT -> FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED
```

| 狀態 | AI 可做事項 |
|---|---|
| **DRAFT** | 只能討論，不可改檔 |
| **FROZEN** | 等主公核准，不可改檔 |
| **APPROVED** | 可依計畫動工 |
| **IN_PROGRESS** | 繼續當前 step |
| **VERIFYING** | 只能測試、修同範圍問題 |
| **CLOSED** | 不可再改，開下一 Phase |

## Required Verification

```powershell
git status -sb
git diff --check
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P80 已收官：2026-05-17 GitHub Actions `daily_report.yml` / `workflow_dispatch` 的 `run-pipeline` succeeded（42s，主公截圖確認），最新驗證 commit 為 `5a3c25d`。

## Next Decision

P83 已由主公核准。下一步從 P83.0 inventory 開始，先盤點 source/LLM/report/manifest/debug bundle 的 raw/sanitized 邊界，再進 P83.1。
