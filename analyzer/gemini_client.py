"""
Gemini LLM 客戶端 — 直接呼叫 REST API。

不使用 google-generativeai 套件（需要 Rust），
改用 httpx 直接呼叫 Gemini REST API，完全相容 Python 3.8。
"""

import asyncio
import json
import logging
from typing import Optional, Union, List

import httpx

import config

logger = logging.getLogger(__name__)

# Gemini REST API 端點
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.5-flash"  # 確保使用目前可用的模型版本


class GeminiClient:
    """
    透過 REST API 呼叫 Google Gemini，支援 JSON 輸出。
    完全不依賴 google-generativeai 套件。
    """

    MAX_RETRIES = 3

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.logger = logging.getLogger(f"{__name__}.GeminiClient")

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> Union[dict, str]:
        """
        呼叫 Gemini API 進行對話。

        Args:
            system_prompt: 系統提示詞
            user_prompt: 使用者提示詞
            json_mode: 是否強制要求 JSON 輸出
            temperature: 產出多樣性（0=穩定，1=創意）

        Returns:
            json_mode=True 時回傳 dict，否則回傳 str
        """
        url = (
            f"{GEMINI_API_BASE}/{GEMINI_MODEL}"
            f":generateContent?key={self.api_key}"
        )

        # 如果要 JSON 輸出，在 system prompt 裡再強調一次
        if json_mode:
            system_prompt += "\n\n重要：你的回覆必須是有效的 JSON 格式，不得包含任何 JSON 之外的文字、markdown 標記或說明。"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"[系統指令]\n{system_prompt}\n\n"
                                f"[使用者輸入]\n{user_prompt}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json" if json_mode else "text/plain",
            },
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

                # 取出回應文字
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )

                if json_mode:
                    # 清理可能的 markdown code block 包裹
                    text = text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    return json.loads(text)

                return text

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"Gemini API HTTP 錯誤 (第 {attempt} 次): {e.response.status_code}"
                )
                if attempt == self.MAX_RETRIES:
                    raise
                    
                if e.response.status_code == 429:
                    # Rate limit，等待後重試
                    await asyncio.sleep(4 ** attempt)  # 加大等待時間
                else:
                    await asyncio.sleep(1)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                self.logger.warning(f"回應解析失敗 (第 {attempt} 次): {e}")
                if attempt == self.MAX_RETRIES:
                    raise
                await asyncio.sleep(1)

        return {} if json_mode else ""

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: int = 3,
    ) -> List[Union[dict, str]]:
        """
        批次呼叫 Gemini API，支援並行控制。
        免費額度限制每分鐘 15 次，並行數設低一點。
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: List[Optional[Union[dict, str]]] = [None] * len(user_prompts)

        async def _call(idx: int, prompt: str):
            async with semaphore:
                try:
                    result = await self.chat(system_prompt, prompt, json_mode)
                    results[idx] = result
                    # 加入小延遲，避免超過免費 rate limit
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.logger.error(f"批次呼叫 #{idx} 失敗: {e}")
                    results[idx] = {"error": str(e)}

        await asyncio.gather(*[_call(i, p) for i, p in enumerate(user_prompts)])
        return results


# ── 可直接執行的連線測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        client = GeminiClient()
        result = await client.chat(
            system_prompt="你是輿情分析師，請回傳 JSON。",
            user_prompt='分析這段文字的情緒：「傳說對決最近的新英雄好強！」',
            json_mode=True,
        )
        print("Gemini 回應:", result)

    asyncio.run(main())
