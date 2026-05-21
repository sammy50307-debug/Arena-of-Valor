"""Daily report health checker for GitHub Actions.

P70.2: verify that a daily run produced the canonical report, injected
metadata, updated the landing page, and optionally left no uncommitted report
changes behind.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analyzer.run_context import build_run_context
from analyzer.run_manifest import ALLOWED_QUALITY_TIERS, PUBLISHABLE_QUALITY_TIERS


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
META_MODE_RE = re.compile(r"mode:\s*([a-zA-Z0-9_:-]+)")
META_TIER_RE = re.compile(r"quality_tier:\s*([a-zA-Z0-9_:-]+)")
MAIN_BTN_RE = re.compile(r'<a\s+href="([^"]+)"\s+class="main-btn"', re.IGNORECASE)
CANONICAL_REPORT_RE = re.compile(r"^aov_report_\d{4}-\d{2}-\d{2}\.html$")


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def taipei_today() -> str:
    """Return today's daily-run date in Asia/Taipei."""
    return build_run_context().run_date


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


def manifest_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / "data" / "runs" / date_str / "run_manifest.json"


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


def extract_metadata_quality_tier(report_file: Path) -> Optional[str]:
    """Extract `quality_tier: ...` from the first metadata comment line."""
    try:
        first_line = report_file.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except IndexError:
        return None
    match = META_TIER_RE.search(first_line)
    if not match:
        return None
    return match.group(1).strip()


def extract_landing_main_href(index_file: Path) -> Optional[str]:
    content = index_file.read_text(encoding="utf-8", errors="replace")
    match = MAIN_BTN_RE.search(content)
    if not match:
        return None
    return match.group(1).strip()


def latest_production_report(repo_root: Path) -> Optional[Path]:
    reports_dir = repo_root / "data" / "reports"
    candidates = [p for p in reports_dir.glob("aov_report_*.html") if CANONICAL_REPORT_RE.match(p.name)]
    candidates.sort(key=lambda p: p.name, reverse=True)
    for report in candidates:
        if extract_metadata_mode(report) == "production":
            return report
    return None


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
    use_latest_production: bool = False,
    check_landing: bool = True,
    expected_report_path: Optional[Path] = None,
) -> List[CheckResult]:
    """Run health checks and return structured results."""
    repo_root = repo_root.resolve()
    normalized_date: Optional[str] = None
    expected_report: Optional[Path] = None
    rel_report: Optional[str] = None

    if expected_report_path is not None:
        expected_report = expected_report_path.resolve()
        try:
            rel_report = str(expected_report.relative_to(repo_root)).replace("\\", "/")
        except ValueError:
            rel_report = str(expected_report)
        normalized_date = expected_report.stem.replace("aov_report_", "")
    elif use_latest_production:
        expected_report = latest_production_report(repo_root)
        if expected_report is None:
            return [CheckResult("latest production report", "FAIL", "no production canonical report found")]
        normalized_date = expected_report.name.replace("aov_report_", "").replace(".html", "")
        rel_report = "data/reports/%s" % expected_report.name
    else:
        normalized_date = validate_date(date_str)
        expected_report = report_path(repo_root, normalized_date)
        rel_report = "data/reports/aov_report_%s.html" % normalized_date

    landing = index_path(repo_root)
    results: List[CheckResult] = []
    manifest_date: Optional[str] = None
    try:
        manifest_date = validate_date(date_str)
    except ValueError:
        manifest_date = normalized_date if normalized_date and DATE_RE.match(normalized_date) else None

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

        tier = extract_metadata_quality_tier(expected_report)
        if tier is None:
            results.append(CheckResult("metadata quality tier", "WARN", "metadata comment missing quality_tier"))
        elif tier not in ALLOWED_QUALITY_TIERS:
            results.append(CheckResult("metadata quality tier", "FAIL", "quality_tier=%s is invalid" % tier))
        else:
            status = "PASS" if tier in PUBLISHABLE_QUALITY_TIERS else "WARN"
            results.append(CheckResult("metadata quality tier", status, "quality_tier=%s" % tier))

    if manifest_date:
        manifest_file = manifest_path(repo_root, manifest_date)
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            except Exception as exc:
                results.append(
                    CheckResult(
                        "core contract",
                        "WARN",
                        "manifest unreadable: %s: %s" % (type(exc).__name__, exc),
                    )
                )
            else:
                quality = manifest.get("quality", {}) if isinstance(manifest, dict) else {}
                core_contract = quality.get("core_contract") if isinstance(quality, dict) else None
                tier = quality.get("tier") if isinstance(quality, dict) else None
                analysis_source = quality.get("analysis_source") if isinstance(quality, dict) else None
                llm_coverage = quality.get("llm_coverage") if isinstance(quality, dict) else None
                if tier is None:
                    results.append(CheckResult("quality tier", "WARN", "quality.tier missing"))
                elif tier not in ALLOWED_QUALITY_TIERS:
                    results.append(CheckResult("quality tier", "FAIL", "quality.tier=%s is invalid" % tier))
                else:
                    detail = "tier=%s analysis_source=%s llm_coverage=%s" % (
                        tier,
                        analysis_source or "unknown",
                        llm_coverage or "unknown",
                    )
                    status = "PASS" if tier in PUBLISHABLE_QUALITY_TIERS else "WARN"
                    results.append(CheckResult("quality tier", status, detail))
                if not isinstance(core_contract, dict):
                    results.append(CheckResult("core contract", "WARN", "quality.core_contract missing"))
                else:
                    status = str(core_contract.get("status", "unknown"))
                    reasons = core_contract.get("reasons", [])
                    detail = (
                        "status=%s total_posts=%s platform_count=%s source_count=%s "
                        "has_report=%s has_analysis=%s reasons=%s"
                        % (
                            status,
                            core_contract.get("total_posts", 0),
                            core_contract.get("platform_count", 0),
                            core_contract.get("source_count", 0),
                            core_contract.get("has_report", False),
                            core_contract.get("has_analysis", False),
                            reasons,
                        )
                    )
                    if status == "pass":
                        results.append(CheckResult("core contract", "PASS", detail))
                    else:
                        results.append(CheckResult("core contract", "WARN", detail))

    if check_landing and landing.exists():
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
    elif check_landing:
        results.append(CheckResult("landing main link", "FAIL", "missing %s" % landing))

    if check_landing and landing.exists() and rel_report and expected_mode == "production":
        href = extract_landing_main_href(landing)
        if href:
            landing_report = (repo_root / href).resolve()
            if landing_report.exists():
                landing_mode = extract_metadata_mode(landing_report)
                if landing_mode != "production":
                    results.append(
                        CheckResult(
                            "landing target mode",
                            "FAIL",
                            "mode=%s for %s, expected=production" % ((landing_mode or "<missing>"), href),
                        )
                    )
                else:
                    results.append(CheckResult("landing target mode", "PASS", "mode=production"))
            else:
                results.append(CheckResult("landing target mode", "FAIL", "landing target missing: %s" % href))
        else:
            results.append(CheckResult("landing target mode", "FAIL", "landing main-btn href missing"))

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
    parser.add_argument(
        "--use-latest-production",
        action="store_true",
        help="Use the latest canonical report with metadata mode=production as target.",
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
        use_latest_production=args.use_latest_production,
    )
    print_results(date_str, Path(args.repo_root), results)
    return 1 if any(result.failed for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
