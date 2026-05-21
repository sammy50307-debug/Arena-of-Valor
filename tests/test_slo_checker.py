from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analyzer.run_manifest import build_manifest, build_source_quality, write_manifest
from scripts import slo_checker


def _write_report_and_index(repo_root: Path, date_str: str, mode: str = "production") -> None:
    reports = repo_root / "data" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / ("aov_report_%s.html" % date_str)
    report.write_text(
        "<!-- cache_hit: 1/1 (100%%) | llm_calls: 0 | mode: %s -->\n<html></html>\n" % mode,
        encoding="utf-8",
    )
    (repo_root / "index.html").write_text(
        '<a href="data/reports/aov_report_%s.html" class="main-btn">進入最新戰報</a>\n' % date_str,
        encoding="utf-8",
    )


def _write_manifest(repo_root: Path, date_str: str, mode: str = "production", status: str = "ok") -> None:
    data_dir = repo_root / "data"
    source_quality = build_source_quality(
        [
            {"platform": "dcard", "source": "dcard.tw"},
            {"platform": "bahamut", "source": "forum.gamer.com.tw"},
        ]
    )
    manifest = build_manifest(
        run_date=date_str,
        mode=mode,
        raw_path=data_dir / ("raw_%s.json" % date_str.replace("-", "")),
        analysis_path=data_dir / ("analysis_%s.json" % date_str.replace("-", "")),
        report_path=data_dir / "reports" / ("aov_report_%s.html" % date_str),
        meta={"history_status": "ok"},
        history_delta={
            "weekly_vol_pulse": {"volumes": [1, 2, 3]},
            "diagnostics": {"source_dates": ["2026-05-14"], "missing_dates": []},
        },
        status=status,
        source_quality=source_quality,
    )
    write_manifest(data_dir, manifest)


def _write_day(repo_root: Path, date_str: str, mode: str = "production", manifest_mode: Optional[str] = None) -> None:
    _write_report_and_index(repo_root, date_str, mode=mode)
    _write_manifest(repo_root, date_str, mode=manifest_mode or mode)


def _issue_codes(result):
    return {issue.code for issue in result.issues}


def test_slo_passes_when_window_has_production_and_manifests(tmp_path: Path):
    _write_day(tmp_path, "2026-05-16")
    _write_day(tmp_path, "2026-05-17")

    result = slo_checker.evaluate_slo(tmp_path, "2026-05-17", window_days=2)

    assert result.consecutive_no_production == 0
    assert result.missing_manifest_count == 0
    assert result.issues == []
    assert slo_checker.exit_code_for(result) == 0


def test_slo_escalates_missing_manifest(tmp_path: Path):
    _write_day(tmp_path, "2026-05-17")
    _write_report_and_index(tmp_path, "2026-05-18", mode="production")

    result = slo_checker.evaluate_slo(tmp_path, "2026-05-18", window_days=2)

    assert "SLO002" in _issue_codes(result)
    assert result.missing_manifest_count == 1
    assert slo_checker.exit_code_for(result) == 1


def test_slo_escalates_consecutive_no_production(tmp_path: Path):
    _write_day(tmp_path, "2026-05-15")
    _write_manifest(tmp_path, "2026-05-16", mode="showcase")
    _write_manifest(tmp_path, "2026-05-17", mode="showcase")

    result = slo_checker.evaluate_slo(
        tmp_path,
        "2026-05-17",
        window_days=3,
        max_consecutive_no_production=1,
        max_missing_manifests=0,
    )

    assert "SLO001" in _issue_codes(result)
    assert result.consecutive_no_production == 2


def test_slo_escalates_doctor_degraded_budget(tmp_path: Path):
    _write_day(tmp_path, "2026-05-15", mode="showcase")
    _write_day(tmp_path, "2026-05-16", mode="showcase")
    _write_day(tmp_path, "2026-05-17", mode="production")

    result = slo_checker.evaluate_slo(
        tmp_path,
        "2026-05-17",
        window_days=3,
        max_consecutive_no_production=3,
        max_doctor_degraded_days=1,
    )

    assert "SLO003" in _issue_codes(result)
    assert result.doctor_degraded_days == 2
    assert slo_checker.exit_code_for(result) == 0


def test_cli_json_contains_slo_issue(tmp_path: Path, capsys):
    _write_day(tmp_path, "2026-05-17")
    rc = slo_checker.main(
        [
            "--repo-root",
            str(tmp_path),
            "--date",
            "2026-05-18",
            "--window-days",
            "2",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 1
    assert payload["missing_manifest_count"] == 1
    assert any(issue["code"] == "SLO002" for issue in payload["issues"])
