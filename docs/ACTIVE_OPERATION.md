# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P91（Cache / Dedupe / Top-N / DRAFT） |
| **Current Step** | P90 runtime 已完成本地收官；下一步只能建立/凍結 `docs/PHASE_91_PLAN.md`，不可直接改 cache/dedupe/top-N runtime |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `f2b6b47 docs: 凍結 P90 budget ledger cooldown plan`（P90 runtime 若已有本地 commit，則以 `git log -1 --oneline` 為準） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-21 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 最近收官 Phase 計畫：`docs/PHASE_90_PLAN.md`
4. 下一 Phase 計畫：`docs/PHASE_91_PLAN.md`（尚未建立）
5. 已收官 Phase 計畫：`docs/PHASE_89_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P91（DRAFT） |
| **Current Step** | 建立/凍結 `docs/PHASE_91_PLAN.md`；未凍結核准前不可改 cache/dedupe/top-N runtime |
| **Allowed Files** | DRAFT 階段只能檢視 P90 收官證據、更新狀態文件、建立 `docs/PHASE_91_PLAN.md`；P91 runtime 需主公另行核准 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不直接改 cache/dedupe/top-N runtime；不做 P92-P95 runtime；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P90 runtime 已完成本地收官；下一步 P91 plan 需過 17 層稽核、M1/M2、handoff truth、governance doctor、diff check |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_90_PLAN.md`；若要繼續 R-016 主線，先建立/凍結 P91 計畫，不得直接動 runtime |

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
py scripts\lint_phase_plan.py docs\PHASE_90_PLAN.md
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron改成 UTC 08:30 / 台北 16:30。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015。P88 已 CLOSED：新增 deterministic local analyzer，LLM 429 / provider exception 會保留真實貼文並產生 `analysis_source=local_deterministic` baseline。P89 已 CLOSED：新增 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage` contract，promotion gate 改看 publishable quality tier；`production_local_only` 在 core/local baseline pass 時可 promotion，manual showcase / error fallback 不可 promotion。P90 已 CLOSED：新增 raw-free `analyzer/llm_budget.py`、budget/cooldown state、provider 呼叫前停損、429 cooldown 記帳、manifest `budget` snapshot、DOC017 / CCG006 advisory；focused tests 64 passed、full pytest 254 passed。R-016 仍 Open，因為 P91-P95 尚未完成。

## Next Decision

下一步是建立/凍結 P91 Cache / Dedupe / Top-N 計畫。P91 runtime 未核准前不得修改 cache/dedupe/top-N 主鏈路；R-016 仍 Open，不得關閉。
