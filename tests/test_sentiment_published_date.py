"""
P108.3.1 — sentiment 重建層 published_date 流向測試。

升級 A：_post_timestamp 直接屬性存取（單元）。
升級 B：端到端契約——mock LLM 驗 published_date 真流到 analyzed_posts 的 post，
涵蓋三路徑（381 LLM 成功 / 401 LLM error 分支 / 347 showcase），防 P108.3
同類「單元過但 production 沒生效」復發。
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from analyzer.sentiment import _post_timestamp, SentimentAnalyzer
from scrapers.tavily_searcher import SearchResult


def _sr(published_date="", title="芽芽改版", platform="bahamut"):
    return SearchResult(
        title=title, content="芽芽強度討論內容", url="https://forum.gamer.com.tw/x",
        source="forum.gamer.com.tw", platform=platform,
        published_date=published_date, detected_heroes=["芽芽"] if "芽芽" in title else [],
    )


# ── 升級 A：_post_timestamp 直接屬性存取單元測試 ──

def test_post_timestamp_returns_published_date():
    assert _post_timestamp(_sr("2026-06-01 22:39:00")) == "2026-06-01 22:39:00"


def test_post_timestamp_empty_returns_default():
    assert _post_timestamp(_sr("")) == "時間未知"


def test_post_timestamp_custom_default():
    assert _post_timestamp(_sr(""), "2026-06-07 00:00:00") == "2026-06-07 00:00:00"


# ── 升級 B：端到端契約測試（mock LLM，不燒額度）──

_VALID_ANALYSIS = {
    "reasoning": "ok", "sentiment": "neutral", "sentiment_score": 0.5,
    "region": "TW", "original_language": "zh", "translated_content": "",
    "category": "一般", "keywords": [], "summary": "ok",
    "relevance_score": 0.8, "is_hero_focus": False, "events": [],
}


def _make_analyzer(batch_return):
    cache = MagicMock()
    cache.hero_key.return_value = None
    cache.get.return_value = None
    cache.increment_stat = MagicMock()
    llm = MagicMock()
    llm.batch_chat = AsyncMock(return_value=batch_return)
    llm.cache_manager = cache
    return SentimentAnalyzer(llm_client=llm)


@pytest.mark.asyncio
async def test_llm_success_path_preserves_published_date():
    """381 LLM 成功路徑：published_date 流到 post.timestamp（修前會是「時間未知」）。"""
    analyzer = _make_analyzer([dict(_VALID_ANALYSIS)])
    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_sr("2026-06-01 22:39:00")], showcase=False)
    assert result["posts"][0]["post"]["timestamp"] == "2026-06-01 22:39:00"


@pytest.mark.asyncio
async def test_llm_error_branch_preserves_published_date():
    """401 LLM error 分支（analysis 含 error）：仍保留 published_date。"""
    analyzer = _make_analyzer([{"error": "bad response"}])
    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_sr("2026-05-29 11:39:00")], showcase=False)
    assert result["posts"][0]["post"]["timestamp"] == "2026-05-29 11:39:00"


@pytest.mark.asyncio
async def test_showcase_path_preserves_published_date():
    """347 showcase 路徑（batch 回空）：有 published_date 時用它，非寫死 now。"""
    analyzer = _make_analyzer([])
    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_sr("2026-06-01 22:39:00")], showcase=True)
    assert result["posts"][0]["post"]["timestamp"] == "2026-06-01 22:39:00"


@pytest.mark.asyncio
async def test_llm_path_empty_date_falls_back_to_unknown():
    """無 published_date（tavily/ddg 空值）走 LLM → 回「時間未知」（不退步，R-032 待 fallback）。"""
    analyzer = _make_analyzer([dict(_VALID_ANALYSIS)])
    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_sr("", title="一般新聞", platform="web")], showcase=False)
    assert result["posts"][0]["post"]["timestamp"] == "時間未知"
