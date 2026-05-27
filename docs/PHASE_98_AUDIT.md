# Phase P98 Runtime Audit — Project Flywheel Audit

> Status: COMPLETED / REPORT ONLY. 主公已核准 `P98 audit runtime`（2026-05-27）。本文件只記錄 metadata audit 與下一步候選；未清理、未搬檔、未改 `.gitignore`、未改 runtime code、未改 GitHub Actions、未導入 RTK。

---

## 1. Executive Decision

P98 的核心發現很直接：

- AOV 不是「核心程式碼巨大」的專案；核心 runtime 約 49 tracked files / 0.44 MB。
- 真正造成接手與返工成本的，是 generated/deploy artifacts、agent/skill layer、靜態大圖/字型、治理文件、根目錄 legacy/debug 檔與 untracked 暫存一起堆在同一個 repo 視野。
- 已經有一批 guard 能保護 R-016 / R-017 / R-018，但「repo hygiene / generated artifact policy / root legacy debris / skill layer drift」還主要靠人腦與 handoff 提醒。
- 下一步不應大重構；應拆成小 Phase，把最容易誤 stage、誤刪、誤判的地方先做成 policy + checker。

**P98 裁決**：

| 項目 | 裁決 |
|---|---|
| 立刻清理 generated reports / scratch | 不做；需另開 P99+ 並有 rollback policy |
| 立刻改 `.gitignore` | 不做；先寫 artifact policy / inventory |
| 立刻移除 root legacy logs | 不做；先列 quarantine candidate |
| 立刻整理 `.agents` / skills | 不做；先列 skill-layer hygiene candidate |
| 下一個最推薦 Phase | **P99 Generated Artifact Hygiene Policy / Stage Guard** |

---

## 2. Evidence Commands

P98 audit 使用 metadata / focused check，不全讀 `TASK_HISTORY.md`，不讀 raw artifacts。

```powershell
git status --short --branch
git ls-files | Measure-Object
git ls-files | Group-Object top-level path
git ls-files | Get-Item Length | Sort-Object Bytes -Descending
git status --short | group untracked top-level path
git check-ignore -v scratch/ data/enrichment_queue/example.json
py scripts\check_report_content_trust.py --repo-root . --date 2026-05-26
py scripts\slo_checker.py --repo-root . --date 2026-05-26
py scripts\system_doctor.py --repo-root . --date 2026-05-26 --profile local --require-production
py scripts\cost_cache_governance.py --repo-root . --date 2026-05-26 --window-days 3
py scripts\lint_skill_registry.py
```

---

## 3. Repo Layer Inventory

### 3.1 Tracked File Shape

| Layer | Files | Size | P98 interpretation |
|---|---:|---:|---|
| Generated / deploy artifacts | 123 | 22.18 MB | 最大 tracked layer；包含 reports、previews、backups、landing。不可直接刪，因可能是 Pages / history evidence。 |
| Agent / skill layer | 383 | 9.30 MB | 檔案數最大；主要來自 `.agents/skills/ui-ux-pro-max-skill`。需另開 skill hygiene，不應混進 product bugfix。 |
| Static assets | 3 | 7.89 MB | 根目錄 / image 類大檔；`yaya_bg.png` 有多份。需判斷 canonical asset source。 |
| Governance docs | 87 | 1.71 MB | phase docs / risk / runbook / handoff；可追溯性高，但同步成本高。 |
| Root legacy / other | 59 | 0.48 MB | 根目錄有多個 debug / diff / log / loose script；接手噪音高。 |
| Core runtime | 49 | 0.44 MB | 核心程式其實小；不該用大重構處理 repo 變亂感。 |
| Automation scripts / CI | 30 | 0.22 MB | 現有 checker / doctor / workflow guard 層。 |
| Tests | 44 | 0.22 MB | 測試量與 core 相稱，是健康訊號。 |
| Data / cache / manifests | 16 | 0.20 MB | `data/runs/**/run_manifest.json` 已納入 production truth；raw queue 仍 git-ignored。 |

### 3.2 High-Weight Files / Directories

