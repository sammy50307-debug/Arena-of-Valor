"""
DuckDuckGo HTML 通用 AOV 搜尋器。

以 POST https://html.duckduckgo.com/html/ 搜尋 AOV 相關關鍵字，
不需要任何 API Key，完全免費。作為 Tavily 的備援搜尋源使用。
"""

import logging
import re
import sys
from typing import List

import httpx
from bs4 import BeautifulSoup

from scrapers.tavily_searcher import SearchResult

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

DDG_HTML_URL = "https://html.duckduckgo.com/html/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 已知遊戲討論平台清單，用於 platform 標記
PLATFORM_MAP = {
    "dcard.tw": "dcard",
    "ptt.cc": "ptt",
    "forum.gamer.com.tw": "bahamut",
    "facebook.com": "facebook",
    "threads.net": "threads",
    "instagram.com": "instagram",
    "youtube.com": "youtube",
    "mobile01.com": "mobile01",
    "pantip.com": "pantip",
}


class DDGSearcher:
    """
    透過 DuckDuckGo HTML endpoint 搜尋 AOV 相關討論。
    免費、無需 API Key，作為 Tavily 額度耗盡時的備援。
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DDGSearcher")

    async def search(
        self,
        max_results_per_region: int = 5,
    ) -> List[SearchResult]:
        """
        對 config.REGIONAL_KEYWORDS 所有區域執行 DDG 搜尋，
        介面與 TavilySearcher.search() 相容。
        """
        import config
        all_results: List[SearchResult] = []
        seen_urls: set = set()

        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for region, keywords in config.REGIONAL_KEYWORDS.items():
                per_kw = max(1, max_results_per_region // len(keywords))
                for keyword in keywords:
                    try:
                        results = await self._search_keyword(client, keyword, per_kw, region)
                        for r in results:
                            if r.url not in seen_urls:
                                seen_urls.add(r.url)
                                all_results.append(r)
                        self.logger.info(f"[DDG] {region} '{keyword}' 取得 {len(results)} 筆")
                    except Exception as e:
                        self.logger.error(f"[DDG] 搜尋 '{keyword}' 失敗: {e}")

        self.logger.info(f"[DDG] 共取得 {len(all_results)} 筆不重複結果")
        return all_results

    async def _search_keyword(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """對單一關鍵字執行 DDG HTML 搜尋。"""
        resp = await client.post(DDG_HTML_URL, data={
            "q": f"傳說對決 {keyword}",
            "kl": "tw-tzh",
        })
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_results(soup, keyword, max_results, region)

    def _parse_results(
        self,
        soup: BeautifulSoup,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """解析 DDG HTML 搜尋結果頁，回傳 SearchResult 列表。"""
        results: List[SearchResult] = []
        seen_urls: set = set()

        for a_tag in soup.select(".result__a"):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)

            if not title or not href:
                continue

            # 清除 DDG 重導向參數，取出真實 URL
            url_match = re.search(r"uddg=(https?://[^&]+)", href)
            url = url_match.group(1) if url_match else href
            # URL decode
            try:
                from urllib.parse import unquote
                url = unquote(url)
            except Exception:
                pass

            if url in seen_urls:
                continue
            seen_urls.add(url)

            platform = self._detect_platform(url)
            snippet_el = a_tag.find_next(".result__snippet")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            results.append(SearchResult(
                title=title,
                content=f"{title}。{snippet}"[:600] if snippet else title,
                url=url,
                source=self._extract_domain(url),
                platform=platform,
                score=0.55,
                region=region,
                published_date="",
            ))
            if len(results) >= max_results:
                break

        return results

    def _detect_platform(self, url: str) -> str:
        for domain, platform in PLATFORM_MAP.items():
            if domain in url:
                return platform
        return "web"

    def _extract_domain(self, url: str) -> str:
        m = re.search(r"https?://([^/]+)", url)
        return m.group(1) if m else url


# ── 直接執行測試 ──────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        searcher = DDGSearcher()
        results = await searcher.search(max_results_per_region=3)
        for r in results:
            print(f"[{r.platform}] {r.title[:60]}")
            print(f"  URL: {r.url}")
            print()

    asyncio.run(main())
