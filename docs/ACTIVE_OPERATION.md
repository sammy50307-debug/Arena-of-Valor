# ACTIVE OPERATION — R-019 Project Self-Optimization Flywheel Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-019 Project Self-Optimization Flywheel Program |
| **Current Phase** | P98（DRAFT / Project Flywheel Audit Plan） |
| **Current Step** | 主公已要求開 `P98 Project Flywheel Audit Plan`；只允許建立 plan / handoff / active / risk / history，不清理、不搬檔、不改 runtime、不動 GitHub Actions。下一門是 `核准 P98 plan freeze`。 |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `e883117` 已推送；P98 plan draft 本地同步中 |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-27 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_98_PLAN.md`
4. 最近收官 Phase 計畫：`docs/PHASE_97_PLAN.md`
5. 最近裁決 Phase 計畫：`docs/PHASE_96_PLAN.md`
6. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P98（DRAFT / PROJECT_FLYWHEEL_AUDIT_PLAN / RUNTIME_NOT_STARTED） |
| **Current Step** | P98 plan draft 建立中；等待 checks / commit / 主公確認 push，下一門是 `核准 P98 plan freeze` |
| **Allowed Files** | P98 plan scope：`docs/PHASE_98_PLAN.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md`、`TASK_HISTORY.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage scratch；不清理、不搬檔、不 rename、不改 `.gitignore`；不改 runtime code；不改 GitHub Actions / Pages；不導入 RTK 或新工具；不 git push，除非主公明確確認 |
| **Exit Criteria** | `docs/PHASE_98_PLAN.md` lint PASS；handoff / active / risk / history synchronized；R-019 Open；P98 plan draft committed |
| **Resume Rule** | 新視窗讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap、`docs/PHASE_98_PLAN.md`、`docs/RISK_REGISTRY.md` R-019；若 local ahead 是 P98 plan draft，等待主公 push；若已推，下一步是 `核准 P98 plan freeze` |

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
py scripts\lint_phase_plan.py docs\PHASE_97_PLAN.md
py scripts\lint_phase_plan.py docs\PHASE_98_PLAN.md
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_slo_checker.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
py -m pytest -q
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85-P95.1 已把 R-016 後端可靠性主線推進到 monitoring：post-P95.1C cloud verification run `26379118247` success，2026-05-25 health PASS，SLO `issues=[]`，doctor 無 blocking，budget `cooldown_active=false`，provider routing disabled，CCG008 僅 residual no_eligible。主公於 2026-05-25 核准 `R-016 downgrade to monitoring`；R-016 不標 Closed，保留 Open（Monitoring）至 2026-06-01。

P96/R-017 已完成 Website Content Trust runtime：cloud commit `0618717` content trust checker 全 PASS，主公於 2026-05-26 核准 `R-017 downgrade to monitoring`。R-017 不標 Closed，保留 Open（Monitoring）至 2026-06-02；若 latest report 再出現錯觀察室、`時間未知`、舊文污染或 checker FAIL，升回 active R-017。

P97/R-018 工具鏈戰線已完成 evaluation runtime。RTK `v0.42.0` Windows binary checksum PASS，僅在 `scratch/rtk_eval/bin/rtk.exe` 隔離執行；`Get-Command rtk` 前後皆 `NOT_FOUND`，未加入 PATH。`rtk init --codex --dry-run -v` would create `RTK.md` and patch `AGENTS.md` with `@RTK.md`，但 tracked diff before/after empty，未套用。Telemetry 顯示 `RTK_TELEMETRY_DISABLED=1 (blocked)`；runtime 建立的 local AppData `history.db` / `.hook_warn_last` 已清除。Baseline 顯示 pytest pass 有 83.0% savings，但 Git/search/read 類幾乎無收益或負收益；failure diagnostics 失敗，missing path / sentinel traceback 會被壓掉。裁決：不全域部署、不 project init、不 patch AOV instructions；若要繼續 RTK，另開 P99+ 或獨立 phase。

P98/R-019 是新專案飛輪戰線：Project Flywheel Audit Plan。P98 只建立 audit 計畫，目標是盤點 core/generated/governance/skill/scratch 分層、known issue memory gap、generated artifact hygiene、verification ladder 與下一批 P99+ 候選；P98 不清理、不搬檔、不改 runtime、不改 workflow。

## Window Switch Guidance

- 可以換視窗：P98 plan draft commit / push 後最穩；若本地 ahead 1，下一窗可先等主公 push。
- 最佳換窗點：P98 plan draft 已推送後，等待主公裁決是否核准 `P98 plan freeze`。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_98_PLAN.md`，先確認是否 push local P98 plan draft commit。

## Next Decision

下一步是跑 P98 plan draft checks，commit P98 plan draft；push 仍需主公確認。推完後由主公裁決是否核准 `P98 plan freeze`。
