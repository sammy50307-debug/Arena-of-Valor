"""
Tavily 搜尋模組。

直接呼叫 Tavily REST API（不使用 tavily-python 套件，
避免 tiktoken 相依 Rust 的問題），僅需 httpx。
"""

import logging
from typing import List, Optional
from dataclasses import dataclass, field, asdict

import httpx

import config

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass
class SearchResult:
    """標準化的搜尋結果資料模型。"""
    title: str
    content: str
    url: str
    source: str = ""       # 來源網域
    platform: str = "web"  # 推測的平台（instagram/threads/facebook/web）
    score: float = 0.0
    region: str = "TW"     # 新增區域標籤 (TW/TH/VN)
    published_date: str = "" # 新增發佈日期 
    detected_heroes: List[str] = field(default_factory=list) # 偵測到的名單英雄

    def to_dict(self) -> dict:
        return asdict(self)


class TavilySearcher:
    """
    呼叫 Tavily Search API 搜集與《傳說對決》相關的公開資訊。
    Tavily 會自動從全網（含 IG/Threads/FB 公開頁、新聞、論壇）取回結果。
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.TAVILY_API_KEY
        self.logger = logging.getLogger(f"{__name__}.TavilySearcher")

    async def search(
        self,
        max_results_per_region: int = 5,
    ) -> List[SearchResult]:
        """
        遍歷各個區域並執行同步搜尋與匯流。
        """
        if not self.api_key:
            self.logger.error("TAVILY_API_KEY 未設定")
            return []

        all_results: List[SearchResult] = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=45) as client:
            # 遍歷 config 定義的區域進行搜集
            for region in config.REGIONS:
                keywords = config.REGIONAL_KEYWORDS.get(region, ["傳說對決"])
                self.logger.info(f"🌐 開始搜集區域情報: {region} | 關鍵字: {keywords}")

                for keyword in keywords:
                    try:
                        results = await self._search_keyword(
                            client, keyword, max_results_per_region // len(keywords), region
                        )
                        for r in results:
                            if r.url not in seen_urls:
                                seen_urls.add(r.url)
                                all_results.append(r)
                    except Exception as e:
                        self.logger.error(f"搜尋區域 {region} 關鍵字 '{keyword}' 失敗: {e}")

        self.logger.info(f"🌍 全球情報匯流完成 | 共取得 {len(all_results)} 筆不重複結果")
        return all_results

    async def _search_keyword(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        max_results: int,
        region: str = "TW"
    ) -> List[SearchResult]:
        """對單一關鍵字呼叫 Tavily API。"""
        # ── 搜尋場景進化：大師級語意導航 ──
        # 1. 排除項擴張 (租借、抽獎、行銷字眼)
        exclude_terms = "-買賣 -帳號 -收購 -代購 -代練 -打字 -交易 -租借 -抽獎 -互追 -互粉 -互讚"
        
        # 2. 自動意圖注入 (若針對英雄，自動導向討論語境)
        if any(hero_kw in keyword for hero_kw in ["芽芽", config.HERO_FOCUS_NAME]):
            intent_qualifier = "(評價 OR 攻略 OR 配裝 OR 心得 OR 削弱 OR 造型特效)"
            processed_query = f"{keyword} {intent_qualifier} {exclude_terms}"
        else:
            processed_query = f"{keyword} {exclude_terms}"
        
        payload = {
            "api_key": self.api_key,
            "query": processed_query,
            "search_depth": "advanced", # 升級回進階搜尋以確保資料品質
            "max_results": max_results,
            "include_domains": [
                "dcard.tw", "threads.net", "instagram.com", "ptt.cc",
                "facebook.com", "youtube.com", "mobile01.com",
                "forum.gamer.com.tw",
                "pantip.com", "sanook.com", "gamek.vn", "lienquan.garena.vn"
            ],
            "include_raw_content": False,
            "time_range": "day"
        }

        response = await client.post(TAVILY_SEARCH_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")
            content = item.get("content", "")
            platform = self._detect_platform(url)
            
            # 建立偵測標籤：判斷這篇貼文提到名單中的哪些英雄
            detected = [
                hero for hero in config.HERO_WATCHLIST 
                if hero in title or hero in content
            ]
            
            results.append(
                SearchResult(
                    title=title,
                    content=content,
                    url=url,
                    source=item.get("source", ""),
                    platform=platform,
                    score=item.get("score", 0.0),
                    region=region,
                    published_date=item.get("published_date", ""),
                    detected_heroes=detected
                )
            )
        return results

    @staticmethod
    def _detect_platform(url: str) -> str:
        """從 URL 推測來源平台。"""
        url_lower = url.lower()
        if "instagram.com" in url_lower:
            return "instagram"
        elif "threads.net" in url_lower:
            return "threads"
        elif "facebook.com" in url_lower or "fb.com" in url_lower:
            return "facebook"
        elif "ptt.cc" in url_lower:
            return "ptt"
        elif "dcard.tw" in url_lower:
            return "dcard"
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        else:
            return "web"


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    logging.basicConfig(level=logging.INFO)

    async def main():
        searcher = TavilySearcher()
        results = await searcher.search(max_results_per_region=5)
        for r in results:
            print(f"[{r.platform}] {r.title}")
            print(f"  URL: {r.url}")
            print(f"  內容: {r.content[:100]}...")
            print()

    asyncio.run(main())
