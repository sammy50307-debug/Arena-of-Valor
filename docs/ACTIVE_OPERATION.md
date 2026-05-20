# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P88（Deterministic Local Analyzer / FROZEN） |
| **Current Step** | P88 計畫已凍結；等待主公核准後才能改 runtime code |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `HEAD`（P88 plan freeze 本地 commit 待 push；P87 runtime commit = `4f86488`；若本欄與 repo 狀態不一致，以 `git log -1 --oneline` 為準） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-20 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_88_PLAN.md`
4. 已收官 Phase 計畫：`docs/PHASE_86_PLAN.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P88（FROZEN） |
| **Current Step** | 等待主公核准 P88 runtime 動工 |
| **Allowed Files** | FROZEN 階段只可動 `docs/PHASE_88_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`；runtime 核准後才可依 `docs/PHASE_88_PLAN.md` 動 `analyzer/local_analyzer.py`, `analyzer/sentiment.py`, tests，必要時最小修改 `main.py` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不改 quality tier / promotion gate；不改 LLM budget ledger；不做 P89-P95；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P88 plan 已完成 17 層稽核、M1/M1.5/M2、Entry/Exit Criteria、影響檔案、Forbidden Work；runtime 收官需依 `docs/PHASE_88_PLAN.md` 全部 Exit Criteria 驗證 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_88_PLAN.md`；若主公說「核准 P88」或「開始 P88 runtime」，才可依計畫動工 |

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
py scripts\lint_phase_plan.py docs\PHASE_88_PLAN.md
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron 改成 UTC 08:30 / 台北 16:30，focused tests / full pytest / py38 import 通過。遠端 commit `100460f` 由 GitHub Actions 產出 `mode=production` report。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015；focused tests 41 passed、full pytest 221 passed。P88 plan 已凍結為 Deterministic Local Analyzer：未來 runtime 會建立不打 LLM 的本地 baseline analysis，但不改 quality tier / promotion gate。R-016 仍 Open，因為 P88-P95 尚未完成。

## Next Decision

下一步是等待主公核准 P88 runtime 動工。P88 目標是 Deterministic Local Analyzer：建立不打外部 LLM 的本地情緒、關鍵字、英雄、平台、事件初判；FROZEN 狀態下不得改 runtime code。
