# ACTIVE OPERATION — R-018 RTK Token Savings Evaluation Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-018 RTK Token Savings Evaluation Program |
| **Current Phase** | P97（FROZEN / RTK Token Savings Evaluation Plan） |
| **Current Step** | 主公已核准 `P97 plan freeze`；只允許等待 freeze docs commit / push，不安裝 RTK、不執行 `rtk init`、不改全域規則；下一門是 `核准 P97 evaluation runtime` |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `ad9f761` 已推送；R-017 Open（Monitoring）至 2026-06-02 |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-26 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_97_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_96_PLAN.md`
5. 最近裁決 Phase 計畫：`docs/PHASE_95_1_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P97（FROZEN / RTK_EVALUATION_PLAN / RUNTIME_NOT_STARTED） |
| **Current Step** | P97 plan freeze 已核准；等待 freeze docs commit / push，接著請主公決定是否核准 evaluation runtime |
| **Allowed Files** | P97 plan scope：`docs/PHASE_97_PLAN.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md`、`TASK_HISTORY.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch artifact / raw queue / git-ignored enriched_posts；不安裝 RTK；不執行 `rtk init`；不改 PATH / shell profile / global AGENTS / CLAUDE / GEMINI；不啟用 telemetry；不改 GitHub Actions / Daily Monitor；不 git push，除非主公明確確認 |
| **Exit Criteria** | `docs/PHASE_97_PLAN.md` lint PASS；handoff / active / risk / history synchronized；R-018 Open；freeze docs committed |
| **Resume Rule** | 新視窗讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap、`docs/PHASE_97_PLAN.md`、`docs/RISK_REGISTRY.md` R-018；若 local ahead 是 P97 freeze docs，等待主公 push；若已推，下一步是 `核准 P97 evaluation runtime` |

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

P85-P95.1 已把 R-016 後端可靠性主線推進到 monitoring：post-P95.1C cloud verification run `26379118247` success，2026-05-25 health PASS，SLO `issues=[]`，doctor 無 blocking，budget `cooldown_active=false`，provider routing disabled，CCG008 僅 residual no_eligible。主公於 2026-05-25 核准 `R-016 downgrade to monitoring`；R-016 不標 Closed，保留 Open（Monitoring）至 2026-06-01。

P96/R-017 已完成 Website Content Trust runtime：cloud commit `0618717` content trust checker 全 PASS，主公於 2026-05-26 核准 `R-017 downgrade to monitoring`。R-017 不標 Closed，保留 Open（Monitoring）至 2026-06-02；若 latest report 再出現錯觀察室、`時間未知`、舊文污染或 checker FAIL，升回 active R-017。

P97/R-018 是新工具鏈戰線：RTK token-saving proxy 評估。P97 plan 已凍結；仍不安裝、不初始化、不全域部署。evaluation runtime 需主公另行核准。

## Window Switch Guidance

- 可以換視窗：P97 plan 已核准 freeze；若本地 ahead 1，下一窗可直接等主公 push P97 freeze docs。
- 最佳換窗點：P97 freeze docs commit / push 完成後，等待主公裁決是否啟動 evaluation runtime。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_97_PLAN.md`，先確認是否 push local P97 freeze docs commit。

## Next Decision

下一步是跑 P97 freeze docs checks，commit P97 freeze docs；push 仍需主公確認。推完後才進下一門：`核准 P97 evaluation runtime`。
