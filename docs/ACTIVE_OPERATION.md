# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P95.1D（R-016 Decision / PENDING USER DECISION） |
| **Current Step** | Post-P95.1C cloud verification 已完成：workflow_dispatch run `26379118247` success，strict doctor success，auto-sync `d89c3b9` 產生 2026-05-25 production report；SLO `issues=[]`、doctor 無 blocking、health PASS、budget healthy、CCG008 無 current；下一步由主公裁決 R-016 close / downgrade / keep-open |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `d89c3b9`（post-P95.1C cloud auto-sync；local fast-forward complete） |
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
| **Current Phase** | P95.1D（FROZEN / PENDING USER DECISION） |
| **Current Step** | P95.1C retry complete + post-P95.1C cloud verification complete；2026-05-25 manifest is production/publishable, budget healthy, provider routing disabled, CCG008 residual only；等待 R-016 裁決 |
| **Allowed Files** | P95.1D cloud evidence documentation / commit / push；R-016 close/downgrade/keep-open 只可在主公裁決後更新 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / git-ignored enriched_posts；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不把 R-016 標記 Closed，除非主公明確裁決；不把 R-017 前台內容可信度問題混入 R-016；不 git push，除非主公明確確認 |
| **Exit Criteria** | P95.1D docs 已記錄 run `26379118247`、auto-sync `d89c3b9`、strict doctor success、2026-05-25 probes；local commit 完成後等主公確認 push |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_95_1_PLAN.md` §17；若本地 ahead 1，先等主公 push；若已同步 origin，下一步是請主公裁決 R-016 close / downgrade / keep-open |

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

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86-P94 已完成 model/schedule、report core contract、local deterministic analyzer、quality tier、budget ledger、cache/dedupe、enrichment queue、provider disabled slots、doctor/SLO reclassification。P95 已完成 post-P95 cloud 補證。P95.1A artifact dry-run 已完成；P95.1B apply replay 因 2026-05-24 cooldown active 安全轉成 `skipped_budget`；P95.1C cooldown retry 已於 2026-05-25 09:35 +08 成功補跑，2026-05-22 manifest 現為 `replay_status=completed`、`eligible_posts=2`、`enriched_posts=2`。Post-P95.1C cloud verification：workflow_dispatch run `26379118247` success，strict doctor success，auto-sync `d89c3b9` 產生 2026-05-25 production report；2026-05-25 health PASS，SLO `issues=[]`，doctor 無 blocking，budget `cooldown_active=false` / `llm_calls_used=3` / remaining=17，provider routing disabled，CCG008 僅 residual no_eligible。R-016 仍 Open，等待主公裁決 close / downgrade / keep-open。

## Window Switch Guidance

- 可以換視窗：P95.1D cloud verification 已完成，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_95_1_PLAN.md` §17 即可接手。
- 最佳換窗點：P95.1D cloud evidence docs commit / push 完成後換；若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要自行 close R-016。

## Next Decision

下一步是 commit P95.1D cloud evidence docs；push 仍需主公確認。之後請主公裁決 R-016 close / downgrade / keep-open；AI 的保守建議是 `Downgrade R-016 to monitoring`，再開 R-017 / P96+ 處理芽芽觀察室與舊文章等前台內容可信度問題。
