# ACTIVE OPERATION — Daily Monitoring Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P80（Promotion / Atomic Write） |
| **Current Step** | P80.1 已落地：candidate/promote 分離 + pre-promotion gate，待 CI 實跑驗證 |
| **Mode** | IN_PROGRESS |
| **Latest Verified Commit** | `dccee5b fix: 修正 news_history_indexer 在 Python 3.8 型別註解崩潰` |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-16 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_80_PLAN.md`
4. 總戰役計畫：`docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P80（IN_PROGRESS） |
| **Current Step** | 驗證 P80.1 在 CI 的 promote / non-promote 行為，補收官證據 |
| **Allowed Files** | `main.py`, `reporter/generator.py`, `scripts/check_daily_report_health.py`, `tests/test_daily_report_health.py`, `tests/test_report_generator_landing.py`, `docs/PHASE_80_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage untracked reports；不跳做 P80/P82+ 大改 |
| **Exit Criteria** | 至少取得 1 次 CI 實跑證據，確認 P80.1 行為與計畫一致後再評估收官 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap，再依 `docs/PHASE_79_PLAN.md` 接續 |

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

## Required Verification For P76.1

```powershell
git status -sb
git diff --check
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Next Decision

P80 已開始動工並落地第一版（P80.1）。當前重點是補齊 CI 實跑證據，確認 publish/promote 行為符合預期。
