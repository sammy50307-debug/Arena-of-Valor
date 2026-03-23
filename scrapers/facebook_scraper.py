"""
Facebook 公開貼文爬蟲。

使用 Playwright 存取 Facebook 公開搜尋頁面，
擷取與關鍵字相關的公開貼文。
"""

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
                """攔截 Facebook 的 API 回應。"""
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
                                # FB 有時回傳 for(;;); 前綴的 JSON
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
                # Facebook 公開貼文搜尋
                search_url = (
                    f"https://www.facebook.com/search/posts/?q={keyword}"
                )
                self.logger.info(f"正在存取: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await self._random_delay(3, 5)

                # 捲動載入更多
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_delay(2, 4)

                # 從攔截資料中提取
                posts.extend(self._parse_api_data(captured_data, max_posts))

                # 備用 DOM 解析
                if not posts:
                    self.logger.info("API 攔截無資料，改用 DOM 解析")
                    posts.extend(await self._parse_dom(page, keyword, max_posts))

            except Exception as e:
                self.logger.error(f"Facebook 爬取失敗: {e}")
                raise
            finally:
                await browser.close()

        return posts[:max_posts]

    def _parse_api_data(self, captured_data: list, max_posts: int) -> List[Post]:
        """從 Facebook GraphQL 回應中嘗試解析貼文資料。"""
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
                self.logger.debug(f"解析 FB API 資料失敗: {e}")
                continue

        return posts

    def _find_stories(self, data, depth: int = 0) -> list:
        """遞迴搜尋 Facebook API 回應中的貼文結構。"""
        if depth > 12:
            return []

        results = []
        if isinstance(data, dict):
            # Facebook 常見的結構路徑
            if "message" in data and "text" in data.get("message", {}):
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
        """將 FB story 節點轉換為 Post。"""
        try:
            message = story.get("message", {})
            content = ""
            if isinstance(message, dict):
                content = message.get("text", "")
            elif isinstance(message, str):
                content = message

            if not content:
                return None

            # 嘗試取得作者資訊
            actors = story.get("actors", [])
            author = "unknown"
            if actors and isinstance(actors, list):
                author = actors[0].get("name", "unknown")

            # 嘗試取得連結
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
            self.logger.debug(f"FB story 轉換失敗: {e}")
            return None

    async def _parse_dom(self, page: Page, keyword: str, max_posts: int) -> List[Post]:
        """
        備用方案：從 Facebook 頁面 DOM 中擷取貼文內容。
        Facebook 的 DOM 結構經常變動，此方法僅作為回退方案。
        """
        posts: List[Post] = []
        try:
            # 嘗試各種可能的貼文容器選擇器
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
                        # 過濾掉明顯不是貼文的元素
                        if any(skip in text for skip in ["登入", "註冊", "Log In", "Sign Up"]):
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
                    break  # 如果某個 selector 有結果就不再嘗試其他的

        except Exception as e:
            self.logger.warning(f"FB DOM 解析失敗: {e}")

        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        return re.findall(r"#(\w+)", text)


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = FacebookScraper(headless=True)
        posts = await scraper.scrape(["傳說對決"], max_posts=5)
        for p in posts:
            print(f"  [{p.platform}] {p.author}: {p.content[:80]}...")
            print(f"    URL: {p.url}")
            print()

    asyncio.run(main())
