from __future__ import annotations

from types import SimpleNamespace

from analyzer.local_analyzer import (
    ANALYSIS_SOURCE,
    analyze_local_post,
    analyze_posts_locally,
    generate_local_summary,
)


def _post(title: str, content: str, platform: str = "PTT", score: float = 0.7):
    return SimpleNamespace(
        title=title,
        content=content,
        platform=platform,
        source="tester",
        url="https://example.com/%s" % abs(hash(title)),
        region="TW",
        score=score,
        published_date="2026-05-20",
        detected_heroes=[],
    )


def test_analyze_local_post_detects_positive_hero_and_event():
    result = analyze_local_post(
        _post("新版芽芽輔助教學", "護盾加強真的好用，玩家都很期待。"),
        hero_watchlist=["芽芽", "皮皮"],
    )

    assert result["analysis"]["analysis_source"] == ANALYSIS_SOURCE
    assert result["analysis"]["sentiment"] == "positive"
    assert result["analysis"]["sentiment_score"] > 0.5
    assert result["analysis"]["is_hero_focus"] is True
    assert result["post"]["detected_heroes"] == ["芽芽"]
    assert any(event["type"] == "balance_update" for event in result["analysis"]["events"])


def test_analyze_local_post_detects_negative_issue_report():
    result = analyze_local_post(
        _post("排位問題回報", "今天延遲卡頓又遇到掛機，大家都在抱怨想退坑。"),
        hero_watchlist=["芽芽"],
    )

    assert result["analysis"]["sentiment"] == "negative"
    assert result["analysis"]["sentiment_score"] < 0.5
    assert result["analysis"]["category"] == "問題回報"
    assert any(event["type"] == "issue_report" for event in result["analysis"]["events"])


def test_analyze_local_post_keeps_neutral_when_no_signal():
    result = analyze_local_post(
        _post("例行維護通知", "官方今日公告伺服器維護時間。"),
        hero_watchlist=["芽芽"],
    )

    assert result["analysis"]["sentiment"] == "neutral"
    assert result["analysis"]["sentiment_score"] == 0.5


def test_generate_local_summary_aggregates_platform_topics_events_and_links():
    analyzed = analyze_posts_locally(
        [
            _post("新版芽芽輔助教學", "護盾加強好用，玩家期待。", platform="PTT", score=0.9),
            _post("賽事決賽討論", "GCS 決賽戰隊奪冠，社群覺得精彩。", platform="Facebook", score=0.8),
            _post("排位問題", "延遲卡頓問題讓玩家抱怨。", platform="Dcard", score=0.6),
        ],
        hero_watchlist=["芽芽"],
    )

    summary = generate_local_summary(analyzed, "2026-05-20", hero_focus="芽芽")

    assert summary["analysis_source"] == ANALYSIS_SOURCE
    assert summary["total_posts"] == 3
    assert summary["sentiment_distribution"]["positive"] >= 1
    assert summary["platform_breakdown"]["ptt"]["post_count"] == 1
    assert summary["platform_breakdown"]["facebook"]["post_count"] == 1
    assert any(topic["topic"] == "平衡調整" for topic in summary["hot_topics"])
    assert any(event["type"] == "esports" for event in summary["detected_events"])
    assert summary["hero_stats"]["芽芽"]["count"] == 1
    assert summary["top_links"][0]["url"].startswith("https://example.com/")


def test_generate_local_summary_handles_empty_data():
    summary = generate_local_summary([], "2026-05-20", hero_focus="芽芽")

    assert summary["total_posts"] == 0
    assert summary["sentiment_distribution"] == {"positive": 0, "negative": 0, "neutral": 0}
    assert summary["platform_breakdown"] == {}
    assert summary["top_links"] == []
    assert summary["local_analysis_status"] == "ok"
