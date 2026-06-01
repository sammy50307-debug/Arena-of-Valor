"""
Gemini primary / OpenAI secondary provider wrapper.

P70.4 keeps provider selection out of SentimentAnalyzer business logic.
"""

import logging
from typing import Optional, Union, List

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

import config
from analyzer.llm_client import LLMClient
from analyzer.provider_budget import ensure_budget_for_provider_call
from analyzer.provider_clients.base import LLMProviderClient
from analyzer.provider_registry import build_provider
from analyzer.provider_router import build_provider_diagnostics

logger = logging.getLogger(__name__)


class FallbackLLMClient:
    """首發 provider 優先；provider 級失敗時依序切換到多級 fallback 鏈。

    P105 起首發與 fallback 皆由 ``config.PRIMARY_PROVIDER`` / ``FALLBACK_PROVIDERS``
    透過 ``provider_registry`` 動態組裝（顯式傳入的 ``primary``/``fallbacks`` 優先）。
    對外契約（``cache_manager`` / ``CONCURRENCY_LIMIT`` / ``chat`` / ``batch_chat`` /
    ``fallback_configured`` / ``last_fallback_used`` / ``provider_diagnostics``）不變。
    """

    def __init__(
        self,
        primary: Optional[LLMProviderClient] = None,
        fallbacks: Optional[List[LLMProviderClient]] = None,
        enable_openai: Optional[bool] = None,
    ):
        self.primary: LLMProviderClient = primary or build_provider(
            config.PRIMARY_PROVIDER, model=config.PRIMARY_MODEL or None
        )
        self.logger = logging.getLogger(f"{__name__}.FallbackLLMClient")
        self.last_fallback_used = False

        if enable_openai is False:
            self.fallbacks: List[LLMProviderClient] = []
        elif fallbacks is not None:
            self.fallbacks = list(fallbacks)
        else:
            self.fallbacks = self._build_default_fallbacks()

    def _build_default_fallbacks(self) -> List[LLMProviderClient]:
        """依 config.FALLBACK_PROVIDERS 組多級 fallback，沿用既有 provider gating。"""
        fallbacks: List[LLMProviderClient] = []
        for name in config.FALLBACK_PROVIDERS:
            key = name.strip().lower()
            if key == "openai":
                # 沿用 P70.4 gating：未啟用或無 key 則略過（不硬建呼叫時必爆的 client）。
                if not (config.OPENAI_FALLBACK_ENABLED and config.OPENAI_API_KEY):
                    continue
                fallbacks.append(
                    build_provider("openai", cache_manager=self.primary.cache_manager)
                )
            else:
                fallbacks.append(
                    build_provider(key, cache_manager=self.primary.cache_manager)
                )
        return fallbacks

    @property
    def CONCURRENCY_LIMIT(self) -> int:
        # 反映實際首發 provider 的併發上限（不再寫死 Gemini）。
        return getattr(self.primary, "CONCURRENCY_LIMIT", 1)

    @property
    def cache_manager(self):
        return self.primary.cache_manager

    @property
    def fallback_configured(self) -> bool:
        return bool(self.fallbacks)

    def provider_diagnostics(self) -> dict:
        attempts = []
        if self.last_fallback_used:
            attempts.append(
                {
                    "provider": "openai_fallback",
                    "role": "fallback",
                    "status": "called",
                    "failure_class": "",
                    "budget_decision": "",
                }
            )
        return build_provider_diagnostics(
            router_enabled=False,
            experimental_enabled=False,
            route_status="router_disabled_legacy_default",
            active_provider="gemini_primary",
            attempts=attempts,
        )

    @staticmethod
    def _is_provider_failure(exc: Exception) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            status = getattr(exc.response, "status_code", None)
            return status == 429 or (status is not None and status >= 500)
        if isinstance(exc, httpx.RequestError):
            return True
        if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError)):
            return True
        if isinstance(exc, APIStatusError):
            status = getattr(exc, "status_code", None)
            return status == 429 or (status is not None and status >= 500)
        return False

    def _should_fallback(self, exc: Exception) -> bool:
        provider_failure = self._is_provider_failure(exc)
        if provider_failure and not self.fallbacks:
            self.logger.warning(
                "Primary provider failure (%s) but no fallback provider available "
                "(FALLBACK_PROVIDERS=%s, OPENAI_FALLBACK_ENABLED=%s, OPENAI_API_KEY configured=%s)",
                type(exc).__name__,
                config.FALLBACK_PROVIDERS,
                config.OPENAI_FALLBACK_ENABLED,
                bool(config.OPENAI_API_KEY),
            )
        return bool(self.fallbacks) and provider_failure

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:
        self.last_fallback_used = False
        try:
            return await self.primary.chat(
                system_prompt,
                user_prompt,
                json_mode=json_mode,
                temperature=temperature,
                response_schema=response_schema,
            )
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            ensure_budget_for_provider_call(self.primary)
            self.last_fallback_used = True
            last_exc: Exception = exc
            for fb in self.fallbacks:
                self.logger.warning(
                    "Primary provider failure (%s); switching single chat to fallback %s",
                    type(exc).__name__,
                    type(fb).__name__,
                )
                try:
                    return await fb.chat(
                        system_prompt,
                        user_prompt,
                        json_mode=json_mode,
                        temperature=temperature,
                        response_schema=response_schema,
                    )
                except Exception as fb_exc:
                    last_exc = fb_exc
                    if not self._is_provider_failure(fb_exc):
                        raise  # 非 provider 失敗（如 schema 解析錯）不再試下一級
                    continue  # provider 失敗，試下一級 fallback
            raise last_exc

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: Optional[int] = None,
        response_schema: Optional[dict] = None,
    ) -> List[Union[dict, str]]:
        self.last_fallback_used = False
        try:
            return await self.primary.batch_chat(
                system_prompt,
                user_prompts,
                json_mode=json_mode,
                concurrency=concurrency,
                response_schema=response_schema,
            )
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            ensure_budget_for_provider_call(self.primary)
            self.last_fallback_used = True
            last_exc: Exception = exc
            for fb in self.fallbacks:
                self.logger.warning(
                    "Primary provider failure (%s); switching batch to fallback %s",
                    type(exc).__name__,
                    type(fb).__name__,
                )
                try:
                    return await fb.batch_chat(
                        system_prompt,
                        user_prompts,
                        json_mode=json_mode,
                        # fallback 沿用保守併發上限（與 P70.4 一致；多級異質鏈精細化待後續）
                        concurrency=LLMClient.CONCURRENCY_LIMIT,
                        response_schema=response_schema,
                    )
                except Exception as fb_exc:
                    last_exc = fb_exc
                    if not self._is_provider_failure(fb_exc):
                        raise
                    continue
            raise last_exc
