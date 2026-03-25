"""
Threads ?¨È?Ë≤ºÊ??¨Ëü≤??
‰ΩøÁî® Playwright ?îÊà™ Threads ?ÑÂ?Á´?API ?ûÊ?Ôº?ÂæûÊ?Â∞ãÈ??¢Êì∑?ñË??úÈçµÂ≠óÁõ∏?úÁ?‰∏≤Ê???"""

import json
import logging
from typing import List, Optional
from playwright.async_api import async_playwright, Page

from scrapers.base_scraper import BaseScraper, Post

logger = logging.getLogger(__name__)


class ThreadsScraper(BaseScraper):
    PLATFORM = "threads"

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

            captured_data: list = []

            async def _handle_response(response):
                """?îÊà™ÂæåÁ´Ø API ?ûÊ???""
                try:
                    url = response.url
                    if (
                        "api" in url
                        or "graphql" in url
                        or "search" in url.lower()
                    ):
                        if response.status == 200:
                            content_type = response.headers.get("content-type", "")
                            if "json" in content_type or "javascript" in content_type:
                                body = await response.json()
                                captured_data.append(body)
                except Exception:
                    pass

            page.on("response", _handle_response)

            try:
                search_url = f"https://www.threads.net/search?q={keyword}&serp_type=default"
                self.logger.info(f"Ê≠?ú®Â≠òÂ?: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await self._random_delay(3, 5)

                # ?≤Â?ËºâÂÖ•?¥Â??ßÂÆπ
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_delay(1.5, 3)

                # ÂæûÊ??™Âà∞??API Ë≥áÊ?‰∏≠Ëß£??                posts.extend(self._parse_api_data(captured_data, max_posts))

                # ?ôÁî®ÔºöDOM Ëß??
                if not posts:
                    self.logger.info("API ?îÊà™?°Ë??ôÔ??πÁî® DOM Ëß??")
                    posts.extend(await self._parse_dom(page, keyword, max_posts))

            except Exception as e:
                self.logger.error(f"Threads ?¨Â?Â§±Ê?: {e}")
                raise
            finally:
                await browser.close()

        return posts[:max_posts]

    def _parse_api_data(self, captured_data: list, max_posts: int) -> List[Post]:
        """Âæ?API ?ûÊ?‰∏≠Â?Ë©¶Ëß£?êË≤º?áË??ô„Ä?""
        posts: List[Post] = []

        for data in captured_data:
            try:
                items = self._find_thread_items(data)
                for item in items:
                    post = self._item_to_post(item)
                    if post:
                        posts.append(post)
                    if len(posts) >= max_posts:
                        return posts
            except Exception as e:
                self.logger.debug(f"Ëß?? Threads API Ë≥áÊ?Â§±Ê?: {e}")
                continue

        return posts

    def _find_thread_items(self, data, depth: int = 0) -> list:
        """?ûËø¥?úÂ??ûÊ?‰∏≠Á?‰∏≤Ê??ÖÁõÆ??""
        if depth > 10:
            return []

        items = []
        if isinstance(data, dict):
            # Â∞ãÊâæÂ∏∏Ë??Ñ‰∏≤?áÁ?Êß?            if "thread_items" in data:
                return data["thread_items"]
            if "threads" in data:
                return data["threads"]
            if "data" in data and isinstance(data["data"], dict):
                return self._find_thread_items(data["data"], depth + 1)

            for value in data.values():
                result = self._find_thread_items(value, depth + 1)
                if result:
                    items.extend(result)
        elif isinstance(data, list):
            for item in data:
                result = self._find_thread_items(item, depth + 1)
                if result:
                    items.extend(result)

        return items

    def _item_to_post(self, item: dict) -> Optional[Post]:
        """Â∞?Threads API ?ÖÁõÆËΩâÊ???Post??""
        try:
            # Threads Ë≥áÊ?ÁµêÊ??ØËÉΩ?âÂ?Â±§Â?Â•?            post_data = item.get("post", item)
            user = post_data.get("user", {})
            caption = post_data.get("caption", {})

            content = ""
            if isinstance(caption, dict):
                content = caption.get("text", "")
            elif isinstance(caption, str):
                content = caption

            if not content:
                return None

            username = user.get("username", "unknown")
            code = post_data.get("code", "")

            return Post(
                platform="threads",
                author=username,
                content=content,
                url=f"https://www.threads.net/@{username}/post/{code}" if code else "",
                timestamp=str(post_data.get("taken_at", "")),
                likes=post_data.get("like_count", 0),
                comments=post_data.get("text_post_app_info", {}).get(
                    "direct_reply_count", 0
                ),
                hashtags=self._extract_hashtags(content),
                raw_data=item,
            )
        except Exception as e:
            self.logger.debug(f"‰∏≤Ê?ËΩâÊ?Â§±Ê?: {e}")
            return None

    async def _parse_dom(self, page: Page, keyword: str, max_posts: int) -> List[Post]:
        """?ôÁî®?πÊ?ÔºöÂ? DOM ‰∏≠Êì∑?ñÂèØË¶ãÁ??áÂ??ßÂÆπ??""
        posts: List[Post] = []
        try:
            # Â∞ãÊâæ?ãËµ∑‰æÜÂ?Ë≤ºÊ?ÂÆπÂô®?ÑÂ?Á¥?            elements = await page.query_selector_all(
                '[data-pressable-container="true"], article, [role="article"]'
            )

            for elem in elements[:max_posts]:
                text = await elem.inner_text()
                if text and len(text.strip()) > 10:
                    # ?óË©¶?æÂà∞???
                    link = await elem.query_selector("a[href*='/post/']")
                    url = ""
                    if link:
                        href = await link.get_attribute("href")
                        url = f"https://www.threads.net{href}" if href and href.startswith("/") else (href or "")

                    posts.append(
                        Post(
                            platform="threads",
                            author="unknown",
                            content=text.strip()[:500],
                            url=url,
                        )
                    )
        except Exception as e:
            self.logger.warning(f"Threads DOM Ëß??Â§±Ê?: {e}")

        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        import re
        return re.findall(r"#(\w+)", text)


# ?Ä?Ä ?ØÁõ¥?•Âü∑Ë°åÁ??®Á?Ê∏¨Ë©¶ ?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä
if __name__ == "__main__":
    import asyncio
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = ThreadsScraper(headless=True)
        posts = await scraper.scrape(["?≥Ë™™Â∞çÊ±∫"], max_posts=5)
        for p in posts:
            print(f"  [{p.platform}] {p.author}: {p.content[:80]}...")
            print(f"    URL: {p.url}")
            print()

    asyncio.run(main())
