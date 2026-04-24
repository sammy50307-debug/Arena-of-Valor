"""
HistoryTrendQuery — Phase 61 Stage 2 查詢核心

單英雄時序 Python API，純 JSON 輸出（S3 再加渲染）。
嚴格合約：只信 loader 回傳 status=='ok' 的資料；
缺日 / schema 不合 / 英雄不在 hero_stats 三種情境顯式標記區分。
"""

from __future__ import annotations

import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from time_series_loader import TimeSeriesLoader  # noqa: E402

logger = logging.getLogger(__name__)


class HistoryTrendQuery:
    """被動時序查詢器。S2 提供單英雄 hero_trend API。"""

    def __init__(
        self,
        loader: Optional[TimeSeriesLoader] = None,
        data_dir: Optional[Any] = None,
    ) -> None:
        if loader is not None and data_dir is not None:
            raise ValueError("loader 與 data_dir 不能同時指定")
        self.loader = loader or TimeSeriesLoader(data_dir=data_dir)

    @staticmethod
    def _resolve_until(until: Any) -> date:
        """解析 until 參數；None→date.today()（local time）。"""
        if until is None:
            return date.today()
        if isinstance(until, date) and not isinstance(until, datetime):
            return until
        if isinstance(until, datetime):
            return until.date()
        if isinstance(until, str):
            return datetime.strptime(until, "%Y-%m-%d").date()
        raise ValueError(f"無法解析 until：{until!r}")

    def hero_trend(
        self,
        hero_name: str,
        days: int,
        until: Any = None,
        weighted: bool = False,
    ) -> Dict[str, Any]:
        """
        單英雄時序查詢。

        參數：
            weighted: avg_sentiment_mean 是否用 count 加權。
                False (預設) = 算術平均（各日權重相同）
                True         = 加權平均 sum(sent_i * count_i) / sum(count_i)

        回傳結構：
        {
            "hero": "芽芽",
            "days": 14,
            "range": {"start": "2026-03-23", "end": "2026-04-05"},
            "points": [
                {"date": "...", "status": "ok"|"missing"|"invalid"|"hero_absent",
                 "count": int|None, "avg_sentiment": float|None}
            ],
            "summary": {
                "days_requested": 14,
                "days_ok": 3,
                "days_missing": 8,
                "days_invalid": 0,
                "days_hero_absent": 3,
                "total_count": 16,
                "avg_sentiment_mean": 0.88,
                "avg_sentiment_mode": "weighted"|"arithmetic",
                "coverage_ratio": 0.214
            }
        }
        """
        if not isinstance(hero_name, str) or not hero_name.strip():
            raise ValueError("hero_name 不可為空")
        if not isinstance(days, int) or days < 1:
            raise ValueError(f"days 必須為 >= 1 的整數，got {days!r}")

        end = self._resolve_until(until)
        start = end - timedelta(days=days - 1)
        series = self.loader.load_range(start, end)

        points: List[Dict[str, Any]] = []
        ok_count = 0
        missing_count = 0
        invalid_count = 0
        absent_count = 0
        total_count = 0
        sentiment_sum = 0.0       # 算術平均用：sum(sent_i)
        sentiment_n = 0           # 算術平均用：有 sent 值的日數
        weighted_sum = 0.0        # 加權平均用：sum(sent_i * count_i)
        weighted_denom = 0        # 加權平均用：sum(count_i)

        for entry in series:
            iso = entry["date"]
            status = entry["status"]

            if status == "missing":
                points.append({"date": iso, "status": "missing",
                               "count": None, "avg_sentiment": None})
                missing_count += 1
                continue

            if status == "invalid":
                # R5 合約：invalid 絕不進統計，即使 data 還在
                points.append({"date": iso, "status": "invalid",
                               "count": None, "avg_sentiment": None})
                invalid_count += 1
                continue

            # status == "ok"
            hero_stats = entry["data"].get("hero_stats", {}) or {}
            if hero_name not in hero_stats:
                points.append({"date": iso, "status": "hero_absent",
                               "count": 0, "avg_sentiment": None})
                absent_count += 1
                continue

            h = hero_stats[hero_name] or {}
            count = h.get("count")
            sentiment = h.get("avg_sentiment")

            points.append({
                "date": iso,
                "status": "ok",
                "count": count,
                "avg_sentiment": sentiment,
            })
            ok_count += 1
            if isinstance(count, (int, float)):
                total_count += int(count)
            if isinstance(sentiment, (int, float)):
                sentiment_sum += float(sentiment)
                sentiment_n += 1
                if isinstance(count, (int, float)) and count > 0:
                    weighted_sum += float(sentiment) * float(count)
                    weighted_denom += int(count)

        if weighted:
            avg_mean = (weighted_sum / weighted_denom) if weighted_denom > 0 else None
        else:
            avg_mean = (sentiment_sum / sentiment_n) if sentiment_n > 0 else None

        return {
            "hero": hero_name,
            "days": days,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "points": points,
            "summary": {
                "days_requested": days,
                "days_ok": ok_count,
                "days_missing": missing_count,
                "days_invalid": invalid_count,
                "days_hero_absent": absent_count,
                "total_count": total_count,
                "avg_sentiment_mean": avg_mean,
                "avg_sentiment_mode": "weighted" if weighted else "arithmetic",
                "coverage_ratio": ok_count / days if days > 0 else 0.0,
            },
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="HistoryTrendQuery CLI（debug 用）")
    parser.add_argument("--hero", required=True, help="英雄名稱")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--until", default=None, help="YYYY-MM-DD；預設今日")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--weighted", action="store_true", help="sentiment 以 count 加權")
    args = parser.parse_args()

    q = HistoryTrendQuery(data_dir=args.data_dir) if args.data_dir else HistoryTrendQuery()
    result = q.hero_trend(args.hero, args.days, until=args.until, weighted=args.weighted)
    print(json.dumps(result, ensure_ascii=False, indent=2))
