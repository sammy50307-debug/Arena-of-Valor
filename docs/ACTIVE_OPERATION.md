# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P84（Long-Term Governance / CLOSED） |
| **Current Step** | R-016.1 DONE：manifest sync/backfill 已修補；R-016 仍保留 Open（production 尚未恢復） |
| **Mode** | CLOSED |
| **Latest Verified Commit** | `HEAD fix: 修補 R-016 manifest sync recovery`（本地 commit，待主公確認 push） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-19 |

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
| **Current Step** | R-016.1 DONE：manifest sync/backfill 已修補；R-016 仍保留 Open（production 尚未恢復） |
| **Allowed Files** | 若主公要求繼續 R-016，可讀 `docs/RISK_REGISTRY.md`, `docs/P77_P84_CLOSEOUT_REPORT.md`, `docs/OPERATIONS_RUNBOOK.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`（append only）、`.github/workflows/daily_report.yml`, `.gitignore`, `main.py`, `scripts/backfill_manifest_from_report.py`, `data/runs/**/run_manifest.json` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage unrelated untracked reports；不實刪歷史資料；不自動開 P85；不把 R-016.1 解讀成 production 已恢復；不重寫 P80 promotion/P83 security |
| **Exit Criteria** | R-016.1 已讓 `SLO002` manifest gap 收斂；R-016 仍因 `SLO001` no production 與 `SLO003` degraded budget 保持 Open |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若主公要繼續，下一步是確認外部 API/Actions 是否能產出 production，再跑 health + SLO；否則等待明確任務 |

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

R-016.1 已完成 manifest sync/backfill 修補：`data/runs/**/run_manifest.json` 已解除忽略，`main.py` 與 GitHub Actions fallback push 會同步 `data/runs/`，並已從 5/16-5/19 canonical reports 反建 report-only manifests。2026-05-19 SLO 已從 `SLO001/SLO002/SLO003` 收斂為 `SLO001` BLOCKING + `SLO003` DEGRADED；`SLO002` manifest gap 已消失。

## Next Decision

R-016 尚未關閉。下一步若主公要繼續，應確認外部 API / GitHub Actions 是否能產出 `mode=production`，再跑 `check_daily_report_health` 與 `slo_checker`；push 前仍需主公確認。
