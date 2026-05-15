"""
Gemini primary / OpenAI secondary provider wrapper.

P70.4 keeps provider selection out of SentimentAnalyzer business logic.
"""

import logging
from typing import Optional, Union, List

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

import config
from analyzer.gemini_client import GeminiClient
from analyzer.llm_client import LLMClient

logger = logging.getLogger(__name__)


class FallbackLLMClient:
    """Use Gemini first; fallback to OpenAI for provider-level failures."""

    CONCURRENCY_LIMIT = GeminiClient.CONCURRENCY_LIMIT

    def __init__(
        self,
        primary: Optional[GeminiClient] = None,
        fallback: Optional[LLMClient] = None,
        enable_openai: Optional[bool] = None,
    ):
        self.primary = primary or GeminiClient()
        self.logger = logging.getLogger(f"{__name__}.FallbackLLMClient")

        if enable_openai is False:
            self.fallback = None
        elif fallback is not None:
            self.fallback = fallback
        elif config.OPENAI_FALLBACK_ENABLED and config.OPENAI_API_KEY:
            self.fallback = LLMClient(cache_manager=self.primary.cache_manager)
        else:
            self.fallback = None

    @property
    def cache_manager(self):
        return self.primary.cache_manager

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
        return self.fallback is not None and self._is_provider_failure(exc)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:
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
            self.logger.warning(
                "Gemini provider failure (%s); switching single chat to OpenAI fallback",
                type(exc).__name__,
            )
            return await self.fallback.chat(
                system_prompt,
                user_prompt,
                json_mode=json_mode,
                temperature=temperature,
                response_schema=response_schema,
            )

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: Optional[int] = None,
        response_schema: Optional[dict] = None,
    ) -> List[Union[dict, str]]:
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
            self.logger.warning(
                "Gemini provider failure (%s); switching batch to OpenAI fallback",
                type(exc).__name__,
            )
            return await self.fallback.batch_chat(
                system_prompt,
                user_prompts,
                json_mode=json_mode,
                concurrency=LLMClient.CONCURRENCY_LIMIT,
                response_schema=response_schema,
            )
