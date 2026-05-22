"""
P70.4 OpenAI fallback tests.

All tests mock provider clients; no real Gemini/OpenAI API call is made.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def _make_429_error():
    response = httpx.Response(429, request=httpx.Request("POST", "https://example.test"))
    return httpx.HTTPStatusError("429", request=response.request, response=response)


def _make_openai_response(content='{"ok": true}'):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def _make_search_result(title="測試文章"):
    sr = MagicMock()
    sr.title = title
    sr.content = "內容"
    sr.platform = "PTT"
    sr.source = "user"
    sr.url = "https://example.com"
    sr.region = "TW"
    return sr


@pytest.mark.asyncio
async def test_fallback_batch_chat_uses_openai_after_gemini_429():
    from analyzer.fallback_llm_client import FallbackLLMClient

    primary = MagicMock()
    primary.batch_chat = AsyncMock(side_effect=_make_429_error())
    primary.cache_manager = MagicMock()

    fallback = MagicMock()
    fallback.batch_chat = AsyncMock(return_value=[{"sentiment": "neutral"}])

    client = FallbackLLMClient(primary=primary, fallback=fallback)

    result = await client.batch_chat(
        system_prompt="sys",
        user_prompts=["user"],
        json_mode=True,
        response_schema={"type": "OBJECT"},
    )

    assert result == [{"sentiment": "neutral"}]
    fallback.batch_chat.assert_awaited_once()
    assert fallback.batch_chat.await_args.kwargs["concurrency"] == 1
    assert fallback.batch_chat.await_args.kwargs["response_schema"] == {"type": "OBJECT"}
    assert client.fallback_configured is True
    assert client.last_fallback_used is True


@pytest.mark.asyncio
async def test_sentiment_analyze_posts_stays_production_after_openai_fallback():
    from analyzer.fallback_llm_client import FallbackLLMClient
    from analyzer.sentiment import SentimentAnalyzer

    cache = MagicMock()
    cache.hero_key.return_value = None
    cache.get.return_value = None
    cache.increment_stat = MagicMock()

    primary = MagicMock()
    primary.batch_chat = AsyncMock(side_effect=_make_429_error())
    primary.cache_manager = cache

    fallback = MagicMock()
    fallback.batch_chat = AsyncMock(return_value=[
        {
            "reasoning": "ok",
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "region": "TW",
            "original_language": "zh",
            "translated_content": "",
            "category": "一般",
            "keywords": [],
            "summary": "fallback ok",
            "relevance_score": 0.8,
            "is_hero_focus": False,
            "events": [],
        }
    ])

    client = FallbackLLMClient(primary=primary, fallback=fallback)
    analyzer = SentimentAnalyzer(llm_client=client)

    with patch.object(analyzer, "_compress_content", return_value="x"):
        result = await analyzer.analyze_posts([_make_search_result()], showcase=False)

    assert result["is_showcase"] is False
    assert result["quota_error"] is False
    assert result["posts"][0]["analysis"]["summary"] == "fallback ok"
    assert result["provider_diagnostics"]["openai_fallback_configured"] is True
    assert result["provider_diagnostics"]["openai_fallback_used"] is True


@pytest.mark.asyncio
async def test_fallback_batch_chat_reraises_without_openai_key():
    from analyzer.fallback_llm_client import FallbackLLMClient

    primary = MagicMock()
    primary.batch_chat = AsyncMock(side_effect=_make_429_error())
    primary.cache_manager = MagicMock()

    client = FallbackLLMClient(primary=primary, enable_openai=False)

    with pytest.raises(httpx.HTTPStatusError):
        await client.batch_chat("sys", ["user"])
    assert client.fallback_configured is False
    assert client.last_fallback_used is False


@pytest.mark.asyncio
async def test_openai_client_uses_json_schema_response_format():
    from analyzer.llm_client import LLMClient

    create = AsyncMock(return_value=_make_openai_response())
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create),
        )
    )

    cache = MagicMock()
    cache.get.return_value = None

    client = LLMClient.__new__(LLMClient)
    client.client = fake_client
    client.model = "gpt-4o-mini"
    client.logger = MagicMock()
    client._cm = cache
    client._save_lock = __import__("asyncio").Lock()

    result = await client.chat(
        "sys",
        "user",
        json_mode=True,
        response_schema={
            "type": "OBJECT",
            "properties": {"ok": {"type": "BOOLEAN"}},
            "required": ["ok"],
        },
    )

    assert result == {"ok": True}
    kwargs = create.await_args.kwargs
    assert kwargs["response_format"]["type"] == "json_schema"
    schema = kwargs["response_format"]["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert schema["properties"]["ok"]["type"] == "boolean"
    cache.set.assert_called_once()


def test_sentiment_analyzer_defaults_to_fallback_client():
    with patch("analyzer.sentiment.build_default_llm_client") as fallback_cls:
        fallback = MagicMock()
        fallback_cls.return_value = fallback

        from analyzer.sentiment import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

    assert analyzer.llm is fallback
    fallback_cls.assert_called_once()
