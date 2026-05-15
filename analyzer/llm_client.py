"""
OpenAI LLM API 客戶端封裝。

保留舊版 Chat Completions API，原因是本專案仍鎖 Python 3.8 與
openai<1.56；P70.4 只做 fallback，不進行 SDK / Responses API migration。
"""

import asyncio
import hashlib
import json
import logging
from typing import Any, Optional, Union, List

from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

import config
from analyzer.cache_manager import CacheManager

logger = logging.getLogger(__name__)


_JSON_SCHEMA_TYPE_MAP = {
    "OBJECT": "object",
    "STRING": "string",
    "NUMBER": "number",
    "INTEGER": "integer",
    "BOOLEAN": "boolean",
    "ARRAY": "array",
}


def _to_openai_json_schema(schema: Any) -> Any:
    """Convert Gemini-style uppercase schema types to standard JSON Schema."""
    if isinstance(schema, list):
        return [_to_openai_json_schema(item) for item in schema]
    if not isinstance(schema, dict):
        return schema

    converted = {}
    for key, value in schema.items():
        if key == "type" and isinstance(value, str):
            converted[key] = _JSON_SCHEMA_TYPE_MAP.get(value.upper(), value.lower())
        elif key == "properties" and isinstance(value, dict):
            converted[key] = {
                prop: _to_openai_json_schema(prop_schema)
                for prop, prop_schema in value.items()
            }
        else:
            converted[key] = _to_openai_json_schema(value)
    return converted


class LLMClient:
    """
    OpenAI Chat Completions client.

    Interface mirrors GeminiClient enough for SentimentAnalyzer:
    chat(), batch_chat(), and cache_manager are all available.
    """

    MAX_RETRIES = 3
    CONCURRENCY_LIMIT = 1
    MODEL = config.OPENAI_FALLBACK_MODEL

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_manager: Optional[CacheManager] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model or self.MODEL
        self.logger = logging.getLogger(f"{__name__}.LLMClient")
        self._cm = cache_manager or CacheManager()
        self._save_lock = asyncio.Lock()

    @property
    def cache_manager(self) -> CacheManager:
        return self._cm

    def _prompt_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        md5 = hashlib.md5(f"{system_prompt}|{user_prompt}".encode("utf-8")).hexdigest()
        return CacheManager.prompt_key(md5)

    async def _save_cache(self) -> None:
        async with self._save_lock:
            self._cm.save()

    def _build_response_format(
        self,
        json_mode: bool,
        response_schema: Optional[dict],
    ) -> Optional[dict]:
        if not json_mode:
            return None
        if response_schema:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "aov_response",
                    "schema": _to_openai_json_schema(response_schema),
                    "strict": False,
                },
            }
        return {"type": "json_object"}

    @staticmethod
    def _should_retry_status(exc: APIStatusError) -> bool:
        status = getattr(exc, "status_code", None)
        return status == 429 or (status is not None and status >= 500)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:
        """
        Send one request to OpenAI.

        Returns parsed dict when json_mode=True, raw text otherwise.
        """
        cache_key = self._prompt_cache_key(system_prompt, user_prompt)
        cached = self._cm.get(cache_key)
        if cached is not None:
            self._cm.increment_stat("total_l2_hits")
            self.logger.info("   [⚡] OpenAI L2 快取命中，零 API 呼叫")
            return cached

        self._cm.increment_stat("total_misses")

        if json_mode and not response_schema:
            system_prompt += "\n\n重要：你的回覆必須是有效的 JSON 格式，不得包含任何 JSON 之外的文字、markdown 標記或說明。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000,
        }
        response_format = self._build_response_format(json_mode, response_schema)
        if response_format:
            kwargs["response_format"] = response_format

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""

                if json_mode:
                    result = json.loads(content)
                else:
                    result = content

                self._cm.set(cache_key, result)
                await self._save_cache()
                return result

            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                self.logger.warning(
                    "OpenAI API provider failure (attempt %s/%s): %s",
                    attempt,
                    self.MAX_RETRIES,
                    type(e).__name__,
                )
                if attempt >= self.MAX_RETRIES:
                    raise
                await asyncio.sleep(2 ** attempt)

            except APIStatusError as e:
                if not self._should_retry_status(e):
                    raise
                self.logger.warning(
                    "OpenAI API status failure (attempt %s/%s): HTTP %s",
                    attempt,
                    self.MAX_RETRIES,
                    getattr(e, "status_code", "unknown"),
                )
                if attempt >= self.MAX_RETRIES:
                    raise
                await asyncio.sleep(2 ** attempt)

            except json.JSONDecodeError as e:
                self.logger.error("OpenAI 回傳 JSON 解析失敗: %s", e)
                if attempt >= self.MAX_RETRIES:
                    raise
                await asyncio.sleep(1)

        raise RuntimeError("OpenAI chat exhausted retries without returning")

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: Optional[int] = None,
        response_schema: Optional[dict] = None,
    ) -> List[Union[dict, str]]:
        """Batch OpenAI calls with conservative concurrency."""
        concurrency = concurrency if concurrency is not None else self.CONCURRENCY_LIMIT
        semaphore = asyncio.Semaphore(concurrency)
        results: List[Optional[Union[dict, str]]] = [None] * len(user_prompts)

        async def _call(idx: int, prompt: str) -> None:
            async with semaphore:
                try:
                    results[idx] = await self.chat(
                        system_prompt,
                        prompt,
                        json_mode=json_mode,
                        response_schema=response_schema,
                    )
                except Exception as e:
                    self.logger.error("OpenAI 批次呼叫 #%s 失敗: %s", idx, type(e).__name__)
                    results[idx] = {"error": str(e)}

        tasks = [_call(i, prompt) for i, prompt in enumerate(user_prompts)]
        await asyncio.gather(*tasks)
        return list(results)
