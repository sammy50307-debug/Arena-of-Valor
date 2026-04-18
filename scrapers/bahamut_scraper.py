"""
巴哈姆特 AOV 哈啦板爬蟲。

直接以 BeautifulSoup 爬取巴哈姆特論壇 (bsn=30518) 搜尋結果，
不需要任何 API Key，完全免費。
"""

import logging
import re
import sys
from typing import List
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from scrapers.tavily_searcher import SearchResult

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

BAHAMUT_BSN   = "30518"  # AOV 哈啦板的 board serial number
BAHAMUT_SEARCH_URL = "https://forum.gamer.com.tw/B.php"
BAHAMUT_BASE  = "https://forum.gamer.com.tw"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
    "Referer": "https://forum.gamer.com.tw/",
}


class BahamutScraper:
    """
    爬取巴哈姆特 AOV 哈啦板的搜尋結果。
    使用 httpx 抓 HTML + BeautifulSoup 解析，無需 API Key。
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.BahamutScraper")

    async def search(
        self,
        keywords: List[str],
        max_results: int = 10,
        region: str = "TW",
    ) -> List[SearchResult]:
        """
        對每個關鍵字搜尋巴哈 AOV 板，回傳 SearchResult 列表。
        """
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
                    self.logger.info(f"[Bahamut] 關鍵字 '{keyword}' 取得 {len(results)} 篇")
                except Exception as e:
                    self.logger.error(f"[Bahamut] 搜尋 '{keyword}' 失敗: {e}")

        self.logger.info(f"[Bahamut] 共取得 {len(all_results)} 篇不重複文章")
        return all_results

    async def _search_keyword(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """使用巴哈論壇搜尋功能，爬取結果頁 HTML 並解析。"""
        params = {
            "bsn": BAHAMUT_BSN,
            "qt": "1",        # qt=1 代表搜尋標題
            "q": keyword,
        }
        resp = await client.get(BAHAMUT_SEARCH_URL, params=params)
        resp.raise_for_status()

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        return self._parse_post_list(soup, keyword, max_results, region)

    def _parse_post_list(
        self,
        soup: BeautifulSoup,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """解析巴哈論壇文章列表頁的 HTML。"""
        results: List[SearchResult] = []

        # 巴哈文章列表：每篇文章在 <tr class="b-list__row"> 裡
        rows = soup.select("tr.b-list__row")

        for item in rows:
            result = self._parse_row(item, keyword, region)
            if result:
                results.append(result)
            if len(results) >= max_results:
                break

        if not results:
            results = self._parse_latest_fallback(soup, keyword, max_results, region)

        return results

    def _parse_row(self, item, keyword: str, region: str):
        """從單一文章列元素解析資訊。"""
        try:
            # 標題在 <p class="b-list__main__title"> 內
            title_el = item.select_one("p.b-list__main__title")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            if not title or keyword not in title:
                return None

            # 連結在 <td class="b-list__main"> 內第一個 <a> 上
            link = item.select_one("td.b-list__main > a[href]")
            if not link:
                return None
            href = link.get("href", "")
            # href 可能是 "C.php?..." 或 "/C.php?..." 或完整 URL
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = f"{BAHAMUT_BASE}{href}"
            else:
                url = f"{BAHAMUT_BASE}/{href}"

            # 時間：<a> 在 b-list__time 下
            published = ""
            time_el = item.select_one(".b-list__time__edittime a, .b-list__time a")
            if time_el:
                published = time_el.get_text(strip=True)

            # 互動數：b-list__count__number > span[title]
            reply_count = 0
            spans = item.select(".b-list__count__number span[title]")
            for sp in spans:
                t = sp.get("title", "")
                m = re.search(r"\d+", t.replace(",", ""))
                if m:
                    reply_count = max(reply_count, int(m.group()))

            return SearchResult(
                title=title,
                content=f"{title}（巴哈姆特 AOV 哈啦板）[💬{reply_count}]",
                url=url,
                source="forum.gamer.com.tw",
                platform="bahamut",
                score=min(1.0, reply_count / 50) if reply_count > 0 else 0.5,
                region=region,
                published_date=published,
            )
        except Exception as e:
            self.logger.debug(f"解析巴哈文章列失敗: {e}")
            return None

    def _parse_latest_fallback(
        self,
        soup: BeautifulSoup,
        keyword: str,
        max_results: int,
        region: str,
    ) -> List[SearchResult]:
        """備援：從頁面中找所有含關鍵字的 AOV 文章連結。"""
        results = []
        links = soup.find_all("a", href=re.compile(r"C\.php\?bsn=30518"))
        for link in links:
            title = link.get_text(strip=True)
            href  = link.get("href", "")
            if not title or not href or keyword not in title:
                continue
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = f"{BAHAMUT_BASE}{href}"
            else:
                url = f"{BAHAMUT_BASE}/{href}"
            results.append(SearchResult(
                title=title,
                content=f"{title}（巴哈姆特 AOV 哈啦板）",
                url=url,
                source="forum.gamer.com.tw",
                platform="bahamut",
                score=0.5,
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
        scraper = BahamutScraper()
        results = await scraper.search(["芽芽"], max_results=5)
        for r in results:
            print(f"[{r.platform}] {r.title}")
            print(f"  URL: {r.url}")
            print(f"  內容: {r.content[:100]}")
            print()

    asyncio.run(main())
