# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P95.1B（Pending Closure Apply / PENDING APPROVAL） |
| **Current Step** | P95.1A artifact dry-run 已完成：2026-05-22 queue valid，eligible=2，will_replay=2，remaining_budget=15；下一步 P95.1B apply replay 尚未核准 |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `a63c7a0`（P95.1 plan freeze 已 push；P95.1A docs 尚待 commit） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-24 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_95_1_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_95_PLAN.md`
5. 已收官 Phase 計畫：`docs/PHASE_90_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P95.1B（FROZEN / PENDING APPROVAL） |
| **Current Step** | P95.1A artifact dry-run complete；2026-05-22 queue valid、eligible=2、will_replay=2、remaining_budget=15；等待 commit / push 或主公核准 P95.1B apply replay |
| **Allowed Files** | P95.1A documentation closeout / commit / push；P95.1B 只可在主公另核准後 apply replay |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / enriched_posts；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不 apply replay；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P95.1A docs 已記錄 correct artifact id、schema/count、dry-run output、P95.1B decision；需通過 phase lint / handoff truth / governance doctor / diff check 並 commit |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_95_1_PLAN.md` §14；若本地 ahead 1，先等主公 push；若主公核准 P95.1B apply replay，才可執行 `--apply` |

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
py scripts\lint_phase_plan.py docs\PHASE_95_1_PLAN.md
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_slo_checker.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
py -m pytest -q
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86 已 CLOSED：model list 改成 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，daily cron改成 UTC 08:30 / 台北 16:30。P87 已 CLOSED：manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015。P88 已 CLOSED：新增 deterministic local analyzer，LLM 429 / provider exception 會保留真實貼文並產生 `analysis_source=local_deterministic` baseline。P89 已 CLOSED：新增 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage` contract，promotion gate 改看 publishable quality tier；`production_local_only` 在 core/local baseline pass 時可 promotion，manual showcase / error fallback 不可 promotion。P90 已 CLOSED：新增 raw-free `analyzer/llm_budget.py`、budget/cooldown state、provider 呼叫前停損、429 cooldown 記帳、manifest `budget` snapshot、DOC017 / CCG006 advisory；focused tests 64 passed、full pytest 254 passed。P91 已 CLOSED：新增 source selection / dedupe / Top-N；2026-05-22 Actions 實跑已產生 selection snapshot。P92 已 CLOSED：新增 artifact-backed enrichment queue、manual `scripts/enrichment_replay.py`、manifest raw-free `enrichment` snapshot、DOC019 / CCG008。P93 已 CLOSED：provider routing disabled-by-default。P94 已 CLOSED：current / historical / residual classification。P95 已完成 post-P95 cloud 補證：run `26356870400` success，auto-sync `65b9f92` 產生 2026-05-24 production report；5/24 SLO `issues=[]`、doctor 無 blocking、landing PASS、provider routing disabled、5/24 LLM calls=5。P95.1A artifact dry-run 已完成：正確 artifact 是 run `26285001843` / artifact `7159368993`，zip entry `2026-05-22/enrichment_queue.json`；queue valid、eligible=2、skipped=8；dry-run output `eligible=2 will_replay=2 remaining_budget=15 status=dry_run`。下一步是 P95.1B apply replay，尚未核准。

## Window Switch Guidance

- 可以換視窗：P95.1A dry-run 已完成，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_95_1_PLAN.md` §14 即可接手。
- 最佳換窗點：P95.1A docs commit / push 完成後換；若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要直接 apply replay。

## Next Decision

下一步是 commit P95.1A dry-run docs；push 仍需主公明確確認。P95.1B apply replay 尚未核准；R-016 維持 Open，不能 close。
