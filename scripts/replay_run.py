"""Replay/backfill a daily report from existing analysis JSON (P81 baseline)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyzer.run_manifest import build_manifest, write_manifest
from reporter.generator import ReportGenerator
import config
from debug_bundle import write_debug_bundle


def validate_date(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")


def analysis_path_for(date_str: str) -> Path:
    return config.DATA_DIR / ("analysis_%s.json" % date_str.replace("-", ""))


def raw_path_for(date_str: str) -> Path:
    return config.DATA_DIR / ("raw_%s.json" % date_str.replace("-", ""))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_analysis_summary(summary: dict) -> Tuple[bool, str]:
    if not isinstance(summary, dict):
        return False, "analysis payload must be object"
    required = ("overall", "sentiment_distribution")
    missing = [k for k in required if k not in summary]
    if missing:
        return False, "missing required keys: %s" % ", ".join(missing)
    if not isinstance(summary.get("overall"), dict):
        return False, "overall must be object"
    if not isinstance(summary.get("sentiment_distribution"), dict):
        return False, "sentiment_distribution must be object"
    return True, ""


def quarantine_analysis_file(data_dir: Path, source: Path, reason: str, detail: str) -> Path:
    qdir = data_dir / "quarantine" / reason
    qdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    target = qdir / ("%s__%s.json" % (source.stem, stamp))
    shutil.copy2(str(source), str(target))
    source.unlink(missing_ok=True)
    meta_path = target.with_suffix(".meta.json")
    meta = {
        "original_path": str(source),
        "quarantined_path": str(target),
        "quarantined_at": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "detail": detail,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Replay/backfill report from analysis JSON.")
    parser.add_argument("--date", required=True, help="Target date, format YYYY-MM-DD")
    parser.add_argument("--check-health", action="store_true", help="Run health checker after replay.")
    parser.add_argument(
        "--expected-mode",
        default="any",
        help="Expected mode for health check (default: any).",
    )
    parser.add_argument(
        "--debug-bundle",
        action="store_true",
        help="Always emit a debug bundle JSON after replay.",
    )
    args = parser.parse_args(argv)

    date_str = validate_date(args.date)
    analysis_path = analysis_path_for(date_str)
    raw_path = raw_path_for(date_str)
    report_path: Optional[Path] = None
    manifest_out: Optional[Path] = None
    health_checks = []

    def _emit_bundle(status: str, error: str, force: bool = False, extra: Optional[dict] = None) -> Optional[Path]:
        if not force and not args.debug_bundle:
            return None
        out = write_debug_bundle(
            data_dir=config.DATA_DIR,
            repo_root=PROJECT_ROOT,
            run_date=date_str,
            status=status,
            error=error,
            analysis_path=analysis_path if analysis_path.exists() else None,
            raw_path=raw_path if raw_path.exists() else None,
            report_path=report_path,
            manifest_path=manifest_out,
            health_checks=health_checks,
            extra=extra or {},
        )
        print("INFO: debug bundle written: %s" % out)
        return out

    if not analysis_path.exists():
        print("FAIL: missing analysis file: %s" % analysis_path)
        _emit_bundle("failed", "missing analysis file", force=True)
        return 1

    try:
        summary = load_json(analysis_path)
    except Exception as exc:
        qpath = quarantine_analysis_file(
            config.DATA_DIR,
            analysis_path,
            reason="invalid_json",
            detail="%s: %s" % (type(exc).__name__, exc),
        )
        print("FAIL: invalid analysis JSON, quarantined to %s" % qpath)
        _emit_bundle("failed", "analysis invalid JSON", force=True, extra={"quarantine_path": str(qpath)})
        return 1

    ok, reason = validate_analysis_summary(summary)
    if not ok:
        qpath = quarantine_analysis_file(
            config.DATA_DIR,
            analysis_path,
            reason="analysis_schema_violation",
            detail=reason,
        )
        print("FAIL: invalid analysis schema (%s), quarantined to %s" % (reason, qpath))
        _emit_bundle(
            "failed",
            "analysis schema violation: %s" % reason,
            force=True,
            extra={"quarantine_path": str(qpath)},
        )
        return 1

    summary["date"] = date_str
    summary.setdefault("_meta", {})
    summary["_meta"]["replay"] = True
    summary["_meta"]["replay_source"] = "analysis_json"
    summary["_meta"]["is_backfill"] = True

    analyzed_posts = []
    if raw_path.exists():
        try:
            raw_items = load_json(raw_path)
            if isinstance(raw_items, list):
                analyzed_posts = [{"post": item, "analysis": {}} for item in raw_items if isinstance(item, dict)]
        except Exception:
            analyzed_posts = []

    generator = ReportGenerator()
    report_path = generator.generate(summary, analyzed_posts)
    print("OK: replay report generated: %s" % report_path)

    manifest = build_manifest(
        run_date=date_str,
        mode=summary.get("_meta", {}).get("mode", "unknown"),
        raw_path=raw_path if raw_path.exists() else None,
        analysis_path=analysis_path,
        report_path=report_path,
        meta=summary.get("_meta", {}),
        history_delta=summary.get("history_delta"),
        status="ok",
        error="",
        dry_run=True,
        showcase_flag=False,
        replay_source="analysis_json",
        is_backfill=True,
    )
    manifest_out = write_manifest(config.DATA_DIR, manifest)
    print("OK: run manifest written: %s" % manifest_out)

    if args.check_health:
        sys.path.insert(0, str((Path(__file__).resolve().parent)))
        from check_daily_report_health import run_checks

        health_checks = run_checks(
            Path("."),
            date_str,
            expected_mode=args.expected_mode,
            check_git_clean=False,
        )
        failed = [c for c in health_checks if c.failed]
        for c in health_checks:
            print("%s: %s - %s" % (c.name, c.status, c.detail))
        if failed:
            _emit_bundle(
                "failed",
                "health checks failed (%d)" % len(failed),
                force=True,
                extra={"expected_mode": args.expected_mode},
            )
            return 1

    _emit_bundle("ok", "", force=False, extra={"expected_mode": args.expected_mode, "checked_health": args.check_health})

    return 0


if __name__ == "__main__":
    sys.exit(main())
