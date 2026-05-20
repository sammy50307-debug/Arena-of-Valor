# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P86（Gemini Model & Schedule Modernization / VERIFYING） |
| **Current Step** | P86.3 VERIFYING：Gemini 3.1 / 3.5 model list、UTC 08:30 cron、focused tests 已本地完成；等待 push 後 GitHub Actions 實證 |
| **Mode** | VERIFYING |
| **Latest Verified Commit** | `HEAD`（P86 本地實作 commit；若本欄與 repo 狀態不一致，以 `git log -1 --oneline` 為準） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-20 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_86_PLAN.md`
4. 總戰略計畫：`docs/PHASE_85_PLAN.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P86（VERIFYING） |
| **Current Step** | P86.3 VERIFYING：等待 push 與 GitHub Actions `AoV Daily Monitor` 實跑證據 |
| **Allowed Files** | `analyzer/gemini_client.py`, `.github/workflows/daily_report.yml`, `tests/test_429_retry.py`, `tests/test_gemini_model_policy.py`, `tests/test_daily_report_schedule.py`, `docs/PHASE_86_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`；VERIFYING 只允許修 P86 同範圍回歸 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不做 P87-P95；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | 本地 focused tests / py38 import 已通過；仍需 push 後 GitHub Actions `AoV Daily Monitor` 成功，才能把 P86 關閉或轉下一 Phase |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若 P86 commit 已 push，先跑/檢查 GitHub Actions；若 CI 失敗，只修 P86 同範圍問題 |

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
py scripts/lint_phase_plan.py docs/PHASE_86_PLAN.md
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已完成官方查證：Gemini rate limit 以 RPM/TPM/RPD 評估、套在 project 而非 API key，RPD 在 Pacific midnight reset；`gemini-2.0-flash` 與 `gemini-2.0-flash-lite` 官方 shutdown date 為 2026-06-01。P86.0a 於 2026-05-20 重新查證 Google 模型頁與 deprecations，將 P86 實作目標從 2.5 路線修正為 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`。P86.1/P86.2 本地實作已完成：model list 改成 Gemini 3.1/3.5，daily cron 改成 UTC 08:30 / 台北 16:30，focused tests 與 py38 import 已通過。P86 仍需 push 後 GitHub Actions 實跑證據，不得視為 R-016 已恢復 production。

## Next Decision

下一步是推 P86 implementation commit，然後手動或等待排程跑 GitHub Actions `AoV Daily Monitor`，用遠端實跑結果驗證 Gemini 3.1 / 3.5 endpoint 與現有 JSON pipeline 相容。
