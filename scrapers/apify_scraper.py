"""
Apify Instagram 雲端爬蟲模組。

使用 Apify 平台上的現成爬蟲 Actor (apify/instagram-scraper)
直接深入 Instagram 抓取公開貼文，穩定且具備高匿名性。
"""

import logging
from typing import List, Optional

from apify_client import ApifyClientAsync
import config
from scrapers.tavily_searcher import SearchResult


class ApifyInstagramScraper:
    """
    透過 Apify 抓取 Instagram 貼文。
    """

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or config.APIFY_TOKEN
        self.logger = logging.getLogger(f"{__name__}.ApifyInstagramScraper")

    async def search(
        self,
        keywords: List[str],
        max_results_per_keyword: int = 5,
    ) -> List[SearchResult]:
        """
        對每個關鍵字呼叫 Apify Instagram 爬蟲。
        """
        if not self.api_token:
            self.logger.error("APIFY_TOKEN 未設定，無法啟用 Apify 爬蟲")
            return []

        all_results: List[SearchResult] = []
        client = ApifyClientAsync(self.api_token)

        for keyword in keywords:
            try:
                self.logger.info(f"正在啟動 Apify 爬蟲抓取 IG: {keyword} (這可能需要 1~2 分鐘)...")
                
                # Actor: apify/instagram-scraper
                run_input = {
                    "search": keyword,
                    "searchType": "hashtag",
                    "resultsLimit": max_results_per_keyword,
                }

                # 呼叫並等待執行完畢
                run = await client.actor("apify/instagram-scraper").call(run_input=run_input)
                
                # 取得結果
                dataset_client = client.dataset(run["defaultDatasetId"])
                items = await dataset_client.list_items()
                
                post_count = 0
                for item in items.items:
                    # 避免沒有內容的貼文
                    caption = item.get("caption") or item.get("text") or ""
                    url = item.get("url") or ""
                    owner = item.get("ownerUsername") or "instagram_user"
                    
                    if caption and url:
                        all_results.append(
                            SearchResult(
                                title=f"[{keyword}] IG 貼文 (@{owner})",
                                content=caption[:1000],  # 限制長度
                                url=url,
                                source=owner,
                                platform="instagram",
                            )
                        )
                        post_count += 1

                self.logger.info(f"Apify IG 關鍵字 '{keyword}' 取得 {post_count} 筆結果。")

            except Exception as e:
                self.logger.error(f"Apify Instagram 爬蟲失敗 (keyword: {keyword}): {e}")

        # 回傳綜合結果
        self.logger.info(f"Apify 共取得 {len(all_results)} 筆 Instagram 結果。")
        return all_results
