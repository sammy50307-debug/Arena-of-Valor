"""
P69：旗艦展演模式四態驗證。

TC1  analyze_posts 遇 429 → quota_error=True, is_showcase=True
TC2  analyze_posts 正常執行  → quota_error=False, is_showcase=False
TC3  analyze_posts 主動 showcase=True（無 429）→ quota_error=False, is_showcase=True
TC4  generate_daily_summary(showcase=True) 不呼叫 self.llm.chat
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


# ── 共用 helper ─────────────────────────────────────────────

def _make_search_result(title="測試文章"):
    sr = MagicMock()
    sr.title = title
    sr.content = "內容"
    sr.platform = "PTT"
    sr.source = "user"
    sr.url = "https://example.com"
    sr.region = "TW"
    return sr


def _make_analyzer():
    from analyzer.sentiment import SentimentAnalyzer
    analyzer = SentimentAnalyzer.__new__(SentimentAnalyzer)
    analyzer.logger = MagicMock()

    cm = MagicMock()
    cm.hero_key.return_value = None
    cm.get.return_value = None
    cm.increment_stat = MagicMock()
    cm.set = MagicMock()
    cm.save = MagicMock()
    cm.daily_summary_key.return_value = "ds_2026-05-08"

    llm = MagicMock()
    llm.cache_manager = cm
    analyzer.llm = llm
    return analyzer


def _make_429_error():
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 429
    return httpx.HTTPStatusError("429", request=MagicMock(), response=resp)


# ── TC1：429 → quota_error=True ─────────────────────────────

@pytest.mark.asyncio
async def test_tc1_429_triggers_quota_error():
    """batch_chat 拋出 429 → quota_error=True, is_showcase=True"""
    analyzer = _make_analyzer()
    analyzer.llm.batch_chat = AsyncMock(side_effect=_make_429_error())

    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts(
            [_make_search_result()],
            showcase=False,
        )

    assert result["is_showcase"] is True
    assert result["quota_error"] is True


# ── TC2：正常執行 → quota_error=False ───────────────────────

@pytest.mark.asyncio
async def test_tc2_normal_run_no_quota_error():
    """batch_chat 成功 → quota_error=False, is_showcase=False"""
    analyzer = _make_analyzer()
    analyzer.llm.batch_chat = AsyncMock(return_value=[
        {"sentiment": "positive", "sentiment_score": 0.8, "summary": "ok",
         "keywords": [], "relevance_score": 0.9, "category": "一般",
         "region": "TW", "original_language": "zh", "is_hero_focus": False,
         "detected_heroes": [], "translated_content": "", "events": []}
    ])

    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts(
            [_make_search_result()],
            showcase=False,
        )

    assert result["is_showcase"] is False
    assert result["quota_error"] is False


# ── TC3：主動 showcase=True（非 429）→ quota_error=False ────

@pytest.mark.asyncio
async def test_tc3_explicit_showcase_no_quota_error():
    """使用者主動 --showcase 旗標，未遇 429 → quota_error=False, is_showcase=True"""
    analyzer = _make_analyzer()
    # showcase=True 且 results=[] 會走 mock 路徑，但 quota_error 應為 False
    analyzer.llm.batch_chat = AsyncMock(return_value=[])

    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts(
            [_make_search_result()],
            showcase=True,
        )

    assert result["is_showcase"] is True
    assert result["quota_error"] is False


# ── TC4：generate_daily_summary(showcase=True) 不打 LLM ────

@pytest.mark.asyncio
async def test_tc4_showcase_skips_llm_in_daily_summary():
    """showcase=True 時 generate_daily_summary 走 fallback，不呼叫 self.llm.chat"""
    analyzer = _make_analyzer()
    analyzer.llm.chat = AsyncMock()

    mock_posts = [
        {"post": {"region": "TW", "content": "x", "detected_heroes": []},
         "analysis": {"sentiment": "neutral", "sentiment_score": 0.5,
                      "summary": "mock", "keywords": []}}
    ]

    with patch.object(analyzer, "_generate_fallback_summary", return_value={"mock": True}) as fb:
        await analyzer.generate_daily_summary(mock_posts, showcase=True)

    analyzer.llm.chat.assert_not_called()
    fb.assert_called_once()
