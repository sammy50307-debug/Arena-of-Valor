"""Advisory generated artifact hygiene checker for P99.

The checker is intentionally path-only. It does not read file contents, mutate
the git index, delete files, or decide cleanup. By default it reports advisory
findings and exits 0; --strict converts advisory findings into exit 1 for
experiments and future promotion reviews.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEVERITY_ADVISORY = "ADVISORY"


ROOT_DEBUG_OUTPUTS = {
    "compile_errors.txt",
    "debug_output.txt",
    "diff_result.txt",
    "encoding_errors.txt",
    "err.log",
    "err.txt",
    "error.log",
    "error.txt",
    "full_diff.txt",
    "out.txt",
    "output.log",
    "run_log.txt",
    "syntax_out.txt",
    "test_handoff_out.txt",
    "ver.txt",
}

REPORT_VARIANT_RE = re.compile(r"^data/reports/.+_v\d+[^/]*\.html$", re.IGNORECASE)
REPORT_PREVIEW_RE = re.compile(r"^data/reports/PREVIEW_[^/]+\.html$", re.IGNORECASE)
REPORT_DASH_PREVIEW_RE = re.compile(r"^data/reports/.+-preview\.html$", re.IGNORECASE)


@dataclass(frozen=True)
class HygieneFinding:
    path: str
    severity: str
    category: str
    action: str
    reason: str


def _normalize(path: str) -> str:
    normalized = str(path).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def _finding(path: str, category: str, action: str, reason: str) -> HygieneFinding:
    return HygieneFinding(
        path=path,
        severity=SEVERITY_ADVISORY,
        category=category,
        action=action,
        reason=reason,
    )


def classify_path(path: str) -> Optional[HygieneFinding]:
    normalized = _normalize(path)
    lower = normalized.lower()

    if not normalized:
        return None

    if lower.startswith("scratch/"):
        return _finding(
            normalized,
            "scratch_local_artifact",
            "Unstage unless this Phase explicitly approved scratch evidence.",
            "scratch/ is local working evidence and should normally stay out of commits.",
        )

    if lower.startswith("data/enrichment_queue/"):
        return _finding(
            normalized,
            "raw_enrichment_queue",
            "Keep as artifact or document the decision before staging.",
            "raw enrichment queue data is not a stable source-of-truth commit target.",
        )

    if REPORT_PREVIEW_RE.match(normalized) or REPORT_DASH_PREVIEW_RE.match(normalized):
        return _finding(
            normalized,
            "preview_report",
            "Unstage unless this commit intentionally publishes preview evidence.",
            "preview reports are generated review artifacts, not normal source changes.",
        )

    if REPORT_VARIANT_RE.match(normalized):
        return _finding(
            normalized,
            "report_variant",
            "Require an explicit canonical/evidence decision before staging.",
            "versioned report variants are generated artifacts and can pollute history.",
        )

    if lower.startswith("ui_previews/"):
        return _finding(
            normalized,
            "ui_preview",
            "Unstage unless this Phase explicitly updates golden preview evidence.",
            "ui_previews/ contains generated or historical preview artifacts.",
        )

    if lower.startswith("backups/"):
        return _finding(
            normalized,
            "backup_artifact",
            "Unstage unless this backup is the approved artifact for this Phase.",
            "backups/ is normally local or historical evidence, not product code.",
        )

    if "/" not in normalized and lower in ROOT_DEBUG_OUTPUTS:
        return _finding(
            normalized,
            "root_debug_output",
            "Unstage and move the useful conclusion into docs if needed.",
            "root debug outputs are quarantine candidates; P99 only warns about them.",
        )

    if lower == ".gitignore" or lower.startswith(".github/workflows/"):
        return _finding(
            normalized,
            "decision_required",
            "Requires explicit 主公 approval and usually a separate Phase.",
            "ignore rules and workflows can affect deployment or future automation.",
        )

    return None


def find_hygiene_advisories(paths: Iterable[str]) -> list[HygieneFinding]:
    findings: list[HygieneFinding] = []
    seen: set[str] = set()
    for path in paths:
        normalized = _normalize(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        finding = classify_path(normalized)
        if finding is not None:
            findings.append(finding)
    return findings


def staged_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff --cached failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _print_table(findings: list[HygieneFinding]) -> None:
    if not findings:
        print("No generated artifact hygiene advisories.")
        return

    print("| severity | category | path | action | reason |")
    print("|---|---|---|---|---|")
    for item in findings:
        print(
            "| %s | %s | %s | %s | %s |"
            % (item.severity, item.category, item.path, item.action, item.reason)
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Advisory generated artifact hygiene checker.")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--paths", nargs="*", help="Explicit paths to check instead of staged git paths.")
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when advisories are present.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    paths = args.paths if args.paths is not None else staged_paths(repo_root)
    findings = find_hygiene_advisories(paths)

    if args.json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        _print_table(findings)

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
