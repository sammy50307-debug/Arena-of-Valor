# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P84（Long-Term Governance） |
| **Current Step** | P84.1 APPROVED：開始 Retention policy / dry-run inventory |
| **Mode** | APPROVED |
| **Latest Verified Commit** | `1d60208 docs: 凍結 P84 long-term governance 計畫`（已推送到 `origin/main`） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-17 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_84_PLAN.md`
4. 總戰役計畫：`docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P84（APPROVED） |
| **Current Step** | P84.1 Retention policy / dry-run inventory |
| **Allowed Files** | `docs/PHASE_84_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`, P84.1 新增的 retention policy / tests / runbook 檔 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage untracked reports；不實刪歷史資料；不跳到 P84.2-P84.6；不重寫 P80 promotion/P83 security |
| **Exit Criteria** | P84.1 完成 retention policy 與 dry-run inventory，測試通過，狀態文件與 TASK_HISTORY 同步 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；P84 已 APPROVED，只能先做 P84.1，不可跨步到後續 stage |

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

P84 已由主公核准。下一步進 P84.1 Retention policy / dry-run inventory；不得實刪資料，不得跳到 P84.2-P84.6；push 前仍需主公確認。
