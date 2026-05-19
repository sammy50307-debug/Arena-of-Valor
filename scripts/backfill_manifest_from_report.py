"""Backfill a run manifest from an existing canonical report.

This is a recovery tool for days where the report was committed but the
manifest was not persisted by the sync path. It does not reconstruct raw or
analysis data and does not mark a report as production.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyzer.run_manifest import build_manifest, write_manifest
from check_daily_report_health import extract_metadata_mode, validate_date
import config


META_RE = re.compile(r"cache_hit:\s*(\d+)\s*/\s*(\d+).*?llm_calls:\s*(\d+)", re.IGNORECASE)


def report_path_for(repo_root: Path, date_str: str) -> Path:
    return repo_root / "data" / "reports" / ("aov_report_%s.html" % date_str)


def _report_meta(report_path: Path) -> dict:
    first_line = report_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    match = META_RE.search(first_line)
    if not match:
        return {"cache_hit": 0, "total_calls": 0, "llm_calls": 0}
    cache_hit = int(match.group(1))
    total_calls = int(match.group(2))
    llm_calls = int(match.group(3))
    return {
        "cache_hit": cache_hit,
        "l1_hits": 0,
        "l2_hits": 0,
        "apify_hits": 0,
        "llm_calls": llm_calls,
        "total_calls": total_calls,
    }


def backfill_manifest(repo_root: Path, date_str: str) -> Path:
    repo_root = repo_root.resolve()
    date_str = validate_date(date_str)
    report_path = report_path_for(repo_root, date_str)
    if not report_path.exists():
        raise FileNotFoundError("missing canonical report: %s" % report_path)

    mode = extract_metadata_mode(report_path) or "unknown"
    meta = _report_meta(report_path)
    meta["mode"] = mode
    meta["history_status"] = "unknown"

    reasons = ["manifest backfilled from canonical report only"]
    if mode != "production":
        reasons.append("mode is %s (not production)" % mode)

    try:
        report_rel = report_path.relative_to(repo_root)
    except ValueError:
        report_rel = report_path

    manifest = build_manifest(
        run_date=date_str,
        mode=mode,
        raw_path=None,
        analysis_path=None,
        report_path=report_rel,
        meta=meta,
        history_delta={"weekly_vol_pulse": {"volumes": []}, "diagnostics": {}},
        status="ok",
        error="",
        dry_run=True,
        showcase_flag=False,
        replay_source="report_metadata",
        is_backfill=True,
        gate_mode="shadow",
        eligibility_reasons=reasons,
        source_hash="report-only-%s" % date_str,
        timezone_name=getattr(config, "TIMEZONE", "Asia/Taipei"),
        source_quality={"status": "unknown", "total_posts": 0, "platform_count": 0, "platform_counts": {}, "source_count": 0, "reasons": []},
    )
    return write_manifest(repo_root / "data", manifest)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill run_manifest.json from an existing canonical report.")
    parser.add_argument("--date", required=True, help="Target date, format YYYY-MM-DD")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    args = parser.parse_args(argv)

    try:
        out = backfill_manifest(Path(args.repo_root), args.date)
    except Exception as exc:
        print("FAIL: %s: %s" % (type(exc).__name__, exc))
        return 1

    print("OK: manifest backfilled: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
