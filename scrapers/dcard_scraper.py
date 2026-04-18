"""
Dcard 傳說對決板爬蟲。

以 DuckDuckGo HTML 搜尋 site:dcard.tw/f/aov 取得 Dcard AOV 板文章，
不需要 API Key，完全免費。Dcard 官方 API 受 Cloudflare 保護，
故改走 DDG 搜尋引擎索引取得文章清單。
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
    "Referer": "https://html.duckduckgo.com/",
}


class DcardScraper:
    """
    透過 DuckDuckGo HTML 搜尋取得 Dcard /f/aov 板文章。
    Dcard 官方 API 受 Cloudflare 保護，改走 DDG 搜尋 site:dcard.tw/f/aov。
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DcardScraper")

    async def search(
        self,
        keywords: List[str],
        max_results: int = 10,
        region: str = "TW",
    ) -> List[SearchResult]:
        """對每個關鍵字搜尋 Dcard AOV 板，回傳 SearchResult 列表。"""
        all_results: List[SearchResult] = []
        seen_urls: set = set()

        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for keyword in keywords:
                try:
                    results = await self._search_keyword(client, keyword, max_results, region)
                    for r in results:
                        if r.url not in seen_urls:
                            seen_urls.add(r.url)
                            all_results.append(r)
                    self.logger.info(f"[Dcard] 關鍵字 '{keyword}' 取得 {len(results)} 篇")
                except Exception as e:
                    self.logger.error(f"[Dcard] 搜尋 '{keyword}' 失敗: {e}")

        self.logger.info(f"[Dcard] 共取得 {len(all_results)} 篇不重複文章")
        return all_results

    async def _search_keyword(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """用 DuckDuckGo HTML endpoint 搜尋 site:dcard.tw/f/aov + keyword。"""
        query = f"site:dcard.tw/f/aov {keyword}"
        resp = await client.post(DDG_HTML_URL, data={
            "q": query,
            "kl": "tw-tzh",
        })
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_ddg_results(soup, keyword, max_results, region)

    def _parse_ddg_results(
        self,
        soup: BeautifulSoup,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """解析 DDG HTML 搜尋結果，篩選 dcard.tw/f/aov 的文章連結。"""
        results: List[SearchResult] = []
        seen_urls: set = set()

        # DDG 結果：每筆結果的標題連結在 .result__a
        for a_tag in soup.select(".result__a"):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)

            # 只保留 dcard.tw/f/aov/p/ 文章
            if "dcard.tw/f/aov/p/" not in href:
                continue
            # 清除 DDG 重導向前綴（如有）
            url_match = re.search(r"(https?://www\.dcard\.tw/f/aov/p/\d+)", href)
            if url_match:
                url = url_match.group(1)
            else:
                url = href

            if url in seen_urls or not title or keyword not in title:
                continue
            seen_urls.add(url)

            results.append(SearchResult(
                title=title,
                content=f"{title}（Dcard 傳說對決板）",
                url=url,
                source="dcard.tw",
                platform="dcard",
                score=0.6,
                region=region,
                published_date="",
            ))
            if len(results) >= max_results:
                break

        return results


# ── 直接執行測試 ──────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = DcardScraper()
        results = await scraper.search(["芽芽", "傳說對決"], max_results=5)
        for r in results:
            print(f"[{r.platform}] {r.title}")
            print(f"  URL: {r.url}")
            print(f"  內容: {r.content[:100]}")
            print()

    asyncio.run(main())
