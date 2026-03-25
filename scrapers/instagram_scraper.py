"""
Instagram 公開貼文爬蟲。

使用 Playwright 攔截 Instagram 的 GraphQL API 回應，
從公開的 hashtag 探索頁面擷取與關鍵字相關的貼文。
"""

import json
import logging
from typing import List, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

from scrapers.base_scraper import BaseScraper, Post

logger = logging.getLogger(__name__)


class InstagramScraper(BaseScraper):
    PLATFORM = "instagram"

    async def _do_scrape(self, keyword: str, max_posts: int) -> List[Post]:
        posts: List[Post] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="zh-TW",
            )
            page = await context.new_page()

            # 用來收集攔截到的 API 回應
            captured_data: list = []

            async def _handle_response(response):
                """攔截 GraphQL API 回應，擷取貼文資料。"""
                try:
                    url = response.url
                    if "graphql" in url or "api/v1" in url:
                        if response.status == 200:
                            body = await response.json()
                            captured_data.append(body)
                except Exception:
                    pass

            page.on("response", _handle_response)

            try:
                # 前往 hashtag 探索頁面
                tag = keyword.replace(" ", "").replace("#", "")
                search_url = f"https://www.instagram.com/explore/tags/{tag}/"
                self.logger.info(f"正在存取: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await self._random_delay(2, 4)

                # 捲動頁面以載入更多貼文
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_delay(1.5, 3)

                # 嘗試從攔截到的 API 資料中提取貼文
                posts.extend(self._parse_api_data(captured_data, max_posts))

                # 如果 API 攔截沒有結果，改用頁面 DOM 解析
                if not posts:
                    self.logger.info("API 攔截無資料，改用 DOM 解析")
                    posts.extend(await self._parse_dom(page, keyword, max_posts))

            except Exception as e:
                self.logger.error(f"Instagram 爬取失敗: {e}")
                raise
            finally:
                await browser.close()

        return posts[:max_posts]

    def _parse_api_data(self, captured_data: list, max_posts: int) -> List[Post]:
        """從攔截到的 GraphQL 回應中解析貼文。"""
        posts: List[Post] = []

        for data in captured_data:
            try:
                edges = self._extract_edges(data)
                for edge in edges:
                    node = edge.get("node", edge)
                    post = self._node_to_post(node)
                    if post:
                        posts.append(post)
                    if len(posts) >= max_posts:
                        return posts
            except Exception as e:
                self.logger.debug(f"解析 API 資料片段失敗: {e}")
                continue

        return posts

    def _extract_edges(self, data: dict) -> list:
        """遞迴搜尋 GraphQL 回應中的 edges 陣列。"""
        if isinstance(data, dict):
            if "edges" in data:
                return data["edges"]
            for value in data.values():
                result = self._extract_edges(value)
                if result:
                    return result
        return []

    def _node_to_post(self, node: dict) -> Optional[Post]:
        """將 GraphQL node 轉換為 Post 物件。"""
        try:
            shortcode = node.get("shortcode", "")
            text_edges = (
                node.get("edge_media_to_caption", {}).get("edges", [])
            )
            content = ""
            if text_edges:
                content = text_edges[0].get("node", {}).get("text", "")

            if not content and not shortcode:
                return None

            owner = node.get("owner", {})
            timestamp = node.get("taken_at_timestamp", "")

            return Post(
                platform="instagram",
                author=owner.get("username", "unknown"),
                content=content,
                url=f"https://www.instagram.com/p/{shortcode}/" if shortcode else "",
                timestamp=str(timestamp) if timestamp else None,
                likes=node.get("edge_liked_by", {}).get("count", 0)
                or node.get("edge_media_preview_like", {}).get("count", 0),
                comments=node.get("edge_media_to_comment", {}).get("count", 0),
                hashtags=self._extract_hashtags(content),
                raw_data=node,
            )
        except Exception as e:
            self.logger.debug(f"節點轉換失敗: {e}")
            return None

    async def _parse_dom(self, page: Page, keyword: str, max_posts: int) -> List[Post]:
        """
        備用方案：直接從 DOM 中提取連結和文字。
        當 API 攔截無資料時使用。
        """
        posts: List[Post] = []
        try:
            # 嘗試取得貼文連結
            links = await page.query_selector_all('a[href*="/p/"]')
            seen = set()

            for link in links[:max_posts]:
                href = await link.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    full_url = f"https://www.instagram.com{href}" if href.startswith("/") else href
                    posts.append(
                        Post(
                            platform="instagram",
                            author="unknown",
                            content=f"[從 IG 搜尋 '{keyword}' 取得的貼文]",
                            url=full_url,
                        )
                    )
        except Exception as e:
            self.logger.warning(f"DOM 解析失敗: {e}")

        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        """從貼文內容中提取 hashtag。"""
        import re
        return re.findall(r"#(\w+)", text)


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = InstagramScraper(headless=True)
        posts = await scraper.scrape(["傳說對決"], max_posts=5)
        for p in posts:
            print(f"  [{p.platform}] {p.author}: {p.content[:80]}...")
            print(f"    URL: {p.url}")
            print()

    asyncio.run(main())
