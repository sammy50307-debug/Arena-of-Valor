"""
LLM API 客戶端封裝。

支援 OpenAI GPT 系列，並透過 adapter pattern 可替換為其他 LLM。
內建重試與 rate limit 處理。
"""

import asyncio
import json
import logging
from typing import Optional, Union, List

from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError

import config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    封裝 OpenAI API 呼叫的客戶端。
    支援 JSON mode，可穩定輸出結構化資料。
    """

    MAX_RETRIES = 3
    MODEL = "gpt-4o-mini"  # 成本低、速度快，足以應付情緒分析

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or config.OPENAI_API_KEY)
        self.logger = logging.getLogger(f"{__name__}.LLMClient")

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> Union[dict, str]:
        """
        向 LLM 發送對話請求。

        Args:
            system_prompt: 系統提示詞
            user_prompt: 使用者提示詞
            json_mode: 是否啟用 JSON 輸出模式
            temperature: 創造力參數（0-1，越低越穩定）

        Returns:
            json_mode=True 時回傳 dict，否則回傳原始 str
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content

                if json_mode:
                    return json.loads(content)
                return content

            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                self.logger.warning(
                    f"LLM API 呼叫失敗 (第 {attempt} 次): {type(e).__name__}: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    wait = 2 ** attempt
                    self.logger.info(f"等待 {wait} 秒後重試...")
                    await asyncio.sleep(wait)
                else:
                    self.logger.error("已達最大重試次數，放棄呼叫。")
                    raise

            except json.JSONDecodeError as e:
                self.logger.error(f"LLM 回傳的 JSON 解析失敗: {e}")
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(1)
                else:
                    raise

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: int = 5,
    ) -> List[Union[dict, str]]:
        """
        批次呼叫 LLM API，支援並行控制。

        Args:
            system_prompt: 共用的系統提示詞
            user_prompts: 多個使用者提示詞
            json_mode: 是否啟用 JSON mode
            concurrency: 最大並行數

        Returns:
            與 user_prompts 順序對應的回應列表
        """
        semaphore = asyncio.Semaphore(concurrency)
        results = [None] * len(user_prompts)

        async def _call(idx: int, prompt: str):
            async with semaphore:
                try:
                    result = await self.chat(system_prompt, prompt, json_mode)
                    results[idx] = result
                except Exception as e:
                    self.logger.error(f"批次呼叫 #{idx} 失敗: {e}")
                    results[idx] = {"error": str(e)}

        tasks = [_call(i, p) for i, p in enumerate(user_prompts)]
        await asyncio.gather(*tasks)
        return results
