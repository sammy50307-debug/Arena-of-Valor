# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P84（Long-Term Governance / CLOSED） |
| **Current Step** | P84.6 CLOSED：P77-P84 總收官完成；R-016 保留 Open operational risk |
| **Mode** | CLOSED |
| **Latest Verified Commit** | `HEAD docs: 完成 P84.6 P77-P84 closeout`（本地 commit，待主公確認 push） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-18 |

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
| **Current Phase** | P84（CLOSED） |
| **Current Step** | P84.6 CLOSED：P77-P84 總收官完成；R-016 保留 Open operational risk |
| **Allowed Files** | 預設不可動工；若主公要求維護 R-016，可讀 `docs/P77_P84_CLOSEOUT_REPORT.md`, `docs/RISK_REGISTRY.md`, `docs/OPERATIONS_RUNBOOK.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`（append only）與必要的 production/backfill 檔案 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage untracked reports；不實刪歷史資料；不自動開 P85；不把 P84 CLOSED 解讀成 production SLO 已恢復；不重寫 P80 promotion/P83 security |
| **Exit Criteria** | P84.6 已完成；P77-P84 總戰役 CLOSED WITH KNOWN OPERATIONAL RISK；R-016 留待主公另行指示 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若主公要修 R-016，依 closeout report 的 production/backfill/recovery 順序處理；否則等待明確任務 |

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

P84.6 已收官：2026-05-18 P77-P84 總收官驗證完成，`py -m pytest -q` -> `204 passed`；handoff truth / governance doctor / phase lint / Python 3.8 import guard 皆通過。SLO checker 與 latest report health 揭露 R-016：production SLO blocking 與 landing stale，仍為 Open operational risk。

## Next Decision

目前沒有自動開啟的新 Phase。若主公要處理 R-016，下一步應是 production/backfill/recovery 範圍；否則等待主公明確指定新任務。push 前仍需主公確認。
