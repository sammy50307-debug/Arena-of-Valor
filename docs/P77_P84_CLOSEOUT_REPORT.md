# P77-P84 Daily Monitoring Reliability Program Closeout（2026-05-18）

> 狀態：CLOSED WITH KNOWN OPERATIONAL RISK
> 範圍：P77 止血 -> P84 long-term governance
> 原則：本報告關閉的是可靠性治理戰役；目前 production SLO 仍有殘留營運風險，已登記為 `R-016`。

## 1. Phase 收官狀態

| Phase | 收官狀態 | 主要能力 | 證據 |
|---|---|---|---|
| P77 | CLOSED | 主鏈路止血、landing/report health 修復 | TASK_HISTORY P77 / P84.6 驗證矩陣 |
| P78 | CLOSED | run manifest / publish eligibility 合約 | `data/runs/2026-05-16/run_manifest.json`、manifest tests |
| P79 | CLOSED | `system_doctor.py` / runbook issue code | `DOC###` runbook anchors、doctor tests |
| P80 | CLOSED | promotion / atomic write / CI 實跑 | 2026-05-17 workflow_dispatch 成功證據 |
| P81 | CLOSED | replay / quarantine / backfill / debug bundle | replay/debug bundle tests 與 TASK_HISTORY |
| P82 | CLOSED | Asia/Taipei run context、run_id/source_hash | P82 tests、manifest v2 fields |
| P83 | CLOSED | data quality / HTML escape / LLM contract | P83 tests、doctor quality issue code |
| P84 | CLOSED | retention / SLO / handoff / governance / cost-cache | P84.1-P84.6 checker 與全套 pytest |

## 2. 收官驗證矩陣

| Check | Command | Result | 判讀 |
|---|---|---|---|
| Full pytest | `py -m pytest -q` | `204 passed` | PASS |
| Retention dry-run | `py scripts\retention_policy.py --repo-root . --today 2026-05-18 --max-candidates 5` | `dry_run=true`, `will_delete=false`, 17 report variant candidates | PASS；無實刪 |
| SLO checker | `py scripts\slo_checker.py --repo-root . --date 2026-05-18 --window-days 3` | `SLO001/SLO002/SLO003 BLOCKING` | KNOWN RISK；已登記 R-016 |
| Daily report health latest | `py scripts\check_daily_report_health.py --date 2026-05-18 --expected-mode any` | canonical/mode PASS；landing FAIL，仍指 2026-05-16 | KNOWN RISK；已登記 R-016 |
| Daily report health landing current | `py scripts\check_daily_report_health.py --date 2026-05-16 --expected-mode any` | PASS | 現有 landing 指向 2026-05-16 showcase_forced |
| Handoff truth | `py scripts\check_handoff_truth.py --repo-root .` | `HND000` | PASS |
| Governance doctor | `py scripts\governance_doctor.py --repo-root .` | `GOV000` | PASS |
| Cost/cache governance | `py scripts\cost_cache_governance.py --repo-root . --date 2026-05-18 --window-days 3` | `CCG003 ADVISORY` | PASS；低 cache hit 已可見 |
| Phase lint | `py scripts\lint_phase_plan.py docs\PHASE_84_PLAN.md` | PASS | PASS |
| Python 3.8 import guard | `py -3.8 -c "import ..."` | PASS | PASS |
| Whitespace diff | `git diff --check` | PASS | PASS |

## 3. Known Operational Risk

### R-016：production SLO blocking / landing stale

- `SLO001`: `consecutive_no_production=3 threshold=1`
- `SLO002`: `missing_manifest_count=2 threshold=0 window=2026-05-16,2026-05-17,2026-05-18`
- `SLO003`: `blocking_days=2 degraded_days=3 degraded_threshold=2`
- `check_daily_report_health --date 2026-05-18 --expected-mode any` 顯示 landing main link 仍指向 `data/reports/aov_report_2026-05-16.html`。

**判讀**：這不是 P84.6 的 checker 失敗，而是 P84/P79/P80/P84.2 成功把目前營運風險照出來。後續處置需在外部配額恢復或主公核准 production/backfill 後執行。

**R-016.1 更新（2026-05-19）**：
- 已修補 manifest sync contract：`.gitignore` 允許 `data/runs/**/run_manifest.json`，`main.py` 與 GitHub Actions fallback push 會同步 `data/runs/`。
- 已新增 `scripts/backfill_manifest_from_report.py`，可從既有 canonical report 反建 report-only manifest，不偽造 raw / analysis / production。
- 已從 2026-05-16 至 2026-05-19 canonical reports 建立 report-only manifests。
- 2026-05-19 SLO 已從 `SLO001/SLO002/SLO003` 收斂為 `SLO001` BLOCKING + `SLO003` DEGRADED；`SLO002` manifest gap 已消失。
- R-016 仍 Open，因目前所有 5/17-5/19 report 仍為 `showcase_forced`，尚未產出 `mode=production`。

**R-016.2 更新（2026-05-19）**：
- GitHub API 可列出 run，但 logs download endpoint 回覆 403：`Must have admin rights to Repository`，因此不能直接由本機下載 `Execute AoV Pipeline` 原始 log。
- 2026-05-19 手動 workflow #36 成功，後續 push run 也成功；manifest 顯示 source quality 正常（19 posts / 4 platforms），但 mode 仍為 `showcase_forced`。
- 已新增 workflow `LLM Secret Preflight (Advisory)`，下次 rerun 可直接在 Actions UI 看 `GEMINI_API_KEY` / `OPENAI_API_KEY` 是否配置，且不輸出 secret 值。
- 已新增 manifest provider diagnostics：`quota_error`、`openai_fallback_configured`、`openai_fallback_used`。
- 已讓 fallback client 在 Gemini provider failure 但 OpenAI fallback 不可用時輸出不含 secret 值的警示。

## 4. 後續維護規則

1. 新視窗不再自動開新 Phase；先讀 `NEXT_SESSION_HANDOFF.md` active bootstrap。
2. 若要修 R-016，優先順序是：確認外部配額 / 重跑 production / replay backfill / 跑 health + SLO。
3. 任一新 `DOC###` / `SLO###` / `HND###` / `GOV###` / `CCG###` 必須同 commit 更新 runbook anchor。
4. 任一 retention 實刪、資料搬移、production overwrite 都需要主公明確確認。
5. `TASK_HISTORY.md` 仍禁止全讀；查歷史只做 anchor search。
