# ACTIVE OPERATION — R-018 RTK Token Savings Evaluation Program（P97 CLOSED / INSTALL BLOCKED）

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-018 RTK Token Savings Evaluation Program |
| **Current Phase** | P97（CLOSED / RTK Evaluation Runtime Complete / INSTALL BLOCKED） |
| **Current Step** | P97 runtime 已完成；RTK 不全域部署、不 project init、不 patch `AGENTS.md`。下一步若主公要繼續 RTK，只能另開 P98 project-local/manual-prefix pilot；否則回到 R-016/R-017 monitoring。 |
| **Mode** | CLOSED |
| **Latest Verified Commit** | `2d45f28` 已推送；P97 runtime closeout docs 本地同步中 |
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
| **Current Phase** | P97（CLOSED / RTK_EVALUATION_RUNTIME_COMPLETE / INSTALL_BLOCKED） |
| **Current Step** | P97 runtime evidence 已完成；等待 closeout docs checks / commit / 主公確認 push |
| **Allowed Files** | P97 closeout scope：`docs/PHASE_97_PLAN.md`、`docs/PHASE_97_RTK_EVALUATION.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md`、`TASK_HISTORY.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不 stage `scratch/rtk_eval/`；不安裝 RTK；不執行非 dry-run `rtk init`；不改 PATH / shell profile / global AGENTS / CLAUDE / GEMINI；不啟用 telemetry；不改 GitHub Actions / Daily Monitor；不 git push，除非主公明確確認 |
| **Exit Criteria** | P97 runtime evidence doc exists；handoff / active / risk / history synchronized；R-018 Open（install blocked）；governance checks PASS；closeout docs committed |
| **Resume Rule** | 新視窗讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap、`docs/PHASE_97_RTK_EVALUATION.md`、`docs/RISK_REGISTRY.md` R-018；若 local ahead 是 P97 runtime closeout docs，等待主公 push；若已推，下一步由主公裁決是否開 P98 project-local/manual-prefix pilot |

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
py scripts\check_handoff_truth.py --repo-root .
py scripts\governance_doctor.py --repo-root .
py -m pytest -q tests\test_slo_checker.py tests\test_system_doctor.py tests\test_cost_cache_governance.py
py -m pytest -q
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

P85-P95.1 已把 R-016 後端可靠性主線推進到 monitoring：post-P95.1C cloud verification run `26379118247` success，2026-05-25 health PASS，SLO `issues=[]`，doctor 無 blocking，budget `cooldown_active=false`，provider routing disabled，CCG008 僅 residual no_eligible。主公於 2026-05-25 核准 `R-016 downgrade to monitoring`；R-016 不標 Closed，保留 Open（Monitoring）至 2026-06-01。

P96/R-017 已完成 Website Content Trust runtime：cloud commit `0618717` content trust checker 全 PASS，主公於 2026-05-26 核准 `R-017 downgrade to monitoring`。R-017 不標 Closed，保留 Open（Monitoring）至 2026-06-02；若 latest report 再出現錯觀察室、`時間未知`、舊文污染或 checker FAIL，升回 active R-017。

P97/R-018 工具鏈戰線已完成 evaluation runtime。RTK `v0.42.0` Windows binary checksum PASS，僅在 `scratch/rtk_eval/bin/rtk.exe` 隔離執行；`Get-Command rtk` 前後皆 `NOT_FOUND`，未加入 PATH。`rtk init --codex --dry-run -v` would create `RTK.md` and patch `AGENTS.md` with `@RTK.md`，但 tracked diff before/after empty，未套用。Telemetry 顯示 `RTK_TELEMETRY_DISABLED=1 (blocked)`；runtime 建立的 local AppData `history.db` / `.hook_warn_last` 已清除。Baseline 顯示 pytest pass 有 83.0% savings，但 Git/search/read 類幾乎無收益或負收益；failure diagnostics 失敗，missing path / sentinel traceback 會被壓掉。裁決：不全域部署、不 project init、不 patch AOV instructions；若要繼續只能另開 P98 manual-prefix pilot。

## Window Switch Guidance

- 可以換視窗：P97 runtime closeout docs commit / push 後最穩；若本地 ahead 1，下一窗可先等主公 push。
- 最佳換窗點：P97 runtime closeout docs 已推送後，等待主公裁決是否開 P98 manual-prefix pilot。
- 若現在立刻換：下一窗讀 `NEXT_SESSION_HANDOFF.md` 頂部與 `docs/PHASE_97_RTK_EVALUATION.md`，先確認是否 push local P97 closeout commit。

## Next Decision

下一步是跑 P97 runtime closeout checks，commit closeout docs；push 仍需主公確認。推完後由主公裁決是否開 P98 project-local/manual-prefix pilot；目前不建議也不允許全域部署。
