"""LLM provider client protocol shared by provider routing code."""

from __future__ import annotations

from typing import Any, List, Optional, Protocol, Union, runtime_checkable


@runtime_checkable
class LLMProviderClient(Protocol):
    """Minimum async contract used by the AOV analyzer LLM path."""

    CONCURRENCY_LIMIT: int

    @property
    def cache_manager(self) -> Any:
        """Cache manager compatible with the existing Gemini/OpenAI clients."""

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:
        """Analyze one prompt and return either structured JSON or text."""

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: Optional[int] = None,
        response_schema: Optional[dict] = None,
    ) -> List[Union[dict, str]]:
        """Analyze multiple prompts with the same system prompt."""
