"""
Gemini LLM 客戶端 — 直接呼叫 REST API。

包含大腦優化：支援 JSON Schema 結構化輸出、智慧 Semaphore 多工節流、以及本地零消耗快取！
"""

import asyncio
import json
import logging
import hashlib
from typing import Optional, Union, List

import httpx

import config

logger = logging.getLogger(__name__)

# Gemini REST API 端點
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODELS = [
    "gemini-2.0-flash", 
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]

CACHE_FILE = config.DATA_DIR / "llm_cache.json"


class GeminiClient:
    """
    透過 REST API 呼叫 Google Gemini，支援 JSON Schema 與本地快取。
    """

    MAX_RETRIES = 5
    CONCURRENCY_LIMIT = 3 # 預設最大併發數，避免瞬間觸發 429

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.logger = logging.getLogger(f"{__name__}.GeminiClient")
        self._cache = self._load_cache()
        self._cache_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(self.CONCURRENCY_LIMIT)

    def _load_cache(self) -> dict:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"快取載入失敗: {e}，將重建快取")
        return {}

    async def _save_cache(self):
        async with self._cache_lock:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.logger.error(f"快取寫入失敗: {e}")

    def _get_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        combined = f"{system_prompt}|{user_prompt}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None
    ) -> Union[dict, str]:
        
        # 1. 檢查快取
        cache_key = self._get_cache_key(system_prompt, user_prompt)
        if cache_key in self._cache:
            self.logger.info("   [⚡] 從本地快取提取結果，零延遲節省額度！")
            return self._cache[cache_key]

        if json_mode and not response_schema:
            system_prompt += "\n\n重要：你的回覆必須是有效的 JSON 格式，不得包含任何 JSON 之外的文字、markdown 標記或說明。"

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json" if json_mode else "text/plain",
            },
        }

        # 2. 注入 JSON Schema 實現原生結構化輸出
        if json_mode and response_schema:
            payload["generationConfig"]["responseSchema"] = response_schema

        # 限流重試邏輯 (Exponential Backoff with Model Tiering)
        models_to_try = GEMINI_MODELS.copy()
        current_model = models_to_try.pop(0)

        for attempt in range(1, self.MAX_RETRIES + 1):
            url = f"{GEMINI_API_BASE}/{current_model}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        self.logger.warning(
                            f"Gemini API 錯誤詳情 (HTTP {response.status_code}): {response.text}"
                        )
                    response.raise_for_status()
                    data = response.json()

                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )

                if json_mode:
                    text = text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    result = json.loads(text)
                else:
                    result = text

                # 3. 寫入快取
                self._cache[cache_key] = result
                await self._save_cache()
                return result

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"Gemini API HTTP 錯誤 (第 {attempt} 次) [{current_model}]: {e.response.status_code}"
                )
                
                if e.response.status_code == 429:
                    if models_to_try:
                        next_model = models_to_try.pop(0)
                        self.logger.warning(f"偵測到 429 額度耗盡！觸發替身防禦網，切換模型至：{next_model}")
                        current_model = next_model
                        await asyncio.sleep(1) # 短暫冷卻後切換
                        continue
                    else:
                        self.logger.error("所有備用模型均已遭遇 429 額度耗盡，拋出例外觸發終極斷路器。")
                        raise
                        
                if attempt == self.MAX_RETRIES:
                    raise
                await asyncio.sleep(2 ** attempt)

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
        response_schema: Optional[dict] = None
    ) -> List[Union[dict, str]]:
        """
        全自動降壓版批次分析。
        使用 Semaphore 控制併發，取代原本的循序延遲，提升速度。
        被斷路器捕捉到 429 會向上拋出以啟動 Showcase 模式。
        """
        sem = asyncio.Semaphore(concurrency)
        total = len(user_prompts)
        self.logger.info(f"開始批次分析 {total} 筆資料 (最大併發: {concurrency})")

        async def _analyze(i, prompt):
            async with sem:
                self.logger.info(f"   [⏳] 正在分析第 {i}/{total} 篇情報...")
                try:
                    return await self.chat(system_prompt, prompt, json_mode, response_schema=response_schema)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        raise e 
                    self.logger.error(f"   [!] 批次分析 #{i} 發生錯誤: {e}")
                    return {"error": str(e)}
                except Exception as e:
                    self.logger.error(f"   [!] 批次分析 #{i} 發生錯誤: {e}")
                    return {"error": str(e)}

        tasks = [_analyze(i, prompt) for i, prompt in enumerate(user_prompts, 1)]

        try:
            results = await asyncio.gather(*tasks)
            return list(results)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.logger.error("批次分析中發生 429 錯誤！已強制熔斷。")
                raise 
            return []

# ── 可直接執行的連線測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        client = GeminiClient()
        test_schema = {
            "type": "OBJECT",
            "properties": {
                "sentiment": {"type": "STRING", "enum": ["positive", "negative", "neutral"]},
            },
            "required": ["sentiment"]
        }
        result = await client.chat(
            system_prompt="你是輿情分析師。",
            user_prompt='分析這段文字的情緒：「傳說對決最近的新英雄好強！」',
            json_mode=True,
            response_schema=test_schema
        )
        print("Gemini 回應:", result)

    asyncio.run(main())
