from __future__ import annotations

from pathlib import Path

import config
from analyzer import news_history_indexer as _indexer
from reporter.generator import ReportGenerator


def _entry(
    *,
    title: str,
    url: str,
    summary: str,
    timestamp: str = "2026-05-25 10:00:00",
    is_hero_focus: bool = False,
    score: float = 0.9,
) -> dict:
    return {
        "post": {
            "platform": "dcard",
            "author": "dcard.tw",
            "url": url,
            "title": title,
            "content": title,
            "timestamp": timestamp,
            "region": "TW",
            "is_hero_focus": is_hero_focus,
        },
        "analysis": {
            "sentiment": "positive",
            "summary": summary,
            "relevance_score": score,
            "is_hero_focus": is_hero_focus,
        },
    }


def test_report_locks_focus_title_to_config_and_filters_false_focus_cards(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(config, "HERO_FOCUS_NAME", "芽芽", raising=False)
    monkeypatch.setattr(config, "ENABLE_TOP5_NEWS", True, raising=False)
    monkeypatch.setattr(_indexer, "_INDEX_PATH", tmp_path / "news_history_index.json", raising=False)

    summary = {
        "date": "2026-05-25",
        "overview": "測試",
        "sentiment_distribution": {"positive": 2, "negative": 0, "neutral": 0},
        "platform_breakdown": {},
        "hot_topics": [],
        "detected_events": [],
        "hero_focus": {
            "name": "圖倫",
            "summary": "測試摘要",
            "sentiment_score": 0.5,
            "top_comments": [],
        },
        "_meta": {"mode": "production"},
    }
    analyzed_posts = [
        _entry(
            title="圖倫完整教學",
            url="https://example.com/tulen",
            summary="玩家分享圖倫教學。",
            is_hero_focus=True,
            score=0.99,
        ),
        _entry(
            title="芽芽輔助護盾討論",
            url="https://example.com/yaya",
            summary="玩家討論芽芽護盾。",
            is_hero_focus=False,
            score=0.8,
        ),
    ]

    out = ReportGenerator().generate(summary, analyzed_posts, output_dir=tmp_path, promote=False)
    html = out.read_text(encoding="utf-8")

    assert "芽芽 觀察室" in html
    assert "圖倫 觀察室" not in html

    yaya_section = html.split("📰 芽芽近期動態", 1)[1].split("Combat Stats Dashboard", 1)[0]
    assert "芽芽輔助護盾討論" in yaya_section
    assert "圖倫完整教學" not in yaya_section


def test_report_excludes_unknown_date_from_focus_recent_cards(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(config, "HERO_FOCUS_NAME", "芽芽", raising=False)
    monkeypatch.setattr(config, "ENABLE_TOP5_NEWS", True, raising=False)
    monkeypatch.setattr(_indexer, "_INDEX_PATH", tmp_path / "news_history_index.json", raising=False)

    summary = {
        "date": "2026-05-25",
        "overview": "測試",
        "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
        "platform_breakdown": {},
        "hot_topics": [],
        "detected_events": [],
        "hero_focus": {"name": "芽芽", "summary": "測試摘要", "sentiment_score": 0.5, "top_comments": []},
        "_meta": {"mode": "production"},
    }
    analyzed_posts = [
        _entry(
            title="芽芽未知時間心得",
            url="https://example.com/yaya-unknown",
            summary="玩家討論芽芽。",
            timestamp="",
            is_hero_focus=True,
        ),
    ]

    out = ReportGenerator().generate(summary, analyzed_posts, output_dir=tmp_path, promote=False)
    html = out.read_text(encoding="utf-8")

    assert "🌸 今天芽芽在森林裡休息喔~" in html
    assert "芽芽未知時間心得" not in html.split("📰 芽芽近期動態", 1)[-1].split("Combat Stats Dashboard", 1)[0]


def test_report_excludes_unknown_date_from_general_feed(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(config, "HERO_FOCUS_NAME", "芽芽", raising=False)
    monkeypatch.setattr(config, "ENABLE_TOP5_NEWS", True, raising=False)
    monkeypatch.setattr(_indexer, "_INDEX_PATH", tmp_path / "news_history_index.json", raising=False)

    summary = {
        "date": "2026-05-25",
        "overview": "測試",
        "sentiment_distribution": {"positive": 2, "negative": 0, "neutral": 0},
        "platform_breakdown": {},
        "hot_topics": [],
        "detected_events": [],
        "hero_focus": {"name": "芽芽", "summary": "測試摘要", "sentiment_score": 0.5, "top_comments": []},
        "_meta": {"mode": "production"},
    }
    analyzed_posts = [
        _entry(
            title="圖倫未知時間教學",
            url="https://example.com/tulen-unknown",
            summary="玩家分享圖倫教學。",
            timestamp="時間未知",
            score=0.99,
        ),
        _entry(
            title="版本活動整理",
            url="https://example.com/event",
            summary="玩家整理版本活動。",
            timestamp="2026-05-25 10:00:00",
            score=0.8,
        ),
    ]

    out = ReportGenerator().generate(summary, analyzed_posts, output_dir=tmp_path, promote=False)
    html = out.read_text(encoding="utf-8")

    assert "版本活動整理" in html
    assert "圖倫未知時間教學" not in html
    assert "時間未知" not in html


def test_hero_focus_empty_posts_shows_placeholder(tmp_path: Path, monkeypatch):
    """P106.1 問題 1：hero_focus_posts 為空時，玩家熱議焦點顯示友善 placeholder。"""
    monkeypatch.setattr(config, "HERO_FOCUS_NAME", "芽芽", raising=False)
    monkeypatch.setattr(config, "ENABLE_TOP5_NEWS", True, raising=False)
    monkeypatch.setattr(_indexer, "_INDEX_PATH", tmp_path / "news_history_index.json", raising=False)

    summary = {
        "date": "2026-05-25",
        "overview": "測試",
        "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
        "platform_breakdown": {},
        "hot_topics": [],
        "detected_events": [],
        "hero_focus": {"name": "芽芽", "summary": "今日無特定焦點分析", "sentiment_score": 0.5, "top_comments": []},
        "_meta": {"mode": "production"},
    }
    analyzed_posts = [
        _entry(
            title="圖倫使用心得",
            url="https://example.com/tulen",
            summary="玩家分享圖倫心得。",
            timestamp="2026-05-25 10:00:00",
        ),
    ]

    out = ReportGenerator().generate(summary, analyzed_posts, output_dir=tmp_path, promote=False)
    html = out.read_text(encoding="utf-8")

    assert "今日尚無芽芽相關討論，靜待玩家動態~" in html
