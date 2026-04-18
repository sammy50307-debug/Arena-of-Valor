"""
Daily Diff Radar — 每日差異雷達。

比對今日 vs 昨日（或最近可用前日）的 analysis_YYYYMMDD.json，
萃取關鍵變化並輸出精簡差異摘要，供快速日報 briefing 使用。
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "data"
ANALYSIS_PATTERN = re.compile(r"^analysis_(\d{8})\.json$")

# 警戒門檻
ALERT_HIGH_SENTIMENT = 0.30
ALERT_HIGH_VOLUME_PCT = 50.0
ALERT_MED_SENTIMENT = 0.15
ALERT_MED_VOLUME_PCT = 25.0


class DailyDiffRadar:
    """
    對比兩份 analysis JSON，輸出差異摘要。

    典型使用：
        radar = DailyDiffRadar()
        report = radar.radar()   # 自動找最新兩天

    或指定日期：
        report = radar.radar(today_date="2026-04-19")
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.logger = logging.getLogger(f"{__name__}.DailyDiffRadar")

    # ── 公開介面 ──────────────────────────────────────

    def radar(self, today_date: Optional[str] = None) -> Dict:
        """自動偵測最新兩天 analysis，輸出差異摘要。"""
        files = self._list_analysis_files()
        if len(files) < 2:
            return {
                "error": "需要至少兩份 analysis 檔才能比對",
                "available": [f.name for f in files],
            }

        if today_date:
            today_path = self.data_dir / f"analysis_{today_date.replace('-', '')}.json"
            if not today_path.exists():
                return {"error": f"找不到 {today_path.name}"}
            prev_path = self._find_previous(files, today_path)
        else:
            today_path = files[-1]
            prev_path = files[-2]

        if prev_path is None:
            return {"error": "找不到今日之前的 analysis 檔"}

        today_data = self._load(today_path)
        prev_data = self._load(prev_path)
        return self.diff(today_data, prev_data,
                         today_date=self._date_from_path(today_path),
                         prev_date=self._date_from_path(prev_path))

    def diff(
        self,
        today: Dict,
        yesterday: Dict,
        today_date: str = "",
        prev_date: str = "",
    ) -> Dict:
        """核心差異計算。"""
        # 情緒分數
        today_sent = float(today.get("overall", {}).get("sentiment_score", 0))
        prev_sent = float(yesterday.get("overall", {}).get("sentiment_score", 0))
        sentiment_delta = round(today_sent - prev_sent, 4)

        # 聲量
        today_vol = int(today.get("total_posts", 0))
        prev_vol = int(yesterday.get("total_posts", 0))
        volume_delta = today_vol - prev_vol
        volume_delta_pct = round(
            (volume_delta / prev_vol * 100) if prev_vol > 0 else 0.0, 2
        )

        # 趨勢變化
        today_trend = today.get("overall", {}).get("trend", "")
        prev_trend = yesterday.get("overall", {}).get("trend", "")
        trend_change = (
            f"{prev_trend} → {today_trend}" if prev_trend != today_trend
            else f"{today_trend}（無變化）"
        )

        # 英雄上下榜
        today_heroes = set((today.get("hero_stats") or {}).keys())
        prev_heroes = set((yesterday.get("hero_stats") or {}).keys())
        new_heroes = sorted(today_heroes - prev_heroes)
        dropped_heroes = sorted(prev_heroes - today_heroes)

        # 共同英雄情緒變化
        hero_sentiment_shifts = self._compute_hero_shifts(
            today.get("hero_stats") or {},
            yesterday.get("hero_stats") or {},
        )

        # 各平台變化
        platform_changes = self._compute_platform_changes(
            today.get("platform_breakdown") or {},
            yesterday.get("platform_breakdown") or {},
        )

        # Alert 等級
        alert_level = self._compute_alert_level(sentiment_delta, volume_delta_pct)

        return {
            "today_date": today_date,
            "yesterday_date": prev_date,
            "sentiment_delta": sentiment_delta,
            "volume_delta": volume_delta,
            "volume_delta_pct": volume_delta_pct,
            "trend_change": trend_change,
            "new_heroes": new_heroes,
            "dropped_heroes": dropped_heroes,
            "hero_sentiment_shifts": hero_sentiment_shifts,
            "platform_changes": platform_changes,
            "alert_level": alert_level,
        }

    # ── 內部工具 ──────────────────────────────────────

    def _list_analysis_files(self) -> List[Path]:
        """列出 data_dir 內所有 analysis_YYYYMMDD.json，按日期排序。"""
        if not self.data_dir.exists():
            return []
        files = []
        for p in self.data_dir.iterdir():
            if ANALYSIS_PATTERN.match(p.name):
                files.append(p)
        files.sort(key=lambda p: p.name)
        return files

    def _find_previous(self, files: List[Path], today_path: Path) -> Optional[Path]:
        """回傳 today_path 之前最近的一份。"""
        prev = None
        for p in files:
            if p.name < today_path.name:
                prev = p
            elif p.name == today_path.name:
                break
        return prev

    def _date_from_path(self, p: Path) -> str:
        m = ANALYSIS_PATTERN.match(p.name)
        if not m:
            return ""
        d = m.group(1)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"

    def _load(self, p: Path) -> Dict:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            self.logger.warning(f"讀取 {p.name} 失敗: {e}")
            return {}

    def _compute_hero_shifts(
        self, today_heroes: Dict, prev_heroes: Dict
    ) -> Dict[str, float]:
        """共同英雄的 avg_sentiment 變化，僅保留變化 >= 0.05 的項目。"""
        shifts = {}
        common = set(today_heroes.keys()) & set(prev_heroes.keys())
        for hero in common:
            t = float(today_heroes[hero].get("avg_sentiment", 0))
            y = float(prev_heroes[hero].get("avg_sentiment", 0))
            delta = round(t - y, 3)
            if abs(delta) >= 0.05:
                shifts[hero] = delta
        return dict(sorted(shifts.items(), key=lambda kv: abs(kv[1]), reverse=True))

    def _compute_platform_changes(
        self, today_plat: Dict, prev_plat: Dict
    ) -> Dict[str, Dict]:
        """各平台 post_count 的變化。"""
        all_platforms = set(today_plat.keys()) | set(prev_plat.keys())
        result = {}
        for plat in sorted(all_platforms):
            t = int(today_plat.get(plat, {}).get("post_count", 0))
            y = int(prev_plat.get(plat, {}).get("post_count", 0))
            if t == y == 0:
                continue
            result[plat] = {"today": t, "yesterday": y, "delta": t - y}
        return result

    def _compute_alert_level(self, sent_delta: float, vol_pct: float) -> str:
        a_sent = abs(sent_delta)
        a_vol = abs(vol_pct)
        if a_sent >= ALERT_HIGH_SENTIMENT or a_vol >= ALERT_HIGH_VOLUME_PCT:
            return "HIGH"
        if a_sent >= ALERT_MED_SENTIMENT or a_vol >= ALERT_MED_VOLUME_PCT:
            return "MEDIUM"
        return "LOW"


# ── 直接執行 ─────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = DailyDiffRadar()
    report = r.radar()
    print(json.dumps(report, ensure_ascii=False, indent=2))
