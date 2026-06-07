"""
英雄戰績數據載入模組 (Combat Stats Loader)。
由於官方數據源已下線，本模組現透過載入本地手動維護的 YAML 檔案來取得真實的官方勝率、登場率和禁用率。
"""

import json
import logging
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
    data_source: str = "none"
    tier: str = ""         # 熱度梯隊（如 T1）

class HeroStatsScraper:
    """載入並解析 AOV 英雄實時戰績。"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.HeroStatsScraper")

    async def fetch_watchlist_stats(self) -> Dict[str, HeroCombatStats]:
        """
        針對 Watchlist 中的英雄載入真實官方戰績。
        """
        stats_map: Dict[str, HeroCombatStats] = {}
        # 確保 watchlist 是一個 list[str]
        raw_watchlist = getattr(config, "HERO_WATCHLIST", ["芽芽", "皮皮"])
        watchlist: List[str] = [str(h) for h in raw_watchlist]
        
        self.logger.info(f"開始載入英雄數據: {watchlist}")
        
        yaml_path = getattr(config, "HERO_COMBAT_STATS_PATH", None)
        if not yaml_path or not yaml_path.exists():
            self.logger.warning(f"戰績設定檔不存在: {yaml_path}")
            return {}

        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"解析戰績設定檔失敗: {e}")
            return {}

        if not data or not isinstance(data, dict):
            self.logger.warning("戰績設定檔格式無效")
            return {}

        updated_date = data.get("updated_date", "")
        heroes_data = data.get("heroes", {}) or {}

        for hero in watchlist:
            if hero in heroes_data:
                d = heroes_data[hero]
                if d is None:
                    continue
                stats_map[hero] = HeroCombatStats(
                    name=hero,
                    win_rate=float(d.get("win_rate", 50.0) if d.get("win_rate") is not None else 50.0),
                    pick_rate=float(d.get("pick_rate", 5.0) if d.get("pick_rate") is not None else 5.0),
                    ban_rate=float(d.get("ban_rate", 0.0) if d.get("ban_rate") is not None else 0.0),
                    rank=int(d.get("rank", 99) if d.get("rank") is not None else 99),
                    update_time=updated_date,
                    data_source="manual_yaml",
                    tier=str(d.get("tier", "") or "")
                )
        
        return stats_map

# ── 獨立測試 ──────────────────────────────
if __name__ == "__main__":
    async def test():
        scraper = HeroStatsScraper()
        res = await scraper.fetch_watchlist_stats()
        for hero, stats in res.items():
            print(f"[{hero}] 勝率: {stats.win_rate}% | 禁用率: {stats.ban_rate}% | 來源: {stats.data_source}")

    asyncio.run(test())
