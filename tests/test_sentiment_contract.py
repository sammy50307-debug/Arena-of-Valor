from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from analyzer.sentiment import SentimentAnalyzer


def _make_search_result(title: str = "測試文章"):
    sr = MagicMock()
    sr.title = title
    sr.content = "內容"
    sr.platform = "PTT"
    sr.source = "user"
    sr.url = "https://example.com"
    sr.region = "TW"
    return sr


def _make_analyzer() -> SentimentAnalyzer:
    analyzer = SentimentAnalyzer.__new__(SentimentAnalyzer)
    analyzer.logger = MagicMock()

    cm = MagicMock()
    cm.hero_key.return_value = None
    cm.get.return_value = None
    cm.increment_stat = MagicMock()
    cm.set = MagicMock()
    cm.save = MagicMock()
    cm.daily_summary_key.return_value = "ds_2026-05-17"

    llm = MagicMock()
    llm.cache_manager = cm
    analyzer.llm = llm
    return analyzer


def _valid_single_post_payload() -> dict:
    return {
        "reasoning": "ok",
        "sentiment": "neutral",
        "sentiment_score": 0.5,
        "region": "TW",
        "original_language": "zh",
        "translated_content": "",
        "category": "一般",
        "keywords": [],
        "summary": "ok",
        "relevance_score": 0.8,
        "is_hero_focus": False,
        "events": [],
    }


def _analyzed_post() -> dict:
    return {
        "post": {
            "platform": "PTT",
            "source": "user",
            "url": "https://example.com",
            "title": "測試文章",
            "content": "內容",
            "region": "TW",
            "detected_heroes": [],
        },
        "analysis": {
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "summary": "ok",
            "keywords": [],
            "relevance_score": 0.8,
        },
    }


@pytest.mark.asyncio
async def test_analyze_posts_degrades_bad_single_post_contract():
    analyzer = _make_analyzer()
    analyzer.llm.batch_chat = AsyncMock(return_value=[{"sentiment": "positive"}])

    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_make_search_result()], showcase=False)

    assert result["contract_status"] == "degraded"
    assert result["contract_errors"]
    assert result["posts"][0]["analysis"]["summary"] == "分析失敗"
    assert result["posts"][0]["analysis"]["llm_contract"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_analyze_posts_marks_valid_single_post_contract_ok():
    analyzer = _make_analyzer()
    analyzer.llm.batch_chat = AsyncMock(return_value=[_valid_single_post_payload()])

    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_make_search_result()], showcase=False)

    assert result["contract_status"] == "ok"
    assert result["contract_errors"] == []
    assert result["posts"][0]["analysis"]["llm_contract"]["status"] == "ok"


@pytest.mark.asyncio
async def test_generate_daily_summary_degrades_bad_contract_to_fallback():
    analyzer = _make_analyzer()
    analyzer.llm.chat = AsyncMock(return_value={"date": "2026-05-17"})

    summary = await analyzer.generate_daily_summary([_analyzed_post()], date="2026-05-17")

    assert summary["llm_contract"]["status"] == "degraded"
    assert any("daily_summary missing required field" in e for e in summary["llm_contract"]["errors"])
    assert summary["overview"].startswith("今日輿情共搜集到")


@pytest.mark.asyncio
async def test_generate_daily_summary_marks_valid_contract_ok():
    analyzer = _make_analyzer()
    analyzer.llm.chat = AsyncMock(
        return_value={
            "date": "2026-05-17",
            "overview": "ok",
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 1},
            "hot_topics": [],
            "detected_events": [],
            "platform_breakdown": {},
            "alerts": [],
            "recommendation": "ok",
        }
    )

    summary = await analyzer.generate_daily_summary([_analyzed_post()], date="2026-05-17")

    assert summary["llm_contract"] == {"status": "ok", "errors": []}
