# Root Legacy / Debug Debris Quarantine

> Status: ACTIVE / P100 runtime evidence. Created on 2026-05-27. This document is a quarantine decision table, not a cleanup approval. No root file is deleted, moved, renamed, or ignored by P100.

## Purpose

P100 addresses root-level noise: tracked debug logs, diff outputs, loose preview scripts, old helper scripts, and static assets that sit beside actual entry files. The goal is to stop future AI sessions from treating old root debris as current truth.

P100 uses this sequence:

```text
root path -> metadata inventory -> safe reference check -> decision table -> future explicit approval before cleanup
```

## Guardrails

- Do not delete, move, rename, or archive any root file in P100.
- Do not modify `.gitignore`.
- Do not modify GitHub Actions or Pages deployment.
- Do not read raw debug log contents.
- Do not treat references in `TASK_HISTORY.md` as active usage.
- Any future cleanup must include a rollback plan and 主公 approval.

## Inventory Summary

| Group | Paths | Evidence | P100 decision |
|---|---|---|---|
| Keep / entry | `main.py`, `config.py`, `index.html`, `requirements.txt`, `.nojekyll`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_RULES.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md` | Product entry, deployment truth, dependency/config, or governance source | Keep |
| Static asset decision | `yaya_bg.png`, `step.jpg` | Large root assets; `yaya_bg.png` and preview/report copies are a separate static asset source problem | Decision required outside P100 |
| High-weight debug output | `run_log.txt`, `full_diff.txt`, `diff_result.txt`, `output.log` | Large root logs/diffs; no active code/workflow references found in safe-scope search | Archive candidate only after future approval |
| Tiny debug output | `compile_errors.txt`, `debug_output.txt`, `encoding_errors.txt`, `err.log`, `err.txt`, `error.txt`, `out.txt`, `syntax_out.txt`, `test_handoff_out.txt`, `ver.txt` | Mostly zero-byte or tiny outputs; `err.log` is referenced in `AGENTS.md` as an example output path | Decision required; do not delete in P100 |
| Loose preview/generation scripts | `preview_report_script.py`, `preview_phase33.py`, `generate_final_demo.py`, `generate_final_full_preview.py`, `generate_flagship_report.py`, `force_gen.py`, `quick_demo.py` | Git history ties them to older UI/report phases; no active safe-scope references found | Archive candidate after reference review |
| Loose patch/manual helpers | `patch.py`, `patch_generate.py`, `push_now.py`, `diag_boot.py`, `css_compare.py` | Root helper scripts likely created for manual repair/debug | Archive candidate after reference review |
| Root test/health helpers | `test_data_writer.py`, `test_gemini.py`, `test_imports.py`, `test_run.py`, `test_tg.py`, `check_health.py`, `validate_data_dir.py`, `syntax_check.py` | `check_health.py` is referenced by `README.md`; others need future owner decision | Keep or document-only pending future runtime |

## Safe Reference Check

P100 used a metadata-safe reference scan over `docs`, `scripts`, `tests`, `.github`, `analyzer`, `reporter`, `scrapers`, `notifier`, `configs`, and root governance/config files. It deliberately excluded raw debug log contents and did not full-read `TASK_HISTORY.md`.

| Candidate group | Safe-scope result | Interpretation |
|---|---|---|
| `run_log.txt` | References found in P99/P100 governance docs, P99 checker, and P99 tests | Reference exists as known-risk documentation, not active runtime usage. |
| `full_diff.txt`, `diff_result.txt`, `output.log` | References found in generated artifact policy, P98/P99/P100 docs, and P99 checker | Reference exists as governance evidence, not active runtime usage. |
| zero-byte debug outputs | Mostly referenced only by P99 checker; `err.log` also appears in `AGENTS.md` as an error-log example | Treat as decision-required; `err.log` convention needs a future replacement or ignore decision. |
| loose preview/generation scripts | No active safe-scope references found | Likely archive candidates, but move/delete still requires future explicit approval. |
| `check_health.py` | Referenced by `README.md` | Keep or modernize in a separate health-check phase. |
| root static assets | Not assessed for cleanup | Static asset canonical source is out of P100 scope. |

## Advisory Checker

P100 adds `scripts/check_root_legacy_hygiene.py`.

The checker is advisory-only:

- By default it checks staged paths from `git diff --name-only --cached --diff-filter=ACMR`.
- It supports `--paths` for dry-runs and tests.
- It supports `--json` for machine-readable output.
- It exits `0` by default even when advisories exist.
- It exits `1` only when explicitly run with `--strict`.
- It is path-only and never reads raw debug log contents.

## Future Runtime Gate

Future cleanup may only proceed after a new approval that contains:

| Requirement | Meaning |
|---|---|
| Reference result | Show whether the file is referenced by active docs/scripts/workflows/imports. |
| Proposed action | Keep, document-only, archive, delete, or decision-required. |
| Rollback | Exact restore command or commit revert route. |
| Scope separation | Do not mix root cleanup with generated reports, static assets, or skill-layer work. |
| 主公 approval | Approval must be explicit and per action group. |

## Current Decision

P100 runtime produces evidence and an advisory guard. It does not approve cleanup.

Next high-ROI follow-up candidates:

- P100.1 root reference inventory runtime, if 主公 wants actual archive/delete proposals.
- P101 Known Issue Guard Index.
- P102 Skill Layer Hygiene Audit.
