# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P83（Data Quality / Security） |
| **Current Step** | 建立並凍結 `docs/PHASE_83_PLAN.md`；尚未核准前不可改程式碼 |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `4a9f543 feat: 落地 P82 run context 與 run identity` |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-17 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_83_PLAN.md`（尚未建立前，以 `docs/PHASE_TEMPLATE.md` + 總戰役 P83 段落起草）
4. 總戰役計畫：`docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P83（DRAFT） |
| **Current Step** | 起草 `docs/PHASE_83_PLAN.md`，聚焦 data quality / security，不進入程式動工 |
| **Allowed Files** | `docs/PHASE_83_PLAN.md`, `docs/PHASE_TEMPLATE.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage untracked reports；不改程式碼；不跳做 P84 |
| **Exit Criteria** | P83 計畫書完成 17 層稽核、M1/M2、Entry/Exit Criteria，並等待主公核准 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap，再起草/審核 P83 計畫 |

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

P82 已完成本地驗證並收官：`py -m pytest -q` 為 163 passed，Python 3.8 import smoke 通過。下一步進入 P83 草案期，先建立/凍結 `docs/PHASE_83_PLAN.md`。
