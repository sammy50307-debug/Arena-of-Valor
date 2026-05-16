from __future__ import annotations

import json
from pathlib import Path

import scripts.system_doctor as doctor
from analyzer.run_manifest import build_manifest, write_manifest


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


def _write_manifest(repo_root: Path, date_str: str, mode: str = "production") -> None:
    data_dir = repo_root / "data"
    manifest = build_manifest(
        run_date=date_str,
        mode=mode,
        raw_path=data_dir / ("raw_%s.json" % date_str.replace("-", "")),
        analysis_path=data_dir / ("analysis_%s.json" % date_str.replace("-", "")),
        report_path=data_dir / "reports" / ("aov_report_%s.html" % date_str),
        meta={"history_status": "ok"},
        history_delta={
            "weekly_vol_pulse": {"volumes": [1, 2, 3]},
            "diagnostics": {"source_dates": ["2026-05-15"], "missing_dates": ["2026-05-14"]},
        },
        status="ok",
    )
    write_manifest(data_dir, manifest)


def test_system_doctor_local_passes_with_production_manifest(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")
    _write_manifest(tmp_path, date_str, mode="production")

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert result.blocking_count == 0
    assert all(x.code.startswith("DOC") for x in result.issues)
    assert all(x.runbook.startswith("docs/OPERATIONS_RUNBOOK.md#") for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_blocks_when_manifest_missing(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert result.blocking_count > 0
    assert any(x.code == "DOC001" for x in result.issues)
    assert doctor.exit_code_for(result) == 1


def test_system_doctor_local_does_not_fail_on_degraded(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="showcase_forced")
    _write_manifest(tmp_path, date_str, mode="showcase_forced")

    result = doctor.run_doctor(tmp_path, date_str, profile="local", require_production=False)

    assert result.blocking_count == 0
    assert result.degraded_count > 0
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_ci_fails_on_degraded(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="showcase_forced")
    _write_manifest(tmp_path, date_str, mode="showcase_forced")

    result = doctor.run_doctor(tmp_path, date_str, profile="ci", require_production=True)

    assert result.degraded_count > 0
    assert doctor.exit_code_for(result) == 1


def test_system_doctor_failure_links_latest_debug_bundle(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="showcase_forced")
    _write_manifest(tmp_path, date_str, mode="showcase_forced")

    bundle_dir = tmp_path / "data" / "debug_bundles" / date_str
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle = bundle_dir / "debug_bundle_20260516T010203Z.json"
    bundle.write_text(
        json.dumps(
            {
                "status": "failed",
                "error": "health checks failed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="ci", require_production=True)

    assert doctor.exit_code_for(result) == 1
    assert result.debug_bundle_path.endswith(bundle.name)
    assert any(x.code == "DOC011" for x in result.issues)
