"""SLO / escalation checker for P84.2 long-term governance.

The checker is advisory-first: it emits explicit SLO issue codes and exits
non-zero only when a BLOCKING SLO is detected. It does not modify data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyzer.run_context import build_run_context
from check_daily_report_health import extract_metadata_mode, report_path
from system_doctor import SEV_ADVISORY, SEV_BLOCKING, SEV_DEGRADED, run_doctor


RUNBOOK_PATH = "docs/OPERATIONS_RUNBOOK.md"
CLASS_CURRENT = "current"

ISSUE_CATALOG = {
    "production_stale": {"code": "SLO001", "name": "production freshness"},
    "manifest_gap": {"code": "SLO002", "name": "manifest gap"},
    "doctor_severity": {"code": "SLO003", "name": "doctor severity budget"},
}


@dataclass
class DailySloState:
    date: str
    manifest_present: bool
    production_report: bool
    doctor_blocking: int
    doctor_degraded: int
    doctor_advisory: int


@dataclass
class SloIssue:
    code: str
    severity: str
    name: str
    detail: str
    runbook: str
    classification: str


@dataclass
class SloResult:
    date: str
    window_days: int
    classification: str
    consecutive_no_production: int
    missing_manifest_count: int
    doctor_blocking_days: int
    doctor_degraded_days: int
    issues: List[SloIssue]
    days: List[DailySloState]


def taipei_today() -> str:
    return build_run_context().run_date


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError("date must use YYYY-MM-DD format")


def _date_window(end_date: str, window_days: int) -> List[str]:
    if window_days < 1:
        raise ValueError("window_days must be >= 1")
    end = _parse_date(end_date)
    start = end - timedelta(days=window_days - 1)
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(window_days)]


def _runbook_link(code: str) -> str:
    return "%s#%s" % (RUNBOOK_PATH, code.lower())


def _issue(key: str, severity: str, detail: str, classification: str = CLASS_CURRENT) -> SloIssue:
    entry = ISSUE_CATALOG[key]
    return SloIssue(
        code=entry["code"],
        severity=severity,
        name=entry["name"],
        detail=detail,
        runbook=_runbook_link(entry["code"]),
        classification=classification,
    )


def _manifest_present(repo_root: Path, date_str: str) -> bool:
    return (repo_root / "data" / "runs" / date_str / "run_manifest.json").exists()


def _is_production_report(repo_root: Path, date_str: str) -> bool:
    report = report_path(repo_root, date_str)
    if not report.exists():
        return False
    return extract_metadata_mode(report) == "production"


def _consecutive_tail_failures(days: List[DailySloState]) -> int:
    count = 0
    for item in reversed(days):
        if item.production_report:
            break
        count += 1
    return count


def evaluate_slo(
    repo_root: Path,
    date_str: str,
    window_days: int = 7,
    max_consecutive_no_production: int = 1,
    max_missing_manifests: int = 0,
    max_doctor_degraded_days: int = 2,
) -> SloResult:
    repo_root = Path(repo_root).resolve()
    dates = _date_window(date_str, window_days)
    days: List[DailySloState] = []

    for current in dates:
        doctor_result = run_doctor(
            repo_root,
            current,
            profile="local",
            require_production=True,
            check_landing=False,
        )
        days.append(
            DailySloState(
                date=current,
                manifest_present=_manifest_present(repo_root, current),
                production_report=_is_production_report(repo_root, current),
                doctor_blocking=doctor_result.blocking_count,
                doctor_degraded=doctor_result.degraded_count,
                doctor_advisory=doctor_result.advisory_count,
            )
        )

    consecutive_no_production = _consecutive_tail_failures(days)
    missing_manifest_count = len([x for x in days if not x.manifest_present])
    doctor_blocking_days = len([x for x in days if x.doctor_blocking > 0])
    doctor_degraded_days = len([x for x in days if x.doctor_degraded > 0])

    issues: List[SloIssue] = []
    if consecutive_no_production > max_consecutive_no_production:
        severity = SEV_BLOCKING if consecutive_no_production >= 3 else SEV_DEGRADED
        issues.append(
            _issue(
                "production_stale",
                severity,
                "consecutive_no_production=%s threshold=%s"
                % (consecutive_no_production, max_consecutive_no_production),
            )
        )

    if missing_manifest_count > max_missing_manifests:
        issues.append(
            _issue(
                "manifest_gap",
                SEV_BLOCKING,
                "missing_manifest_count=%s threshold=%s window=%s"
                % (missing_manifest_count, max_missing_manifests, ",".join(dates)),
            )
        )

    if doctor_blocking_days > 0 or doctor_degraded_days > max_doctor_degraded_days:
        severity = SEV_BLOCKING if doctor_blocking_days > 0 else SEV_DEGRADED
        issues.append(
            _issue(
                "doctor_severity",
                severity,
                "blocking_days=%s degraded_days=%s degraded_threshold=%s"
                % (doctor_blocking_days, doctor_degraded_days, max_doctor_degraded_days),
            )
        )

    return SloResult(
        date=date_str,
        window_days=window_days,
        classification=CLASS_CURRENT,
        consecutive_no_production=consecutive_no_production,
        missing_manifest_count=missing_manifest_count,
        doctor_blocking_days=doctor_blocking_days,
        doctor_degraded_days=doctor_degraded_days,
        issues=issues,
        days=days,
    )


def result_to_dict(result: SloResult) -> Dict[str, object]:
    return {
        "date": result.date,
        "window_days": result.window_days,
        "classification": result.classification,
        "consecutive_no_production": result.consecutive_no_production,
        "missing_manifest_count": result.missing_manifest_count,
        "doctor_blocking_days": result.doctor_blocking_days,
        "doctor_degraded_days": result.doctor_degraded_days,
        "issues": [asdict(x) for x in result.issues],
        "days": [asdict(x) for x in result.days],
    }


def print_result(result: SloResult) -> None:
    print("SLO checker")
    print("date: %s" % result.date)
    print("window_days: %s" % result.window_days)
    print("classification: %s" % result.classification)
    print("")
    print("| severity | code | class | check | detail | runbook |")
    print("|---|---|---|---|---|---|")
    if not result.issues:
        print("| OK | SLO000 | %s | summary | no SLO issues detected | %s#slo000 |" % (CLASS_CURRENT, RUNBOOK_PATH))
    for issue in result.issues:
        print(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                issue.severity,
                issue.code,
                issue.classification,
                issue.name,
                issue.detail.replace("|", "/"),
                issue.runbook,
            )
        )

    print("")
    print("| date | manifest | production | doctor_blocking | doctor_degraded | doctor_advisory |")
    print("|---|---|---|---:|---:|---:|")
    for item in result.days:
        print(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                item.date,
                "yes" if item.manifest_present else "no",
                "yes" if item.production_report else "no",
                item.doctor_blocking,
                item.doctor_degraded,
                item.doctor_advisory,
            )
        )


def exit_code_for(result: SloResult) -> int:
    return 1 if any(x.severity == SEV_BLOCKING for x in result.issues) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check AoV daily-monitoring SLOs.")
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument("--date", default=taipei_today(), help="Window end date YYYY-MM-DD.")
    parser.add_argument("--window-days", type=int, default=7, help="SLO window length. Default: 7.")
    parser.add_argument(
        "--max-consecutive-no-production",
        type=int,
        default=1,
        help="Allowed trailing days without production report. Default: 1.",
    )
    parser.add_argument(
        "--max-missing-manifests",
        type=int,
        default=0,
        help="Allowed manifest gaps in the window. Default: 0.",
    )
    parser.add_argument(
        "--max-doctor-degraded-days",
        type=int,
        default=2,
        help="Allowed doctor-degraded days before escalation. Default: 2.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = evaluate_slo(
            Path(args.repo_root),
            args.date,
            window_days=args.window_days,
            max_consecutive_no_production=args.max_consecutive_no_production,
            max_missing_manifests=args.max_missing_manifests,
            max_doctor_degraded_days=args.max_doctor_degraded_days,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    else:
        print_result(result)
    return exit_code_for(result)


if __name__ == "__main__":
    sys.exit(main())
