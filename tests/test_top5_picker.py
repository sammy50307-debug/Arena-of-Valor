"""
T1 單元測試 — top5_picker (P65-S2)
Exit Criteria: ≥ 12 cases 全綠
"""

import pytest
from datetime import datetime

from analyzer.top5_picker import (
    _extract_score,
    _compute_decay,
    _compute_boost,
    pick_top5,
)
from analyzer.url_normalizer import normalize


# ────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────

def _make_post(
    url="https://example.com/article/1",
    score=0.8,
    timestamp="2026-05-03 10:00:00",
    hero_focus=False,
    title="測試標題",
    content="測試內文",
    region="TW",
    sentiment="neutral",
    relevance_score=None,
):
    analysis_score = relevance_score if relevance_score is not None else score
    return {
        "post": {
            "url": url,
            "title": title,
            "content": content,
            "timestamp": timestamp,
            "platform": "ptt",
            "region": region,
            "is_hero_focus": hero_focus,
            "detected_heroes": ["芽芽"] if hero_focus else [],
        },
        "analysis": {
            "sentiment": sentiment,
            "relevance_score": analysis_score,
            "summary": f"{title} 的摘要",
            "is_hero_focus": hero_focus,
        },
    }


NOW = datetime(2026, 5, 3, 12, 0, 0)
TODAY = "2026-05-03"


# ────────────────────────────────────────────────────────
# 1. _extract_score
# ────────────────────────────────────────────────────────

def test_extract_score_from_analysis():
    entry = _make_post(score=0.9, relevance_score=0.9)
    assert _extract_score(entry) == pytest.approx(0.9)


def test_extract_score_fallback_to_post_score():
    entry = {"post": {"score": 0.75}, "analysis": {}}
    assert _extract_score(entry) == pytest.approx(0.75)


def test_extract_score_default_when_missing():
    assert _extract_score({}) == pytest.approx(0.5)


# ────────────────────────────────────────────────────────
# 2. _compute_decay
# ────────────────────────────────────────────────────────

def test_decay_fresh_post():
    ts = "2026-05-03 11:00:00"
    d = _compute_decay(ts, now=NOW)
    assert d == pytest.approx(1.0 - 1.0 / 72, abs=0.01)


def test_decay_old_post_floored():
    ts = "2026-04-01 00:00:00"
    d = _compute_decay(ts, now=NOW)
    assert d == pytest.approx(0.3)


def test_decay_missing_timestamp():
    assert _compute_decay(None) == pytest.approx(1.0)


def test_decay_dateonly_format():
    ts = "2026-05-03"
    d = _compute_decay(ts, now=NOW)
    assert 0.3 <= d <= 1.0


# ────────────────────────────────────────────────────────
# 3. _compute_boost
# ────────────────────────────────────────────────────────

def test_boost_hero_focus_post():
    entry = _make_post(hero_focus=True)
    b = _compute_boost(entry, "芽芽")
    assert b == pytest.approx(1.2)


def test_boost_non_hero_post():
    entry = _make_post(hero_focus=False)
    b = _compute_boost(entry, "芽芽")
    assert b == pytest.approx(1.0)


def test_boost_hero_in_title():
    entry = _make_post(title="芽芽新造型來了", hero_focus=False)
    b = _compute_boost(entry, "芽芽")
    assert b == pytest.approx(1.2)


def test_boost_no_focus_hero():
    entry = _make_post(hero_focus=True)
    b = _compute_boost(entry, "")
    assert b == pytest.approx(1.0)


# ────────────────────────────────────────────────────────
# 4. pick_top5 — 核心邏輯
# ────────────────────────────────────────────────────────

def test_pick_top5_returns_top_n():
    posts = [_make_post(url=f"https://example.com/{i}", score=i * 0.1 + 0.1) for i in range(10)]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index={})
    assert len(cards) == 5


def test_pick_top5_sorted_by_final_score():
    posts = [_make_post(url=f"https://example.com/{i}", score=float(i) * 0.1 + 0.05) for i in range(7)]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index={})
    scores = [c["picker"]["final_score"] for c in cards]
    assert scores == sorted(scores, reverse=True)


def test_pick_top5_hero_post_ranked_higher():
    normal = _make_post(url="https://example.com/normal", score=0.7, hero_focus=False)
    yaya = _make_post(url="https://example.com/yaya", score=0.7, hero_focus=True)
    cards, _ = pick_top5([normal, yaya], hero_focus="芽芽", today=TODAY, now=NOW, history_index={}, top_n=2)
    assert cards[0]["post"]["url"] == "https://example.com/yaya"


def test_pick_top5_empty_input():
    cards, idx = pick_top5([], today=TODAY, now=NOW, history_index={})
    assert cards == []
    assert idx == {}


def test_pick_top5_fewer_than_5_posts():
    posts = [_make_post(url=f"https://example.com/{i}", score=0.5) for i in range(3)]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index={})
    assert len(cards) == 3


def test_pick_top5_dedup_marks_duplicate():
    url = "https://example.com/old-news"
    history = {normalize(url): {"first_seen": "2026-05-02"}}
    post = _make_post(url=url, score=0.9)
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index=history)
    assert cards[0]["picker"]["is_duplicate"] is True
    assert cards[0]["picker"]["dup_badge"] == "day1"


def test_pick_top5_bypass_dedup_ignores_history():
    url = "https://example.com/old-news"
    history = {normalize(url): {"first_seen": "2026-05-01"}}
    post = _make_post(url=url, score=0.9)
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index=history, bypass_dedup=True)
    assert cards[0]["picker"]["is_duplicate"] is False


def test_pick_top5_new_urls_recorded_in_index():
    post = _make_post(url="https://example.com/brand-new", score=0.8)
    _, updated_idx = pick_top5([post], today=TODAY, now=NOW, history_index={})
    assert normalize("https://example.com/brand-new") in updated_idx


def test_pick_top5_picker_metadata_present():
    post = _make_post()
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index={})
    picker = cards[0]["picker"]
    for key in ("final_score", "base_score", "decay", "boost", "is_duplicate", "dup_badge", "norm_url"):
        assert key in picker, f"missing picker key: {key}"


# ────────────────────────────────────────────────────────
# 5. url_normalizer
# ────────────────────────────────────────────────────────

def test_normalize_strips_utm():
    raw = "https://example.com/article?utm_source=fb&utm_medium=social&id=123"
    assert "utm_source" not in normalize(raw)
    assert "id=123" in normalize(raw)


def test_normalize_strips_trailing_slash():
    assert normalize("https://example.com/article/") == "https://example.com/article"


def test_normalize_empty_url():
    assert normalize("") == ""
    assert normalize("#") == "#"
