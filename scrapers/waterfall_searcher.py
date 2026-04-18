"""
瀑布式輪用搜尋鏈 (Waterfall Search Chain)。

依序嘗試多個搜尋源，前一個失敗或額度耗盡時自動切換下一個。
源清單（優先順序）：
  1. Tavily      - 付費 API，品質最高
  2. DDGSearcher - DuckDuckGo HTML，免費無限額
返回第一個成功且有結果的源的資料。
"""

import logging
import sys
from typing import List, Tuple

import httpx

from scrapers.tavily_searcher import SearchResult

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# Tavily 額度耗盡時的回應關鍵字
QUOTA_SIGNALS = [
    "quota",
    "rate limit",
    "too many requests",
    "exceeded",
    "limit reached",
    "subscription",
]


def _is_quota_error(exc: Exception) -> bool:
    """判斷例外是否為 API 額度耗盡或速率限制。"""
    msg = str(exc).lower()
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code in (429, 402, 403):
            return True
        try:
            body = exc.response.text.lower()
            if any(sig in body for sig in QUOTA_SIGNALS):
                return True
        except Exception:
            pass
    return any(sig in msg for sig in QUOTA_SIGNALS)


class WaterfallSearcher:
    """
    瀑布式搜尋鏈：依序嘗試各搜尋源，自動備援。

    使用方式：
        searcher = WaterfallSearcher()
        results = await searcher.search(max_results_per_region=5)

    results 與 TavilySearcher.search() 回傳格式完全相容。
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.WaterfallSearcher")
        self._sources: List[Tuple[str, object]] = []
        self._build_sources()

    def _build_sources(self):
        """初始化搜尋源列表，按優先順序排列。"""
        # Tavily（若無 API Key 則跳過）
        try:
            import config
            if config.TAVILY_API_KEY:
                from scrapers.tavily_searcher import TavilySearcher
                self._sources.append(("Tavily", TavilySearcher()))
            else:
                self.logger.warning("[Waterfall] TAVILY_API_KEY 未設定，跳過 Tavily")
        except Exception as e:
            self.logger.warning(f"[Waterfall] Tavily 初始化失敗: {e}")

        # DDG（永遠加入作為最終備援）
        try:
            from scrapers.ddg_searcher import DDGSearcher
            self._sources.append(("DDG", DDGSearcher()))
        except Exception as e:
            self.logger.warning(f"[Waterfall] DDGSearcher 初始化失敗: {e}")

    async def search(
        self,
        max_results_per_region: int = 5,
    ) -> List[SearchResult]:
        """
        依序嘗試各搜尋源。
        - 若源成功且有結果 → 立即回傳
        - 若源拋出額度錯誤 → 記錄並切換下一個
        - 若源回傳空結果   → 記錄並切換下一個（網路問題也繼續嘗試）
        """
        for name, source in self._sources:
            try:
                self.logger.info(f"[Waterfall] 嘗試搜尋源：{name}")
                results = await source.search(max_results_per_region=max_results_per_region)

                if results:
                    self.logger.info(
                        f"[Waterfall] ✅ {name} 成功取得 {len(results)} 筆，"
                        f"後續源跳過。"
                    )
                    # 在每筆結果標記使用的搜尋源
                    for r in results:
                        if not r.source:
                            r.source = name.lower()
                    return results
                else:
                    self.logger.warning(
                        f"[Waterfall] {name} 返回空結果，切換下一個搜尋源..."
                    )

            except Exception as e:
                if _is_quota_error(e):
                    self.logger.warning(
                        f"[Waterfall] ⚠️  {name} 額度耗盡或速率限制，"
                        f"自動切換下一個搜尋源..."
                    )
                else:
                    self.logger.error(
                        f"[Waterfall] ❌ {name} 發生錯誤: {e}，切換下一個..."
                    )

        self.logger.error("[Waterfall] 所有搜尋源均失敗，回傳空列表。")
        return []

    def list_sources(self) -> List[str]:
        """回傳目前已載入的搜尋源名稱清單。"""
        return [name for name, _ in self._sources]


# ── 直接執行測試 ──────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        searcher = WaterfallSearcher()
        print(f"已載入搜尋源: {searcher.list_sources()}")
        results = await searcher.search(max_results_per_region=3)
        print(f"\n共取得 {len(results)} 筆結果：")
        for r in results:
            print(f"  [{r.platform}] {r.title[:60]}")

    asyncio.run(main())
