# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P95.1D（R-016 Decision / PENDING USER DECISION） |
| **Current Step** | P95.1C cooldown retry 已完成且 local commit 已建立：2026-05-22 enrichment `eligible=2 enriched=2 replay_status=completed`，CCG008 current blocker 已清除；下一步是等主公確認 push，然後裁決 R-016 close / downgrade / keep-open |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `05be57a`（latest pushed；P95.1C local commit 已建立，若 `git status -sb` 顯示 ahead 1 代表尚待 push） |
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
| **Current Step** | P95.1C retry complete；2026-05-22 manifest now `replay_status=completed` / `eligible_posts=2` / `enriched_posts=2`；local commit 已建立；等待 push 與 R-016 裁決 |
| **Allowed Files** | P95.1C documentation closeout / commit / push；P95.1D 只可在主公裁決後更新 R-016 close / downgrade / keep-open |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / git-ignored enriched_posts；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不把 R-016 標記 Closed，除非主公明確裁決；不 git push，除非主公明確確認 |
| **Exit Criteria** | P95.1C docs 已記錄 completed manifest delta、probes、tests；phase lint / handoff truth / governance doctor / diff check 已通過；local commit 已完成，等主公確認 push |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_95_1_PLAN.md` §16；若本地 ahead 1，先等主公 push；若已同步 origin，下一步是請主公裁決 R-016 close / downgrade / keep-open，或先跑 post-2026-05-25 Daily Monitor 補雲端證據 |

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

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86-P94 已完成 model/schedule、report core contract、local deterministic analyzer、quality tier、budget ledger、cache/dedupe、enrichment queue、provider disabled slots、doctor/SLO reclassification。P95 已完成 post-P95 cloud 補證：run `26356870400` success，auto-sync `65b9f92` 產生 2026-05-24 production report；5/24 SLO `issues=[]`、doctor 無 blocking、landing PASS、provider routing disabled。P95.1A artifact dry-run 已完成：正確 artifact 是 run `26285001843` / artifact `7159368993`，queue valid、eligible=2，dry-run output `eligible=2 will_replay=2 remaining_budget=15 status=dry_run`。P95.1B apply replay 因 2026-05-24 cooldown active 安全轉成 `skipped_budget`。P95.1C cooldown retry 已於 2026-05-25 09:35 +08 成功補跑，2026-05-22 manifest 現為 `replay_status=completed`、`eligible_posts=2`、`enriched_posts=2`；cost governance 三日窗已無 CCG008 current，僅保留 2026-05-23/24 no_eligible residual。R-016 仍 Open，等待主公裁決 close / downgrade / keep-open。

## Window Switch Guidance

- 可以換視窗：P95.1C 已完成補跑，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_95_1_PLAN.md` §16 即可接手。
- 最佳換窗點：P95.1C docs commit / push 完成後換；若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要自行 close R-016。

## Next Decision

下一步是等主公確認 push P95.1C local commit。之後請主公裁決 R-016 close / downgrade / keep-open；AI 建議若要「完美收尾」，可先 push 後手動 dispatch 一次 post-2026-05-25 Daily Monitor 補雲端證據。
