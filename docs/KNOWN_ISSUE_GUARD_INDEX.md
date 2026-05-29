# Known Issue Guard Index

> Status: ACTIVE / P101 runtime. Created on 2026-05-29. This index is a guard map, not a cleanup approval and not proof that every risk is fully solved.

## Purpose

P101 turns scattered known issue memory into a single handoff surface:

```text
known issue / risk -> human doc -> machine guard -> focused command -> state -> gap -> next action
```

The index is metadata-only. It does not copy raw report content, raw posts, raw logs, queue payloads, secrets, or generated artifact bodies.

## Guard Rules

- A row may claim a machine guard only when a concrete script, test, config, schema, or monitor exists.
- Human-only decisions must say `human-only` or `missing-machine-guard` in the Gap column.
- Advisory guards are not strict gates unless a later Phase explicitly promotes them.
- Missing guards are backlog items, not hidden success.
- Paths and commands are references; this document does not approve cleanup, provider changes, RTK install, or GitHub Actions changes.

<!-- GUARD_INDEX_START -->
| Risk ID | Issue | Human Doc | Machine Guard | Focused Command | State | Gap | Next Action |
|---|---|---|---|---|---|---|---|
| R-016 | Production SLO / backend reliability / landing freshness | `docs/RISK_REGISTRY.md` R-016; `docs/OPERATIONS_RUNBOOK.md` | `scripts/slo_checker.py`; `scripts/system_doctor.py`; `scripts/cost_cache_governance.py` | `py scripts\slo_checker.py --repo-root .`; `py scripts\system_doctor.py --repo-root .`; `py scripts\cost_cache_governance.py --repo-root .` | Open Monitoring until 2026-06-01 | observation-window; not-closed | Review latest cloud evidence after monitoring window before downgrade/close. |
| R-017 | Website content trust / focus hero mismatch / stale articles | `docs/CONTENT_TRUST_KNOWN_ISSUES.md`; `docs/RISK_REGISTRY.md` R-017 | `configs/content_trust_known_issues.yaml`; `scripts/check_report_content_trust.py`; `tests/test_report_content_trust.py`; `tests/test_report_content_trust_checker.py` | `py scripts\check_report_content_trust.py --repo-root . --date YYYY-MM-DD` | Open Monitoring until 2026-06-02 | content-trust-not-covered-by-R-016; latest-report-sensitive | Run after Daily Monitor or manual dispatch; escalate if focus title, stale article, or unknown date returns. |
| R-018 | RTK token-saving proxy / toolchain output fidelity | `docs/PHASE_97_RTK_EVALUATION.md`; `docs/RISK_REGISTRY.md` R-018 | N/A | N/A | Open Install blocked | missing-machine-guard; human-only; global-deployment-blocked | Only revisit through isolated pilot with ROI, fidelity, rollback, scope, and privacy gates. |
| R-019 | Project self-optimization flywheel / repo entropy | `docs/PHASE_98_AUDIT.md`; `docs/RISK_REGISTRY.md` R-019; `docs/KNOWN_ISSUE_GUARD_INDEX.md` | `scripts/check_generated_artifact_hygiene.py`; `scripts/check_root_legacy_hygiene.py`; `scripts/check_known_issue_guard_index.py` | `py scripts\check_generated_artifact_hygiene.py --repo-root .`; `py scripts\check_root_legacy_hygiene.py --repo-root .`; `py scripts\check_known_issue_guard_index.py --repo-root .` | Open Program guard active | composite-advisory; no-strict-gate | Keep splitting high-ROI gaps into small phases; review every 5-10 phases. |
| R-020 | Generated artifact hygiene / stage guard false positives | `docs/GENERATED_ARTIFACT_POLICY.md`; `docs/RISK_REGISTRY.md` R-020 | `scripts/check_generated_artifact_hygiene.py`; `tests/test_generated_artifact_hygiene.py` | `py scripts\check_generated_artifact_hygiene.py --repo-root . --paths <paths>` | Open Advisory guard active; cleanup blocked | advisory-only; no-strict-gate | Use before commits that touch reports, previews, backups, scratch, workflows, or `.gitignore`. |
| R-021 | Root legacy / debug debris quarantine false deletion | `docs/ROOT_LEGACY_QUARANTINE.md`; `docs/RISK_REGISTRY.md` R-021 | `scripts/check_root_legacy_hygiene.py`; `tests/test_root_legacy_hygiene.py` | `py scripts\check_root_legacy_hygiene.py --repo-root . --paths <paths>` | Open Advisory guard active; cleanup blocked | advisory-only; no-cleanup-approval | Keep warning on root debris; any move/delete needs separate approval and rollback. |
| R-022 | Known issue guard index drift / false confidence | `docs/PHASE_101_PLAN.md`; `docs/RISK_REGISTRY.md` R-022; `docs/KNOWN_ISSUE_GUARD_INDEX.md` | `scripts/check_known_issue_guard_index.py`; `tests/test_known_issue_guard_index.py` | `py scripts\check_known_issue_guard_index.py --repo-root .` | Open Advisory guard active | advisory-only; no-strict-gate | Re-run when risk registry, known issue docs, guard scripts, or phase state changes. |
| GOV-HANDOFF | Handoff truth / governance drift | `NEXT_SESSION_HANDOFF.md`; `docs/ACTIVE_OPERATION.md`; `docs/OPERATIONS_RUNBOOK.md` | `scripts/check_handoff_truth.py`; `scripts/governance_doctor.py`; `tests/test_governance_doctor.py` | `py scripts\check_handoff_truth.py --repo-root .`; `py scripts\governance_doctor.py --repo-root .` | Active governance guard | governance-only; not-product-correctness | Run before handoff/risk/active-operation commits. |
<!-- GUARD_INDEX_END -->

