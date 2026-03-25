"""
Threads 公開貼文爬蟲。

使用 Playwright 攔截 Threads 的後端 API 回應，
從搜尋頁面擷取與關鍵字相關的串文。
"""

import json
import logging
from typing import List, Optional
from playwright.async_api import async_playwright, Page  # type: ignore[import]

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
                """攔截後端 API 回應。"""
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
                self.logger.info(f"正在存取: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await self._random_delay(3, 5)

                # 捲動載入更多內容
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_delay(1.5, 3)

                # 從攔截到的 API 資料中解析
                posts.extend(self._parse_api_data(captured_data, max_posts))

                # 備用：DOM 解析
                if not posts:
                    self.logger.info("API 攔截無資料，改用 DOM 解析")
                    posts.extend(await self._parse_dom(page, keyword, max_posts))

            except Exception as e:
                self.logger.error(f"Threads 爬取失敗: {e}")
                raise
            finally:
                await browser.close()

        return posts[:max_posts]

    def _parse_api_data(self, captured_data: list, max_posts: int) -> List[Post]:
        """從 API 回應中嘗試解析貼文資料。"""
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
                self.logger.debug(f"解析 Threads API 資料失敗: {e}")
                continue

        return posts

    def _find_thread_items(self, data, depth: int = 0) -> list:
        """遞迴搜尋回應中的串文項目。"""
        if depth > 10:
            return []

        items = []
        if isinstance(data, dict):
            # 尋找常見的串文結構
            if "thread_items" in data:
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
        """將 Threads API 項目轉換為 Post。"""
        try:
            # Threads 資料結構可能有多層嵌套
            post_data = item.get("post", item)
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
            self.logger.debug(f"串文轉換失敗: {e}")
            return None

    async def _parse_dom(self, page: Page, keyword: str, max_posts: int) -> List[Post]:
        """備用方案：從 DOM 中擷取可見的文字內容。"""
        posts: List[Post] = []
        try:
            # 尋找看起來像貼文容器的元素
            elements = await page.query_selector_all(
                '[data-pressable-container="true"], article, [role="article"]'
            )

            for elem in elements[:max_posts]:
                text = await elem.inner_text()
                if text and len(text.strip()) > 10:
                    # 嘗試找到連結
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
            self.logger.warning(f"Threads DOM 解析失敗: {e}")

        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        import re
        return re.findall(r"#(\w+)", text)


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        scraper = ThreadsScraper(headless=True)
        posts = await scraper.scrape(["傳說對決"], max_posts=5)
        for p in posts:
            print(f"  [{p.platform}] {p.author}: {p.content[:80]}...")
            print(f"    URL: {p.url}")
            print()

    asyncio.run(main())
