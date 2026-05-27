# Generated Artifact Hygiene Policy

> Status: ACTIVE / P99. Created on 2026-05-27. This policy is advisory-only: it classifies staged paths before commit, but it does not delete, move, rename, unstage, or change `.gitignore`.

## Purpose

P98 showed that the AOV repository is not large because of core runtime code. The main hygiene risk is that generated reports, previews, scratch evidence, backups, and root debug outputs can drift into the same view as product code and governance docs.

P99 turns that risk into a path-only guard:

```text
staged path -> classify -> warn if risky -> human decides -> no automatic cleanup
```

The policy protects commit quality. It does not fix website content trust issues, old article selection, focus hero naming, GitHub Pages deployment, or report cleanup.

## Classifications

| Class | Examples | Default decision | Why |
|---|---|---|---|
| Keep | `analyzer/**`, `scrapers/**`, `reporter/**`, `notifier/**`, `configs/**`, `tests/**`, `scripts/**`, `docs/**`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md` | OK to stage when tied to the current task | Core code, checks, and governance truth belong in normal commits. |
| Production truth | `index.html`, `data/runs/**/run_manifest.json`, `data/llm_cache.json`, `data/llm_budget_state.json`, `data/.cache_policy.md` | OK only when the Phase explicitly needs it | These may be generated, but they can also be current deployment or runtime evidence. |
| Generated review | `data/reports/PREVIEW_*.html`, `data/reports/*_vN*.html`, `ui_previews/**`, `backups/**` | Advisory warning | These files are usually local previews, variants, or historical evidence. They require an explicit reason before staging. |
| Scratch / raw artifact | `scratch/**`, `data/enrichment_queue/**`, downloaded raw logs, temporary artifacts | Advisory warning; normally do not stage | These are working evidence, not source of truth. Keep the useful conclusion in docs instead. |
| Quarantine candidate | root debug outputs such as `run_log.txt`, `full_diff.txt`, `diff_result.txt`, `output.log`, `err.log`, `debug_output.txt` | Advisory warning; cleanup is out of P99 scope | These are likely legacy/debug debris. P99 only warns; P100+ must decide cleanup. |
| Decision required | `.gitignore`, `.github/workflows/**`, report deletion/move/rename, preview deletion/move/rename | Requires explicit 主公 approval and usually a separate Phase | These can affect deployment, history evidence, or future automation. |

## Advisory Guard Rules

The P99 checker is `scripts/check_generated_artifact_hygiene.py`.

Required behavior:

- Inspect only staged paths by default: `git diff --name-only --cached --diff-filter=ACMR`.
- Never read file contents.
- Never print raw report, raw post, queue, or secret content.
- Never modify the index, working tree, `.gitignore`, workflows, reports, or previews.
- Exit `0` by default even when advisories exist.
- Exit `1` only when explicitly run with `--strict`.
- Support `--paths` for tests and manual dry-runs.
- Support `--json` for machine-readable output.

## Examples

Safe dry-run with explicit paths:

```powershell
py scripts\check_generated_artifact_hygiene.py --repo-root . --paths docs/PHASE_99_PLAN.md analyzer/source_selection.py
```

Expected warning dry-run:

```powershell
py scripts\check_generated_artifact_hygiene.py --repo-root . --paths scratch/demo.txt data/reports/PREVIEW_yaya.html run_log.txt
```

Strict mode is reserved for experiments and future promotion reviews:

```powershell
py scripts\check_generated_artifact_hygiene.py --repo-root . --paths scratch/demo.txt --strict
```

## Promotion Criteria

This policy can only be promoted from advisory to strict after all conditions are met:

- At least two real Phase commits run the checker without harmful false positives.
- Any warning category that appears often has a documented keep/ignore decision.
- No production report, Pages artifact, or manifest is mislabeled as removable.
- 主公 explicitly approves the promotion in a later Phase.
- Rollback is trivial: strict mode can be disabled without touching product runtime.

## Stop Rules

Stop and open a new Phase if any of the following is needed:

- Delete, move, or rename tracked reports, previews, backups, or root debug files.
- Modify `.gitignore`.
- Modify GitHub Actions or Pages deployment.
- Read raw artifact contents to decide whether a file is safe.
- Convert the advisory checker into a pre-commit or CI blocking gate.

## Related Work

- P98: Project Flywheel Audit identified generated/deploy artifacts as the highest ROI hygiene target.
- P99: This policy and advisory checker.
- P100 candidate: Root legacy/debug debris quarantine plan.
- R-017 / P104 candidate: Content trust issues such as focus hero drift and old article pollution.
