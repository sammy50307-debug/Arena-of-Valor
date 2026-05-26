# ACTIVE OPERATION — R-017 Website Content Trust Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-017 Website Content Trust Program |
| **Current Phase** | P96（IN_PROGRESS / Website Content Trust Runtime） |
| **Current Step** | P96.0 Evidence Inventory 完成；content trust minimal fix / guard 已 commit 到 local HEAD，待 push 後重新產生報告或手動 dispatch 驗證 |
| **Mode** | IN_PROGRESS |
| **Latest Verified Commit** | local `HEAD`（P96 runtime guard，尚未 push；以 `git log -1 --oneline` 為準）；origin 最新已推送為 `61f03a1`（P96 plan freeze） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-26 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_96_PLAN.md`
4. 最近裁決 Phase 計畫：`docs/PHASE_95_1_PLAN.md`
5. 最近收官 Phase 計畫：`docs/PHASE_95_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P96（IN_PROGRESS / CONTENT_TRUST_RUNTIME） |
| **Current Step** | P96.0 evidence 完成；minimal fix、known issue memory、checker/tests 已 commit 到 local HEAD；待 push / regenerated report verification |
| **Allowed Files** | P96 runtime scope：`reporter/generator.py`、`reporter/templates/report.html`、`analyzer/top5_picker.py`、content trust checker/tests/docs/config、handoff/active/history |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / git-ignored enriched_posts；不新增 provider key / PAT / Cloudflare token / Groq key；不加 GitHub Actions `models: read`；不接 Groq / Cloudflare / GitHub Models 到 daily default；不改 workflow；不降低 SLO001/SLO002/SLO003 blocking 門檻；不重開 R-016，除非 monitoring 觸發條件命中；不未經計畫就修芽芽觀察室或舊文章；不 git push，除非主公明確確認 |
| **Exit Criteria** | focused tests pass；content trust checker produces fail-before on old report and pass-after on regenerated/new report；handoff / active / history synchronized; runtime commit pushed |
| **Resume Rule** | 新視窗讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap、`docs/PHASE_96_PLAN.md`、`docs/PHASE_96_EVIDENCE_INVENTORY.md`；若本地 ahead 1 是 P96 runtime guard，先等主公 push；若已 pushed，下一步是重新產生報告或手動 dispatch verification |

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
py scripts\lint_phase_plan.py docs\PHASE_96_PLAN.md
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_slo_checker.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
py -m pytest -q
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85-P95.1 已把 R-016 後端可靠性主線推進到 monitoring：post-P95.1C cloud verification run `26379118247` success，2026-05-25 health PASS，SLO `issues=[]`，doctor 無 blocking，budget `cooldown_active=false`，provider routing disabled，CCG008 僅 residual no_eligible。主公於 2026-05-25 核准 `R-016 downgrade to monitoring`；R-016 不標 Closed，保留 Open（Monitoring）至 2026-06-01。P96/R-017 是新戰線：Website Content Trust，處理芽芽觀察室錯標、舊文章、known issue guard；不得混入 R-016。

## Window Switch Guidance

- 可以換視窗：P96 runtime guard 已 commit；若本地 ahead 1，下一窗可直接等主公 push。
- 最佳換窗點：P96 runtime commit / push 完成，且 latest report 重新產生驗證後換。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_96_EVIDENCE_INVENTORY.md`，先確認是否 push local runtime commit。

## Next Decision

下一步是完成 P96 runtime commit / push，然後重新產生 report 或手動 dispatch AoV Daily Monitor，確認 `scripts/check_report_content_trust.py --repo-root . --date <latest>` 通過。
