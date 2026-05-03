"""
Unit tests for GeminiClient 429 wait-retry logic (P63.4-S1b).

Verifies that when all models return 429, the client waits 60s then 120s
before finally raising — instead of immediately triggering the circuit breaker.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


def _make_429_response():
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 429
    resp.text = "RESOURCE_EXHAUSTED"
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "429", request=MagicMock(), response=resp
    )
    return resp


@pytest.mark.asyncio
async def test_429_waits_60s_then_120s_before_raising():
    """模型全耗盡後，依序等待 60s、120s，第三輪才 raise。"""
    from analyzer.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    client.api_key = "test-key"
    client.logger = MagicMock()
    client._cache = {}
    client._cache_lock = asyncio.Lock()

    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    mock_response = _make_429_response()

    with patch("asyncio.sleep", side_effect=fake_sleep), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(httpx.HTTPStatusError):
            await client.chat("sys", "user")

    wait_calls = [s for s in sleep_calls if s in (60, 120)]
    assert wait_calls == [60, 120], f"期望 [60, 120]，實際 {wait_calls}"


@pytest.mark.asyncio
async def test_429_recovers_if_model_succeeds_after_wait():
    """等待 60s 後若模型恢復正常，應成功返回結果不 raise。"""
    from analyzer.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    client.api_key = "test-key"
    client.logger = MagicMock()
    client._cache = {}
    client._cache_lock = asyncio.Lock()

    call_count = 0

    def make_response(status, body=None):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status
        if status == 429:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=resp
            )
        else:
            resp.raise_for_status.return_value = None
            resp.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]
            }
        return resp

    from analyzer import gemini_client as gc_module
    all_models = gc_module.GEMINI_MODELS

    async def post_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # 前三輪（所有模型）回 429，第四輪成功
        if call_count <= len(all_models):
            return make_response(429)
        return make_response(200)

    with patch("asyncio.sleep", new=AsyncMock()), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=post_side_effect)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_save_cache", new=AsyncMock()):
            result = await client.chat("sys", "user")

    assert result == {"ok": True}
