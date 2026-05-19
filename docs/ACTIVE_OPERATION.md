# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P86（Gemini Model & Schedule Modernization / FROZEN） |
| **Current Step** | P86 FROZEN：Gemini model / schedule 詳細計畫已凍結；等待主公核准 P86 才能改程式碼 |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `HEAD docs: 凍結 P86 gemini model schedule plan`（本地 commit，待主公確認 push） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-19 |

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
| **Current Phase** | P86（FROZEN） |
| **Current Step** | P86 FROZEN：等待主公核准 P86 APPROVED |
| **Allowed Files** | FROZEN 狀態只允許讀 `docs/PHASE_86_PLAN.md`, `docs/PHASE_85_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`；若要修正 P86 文件真相，可改 docs/handoff/history，但不可改 runtime code |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；未核准前不改 `.github/workflows/daily_report.yml`；未核准前不改 `analyzer/gemini_client.py`；不把 R-016 標記 Closed |
| **Exit Criteria** | P86 只凍結細項計畫，不關閉 R-016；P86 APPROVED 後才可移除 deprecated Gemini 2.0 models 與調整 cron |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若主公說「開始」或「核准」，才依 P86 plan 動 `analyzer/gemini_client.py` 與 `.github/workflows/daily_report.yml` |

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

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已完成官方查證：Gemini rate limit 以 RPM/TPM/RPD 評估、套在 project 而非 API key，RPD 在 Pacific midnight reset；`gemini-2.0-flash` 與 `gemini-2.0-flash-lite` 官方 shutdown date 為 2026-06-01。P86 仍只是 FROZEN 計畫，不是 runtime 修復。

## Next Decision

下一步是主公是否核准 P86 APPROVED。核准後才可改 `analyzer/gemini_client.py` 與 `.github/workflows/daily_report.yml`，實作 model list 現代化與 cron 調整。
