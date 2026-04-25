"""
HistoryTrendQuery — Phase 61 Stage 2/4 查詢核心

S2 單英雄時序 + S4 多維度（多英雄比對 / 整體輿情 / 平台別走勢）。
嚴格合約：只信 loader 回傳 status=='ok' 的資料；
缺日 / schema 不合 / 英雄不在 / 平台不在 四種情境顯式標記區分。

S4 設計決策（2026-04-25 主公核准 B 全選）：
    - 多英雄上限 5 軌（避免 SVG palette 與 legend 擠爆）
    - 跨軌 min-max 正規化共用 _cross_normalize helper
    - raw=True 不寫 normalized_* 欄位（debug / 下游用）
    - platform_trend 用 status='absent' 通用詞（與 hero_trend 的 hero_absent 區分但同義）
"""

from __future__ import annotations

import logging
import sys
from datetime import date, datetime, timedelta
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from time_series_loader import TimeSeriesLoader  # noqa: E402

logger = logging.getLogger(__name__)


DAYS_HARD_CAP = 90  # S5 F2：days 參數硬上限（R11），配 LRU cache 控記憶體與效能


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
    def _validate_days(days: Any) -> None:
        """S5 F2：days 必須為 1~DAYS_HARD_CAP 的 int，超過硬上限即噴錯。"""
        if not isinstance(days, int) or isinstance(days, bool) or days < 1:
            raise ValueError(f"days 必須為 >= 1 的整數，got {days!r}")
        if days > DAYS_HARD_CAP:
            raise ValueError(
                f"days 超過硬上限 {DAYS_HARD_CAP} 天，got {days}"
                "（如需更長區間請分段查詢或調整 DAYS_HARD_CAP）"
            )

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
        fuzzy: bool = True,
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
        self._validate_days(days)

        end = self._resolve_until(until)
        start = end - timedelta(days=days - 1)
        series = self.loader.load_range(start, end)

        # S5 F4：fuzzy hero name resolution（cutoff=0.6，主公 2026-04-25 核定）
        # 候選名單 = 區間內所有 ok 日 hero_stats 的聯集
        # 精確命中或全 missing 時不啟動；命中模糊比對時把 hero_name 重指、附 resolved_from
        resolved_from: Optional[str] = None
        if fuzzy:
            candidates: set = set()
            for entry in series:
                if entry["status"] == "ok":
                    hs = (entry["data"] or {}).get("hero_stats") or {}
                    if isinstance(hs, dict):
                        candidates.update(hs.keys())
            if candidates and hero_name not in candidates:
                matches = get_close_matches(
                    hero_name, list(candidates), n=1, cutoff=0.6
                )
                if matches:
                    logger.info(
                        "fuzzy hero match：%r → %r（cutoff=0.6）",
                        hero_name, matches[0],
                    )
                    resolved_from = hero_name
                    hero_name = matches[0]

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
            "resolved_from": resolved_from,  # S5 F4：fuzzy 命中時為原輸入；精確或無命中為 None
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


    # ────────────────────────────────────────────────────
    # S4 共用 helper：跨軌 min-max 正規化
    # ────────────────────────────────────────────────────
    @staticmethod
    def _cross_normalize(
        all_points_lists: List[List[Dict[str, Any]]],
        value_key: str,
        normalized_key: str,
    ) -> None:
        """
        對多條軌道做共用 min-max 正規化，就地寫入 normalized_key 欄。
        只考慮 status=='ok' 且 value_key 為數值的點。span=0 時統一填 0.5。
        """
        all_values: List[float] = []
        for pts in all_points_lists:
            for p in pts:
                if p.get("status") == "ok":
                    v = p.get(value_key)
                    if isinstance(v, (int, float)):
                        all_values.append(float(v))
        if not all_values:
            return
        lo, hi = min(all_values), max(all_values)
        span = hi - lo
        for pts in all_points_lists:
            for p in pts:
                if p.get("status") == "ok":
                    v = p.get(value_key)
                    if isinstance(v, (int, float)):
                        p[normalized_key] = (
                            (float(v) - lo) / span if span > 0 else 0.5
                        )

    # ────────────────────────────────────────────────────
    # S5 F3：每軌獨立 min-max 正規化（解 R17 小量級被壓平）
    # ────────────────────────────────────────────────────
    @staticmethod
    def _per_normalize(
        all_points_lists: List[List[Dict[str, Any]]],
        value_key: str,
        normalized_key: str,
    ) -> None:
        """
        對每條軌道**各自**做 min-max 正規化，就地寫入 normalized_key 欄。
        小量級軌與大量級軌共圖時可看出各自形狀（不被全局最大壓平至 0~0.05）。
        """
        for pts in all_points_lists:
            ok_vals = [
                float(p[value_key]) for p in pts
                if p.get("status") == "ok" and isinstance(p.get(value_key), (int, float))
            ]
            if not ok_vals:
                continue
            lo, hi = min(ok_vals), max(ok_vals)
            span = hi - lo
            for p in pts:
                if p.get("status") == "ok":
                    v = p.get(value_key)
                    if isinstance(v, (int, float)):
                        p[normalized_key] = (
                            (float(v) - lo) / span if span > 0 else 0.5
                        )

    @classmethod
    def _apply_normalize(
        cls,
        all_points_lists: List[List[Dict[str, Any]]],
        value_key: str,
        normalized_key: str,
        axis: str,
    ) -> None:
        """S5 F3 dispatcher：依 axis 走 cross 或 per。"""
        if axis == "cross":
            cls._cross_normalize(all_points_lists, value_key, normalized_key)
        elif axis == "per":
            cls._per_normalize(all_points_lists, value_key, normalized_key)
        else:
            raise ValueError(
                f"normalize_axis 必須為 'cross' 或 'per'，got {axis!r}"
            )

    # ────────────────────────────────────────────────────
    # S4 F1：多英雄比對
    # ────────────────────────────────────────────────────
    def heroes_trend(
        self,
        hero_names: List[str],
        days: int,
        until: Any = None,
        weighted: bool = False,
        raw: bool = False,
        normalize_axis: str = "cross",
        fuzzy: bool = True,
    ) -> Dict[str, Any]:
        """
        多英雄比對。每個英雄產一份 hero_trend，再跨英雄 min-max 正規化 count。

        參數：
            hero_names: 1~5 個英雄名（重複/空字串噴 ValueError）
            raw: True → 不算 normalized_count（單純多軌原值）
                 False（預設）→ points 加 normalized_count ∈ [0,1]
            normalize_axis (S5 F3, R17):
                "cross"（預設）→ 全軌共用 min-max（看相對量級）
                "per"          → 各軌獨立 min-max（看各自形狀，小量級不被壓平）
        """
        if not isinstance(hero_names, list) or not hero_names:
            raise ValueError("hero_names 必須為非空 list")
        self._validate_days(days)
        if len(hero_names) > 5:
            raise ValueError(
                f"多英雄比對上限 5 軌，got {len(hero_names)}"
            )
        seen = set()
        for n in hero_names:
            if not isinstance(n, str) or not n.strip():
                raise ValueError(f"hero_names 含非法名稱：{n!r}")
            if n in seen:
                raise ValueError(f"hero_names 重複：{n!r}")
            seen.add(n)

        heroes = [
            self.hero_trend(n, days, until=until, weighted=weighted, fuzzy=fuzzy)
            for n in hero_names
        ]

        if not raw:
            self._apply_normalize(
                [h["points"] for h in heroes],
                value_key="count",
                normalized_key="normalized_count",
                axis=normalize_axis,
            )
        elif normalize_axis not in ("cross", "per"):
            # raw=True 仍要驗值合法（以免日後拿掉 raw 才發現參數錯）
            raise ValueError(
                f"normalize_axis 必須為 'cross' 或 'per'，got {normalize_axis!r}"
            )

        end = self._resolve_until(until)
        start = end - timedelta(days=days - 1)
        return {
            "mode": "heroes",
            "hero_names": list(hero_names),
            "days": days,
            "raw": raw,
            "normalize_axis": normalize_axis,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "heroes": heroes,
        }

    # ────────────────────────────────────────────────────
    # S4 F2：整體輿情走勢
    # ────────────────────────────────────────────────────
    def overall_trend(
        self,
        days: int,
        until: Any = None,
        raw: bool = False,
        normalize_axis: str = "cross",
    ) -> Dict[str, Any]:
        """
        整體輿情每日走勢：total_posts + sentiment_distribution 三欄並陳。
        缺日標 missing；schema 不合標 invalid；不再有 absent（不綁英雄）。
        """
        self._validate_days(days)

        end = self._resolve_until(until)
        start = end - timedelta(days=days - 1)
        series = self.loader.load_range(start, end)

        points: List[Dict[str, Any]] = []
        ok_count = missing_count = invalid_count = 0
        total_sum = pos_sum = neg_sum = neu_sum = 0

        for entry in series:
            iso = entry["date"]
            st = entry["status"]
            if st == "missing":
                points.append({
                    "date": iso, "status": "missing",
                    "total_posts": None, "positive": None,
                    "negative": None, "neutral": None,
                })
                missing_count += 1
                continue
            if st == "invalid":
                points.append({
                    "date": iso, "status": "invalid",
                    "total_posts": None, "positive": None,
                    "negative": None, "neutral": None,
                })
                invalid_count += 1
                continue

            data = entry["data"] or {}
            tp = data.get("total_posts")
            sd = data.get("sentiment_distribution", {}) or {}
            pos = sd.get("positive", 0) or 0
            neg = sd.get("negative", 0) or 0
            neu = sd.get("neutral", 0) or 0

            points.append({
                "date": iso, "status": "ok",
                "total_posts": tp,
                "positive": pos, "negative": neg, "neutral": neu,
            })
            ok_count += 1
            if isinstance(tp, (int, float)):
                total_sum += int(tp)
            if isinstance(pos, (int, float)):
                pos_sum += int(pos)
            if isinstance(neg, (int, float)):
                neg_sum += int(neg)
            if isinstance(neu, (int, float)):
                neu_sum += int(neu)

        if not raw:
            self._apply_normalize(
                [points],
                value_key="total_posts",
                normalized_key="normalized_total",
                axis=normalize_axis,
            )
        elif normalize_axis not in ("cross", "per"):
            raise ValueError(
                f"normalize_axis 必須為 'cross' 或 'per'，got {normalize_axis!r}"
            )

        return {
            "mode": "overall",
            "days": days,
            "raw": raw,
            "normalize_axis": normalize_axis,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "points": points,
            "summary": {
                "days_requested": days,
                "days_ok": ok_count,
                "days_missing": missing_count,
                "days_invalid": invalid_count,
                "total_posts_sum": total_sum,
                "positive_sum": pos_sum,
                "negative_sum": neg_sum,
                "neutral_sum": neu_sum,
                "coverage_ratio": ok_count / days if days > 0 else 0.0,
            },
        }

    # ────────────────────────────────────────────────────
    # S4 F3：平台別走勢
    # ────────────────────────────────────────────────────
    def platform_trend(
        self,
        days: int,
        until: Any = None,
        raw: bool = False,
        normalize_axis: str = "cross",
    ) -> Dict[str, Any]:
        """
        平台別走勢。聯集所有 ok 日 platform_breakdown 出現過的 key 為平台清單。
        某日有檔但缺該平台 → status='absent' / post_count=0；缺日 → missing。

        S5 F5 嚴驗（R18）：
            - platform_breakdown 非 dict → 整日該平台 invalid
            - 某平台 entry 非 dict → invalid
            - post_count 非數值 → invalid
        """
        self._validate_days(days)

        end = self._resolve_until(until)
        start = end - timedelta(days=days - 1)
        series = self.loader.load_range(start, end)

        # 第一輪：聯集平台清單（保序）。pb 非 dict 該日略過、不影響其他日。
        platforms: List[str] = []
        seen_p = set()
        for entry in series:
            if entry["status"] != "ok":
                continue
            pb_raw = (entry["data"] or {}).get("platform_breakdown")
            if not isinstance(pb_raw, dict):
                continue
            for p_name in pb_raw.keys():
                if p_name not in seen_p:
                    seen_p.add(p_name)
                    platforms.append(p_name)

        # 第二輪：對每個平台組軌道（S5 F5 R18 嚴驗）
        platform_data: Dict[str, List[Dict[str, Any]]] = {}
        for p_name in platforms:
            pts: List[Dict[str, Any]] = []
            for entry in series:
                iso = entry["date"]
                st = entry["status"]
                if st == "missing":
                    pts.append({"date": iso, "status": "missing", "post_count": None})
                    continue
                if st == "invalid":
                    pts.append({"date": iso, "status": "invalid", "post_count": None})
                    continue
                pb_raw = (entry["data"] or {}).get("platform_breakdown")
                # 整日 platform_breakdown 不是 dict → 該日該平台 invalid
                if not isinstance(pb_raw, dict):
                    pts.append({"date": iso, "status": "invalid", "post_count": None})
                    continue
                if p_name not in pb_raw:
                    pts.append({"date": iso, "status": "absent", "post_count": 0})
                    continue
                pdata = pb_raw[p_name]
                # 該平台 entry 非 dict → invalid（不再默默當 0）
                if not isinstance(pdata, dict):
                    pts.append({"date": iso, "status": "invalid", "post_count": None})
                    continue
                cnt = pdata.get("post_count")
                # post_count 缺、非數值或 bool → invalid
                if not isinstance(cnt, (int, float)) or isinstance(cnt, bool):
                    pts.append({"date": iso, "status": "invalid", "post_count": None})
                    continue
                pts.append({"date": iso, "status": "ok", "post_count": cnt})
            platform_data[p_name] = pts

        if not raw:
            self._apply_normalize(
                list(platform_data.values()),
                value_key="post_count",
                normalized_key="normalized_count",
                axis=normalize_axis,
            )
        elif normalize_axis not in ("cross", "per"):
            raise ValueError(
                f"normalize_axis 必須為 'cross' 或 'per'，got {normalize_axis!r}"
            )

        return {
            "mode": "platform",
            "days": days,
            "raw": raw,
            "normalize_axis": normalize_axis,
            "platforms": platforms,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "platform_data": platform_data,
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="HistoryTrendQuery CLI（debug 用）")
    parser.add_argument("--mode", choices=["hero", "heroes", "overall", "platform"], default="hero")
    parser.add_argument("--hero", help="英雄名稱（mode=hero）")
    parser.add_argument("--heroes", help="多英雄逗號分隔（mode=heroes）")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--until", default=None, help="YYYY-MM-DD；預設今日")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--weighted", action="store_true", help="sentiment 以 count 加權")
    parser.add_argument("--raw", action="store_true", help="不做跨軌 normalize")
    args = parser.parse_args()

    q = HistoryTrendQuery(data_dir=args.data_dir) if args.data_dir else HistoryTrendQuery()

    if args.mode == "hero":
        if not args.hero:
            parser.error("--mode=hero 需要 --hero")
        result = q.hero_trend(args.hero, args.days, until=args.until, weighted=args.weighted)
    elif args.mode == "heroes":
        if not args.heroes:
            parser.error("--mode=heroes 需要 --heroes")
        names = [s.strip() for s in args.heroes.split(",") if s.strip()]
        result = q.heroes_trend(names, args.days, until=args.until,
                                weighted=args.weighted, raw=args.raw)
    elif args.mode == "overall":
        result = q.overall_trend(args.days, until=args.until, raw=args.raw)
    else:
        result = q.platform_trend(args.days, until=args.until, raw=args.raw)

    print(json.dumps(result, ensure_ascii=False, indent=2))
