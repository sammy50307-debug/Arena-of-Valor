"""Advisory known issue guard index checker for P101.

The checker reads only the P101 guard index document. It does not inspect raw
reports, logs, queues, generated report bodies, or secrets. By default it exits
0 and prints advisory findings; --strict converts findings into exit 1 for
future promotion experiments.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = "docs/KNOWN_ISSUE_GUARD_INDEX.md"
SEVERITY_ADVISORY = "ADVISORY"
START_MARKER = "<!-- GUARD_INDEX_START -->"
END_MARKER = "<!-- GUARD_INDEX_END -->"

REQUIRED_COLUMNS = [
    "Risk ID",
    "Issue",
    "Human Doc",
    "Machine Guard",
    "Focused Command",
    "State",
    "Gap",
    "Next Action",
]

REQUIRED_ENTRIES: dict[str, dict[str, object]] = {
    "R-016": {
        "tokens": [
            "scripts/slo_checker.py",
            "scripts/system_doctor.py",
            "scripts/cost_cache_governance.py",
            "Monitoring",
        ],
        "machine_required": True,
    },
    "R-017": {
        "tokens": [
            "docs/CONTENT_TRUST_KNOWN_ISSUES.md",
            "configs/content_trust_known_issues.yaml",
            "scripts/check_report_content_trust.py",
            "Monitoring",
        ],
        "machine_required": True,
    },
    "R-018": {
        "tokens": [
            "docs/PHASE_97_RTK_EVALUATION.md",
            "docs/RISK_REGISTRY.md",
        ],
        "machine_required": False,
        "gap_tokens": ["missing-machine-guard", "human-only"],
    },
    "R-019": {
        "tokens": [
            "docs/PHASE_98_AUDIT.md",
            "scripts/check_generated_artifact_hygiene.py",
            "scripts/check_root_legacy_hygiene.py",
            "scripts/check_known_issue_guard_index.py",
        ],
        "machine_required": True,
    },
    "R-020": {
        "tokens": [
            "docs/GENERATED_ARTIFACT_POLICY.md",
            "scripts/check_generated_artifact_hygiene.py",
            "tests/test_generated_artifact_hygiene.py",
        ],
        "machine_required": True,
    },
    "R-021": {
        "tokens": [
            "docs/ROOT_LEGACY_QUARANTINE.md",
            "scripts/check_root_legacy_hygiene.py",
            "tests/test_root_legacy_hygiene.py",
        ],
        "machine_required": True,
    },
    "R-022": {
        "tokens": [
            "docs/PHASE_101_PLAN.md",
            "docs/KNOWN_ISSUE_GUARD_INDEX.md",
            "scripts/check_known_issue_guard_index.py",
            "tests/test_known_issue_guard_index.py",
        ],
        "machine_required": True,
    },
    "GOV-HANDOFF": {
        "tokens": [
            "NEXT_SESSION_HANDOFF.md",
            "docs/ACTIVE_OPERATION.md",
            "scripts/check_handoff_truth.py",
            "scripts/governance_doctor.py",
        ],
        "machine_required": True,
    },
}


@dataclass(frozen=True)
class GuardIndexFinding:
    severity: str
    category: str
    risk_id: str
    action: str
    reason: str


def _finding(category: str, risk_id: str, action: str, reason: str) -> GuardIndexFinding:
    return GuardIndexFinding(
        severity=SEVERITY_ADVISORY,
        category=category,
        risk_id=risk_id,
        action=action,
        reason=reason,
    )


def _normalize_header(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells)


def _normalize_text(value: str) -> str:
    return value.replace("\\", "/").lower()


def _machine_guard_is_empty(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "-", "n/a", "none", "na"}


def _extract_table(text: str) -> tuple[list[dict[str, str]], list[GuardIndexFinding]]:
    findings: list[GuardIndexFinding] = []
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        findings.append(
            _finding(
                "marker_layout",
                "INDEX",
                "Keep exactly one GUARD_INDEX_START and GUARD_INDEX_END block.",
                "guard index markers are missing or duplicated",
            )
        )
        return [], findings

    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    if end <= start:
        findings.append(
            _finding(
                "marker_layout",
                "INDEX",
                "Place GUARD_INDEX_END after GUARD_INDEX_START.",
                "guard index marker order is invalid",
            )
        )
        return [], findings

    lines = [line.strip() for line in text[start:end].splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        findings.append(
            _finding(
                "missing_table",
                "INDEX",
                "Add the required markdown table inside the guard index markers.",
                "guard index table is missing",
            )
        )
        return [], findings

    headers = _split_row(lines[0])
    normalized_headers = [_normalize_header(header) for header in headers]
    required_normalized = [_normalize_header(column) for column in REQUIRED_COLUMNS]
    for column, normalized in zip(REQUIRED_COLUMNS, required_normalized):
        if normalized not in normalized_headers:
            findings.append(
                _finding(
                    "missing_column",
                    "INDEX",
                    "Add the `%s` column to the guard index table." % column,
                    "required column is missing",
                )
            )
    if findings:
        return [], findings

    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        cells = _split_row(line)
        if _is_separator(cells):
            continue
        if len(cells) != len(headers):
            findings.append(
                _finding(
                    "malformed_row",
                    "INDEX",
                    "Avoid `|` inside cells and keep every row aligned with the header.",
                    "row has %s cells but header has %s" % (len(cells), len(headers)),
                )
            )
            continue
        rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows, findings


def check_index(index_path: Path) -> list[GuardIndexFinding]:
    index_path = Path(index_path)
    findings: list[GuardIndexFinding] = []
    if not index_path.exists():
        return [
            _finding(
                "missing_index_file",
                "INDEX",
                "Create %s before running P101 runtime checks." % index_path,
                "known issue guard index file is missing",
            )
        ]

    text = index_path.read_text(encoding="utf-8", errors="replace")
    rows, parse_findings = _extract_table(text)
    findings.extend(parse_findings)
    if parse_findings:
        return findings

    rows_by_id = {row.get("Risk ID", "").strip(): row for row in rows}

    for risk_id, requirements in REQUIRED_ENTRIES.items():
        row = rows_by_id.get(risk_id)
        if row is None:
            findings.append(
                _finding(
                    "missing_required_entry",
                    risk_id,
                    "Add a row for %s to the guard index." % risk_id,
                    "required risk/source is not indexed",
                )
            )
            continue

        combined = _normalize_text(" ".join(row.values()))
        for token in requirements.get("tokens", []):
            if _normalize_text(str(token)) not in combined:
                findings.append(
                    _finding(
                        "missing_required_token",
                        risk_id,
                        "Add `%s` to the %s row." % (token, risk_id),
                        "required guard/doc/command token is missing",
                    )
                )

        machine_guard = row.get("Machine Guard", "")
        gap = _normalize_text(row.get("Gap", ""))
        if bool(requirements.get("machine_required")) and _machine_guard_is_empty(machine_guard):
            findings.append(
                _finding(
                    "missing_machine_guard",
                    risk_id,
                    "Do not mark %s as guarded without listing a machine guard." % risk_id,
                    "machine guard is required but missing",
                )
            )

        if _machine_guard_is_empty(machine_guard) and not (
            "missing-machine-guard" in gap or "human-only" in gap
        ):
            findings.append(
                _finding(
                    "human_only_gap_unmarked",
                    risk_id,
                    "Mark human-only rows with `missing-machine-guard` or `human-only` in Gap.",
                    "empty machine guard can create false confidence",
                )
            )

        for gap_token in requirements.get("gap_tokens", []):
            if _normalize_text(str(gap_token)) not in gap:
                findings.append(
                    _finding(
                        "missing_gap_token",
                        risk_id,
                        "Add `%s` to the Gap column for %s." % (gap_token, risk_id),
                        "required gap marker is missing",
                    )
                )

    return findings


def _print_table(findings: list[GuardIndexFinding]) -> None:
    if not findings:
        print("No known issue guard index advisories.")
        return

    print("| severity | category | risk_id | action | reason |")
    print("|---|---|---|---|---|")
    for item in findings:
        print(
            "| %s | %s | %s | %s | %s |"
            % (item.severity, item.category, item.risk_id, item.action, item.reason)
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Advisory known issue guard index checker.")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--index", help="Index file to check. Defaults to docs/KNOWN_ISSUE_GUARD_INDEX.md.")
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when advisories are present.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    index_path = Path(args.index) if args.index else repo_root / DEFAULT_INDEX
    findings = check_index(index_path)

    if args.json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        _print_table(findings)

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
