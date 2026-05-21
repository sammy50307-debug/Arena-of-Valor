# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P92（Enrichment Replay / Local-only 補深讀 / FROZEN） |
| **Current Step** | P92 plan 已凍結；等待主公另行核准 P92 runtime 動工，未核准前不得改 `main.py` / `analyzer/` / `scripts` runtime |
| **Mode** | FROZEN |
| **Latest Verified Commit** | Plan freeze in progress：`docs/PHASE_92_PLAN.md` 已通過 lint；handoff docs 以 `git log -1 --oneline` 為準 |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-22 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_92_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_91_PLAN.md`
5. 已收官 Phase 計畫：`docs/PHASE_90_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P92（FROZEN） |
| **Current Step** | P92 enrichment replay / local-only 補深讀計畫已凍結；等待主公核准 P92 runtime |
| **Allowed Files** | P92 plan 已封存；未核准 runtime 前只能補 closeout / handoff / risk / history 文件，不得改 `main.py` / `analyzer/` / `scripts/` runtime |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不改 P91 已封存 runtime；不直接做 P92 replay/backfill runtime；不做 P93 provider abstraction；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P92 plan 已完成 artifact-backed enrichment queue / budget-aware replay / duplicate no-op / raw-free manifest 設計，並通過 `lint_phase_plan.py`；R-016 仍 Open |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_92_PLAN.md`；下一步只可等待或請示 P92 runtime 核准，除非主公明確核准 P92 runtime |

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
py scripts\lint_phase_plan.py docs\PHASE_91_PLAN.md
py scripts\lint_phase_plan.py docs\PHASE_92_PLAN.md
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_source_selection.py tests\test_run_manifest.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron改成 UTC 08:30 / 台北 16:30。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015。P88 已 CLOSED：新增 deterministic local analyzer，LLM 429 / provider exception 會保留真實貼文並產生 `analysis_source=local_deterministic` baseline。P89 已 CLOSED：新增 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage` contract，promotion gate 改看 publishable quality tier；`production_local_only` 在 core/local baseline pass 時可 promotion，manual showcase / error fallback 不可 promotion。P90 已 CLOSED：新增 raw-free `analyzer/llm_budget.py`、budget/cooldown state、provider 呼叫前停損、429 cooldown 記帳、manifest `budget` snapshot、DOC017 / CCG006 advisory；focused tests 64 passed、full pytest 254 passed。P91 已 CLOSED：新增 source selection / dedupe / budget-aware Top-N / local-only merge / manifest selection snapshot / DOC018 / CCG007；focused tests 56 passed、full pytest 263 passed。2026-05-22 Actions 實跑已產生 P91 `selection` snapshot，`llm_calls` 從 pre-P91 的 28 降至 6，`duplicate_posts=7` 且 local-only 全由 duplicate_url 主導。P92 plan 已 FROZEN：採 artifact-backed enrichment queue + budget-aware replay 設計，duplicate local-only 預設 no-op；runtime 尚未核准。R-016 仍 Open，因為 P92-P95 尚未完成。

## Window Switch Guidance

- 可以換視窗：P92 plan 已凍結，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_92_PLAN.md` 即可接手。
- 最佳換窗點：P92 plan freeze commit 完成後換；下一窗可直接等主公核准 runtime 或做只讀設計審查。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要重修 P91，也不要直接動 P92 runtime。

## Next Decision

下一步是等待主公核准 P92 runtime 動工。未核准前不得修改 `main.py` / `analyzer/` / `scripts/` runtime；R-016 仍 Open，不得關閉。
