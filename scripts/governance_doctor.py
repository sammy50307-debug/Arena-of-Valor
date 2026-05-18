"""Runbook and risk-registry governance checker for P84.4.

The checker validates two long-term governance contracts:

1. Issue codes emitted by governance scripts must have matching runbook anchors.
2. Risk registry entries must stay in a section that matches their status.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


RUNBOOK_PATH = "docs/OPERATIONS_RUNBOOK.md"
RISK_REGISTRY_PATH = "docs/RISK_REGISTRY.md"
DEFAULT_ISSUE_SOURCE_PATHS = [
    "scripts/system_doctor.py",
    "scripts/slo_checker.py",
    "scripts/check_handoff_truth.py",
    "scripts/governance_doctor.py",
    "scripts/cost_cache_governance.py",
]

SEV_BLOCKING = "BLOCKING"
SEV_DEGRADED = "DEGRADED"
SEV_ADVISORY = "ADVISORY"

ISSUE_CATALOG = {
    "runbook_missing_anchor": {"code": "GOV001", "name": "runbook missing anchor"},
    "runbook_duplicate_anchor": {"code": "GOV002", "name": "runbook duplicate anchor"},
    "risk_state_mismatch": {"code": "GOV003", "name": "risk registry state mismatch"},
    "risk_duplicate_id": {"code": "GOV004", "name": "risk registry duplicate id"},
}

ISSUE_CODE_RE = re.compile(r"\b(?:DOC|SLO|HND|GOV|CCG)\d{3}\b")
RUNBOOK_ANCHOR_RE = re.compile(r'id="([a-z]{3}\d{3})"')
RISK_HEADING_RE = re.compile(r"^###\s+(R-\d{3})", re.MULTILINE)
STATUS_RE = re.compile(r"^\-\s+\*\*狀態\*\*[:：]\s*(.+)$", re.MULTILINE)


@dataclass
class GovernanceIssue:
    code: str
    severity: str
    name: str
    detail: str
    runbook: str


@dataclass
class GovernanceResult:
    runbook_path: str
    risk_registry_path: str
    issue_source_paths: List[str]
    issue_codes: List[str]
    runbook_anchors: List[str]
    risk_ids: List[str]
    issues: List[GovernanceIssue]

    @property
    def blocking_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_BLOCKING])

    @property
    def degraded_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_DEGRADED])


def _runbook_link(code: str) -> str:
    return "%s#%s" % (RUNBOOK_PATH, code.lower())


def _issue(key: str, severity: str, detail: str) -> GovernanceIssue:
    entry = ISSUE_CATALOG[key]
    return GovernanceIssue(
        code=entry["code"],
        severity=severity,
        name=entry["name"],
        detail=detail,
        runbook=_runbook_link(entry["code"]),
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_issue_codes(repo_root: Path, source_paths: Sequence[str]) -> Dict[str, List[str]]:
    codes: Dict[str, List[str]] = {}
    for raw_path in source_paths:
        path = repo_root / raw_path
        if not path.exists():
            continue
        text = _read_text(path)
        for code in ISSUE_CODE_RE.findall(text):
            codes.setdefault(code, [])
            if raw_path not in codes[code]:
                codes[code].append(raw_path)
    return codes


def _extract_runbook_anchor_counts(text: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for anchor in RUNBOOK_ANCHOR_RE.findall(text):
        counts[anchor.lower()] = counts.get(anchor.lower(), 0) + 1
    return counts


def _find_section(text: str, heading_fragment: str) -> str:
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if line.startswith("## ") and heading_fragment in line:
            start = index
            break
    if start < 0:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end])


def _risk_blocks(section_text: str) -> List[Dict[str, str]]:
    matches = list(RISK_HEADING_RE.finditer(section_text))
    blocks: List[Dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_text)
        blocks.append({"id": match.group(1), "text": section_text[start:end]})
    return blocks


def _status_value(block_text: str) -> str:
    match = STATUS_RE.search(block_text)
    return match.group(1).strip() if match else ""


def _is_open_status(status: str) -> bool:
    return "Open" in status


def _is_closed_status(status: str) -> bool:
    return ("已" in status) or ("Closed" in status) or ("closed" in status)


def _check_runbook_mapping(
    repo_root: Path,
    runbook_path: Path,
    source_paths: Sequence[str],
    issues: List[GovernanceIssue],
) -> Dict[str, object]:
    if not runbook_path.exists():
        issues.append(_issue("runbook_missing_anchor", SEV_BLOCKING, "missing runbook file: %s" % runbook_path))
        return {"issue_codes": {}, "anchors": {}}

    source_codes = _extract_issue_codes(repo_root, source_paths)
    anchors = _extract_runbook_anchor_counts(_read_text(runbook_path))

    for code in sorted(source_codes):
        if code.lower() not in anchors:
            issues.append(
                _issue(
                    "runbook_missing_anchor",
                    SEV_BLOCKING,
                    "%s emitted by %s has no runbook anchor"
                    % (code, ", ".join(source_codes[code])),
                )
            )

    duplicates = sorted(anchor.upper() for anchor, count in anchors.items() if count > 1)
    if duplicates:
        issues.append(
            _issue(
                "runbook_duplicate_anchor",
                SEV_BLOCKING,
                "duplicate anchors: %s" % ", ".join(duplicates),
            )
        )

    return {"issue_codes": source_codes, "anchors": anchors}


def _check_risk_registry(risk_registry_path: Path, issues: List[GovernanceIssue]) -> List[str]:
    if not risk_registry_path.exists():
        issues.append(_issue("risk_state_mismatch", SEV_BLOCKING, "missing risk registry: %s" % risk_registry_path))
        return []

    text = _read_text(risk_registry_path)
    all_ids = RISK_HEADING_RE.findall(text)
    seen: Dict[str, int] = {}
    for risk_id in all_ids:
        seen[risk_id] = seen.get(risk_id, 0) + 1
    duplicates = sorted(risk_id for risk_id, count in seen.items() if count > 1)
    if duplicates:
        issues.append(_issue("risk_duplicate_id", SEV_BLOCKING, "duplicate risk ids: %s" % ", ".join(duplicates)))

    open_section = _find_section(text, "開放風險")
    closed_section = _find_section(text, "已關閉風險")
    if not open_section or not closed_section:
        issues.append(_issue("risk_state_mismatch", SEV_BLOCKING, "missing Open or Closed risk section"))
        return all_ids

    for block in _risk_blocks(open_section):
        status = _status_value(block["text"])
        if not status:
            issues.append(_issue("risk_state_mismatch", SEV_BLOCKING, "%s missing status" % block["id"]))
        elif not _is_open_status(status):
            issues.append(
                _issue(
                    "risk_state_mismatch",
                    SEV_BLOCKING,
                    "%s is under Open section but status is %s" % (block["id"], status),
                )
            )

    for block in _risk_blocks(closed_section):
        status = _status_value(block["text"])
        if not status:
            issues.append(_issue("risk_state_mismatch", SEV_BLOCKING, "%s missing status" % block["id"]))
        elif not _is_closed_status(status):
            issues.append(
                _issue(
                    "risk_state_mismatch",
                    SEV_BLOCKING,
                    "%s is under Closed section but status is %s" % (block["id"], status),
                )
            )

    return all_ids


def check_governance(
    repo_root: Path,
    issue_source_paths: Optional[Sequence[str]] = None,
    runbook_path: Optional[Path] = None,
    risk_registry_path: Optional[Path] = None,
) -> GovernanceResult:
    repo_root = Path(repo_root).resolve()
    source_paths = list(issue_source_paths or DEFAULT_ISSUE_SOURCE_PATHS)
    runbook = Path(runbook_path) if runbook_path else repo_root / RUNBOOK_PATH
    risk_registry = Path(risk_registry_path) if risk_registry_path else repo_root / RISK_REGISTRY_PATH
    issues: List[GovernanceIssue] = []

    mapping = _check_runbook_mapping(repo_root, runbook, source_paths, issues)
    risk_ids = _check_risk_registry(risk_registry, issues)

    issue_codes = sorted(mapping.get("issue_codes", {}).keys())
    anchors = sorted(mapping.get("anchors", {}).keys())

    return GovernanceResult(
        runbook_path=str(runbook),
        risk_registry_path=str(risk_registry),
        issue_source_paths=source_paths,
        issue_codes=issue_codes,
        runbook_anchors=anchors,
        risk_ids=risk_ids,
        issues=issues,
    )


def result_to_dict(result: GovernanceResult) -> Dict[str, object]:
    return {
        "runbook_path": result.runbook_path,
        "risk_registry_path": result.risk_registry_path,
        "issue_source_paths": result.issue_source_paths,
        "issue_codes": result.issue_codes,
        "runbook_anchors": result.runbook_anchors,
        "risk_ids": result.risk_ids,
        "issues": [asdict(issue) for issue in result.issues],
    }


def print_result(result: GovernanceResult) -> None:
    print("Governance doctor")
    print("runbook: %s" % result.runbook_path)
    print("risk_registry: %s" % result.risk_registry_path)
    print("")
    print("| severity | code | check | detail | runbook |")
    print("|---|---|---|---|---|")
    if not result.issues:
        print("| OK | GOV000 | summary | runbook and risk registry governance verified | %s#gov000 |" % RUNBOOK_PATH)
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


def exit_code_for(result: GovernanceResult) -> int:
    return 1 if (result.blocking_count > 0 or result.degraded_count > 0) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate runbook and risk-registry governance.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--runbook", default=RUNBOOK_PATH, help="Runbook path relative to repo root.")
    parser.add_argument(
        "--risk-registry",
        default=RISK_REGISTRY_PATH,
        help="Risk registry path relative to repo root.",
    )
    parser.add_argument(
        "--issue-source",
        action="append",
        default=None,
        help="Issue-code source path relative to repo root. May be repeated.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    result = check_governance(
        repo_root,
        issue_source_paths=args.issue_source,
        runbook_path=repo_root / args.runbook,
        risk_registry_path=repo_root / args.risk_registry,
    )
    if args.json:
        print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    else:
        print_result(result)
    return exit_code_for(result)


if __name__ == "__main__":
    sys.exit(main())
