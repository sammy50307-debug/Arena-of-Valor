"""
輿情時空熱度圖分析引擎 (Hero Sentiment Heatmap Engine)。
統計 24H 內的聲量消長、正負面情緒比重，為可視化提供數據矩陣。
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)

class HeatmapAnalyzer:
    """計算英雄聲量與情緒的熱度分布。"""

    def __init__(self, watchlist: List[str] = None):
        self.watchlist = watchlist or getattr(config, "HERO_WATCHLIST", ["芽芽", "皮皮"])

    def generate_matrix(self, analyzed_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        產出適用於 ECharts Heatmap 的數據結構。
        
        橫軸: 24 小時 (00:00 - 23:00)
        縱軸: Watchlist 英雄列表
        數值: [hour_index, hero_index, heat_score, sentiment_type]
        """
        # 初始化 24 小時數據結構
        hours = list(range(24))
        heroes = self.watchlist
        
        # heatmap_data [hour, hero, score, mood]
        # mood: 1(正), 0(中), -1(負)
        matrix = []
        
        # 建立英雄索引
        hero_idx_map = {name: i for i, name in enumerate(heroes)}
        
        # 統計容器 {hero: {hour: {'count': 0, 'score': 0}}}
        stats = {h: {hr: {"count": 0, "pos": 0, "neg": 0} for hr in hours} for h in heroes}

        for post_data in analyzed_posts:
            post = post_data.get("post", {})
            analysis = post_data.get("analysis", {})
            
            # 解析日期與時間小時
            try:
                dt_str = post.get("date", "")
                # 兼容格式如 "2024-03-28 14:30" 或 "2024-03-28"
                if len(dt_str) > 10:
                    dt = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
                else:
                    dt = datetime.now() # 預設今日
                hour = dt.hour
            except:
                hour = datetime.now().hour

            detected_heroes = post.get("detected_heroes", [])
            sentiment = analysis.get("sentiment", "neutral").lower()

            for hero in detected_heroes:
                if hero in stats:
                    stats[hero][hour]["count"] += 1
                    if "positive" in sentiment:
                        stats[hero][hour]["pos"] += 1
                    elif "negative" in sentiment:
                        stats[hero][hour]["neg"] += 1

                # 最終矩陣轉換
        for h_name in heroes:
            h_idx = hero_idx_map[h_name]
            for hr in hours:
                s = stats[h_name][hr]
                count = s["count"]
                
                # 計算熱度權重 (簡化版積分: 總量 + 正向加成 - 負向權重)
                if count == 0:
                    score = 0.0
                else:
                    score = float(count) + (float(s["pos"]) * 0.5) - (float(s["neg"]) * 1.5)
                
                # 情緒類型判定
                mood_type = 0 # Neutral
                if s["neg"] > s["pos"]: mood_type = -1
                elif s["pos"] > s["neg"]: mood_type = 1
                
                matrix.append([hr, h_idx, round(score, 1), mood_type])

        return {
            "hours": hours,
            "heroes": heroes,
            "data": matrix,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

# ── 獨立測試 ──────────────────────────────
if __name__ == "__main__":
    analyzer = HeatmapAnalyzer()
    dummy_posts = [
        {"post": {"date": "2024-03-28 10:00", "detected_heroes": ["芽芽"]}, "analysis": {"sentiment": "positive"}},
        {"post": {"date": "2024-03-28 10:30", "detected_heroes": ["芽芽"]}, "analysis": {"sentiment": "positive"}},
        {"post": {"date": "2024-03-28 14:00", "detected_heroes": ["皮皮"]}, "analysis": {"sentiment": "negative"}},
    ]
    res = analyzer.generate_matrix(dummy_posts)
    print(res)
