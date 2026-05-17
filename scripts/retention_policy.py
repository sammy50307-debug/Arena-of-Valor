"""Retention policy dry-run inventory for P84.1 governance.

This script is intentionally advisory-only. It reports files/directories that
would need manual archive review, but it never deletes or moves data.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


REPORT_RE = re.compile(r"^aov_report_(\d{4}-\d{2}-\d{2})(?:_.+)?\.html$")
CANONICAL_REPORT_RE = re.compile(r"^aov_report_\d{4}-\d{2}-\d{2}\.html$")
DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

MODE = "dry-run"
WILL_DELETE = False


@dataclass
class PolicySummary:
    policy: str
    path: str
    retention_days: str
    action: str
    status: str
    item_count: int
    total_bytes: int
    candidate_count: int
    note: str


@dataclass
class RetentionCandidate:
    policy: str
    path: str
    item_type: str
    age_days: int
    size_bytes: int
    reason: str
    action: str


def _parse_date(value: str) -> Optional[date]:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _today(today: Optional[str]) -> date:
    if today:
        parsed = _parse_date(today)
        if parsed is None:
            raise ValueError("today must use YYYY-MM-DD")
        return parsed
    return datetime.now().date()


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total


def _mtime_date(path: Path) -> Optional[date]:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date()
    except OSError:
        return None


def _age_days(today_value: date, item_date: Optional[date]) -> int:
    if item_date is None:
        return 0
    return max(0, (today_value - item_date).days)


def _summary(
    policy: str,
    path: str,
    retention_days: str,
    action: str,
    status: str,
    item_count: int,
    total_bytes: int,
    candidate_count: int,
    note: str,
) -> PolicySummary:
    return PolicySummary(
        policy=policy,
        path=path,
        retention_days=retention_days,
        action=action,
        status=status,
        item_count=item_count,
        total_bytes=total_bytes,
        candidate_count=candidate_count,
        note=note,
    )


def _candidate(
    repo_root: Path,
    policy: str,
    path: Path,
    item_type: str,
    age_days: int,
    size_bytes: int,
    reason: str,
) -> RetentionCandidate:
    return RetentionCandidate(
        policy=policy,
        path=_rel(repo_root, path),
        item_type=item_type,
        age_days=age_days,
        size_bytes=size_bytes,
        reason=reason,
        action="manual_archive_review_only",
    )


def _scan_reports(repo_root: Path, today_value: date) -> Tuple[List[PolicySummary], List[RetentionCandidate]]:
    reports_dir = repo_root / "data" / "reports"
    rel = "data/reports"
    summaries: List[PolicySummary] = []
    candidates: List[RetentionCandidate] = []
    if not reports_dir.exists():
        return [
            _summary(
                "reports",
                rel,
                "canonical=180, variants=30",
                "manual_archive_review_only",
                "missing",
                0,
                0,
                0,
                "directory missing; nothing to inventory",
            )
        ], []

    canonical_count = 0
    variant_count = 0
    total_bytes = 0
    canonical_candidates = 0
    variant_candidates = 0

    for report in reports_dir.glob("*.html"):
        if not report.is_file():
            continue
        size = _path_size(report)
        total_bytes += size
        match = REPORT_RE.match(report.name)
        item_date = _parse_date(match.group(1)) if match else _mtime_date(report)
        age = _age_days(today_value, item_date)
        if CANONICAL_REPORT_RE.match(report.name):
            canonical_count += 1
            if age > 180:
                canonical_candidates += 1
                candidates.append(
                    _candidate(
                        repo_root,
                        "reports_canonical",
                        report,
                        "file",
                        age,
                        size,
                        "canonical report older than 180 days",
                    )
                )
        else:
            variant_count += 1
            if age > 30:
                variant_candidates += 1
                candidates.append(
                    _candidate(
                        repo_root,
                        "reports_variants",
                        report,
                        "file",
                        age,
                        size,
                        "preview/versioned report older than 30 days",
                    )
                )

    summaries.append(
        _summary(
            "reports_canonical",
            rel,
            "180",
            "manual_archive_review_only",
            "ok",
            canonical_count,
            total_bytes,
            canonical_candidates,
            "canonical production reports are never auto-deleted",
        )
    )
    summaries.append(
        _summary(
            "reports_variants",
            rel,
            "30",
            "manual_archive_review_only",
            "ok",
            variant_count,
            total_bytes,
            variant_candidates,
            "preview/versioned reports are dry-run candidates only",
        )
    )
    return summaries, candidates


def _scan_date_dirs(
    repo_root: Path,
    root_rel: str,
    policy: str,
    retention_days: int,
    note: str,
    today_value: date,
) -> Tuple[PolicySummary, List[RetentionCandidate]]:
    root = repo_root / root_rel
    candidates: List[RetentionCandidate] = []
    if not root.exists():
        return (
            _summary(policy, root_rel, str(retention_days), "manual_archive_review_only", "missing", 0, 0, 0, "directory missing; nothing to inventory"),
            [],
        )

    item_count = 0
    total_bytes = 0
    for item in root.iterdir():
        if not item.is_dir() or not DATE_DIR_RE.match(item.name):
            continue
        item_count += 1
        size = _path_size(item)
        total_bytes += size
        age = _age_days(today_value, _parse_date(item.name))
        if age > retention_days:
            candidates.append(
                _candidate(
                    repo_root,
                    policy,
                    item,
                    "directory",
                    age,
                    size,
                    "%s older than %s days" % (policy, retention_days),
                )
            )
    return (
        _summary(
            policy,
            root_rel,
            str(retention_days),
            "manual_archive_review_only",
            "ok",
            item_count,
            total_bytes,
            len(candidates),
            note,
        ),
        candidates,
    )


def _scan_quarantine(
    repo_root: Path,
    roots: Iterable[str],
    today_value: date,
) -> Tuple[List[PolicySummary], List[RetentionCandidate]]:
    summaries: List[PolicySummary] = []
    candidates: List[RetentionCandidate] = []
    protected_names = {"README.md", ".gitkeep"}

    for root_rel in roots:
        root = repo_root / root_rel
        if not root.exists():
            summaries.append(
                _summary(
                    "quarantine",
                    root_rel,
                    "90",
                    "manual_archive_review_only",
                    "missing",
                    0,
                    0,
                    0,
                    "directory missing; nothing to inventory",
                )
            )
            continue

        item_count = 0
        total_bytes = 0
        candidate_count = 0
        for item in root.rglob("*"):
            if not item.is_file() or item.name in protected_names:
                continue
            item_count += 1
            size = _path_size(item)
            total_bytes += size
            age = _age_days(today_value, _mtime_date(item))
            if age > 90:
                candidate_count += 1
                candidates.append(
                    _candidate(
                        repo_root,
                        "quarantine",
                        item,
                        "file",
                        age,
                        size,
                        "quarantine file older than 90 days",
                    )
                )
        summaries.append(
            _summary(
                "quarantine",
                root_rel,
                "90",
                "manual_archive_review_only",
                "ok",
                item_count,
                total_bytes,
                candidate_count,
                "quarantine artifacts are dry-run candidates only",
            )
        )

    return summaries, candidates


def _scan_cache(repo_root: Path, today_value: date) -> Tuple[List[PolicySummary], List[RetentionCandidate], List[str]]:
    summaries: List[PolicySummary] = []
    candidates: List[RetentionCandidate] = []
    warnings: List[str] = []
    cache_file = repo_root / "data" / "llm_cache.json"
    cache_rel = "data/llm_cache.json"

    if cache_file.exists():
        size = _path_size(cache_file)
        if size > 5 * 1024 * 1024:
            warnings.append("%s is larger than 5 MB; review CacheManager max entries" % cache_rel)
        summaries.append(
            _summary(
                "llm_cache",
                cache_rel,
                "managed by CacheManager TTL/max_entries",
                "keep_file_enforce_internal_lru",
                "ok",
                1,
                size,
                0,
                "cache file is versioned state; do not delete via retention dry-run",
            )
        )
    else:
        summaries.append(
            _summary(
                "llm_cache",
                cache_rel,
                "managed by CacheManager TTL/max_entries",
                "keep_file_enforce_internal_lru",
                "missing",
                0,
                0,
                0,
                "cache file missing; not a deletion candidate",
            )
        )

    backup = repo_root / "data" / "llm_cache.json.bak"
    if backup.exists():
        size = _path_size(backup)
        age = _age_days(today_value, _mtime_date(backup))
        candidate_count = 0
        if age > 30:
            candidate_count = 1
            candidates.append(
                _candidate(
                    repo_root,
                    "llm_cache_backup",
                    backup,
                    "file",
                    age,
                    size,
                    "cache backup older than 30 days",
                )
            )
        summaries.append(
            _summary(
                "llm_cache_backup",
                "data/llm_cache.json.bak",
                "30",
                "manual_archive_review_only",
                "ok",
                1,
                size,
                candidate_count,
                "migration backup is dry-run candidate only",
            )
        )

    return summaries, candidates, warnings


def _scan_raw_analysis(repo_root: Path) -> PolicySummary:
    data_dir = repo_root / "data"
    if not data_dir.exists():
        return _summary("raw_analysis_snapshots", "data/raw_*.json,data/analysis_*.json", "manual review", "protect", "missing", 0, 0, 0, "data directory missing")
    items = list(data_dir.glob("raw_*.json")) + list(data_dir.glob("analysis_*.json"))
    return _summary(
        "raw_analysis_snapshots",
        "data/raw_*.json,data/analysis_*.json",
        "manual review",
        "protect",
        "ok",
        len(items),
        sum(_path_size(item) for item in items),
        0,
        "raw/analysis snapshots are protected from automated retention",
    )


def collect_inventory(repo_root: Path, today: Optional[str] = None, max_candidates: int = 25) -> Dict[str, object]:
    repo_root = Path(repo_root).resolve()
    today_value = _today(today)
    summaries: List[PolicySummary] = []
    candidates: List[RetentionCandidate] = []
    warnings: List[str] = []

    report_summaries, report_candidates = _scan_reports(repo_root, today_value)
    summaries.extend(report_summaries)
    candidates.extend(report_candidates)

    runs_summary, runs_candidates = _scan_date_dirs(
        repo_root,
        "data/runs",
        "run_manifests",
        180,
        "run manifests preserve publish/debug truth; dry-run candidates only",
        today_value,
    )
    summaries.append(runs_summary)
    candidates.extend(runs_candidates)

    bundle_summary, bundle_candidates = _scan_date_dirs(
        repo_root,
        "data/debug_bundles",
        "debug_bundles",
        30,
        "debug bundles may contain diagnostic paths; dry-run candidates only",
        today_value,
    )
    summaries.append(bundle_summary)
    candidates.extend(bundle_candidates)

    quarantine_summaries, quarantine_candidates = _scan_quarantine(
        repo_root,
        ["data/quarantine", "data/_quarantine"],
        today_value,
    )
    summaries.extend(quarantine_summaries)
    candidates.extend(quarantine_candidates)

    cache_summaries, cache_candidates, cache_warnings = _scan_cache(repo_root, today_value)
    summaries.extend(cache_summaries)
    candidates.extend(cache_candidates)
    warnings.extend(cache_warnings)

    summaries.append(_scan_raw_analysis(repo_root))

    candidates.sort(key=lambda item: (item.policy, item.path))
    visible_candidates = candidates[:max(0, max_candidates)]

    return {
        "mode": MODE,
        "dry_run": True,
        "will_delete": WILL_DELETE,
        "today": today_value.strftime("%Y-%m-%d"),
        "repo_root": str(repo_root),
        "policy_count": len(summaries),
        "candidate_count": len(candidates),
        "candidates_truncated": len(candidates) > len(visible_candidates),
        "summaries": [asdict(item) for item in summaries],
        "candidates": [asdict(item) for item in visible_candidates],
        "warnings": warnings,
    }


def print_inventory(inventory: Dict[str, object]) -> None:
    print("Retention policy inventory")
    print("mode: %s" % inventory["mode"])
    print("dry_run: %s" % str(inventory["dry_run"]).lower())
    print("will_delete: %s" % str(inventory["will_delete"]).lower())
    print("today: %s" % inventory["today"])
    print("")
    print("| policy | path | retention | items | bytes | candidates | action | status |")
    print("|---|---|---|---:|---:|---:|---|---|")
    for summary in inventory["summaries"]:  # type: ignore[index]
        print(
            "| {policy} | {path} | {retention_days} | {item_count} | {total_bytes} | {candidate_count} | {action} | {status} |".format(
                **summary
            )
        )

    warnings = inventory["warnings"]  # type: ignore[index]
    if warnings:
        print("")
        print("Warnings:")
        for warning in warnings:
            print("- %s" % warning)

    candidates = inventory["candidates"]  # type: ignore[index]
    if candidates:
        print("")
        print("Dry-run candidates (manual review only):")
        print("| policy | path | age_days | bytes | reason |")
        print("|---|---|---:|---:|---|")
        for candidate in candidates:
            print(
                "| {policy} | {path} | {age_days} | {size_bytes} | {reason} |".format(
                    **candidate
                )
            )
        if inventory["candidates_truncated"]:
            print("")
            print("candidate list truncated; rerun with --max-candidates for more")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run retention inventory for AoV data artifacts.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--today", default=None, help="Override today's date in YYYY-MM-DD for deterministic checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--max-candidates", type=int, default=25, help="Maximum candidates to print/include. Default: 25.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        inventory = collect_inventory(Path(args.repo_root), today=args.today, max_candidates=args.max_candidates)
    except ValueError as exc:
        parser.error(str(exc))
        return 2
    if args.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    else:
        print_inventory(inventory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
