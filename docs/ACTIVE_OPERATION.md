# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P84（Long-Term Governance / CLOSED） |
| **Current Step** | R-016.2 DONE：LLM fallback/secret diagnostics 已加強；R-016 仍保留 Open（待 rerun 驗證 production） |
| **Mode** | CLOSED |
| **Latest Verified Commit** | `HEAD fix: 加強 R-016 LLM fallback diagnostics`（本地 commit，待主公確認 push） |
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
| **Current Step** | R-016.2 DONE：LLM fallback/secret diagnostics 已加強；R-016 仍保留 Open（待 rerun 驗證 production） |
| **Allowed Files** | 若主公要求繼續 R-016，可讀 `docs/RISK_REGISTRY.md`, `docs/P77_P84_CLOSEOUT_REPORT.md`, `docs/OPERATIONS_RUNBOOK.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`（append only）、`.github/workflows/daily_report.yml`, `analyzer/fallback_llm_client.py`, `analyzer/sentiment.py`, `analyzer/run_manifest.py`, `main.py`, `data/runs/**/run_manifest.json` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage unrelated untracked reports；不實刪歷史資料；不自動開 P85；不把 R-016.2 解讀成 production 已恢復；不重寫 P80 promotion/P83 security |
| **Exit Criteria** | R-016.2 已讓下一次 Actions 可直接顯示 secrets presence 與 manifest provider diagnostics；R-016 仍因 `SLO001` no production 與 `SLO003` degraded budget 保持 Open |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；下一步是推送 R-016.2 後重跑 Actions，檢查 `LLM Secret Preflight` 與 manifest `provider` 欄位，再跑 health + SLO |

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

R-016.2 已完成 LLM fallback/secret diagnostics：GitHub Actions 新增 `LLM Secret Preflight (Advisory)`；manifest 新增 `provider.quota_error`、`provider.openai_fallback_configured`、`provider.openai_fallback_used`；fallback client 會在 Gemini provider failure 但 OpenAI fallback 不可用時記錄不含 secret 值的警示。2026-05-19 workflow 已跑通但仍 `mode=showcase_forced`，R-016 仍 Open。

## Next Decision

R-016 尚未關閉。下一步是 push R-016.2 後重跑 Actions，從 `LLM Secret Preflight` 與 manifest `provider` 欄位確認 OpenAI fallback 是否配置/使用，再跑 `check_daily_report_health` 與 `slo_checker`；push 前仍需主公確認。
