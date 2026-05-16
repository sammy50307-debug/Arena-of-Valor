# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P82（Idempotency / Timezone） |
| **Current Step** | `docs/PHASE_82_PLAN.md` 已凍結；等待主公核准後才可動工 |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `5a3c25d fix: 補齊主鏈路 Python 3.8 型別註解防護` |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-17 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_82_PLAN.md`
4. 總戰役計畫：`docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P82（FROZEN） |
| **Current Step** | 審核 `docs/PHASE_82_PLAN.md`，等待主公核准 |
| **Allowed Files** | `docs/PHASE_82_PLAN.md`, `docs/PHASE_TEMPLATE.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage untracked reports；不改程式碼；不跳做 P83/P84 |
| **Exit Criteria** | 主公核准 P82 後，才可把狀態切 APPROVED 並開始 P82.0 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap，再讀 P82 凍結計畫並等待主公核准 |

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

P82 計畫已凍結。下一步是主公審核；核准後才可將狀態切為 APPROVED 並開始 P82.0。
