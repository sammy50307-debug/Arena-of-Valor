# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P87（Report Core Contract / DRAFT_PENDING_PLAN） |
| **Current Step** | P86 CLOSED；下一步建立/凍結 `docs/PHASE_87_PLAN.md`，不可直接改 runtime code |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `HEAD`（P86 closeout docs，本地 commit 待 push；P86 production evidence commit = `100460f`；若本欄與 repo 狀態不一致，以 `git log -1 --oneline` 為準） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-20 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 總戰略計畫：`docs/PHASE_85_PLAN.md` 的 P87 roadmap
4. 已收官 Phase 計畫：`docs/PHASE_86_PLAN.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P87（DRAFT_PENDING_PLAN） |
| **Current Step** | P86 CLOSED；建立/凍結 `docs/PHASE_87_PLAN.md` |
| **Allowed Files** | `docs/PHASE_87_PLAN.md`, `docs/PHASE_85_PLAN.md`, `docs/PHASE_86_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`；DRAFT 階段只可做 P87 plan / handoff / risk / history |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不改 runtime code；不做 P88-P95；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P87 plan 需完成 17 層稽核、M1/M1.5/M2、Entry/Exit Criteria、影響檔案、Forbidden Work，並通過 `lint_phase_plan.py` 後才可 FROZEN |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若主公說「凍結 P87」或「開始規劃 P87」，只建立/更新 `docs/PHASE_87_PLAN.md`，不得改 runtime code |

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
if (Test-Path docs\PHASE_87_PLAN.md) { py scripts/lint_phase_plan.py docs\PHASE_87_PLAN.md }
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron 改成 UTC 08:30 / 台北 16:30，focused tests / full pytest / py38 import 通過。遠端 commit `100460f` 由 GitHub Actions 產出 `mode=production` report，manifest 顯示 `publish_eligible=true`、`quota_error=false`、`llm_calls=20`；health check production PASS，system doctor 無 blocking、僅 DOC007 advisory。R-016 仍 Open，因為 P87-P95 尚未完成。

## Next Decision

下一步是建立/凍結 `docs/PHASE_87_PLAN.md`。P87 目標是 Report Core Contract：定義不靠 LLM 也能 production 的最低真實報告標準；P87 plan 凍結前不得改 runtime code。
