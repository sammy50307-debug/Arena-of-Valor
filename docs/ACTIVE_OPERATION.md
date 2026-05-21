# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P90（Budget Ledger / Cooldown / DRAFT） |
| **Current Step** | P89 runtime 已完成本地驗證；下一步建立/凍結 P90 計畫，未核准前不得改 budget runtime |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `HEAD`（P89 runtime commit 建立後即為最新本地真相；若本欄與 repo 狀態不一致，以 `git log -1 --oneline` 為準） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-21 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：尚待建立 `docs/PHASE_90_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_89_PLAN.md`
5. 已收官 Phase 計畫：`docs/PHASE_88_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P90（DRAFT） |
| **Current Step** | 建立/凍結 `docs/PHASE_90_PLAN.md`；未凍結且未核准前不可改 budget runtime |
| **Allowed Files** | DRAFT 階段只可動 `docs/PHASE_90_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`；runtime 核准後才可依 P90 計畫動 code |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不做 P91-P95 runtime；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P89 runtime 已完成：quality tier contract / promotion gate / metadata / health / doctor / tests；P90 plan 需先完成 17 層稽核與 M1/M2 後才能 runtime |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若要動 P90，先建立/凍結 `docs/PHASE_90_PLAN.md`，不得直接改 budget runtime |

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
py scripts\lint_phase_plan.py docs\PHASE_89_PLAN.md
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron 改成 UTC 08:30 / 台北 16:30。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015。P88 已 CLOSED：新增 deterministic local analyzer，LLM 429 / provider exception 會保留真實貼文並產生 `analysis_source=local_deterministic` baseline。P89 已 CLOSED：新增 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage` contract，promotion gate 改看 publishable quality tier；`production_local_only` 在 core/local baseline pass 時可 promotion，manual showcase / error fallback 不可 promotion。focused tests 57 passed、full pytest 240 passed；2026-05-20 health/doctor 無 blocking。R-016 仍 Open，因為 P90-P95 尚未完成。

## Next Decision

下一步是建立/凍結 P90 Budget Ledger / Cooldown 計畫。P90 未凍結且未經主公核准前，不得修改 budget runtime；R-016 仍 Open，不得關閉。
