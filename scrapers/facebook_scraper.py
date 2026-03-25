"""
Facebook ?¨È?Ë≤ºÊ??¨Ëü≤??
‰ΩøÁî® Playwright Â≠òÂ? Facebook ?¨È??úÂ??ÅÈù¢Ôº??∑Â??áÈ??µÂ??∏È??ÑÂÖ¨?ãË≤º?á„Ä?"""

import json
import logging
import re
from typing import List, Optional
from playwright.async_api import async_playwright, Page

from scrapers.base_scraper import BaseScraper, Post

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):
    PLATFORM = "facebook"

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
                """?îÊà™ Facebook ??API ?ûÊ???""
                try:
                    url = response.url
                    if "graphql" in url or "api" in url or "search" in url.lower():
                        if response.status == 200:
                            content_type = response.headers.get("content-type", "")
                            if "json" in content_type:
                                body = await response.json()
                                captured_data.append(body)
                            elif "javascript" in content_type or "text" in content_type:
                                text = await response.text()
                                # FB ?âÊ??ûÂÇ≥ for(;;); ?çÁ∂¥??JSON
                                text = re.sub(r"^for\s*\(\s*;\s*;\s*\)\s*;\s*", "", text)
                                try:
                                    body = json.loads(text)
                                    captured_data.append(body)
                                except json.JSONDecodeError:
                                    pass
                except Exception:
                    pass

            page.on("response", _handle_response)

            try:
                # Facebook ?¨È?Ë≤ºÊ??úÂ?
                search_url = (
                    f"https://www.facebook.com/search/posts/?q={keyword}"
                )
                self.logger.info(f"Ê≠?ú®Â≠òÂ?: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await self._random_delay(3, 5)

                # ?≤Â?ËºâÂÖ•?¥Â?
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_delay(2, 4)

                # ÂæûÊ??™Ë??ô‰∏≠?êÂ?
                posts.extend(self._parse_api_data(captured_data, max_posts))

                # ?ôÁî® DOM Ëß??
                if not posts:
                    self.logger.info("API ?îÊà™?°Ë??ôÔ??πÁî® DOM Ëß??")
                    posts.extend(await self._parse_dom(page, keyword, max_posts))

            except Exception as e:
                self.logger.error(f"Facebook ?¨Â?Â§±Ê?: {e}")
                raise
            finally:
                await browser.close()

        return posts[:max_posts]

    def _parse_api_data(self, captured_data: list, max_posts: int) -> List[Post]:
        """Âæ?Facebook GraphQL ?ûÊ?‰∏≠Â?Ë©¶Ëß£?êË≤º?áË??ô„Ä?""
        posts: List[Post] = []

        for data in captured_data:
            try:
                stories = self._find_stories(data)
                for story in stories:
                    post = self._story_to_post(story)
                    if post:
                        posts.append(post)
                    if len(posts) >= max_posts:
                        return posts
            except Exception as e:
                self.logger.debug(f"Ëß?? FB API Ë≥áÊ?Â§±Ê?: {e}")
                continue

        return posts

    def _find_stories(self, data, depth: int = 0) -> list:
        """?ûËø¥?úÂ? Facebook API ?ûÊ?‰∏≠Á?Ë≤ºÊ?ÁµêÊ???""
        if depth > 12:
            return []

        results = []
        if isinstance(data, dict):
            # Facebook Â∏∏Ë??ÑÁ?ÊßãË∑ØÂæ?            if "message" in data and "text" in data.get("message", {}):
                return [data]
            if "story" in data:
                return [data["story"]]
            if "edges" in data:
                for edge in data["edges"]:
                    node = edge.get("node", edge)
                    results.extend(self._find_stories(node, depth + 1))
                return results

            for value in data.values():
                results.extend(self._find_stories(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                results.extend(self._find_stories(item, depth + 1))

        return results

    def _story_to_post(self, story: dict) -> Optional[Post]:
        """Â∞?FB story ÁØÄÈªûË??õÁÇ∫ Post??""
        try:
            message = story.get("message", {})
            content = ""
            if isinstance(message, dict):
                content = message.get("text", "")
            elif isinstance(message, str):
                content = message

            if not content:
                return None

            # ?óË©¶?ñÂ?‰ΩúËÄÖË?Ë®?            actors = story.get("actors", [])
            author = "unknown"
            if actors and isinstance(actors, list):
                author = actors[0].get("name", "unknown")

            # ?óË©¶?ñÂ????
            url = story.get("url", "")

            return Post(
                platform="facebook",
                author=author,
                content=content,
                url=url,
                likes=story.get("feedback", {}).get("reaction_count", {}).get("count", 0),
                comments=story.get("feedback", {}).get("comment_count", {}).get("total_count", 0),
                shares=story.get("feedback", {}).get("share_count", {}).get("count", 0),
                hashtags=self._extract_hashtags(content),
                raw_data=story,
            )
        except Exception as e:
            self.logger.debug(f"FB story ËΩâÊ?Â§±Ê?: {e}")
            return None

    async def _parse_dom(self, page: Page, keyword: str, max_posts: int) -> List[Post]:
        """
        ?ôÁî®?πÊ?ÔºöÂ? Facebook ?ÅÈù¢ DOM ‰∏≠Êì∑?ñË≤º?áÂÖßÂÆπ„Ä?        Facebook ??DOM ÁµêÊ?Á∂ìÂ∏∏ËÆäÂ?ÔºåÊ≠§?πÊ??Ö‰??∫Â??Ä?πÊ???        """
        posts: List[Post] = []
        try:
            # ?óË©¶?ÑÁ®Æ?ØËÉΩ?ÑË≤º?áÂÆπ?®ÈÅ∏?áÂô®
            selectors = [
                '[role="article"]',
                '[data-ad-comet-preview="message"]',
                'div[dir="auto"]',
            ]

            for selector in selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.inner_text()
                    if text and len(text.strip()) > 20:
                        # ?éÊøæ?âÊ?È°Ø‰??ØË≤º?áÁ??ÉÁ?
                        if any(skip in text for skip in ["?ªÂÖ•", "Ë®ªÂ?", "Log In", "Sign Up"]):
                            continue

                        posts.append(
                            Post(
                                platform="facebook",
                                author="unknown",
                                content=text.strip()[:500],
                                url="",
                            )
                        )

                        if len(posts) >= max_posts:
                            return posts

                if posts:
                    break  # Â¶ÇÊ??êÂÄ?selector ?âÁ??úÂ∞±‰∏çÂ??óË©¶?∂‰???
        except Exception as e:
            self.logger.warning(f"FB DOM Ëß??Â§±Ê?: {e}")

        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        return re.findall(r"#(\w+)", text)


# ?Ä?Ä ?ØÁõ¥?•Âü∑Ë°åÁ??®Á?Ê∏¨Ë©¶ ?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä
if __name__ == "__main__":
    import asyncio
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = FacebookScraper(headless=True)
        posts = await scraper.scrape(["?≥Ë™™Â∞çÊ±∫"], max_posts=5)
        for p in posts:
            print(f"  [{p.platform}] {p.author}: {p.content[:80]}...")
            print(f"    URL: {p.url}")
            print()

    asyncio.run(main())
