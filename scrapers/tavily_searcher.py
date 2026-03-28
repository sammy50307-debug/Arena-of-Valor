"""
Tavily 搜尋模組。

直接呼叫 Tavily REST API（不使用 tavily-python 套件，
避免 tiktoken 相依 Rust 的問題），僅需 httpx。
"""

import logging
from typing import List, Optional
from dataclasses import dataclass, field, asdict

import httpx

import config

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass
class SearchResult:
    """標準化的搜尋結果資料模型。"""
    title: str
    content: str
    url: str
    source: str = ""       # 來源網域
    platform: str = "web"  # 推測的平台（instagram/threads/facebook/web）
    score: float = 0.0
    published_date: str = "" # 新增發佈日期 

    def to_dict(self) -> dict:
        return asdict(self)


class TavilySearcher:
    """
    呼叫 Tavily Search API 搜集與《傳說對決》相關的公開資訊。
    Tavily 會自動從全網（含 IG/Threads/FB 公開頁、新聞、論壇）取回結果。
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.TAVILY_API_KEY
        self.logger = logging.getLogger(f"{__name__}.TavilySearcher")

    async def search(
        self,
        keywords: List[str],
        max_results_per_keyword: int = 10,
    ) -> List[SearchResult]:
        """
        對每個關鍵字呼叫 Tavily 搜尋 API。

        Args:
            keywords: 搜尋關鍵字列表
            max_results_per_keyword: 每個關鍵字取回的最大結果數

        Returns:
            去重後的 SearchResult 列表
        """
        if not self.api_key:
            self.logger.error("TAVILY_API_KEY 未設定")
            return []

        all_results: List[SearchResult] = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=30) as client:
            for keyword in keywords:
                try:
                    results = await self._search_keyword(
                        client, keyword, max_results_per_keyword
                    )
                    # 去重
                    for r in results:
                        if r.url not in seen_urls:
                            seen_urls.add(r.url)
                            all_results.append(r)

                    self.logger.info(
                        f"關鍵字 '{keyword}' 取得 {len(results)} 筆結果"
                    )
                except Exception as e:
                    self.logger.error(f"搜尋 '{keyword}' 失敗: {e}")

        self.logger.info(f"共取得 {len(all_results)} 筆不重複結果")
        return all_results

    async def _search_keyword(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        max_results: int,
    ) -> List[SearchResult]:
        """對單一關鍵字呼叫 Tavily API。"""
        payload = {
            "api_key": self.api_key,
            "query": keyword,
            "search_depth": "basic",
            "max_results": max_results,
            "include_domains": [
                "dcard.tw",
                "threads.net",
                "instagram.com",
                "ptt.cc",
                "facebook.com"
            ],
            "include_raw_content": False,
            "time_range": "day"  # 確保只抓取最近 24-72 小時內的即時內容
        }

        response = await client.post(TAVILY_SEARCH_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            url = item.get("url", "")
            platform = self._detect_platform(url)
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    url=url,
                    source=item.get("source", ""),
                    platform=platform,
                    score=item.get("score", 0.0),
                    published_date=item.get("published_date", "") # 提取 Tavily 提供的日期 
                )
            )
        return results

    @staticmethod
    def _detect_platform(url: str) -> str:
        """從 URL 推測來源平台。"""
        url_lower = url.lower()
        if "instagram.com" in url_lower:
            return "instagram"
        elif "threads.net" in url_lower:
            return "threads"
        elif "facebook.com" in url_lower or "fb.com" in url_lower:
            return "facebook"
        elif "ptt.cc" in url_lower:
            return "ptt"
        elif "dcard.tw" in url_lower:
            return "dcard"
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        else:
            return "web"


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        searcher = TavilySearcher()
        results = await searcher.search(["傳說對決"], max_results_per_keyword=5)
        for r in results:
            print(f"[{r.platform}] {r.title}")
            print(f"  URL: {r.url}")
            print(f"  內容: {r.content[:100]}...")
            print()

    asyncio.run(main())
