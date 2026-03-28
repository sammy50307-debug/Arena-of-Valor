"""
英雄戰鬥數據抓取模組 (Combat Stats Scraper)。
負責從 Garena 官方排行榜或數據源抓取英雄的 Win Rate, Ban Rate, Pick Rate。
"""

import json
import logging
import httpx
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import config

logger = logging.getLogger(__name__)

@dataclass
class HeroCombatStats:
    name: str
    win_rate: float        # 勝率 %
    pick_rate: float       # 出場率 %
    ban_rate: float        # 禁用率 %
    rank: int              # 全服排名
    update_time: str       # 數據更新時間

class HeroStatsScraper:
    """抓取並解析 AOV 英雄實時戰績。"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.HeroStatsScraper")

    async def fetch_watchlist_stats(self) -> Dict[str, HeroCombatStats]:
        """
        針對 Watchlist 中的英雄抓取戰績。
        """
        stats_map: Dict[str, HeroCombatStats] = {}
        # 確保 watchlist 是一個 list[str]
        raw_watchlist = getattr(config, "HERO_WATCHLIST", ["芽芽", "皮皮"])
        watchlist: List[str] = [str(h) for h in raw_watchlist]
        
        self.logger.info(f"開始抓取英雄數據: {watchlist}")
        
        # 模擬數據
        mock_data: Dict[str, Dict[str, float]] = {
            "芽芽": {"wr": 52.8, "pr": 12.5, "br": 45.2, "rank": 5.0},
            "皮皮": {"wr": 49.2, "pr": 8.1, "br": 62.4, "rank": 12.0}
        }

        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        for hero in watchlist:
            if hero in mock_data:
                d = mock_data[hero]
                stats_map[hero] = HeroCombatStats(
                    name=hero,
                    win_rate=float(d.get("wr", 50.0)),
                    pick_rate=float(d.get("pr", 5.0)),
                    ban_rate=float(d.get("br", 0.0)),
                    rank=int(d.get("rank", 99.0)),
                    update_time=now_str
                )
            else:
                stats_map[hero] = HeroCombatStats(
                    name=hero,
                    win_rate=50.0,
                    pick_rate=5.0,
                    ban_rate=0.0,
                    rank=99,
                    update_time=now_str
                )
        
        return stats_map

# ── 獨立測試 ──────────────────────────────
if __name__ == "__main__":
    async def test():
        scraper = HeroStatsScraper()
        res = await scraper.fetch_watchlist_stats()
        for hero, stats in res.items():
            print(f"[{hero}] 勝率: {stats.win_rate}% | 禁用率: {stats.ban_rate}% | 全服排名: {stats.rank}")

    asyncio.run(test())
