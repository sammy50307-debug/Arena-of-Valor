"""Daily report health checker for GitHub Actions.

P70.2: verify that a daily run produced the canonical report, injected
metadata, updated the landing page, and optionally left no uncommitted report
changes behind.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
META_MODE_RE = re.compile(r"mode:\s*([a-zA-Z0-9_:-]+)")
MAIN_BTN_RE = re.compile(r'<a\s+href="([^"]+)"\s+class="main-btn"', re.IGNORECASE)


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def taipei_today() -> str:
    """Return today's date in Asia/Taipei without depending on zoneinfo."""
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")


def validate_date(date_str: str) -> str:
    """Validate YYYY-MM-DD and return the normalized value."""
    if not DATE_RE.match(date_str):
        raise ValueError("date must use YYYY-MM-DD format")
    parsed = datetime.strptime(date_str, "%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d")


def report_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / "data" / "reports" / ("aov_report_%s.html" % date_str)


def index_path(repo_root: Path) -> Path:
    return repo_root / "index.html"


def extract_metadata_mode(report_file: Path) -> Optional[str]:
    """Extract `mode: ...` from the first metadata comment line."""
    try:
        first_line = report_file.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except IndexError:
        return None
    match = META_MODE_RE.search(first_line)
    if not match:
        return None
    return match.group(1).strip()


def extract_landing_main_href(index_file: Path) -> Optional[str]:
    content = index_file.read_text(encoding="utf-8", errors="replace")
    match = MAIN_BTN_RE.search(content)
    if not match:
        return None
    return match.group(1).strip()


def git_dirty_for_paths(repo_root: Path, paths: Iterable[str]) -> str:
    cmd = ["git", "status", "--porcelain", "--"] + list(paths)
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return "git status failed: %s" % (proc.stderr.strip() or proc.returncode)
    return proc.stdout.strip()


def run_checks(
    repo_root: Path,
    date_str: str,
    expected_mode: str = "production",
    check_git_clean: bool = False,
) -> List[CheckResult]:
    """Run health checks and return structured results."""
    normalized_date = validate_date(date_str)
    repo_root = repo_root.resolve()
    expected_report = report_path(repo_root, normalized_date)
    landing = index_path(repo_root)
    rel_report = "data/reports/aov_report_%s.html" % normalized_date
    results: List[CheckResult] = []

    if expected_report.exists():
        results.append(CheckResult("canonical report", "PASS", str(expected_report)))
    else:
        results.append(CheckResult("canonical report", "FAIL", "missing %s" % expected_report))

    if expected_report.exists():
        mode = extract_metadata_mode(expected_report)
        if mode is None:
            results.append(CheckResult("metadata mode", "FAIL", "metadata comment missing mode"))
        elif expected_mode != "any" and mode != expected_mode:
            results.append(
                CheckResult(
                    "metadata mode",
                    "FAIL",
                    "mode=%s, expected=%s" % (mode, expected_mode),
                )
            )
        else:
            results.append(CheckResult("metadata mode", "PASS", "mode=%s" % mode))

    if landing.exists():
        href = extract_landing_main_href(landing)
        if href == rel_report:
            results.append(CheckResult("landing main link", "PASS", href))
        else:
            results.append(
                CheckResult(
                    "landing main link",
                    "FAIL",
                    "href=%s, expected=%s" % (href or "<missing>", rel_report),
                )
            )
    else:
        results.append(CheckResult("landing main link", "FAIL", "missing %s" % landing))

    if check_git_clean:
        dirty = git_dirty_for_paths(
            repo_root,
            [rel_report, "index.html", "data/llm_cache.json"],
        )
        if dirty:
            results.append(CheckResult("git clean", "FAIL", dirty.replace("\n", " | ")))
        else:
            results.append(CheckResult("git clean", "PASS", "report/index/cache clean"))

    return results


def print_results(date_str: str, repo_root: Path, results: List[CheckResult]) -> None:
    print("Daily report health check")
    print("date: %s" % date_str)
    print("repo: %s" % repo_root.resolve())
    print("")
    print("| check | status | detail |")
    print("|---|---|---|")
    for result in results:
        print("| %s | %s | %s |" % (result.name, result.status, result.detail.replace("|", "/")))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check AoV daily report health.")
    parser.add_argument("--date", default=taipei_today(), help="Report date in YYYY-MM-DD; default is Asia/Taipei today.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument(
        "--expected-mode",
        default="production",
        help="Expected metadata mode. Use 'any' to accept any mode.",
    )
    parser.add_argument(
        "--check-git-clean",
        action="store_true",
        help="Fail if report/index/cache still have uncommitted changes.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        date_str = validate_date(args.date)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    results = run_checks(
        Path(args.repo_root),
        date_str,
        expected_mode=args.expected_mode,
        check_git_clean=args.check_git_clean,
    )
    print_results(date_str, Path(args.repo_root), results)
    return 1 if any(result.failed for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
