"""
Gemini LLM 客戶端 — 直接呼叫 REST API。

包含大腦優化：支援 JSON Schema 結構化輸出、智慧 Semaphore 多工節流、以及本地零消耗快取！
"""

import asyncio
import json
import logging
import hashlib
import re
from typing import Optional, Union, List

import httpx

import config
from analyzer.cache_manager import CacheManager
from analyzer.llm_budget import (
    BudgetDecision,
    LLMBudgetManager,
    LLMBudgetSkip,
    REASON_BUDGET_EXHAUSTED,
)
from analyzer.run_context import build_run_context

logger = logging.getLogger(__name__)

# Gemini REST API 端點
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
]


_SECRET_TEXT_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"sk-(?:or-v1-|proj-|ant-|live-)?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_\-]{20,}"),
]


def _redact_secret_text(text: object) -> str:
    """Redact API keys from error strings before they can reach logs or reports."""
    value = str(text)
    value = re.sub(r"([?&]key=)[^&\s'\"<>]+", r"\1***", value)
    for pattern in _SECRET_TEXT_PATTERNS:
        value = pattern.sub("***REDACTED***", value)
    return value


def _masked_url(url: str) -> str:
    """遮罩 URL 中的 API key，防止 secret 洩漏進 log。"""
    return _redact_secret_text(url)


def _safe_error_message(exc: BaseException) -> str:
    """httpx exceptions include request URLs; sanitize them before logging."""
    return _redact_secret_text(exc)