## Human-only Backlog

These open risks are intentionally listed as human-only or partially guarded. P101 does not pretend they are solved.

| Risk ID | Current protection | Gap | Future trigger |
|---|---|---|---|
| R-001 | Manual sync discipline for model guide mirrors | missing-machine-guard; human-only | If model guide drift recurs, add sync checker. |
| R-002 | 90-day model guide review policy | missing-machine-guard; human-only | If provider/model facts change, run web-verified guide update. |
| R-003 | Behavioral observation for model escalation reminders | missing-machine-guard; human-only | If AI misses escalation reminder, reinforce global/project rules. |
| R-004 | Manual LINE WebView validation SOP | missing-machine-guard; human-only | If template changes or mobile regression returns, add browser/device smoke. |
| R-006 | Manual static report patching SOP | missing-machine-guard; human-only | If generated report structure diverges again, add idempotent patch check. |
| R-011 | Orphan skill lint warning exemption | partial-machine-guard | If orphan skill is revived, require S1 schema before commit. |
| R-012 | Manual skill metrics size check | missing-machine-guard; human-only | If metrics file grows past threshold, add rotation command/check. |
| R-013 | M4 sync-rules heuristic warning | partial-machine-guard | If false recall causes duplicated rules, improve heuristic or use semantic matching. |

## Advisory Checker

P101 adds `scripts/check_known_issue_guard_index.py`.

Required behavior:

- Read only `docs/KNOWN_ISSUE_GUARD_INDEX.md` unless `--index` points to a test file.
- Never read raw reports, raw logs, raw queues, generated report bodies, or secrets.
- Check that required rows and columns exist.
- Check that required guard tokens are visible for R-016, R-017, R-019, R-020, R-021, R-022, and GOV-HANDOFF.
- Check that R-018 is explicitly marked `missing-machine-guard` / `human-only`.
- Exit `0` by default even when advisories exist.
- Exit `1` only when explicitly run with `--strict`.

## Commands

Default advisory check:

```powershell
py scripts\check_known_issue_guard_index.py --repo-root .
```

JSON output:

```powershell
py scripts\check_known_issue_guard_index.py --repo-root . --json
```

Strict mode is reserved for experiments and future promotion reviews:

```powershell
py scripts\check_known_issue_guard_index.py --repo-root . --strict
```

## Stop Rules

Stop and open a new Phase if any of the following is needed:

- Convert the checker into a pre-commit, CI, or GitHub Actions blocking gate.
- Modify existing P96/P99/P100/R-016 checkers while updating this index.
- Close R-016 or R-017 monitoring without fresh production evidence.
- Treat RTK as installed or approved.
- Delete, move, rename, or ignore generated/root/scratch files.
- Copy raw report/log/post/queue content into this index.

## Related Work

- P96: Website Content Trust guard.
- P97: RTK evaluation and install-blocked decision.
- P98: Project flywheel audit.
- P99: Generated artifact hygiene policy and advisory guard.
- P100: Root legacy/debug debris quarantine and advisory guard.
- P101: This index and advisory drift checker.
