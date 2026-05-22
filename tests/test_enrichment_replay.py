from __future__ import annotations

import json
from pathlib import Path

import config
from analyzer.enrichment_queue import build_enrichment_queue, write_enrichment_queue
from analyzer.llm_budget import LLMBudgetManager
from analyzer.source_selection import REASON_DUPLICATE_URL, REASON_TOPN_OVERFLOW
from scrapers.tavily_searcher import SearchResult
from scripts import enrichment_replay


DATE = "2026-05-22"


def _patch_paths(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "REPORTS_DIR", data_dir / "reports")
    monkeypatch.setattr(config, "ENRICHMENT_QUEUE_DIR", data_dir / "enrichment_queue")
    monkeypatch.setattr(config, "LLM_BUDGET_STATE_FILE", data_dir / "llm_budget_state.json")
    monkeypatch.setattr(config, "LLM_DAILY_BUDGET", 3)
    monkeypatch.setattr(config, "ENRICHMENT_REPLAY_MAX_POSTS", 2)
    monkeypatch.setattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3)
    monkeypatch.setattr(enrichment_replay, "replay_budget_date", lambda: DATE)


def _post(title: str, url: str) -> SearchResult:
    return SearchResult(
        title=title,
        content="芽芽玩家討論護盾、排位與團戰，內容足夠 replay 深讀。",
        url=url,
        source="dcard",
        platform="dcard",
        score=0.8,
        region="TW",
    )


def _write_queue(reasons: list[str]) -> Path:
    posts = [_post("貼文 %s" % i, "https://example.com/%s" % i) for i, _reason in enumerate(reasons)]
    queue = build_enrichment_queue(
        run_date=DATE,
        source_hash="abc123",
        local_only_posts=posts,
        local_only_reasons=reasons,
        max_replay_posts=2,
        retention_days=3,
        created_at_utc="2026-05-22T00:00:00Z",
    )
    return write_enrichment_queue(config.ENRICHMENT_QUEUE_DIR, queue)


def test_enrichment_replay_missing_queue_returns_failure(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)

    rc = enrichment_replay.main(["--date", DATE])

    assert rc == 1


def test_enrichment_replay_duplicate_only_noops(monkeypatch, tmp_path: Path, capsys):
    _patch_paths(monkeypatch, tmp_path)
    _write_queue([REASON_DUPLICATE_URL])

    rc = enrichment_replay.main(["--date", DATE])
    captured = capsys.readouterr()

    assert rc == 0
    assert "no eligible" in captured.out


def test_enrichment_replay_respects_budget_skip(monkeypatch, tmp_path: Path, capsys):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "LLM_DAILY_BUDGET", 1)
    _write_queue([REASON_TOPN_OVERFLOW])
    manager = LLMBudgetManager(config.LLM_BUDGET_STATE_FILE, max_daily_llm_calls=1, cooldown_minutes=60)
    manager.record_llm_call(DATE)

    rc = enrichment_replay.main(["--date", DATE, "--apply"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "budget skip" in captured.out


def test_enrichment_replay_apply_writes_enriched_posts(monkeypatch, tmp_path: Path):
    _patch_paths(monkeypatch, tmp_path)
    _write_queue([REASON_TOPN_OVERFLOW])

    async def fake_analyze(records):
        raw = records[0]["raw_post"]
        return (
            [
                {
                    "post": raw,
                    "analysis": {
                        "summary": "LLM enriched",
                        "llm_contract": {"status": "ok", "errors": []},
                    },
                }
            ],
            {"analysis_source": "llm"},
        )

    monkeypatch.setattr(enrichment_replay, "_analyze", fake_analyze)

    rc = enrichment_replay.main(["--date", DATE, "--apply"])

    assert rc == 0
    payload = json.loads(enrichment_replay.enriched_posts_path_for(DATE).read_text(encoding="utf-8"))
    assert payload["replay_status"] == "completed"
    assert payload["enriched_posts"][0]["analysis"]["summary"] == "LLM enriched"