class GeminiClient:
    """
    透過 REST API 呼叫 Google Gemini，支援 JSON Schema 與本地快取。
    """

    MAX_RETRIES = 5
    CONCURRENCY_LIMIT = 1  # GHA 環境 burst 防 429

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.logger = logging.getLogger(f"{__name__}.GeminiClient")
        self._cm = CacheManager()
        self._save_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(self.CONCURRENCY_LIMIT)
        self._budget_manager = LLMBudgetManager(
            config.LLM_BUDGET_STATE_FILE,
            max_daily_llm_calls=config.LLM_DAILY_BUDGET,
            cooldown_minutes=config.LLM_BUDGET_COOLDOWN_MINUTES,
            retention_days=config.LLM_BUDGET_RETENTION_DAYS,
        )

    # ── 內部工具 ──────────────────────────────────────────────────────────────

    def _prompt_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        md5 = hashlib.md5(f"{system_prompt}|{user_prompt}".encode("utf-8")).hexdigest()
        return CacheManager.prompt_key(md5)

    async def _save_cache(self):
        async with self._save_lock:
            self._cm.save()

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
                "LLM budget/cooldown active: decision=%s reason=%s used=%s/%s",
                decision.decision,
                decision.reason,
                decision.snapshot.get("llm_calls_used"),
                decision.snapshot.get("max_daily_llm_calls"),
            )
            raise LLMBudgetSkip(decision)
        if record_call:
            budget.record_llm_call(run_date)

    def _record_quota_error(self) -> None:
        budget = self._budget()
        if budget is None:
            return
        budget.record_quota_error(self._run_date())

    # ── Pre-flight 探活 ───────────────────────────────────────────────────────

    async def preflight_check(self) -> bool:
        """
        送 1-token 輕量請求確認配額可用。
        回傳 True = 可用；False / raise = 429 或其他錯誤。
        """
        model = GEMINI_MODELS[0]
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "hi"}]}],
            "generationConfig": {"maxOutputTokens": 1},
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 429:
                    self.logger.warning(
                        f"Pre-flight 失敗：429 配額耗盡（model={model}）"
                    )
                    return False
                resp.raise_for_status()
                self.logger.info("Pre-flight OK：配額正常")
                return True
        except Exception as e:
            self.logger.warning(f"Pre-flight 例外: {_safe_error_message(e)}")
            return False

    # ── 單次 LLM 呼叫（L2 cache）────────────────────────────────────────────

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:

        # 1. L2 快取命中
        cache_key = self._prompt_cache_key(system_prompt, user_prompt)
        cached = self._cm.get(cache_key)
        if cached is not None:
            self._cm.increment_stat("total_l2_hits")
            self.logger.info("   [⚡] L2 快取命中，零延遲節省額度！")
            return cached

        self._ensure_budget_for_provider_call()
        self._cm.increment_stat("total_misses")

        if json_mode and not response_schema:
            system_prompt += "\n\n重要：你的回覆必須是有效的 JSON 格式，不得包含任何 JSON 之外的文字、markdown 標記或說明。"

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json" if json_mode else "text/plain",
            },
        }
        if json_mode and response_schema:
            payload["generationConfig"]["responseSchema"] = response_schema

        # 2. 限流重試邏輯
        # - 429：模型輪替 → wait 60s→300s→900s → 熔斷
        # - 其他錯誤：exponential backoff，上限 MAX_RETRIES
        models_to_try = GEMINI_MODELS.copy()
        current_model = models_to_try.pop(0)
        _429_waits = [60, 300, 900]
        _429_wait_idx = 0
        transient_attempt = 0

        while True:
            url = f"{GEMINI_API_BASE}/{current_model}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        self.logger.warning(
                            "Gemini API 錯誤詳情 (HTTP %s): %s",
                            response.status_code,
                            _redact_secret_text(response.text),
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

                # 3. 寫入 L2 快取
                self._cm.set(cache_key, result)
                await self._save_cache()
                return result

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"Gemini API HTTP 錯誤 [{current_model}]: {e.response.status_code}"
                )

                if e.response.status_code == 429:
                    if models_to_try:
                        next_model = models_to_try.pop(0)
                        self.logger.warning(
                            f"偵測到 429！切換模型至：{next_model}"
                        )
                        current_model = next_model
                        await asyncio.sleep(1)
                        continue
                    else:
                        if _429_wait_idx < len(_429_waits):
                            wait_sec = _429_waits[_429_wait_idx]
                            _429_wait_idx += 1
                            self.logger.warning(
                                f"所有備用模型均 429，等待 {wait_sec}s 後重試"
                                f"（{_429_wait_idx}/{len(_429_waits)}）"
                            )
                            await asyncio.sleep(wait_sec)
                            models_to_try = GEMINI_MODELS.copy()
                            current_model = models_to_try.pop(0)
                            continue
                        else:
                            self.logger.error(
                                "所有備用模型均已遭遇 429 配額耗盡，拋出例外觸發終極斷路器。"
                            )
                            self._record_quota_error()
                            raise

                transient_attempt += 1
                if transient_attempt >= self.MAX_RETRIES:
                    raise
                await asyncio.sleep(2 ** transient_attempt)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                self.logger.warning(
                    "回應解析失敗 (第 %s 次): %s",
                    transient_attempt + 1,
                    _safe_error_message(e),
                )
                transient_attempt += 1
                if transient_attempt >= self.MAX_RETRIES:
                    raise
                await asyncio.sleep(1)

    # ── 批次呼叫（L1 在 sentiment.py 上層處理）──────────────────────────────

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: Optional[int] = None,
        response_schema: Optional[dict] = None,
    ) -> List[Union[dict, str]]:
        """
        全自動降壓版批次分析。
        入口前執行 pre-flight；429 熔斷向上拋出以啟動 Showcase 模式。
        """
        concurrency = concurrency if concurrency is not None else self.CONCURRENCY_LIMIT
        total = len(user_prompts)
        self.logger.info(f"開始批次分析 {total} 筆資料 (最大併發: {concurrency})")

        # Pre-flight：省去 3 分鐘空等 retry
        self._ensure_budget_for_provider_call(record_call=False)
        budget = self._budget()
        if budget is not None:
            run_date = self._run_date()
            snapshot = budget.snapshot(run_date)
            uncached_prompts = sum(
                1
                for prompt in user_prompts
                if self._cm.get(self._prompt_cache_key(system_prompt, prompt)) is None
            )
            if uncached_prompts > snapshot.get("remaining_llm_calls", 0):
                snapshot = dict(snapshot)
                snapshot["decision"] = "skip_llm"
                snapshot["decision_reason"] = REASON_BUDGET_EXHAUSTED
                raise LLMBudgetSkip(
                    BudgetDecision(
                        run_date,
                        False,
                        "skip_llm",
                        REASON_BUDGET_EXHAUSTED,
                        snapshot,
                    )
                )
        ok = await self.preflight_check()
        if not ok:
            self._record_quota_error()
            raise httpx.HTTPStatusError(
                "Pre-flight 429",
                request=None,
                response=httpx.Response(429),
            )

        sem = asyncio.Semaphore(concurrency)

        async def _analyze(i, prompt):
            async with sem:
                self.logger.info(f"   [⏳] 正在分析第 {i}/{total} 篇情報...")
                try:
                    return await self.chat(
                        system_prompt, prompt, json_mode,
                        response_schema=response_schema,
                    )
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        raise
                    safe_error = _safe_error_message(e)
                    self.logger.error(f"   [!] 批次分析 #{i} 發生錯誤: {safe_error}")
                    return {"error": safe_error}
                except LLMBudgetSkip:
                    raise
                except Exception as e:
                    safe_error = _safe_error_message(e)
                    self.logger.error(f"   [!] 批次分析 #{i} 發生錯誤: {safe_error}")
                    return {"error": safe_error}

        tasks = [_analyze(i, prompt) for i, prompt in enumerate(user_prompts, 1)]
        try:
            results = await asyncio.gather(*tasks)
            return list(results)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.logger.error("批次分析中發生 429 錯誤！已強制熔斷。")
                raise
            return []

    # ── CacheManager 存取器（供 sentiment.py 等上層存取）───────────────────

    @property
    def cache_manager(self) -> CacheManager:
        return self._cm


# ── 可直接執行的連線測試 ──────────────────────────────
if __name__ == "__main__":
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
            "required": ["sentiment"],
        }
        result = await client.chat(
            system_prompt="你是輿情分析師。",
            user_prompt='分析這段文字的情緒：「傳說對決最近的新英雄好強！」',
            json_mode=True,
            response_schema=test_schema,
        )
        print("Gemini 回應:", result)

    asyncio.run(main())
