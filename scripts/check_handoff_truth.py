"""Handoff truth checker for P84.3 governance.

The checker validates only the active bootstrap packet at the top of
NEXT_SESSION_HANDOFF.md. Archive text below the archive marker is treated as
historical context and never used for current action decisions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


START_MARKER = "<!-- ACTIVE_BOOTSTRAP_START -->"
END_MARKER = "<!-- ACTIVE_BOOTSTRAP_END -->"
ARCHIVE_MARKER = "<!-- ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION -->"
RUNBOOK_PATH = "docs/OPERATIONS_RUNBOOK.md"

SEV_BLOCKING = "BLOCKING"
SEV_DEGRADED = "DEGRADED"
SEV_ADVISORY = "ADVISORY"

VALID_MODES = {"DRAFT", "FROZEN", "APPROVED", "IN_PROGRESS", "VERIFYING", "CLOSED"}
TOP_FIELDS = [
    "Status",
    "Program",
    "Current Phase",
    "Current Step",
    "Mode",
    "Latest Verified Commit",
    "Updated At",
]
ANTI_DRIFT_FIELDS = [
    "Current Phase",
    "Current Step",
    "Allowed Files",
    "Forbidden Work",
    "Exit Criteria",
    "Resume Rule",
]

ISSUE_CATALOG = {
    "marker_layout": {"code": "HND001", "name": "active bootstrap markers"},
    "top_fields": {"code": "HND002", "name": "bootstrap required fields"},
    "mode": {"code": "HND003", "name": "mode state"},
    "anti_drift": {"code": "HND004", "name": "six anti-drift fields"},
    "bootstrap_consistency": {"code": "HND005", "name": "bootstrap field consistency"},
    "archive_boundary": {"code": "HND006", "name": "archive boundary"},
    "active_operation_consistency": {"code": "HND007", "name": "active operation consistency"},
}


@dataclass
class HandoffIssue:
    code: str
    severity: str
    name: str
    detail: str
    runbook: str


@dataclass
class HandoffTruthResult:
    handoff_path: str
    active_operation_path: str
    issues: List[HandoffIssue]
    bootstrap_fields: Dict[str, str]
    anti_drift_fields: Dict[str, str]
    active_operation_fields: Dict[str, str]

    @property
    def blocking_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_BLOCKING])

    @property
    def degraded_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_DEGRADED])


def _runbook_link(code: str) -> str:
    return "%s#%s" % (RUNBOOK_PATH, code.lower())


def _issue(key: str, severity: str, detail: str) -> HandoffIssue:
    entry = ISSUE_CATALOG[key]
    return HandoffIssue(
        code=entry["code"],
        severity=severity,
        name=entry["name"],
        detail=detail,
        runbook=_runbook_link(entry["code"]),
    )


def _clean_cell(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^\*\*(.+)\*\*$", r"\1", value)
    return value.strip()


def _parse_first_table(text: str) -> Dict[str, str]:
    table_lines: List[str] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
            in_table = True
        elif in_table:
            break
    if len(table_lines) < 3:
        return {}

    result: Dict[str, str] = {}
    for line in table_lines[2:]:
        cells = [_clean_cell(cell) for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0]:
            result[cells[0]] = cells[1]
    return result


def _section(text: str, heading: str) -> str:
    marker = "## %s" % heading
    start = text.find(marker)
    if start < 0:
        return ""
    next_heading = text.find("\n## ", start + len(marker))
    if next_heading < 0:
        return text[start:]
    return text[start:next_heading]


def _phase_id(value: str) -> str:
    match = re.search(r"P\d+", value or "")
    return match.group(0) if match else ""


def _step_id(value: str) -> str:
    match = re.search(r"P\d+(?:\.\d+)+", value or "")
    return match.group(0) if match else ""


def _extract_active_block(text: str) -> Tuple[str, List[HandoffIssue]]:
    issues: List[HandoffIssue] = []
    start_count = text.count(START_MARKER)
    end_count = text.count(END_MARKER)
    archive_count = text.count(ARCHIVE_MARKER)

    if start_count != 1 or end_count != 1:
        issues.append(
            _issue(
                "marker_layout",
                SEV_BLOCKING,
                "expected exactly one active start/end marker; start=%s end=%s" % (start_count, end_count),
            )
        )
        return "", issues

    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    archive = text.find(ARCHIVE_MARKER)

    if start != 0:
        issues.append(_issue("marker_layout", SEV_BLOCKING, "active bootstrap marker must be the first content"))
    if end <= start:
        issues.append(_issue("marker_layout", SEV_BLOCKING, "active end marker must appear after active start marker"))
        return "", issues
    if archive_count != 1 or archive <= end:
        issues.append(
            _issue(
                "archive_boundary",
                SEV_BLOCKING,
                "archive marker must appear exactly once after active bootstrap; count=%s" % archive_count,
            )
        )

    return text[start : end + len(END_MARKER)], issues


def _missing_fields(fields: Dict[str, str], required: List[str]) -> List[str]:
    return [name for name in required if not str(fields.get(name, "")).strip()]


def _check_mode(fields: Dict[str, str], issues: List[HandoffIssue]) -> None:
    mode = str(fields.get("Mode", "")).strip()
    if mode not in VALID_MODES:
        issues.append(_issue("mode", SEV_BLOCKING, "Mode=%s is not a valid state" % (mode or "<missing>")))


def _check_bootstrap_consistency(
    top_fields: Dict[str, str],
    anti_fields: Dict[str, str],
    issues: List[HandoffIssue],
) -> None:
    top_phase = _phase_id(top_fields.get("Current Phase", ""))
    anti_phase = _phase_id(anti_fields.get("Current Phase", ""))
    top_step = _step_id(top_fields.get("Current Step", ""))
    anti_step = _step_id(anti_fields.get("Current Step", ""))
    mode = str(top_fields.get("Mode", "")).strip()
    anti_phase_text = str(anti_fields.get("Current Phase", ""))

    if top_phase and anti_phase and top_phase != anti_phase:
        issues.append(_issue("bootstrap_consistency", SEV_BLOCKING, "Current Phase mismatch: %s != %s" % (top_phase, anti_phase)))
    if top_step and anti_step and top_step != anti_step:
        issues.append(_issue("bootstrap_consistency", SEV_BLOCKING, "Current Step mismatch: %s != %s" % (top_step, anti_step)))
    if mode and mode not in anti_phase_text:
        issues.append(_issue("bootstrap_consistency", SEV_DEGRADED, "Mode %s not reflected in Six Anti-Drift Current Phase" % mode))


def _check_active_operation_consistency(
    top_fields: Dict[str, str],
    active_fields: Dict[str, str],
    issues: List[HandoffIssue],
) -> None:
    if not active_fields:
        issues.append(_issue("active_operation_consistency", SEV_DEGRADED, "ACTIVE_OPERATION fields missing or unreadable"))
        return

    top_phase = _phase_id(top_fields.get("Current Phase", ""))
    active_phase = _phase_id(active_fields.get("Current Phase", ""))
    top_step = _step_id(top_fields.get("Current Step", ""))
    active_step = _step_id(active_fields.get("Current Step", ""))
    top_mode = str(top_fields.get("Mode", "")).strip()
    active_mode = str(active_fields.get("Mode", "")).strip()

    if top_phase and active_phase and top_phase != active_phase:
        issues.append(_issue("active_operation_consistency", SEV_BLOCKING, "phase mismatch: handoff=%s active=%s" % (top_phase, active_phase)))
    if top_step and active_step and top_step != active_step:
        issues.append(_issue("active_operation_consistency", SEV_BLOCKING, "step mismatch: handoff=%s active=%s" % (top_step, active_step)))
    if top_mode and active_mode and top_mode != active_mode:
        issues.append(_issue("active_operation_consistency", SEV_BLOCKING, "mode mismatch: handoff=%s active=%s" % (top_mode, active_mode)))


def check_handoff_truth(
    handoff_path: Path,
    active_operation_path: Optional[Path] = None,
) -> HandoffTruthResult:
    issues: List[HandoffIssue] = []
    handoff_path = Path(handoff_path)
    active_operation_path = Path(active_operation_path) if active_operation_path else None

    text = handoff_path.read_text(encoding="utf-8", errors="replace")
    active_block, marker_issues = _extract_active_block(text)
    issues.extend(marker_issues)

    top_fields: Dict[str, str] = {}
    anti_fields: Dict[str, str] = {}
    active_fields: Dict[str, str] = {}

    if active_block:
        top_fields = _parse_first_table(active_block)
        missing_top = _missing_fields(top_fields, TOP_FIELDS)
        if missing_top:
            issues.append(_issue("top_fields", SEV_BLOCKING, "missing fields: %s" % ", ".join(missing_top)))
        _check_mode(top_fields, issues)

        anti_section = _section(active_block, "Six Anti-Drift Fields")
        anti_fields = _parse_first_table(anti_section)
        missing_anti = _missing_fields(anti_fields, ANTI_DRIFT_FIELDS)
        if missing_anti:
            issues.append(_issue("anti_drift", SEV_BLOCKING, "missing fields: %s" % ", ".join(missing_anti)))
        _check_bootstrap_consistency(top_fields, anti_fields, issues)

    if active_operation_path is not None and active_operation_path.exists():
        active_text = active_operation_path.read_text(encoding="utf-8", errors="replace")
        state_section = _section(active_text, "Current State")
        active_fields = _parse_first_table(state_section)
        _check_active_operation_consistency(top_fields, active_fields, issues)
    elif active_operation_path is not None:
        issues.append(_issue("active_operation_consistency", SEV_DEGRADED, "missing %s" % active_operation_path))

    return HandoffTruthResult(
        handoff_path=str(handoff_path),
        active_operation_path=str(active_operation_path or ""),
        issues=issues,
        bootstrap_fields=top_fields,
        anti_drift_fields=anti_fields,
        active_operation_fields=active_fields,
    )


def result_to_dict(result: HandoffTruthResult) -> Dict[str, object]:
    return {
        "handoff_path": result.handoff_path,
        "active_operation_path": result.active_operation_path,
        "issues": [asdict(issue) for issue in result.issues],
        "bootstrap_fields": result.bootstrap_fields,
        "anti_drift_fields": result.anti_drift_fields,
        "active_operation_fields": result.active_operation_fields,
    }


def print_result(result: HandoffTruthResult) -> None:
    print("Handoff truth checker")
    print("handoff: %s" % result.handoff_path)
    if result.active_operation_path:
        print("active_operation: %s" % result.active_operation_path)
    print("")
    print("| severity | code | check | detail | runbook |")
    print("|---|---|---|---|---|")
    if not result.issues:
        print("| OK | HND000 | summary | active bootstrap truth verified | %s#hnd000 |" % RUNBOOK_PATH)
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


def exit_code_for(result: HandoffTruthResult) -> int:
    return 1 if (result.blocking_count > 0 or result.degraded_count > 0) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate NEXT_SESSION_HANDOFF active bootstrap truth.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--handoff", default="NEXT_SESSION_HANDOFF.md", help="Handoff file path relative to repo root.")
    parser.add_argument(
        "--active-operation",
        default="docs/ACTIVE_OPERATION.md",
        help="ACTIVE_OPERATION file path relative to repo root. Use empty string to skip.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    active_path = (repo_root / args.active_operation) if args.active_operation else None
    result = check_handoff_truth(repo_root / args.handoff, active_path)
    if args.json:
        print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    else:
        print_result(result)
    return exit_code_for(result)


if __name__ == "__main__":
    sys.exit(main())
