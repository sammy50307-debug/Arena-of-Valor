# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P95.1C（Cooldown Retry / PENDING APPROVAL） |
| **Current Step** | P95.1B apply replay 已執行且 docs local commit 已準備；budget guard 安全擋下 LLM replay，2026-05-22 enrichment 已由 pending 轉 skipped_budget；若 `main ahead 1` 則先等主公 push，若已同步 origin 則等 2026-05-25 00:20:27 +08 後 retry apply |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `b836bc0`（本段撰寫時 latest pushed；若 `git status -sb` 顯示 ahead 1，代表 P95.1B local commit 尚待 push） |
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
| **Current Phase** | P95.1C（FROZEN / PENDING APPROVAL） |
| **Current Step** | P95.1B apply replay complete with budget skip；2026-05-22 manifest now `replay_status=skipped_budget` / `budget_reason=cooldown_active`；local commit 已完成，等待 push 或主公核准 cooldown 後 retry |
| **Allowed Files** | P95.1B documentation closeout / commit / push；P95.1C retry 只可在 cooldown 結束後、主公核准後執行 |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / enriched_posts；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不 bypass budget guard；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P95.1B docs 已記錄 skipped_budget manifest delta、cooldown_until、probes；phase lint / handoff truth / governance doctor / diff check 已通過；local commit 已完成，push 待確認 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap 與 `docs/PHASE_95_1_PLAN.md` §15；若本地 ahead 1，先等主公 push；若主公核准 P95.1C retry，需確認已過 `2026-05-25 00:20:27 +08` |

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

P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。P86-P94 已完成 model/schedule、report core contract、local deterministic analyzer、quality tier、budget ledger、cache/dedupe、enrichment queue、provider disabled slots、doctor/SLO reclassification。P95 已完成 post-P95 cloud 補證：run `26356870400` success，auto-sync `65b9f92` 產生 2026-05-24 production report；5/24 SLO `issues=[]`、doctor 無 blocking、landing PASS、provider routing disabled。P95.1A artifact dry-run 已完成：正確 artifact 是 run `26285001843` / artifact `7159368993`，queue valid、eligible=2，dry-run output `eligible=2 will_replay=2 remaining_budget=15 status=dry_run`。P95.1B apply replay 已執行，但 budget guard 因 2026-05-24 cooldown active 擋下 LLM replay；2026-05-22 manifest 已由 `pending` 轉 `skipped_budget`，budget_reason=`cooldown_active`，cooldown_until=`2026-05-25 00:20:27 +08`。R-016 仍 Open。

## Window Switch Guidance

- 可以換視窗：P95.1B apply 結果已明確，下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_95_1_PLAN.md` §15 即可接手。
- 最佳換窗點：P95.1B local commit 已完成；push 完成後換最乾淨。若本地 ahead，下一窗可直接等主公確認 push。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部即可；不要繞過 budget guard。

## Next Decision

下一步是等待主公確認 push P95.1B local commit。P95.1C cooldown retry 需等 2026-05-25 00:20:27 +08 後另行執行；R-016 維持 Open。