| Finding | Evidence | Risk | Recommended handling |
|---|---|---|---|
| 大圖重複 | `yaya_bg.png`、`ui_previews/yaya_bg.png`、`data/reports/yaya_bg.png` 各約 7.1 MB | repo 體積與 generated boundary 混淆 | P99 只先確認 canonical asset source，不直接刪 |
| tracked reports 多版本 | `data/reports` tracked 88 files；日期如 2026-05-01 有 29 份、2026-04-05 有 18 份 | 歷史證據與 generated output 混在 repo | P99 建 retention policy：canonical keep / preview artifact / old evidence archive |
| tracked previews | `ui_previews` tracked 27 files，但 `.gitignore` 已忽略 `ui_previews/` 新產物 | 既有 tracked 檔仍會留下 | 另開 P99+ 裁決是否保留 golden previews |
| scratch ignored but large | local `scratch/` 66 files / 12.31 MB；`scratch/` 被 `.gitignore` ignore | 不會被 git 自動追蹤，但容易讓 AI 誤讀 | 保持 ignored；只保存 evidence summary |
| root debug debris | `run_log.txt` 154.1 KB、`full_diff.txt` 74.9 KB、`diff_result.txt` 53.9 KB、`output.log` 15.8 KB | 根目錄噪音，可能誤當權威資料 | P100 quarantine plan：先列清單，再裁決 move/delete |
| quoted / escaped tracked paths | git ls-files 顯示 3 個帶 quote/escaped 路徑 | 跨平台 path hygiene 風險 | P100/P102 檢查是否仍需保留 |

---

## 4. Known Issue Memory Gap

| Issue / risk | Human-readable memory | Machine-readable guard | Current check result | Gap |
|---|---|---|---|---|
| R-017 / CT-001 wrong focus hero title | `docs/CONTENT_TRUST_KNOWN_ISSUES.md`、`docs/RISK_REGISTRY.md` | `configs/content_trust_known_issues.yaml`、`scripts/check_report_content_trust.py`、`tests/test_report_content_trust.py` | 2026-05-26 content trust PASS | Good coverage；但 checker 對 `focus recent section absent` 目前 PASS，若未來需要必顯示芽芽區，可另開 strict rule |
| R-017 / CT-002 stale article pollution | 同上 | 同上；unknown date guard | 2026-05-26 `report unknown dates` PASS | Good coverage for `時間未知`；Top-5/general feed 的「舊但有日期」仍需更明確 freshness contract |
| R-016 production SLO / landing stale | `docs/RISK_REGISTRY.md`、`docs/OPERATIONS_RUNBOOK.md` | `scripts/slo_checker.py`、`scripts/system_doctor.py`、health tests | 2026-05-26 SLO000 OK；doctor only advisory/residual | Good coverage；monitoring date 到期需人工裁決 close/downgrade |
| R-018 RTK output fidelity | `docs/PHASE_97_RTK_EVALUATION.md`、`docs/RISK_REGISTRY.md` | No strict repo checker | P97 evidence says install blocked | Gap: 沒有機器檢查 `Get-Command rtk` / `@RTK.md` 未進 repo；低頻但高影響 |
| R-019 repo entropy / generated boundary | `docs/PHASE_98_PLAN.md`、本 audit | No checker yet | N/A | Biggest gap；目前只靠 handoff 禁止誤 stage |
| Skill layer stale / S1 drift | `docs/SKILL_HEALTH.md` | `scripts/lint_skill_registry.py` | 22 warnings, 0 blocking errors | Gap: warning 長期存在，且 `.agents` 體積最大；需裁決哪些 warning 要修、哪些降噪 |
| Root legacy/debug files | none dedicated | none | tracked root debug/log files present | Gap: 沒有 policy 定義 root 哪些檔案可存在 |

---

## 5. Generated Artifact Hygiene

| Class | Examples | Current state | Risk | P98 recommendation |
|---|---|---|---|---|
| Canonical production reports | `data/reports/aov_report_YYYY-MM-DD.html` | tracked, many dates | 可能是 Pages / historical evidence | Keep until P99 defines retention |
| Duplicate report versions | `*_v2.html`, `*_v3.html`, date spikes | tracked/untracked both exist | repo 噪音，AI 容易讀錯版本 | P99 classify: latest canonical vs old variant |
| UI previews | `ui_previews/*.html`, `ui_previews/yaya_bg.png` | tracked old files, new ignored | golden preview vs scratch 混線 | P99 decide golden previews only |
| Local previews / scratch | `scratch/`, `data/reports/PREVIEW_*.html` untracked | ignored or untracked | 誤 stage 風險 | Add stage guard / documented ignore policy |
| Run manifests | `data/runs/**/run_manifest.json` | tracked 11 manifests | production truth | Keep; this is low-size high-value evidence |
| LLM cache / budget state | `data/llm_cache.json`, `data/llm_budget_state.json` | explicitly unignored | can expose derived content / state | Keep only if raw-free policy remains true; checker already reads schema/stats |
| Enrichment raw queue | `data/enrichment_queue/` | ignored by `data/*` | raw post content risk | Keep ignored; artifact short retention only |

