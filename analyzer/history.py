"""
歷史趨勢解析引擎 (Historical Delta Engine)。
掃描存檔資料，計算輿情數值與勝率的時序變動 (Today vs. Avg)，並產出漲跌指標。
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)

class HistoryResolver:
    """負責歷史數據的比對與趨勢分析。"""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or config.DATA_DIR
        self.history_days = 7

    def resolve_trends(self, today_summary: Dict[str, Any], showcase: bool = False) -> Dict[str, Any]:
        """
        比對今日與過去一週的數據，計算 Delta。支援任務演示模式 (Phase 34)。
        """
        self.logger.info(f"  [History] 正在解析趨勢 (Showcase Mode: {showcase})")
        
        # ── 演示模式數據補全 (Phase 34)：強制最高優先權 ──
        if showcase:
            self.logger.info("啟動任務演示模式：正在注入 7 天精選趨勢數據...")
            from datetime import timedelta
            import random
            
            # 建立過去 7 天的標籤與模擬聲量峰值
            labels = [(datetime.now() - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]
            volumes = [random.randint(45, 98) for _ in range(7)]
            
            return {
                "overall": {"volume_pct": 15.5, "is_red_alert": False},
                "heroes": {hero: {"volume_pct": random.uniform(5, 20)} for hero in config.HERO_WATCHLIST},
                "weekly_vol_pulse": {
                    "volumes": volumes,
                    "labels": labels,
                    "average": sum(volumes) / len(volumes)
                },
                "alerts": []
            }

        if not archives:
            logger.info("  [!] 無法找到過往數據，提供備援 Delta 結構。")
            today_vol = today_summary.get("total_posts", 0)
            return {
                "overall": {"volume_pct": 0.0, "avg_baseline": today_vol, "is_red_alert": False},
                "heroes": {},
                "weekly_vol_pulse": {
                    "volumes": [today_vol], 
                    "labels": [datetime.now().strftime("%m/%d")], 
                    "average": today_vol
                },
                "alerts": []
            }

        results = {
            "overall": self._calculate_overall_delta(today_summary, archives),
            "heroes": self._calculate_hero_deltas(today_summary, archives),
            "weekly_vol_pulse": self._get_weekly_pulse(today_summary, archives)
        }
        
        # ── 智慧警報判定 (Phase 30) ──
        results["alerts"] = self._detect_alerts(results, today_summary)
        
        return results

    def _calculate_hero_deltas(self, today: Dict[str, Any], archives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算特定英雄在聲量、情緒比例上的週均值變動。"""
        hero_deltas = {}
        target_hero_id = today.get("hero_focus", {}).get("name", "")
        if not target_hero_id:
            return hero_deltas

        # 彙整過去該英雄的所有分值
        past_scores = []
        for arch in archives:
            h_data = arch.get("hero_focus", {})
            if h_data.get("name") == target_hero_id:
                past_scores.append(h_data.get("sentiment_score", 0.5))

        if past_scores:
            avg_past_score = sum(past_scores) / len(past_scores)
            today_score = today.get("hero_focus", {}).get("sentiment_score", 0.5)
            # 計算情緒偏離度
            score_delta = round((today_score - avg_past_score) * 100, 1)
            hero_deltas[target_hero_id] = {
                "sentiment_delta": score_delta,
                "health_status": "stable" if abs(score_delta) < 15 else ("improving" if score_delta > 0 else "declining")
            }
            
        return hero_deltas

    def _detect_alerts(self, trends: Dict[str, Any], today: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        判斷是否觸發戰略預警，並附加戰術建議 (Phase 31)。
        """
        alerts = []
        overall = trends.get("overall", {})
        
        # 戰術建議矩陣 (Phase 31)
        ADVICE = {
            "VOL_SPIKE": "偵測到異常流量，請確認是否為『新活動預熱』或『突發性伺服器事故』，建議加派社群小編監看論壇留言。",
            "NEG_RATIO": "情緒指引：負評佔比過高。請立即核對是否與『英雄強度平衡』有關，必要時發布『平衡性調整前瞻』以安撫玩家。",
            "WINRATE_CRASH": "數據異常：該英雄勝率跌幅劇烈。請技術團隊核對是否有『特定裝備 Bug』或『技能判定機制變動』，考慮暫時禁選。",
            "DATA_SILENCE": "情報真空：今日關鍵數據缺口較大。請檢查爬蟲 API 額度或監控對象之社群（Dcard/PTT）是否因維修而暫停發文。"
        }
        
        # 1. 總聲量異常監控
        vol_pct = overall.get("volume_pct", 0)
        if vol_pct > config.ALERT_VOL_DELTA:
            alerts.append({
                "type": "error",
                "label": f"總聲量異常暴增 (▲ {vol_pct}%)",
                "advice": ADVICE["VOL_SPIKE"]
            })
        elif vol_pct < -50 and overall.get("avg_baseline", 0) > 10:
            # 新增：聲量腰斬警戒 (通常代表數據抓取異常或大環境靜默)
            alerts.append({
                "type": "info",
                "label": f"核心聲量異常靜默 (▼ {abs(vol_pct)}%)",
                "advice": ADVICE["DATA_SILENCE"]
            })
            
        # 2. 情緒危機預警
        sent = today.get("sentiment_distribution", {})
        total_v = sum(sent.values()) if sent else 0
        if total_v > 0:
            neg_ratio = (sent.get("negative", 0) / total_v) * 100
            if neg_ratio > config.ALERT_NEG_RATIO:
                alerts.append({
                    "type": "warning",
                    "label": f"輿情嚴重惡化 (負評佔比 {round(neg_ratio, 1)}%)",
                    "advice": ADVICE["NEG_RATIO"]
                })
        
        # 3. 戰鬥數據預警 (Phase 31)
        combat_stats = today.get("combat_stats", {})
        # 如果今日總聲量正常卻完全沒有戰鬥數據，可能是數據 API 故障的預警
        if not combat_stats and today.get("total_posts", 0) > 10:
             alerts.append({
                "type": "warning",
                "label": "戰鬥數據同步中測 (Sync Latency)",
                "advice": "目前無法抓取勝率數值，將轉由 AI 根據玩家評論分析判斷當前生態強度。"
             })

        for hero_name, stats in combat_stats.items():
            win_rate = stats.get("win_rate", 0)
            if win_rate > 0 and win_rate < (50.0 - getattr(config, "ALERT_WR_DROP", 3.0)):
                alerts.append({
                    "type": "error",
                    "label": f"戰鬥數據警戒：{hero_name} 勝率異常偏低 ({win_rate}%)",
                    "advice": ADVICE["WINRATE_CRASH"]
                })
        
        return alerts

    def _load_recent_archives(self) -> List[Dict[str, Any]]:
        """加載過去 7 天的分析報告 JSON。"""
        archives = []
        now = datetime.now()
        
        for i in range(1, self.history_days + 1):
            target_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            file_path = self.data_dir / f"analysis_{target_date}.json"
            
            if file_path.exists():
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    archives.append(data)
                except Exception as e:
                    logger.error(f"  [!] 加载歷史檔失敗 {file_path.name}: {e}")
        
        return archives

    def _calculate_overall_delta(self, today: Dict[str, Any], archives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算總聲量變動 (對比過去 7 天平均值)。"""
        today_vol = today.get("total_posts", 0)
        
        # 取得過去幾天的聲量數列
        past_vols = [a.get("total_posts", 0) for a in archives if a.get("total_posts") is not None]
        
        if not past_vols:
            return {"volume_pct": 0.0, "is_red_alert": False}
            
        avg_vol = sum(past_vols) / len(past_vols)
        
        # 計算相對於均值的偏移
        if avg_vol == 0:
            vol_delta = 0.0
        else:
            vol_delta = round(float((today_vol - avg_vol) / avg_vol * 100), 1)

        return {
            "volume_pct": vol_delta,
            "avg_baseline": round(float(avg_vol), 1),
            "is_red_alert": vol_delta > 30.0 # 比平均高出 30% 視為異常
        }

    def _calculate_hero_deltas(self, today: Dict[str, Any], archives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算特定英雄在聲量、情緒比例上的週均值變動。"""
        hero_deltas = {}
        # 這裡可以擴展細節英雄的移動平均比對
        return hero_deltas

    def _get_weekly_pulse(self, today: Dict[str, Any], archives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """產出過去 7 天的數據序列，供前端畫週脈搏圖。"""
        # 最舊 -> 最新
        vols = [a.get("total_posts", 0) for a in reversed(archives)]
        vols.append(today.get("total_posts", 0))
        
        # 產出日期標籤
        dates = [(datetime.now() - timedelta(days=i)).strftime("%m/%d") for i in range(len(vols)-1, -1, -1)]
        
        avg_val = sum(vols) / len(vols) if vols else 0.0
        
        return {
            "volumes": vols,
            "labels": dates,
            "average": round(float(avg_val), 1)
        }
