"""
TimeSeriesLoader — Phase 61 Stage 1 地基

依日期範圍載入 data/analysis_YYYYMMDD.json 時序資料，
缺日顯式標記 status='missing' 並 warning log，
並依 resources/schema_version.json 做 contract check。
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class TimeSeriesLoader:
    """依日期範圍掃 analysis_YYYYMMDD.json，回傳時序列表；缺日標 N/A。"""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        schema_path: Optional[Path] = None,
    ) -> None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[3].parent / "data"
        self.data_dir = Path(data_dir)

        if schema_path is None:
            schema_path = (
                Path(__file__).resolve().parent.parent
                / "resources"
                / "schema_version.json"
            )
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _parse_date(d: Any) -> date:
        if isinstance(d, date):
            return d
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, str):
            return datetime.strptime(d, "%Y-%m-%d").date()
        raise ValueError(f"無法解析日期：{d!r}")

    def _day_file(self, day: date) -> Path:
        return self.data_dir / f"analysis_{day.strftime('%Y%m%d')}.json"

    def validate(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """回傳 (is_valid, missing_fields)。缺任一必要欄位即 invalid。"""
        missing: List[str] = []
        req = self.schema.get("required_fields", {})

        for key in req.get("top_level", []):
            if key not in record:
                missing.append(key)

        overall = record.get("overall", {})
        if isinstance(overall, dict):
            for key in req.get("overall", []):
                if key not in overall:
                    missing.append(f"overall.{key}")

        dist = record.get("sentiment_distribution", {})
        if isinstance(dist, dict):
            for key in req.get("sentiment_distribution", []):
                if key not in dist:
                    missing.append(f"sentiment_distribution.{key}")

        return (len(missing) == 0, missing)

    def load_day(self, day: Any) -> Dict[str, Any]:
        """載入單日資料。缺檔或 schema 不合即回 missing entry + warning。"""
        d = self._parse_date(day)
        path = self._day_file(d)
        iso = d.isoformat()

        if not path.exists():
            logger.warning("缺日資料：%s（預期檔案 %s 不存在）", iso, path.name)
            return {
                "date": iso,
                "status": "missing",
                "reason": "file_not_found",
                "data": None,
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning("缺日資料：%s（JSON 解析失敗 %s）", iso, e)
            return {
                "date": iso,
                "status": "missing",
                "reason": f"json_decode_error: {e}",
                "data": None,
            }

        ok, missing_fields = self.validate(payload)
        if not ok:
            logger.warning(
                "Schema 不合：%s 缺欄位 %s（仍回 data 但標 invalid）",
                iso,
                missing_fields,
            )
            return {
                "date": iso,
                "status": "invalid",
                "reason": "schema_mismatch",
                "missing_fields": missing_fields,
                "data": payload,
            }

        return {
            "date": iso,
            "status": "ok",
            "data": payload,
        }

    def load_range(
        self,
        start_date: Any,
        end_date: Any,
    ) -> List[Dict[str, Any]]:
        """載入 [start_date, end_date] 閉區間的每日資料。"""
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        if start > end:
            raise ValueError(f"start_date {start} 晚於 end_date {end}")

        series: List[Dict[str, Any]] = []
        cursor = start
        while cursor <= end:
            series.append(self.load_day(cursor))
            cursor += timedelta(days=1)

        missing_count = sum(1 for s in series if s["status"] == "missing")
        invalid_count = sum(1 for s in series if s["status"] == "invalid")
        if missing_count or invalid_count:
            logger.warning(
                "區間載入完成：%s~%s 共 %d 日，缺日 %d、schema 不合 %d",
                start,
                end,
                len(series),
                missing_count,
                invalid_count,
            )
        return series

    def load_last_n_days(self, n: int, until: Any = None) -> List[Dict[str, Any]]:
        """載入截至 until（含）往前 n 天的時序。until=None 取今日。"""
        if n < 1:
            raise ValueError("n 必須 >= 1")
        end = self._parse_date(until) if until else date.today()
        start = end - timedelta(days=n - 1)
        return self.load_range(start, end)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TimeSeriesLoader CLI（debug 用）")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args()

    loader = TimeSeriesLoader(data_dir=args.data_dir) if args.data_dir else TimeSeriesLoader()
    result = loader.load_range(args.start, args.end)
    print(json.dumps(
        [{k: v for k, v in r.items() if k != "data"} | {"has_data": r.get("data") is not None} for r in result],
        ensure_ascii=False,
        indent=2,
    ))
