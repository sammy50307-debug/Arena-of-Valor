"""
Instagram ?¬é?è²¼æ??¬èŸ²??
ä½¿ç”¨ Playwright ?”æˆª Instagram ??GraphQL API ?æ?ï¼?å¾å…¬?‹ç? hashtag ?¢ç´¢?é¢?·å??‡é??µå??¸é??„è²¼?‡ã€?"""

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

            # ?¨ä??¶é??”æˆª?°ç? API ?æ?
            captured_data: list = []

            async def _handle_response(response):
                """?”æˆª GraphQL API ?æ?ï¼Œæ“·?–è²¼?‡è??™ã€?""
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
                # ?å? hashtag ?¢ç´¢?é¢
                tag = keyword.replace(" ", "").replace("#", "")
                search_url = f"https://www.instagram.com/explore/tags/{tag}/"
                self.logger.info(f"æ­?œ¨å­˜å?: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await self._random_delay(2, 4)

                # ?²å??é¢ä»¥è??¥æ›´å¤šè²¼??                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_delay(1.5, 3)

                # ?—è©¦å¾æ??ªåˆ°??API è³‡æ?ä¸­æ??–è²¼??                posts.extend(self._parse_api_data(captured_data, max_posts))

                # å¦‚æ? API ?”æˆªæ²’æ?çµæ?ï¼Œæ”¹?¨é???DOM è§??
                if not posts:
                    self.logger.info("API ?”æˆª?¡è??™ï??¹ç”¨ DOM è§??")
                    posts.extend(await self._parse_dom(page, keyword, max_posts))

            except Exception as e:
                self.logger.error(f"Instagram ?¬å?å¤±æ?: {e}")
                raise
            finally:
                await browser.close()

        return posts[:max_posts]

    def _parse_api_data(self, captured_data: list, max_posts: int) -> List[Post]:
        """å¾æ??ªåˆ°??GraphQL ?æ?ä¸­è§£?è²¼?‡ã€?""
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
                self.logger.debug(f"è§?? API è³‡æ??‡æ®µå¤±æ?: {e}")
                continue

        return posts

    def _extract_edges(self, data: dict) -> list:
        """?è¿´?œå? GraphQL ?æ?ä¸­ç? edges ?????""
        if isinstance(data, dict):
            if "edges" in data:
                return data["edges"]
            for value in data.values():
                result = self._extract_edges(value)
                if result:
                    return result
        return []

    def _node_to_post(self, node: dict) -> Optional[Post]:
        """å°?GraphQL node è½‰æ???Post ?©ä»¶??""
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
            self.logger.debug(f"ç¯€é»è??›å¤±?? {e}")
            return None

    async def _parse_dom(self, page: Page, keyword: str, max_posts: int) -> List[Post]:
        """
        ?™ç”¨?¹æ?ï¼šç›´?¥å? DOM ä¸­æ??–é€???Œæ?å­—ã€?        ??API ?”æˆª?¡è??™æ?ä½¿ç”¨??        """
        posts: List[Post] = []
        try:
            # ?—è©¦?–å?è²¼æ????
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
                            content=f"[å¾?IG ?œå? '{keyword}' ?–å??„è²¼?‡]",
                            url=full_url,
                        )
                    )
        except Exception as e:
            self.logger.warning(f"DOM è§??å¤±æ?: {e}")

        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        """å¾è²¼?‡å…§å®¹ä¸­?å? hashtag??""
        import re
        return re.findall(r"#(\w+)", text)


# ?€?€ ?¯ç›´?¥åŸ·è¡Œç??¨ç?æ¸¬è©¦ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
if __name__ == "__main__":
    import asyncio
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = InstagramScraper(headless=True)
        posts = await scraper.scrape(["?³èªªå°æ±º"], max_posts=5)
        for p in posts:
            print(f"  [{p.platform}] {p.author}: {p.content[:80]}...")
            print(f"    URL: {p.url}")
            print()

    asyncio.run(main())
