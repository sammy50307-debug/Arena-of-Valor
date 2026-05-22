from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import scripts.system_doctor as doctor
from analyzer.llm_budget import LLMBudgetManager
from analyzer.run_manifest import build_manifest, build_source_quality, write_manifest


def _write_report_and_index(
    repo_root: Path,
    date_str: str,
    mode: str = "production",
    quality_tier: str = "production_full",
) -> None:
    reports = repo_root / "data" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / ("aov_report_%s.html" % date_str)
    report.write_text(
        (
            "<!-- cache_hit: 1/1 (100%%) | llm_calls: 0 | mode: %s "
            "| quality_tier: %s -->\n<html></html>\n"
        )
        % (mode, quality_tier),
        encoding="utf-8",
    )
    (repo_root / "index.html").write_text(
        '<a href="data/reports/aov_report_%s.html" class="main-btn">進入最新戰報</a>\n' % date_str,
        encoding="utf-8",
    )


def _write_manifest(
    repo_root: Path,
    date_str: str,
    mode: str = "production",
    source_quality: Optional[dict] = None,
    meta: Optional[dict] = None,
    with_analysis: bool = True,
) -> None:
    data_dir = repo_root / "data"
    manifest = build_manifest(
        run_date=date_str,
        mode=mode,
        raw_path=data_dir / ("raw_%s.json" % date_str.replace("-", "")),
        analysis_path=(data_dir / ("analysis_%s.json" % date_str.replace("-", ""))) if with_analysis else None,
        report_path=data_dir / "reports" / ("aov_report_%s.html" % date_str),
        meta=meta or {"history_status": "ok"},
        history_delta={
            "weekly_vol_pulse": {"volumes": [1, 2, 3]},
            "diagnostics": {"source_dates": ["2026-05-15"], "missing_dates": ["2026-05-14"]},
        },
        status="ok",
        source_quality=source_quality,
    )
    write_manifest(data_dir, manifest)


def _budget_skip(tmp_path: Path, date_str: str) -> dict:
    manager = LLMBudgetManager(
        tmp_path / "data" / "llm_budget_state.json",
        max_daily_llm_calls=1,
        cooldown_minutes=60,
    )
    manager.record_llm_call(date_str)
    return manager.snapshot(date_str)


