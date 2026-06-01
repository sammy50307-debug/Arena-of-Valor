from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

import config
from analyzer.llm_budget import BudgetDecision, LLMBudgetSkip, REASON_BUDGET_EXHAUSTED
from analyzer.provider_router import (
    ProviderRouteBlocked,
    ProviderRouter,
    ProviderSlot,
    build_default_llm_client,
    normalize_provider_diagnostics,
)


def _make_429_error():
    response = httpx.Response(429, request=httpx.Request("POST", "https://example.test"))
    return httpx.HTTPStatusError("429", request=response.request, response=response)


def test_build_default_client_keeps_legacy_path_when_router_disabled(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER_ROUTER_ENABLED", False)
    fake_client = MagicMock()

    with patch("analyzer.fallback_llm_client.FallbackLLMClient", return_value=fake_client):
        client = build_default_llm_client()

    assert client is fake_client


def test_build_default_client_wraps_primary_when_router_enabled(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER_ROUTER_ENABLED", True)
    fake_client = MagicMock()
    fake_client.CONCURRENCY_LIMIT = 1
    fake_client.cache_manager = MagicMock()

    with patch("analyzer.fallback_llm_client.FallbackLLMClient", return_value=fake_client):
        client = build_default_llm_client()

    assert isinstance(client, ProviderRouter)
    assert client.primary is fake_client


@pytest.mark.asyncio
async def test_provider_router_delegates_when_no_candidate_slot_enabled():
    primary = MagicMock()
    primary.chat = AsyncMock(return_value={"ok": True})
    primary.cache_manager = MagicMock()

    router = ProviderRouter(
        primary=primary,
        router_enabled=True,
        experimental_enabled=False,
        slots=[ProviderSlot("groq", "openai_compatible", enabled=False)],
    )

    result = await router.chat("sys", "user")

    assert result == {"ok": True}
    primary.chat.assert_awaited_once()
    diagnostics = router.provider_diagnostics()
    assert diagnostics["route_status"] == "router_enabled_primary_only"
    assert diagnostics["slots"][0]["status"] == "disabled_by_default"


@pytest.mark.asyncio
async def test_provider_router_blocks_enabled_candidate_without_provider_call():
    primary = MagicMock()
    primary.batch_chat = AsyncMock(return_value=[{"ok": True}])
    primary.cache_manager = MagicMock()

    router = ProviderRouter(
        primary=primary,
        router_enabled=True,
        experimental_enabled=True,
        slots=[
            ProviderSlot(
                "groq",
                "openai_compatible",
                enabled=True,
                secret_configured=True,
                status="ready_manual_only",
            )
        ],
    )

    with pytest.raises(ProviderRouteBlocked):
        await router.batch_chat("sys", ["user"])

    primary.batch_chat.assert_not_awaited()
    diagnostics = router.provider_diagnostics()
    assert diagnostics["route_status"] == "blocked_enabled_experimental_slot"
    assert diagnostics["attempts"][0]["provider"] == "groq"
    assert diagnostics["attempts"][0]["status"] == "blocked"


def test_provider_diagnostics_normalization_drops_raw_payload_fields():
    diagnostics = normalize_provider_diagnostics(
        {
            "schema_version": 1,
            "provider_truth": "raw-free provider routing snapshot only",
            "router_enabled": True,
            "experimental_free_providers_enabled": True,
            "active_provider": "groq",
            "route_status": "blocked_enabled_experimental_slot",
            "max_attempts": 2,
            "slots": [
                {
                    "name": "groq",
                    "provider_type": "openai_compatible",
                    "enabled": True,
                    "secret_configured": True,
                    "manual_only": True,
                    "status": "ready_manual_only",
                    "api_key": "must-not-survive",
                }
            ],
            "attempts": [
                {
                    "provider": "groq",
                    "role": "candidate",
                    "status": "blocked",
                    "prompt": "must-not-survive",
                    "response": "must-not-survive",
                }
            ],
        }
    )

    text = str(diagnostics)
    assert "must-not-survive" not in text
    assert diagnostics["slots"][0]["secret_configured"] is True
    assert diagnostics["attempts"][0]["provider"] == "groq"


def test_provider_diagnostics_normalization_coerces_bad_max_attempts():
    diagnostics = normalize_provider_diagnostics({"max_attempts": "not-an-int"})

    assert diagnostics["max_attempts"] == 1


@pytest.mark.asyncio
async def test_openai_fallback_passes_budget_guard_before_secondary_call():
    from analyzer.fallback_llm_client import FallbackLLMClient

    primary = MagicMock()
    primary.batch_chat = AsyncMock(side_effect=_make_429_error())
    primary._ensure_budget_for_provider_call = MagicMock()
    primary.cache_manager = MagicMock()

    fallback = MagicMock()
    fallback.batch_chat = AsyncMock(return_value=[{"sentiment": "neutral"}])

    client = FallbackLLMClient(primary=primary, fallbacks=[fallback])
    result = await client.batch_chat("sys", ["user"])

    assert result == [{"sentiment": "neutral"}]
    primary._ensure_budget_for_provider_call.assert_called_once_with(record_call=True)
    fallback.batch_chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_openai_fallback_budget_skip_blocks_secondary_call():
    from analyzer.fallback_llm_client import FallbackLLMClient

    decision = BudgetDecision(
        date="2026-05-22",
        should_call_llm=False,
        decision="skip_llm",
        reason=REASON_BUDGET_EXHAUSTED,
        snapshot={"decision": "skip_llm", "decision_reason": REASON_BUDGET_EXHAUSTED},
    )
    primary = MagicMock()
    primary.chat = AsyncMock(side_effect=_make_429_error())
    primary._ensure_budget_for_provider_call = MagicMock(side_effect=LLMBudgetSkip(decision))
    primary.cache_manager = MagicMock()

    fallback = MagicMock()
    fallback.chat = AsyncMock(return_value={"ok": True})

    client = FallbackLLMClient(primary=primary, fallbacks=[fallback])

    with pytest.raises(LLMBudgetSkip):
        await client.chat("sys", "user")

    fallback.chat.assert_not_awaited()
