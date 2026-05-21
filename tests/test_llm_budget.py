from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from analyzer.llm_budget import (
    BILLING_TRUTH,
    BudgetDecision,
    LLMBudgetManager,
    LLMBudgetSkip,
    REASON_BUDGET_EXHAUSTED,
    REASON_COOLDOWN_ACTIVE,
    REASON_QUOTA_ERROR,
    REASON_STATE_MALFORMED,
)
from analyzer.gemini_client import GeminiClient


RUN_DATE = "2026-05-21"
NOW = datetime(2026, 5, 21, 4, 0, tzinfo=timezone.utc)


def _manager(tmp_path: Path, max_calls: int = 2) -> LLMBudgetManager:
    return LLMBudgetManager(
        tmp_path / "data" / "llm_budget_state.json",
        max_daily_llm_calls=max_calls,
        cooldown_minutes=60,
        retention_days=14,
    )


def test_budget_allows_under_budget(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=2)

    decision = manager.decide(RUN_DATE, now=NOW)

    assert decision.should_call_llm is True
    assert decision.snapshot["decision"] == "call_llm"
    assert decision.snapshot["billing_truth"] == BILLING_TRUTH


def test_budget_blocks_after_daily_limit(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=2)

    manager.record_llm_call(RUN_DATE, now=NOW)
    manager.record_llm_call(RUN_DATE, now=NOW)
    decision = manager.decide(RUN_DATE, now=NOW)

    assert decision.should_call_llm is False
    assert decision.reason == REASON_BUDGET_EXHAUSTED
    assert decision.snapshot["llm_calls_used"] == 2
    assert decision.snapshot["budget_exhausted"] is True


def test_quota_error_writes_active_cooldown(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=5)

    decision = manager.record_quota_error(RUN_DATE, now=NOW)
    payload = json.loads(manager.state_path.read_text(encoding="utf-8"))
    day = payload["days"][RUN_DATE]

    assert decision.should_call_llm is False
    assert decision.reason == REASON_COOLDOWN_ACTIVE
    assert day["quota_error_count"] == 1
    assert day["cooldown_reason"] == REASON_QUOTA_ERROR
    assert day["cooldown_until_utc"] == "2026-05-21T05:00:00Z"


def test_cooldown_expires_and_allows_calls(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=5)
    manager.record_quota_error(RUN_DATE, now=NOW)

    decision = manager.decide(RUN_DATE, now=NOW + timedelta(minutes=61))

    assert decision.should_call_llm is True
    assert decision.snapshot["cooldown_active"] is False


def test_malformed_state_fails_safe_without_provider_call(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=5)
    manager.state_path.parent.mkdir(parents=True, exist_ok=True)
    manager.state_path.write_text("{not-json", encoding="utf-8")

    decision = manager.decide(RUN_DATE, now=NOW)

    assert decision.should_call_llm is False
    assert decision.reason == REASON_STATE_MALFORMED


def test_budget_state_never_writes_raw_prompt_or_post_content(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=5)
    manager.record_llm_call(RUN_DATE, now=NOW)
    manager.record_quota_error(RUN_DATE, now=NOW)

    payload = manager.state_path.read_text(encoding="utf-8")

    assert "secret-api-key" not in payload
    assert "raw prompt" not in payload
    assert "https://example.test/post" not in payload
    assert "player-author" not in payload


def test_gemini_client_raises_budget_skip_before_provider_call(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=1)
    manager.record_llm_call(RUN_DATE, now=NOW)
    client = GeminiClient.__new__(GeminiClient)
    client.logger = MagicMock()
    client._budget_manager = manager
    client._run_date = lambda: RUN_DATE

    with pytest.raises(LLMBudgetSkip):
        client._ensure_budget_for_provider_call()


def test_gemini_client_preflight_check_does_not_consume_budget(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=1)
    client = GeminiClient.__new__(GeminiClient)
    client.logger = MagicMock()
    client._budget_manager = manager
    client._run_date = lambda: RUN_DATE

    client._ensure_budget_for_provider_call(record_call=False)

    assert manager.snapshot(RUN_DATE, now=NOW)["llm_calls_used"] == 0


@pytest.mark.asyncio
async def test_batch_chat_reraises_budget_skip_from_prompt_call():
    decision = BudgetDecision(
        date=RUN_DATE,
        should_call_llm=False,
        decision="skip_llm",
        reason=REASON_BUDGET_EXHAUSTED,
        snapshot={
            "llm_calls_used": 1,
            "max_daily_llm_calls": 1,
        },
    )
    client = GeminiClient.__new__(GeminiClient)
    client.logger = MagicMock()
    client._budget_manager = None
    client.preflight_check = AsyncMock(return_value=True)
    client.chat = AsyncMock(side_effect=LLMBudgetSkip(decision))

    with pytest.raises(LLMBudgetSkip):
        await client.batch_chat("system", ["prompt"])


@pytest.mark.asyncio
async def test_batch_chat_skips_before_preflight_when_remaining_budget_too_low(tmp_path: Path):
    manager = _manager(tmp_path, max_calls=1)
    client = GeminiClient.__new__(GeminiClient)
    client.logger = MagicMock()
    client._budget_manager = manager
    client._run_date = lambda: RUN_DATE
    client._cm = MagicMock()
    client._cm.get.return_value = None
    client.preflight_check = AsyncMock(return_value=True)

    with pytest.raises(LLMBudgetSkip):
        await client.batch_chat("system", ["prompt one", "prompt two"])

    client.preflight_check.assert_not_awaited()
