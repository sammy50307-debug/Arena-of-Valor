# P96.0 Evidence Inventory — Website Content Trust

> Date: 2026-05-26 Asia/Taipei  
> Scope: raw-free evidence for R-017 / P96 content trust. No raw post bodies are stored here.

## Source Of Truth

| Layer | Evidence | Finding | Status |
|---|---|---|---|
| Config | `config.HERO_FOCUS_NAME` | Default focus hero is `芽芽`. | PASS |
| Latest report | `data/reports/aov_report_2026-05-25.html` | Focus room title is `芽芽 觀察室`. | PASS |
| Latest report | `data/reports/aov_report_2026-05-25.html` | `芽芽近期動態` contains a `圖倫` card. | FAIL |
| Latest report | `data/reports/aov_report_2026-05-25.html` | `芽芽近期動態` contains `時間未知`. | WARN |
| Manifest | `data/runs/2026-05-25/run_manifest.json` | Mode is production, status ok, report path is canonical. | PASS |
| Local artifacts | `data/analysis_20260525.json`, `data/raw_20260525.json` | Missing locally, so root cause cannot be proven from raw/analysis JSON. | EVIDENCE_GAP |
| Generator | `reporter/generator.py` | Prior logic trusted `hero_focus.name`, `is_hero_focus`, broad keywords, and missing dates too much. | FIXED_LOCAL |
| Template | `reporter/templates/report.html` | Prior highlight used picker `boost > 1.0`, which can echo false-positive focus labels. | FIXED_LOCAL |
| Picker | `analyzer/top5_picker.py` | Missing/invalid timestamp previously got fresh decay `1.0`. | FIXED_LOCAL |

## Root Cause Hypothesis

The production page failure is not a pure frontend styling issue. It is a content contract issue across generator, picker, and template:

- `hero_focus.name` was accepted from `daily_summary`, so an upstream wrong hero name could become the room title.
- `芽芽近期動態` trusted broad focus signals instead of requiring visible `芽芽` text evidence.
- Unknown timestamps were treated as fresh by the picker.
- The template displayed `[芽芽]` based on boost metadata, which could be inflated by false-positive focus flags.

## Local Fix

| Guard | File | Behavior |
|---|---|---|
| Focus title authority | `reporter/generator.py` | `hero_focus.name` is locked to `config.HERO_FOCUS_NAME`. |
| Focus recent eligibility | `reporter/generator.py` | `芽芽近期動態` requires visible focus hero text and known date. |
| Unknown date penalty | `analyzer/top5_picker.py` | Missing/invalid timestamps decay to `TOP5_SCORE_DECAY_MIN`. |
| Display label guard | `reporter/templates/report.html` | `[芽芽]` highlight no longer relies on boost alone. |
| Human memory | `docs/CONTENT_TRUST_KNOWN_ISSUES.md` | Records CT-001 and CT-002. |
| Machine memory | `configs/content_trust_known_issues.yaml` | Records issue ids, forbidden focus terms, and test links. |
| Executable memory | `scripts/check_report_content_trust.py` | Scans rendered report for known content-trust failures. |

## Verification

| Command | Result |
|---|---|
| `py -m pytest -q tests\test_report_content_trust.py tests\test_report_content_trust_checker.py tests\test_top5_picker.py tests\test_report_security.py tests\test_report_generator_landing.py tests\test_generator_landing.py tests\test_local_analyzer.py` | PASS, 60 passed |
| `py -m pytest -q` | PASS, 292 passed |
| `py scripts\lint_phase_plan.py docs\PHASE_96_PLAN.md` | PASS |
| `py scripts\check_handoff_truth.py --repo-root .` | PASS |
| `py scripts\governance_doctor.py --repo-root .` | PASS |
| `py scripts\check_report_content_trust.py --repo-root . --date 2026-05-25` | Expected fail-before: `focus recent forbidden terms=FAIL`, `focus recent unknown dates=WARN` |
| `git diff --check` | PASS |

## Remaining Gap

The existing committed 2026-05-25 production report still contains the old rendered HTML. P96 cannot be closed until a regenerated or newly dispatched report passes `scripts/check_report_content_trust.py`.
