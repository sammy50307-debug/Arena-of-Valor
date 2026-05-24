# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P95（R-016 Closeout Verification / FROZEN） |
| **Current Step** | P95 plan 已凍結；verification 尚未核准。下一步是 commit P95 plan，push 仍需主公明確確認 |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `1b919b3`（P94 doctor / SLO reclassification runtime 已 push） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-23 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_95_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_94_PLAN.md`
5. 已收官 Phase 計畫：`docs/PHASE_90_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P95（FROZEN） |
| **Current Step** | P95 R-016 Closeout Verification plan 已凍結；verification 尚未核准；等待 commit / push 確認或主公核准 P95 verification |
| **Allowed Files** | P95 plan closeout / commit / push；verification 只可在主公另核准後依 `docs/PHASE_95_PLAN.md` 執行 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P95 plan-only：`docs/PHASE_95_PLAN.md` 已建立，需通過 phase lint / handoff truth / governance doctor / diff check 並 commit；P95 verification 尚未核准 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_95_PLAN.md`；若本地 ahead 1，先等主公 push；若主公核准 P95 verification，才可跑 closeout probes / 裁決 R-016 |

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
py scripts\lint_phase_plan.py docs\PHASE_94_PLAN.md
py scripts\lint_phase_plan.py docs\PHASE_95_PLAN.md
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_slo_checker.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
py -m pytest -q
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron改成 UTC 08:30 / 台北 16:30。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015。P88 已 CLOSED：新增 deterministic local analyzer，LLM 429 / provider exception 會保留真實貼文並產生 `analysis_source=local_deterministic` baseline。P89 已 CLOSED：新增 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage` contract，promotion gate 改看 publishable quality tier；`production_local_only` 在 core/local baseline pass 時可 promotion，manual showcase / error fallback 不可 promotion。P90 已 CLOSED：新增 raw-free `analyzer/llm_budget.py`、budget/cooldown state、provider 呼叫前停損、429 cooldown 記帳、manifest `budget` snapshot、DOC017 / CCG006 advisory；focused tests 64 passed、full pytest 254 passed。P91 已 CLOSED：新增 source selection / dedupe / budget-aware Top-N / local-only merge / manifest selection snapshot / DOC018 / CCG007；focused tests 56 passed、full pytest 263 passed。2026-05-22 Actions 實跑已產生 P91 `selection` snapshot，`llm_calls` 從 pre-P91 的 28 降至 6，`duplicate_posts=7` 且 local-only 全由 duplicate_url 主導。P92 已 CLOSED：新增 artifact-backed `analyzer/enrichment_queue.py`、manual `scripts/enrichment_replay.py`、manifest raw-free `enrichment` snapshot、Actions short-retention artifact、DOC019 / CCG008；duplicate-only local-only 會正確 `no_eligible` no-op，不消耗 LLM；focused tests 66 passed、full pytest 274 passed。P93 已 CLOSED：新增 provider protocol、disabled-by-default provider router、shared budget guard、raw-free manifest `provider.routing`、doctor `DOC020`、cost governance `CCG009`、fake-provider / no-call / budget guard tests；focused tests 70 passed、full pytest 286 passed；Groq / Cloudflare / GitHub Models 目前只是 disabled slots，不得進 daily default。2026-05-23 AoV Daily Monitor run `26299079187` success，auto-sync commit `7da4605` 產生 production manifest/report；雲端 `provider.routing` 維持 `router_disabled_legacy_default`，沒有 DOC020 / `models: read`。P94 已 CLOSED：新增 current / historical / residual classification；SLO 五日窗 current clear，DOC018 / DOC019 residual advisory，CCG005 historical advisory；focused tests 32 passed、full pytest 288 passed。P95 已 FROZEN：只凍結 R-016 closeout verification plan；verification 尚未核准，R-016 仍 Open。

## Window Switch Guidance

- 可以換視窗：P95 plan 已凍結，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_95_PLAN.md` 即可接手。
- 最佳換窗點：P95 plan commit / push 完成後換；若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要直接跑 P95 verification，不要關 R-016，不要啟用 provider。

## Next Decision

下一步是 commit P95 plan；push 仍需主公明確確認。P95 verification 尚未核准；R-016 仍 Open，不得關閉。
