# ACTIVE OPERATION — R-017 Website Content Trust Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-017 Website Content Trust Program |
| **Current Phase** | P96（DRAFT / Website Content Trust Plan / NOT_STARTED） |
| **Current Step** | R-016 已依主公核准降級為 monitoring：post-P95.1C cloud verification success，SLO `issues=[]`、doctor 無 blocking、health PASS、budget healthy、CCG008 無 current；下一步是開 P96 plan，處理芽芽觀察室 / 舊文章 / known issue guard |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `ee8bcba`（P95.1D cloud evidence docs 已 push；R-016 downgrade docs 尚待 commit） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-25 |

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
| **Current Phase** | P96（DRAFT / PLAN_REQUIRED / NOT_STARTED） |
| **Current Step** | R-016 downgrade to monitoring approved by 主公；monitoring window 2026-05-25～2026-06-01；下一步開 R-017 / P96 Website Content Trust plan |
| **Allowed Files** | R-016 downgrade documentation / commit / push；P96 只能先寫 plan，未核准不得動 runtime/template/data logic |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / git-ignored enriched_posts；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不重開 R-016，除非 monitoring 觸發條件命中；不未經計畫就修芽芽觀察室或舊文章；不 git push，除非主公明確確認 |
| **Exit Criteria** | R-016 risk registry status 已改為 `Open（Monitoring）`；handoff / active / phase plan / history 已同步 downgrade 裁決；local commit 完成後等主公確認 push |
| **Resume Rule** | 新視窗讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_95_1_PLAN.md` §18；若本地 ahead 1，先等主公 push；若已同步 origin，下一步是開 P96 Website Content Trust plan |

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

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86-P94 已完成 model/schedule、report core contract、local deterministic analyzer、quality tier、budget ledger、cache/dedupe、enrichment queue、provider disabled slots、doctor/SLO reclassification。P95 已完成 post-P95 cloud 補證。P95.1A artifact dry-run 已完成；P95.1B apply replay 因 2026-05-24 cooldown active 安全轉成 `skipped_budget`；P95.1C cooldown retry 已於 2026-05-25 09:35 +08 成功補跑，2026-05-22 manifest 現為 `replay_status=completed`、`eligible_posts=2`、`enriched_posts=2`。Post-P95.1C cloud verification：workflow_dispatch run `26379118247` success，strict doctor success，auto-sync `d89c3b9` 產生 2026-05-25 production report；2026-05-25 health PASS，SLO `issues=[]`，doctor 無 blocking，budget `cooldown_active=false` / `llm_calls_used=3` / remaining=17，provider routing disabled，CCG008 僅 residual no_eligible。主公於 2026-05-25 核准 `R-016 downgrade to monitoring`；R-016 不標 Closed，保留 Open（Monitoring）至 2026-06-01，若 production SLO / doctor / CCG008 current / landing stale / provider routing 異常復發則升回 active。

## Window Switch Guidance

- 可以換視窗：R-016 已降級為 monitoring；下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_95_1_PLAN.md` §18 即可接手。
- 最佳換窗點：R-016 downgrade docs commit / push 完成後換；若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要重開 R-016，除非 monitoring 觸發條件命中。

## Next Decision

下一步是 commit R-016 downgrade docs；push 仍需主公確認。之後開 R-017 / P96+ Website Content Trust plan，處理芽芽觀察室與舊文章等前台內容可信度問題；不得在沒有 P96 plan 的狀態下直接改 template / report / data logic。