---

## 6. Verification Ladder

Use this ladder for future phases so we stop running either too little or too much.

| Work type | Minimal check | Broader check | Cloud / manual gate |
|---|---|---|---|
| Governance-only docs | `git diff --check`; `lint_phase_plan`; `check_handoff_truth`; `governance_doctor` | phase-specific lint | Push only after主公確認 |
| Content trust / frontend report semantics | `check_report_content_trust.py --date <latest>`; `tests/test_report_content_trust.py` | report generator tests; manual browser screenshot if UI changed | Daily Monitor artifact / Pages latest report |
| Production SLO / pipeline | `slo_checker.py`; `system_doctor.py`; `cost_cache_governance.py` | focused pytest for touched module | GitHub Actions AoV Daily Monitor run |
| Generated artifact / repo hygiene | `git status --short`; proposed stage guard; metadata inventory | no full pytest unless tooling changed | 主公裁決 before move/delete |
| Toolchain / RTK / provider | isolated dry-run; PATH/profile diff; telemetry/privacy check | fidelity tests for failure output | Never global deploy without pilot |
| Skill layer | `lint_skill_registry.py`; `gen_skill_health.py` | skill-specific tests | Only deploy/sync skills in dedicated phase |

---

## 7. P99+ Candidate Ranking

| Rank | Candidate phase | ROI | Risk | Effort | Why this order |
|---:|---|---|---|---|---|
| 1 | **P99 Generated Artifact Hygiene Policy / Stage Guard** | High | Medium | 1.5-2.5h | Directly attacks the largest confusion source: 123 tracked generated/deploy files, 21 untracked reports, and recurring forbidden-work warnings. Output should be policy + checker, not deletion. |
| 2 | **P100 Root Legacy / Debug Debris Quarantine Plan** | High | Medium | 1.5-3h | Root has tracked `run_log.txt`, diff/debug outputs, loose scripts, and escaped filenames. Quarantine plan lowers AI misread risk without touching product behavior. |
| 3 | **P101 Known Issue Guard Index** | High | Low-Medium | 1.5-2h | Build a single index mapping risk -> human doc -> machine guard -> check command. This makes the flywheel real and helps future windows avoid chat-memory-only fixes. |
| 4 | **P102 Skill Layer Hygiene Audit** | Medium | Medium | 2-4h | `.agents` is file-count heavy and `lint_skill_registry.py` has 22 warnings. Needs a dedicated lane so product bugfixes do not fight skill maintenance. |
| 5 | **P103 Verification Ladder Automation** | Medium | Low-Medium | 1.5-3h | Encode “which focused checks to run for which file changes” into a small advisory tool or doc table. Useful, but should follow artifact/known-issue cleanup. |
| 6 | **P104 Content Trust Freshness Strictness Review** | Medium | Medium | 1.5-3h | R-017 guards are good, but freshness of old dated articles and absent focus section strictness may need follow-up if主公 still sees stale content. Should trigger only with fresh production evidence. |

---

## 8. Stop Rules

P99+ must stop and ask主公 before any of these:

- deleting, moving, or renaming tracked reports / previews / assets;
- changing `.gitignore` in a way that changes what production commits;
- removing root scripts/logs without proving they are not referenced;
- promoting advisory checks to blocking gates;
- changing GitHub Actions / Pages deployment;
- installing or initializing RTK.

---

## 9. P98 Runtime Closure

| Exit item | Status |
|---|---|
| Repo layer inventory | PASS |
| Known issue memory gap | PASS |
| Generated artifact hygiene table | PASS |
| Verification ladder | PASS |
| Top P99+ phase ranking | PASS |
| Runtime cleanup / refactor | Not performed by design |

P98 runtime is complete as a report-only audit. The next strategic decision is whether to open **P99 Generated Artifact Hygiene Policy / Stage Guard**.
