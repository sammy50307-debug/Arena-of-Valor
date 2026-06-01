"""P105 S1 provider 切換矩陣鎖。

驗 ``config.PRIMARY_PROVIDER`` 一行切換首發 provider，以及 registry / 多級
fallback 鏈的組裝。不真發 API：對 gemini/openai 驗回傳型別；OpenAI client 初始化
``AsyncOpenAI`` 需非空 key，故以 monkeypatch 注入測試 key。
"""

import pytest

import config
from analyzer.gemini_client import GeminiClient
from analyzer.llm_client import LLMClient
from analyzer.provider_registry import REGISTRY, build_provider


def test_registry_has_gemini_and_openai():
    assert REGISTRY["gemini"] is GeminiClient
    assert REGISTRY["openai"] is LLMClient


def test_build_provider_gemini_returns_gemini_client():
    assert isinstance(build_provider("gemini"), GeminiClient)


def test_build_provider_openai_returns_llm_client(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    assert isinstance(build_provider("openai"), LLMClient)


def test_build_provider_is_case_insensitive(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    assert isinstance(build_provider("OpenAI"), LLMClient)


def test_build_provider_unknown_raises():
    with pytest.raises(ValueError):
        build_provider("groq")


def test_primary_provider_gemini_default(monkeypatch):
    """預設 PRIMARY_PROVIDER=gemini → FallbackLLMClient.primary 是 GeminiClient。"""
    monkeypatch.setattr(config, "PRIMARY_PROVIDER", "gemini")
    from analyzer.fallback_llm_client import FallbackLLMClient

    client = FallbackLLMClient(enable_openai=False)
    assert isinstance(client.primary, GeminiClient)


def test_switch_primary_provider_to_openai(monkeypatch):
    """切 PRIMARY_PROVIDER=openai → FallbackLLMClient.primary 是 LLMClient。"""
    monkeypatch.setattr(config, "PRIMARY_PROVIDER", "openai")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    from analyzer.fallback_llm_client import FallbackLLMClient

    client = FallbackLLMClient(enable_openai=False)
    assert isinstance(client.primary, LLMClient)


def test_build_default_client_switches_primary_to_openai(monkeypatch):
    """計畫 verify：切 PRIMARY_PROVIDER=openai 後 build_default_llm_client().primary 是 LLMClient。"""
    monkeypatch.setattr(config, "PRIMARY_PROVIDER", "openai")
    monkeypatch.setattr(config, "PROVIDER_ROUTER_ENABLED", False)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(config, "FALLBACK_PROVIDERS", [])
    from analyzer.provider_router import build_default_llm_client

    client = build_default_llm_client()
    assert isinstance(client.primary, LLMClient)


def test_fallbacks_default_openai_gated_off_without_key(monkeypatch):
    """沿用 P70.4 gating：FALLBACK_PROVIDERS=[openai] 但無 key → fallbacks 為空。"""
    monkeypatch.setattr(config, "PRIMARY_PROVIDER", "gemini")
    monkeypatch.setattr(config, "FALLBACK_PROVIDERS", ["openai"])
    monkeypatch.setattr(config, "OPENAI_FALLBACK_ENABLED", True)
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    from analyzer.fallback_llm_client import FallbackLLMClient

    client = FallbackLLMClient()
    assert client.fallback_configured is False


@pytest.mark.asyncio
async def test_fallbacks_chain_multilevel():
    """多級 fallbacks：首發＋第一級皆 429，逐級切到第二級成功。"""
    from unittest.mock import AsyncMock, MagicMock

    import httpx

    from analyzer.fallback_llm_client import FallbackLLMClient

    def _429():
        resp = httpx.Response(429, request=httpx.Request("POST", "https://e.test"))
        return httpx.HTTPStatusError("429", request=resp.request, response=resp)

    primary = MagicMock()
    primary.chat = AsyncMock(side_effect=_429())
    primary.cache_manager = MagicMock()
    fb1 = MagicMock()
    fb1.chat = AsyncMock(side_effect=_429())
    fb2 = MagicMock()
    fb2.chat = AsyncMock(return_value={"ok": True})

    client = FallbackLLMClient(primary=primary, fallbacks=[fb1, fb2])
    result = await client.chat("sys", "user")

    assert result == {"ok": True}
    fb1.chat.assert_awaited_once()
    fb2.chat.assert_awaited_once()
    assert client.last_fallback_used is True
