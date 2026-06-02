"""P105 OpenRouter provider client（OpenAI-compatible）。

OpenRouter 提供 OpenAI 相容 API，故繼承 ``LLMClient``，覆寫：

* ``__init__``：改用 ``OPENROUTER_API_KEY`` + ``OPENROUTER_BASE_URL`` 建 ``AsyncOpenAI``，
  並建獨立的 P90 budget ledger（高上限停損，與 Gemini/OpenAI 分開計數）。
* ``_prompt_cache_key``：加 ``"openrouter:<model>"`` 前綴，避免快取污染（R-P105-4）。
* ``chat``：cache miss 時先過 budget 停損守門（R-P105-5）再呼叫父類 chat。

複用 ``LLMClient`` 的 ``chat`` 核心 / ``batch_chat`` / ``_build_response_format`` /
``_to_openai_json_schema`` / retry。滿足 ``LLMProviderClient`` Protocol。

budget 停損（R-P105-5）：OpenRouter 為 6/5 對賭要「燒額度」，故上限
（``OPENROUTER_DAILY_BUDGET``）預設設高、正常燒不到，純防 bug 失控瞬間燒爆；獨立
state 檔避免與 Gemini「省額度」ledger 互相干擾。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, Union

from openai import AsyncOpenAI

import config
from analyzer.cache_manager import CacheManager
from analyzer.llm_budget import LLMBudgetManager, LLMBudgetSkip
from analyzer.llm_client import LLMClient
from analyzer.run_context import build_run_context

logger = logging.getLogger(__name__)


class OpenRouterClient(LLMClient):
    """OpenRouter（OpenAI-compatible）client；繼承 LLMClient 並改接 OpenRouter 端點。"""

    CONCURRENCY_LIMIT = 1
    MODEL = ""  # 由建構參數或 config.OPENROUTER_MODEL 決定

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_manager: Optional[CacheManager] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or config.OPENROUTER_API_KEY
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url or config.OPENROUTER_BASE_URL,
        )
        self.model = model or config.OPENROUTER_MODEL or self.MODEL
        self.logger = logging.getLogger(f"{__name__}.OpenRouterClient")
        self._cm = cache_manager or CacheManager()
        self._save_lock = asyncio.Lock()
        # P105.1 per-model 獨立 budget ledger：state 檔含 sanitize 後 model 名、上限讀
        # OPENROUTER_MODEL_BUDGETS（無對應退回 OPENROUTER_DAILY_BUDGET），避免多 model
        # 共用計數互相干擾；高上限停損純防 bug 失控燒爆，與 Gemini/OpenAI 分開計數。
        state_path, max_budget = self._resolve_model_budget(self.model)
        self._budget_manager = LLMBudgetManager(
            state_path,
            max_daily_llm_calls=max_budget,
            cooldown_minutes=config.LLM_BUDGET_COOLDOWN_MINUTES,
            retention_days=config.LLM_BUDGET_RETENTION_DAYS,
        )

    @staticmethod
    def _resolve_model_budget(model: str):
        """依 model 解出 (budget state 檔路徑, 每日上限)，per-model 隔離。

        有 model：state 檔加 sanitize 後 model 名（非 ``[\\w.\\-]`` 字元→``_``，含 ``/``，
        防 path traversal），上限讀 ``OPENROUTER_MODEL_BUDGETS``（無對應退回總上限）。
        無 model：退回 S2 單一 state 檔 + ``OPENROUTER_DAILY_BUDGET``（向後相容）。
        """
        base = Path(config.OPENROUTER_BUDGET_STATE_FILE)
        if not model:
            return base, config.OPENROUTER_DAILY_BUDGET
        safe = re.sub(r"[^\w.\-]", "_", model)
        state_path = base.parent / f"openrouter_budget_{safe}.json"
        max_budget = config.OPENROUTER_MODEL_BUDGETS.get(model, config.OPENROUTER_DAILY_BUDGET)
        return state_path, max_budget

    def _prompt_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        # 含 provider+model 前綴：避免與 OpenAI／其他 model 共用快取造成污染（R-P105-4）。
        md5 = hashlib.md5(
            f"openrouter:{self.model}|{system_prompt}|{user_prompt}".encode("utf-8")
        ).hexdigest()
        return CacheManager.prompt_key(md5)

    # ── budget 停損守門（仿 GeminiClient P90 介面，duck-typed 供 provider_budget 呼叫）──
    def _run_date(self) -> str:
        return build_run_context(timezone_name=config.TIMEZONE).run_date

    def _budget(self) -> Optional[LLMBudgetManager]:
        return getattr(self, "_budget_manager", None)

    def _ensure_budget_for_provider_call(self, *, record_call: bool = True) -> None:
        budget = self._budget()
        if budget is None:
            return
        run_date = self._run_date()
        decision = budget.decide(run_date)
        if not decision.should_call_llm:
            self.logger.warning(
                "OpenRouter budget/cooldown active: decision=%s reason=%s used=%s/%s",
                decision.decision,
                decision.reason,
                decision.snapshot.get("llm_calls_used"),
                decision.snapshot.get("max_daily_llm_calls"),
            )
            raise LLMBudgetSkip(decision)
        if record_call:
            budget.record_llm_call(run_date)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:
        # 僅 cache miss（將真打 API）才過 budget 停損守門，避免 cache hit 誤記呼叫。
        if self._cm.get(self._prompt_cache_key(system_prompt, user_prompt)) is None:
            self._ensure_budget_for_provider_call()
        return await super().chat(
            system_prompt,
            user_prompt,
            json_mode=json_mode,
            temperature=temperature,
            response_schema=response_schema,
        )