def test_system_doctor_local_passes_with_production_manifest(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")
    _write_manifest(tmp_path, date_str, mode="production")

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert result.blocking_count == 0
    assert all(x.code.startswith("DOC") for x in result.issues)
    assert all(x.runbook.startswith("docs/OPERATIONS_RUNBOOK.md#") for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_accepts_production_local_only(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(
        tmp_path,
        date_str,
        mode="production",
        quality_tier="production_local_only",
    )
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality=build_source_quality(
            [
                {"platform": "dcard", "source": "dcard.tw"},
                {"platform": "bahamut", "source": "forum.gamer.com.tw"},
            ]
        ),
        meta={
            "history_status": "ok",
            "quota_error": True,
            "analysis_source": "local_deterministic",
            "llm_coverage": "none",
            "local_analysis_status": "ok",
        },
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="ci", require_production=True)

    assert not any(x.code == "DOC016" for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_advises_on_budget_cooldown(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(
        tmp_path,
        date_str,
        mode="production",
        quality_tier="production_local_only",
    )
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality=build_source_quality(
            [
                {"platform": "dcard", "source": "dcard.tw"},
                {"platform": "bahamut", "source": "forum.gamer.com.tw"},
            ]
        ),
        meta={
            "history_status": "ok",
            "analysis_source": "local_deterministic",
            "llm_coverage": "none",
            "local_analysis_status": "ok",
            "budget": _budget_skip(tmp_path, date_str),
        },
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="ci", require_production=True)

    assert any(x.code == "DOC017" and x.severity == doctor.SEV_ADVISORY for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_advises_on_selection_throttle(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(
        tmp_path,
        date_str,
        mode="production",
        quality_tier="production_llm_partial",
    )
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality=build_source_quality(
            [
                {"platform": "dcard", "source": "dcard.tw"},
                {"platform": "bahamut", "source": "forum.gamer.com.tw"},
            ]
        ),
        meta={
            "history_status": "ok",
            "analysis_source": "mixed",
            "llm_coverage": "partial",
            "selection": {
                "schema_version": 1,
                "selection_truth": "source selection only; raw sources retained",
                "total_input_posts": 10,
                "unique_posts": 8,
                "duplicate_posts": 2,
                "llm_selected_posts": 4,
                "local_only_posts": 6,
                "max_llm_items": 4,
                "budget_remaining": 10,
                "selection_reasons": ["duplicate_url", "llm_selected", "topn_overflow"],
                "reason_counts": {"duplicate_url": 2, "llm_selected": 4, "topn_overflow": 4},
                "selected_platform_counts": {"dcard": 2, "bahamut": 2},
                "local_only_platform_counts": {"dcard": 6},
            },
        },
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="ci", require_production=True)

    assert any(x.code == "DOC018" and x.severity == doctor.SEV_ADVISORY for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_advises_on_enrichment_noop(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(
        tmp_path,
        date_str,
        mode="production",
        quality_tier="production_llm_partial",
    )
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality=build_source_quality(
            [
                {"platform": "dcard", "source": "dcard.tw"},
                {"platform": "bahamut", "source": "forum.gamer.com.tw"},
            ]
        ),
        meta={
            "history_status": "ok",
            "analysis_source": "mixed",
            "llm_coverage": "partial",
            "enrichment": {
                "schema_version": 1,
                "enrichment_truth": "raw-free enrichment snapshot only",
                "queue_available": True,
                "queue_ref": "data/enrichment_queue/2026-05-16/enrichment_queue.json",
                "queue_digest": "abc123",
                "source_count": 2,
                "eligible_posts": 0,
                "skipped_posts": 2,
                "enriched_posts": 0,
                "artifact_retention_days": 3,
                "replay_status": "no_eligible",
                "eligible_reason_counts": {},
                "skipped_reason_counts": {"duplicate_url": 2},
                "budget_decision": "call_llm",
                "budget_reason": "available",
                "budget_remaining": 10,
                "cooldown_active": False,
            },
        },
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="ci", require_production=True)

    assert any(x.code == "DOC019" and x.severity == doctor.SEV_ADVISORY for x in result.issues)
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


def test_system_doctor_blocks_on_quality_no_posts(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality={
            "status": "failed",
            "total_posts": 0,
            "platform_count": 0,
            "platform_counts": {},
            "source_count": 0,
            "reasons": ["no_posts"],
        },
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert result.blocking_count > 0
    assert any(x.code == "DOC013" for x in result.issues)
    assert doctor.exit_code_for(result) == 1


def test_system_doctor_advises_on_degraded_source_health(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality={
            "status": "degraded",
            "total_posts": 2,
            "platform_count": 1,
            "platform_counts": {"web": 2},
            "source_count": 1,
            "reasons": ["single_platform", "single_source"],
        },
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert result.blocking_count == 0
    assert any(x.code == "DOC014" and x.severity == doctor.SEV_ADVISORY for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_degrades_on_core_contract_fail(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")
    _write_manifest(
        tmp_path,
        date_str,
        mode="production",
        source_quality={
            "status": "ok",
            "total_posts": 2,
            "platform_count": 2,
            "platform_counts": {"dcard": 1, "bahamut": 1},
            "source_count": 2,
            "reasons": [],
        },
        with_analysis=False,
    )

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert result.blocking_count == 0
    assert any(x.code == "DOC015" and x.severity == doctor.SEV_DEGRADED for x in result.issues)
    assert doctor.exit_code_for(result) == 0


def test_system_doctor_advises_when_core_contract_missing(tmp_path: Path):
    date_str = "2026-05-16"
    _write_report_and_index(tmp_path, date_str, mode="production")
    data_dir = tmp_path / "data"
    manifest = build_manifest(
        run_date=date_str,
        mode="production",
        raw_path=data_dir / ("raw_%s.json" % date_str.replace("-", "")),
        analysis_path=data_dir / ("analysis_%s.json" % date_str.replace("-", "")),
        report_path=data_dir / "reports" / ("aov_report_%s.html" % date_str),
    )
    del manifest["quality"]["core_contract"]
    out = data_dir / "runs" / date_str / "run_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    result = doctor.run_doctor(tmp_path, date_str, profile="local")

    assert any(x.code == "DOC015" and x.severity == doctor.SEV_ADVISORY for x in result.issues)
    assert doctor.exit_code_for(result) == 0
