"""
爬蟲基底類別與共用資料模型。
所有平台爬蟲都繼承 BaseScraper 並實作 scrape() 方法。
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Post:
    """統一的貼文資料模型，各平台爬蟲輸出皆轉換為此格式。"""

    platform: str  # "instagram" | "threads" | "facebook"
    author: str
    content: str
    url: str
    timestamp: Optional[str] = None  # ISO 8601
    likes: int = 0
    comments: int = 0
    shares: int = 0
    hashtags: List[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class BaseScraper(ABC):
    """
    爬蟲抽象基底類別。

    提供統一介面、重試邏輯、隨機延遲，子類只需實作 _do_scrape()。
    """

    PLATFORM: str = "unknown"
    MAX_RETRIES: int = 3
    MIN_DELAY: float = 2.0
    MAX_DELAY: float = 5.0

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.logger = logging.getLogger(f"{__name__}.{self.PLATFORM}")

    async def scrape(self, keywords: List[str], max_posts: int = 30) -> List[Post]:
        """
        對外公開的爬取介面。內建重試與延遲機制。
        """
        all_posts: List[Post] = []

        for keyword in keywords:
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    self.logger.info(
                        f"[{self.PLATFORM}] 搜尋關鍵字: '{keyword}' (第 {attempt} 次嘗試)"
                    )
                    posts = await self._do_scrape(keyword, max_posts)
                    all_posts.extend(posts)
                    self.logger.info(
                        f"[{self.PLATFORM}] 關鍵字 '{keyword}' 取得 {len(posts)} 篇貼文"
                    )
                    break  # 成功就跳出重試迴圈

                except Exception as e:
                    self.logger.warning(
                        f"[{self.PLATFORM}] 第 {attempt} 次嘗試失敗: {e}"
                    )
                    if attempt == self.MAX_RETRIES:
                        self.logger.error(
                            f"[{self.PLATFORM}] 關鍵字 '{keyword}' 已達最大重試次數，跳過。"
                        )
                    else:
                        # Exponential backoff + jitter
                        wait = (2 ** attempt) + random.uniform(0, 1)
                        self.logger.info(f"等待 {wait:.1f} 秒後重試...")
                        await asyncio.sleep(wait)

            # 每組關鍵字之間加入隨機延遲，降低被偵測風險
            delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
            await asyncio.sleep(delay)

        # 去重（依 url 判斷）
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            if post.url not in seen_urls:
                seen_urls.add(post.url)
                unique_posts.append(post)

        self.logger.info(
            f"[{self.PLATFORM}] 共取得 {len(unique_posts)} 篇不重複貼文"
        )
        return unique_posts

    @abstractmethod
    async def _do_scrape(self, keyword: str, max_posts: int) -> List[Post]:
        """子類實作實際的爬取邏輯。"""
        ...

    async def _random_delay(self, min_s: float = 1.0, max_s: float = 3.0):
        """注入隨機延遲，模擬人類行為。"""
        await asyncio.sleep(random.uniform(min_s, max_s))
