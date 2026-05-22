from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import cost_cache_governance


def _write_manifest(
    repo_root: Path,
    date_str: str,
    cache_hit: int = 2,
    total_calls: int = 3,
    llm_calls: int = 1,
    mode: str = "production",
    budget: dict | None = None,
    selection: dict | None = None,
    enrichment: dict | None = None,
) -> None:
    path = repo_root / "data" / "runs" / date_str / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "metrics": {
            "cache_hit": cache_hit,
            "l1_hits": cache_hit,
            "l2_hits": 0,
            "apify_hits": 0,
            "llm_calls": llm_calls,
            "total_calls": total_calls,
        },
    }
    if budget is not None:
        payload["budget"] = budget
    if selection is not None:
        payload["selection"] = selection
    if enrichment is not None:
        payload["enrichment"] = enrichment
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_report(
    repo_root: Path,
    date_str: str,
    cache_hit: int = 1,
    total_calls: int = 2,
    llm_calls: int = 1,
    mode: str = "production",
) -> None:
    path = repo_root / "data" / "reports" / ("aov_report_%s.html" % date_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    pct = int(round((cache_hit / total_calls) * 100)) if total_calls else 0
    path.write_text(
        "<!-- cache_hit: %s/%s (%s%%) | llm_calls: %s | mode: %s -->\n<html></html>\n"
        % (cache_hit, total_calls, pct, llm_calls, mode),
        encoding="utf-8",
    )


def _write_cache(repo_root: Path, hits: int = 4, misses: int = 1) -> None:
    path = repo_root / "data" / "llm_cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 3,
        "entries": {
            "prompt:a": {
                "result": {"redacted": True},
                "stored_at": "2026-05-18T00:00:00+00:00",
                "last_accessed": "2026-05-18T00:00:00+00:00",
                "ttl_days": 7,
            }
        },
        "stats": {
            "total_l1_hits": hits,
            "total_l2_hits": 0,
            "total_apify_hits": 0,
            "total_misses": misses,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _codes(result):
    return {issue.code for issue in result.issues}


def test_cost_cache_passes_with_manifest_and_cache_stats(tmp_path: Path):
    _write_manifest(tmp_path, "2026-05-18", cache_hit=2, total_calls=3, llm_calls=1)
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert result.total_cache_hit == 2
    assert result.aggregate_cache_hit_rate_pct == 67
    assert result.cache_store.entry_count == 1
    assert result.issues == []


def test_cost_cache_falls_back_to_report_metadata(tmp_path: Path):
    _write_report(tmp_path, "2026-05-18", cache_hit=1, total_calls=2, llm_calls=1)
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert result.days[0].source == "report_metadata"
    assert result.total_calls == 2


def test_cost_cache_low_hit_rate_is_advisory_only(tmp_path: Path):
    _write_manifest(tmp_path, "2026-05-18", cache_hit=0, total_calls=4, llm_calls=4)
    _write_cache(tmp_path, hits=0, misses=4)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert "CCG003" in _codes(result)
    assert cost_cache_governance.exit_code_for(result) == 0


def test_cost_cache_blocks_invalid_metrics(tmp_path: Path):
    _write_manifest(tmp_path, "2026-05-18", cache_hit=5, total_calls=2, llm_calls=1)
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert "CCG002" in _codes(result)
    assert cost_cache_governance.exit_code_for(result) == 1


def test_cost_cache_degrades_when_llm_call_budget_exceeded(tmp_path: Path):
    _write_manifest(tmp_path, "2026-05-18", cache_hit=0, total_calls=6, llm_calls=6)
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1, max_llm_calls=5)

    assert "CCG005" in _codes(result)
    assert cost_cache_governance.exit_code_for(result) == 1


def test_cost_cache_advises_on_budget_cooldown(tmp_path: Path):
    _write_manifest(
        tmp_path,
        "2026-05-18",
        cache_hit=0,
        total_calls=0,
        llm_calls=0,
        budget={
            "decision": "skip_llm",
            "decision_reason": "cooldown_active",
            "cooldown_active": True,
            "llm_calls_used": 20,
        },
    )
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert "CCG006" in _codes(result)
    assert cost_cache_governance.exit_code_for(result) == 0
    assert result.days[0].budget_decision == "skip_llm"


def test_cost_cache_advises_on_selection_throttle(tmp_path: Path):
    _write_manifest(
        tmp_path,
        "2026-05-18",
        cache_hit=0,
        total_calls=5,
        llm_calls=4,
        selection={
            "total_input_posts": 10,
            "llm_selected_posts": 4,
            "local_only_posts": 6,
            "duplicate_posts": 2,
            "max_llm_items": 4,
        },
    )
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert "CCG007" in _codes(result)
    assert result.days[0].selection_llm_selected_posts == 4
    assert cost_cache_governance.exit_code_for(result) == 0


def test_cost_cache_advises_on_enrichment_pending(tmp_path: Path):
    _write_manifest(
        tmp_path,
        "2026-05-18",
        cache_hit=1,
        total_calls=5,
        llm_calls=2,
        enrichment={
            "queue_available": True,
            "eligible_posts": 2,
            "skipped_posts": 1,
            "enriched_posts": 0,
            "replay_status": "pending",
        },
    )
    _write_cache(tmp_path)

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)

    assert "CCG008" in _codes(result)
    assert result.days[0].enrichment_eligible_posts == 2
    assert cost_cache_governance.exit_code_for(result) == 0


def test_cost_cache_degrades_invalid_cache_stats_without_dumping_entries(tmp_path: Path):
    _write_manifest(tmp_path, "2026-05-18")
    path = tmp_path / "data" / "llm_cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "entries": {"prompt:a": {"result": {"secret": "do-not-print"}}},
                "stats": {"total_l1_hits": "bad", "total_l2_hits": 0, "total_apify_hits": 0, "total_misses": 0},
            }
        ),
        encoding="utf-8",
    )

    result = cost_cache_governance.evaluate_cost_cache(tmp_path, "2026-05-18", window_days=1)
    payload = json.dumps(cost_cache_governance.result_to_dict(result), ensure_ascii=False)

    assert "CCG004" in _codes(result)
    assert "do-not-print" not in payload


def test_cost_cache_cli_json(tmp_path: Path, capsys):
    _write_manifest(tmp_path, "2026-05-18")
    _write_cache(tmp_path)

    rc = cost_cache_governance.main(["--repo-root", str(tmp_path), "--date", "2026-05-18", "--window-days", "1", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert payload["billing_truth"] == "pipeline proxy only; not provider billing truth"
    assert payload["total_llm_calls"] == 1
