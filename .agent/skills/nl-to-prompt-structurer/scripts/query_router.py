"""Query Router — Phase 62 S4 自然語言 → P61 API 呼叫規格。

把中 / 英文自然語言查詢解析為 P61 HistoryTrendQuery 的呼叫規格 dict，
讓 caller（AI / CLI / slash）拿去直接執行。

四模式路由：
  1. hero_trend   — 偵測到 1 個英雄名
  2. heroes_trend — 偵測到 2~5 個英雄名
  3. overall_trend — 偵測到「整體」/「overall」
  4. platform_trend — 偵測到「平台」/「platform」
  fallback → overall_trend（無法判定時）

英雄名候選：動態掃描 data/ 目錄（零維護、自適應新英雄）。
天數 / 日期 / weighted 旗標全走 regex 解析。
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .lang_detector import detect_lang

# ── P61 loader import（動態英雄名候選）────────────────────
_P61_SCRIPTS = Path(__file__).resolve().parents[2] / "history-trend-query" / "scripts"


def _get_hero_candidates(data_dir: Optional[Path] = None, days: int = 30) -> List[str]:
    """動態掃描 data/ 目錄最近 N 天的 analysis_*.json，聯集所有 hero_stats keys。"""
    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[3] / "data"
    data_dir = Path(data_dir)
    if not data_dir.exists():
        return []

    heroes: List[str] = []
    seen: set = set()
    today = date.today()

    for i in range(days):
        d = today - timedelta(days=i)
        fp = data_dir / f"analysis_{d.strftime('%Y%m%d')}.json"
        if not fp.exists():
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                payload = json.load(f)
            hs = payload.get("hero_stats")
            if isinstance(hs, dict):
                for name in hs.keys():
                    if name not in seen:
                        seen.add(name)
                        heroes.append(name)
        except Exception:
            continue
    return heroes


# ── 天數解析 ──────────────────────────────────────────────

# 中文數字映射
_ZH_DIGITS = {"一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
              "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
              "二十": 20, "三十": 30}

# 單位倍率
_UNIT_MULT_ZH = {"天": 1, "日": 1, "週": 7, "周": 7, "星期": 7, "個月": 30, "月": 30}
_UNIT_MULT_EN = {"day": 1, "days": 1, "week": 1, "weeks": 7, "month": 30, "months": 30}

_DEFAULT_DAYS = 14


def _parse_days(text: str) -> int:
    """從文字中解析天數。回 int；解析失敗回 _DEFAULT_DAYS。"""
    # 中文：(數字|中文數字)(天|日|週|周|星期|個月|月)
    m = re.search(r"(\d+|[一二兩三四五六七八九十]+)\s*(個月|星期|週|周|天|日|月)", text)
    if m:
        raw_num, unit = m.group(1), m.group(2)
        if raw_num.isdigit():
            num = int(raw_num)
        else:
            num = _ZH_DIGITS.get(raw_num)
            if num is None:
                return _DEFAULT_DAYS
        mult = _UNIT_MULT_ZH.get(unit, 1)
        return max(1, num * mult)

    # 英文：(number) (day|days|week|weeks|month|months)
    m = re.search(r"(\d+)\s*(days?|weeks?|months?)", text, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        unit = m.group(2).lower()
        mult = _UNIT_MULT_EN.get(unit, 1)
        return max(1, num * mult)

    return _DEFAULT_DAYS


# ── until 日期解析 ────────────────────────────────────────

def _parse_until(text: str) -> Optional[str]:
    """從文字中解析截止日期 YYYY-MM-DD 字串。回 None 表未指定。"""
    # 明確日期格式
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if m:
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return d.isoformat()
        except ValueError:
            pass

    # 中文：昨天/前天/今天/今日
    if "前天" in text:
        return (date.today() - timedelta(days=2)).isoformat()
    if "昨天" in text or "昨日" in text:
        return (date.today() - timedelta(days=1)).isoformat()

    # 英文：yesterday/today
    lo = text.lower()
    if "yesterday" in lo:
        return (date.today() - timedelta(days=1)).isoformat()

    return None


# ── weighted 旗標 ─────────────────────────────────────────

def _parse_weighted(text: str) -> bool:
    """偵測是否要加權。"""
    lo = text.lower()
    return "加權" in text or "weighted" in lo


# ── 模式判定關鍵字 ────────────────────────────────────────

_OVERALL_KW_ZH = ["整體", "全部", "總體", "全局", "概況", "全面"]
_OVERALL_KW_EN = ["overall", "total", "general", "all"]
_PLATFORM_KW_ZH = ["平台", "各平台", "平台別"]
_PLATFORM_KW_EN = ["platform", "platforms", "per platform", "by platform"]


def _detect_mode(text: str, detected_heroes: List[str]) -> str:
    """根據文字和偵測到的英雄名決定路由模式。"""
    lo = text.lower()

    # 平台優先（關鍵字明確度最高）
    for kw in _PLATFORM_KW_ZH:
        if kw in text:
            return "platform_trend"
    for kw in _PLATFORM_KW_EN:
        if kw in lo:
            return "platform_trend"

    # 整體
    for kw in _OVERALL_KW_ZH:
        if kw in text:
            return "overall_trend"
    for kw in _OVERALL_KW_EN:
        if kw in lo:
            return "overall_trend"

    # 英雄數量
    n = len(detected_heroes)
    if n == 1:
        return "hero_trend"
    if 2 <= n <= 5:
        return "heroes_trend"

    # fallback
    return "overall_trend"


# ── 英雄名偵測 ────────────────────────────────────────────

def _detect_heroes(text: str, candidates: List[str]) -> List[str]:
    """從文字中偵測英雄名。長名優先（避免子串互吃）、保序。"""
    if not candidates:
        return []

    # 長名優先排序
    sorted_cands = sorted(candidates, key=lambda s: -len(s))
    hits: List[str] = []
    lo_text = text.lower()
    seen: set = set()

    for cand in sorted_cands:
        if cand.lower() in lo_text and cand not in seen:
            hits.append(cand)
            seen.add(cand)

    # 保出現順序
    if len(hits) > 1:
        hits.sort(key=lambda h: text.lower().find(h.lower()))

    return hits[:5]  # 上限 5 軌


# ── 主入口 ────────────────────────────────────────────────

def route_query(
    text: str,
    data_dir: Optional[Path] = None,
    hero_candidates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """自然語言 → P61 呼叫規格 dict。

    參數：
        text: 自然語言查詢
        data_dir: 資料目錄（None → 預設 data/）
        hero_candidates: 手動提供英雄候選（None → 動態掃描 data/）

    回傳 RouteResult dict：
    {
        "api": "hero_trend" | "heroes_trend" | "overall_trend" | "platform_trend",
        "kwargs": {...},
        "fallback": bool,
        "debug": {...}
    }
    """
    if not text or not text.strip():
        return {
            "api": "overall_trend",
            "kwargs": {"days": _DEFAULT_DAYS},
            "fallback": True,
            "debug": {
                "detected_heroes": [],
                "detected_days": _DEFAULT_DAYS,
                "detected_until": None,
                "raw_input": text or "",
            },
        }

    # 動態英雄候選
    if hero_candidates is None:
        hero_candidates = _get_hero_candidates(data_dir)

    # 解析各元素
    detected_heroes = _detect_heroes(text, hero_candidates)
    detected_days = _parse_days(text)
    detected_until = _parse_until(text)
    weighted = _parse_weighted(text)

    # 路由決策
    api = _detect_mode(text, detected_heroes)
    is_fallback = (
        api == "overall_trend"
        and len(detected_heroes) == 0
        and not any(kw in text for kw in _OVERALL_KW_ZH)
        and not any(kw in text.lower() for kw in _OVERALL_KW_EN)
    )

    # 組裝 kwargs
    kwargs: Dict[str, Any] = {"days": detected_days}
    if detected_until:
        kwargs["until"] = detected_until
    if weighted:
        kwargs["weighted"] = weighted

    if api == "hero_trend" and detected_heroes:
        kwargs["hero_name"] = detected_heroes[0]
    elif api == "heroes_trend" and detected_heroes:
        kwargs["hero_names"] = detected_heroes

    return {
        "api": api,
        "kwargs": kwargs,
        "fallback": is_fallback,
        "debug": {
            "detected_heroes": detected_heroes,
            "detected_days": detected_days,
            "detected_until": detected_until,
            "raw_input": text,
        },
    }


if __name__ == "__main__":
    import sys as _sys

    if len(_sys.argv) < 2:
        print("Usage: py query_router.py <query>")
        _sys.exit(1)

    query = " ".join(_sys.argv[1:])
    result = route_query(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
