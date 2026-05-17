from __future__ import annotations

import json
from pathlib import Path

from analyzer.run_manifest import (
    build_manifest,
    manifest_path,
    validate_manifest,
    write_manifest,
)


SOURCE_HASH = "abcdef1234567890"


def test_build_manifest_basic_fields(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        meta={"cache_hit": 2, "l1_hits": 1, "l2_hits": 1, "llm_calls": 3, "total_calls": 5, "history_status": "ok"},
        history_delta={"weekly_vol_pulse": {"volumes": [1, 2, 3]}},
        status="ok",
        source_hash=SOURCE_HASH,
        scheduled_utc="2026-05-15T16:00:00Z",
    )

    assert manifest["schema_version"] == 2
    assert manifest["run_date"] == "2026-05-16"
    assert manifest["run_date_taipei"] == "2026-05-16"
    assert manifest["timezone"] == "Asia/Taipei"
    assert manifest["scheduled_utc"] == "2026-05-15T16:00:00Z"
    assert manifest["source_hash"] == SOURCE_HASH
    assert manifest["source_hash_version"] == 1
    assert manifest["run_id"] == "2026-05-16-production-abcdef123456"
    assert manifest["mode"] == "production"
    assert manifest["publish_eligible"] is True
    assert manifest["metrics"]["cache_hit"] == 2
    assert manifest["history"]["weekly_points"] == 3
    assert manifest["history"]["source_dates"] == []
    assert manifest["replay_source"] == ""
    assert manifest["is_backfill"] is False
    assert manifest["eligibility"]["gate_mode"] == "shadow"
    assert manifest["eligibility"]["decision"] == "eligible"
    assert manifest["eligibility"]["reasons"] == []
    ok, errors = validate_manifest(manifest)
    assert ok, errors


def test_write_manifest_creates_expected_path(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="showcase_forced",
        raw_path=None,
        analysis_path=None,
        report_path=None,
    )
    out = write_manifest(tmp_path, manifest)
    assert out == manifest_path(tmp_path, "2026-05-16")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["mode"] == "showcase_forced"


def test_build_manifest_with_history_dates_and_backfill(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="showcase_forced",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        meta={"history_status": "degraded"},
        history_delta={
            "weekly_vol_pulse": {"volumes": [3, 5]},
            "diagnostics": {
                "source_dates": ["2026-05-15", "bad-date", "2026-05-14"],
                "missing_dates": ["2026-05-13", 123],
            },
        },
        status="ok",
        replay_source="analysis_json",
        is_backfill=True,
    )
    assert manifest["history"]["source_dates"] == ["2026-05-15", "2026-05-14"]
    assert manifest["history"]["missing_dates"] == ["2026-05-13"]
    assert manifest["replay_source"] == "analysis_json"
    assert manifest["is_backfill"] is True
    ok, errors = validate_manifest(manifest)
    assert ok, errors


def test_validate_manifest_accepts_legacy_schema_v1():
    legacy = {
        "schema_version": 1,
        "generated_at": "2026-05-16T00:00:00Z",
        "run_date": "2026-05-16",
        "status": "ok",
        "error": "",
        "mode": "production",
        "publish_eligible": True,
        "dry_run": False,
        "showcase_flag": False,
        "paths": {"raw": "", "analysis": "", "report": ""},
        "metrics": {"cache_hit": 0, "l1_hits": 0, "l2_hits": 0, "apify_hits": 0, "llm_calls": 0, "total_calls": 0},
        "history": {"status": "ok", "weekly_points": 0, "source_dates": [], "missing_dates": []},
        "replay_source": "",
        "is_backfill": False,
        "eligibility": {
            "gate_mode": "shadow",
            "decision": "eligible",
            "reasons": [],
            "blocking_enforced": False,
            "shadow_blocked": False,
        },
    }

    ok, errors = validate_manifest(legacy)
    assert ok, errors


def test_validate_manifest_rejects_bad_run_id(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        source_hash=SOURCE_HASH,
    )
    manifest["run_id"] = "bad"
    ok, errors = validate_manifest(manifest)
    assert not ok
    assert any("run_id" in msg for msg in errors)


def test_same_day_rerun_identity_is_stable_for_same_source_hash(tmp_path: Path):
    kwargs = {
        "run_date": "2026-05-16",
        "mode": "production",
        "raw_path": tmp_path / "raw_20260516.json",
        "analysis_path": tmp_path / "analysis_20260516.json",
        "report_path": tmp_path / "aov_report_2026-05-16.html",
        "source_hash": SOURCE_HASH,
    }

    first = build_manifest(**kwargs)
    second = build_manifest(**kwargs)

    assert first["run_id"] == second["run_id"]


def test_same_day_rerun_identity_changes_for_different_source_hash(tmp_path: Path):
    first = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        source_hash="111111111111aaaa",
    )
    second = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16_v2.html",
        source_hash="222222222222bbbb",
    )

    assert first["run_id"] != second["run_id"]


def test_validate_manifest_rejects_invalid_publish_eligible(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        status="failed",
        error="boom",
    )
    manifest["publish_eligible"] = True
    ok, errors = validate_manifest(manifest)
    assert not ok
    assert any("publish_eligible" in msg for msg in errors)


def test_build_manifest_shadow_gate_with_reasons_blocks_eligibility(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        gate_mode="shadow",
        eligibility_reasons=["landing main link mismatch"],
        status="ok",
    )
    assert manifest["publish_eligible"] is False
    assert manifest["eligibility"]["decision"] == "ineligible"
    assert manifest["eligibility"]["shadow_blocked"] is True
    assert manifest["eligibility"]["blocking_enforced"] is False
    ok, errors = validate_manifest(manifest)
    assert ok, errors


def test_build_manifest_blocking_gate_marks_blocking(tmp_path: Path):
    manifest = build_manifest(
        run_date="2026-05-16",
        mode="production",
        raw_path=tmp_path / "raw_20260516.json",
        analysis_path=tmp_path / "analysis_20260516.json",
        report_path=tmp_path / "aov_report_2026-05-16.html",
        gate_mode="blocking",
        eligibility_reasons=["metadata mode mismatch"],
        status="ok",
    )
    assert manifest["publish_eligible"] is False
    assert manifest["eligibility"]["gate_mode"] == "blocking"
    assert manifest["eligibility"]["blocking_enforced"] is True
    ok, errors = validate_manifest(manifest)
    assert ok, errors
