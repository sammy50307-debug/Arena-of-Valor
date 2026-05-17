"""System doctor for daily monitoring reliability (P79 baseline)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyzer.run_context import build_run_context
from analyzer.run_manifest import validate_manifest
from check_daily_report_health import run_checks


SEV_BLOCKING = "BLOCKING"
SEV_DEGRADED = "DEGRADED"
SEV_ADVISORY = "ADVISORY"
SEV_OK = "OK"
RUNBOOK_PATH = "docs/OPERATIONS_RUNBOOK.md"

ISSUE_CATALOG = {
    "manifest_missing": {"code": "DOC001", "name": "manifest missing"},
    "manifest_invalid_json": {"code": "DOC002", "name": "manifest invalid json"},
    "manifest_contract": {"code": "DOC003", "name": "manifest contract"},
    "run_status": {"code": "DOC004", "name": "run status"},
    "run_mode": {"code": "DOC005", "name": "run mode"},
    "eligibility": {"code": "DOC006", "name": "eligibility decision"},
    "history_coverage": {"code": "DOC007", "name": "history source coverage"},
    "health_canonical_report": {"code": "DOC008", "name": "health:canonical report"},
    "health_landing_main_link": {"code": "DOC009", "name": "health:landing main link"},
    "health_generic": {"code": "DOC010", "name": "health:generic"},
    "debug_bundle_linked": {"code": "DOC011", "name": "debug bundle"},
    "debug_bundle_missing": {"code": "DOC012", "name": "debug bundle"},
}


@dataclass
class DoctorIssue:
    code: str
    severity: str
    name: str
    detail: str
    runbook: str


@dataclass
class DoctorResult:
    date: str
    profile: str
    issues: List[DoctorIssue]
    debug_bundle_path: str = ""
    debug_bundle_status: str = ""
    debug_bundle_error: str = ""

    @property
    def blocking_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_BLOCKING])

    @property
    def degraded_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_DEGRADED])

    @property
    def advisory_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_ADVISORY])


def taipei_today() -> str:
    return build_run_context().run_date


def _manifest_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / "data" / "runs" / date_str / "run_manifest.json"


def _issue_catalog_entry(key: str) -> dict:
    if key in ISSUE_CATALOG:
        return ISSUE_CATALOG[key]
    return {"code": "DOC999", "name": key}


def _runbook_link(code: str) -> str:
    return "%s#%s" % (RUNBOOK_PATH, code.lower())


def _add_issue(issues: List[DoctorIssue], key: str, severity: str, detail: str) -> None:
    entry = _issue_catalog_entry(key)
    issues.append(
        DoctorIssue(
            code=entry["code"],
            severity=severity,
            name=entry["name"],
            detail=detail,
            runbook=_runbook_link(entry["code"]),
        )
    )


def _would_fail(profile: str, issues: List[DoctorIssue]) -> bool:
    has_blocking = any(x.severity == SEV_BLOCKING for x in issues)
    if has_blocking:
        return True
    if profile == "ci":
        return any(x.severity == SEV_DEGRADED for x in issues)
    return False


def _find_latest_debug_bundle(repo_root: Path, date_str: str) -> Optional[Path]:
    bundle_dir = repo_root / "data" / "debug_bundles" / date_str
    if not bundle_dir.exists():
        return None
    bundles = sorted(bundle_dir.glob("debug_bundle_*.json"), key=lambda p: p.name, reverse=True)
    if not bundles:
        return None
    return bundles[0]


def _bundle_summary(bundle_path: Path) -> Tuple[str, str]:
    try:
        payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return "unknown", "%s: %s" % (type(exc).__name__, exc)
    status = str(payload.get("status", "unknown"))
    error = str(payload.get("error", "")).strip()
    return status, error


def run_doctor(
    repo_root: Path,
    date_str: str,
    profile: str = "local",
    require_production: bool = False,
) -> DoctorResult:
    repo_root = repo_root.resolve()
    issues: List[DoctorIssue] = []

    mpath = _manifest_path(repo_root, date_str)
    manifest = {}
    if not mpath.exists():
        _add_issue(issues, "manifest_missing", SEV_BLOCKING, "missing %s" % mpath)
    else:
        try:
            manifest = json.loads(mpath.read_text(encoding="utf-8"))
        except Exception as exc:
            _add_issue(
                issues,
                "manifest_invalid_json",
                SEV_BLOCKING,
                "invalid JSON: %s: %s" % (type(exc).__name__, exc),
            )
            manifest = {}

    if manifest:
        ok, errs = validate_manifest(manifest)
        if not ok:
            _add_issue(issues, "manifest_contract", SEV_BLOCKING, "; ".join(errs))
        status = manifest.get("status")
        mode = manifest.get("mode", "unknown")
        eligibility = manifest.get("eligibility", {})
        history = manifest.get("history", {})

        if status != "ok":
            _add_issue(issues, "run_status", SEV_BLOCKING, "status=%s" % status)
        if mode != "production":
            sev = SEV_DEGRADED if require_production else SEV_ADVISORY
            _add_issue(issues, "run_mode", sev, "mode=%s (not production)" % mode)

        if isinstance(eligibility, dict):
            decision = eligibility.get("decision")
            reasons = eligibility.get("reasons", [])
            if decision != "eligible":
                _add_issue(
                    issues,
                    "eligibility",
                    SEV_DEGRADED,
                    "decision=%s reasons=%s" % (decision, reasons),
                )

        if isinstance(history, dict):
            source_dates = history.get("source_dates", [])
            missing_dates = history.get("missing_dates", [])
            if (not source_dates) and missing_dates:
                _add_issue(
                    issues,
                    "history_coverage",
                    SEV_ADVISORY,
                    "source_dates empty; missing=%d" % len(missing_dates),
                )

    health_expected = "production" if require_production else "any"
    for check in run_checks(repo_root, date_str, expected_mode=health_expected, check_git_clean=False):
        if not check.failed:
            continue
        if check.name == "canonical report":
            _add_issue(issues, "health_canonical_report", SEV_BLOCKING, check.detail)
        elif check.name == "landing main link":
            _add_issue(issues, "health_landing_main_link", SEV_DEGRADED, check.detail)
        else:
            _add_issue(issues, "health_generic", SEV_DEGRADED, "%s: %s" % (check.name, check.detail))

    result = DoctorResult(date=date_str, profile=profile, issues=issues)
    if _would_fail(profile, issues):
        bundle = _find_latest_debug_bundle(repo_root, date_str)
        if bundle is not None:
            status, error = _bundle_summary(bundle)
            result.debug_bundle_path = str(bundle)
            result.debug_bundle_status = status
            result.debug_bundle_error = error
            detail = "linked %s (status=%s%s)" % (
                bundle,
                status,
                ", error=%s" % error if error else "",
            )
            _add_issue(result.issues, "debug_bundle_linked", SEV_ADVISORY, detail)
        else:
            _add_issue(
                result.issues,
                "debug_bundle_missing",
                SEV_ADVISORY,
                "no bundle found under %s" % (repo_root / "data" / "debug_bundles" / date_str),
            )
    return result


def print_result(result: DoctorResult) -> None:
    print("System doctor")
    print("date: %s" % result.date)
    print("profile: %s" % result.profile)
    print("")
    print("| severity | code | check | detail | runbook |")
    print("|---|---|---|---|---|")
    if not result.issues:
        print("| OK | DOC000 | summary | no issues detected | %s#doc000 |" % RUNBOOK_PATH)
        return
    for issue in result.issues:
        print(
            "| %s | %s | %s | %s | %s |"
            % (
                issue.severity,
                issue.code,
                issue.name,
                issue.detail.replace("|", "/"),
                issue.runbook,
            )
        )


def exit_code_for(result: DoctorResult) -> int:
    if result.blocking_count > 0:
        return 1
    if result.profile == "ci" and result.degraded_count > 0:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="System doctor for daily monitoring pipeline.")
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument("--date", default=taipei_today(), help="Target date YYYY-MM-DD.")
    parser.add_argument("--profile", choices=["local", "ci"], default="local", help="Doctor profile.")
    parser.add_argument(
        "--require-production",
        action="store_true",
        help="Treat non-production mode as degraded and use production health expectation.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_doctor(
        Path(args.repo_root),
        args.date,
        profile=args.profile,
        require_production=args.require_production,
    )
    print_result(result)
    return exit_code_for(result)


if __name__ == "__main__":
    sys.exit(main())
