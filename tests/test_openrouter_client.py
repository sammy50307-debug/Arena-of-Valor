"""P105 S2 OpenRouter client 測試。

* 結構測試（mock，always 跑）：繼承契約、base_url、cache key 前綴、Protocol、registry。
* 真實呼叫測試（skipif：需 ``AOV_RUN_REALAPI=1`` + ``OPENROUTER_API_KEY``）：對 .env
  配置的各 model 真發 json_schema 請求驗 structured output 相容性（R-P105-1，會燒額度）。
  預設 skip，避免一般 pytest 每次都燒額度。
"""

import os

import pytest

import config
from analyzer.provider_clients.base import LLMProviderClient
from analyzer.provider_clients.openrouter_client import OpenRouterClient


def test_openrouter_init_uses_openrouter_endpoint(monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setattr(config, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    client = OpenRouterClient(model="deepseek/deepseek-chat")
    assert "openrouter.ai" in str(client.client.base_url)
    assert client.model == "deepseek/deepseek-chat"


def test_openrouter_cache_key_differs_by_model(monkeypatch):
    """R-P105-4：cache key 含 provider+model 前綴，不同 model 不共用快取。"""
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    a = OpenRouterClient(model="deepseek/deepseek-chat")._prompt_cache_key("s", "u")
    b = OpenRouterClient(model="minimax/minimax-01")._prompt_cache_key("s", "u")
    assert a != b


def test_openrouter_cache_key_differs_from_openai(monkeypatch):
    """OpenRouter 與 OpenAI 同 prompt/model 不共用 cache key（防污染 R-P105-4）。"""
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    from analyzer.llm_client import LLMClient

    or_key = OpenRouterClient(model="gpt-4o-mini")._prompt_cache_key("s", "u")
    oa_key = LLMClient(model="gpt-4o-mini")._prompt_cache_key("s", "u")
    assert or_key != oa_key


def test_openrouter_satisfies_protocol(monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    client = OpenRouterClient(model="x")
    assert isinstance(client, LLMProviderClient)


def test_openrouter_registered_in_registry(monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    from analyzer.provider_registry import REGISTRY, build_provider

    assert REGISTRY["openrouter"] is OpenRouterClient
    client = build_provider("openrouter", model="deepseek/deepseek-chat")
    assert isinstance(client, OpenRouterClient)
    assert client.model == "deepseek/deepseek-chat"


def test_openrouter_has_independent_budget_guard(monkeypatch):
    """R-P105-5：OpenRouter 有獨立 budget ledger + duck-typed budget guard 找得到。"""
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    client = OpenRouterClient(model="deepseek/deepseek-chat")
    assert client._budget() is not None
    assert hasattr(client, "_ensure_budget_for_provider_call")


@pytest.mark.asyncio
async def test_openrouter_chat_blocked_when_budget_exhausted(monkeypatch):
    """R-P105-5 停損：budget 耗盡時 chat 不打 API、raise LLMBudgetSkip。"""
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-or-test")
    from analyzer.llm_budget import BudgetDecision, LLMBudgetSkip

    client = OpenRouterClient(model="x")
    decision = BudgetDecision(
        date="2026-06-01",
        should_call_llm=False,
        decision="skip_llm",
        reason="budget_exhausted",
        snapshot={},
    )
    monkeypatch.setattr(client._budget_manager, "decide", lambda run_date: decision)
    monkeypatch.setattr(client._cm, "get", lambda k: None)

    with pytest.raises(LLMBudgetSkip):
        await client.chat("sys", "user")


# ── 真實呼叫（燒額度）：預設 skip，需 AOV_RUN_REALAPI=1 + OPENROUTER_API_KEY ──
_REALAPI = os.getenv("AOV_RUN_REALAPI") == "1" and bool(config.OPENROUTER_API_KEY)
_MODELS = {
    "MODEL": config.OPENROUTER_MODEL,
    "PRO": config.OPENROUTER_MODEL_PRO,
    "FLASH": config.OPENROUTER_MODEL_FLASH,
    "MINIMAX": config.OPENROUTER_MODEL_MINIMAX,
}


@pytest.mark.skipif(
    not _REALAPI,
    reason="需 AOV_RUN_REALAPI=1 + OPENROUTER_API_KEY（真實呼叫燒額度）",
)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "label",
    [
        "MODEL",
        "PRO",
        "FLASH",
        pytest.param(
            "MINIMAX",
            marks=pytest.mark.xfail(
                reason=(
                    "minimax-01 json_schema 模式回 choices=None，structured output "
                    "不相容（R-P105-1 實證）；不准當首發"
                ),
                strict=False,
            ),
        ),
    ],
)
async def test_openrouter_real_schema_compat(label):
    """對 .env 配置的 model 真發 json_schema 請求，驗 structured output 相容（R-P105-1）。"""
    model = _MODELS[label]
    if not model:
        pytest.skip(f"OPENROUTER_MODEL_{label} 未配置")
    client = OpenRouterClient(model=model)
    schema = {
        "type": "OBJECT",
        "properties": {
            "sentiment": {"type": "STRING"},
            "score": {"type": "NUMBER"},
        },
        "required": ["sentiment", "score"],
    }
    result = await client.chat(
        "你是輿情分析器，只回 JSON。",
        "分析這句的情緒：這英雄超強！",
        json_mode=True,
        response_schema=schema,
    )
    assert isinstance(result, dict), f"{label}({model}) 未回 dict：{type(result)}"
    assert "sentiment" in result, f"{label}({model}) 缺 sentiment：{result}"
