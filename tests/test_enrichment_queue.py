from __future__ import annotations

import json
from pathlib import Path

from scrapers.tavily_searcher import SearchResult
from analyzer.enrichment_queue import (
    STATUS_NO_ELIGIBLE,
    build_enrichment_queue,
    build_enrichment_snapshot,
    validate_enrichment_queue,
    validate_enrichment_snapshot,
    write_enrichment_queue,
)
from analyzer.source_selection import REASON_DUPLICATE_URL, REASON_TOPN_OVERFLOW


def _post(title: str, url: str, score: float = 0.5) -> SearchResult:
    return SearchResult(
        title=title,
        content="芽芽玩家討論護盾、排位與團戰，內容足夠 replay 深讀。",
        url=url,
        source="dcard",
        platform="dcard",
        score=score,
        region="TW",
    )


def test_enrichment_queue_marks_duplicates_noop_and_topn_eligible():
    queue = build_enrichment_queue(
        run_date="2026-05-22",
        source_hash="abc123",
        local_only_posts=[
            _post("重複來源", "https://example.com/a", 0.9),
            _post("可補深讀", "https://example.com/b", 0.8),
            _post("超過 replay cap", "https://example.com/c", 0.7),
        ],
        local_only_reasons=[
            REASON_DUPLICATE_URL,
            REASON_TOPN_OVERFLOW,
            REASON_TOPN_OVERFLOW,
        ],
        max_replay_posts=1,
        retention_days=3,
        created_at_utc="2026-05-22T00:00:00Z",
    )

    assert queue["source_count"] == 3
    assert queue["eligible_count"] == 1
    assert queue["skipped_count"] == 2
    assert queue["records"][0]["eligible"] is False
    assert queue["records"][0]["skip_reason"] == REASON_DUPLICATE_URL
    assert queue["records"][1]["eligible"] is True
    assert queue["records"][2]["skip_reason"] == "replay_cap_overflow"
    assert validate_enrichment_queue(queue) == (True, [])


def test_enrichment_snapshot_is_raw_free_and_valid():
    queue = build_enrichment_queue(
        run_date="2026-05-22",
        source_hash="abc123",
        local_only_posts=[_post("秘密標題不進 manifest", "https://secret.example/a")],
        local_only_reasons=[REASON_DUPLICATE_URL],
        max_replay_posts=1,
        retention_days=3,
        created_at_utc="2026-05-22T00:00:00Z",
    )

    snapshot = build_enrichment_snapshot(
        queue,
        queue_path=Path("data/enrichment_queue/2026-05-22/enrichment_queue.json"),
    )
    payload = json.dumps(snapshot, ensure_ascii=False)

    assert snapshot["replay_status"] == STATUS_NO_ELIGIBLE
    assert snapshot["queue_ref"] == "data/enrichment_queue/2026-05-22/enrichment_queue.json"
    assert "秘密標題不進 manifest" not in payload
    assert "https://secret.example/a" not in payload
    assert "content" not in payload
    assert validate_enrichment_snapshot(snapshot) == (True, [])


def test_write_enrichment_queue_uses_ignored_data_path(tmp_path: Path):
    queue = build_enrichment_queue(
        run_date="2026-05-22",
        source_hash="abc123",
        local_only_posts=[_post("可補深讀", "https://example.com/b")],
        local_only_reasons=[REASON_TOPN_OVERFLOW],
        max_replay_posts=1,
        retention_days=3,
    )

    out = write_enrichment_queue(tmp_path / "data" / "enrichment_queue", queue)

    assert out.name == "enrichment_queue.json"
    assert out.parent.name == "2026-05-22"
    assert json.loads(out.read_text(encoding="utf-8"))["records"][0]["raw_post"]["title"] == "可補深讀"
