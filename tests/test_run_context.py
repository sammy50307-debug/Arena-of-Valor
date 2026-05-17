from __future__ import annotations

from datetime import datetime, timezone

import pytest

from analyzer.run_context import build_run_context, build_run_id, build_source_hash, get_run_timezone


def test_build_run_context_uses_taipei_business_date():
    ctx = build_run_context(
        now_utc=datetime(2026, 5, 16, 16, 30, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
    )

    assert ctx.run_date == "2026-05-17"
    assert ctx.compact_date == "20260517"
    assert ctx.display_date == "05/17"
    assert ctx.started_at_utc == "2026-05-16T16:30:00Z"
    assert ctx.timezone_name == "Asia/Taipei"


def test_get_run_timezone_rejects_unsupported_timezone():
    with pytest.raises(ValueError):
        get_run_timezone("Europe/London")


def test_build_source_hash_is_stable_and_excludes_content():
    items_a = [
        {"url": "https://example.com/b", "title": "B", "platform": "Dcard", "region": "TW", "content": "v1"},
        {"url": "https://example.com/a", "title": "A", "platform": "PTT", "region": "TW", "content": "v1"},
    ]
    items_b = [
        {"url": "https://example.com/a", "title": "A", "platform": "PTT", "region": "TW", "content": "v2"},
        {"url": "https://example.com/b", "title": "B", "platform": "Dcard", "region": "TW", "content": "v2"},
    ]

    assert build_source_hash(items_a) == build_source_hash(items_b)


def test_build_run_id_contract():
    assert build_run_id("2026-05-17", "production", "abcdef1234567890") == "2026-05-17-production-abcdef123456"
