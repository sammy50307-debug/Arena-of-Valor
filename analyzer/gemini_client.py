"""
Gemini LLM å®¢æˆ¶ç«????´æ¥?¼å« REST API??
ä¸ä½¿??google-generativeai å¥—ä»¶ï¼ˆé?è¦?Rustï¼‰ï?
?¹ç”¨ httpx ?´æ¥?¼å« Gemini REST APIï¼Œå??¨ç›¸å®?Python 3.8??"""

import asyncio
import json
import logging
from typing import Optional, Union, List

import httpx

import config

logger = logging.getLogger(__name__)

# Gemini REST API ç«¯é?
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.5-pro"  # ä½¿ç”¨?…ç›®?æ–¹æ¡ˆç‚º Pro


class GeminiClient:
    """
    ?é? REST API ?¼å« Google Geminiï¼Œæ”¯??JSON è¼¸å‡º??    å®Œå…¨ä¸ä?è³?google-generativeai å¥—ä»¶??    """

    MAX_RETRIES = 5

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
        ?¼å« Gemini API ?²è?å°è©±??
        Args:
            system_prompt: ç³»çµ±?ç¤ºè©?            user_prompt: ä½¿ç”¨?…æ?ç¤ºè?
            json_mode: ?¯å¦å¼·åˆ¶è¦æ? JSON è¼¸å‡º
            temperature: ?¢å‡ºå¤šæ¨£?§ï?0=ç©©å?ï¼?=?µæ?ï¼?
        Returns:
            json_mode=True ?‚å???dictï¼Œå¦?‡å???str
        """
        url = (
            f"{GEMINI_API_BASE}/{GEMINI_MODEL}"
            f":generateContent?key={self.api_key}"
        )

        # å¦‚æ?è¦?JSON è¼¸å‡ºï¼Œåœ¨ system prompt è£¡å?å¼·èª¿ä¸€æ¬?        if json_mode:
            system_prompt += "\n\n?è?ï¼šä??„å?è¦†å??ˆæ˜¯?‰æ???JSON ?¼å?ï¼Œä?å¾—å??«ä»»ä½?JSON ä¹‹å??„æ?å­—ã€markdown æ¨™è??–èªª?ã€?

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"[ç³»çµ±?‡ä»¤]\n{system_prompt}\n\n"
                                f"[ä½¿ç”¨?…è¼¸?¥]\n{user_prompt}"
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

                # ?–å‡º?æ??‡å?
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )

                if json_mode:
                    # æ¸…ç??¯èƒ½??markdown code block ?…è£¹
                    text = text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    return json.loads(text)

                return text

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"Gemini API HTTP ?¯èª¤ (ç¬?{attempt} æ¬?: {e.response.status_code}"
                )
                if attempt == self.MAX_RETRIES:
                    raise
                    
                if e.response.status_code == 429:
                    # Rate limitï¼Œç?å¾…å??è©¦
                    await asyncio.sleep(5 * attempt)  # ? å¤§ç­‰å??‚é?
                else:
                    await asyncio.sleep(1)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                self.logger.warning(f"?æ?è§??å¤±æ? (ç¬?{attempt} æ¬?: {e}")
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
        ?¹æ¬¡?¼å« Gemini APIï¼Œæ”¯?´ä¸¦è¡Œæ§?¶ã€?        ?è²»é¡åº¦?åˆ¶æ¯å???15 æ¬¡ï?ä¸¦è??¸è¨­ä½ä?é»ã€?        """
        semaphore = asyncio.Semaphore(concurrency)
        results: List[Union[dict, str]] = [{} for _ in user_prompts]

        async def _call(idx: int, prompt: str):
            async with semaphore:
                try:
                    result = await self.chat(system_prompt, prompt, json_mode)
                    results[idx] = result
                    # å¼·åˆ¶? å…¥ 4.5 ç§’å†·?»ï??¿å?è¶…é??è²» rate limit (15 RPM)
                    await asyncio.sleep(4.5)
                except Exception as e:
                    self.logger.error(f"?¹æ¬¡?¼å« #{idx} å¤±æ?: {e}")
                    results[idx] = {"error": str(e)}

        await asyncio.gather(*[_call(i, p) for i, p in enumerate(user_prompts)])
        return results


# ?€?€ ?¯ç›´?¥åŸ·è¡Œç????æ¸¬è©¦ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        client = GeminiClient()
        result = await client.chat(
            system_prompt="ä½ æ˜¯è¼¿æ??†æ?å¸«ï?è«‹å???JSON??,
            user_prompt='?†æ??™æ®µ?‡å??„æ?ç·’ï??Œå‚³èªªå?æ±ºæ?è¿‘ç??°è‹±?„å¥½å¼·ï???,
            json_mode=True,
        )
        print("Gemini ?æ?:", result)

    asyncio.run(main())
