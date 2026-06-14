"""Replay/backfill a daily report from existing analysis JSON (P81 baseline).

P111 self-heal（--heal-if-missing）：CI 偵測 canonical 報告缺漏時自動重產。
契約（與 cron 同源，勿擅改）：重產 candidate(promote=False) → 跑與 main.py:773/780
逐位元相同的發布閘門（run_checks 參數見 main.py:132-139 + analyzer.run_manifest.should_promote）
→ 通過才 promote，否則 no-op + ::warning:: 降級 L4。零 LLM、零重爬、不繞品質閘門。
改 should_promote / run_checks 參數 / 本流程任一處，需重審 L5 同源性與零額度前提。
"""

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

from analyzer.run_manifest import (
    build_manifest,
    write_manifest,
    manifest_path,
    is_publishable_quality_tier,
    should_promote,
)
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
        "--heal-if-missing",
        action="store_true",
        help="P111 self-heal：canonical 報告缺漏才重產，過同源閘門才 promote（否則 no-op 降級 L4）。",
    )
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
    heal = args.heal_if_missing
    promoted = False

    if heal:
        # ── P111 self-heal gate（與 cron 逐位元同源；契約見模組 docstring）──
        # 統一 repo_root：一律從 config 推導（config.DATA_DIR.parent），讓 canonical 偵測 / 閘門 /
        # landing 與 generate/promote 的輸出位置（config.REPORTS_DIR）同源；測試 monkeypatch config 即可整條隔離。
        from check_daily_report_health import report_path as _canonical_for
        repo_root = config.DATA_DIR.parent
        canonical = _canonical_for(repo_root, date_str)
        if canonical.exists():
            # report 已在 → 非缺漏，零副作用收手（抗重入）
            print("INFO: self-heal no-op: canonical report already exists: %s" % canonical)
            return 0

        tier = summary.get("_meta", {}).get("quality_tier", "")
        if not is_publishable_quality_tier(tier):
            # tier 非可發布（含空/unknown）→ 不重產發布，降級 L4
            print(
                "::warning::self-heal no-op: quality_tier=%s not publishable, staying L4"
                % (tier or "<empty>")
            )
            return 0

        candidate = generator.generate(summary, analyzed_posts, promote=False)
        report_path = candidate
        if candidate.stem != ("aov_report_%s" % date_str):
            print(
                "FAIL: self-heal candidate stem mismatch: %s (expected aov_report_%s)"
                % (candidate.name, date_str)
            )
            _emit_bundle("failed", "candidate stem mismatch", force=True)
            return 1

        # 跑與 main.py:132-139 逐位元相同的發布閘門（尤其 check_landing=False）
        from check_daily_report_health import run_checks as _gate_checks_fn
        gate_checks = _gate_checks_fn(
            repo_root,
            date_str,
            expected_mode="production",
            check_git_clean=False,
            check_landing=False,
            expected_report_path=candidate,
        )
        gate_reasons = [c for c in gate_checks if c.failed]

        if should_promote(True, tier, len(gate_reasons)):
            report_path = generator.promote_candidate(
                candidate, date_str,
                output_dir=config.REPORTS_DIR,
                index_file=repo_root / "index.html",
            )
            promoted = True
            print("OK: self-heal promoted canonical report: %s" % report_path)
        else:
            print(
                "::warning::self-heal no-op: candidate failed publish gate (%d reasons), staying L4"
                % len(gate_reasons)
            )
            for c in gate_reasons:
                print("  gate reason: %s: %s" % (c.name, c.detail))
    else:
        report_path = generator.generate(summary, analyzed_posts)
        print("OK: replay report generated: %s" % report_path)

    # P112：self-heal 會覆蓋同路徑 manifest，先讀既有失敗 manifest 的 error 保留為 pre_heal_error
    # （否則 generate 失敗原因隨覆蓋遺失，只剩 ~90 天 CI log）。讀檔以 try/except 全包覆——
    # 讀失敗→空字串繼續 heal（恢復永遠優先於診斷記錄，不阻斷 self-heal）。
    pre_heal_error = ""
    if heal:
        try:
            _existing_mf = manifest_path(config.DATA_DIR, date_str)
            if _existing_mf.exists():
                _prev = json.loads(_existing_mf.read_text(encoding="utf-8"))
                if _prev.get("status") == "failed":
                    pre_heal_error = str(_prev.get("error", ""))[:500]
        except Exception:
            pre_heal_error = ""

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
        self_heal=heal,
        promoted=(promoted if heal else None),
        pre_heal_error=pre_heal_error,
    )
    manifest_out = write_manifest(config.DATA_DIR, manifest)
    print("OK: run manifest written: %s" % manifest_out)

    if args.check_health and (not heal or promoted):
        # heal 模式僅在真正 promote 後才 gate 住（no-op/降級不阻斷）；統一 repo_root
        sys.path.insert(0, str((Path(__file__).resolve().parent)))
        from check_daily_report_health import run_checks

        health_checks = run_checks(
            repo_root if heal else Path("."),
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
