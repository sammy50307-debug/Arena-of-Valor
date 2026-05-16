"""Tests for scripts/check_daily_report_health.py (P70.2)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_daily_report_health as health


DATE = "2026-05-16"


def _write_repo(
    root: Path,
    date_str: str = DATE,
    mode: str = "production",
    landing_date: str = DATE,
    with_report: bool = True,
    landing_href: str | None = None,
) -> None:
    reports = root / "data" / "reports"
    reports.mkdir(parents=True)
    if with_report:
        (reports / ("aov_report_%s.html" % date_str)).write_text(
            f"<!-- cache_hit: 2/3 (66%) | llm_calls: 1 | mode: {mode} -->\n<html></html>\n",
            encoding="utf-8",
        )
    href = landing_href or ("data/reports/aov_report_%s.html" % landing_date)
    (root / "index.html").write_text(
        '<a href="%s" class="main-btn">進入最新戰報</a>\n' % href,
        encoding="utf-8",
    )


def _status_map(results):
    return {r.name: r.status for r in results}


def _detail_map(results):
    return {r.name: r.detail for r in results}


def test_valid_report_passes(tmp_path: Path):
    _write_repo(tmp_path)
    results = health.run_checks(tmp_path, DATE)
    assert not any(r.failed for r in results)
    assert _status_map(results)["canonical report"] == "PASS"
    assert _status_map(results)["metadata mode"] == "PASS"
    assert _status_map(results)["landing main link"] == "PASS"
    assert _status_map(results)["landing target mode"] == "PASS"


def test_missing_report_fails(tmp_path: Path):
    _write_repo(tmp_path, with_report=False)
    results = health.run_checks(tmp_path, DATE)
    assert _status_map(results)["canonical report"] == "FAIL"
    assert "missing" in _detail_map(results)["canonical report"]


def test_non_production_mode_fails_by_default(tmp_path: Path):
    _write_repo(tmp_path, mode="showcase_forced")
    results = health.run_checks(tmp_path, DATE)
    assert _status_map(results)["metadata mode"] == "FAIL"
    assert "expected=production" in _detail_map(results)["metadata mode"]
    assert _status_map(results)["landing target mode"] == "FAIL"


def test_expected_mode_any_accepts_showcase(tmp_path: Path):
    _write_repo(tmp_path, mode="showcase")
    results = health.run_checks(tmp_path, DATE, expected_mode="any")
    assert _status_map(results)["metadata mode"] == "PASS"


def test_landing_must_point_to_same_date(tmp_path: Path):
    _write_repo(tmp_path, landing_date="2026-05-15")
    results = health.run_checks(tmp_path, DATE)
    assert _status_map(results)["landing main link"] == "FAIL"
    assert "expected=data/reports/aov_report_2026-05-16.html" in _detail_map(results)["landing main link"]


def test_landing_target_missing_fails(tmp_path: Path):
    _write_repo(tmp_path, landing_href="data/reports/aov_report_2099-01-01.html")
    results = health.run_checks(tmp_path, DATE)
    assert _status_map(results)["landing target mode"] == "FAIL"
    assert "landing target missing" in _detail_map(results)["landing target mode"]


def test_use_latest_production_selects_right_target(tmp_path: Path):
    reports = tmp_path / "data" / "reports"
    reports.mkdir(parents=True)
    (reports / "aov_report_2026-05-16.html").write_text(
        "<!-- cache_hit: 0/0 (0%) | llm_calls: 0 | mode: showcase -->\n<html></html>\n",
        encoding="utf-8",
    )
    (reports / "aov_report_2026-05-15.html").write_text(
        "<!-- cache_hit: 0/0 (0%) | llm_calls: 0 | mode: production -->\n<html></html>\n",
        encoding="utf-8",
    )
    (tmp_path / "index.html").write_text(
        '<a href="data/reports/aov_report_2026-05-15.html" class="main-btn">進入最新戰報</a>\n',
        encoding="utf-8",
    )

    results = health.run_checks(tmp_path, DATE, use_latest_production=True)
    assert not any(r.failed for r in results)
    assert _status_map(results)["canonical report"] == "PASS"
    assert _status_map(results)["metadata mode"] == "PASS"
    assert _status_map(results)["landing main link"] == "PASS"
    assert _status_map(results)["landing target mode"] == "PASS"


def test_use_latest_production_fails_when_none(tmp_path: Path):
    _write_repo(tmp_path, mode="showcase")
    results = health.run_checks(tmp_path, DATE, use_latest_production=True)
    assert len(results) == 1
    assert results[0].name == "latest production report"
    assert results[0].status == "FAIL"


def test_invalid_date_rejected():
    with pytest.raises(ValueError):
        health.validate_date("20260516")


def test_cli_returns_failure_for_missing_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    _write_repo(tmp_path, with_report=False)
    rc = health.main(["--repo-root", str(tmp_path), "--date", DATE])
    captured = capsys.readouterr()
    assert rc == 1
    assert "canonical report" in captured.out
