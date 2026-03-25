"""
Tavily ?œå?æ¨¡ç???
?´æ¥?¼å« Tavily REST APIï¼ˆä?ä½¿ç”¨ tavily-python å¥—ä»¶ï¼??¿å? tiktoken ?¸ä? Rust ?„å?é¡Œï?ï¼Œå??€ httpx??"""

import logging
from typing import List, Optional
from dataclasses import dataclass, field, asdict

import httpx

import config

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass
class SearchResult:
    """æ¨™æ??–ç??œå?çµæ?è³‡æ?æ¨¡å???""
    title: str
    content: str
    url: str
    source: str = ""       # ä¾†æ?ç¶²å?
    platform: str = "web"  # ?¨æ¸¬?„å¹³?°ï?instagram/threads/facebook/webï¼?    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class TavilySearcher:
    """
    ?¼å« Tavily Search API ?œé??‡ã€Šå‚³èªªå?æ±ºã€‹ç›¸?œç??¬é?è³‡è???    Tavily ?ƒè‡ª?•å??¨ç¶²ï¼ˆå« IG/Threads/FB ?¬é??ã€æ–°?ã€è?å£‡ï??–å?çµæ???    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.TAVILY_API_KEY
        self.logger = logging.getLogger(f"{__name__}.TavilySearcher")

    async def search(
        self,
        keywords: List[str],
        max_results_per_keyword: int = 10,
    ) -> List[SearchResult]:
        """
        å°æ??‹é??µå??¼å« Tavily ?œå? API??
        Args:
            keywords: ?œå??œéµå­—å?è¡?            max_results_per_keyword: æ¯å€‹é??µå??–å??„æ?å¤§ç??œæ•¸

        Returns:
            ?»é?å¾Œç? SearchResult ?—è¡¨
        """
        if not self.api_key:
            self.logger.error("TAVILY_API_KEY ?ªè¨­å®?)
            return []

        all_results: List[SearchResult] = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=30) as client:
            for keyword in keywords:
                try:
                    results = await self._search_keyword(
                        client, keyword, max_results_per_keyword
                    )
                    # ?»é?
                    for r in results:
                        if r.url not in seen_urls:
                            seen_urls.add(r.url)
                            all_results.append(r)

                    self.logger.info(
                        f"?œéµå­?'{keyword}' ?–å? {len(results)} ç­†ç???
                    )
                except Exception as e:
                    self.logger.error(f"?œå? '{keyword}' å¤±æ?: {e}")

        self.logger.info(f"?±å?å¾?{len(all_results)} ç­†ä??è?çµæ?")
        return all_results

    async def _search_keyword(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        max_results: int,
    ) -> List[SearchResult]:
        """å°å–®ä¸€?œéµå­—å‘¼??Tavily API??""
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
            "include_answer": False,
            "include_raw_content": False,
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
                )
            )
        return results

    @staticmethod
    def _detect_platform(url: str) -> str:
        """å¾?URL ?¨æ¸¬ä¾†æ?å¹³å°??""
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


# ?€?€ ?¯ç›´?¥åŸ·è¡Œç??¨ç?æ¸¬è©¦ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        searcher = TavilySearcher()
        results = await searcher.search(["?³èªªå°æ±º"], max_results_per_keyword=5)
        for r in results:
            print(f"[{r.platform}] {r.title}")
            print(f"  URL: {r.url}")
            print(f"  ?§å®¹: {r.content[:100]}...")
            print()

    asyncio.run(main())
