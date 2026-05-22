# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P93（Provider Abstraction / Disabled-by-default Free Provider Slots / FROZEN） |
| **Current Step** | P93 plan 已凍結；若本地已有 FROZEN commit，下一步是等主公確認是否 push；P93 runtime 需主公另行核准 |
| **Mode** | FROZEN |
| **Latest Verified Commit** | P93 plan freeze 文件已完成本地驗證；commit / push 狀態以 `git log -1 --oneline` 與 `git status -sb` 為準 |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-22 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_93_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_92_PLAN.md`
5. 已收官 Phase 計畫：`docs/PHASE_90_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P93（FROZEN） |
| **Current Step** | P93 provider abstraction plan 已凍結；若本地已有 FROZEN commit，等待主公確認是否 push；P93 runtime 需主公另行核准 |
| **Allowed Files** | P93 FROZEN 文件 closeout / commit / push；P93 runtime 需主公另行核准後才可動 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不做 P93 provider abstraction runtime，除非主公明確核准；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P93 plan 已凍結，明列 disabled-by-default provider slots、kill switch、budget guard、secret/privacy、fake-provider tests、manual-only smoke gate；plan lint / diff / doctor / handoff truth 通過；R-016 仍 Open |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_93_PLAN.md`；若本地 ahead 1，先等主公 push；若主公核准 runtime，依 P93 FROZEN 計畫開工 |

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
py scripts\lint_phase_plan.py docs\PHASE_93_PLAN.md
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_enrichment_queue.py tests\test_enrichment_replay.py tests\test_source_selection.py tests\test_run_manifest.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
py -m pytest -q
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron改成 UTC 08:30 / 台北 16:30。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015。P88 已 CLOSED：新增 deterministic local analyzer，LLM 429 / provider exception 會保留真實貼文並產生 `analysis_source=local_deterministic` baseline。P89 已 CLOSED：新增 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage` contract，promotion gate 改看 publishable quality tier；`production_local_only` 在 core/local baseline pass 時可 promotion，manual showcase / error fallback 不可 promotion。P90 已 CLOSED：新增 raw-free `analyzer/llm_budget.py`、budget/cooldown state、provider 呼叫前停損、429 cooldown 記帳、manifest `budget` snapshot、DOC017 / CCG006 advisory；focused tests 64 passed、full pytest 254 passed。P91 已 CLOSED：新增 source selection / dedupe / budget-aware Top-N / local-only merge / manifest selection snapshot / DOC018 / CCG007；focused tests 56 passed、full pytest 263 passed。2026-05-22 Actions 實跑已產生 P91 `selection` snapshot，`llm_calls` 從 pre-P91 的 28 降至 6，`duplicate_posts=7` 且 local-only 全由 duplicate_url 主導。P92 已 CLOSED：新增 artifact-backed `analyzer/enrichment_queue.py`、manual `scripts/enrichment_replay.py`、manifest raw-free `enrichment` snapshot、Actions short-retention artifact、DOC019 / CCG008；duplicate-only local-only 會正確 `no_eligible` no-op，不消耗 LLM；focused tests 66 passed、full pytest 274 passed。P93 已 FROZEN：provider abstraction 只定義 disabled-by-default slots、kill switch、budget guard、secret/privacy、fake-provider tests、manual-only smoke gate；Groq / Cloudflare / GitHub Models 目前只是候選，不得進 daily default。R-016 仍 Open，因為 P93 runtime 與 P94-P95 尚未完成。

## Window Switch Guidance

- 可以換視窗：P93 plan 已凍結，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_93_PLAN.md` 即可接手。
- 最佳換窗點：P93 FROZEN commit 完成後換；若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要重修 P91/P92，不要直接啟用 provider。

## Next Decision

下一步是確認 P93 FROZEN commit 是否需要 push；push 仍需主公明確確認。若主公另行核准 P93 runtime，才可依 `docs/PHASE_93_PLAN.md` 動工。R-016 仍 Open，不得關閉。
