"""
Apify Instagram ?²ç«¯?¬èŸ²æ¨¡ç???
ä½¿ç”¨ Apify å¹³å°ä¸Šç??¾æ??¬èŸ² Actor (apify/instagram-scraper)
?´æ¥æ·±å…¥ Instagram ?“å??¬é?è²¼æ?ï¼Œç©©å®šä??·å?é«˜åŒ¿?æ€§ã€?"""

import logging
from typing import List, Optional

from apify_client import ApifyClientAsync
import config
from scrapers.tavily_searcher import SearchResult


class ApifyInstagramScraper:
    """
    ?é? Apify ?“å? Instagram è²¼æ???    """

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or config.APIFY_TOKEN
        self.logger = logging.getLogger(f"{__name__}.ApifyInstagramScraper")

    async def search(
        self,
        keywords: List[str],
        max_results_per_keyword: int = 3,
    ) -> List[SearchResult]:
        """
        å°æ??‹é??µå??¼å« Apify Instagram ?¬èŸ²??        """
        if not self.api_token:
            self.logger.error("APIFY_TOKEN ?ªè¨­å®šï??¡æ??Ÿç”¨ Apify ?¬èŸ²")
            return []

        all_results: List[SearchResult] = []
        client = ApifyClientAsync(self.api_token)

        for keyword in keywords:
            try:
                self.logger.info(f"æ­?œ¨?Ÿå? Apify ?¬èŸ²?“å? IG: {keyword} (?™å¯?½é?è¦?1~2 ?†é?)...")
                
                # Actor: apify/instagram-scraper
                run_input = {
                    "search": keyword,
                    "searchType": "hashtag",
                    "resultsLimit": max_results_per_keyword,
                }

                # ?¼å«ä¸¦ç?å¾…åŸ·è¡Œå???                run = await client.actor("apify/instagram-scraper").call(run_input=run_input)
                
                # ?–å?çµæ?
                dataset_client = client.dataset(run["defaultDatasetId"])
                items = await dataset_client.list_items()
                
                post_count = 0
                for item in items.items:
                    # ?¿å?æ²’æ??§å®¹?„è²¼??                    caption = item.get("caption") or item.get("text") or ""
                    url = item.get("url") or ""
                    owner = item.get("ownerUsername") or "instagram_user"
                    
                    if caption and url:
                        all_results.append(
                            SearchResult(
                                title=f"[{keyword}] IG è²¼æ? (@{owner})",
                                content=caption[:1000],  # ?åˆ¶?·åº¦
                                url=url,
                                source=owner,
                                platform="instagram",
                            )
                        )
                        post_count += 1

                self.logger.info(f"Apify IG ?œéµå­?'{keyword}' ?–å? {post_count} ç­†ç??œã€?)

            except Exception as e:
                self.logger.error(f"Apify Instagram ?¬èŸ²å¤±æ? (keyword: {keyword}): {e}")

        # ?å‚³ç¶œå?çµæ?
        self.logger.info(f"Apify ?±å?å¾?{len(all_results)} ç­?Instagram çµæ???)
        return all_results
