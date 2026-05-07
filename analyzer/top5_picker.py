"""
Top-5 新聞精選器 (P65-S2)。

排序公式：final_score = relevance_score × decay × boost
  - relevance_score: analysis.relevance_score（LLM 評分）或 post.score（原始搜尋評分）
  - decay: max(DECAY_MIN, 1 - age_hours / DECAY_HOURS)  — 越新越好
  - boost: HERO_BOOST_FACTOR 若為焦點英雄文章，else 1.0

跨日去重：透過 news_history_indexer；重複文章仍可入選但帶「↻」徽章（R4）。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import config
from analyzer import url_normalizer
from analyzer import news_history_indexer as indexer

logger = logging.getLogger(__name__)

_DECAY_HOURS: int = config.TOP5_SCORE_DECAY_HOURS
_DECAY_MIN: float = config.TOP5_SCORE_DECAY_MIN
_BOOST: float = config.HERO_BOOST_FACTOR


# ── 內部工具函式 ─────────────────────────────────────────

def _extract_score(post_entry: dict) -> float:
    """從 analyzed_post 或 raw post dict 取得基礎分數。"""
    analysis = post_entry.get("analysis", {})
    post = post_entry.get("post", post_entry)
    score = (
        analysis.get("relevance_score")
        or post.get("score")
        or post_entry.get("score")
    )
    try:
        return float(score) if score is not None else 0.5
    except (TypeError, ValueError):
        return 0.5


def _compute_decay(timestamp_str: str | None, *, now: datetime | None = None) -> float:
    """時間衰減因子：越新越接近 1.0，最低 DECAY_MIN。"""
    if not timestamp_str:
        return 1.0
    now = now or datetime.now()
    _FMTS = [
        ("%Y-%m-%d %H:%M:%S", 19),
        ("%Y-%m-%d", 10),
        ("%Y/%m/%d", 10),
    ]
    dt = None
    for fmt, length in _FMTS:
        try:
            dt = datetime.strptime(timestamp_str[:length], fmt)
            break
        except ValueError:
            continue
    if dt is None:
        return 1.0
    age_hours = max(0.0, (now - dt).total_seconds() / 3600)
    return max(_DECAY_MIN, 1.0 - age_hours / _DECAY_HOURS)


def _compute_boost(post_entry: dict, hero_focus: str) -> float:
    """焦點英雄 boost；evergreen 白名單（R14）不衰減但也不 boost 疊加。"""
    if not hero_focus:
        return 1.0
    post = post_entry.get("post", post_entry)
    analysis = post_entry.get("analysis", {})
    heroes = post.get("detected_heroes", []) or analysis.get("detected_heroes", [])
    is_focus = (
        post.get("is_hero_focus")
        or analysis.get("is_hero_focus")
        or hero_focus in (post.get("title", "") or "")
        or hero_focus in (post.get("content", "") or "")
        or hero_focus in heroes
    )
    return _BOOST if is_focus else 1.0


def _get_timestamp(post_entry: dict) -> str | None:
    post = post_entry.get("post", post_entry)
    return post.get("published_date") or post.get("timestamp")


def _get_url(post_entry: dict) -> str:
    post = post_entry.get("post", post_entry)
    return post.get("url", "#")


# ── 主函式 ───────────────────────────────────────────────

def pick_top5(
    analyzed_posts: list[dict],
    *,
    hero_focus: str | None = None,
    today: str | None = None,
    now: datetime | None = None,
    history_index: dict | None = None,
    bypass_dedup: bool = False,
    top_n: int = 5,
) -> tuple[list[dict[str, Any]], dict]:
    """
    從 analyzed_posts 選出 top N 篇，帶 picker metadata。

    Args:
        analyzed_posts: generator.py 的 analyzed_posts 列表
        hero_focus: 焦點英雄名稱（預設 config.HERO_FOCUS_NAME）
        today: 當日 YYYY-MM-DD（預設 datetime.now()）
        now: 當下時間點（測試用）
        history_index: 注入式去重索引（None = 從磁碟讀）
        bypass_dedup: showcase/--bypass-dedup 旗標 (R4)
        top_n: 要取幾篇（預設 5）

    Returns:
        (cards, updated_history_index)
        cards 每筆為:
          {
            "post": {...},        # 原始 post 資料
            "analysis": {...},    # 原始 analysis 資料（可能為 {}）
            "picker": {
              "final_score": float,
              "base_score": float,
              "decay": float,
              "boost": float,
              "is_duplicate": bool,
              "dup_badge": str,   # "" | "day1" | "day3" | "day7"
              "norm_url": str,
            }
          }
        updated_history_index: 更新後的去重索引（呼叫者決定是否寫磁碟）
    """
    hero_focus = hero_focus or getattr(config, "HERO_FOCUS_NAME", "")
    today = today or datetime.now().strftime("%Y-%m-%d")
    now = now or datetime.now()

    if history_index is None:
        history_index = indexer.load_index()
    history_index = indexer.prune_old(history_index, today=today)

    scored: list[tuple[float, dict]] = []

    for entry in analyzed_posts:
        url = _get_url(entry)
        norm_url = url_normalizer.normalize(url)
        is_dup, dup_badge = (False, "") if bypass_dedup else indexer.is_duplicate(url, history_index, today=today)

        base = _extract_score(entry)
        ts = _get_timestamp(entry)
        decay = _compute_decay(ts, now=now)
        boost = _compute_boost(entry, hero_focus)
        final = base * decay * boost

        post = entry.get("post", entry)
        analysis = entry.get("analysis", {})

        card = {
            "post": post,
            "analysis": analysis,
            "picker": {
                "final_score": round(final, 4),
                "base_score": round(base, 4),
                "decay": round(decay, 4),
                "boost": round(boost, 4),
                "is_duplicate": is_dup,
                "dup_badge": dup_badge,
                "norm_url": norm_url,
            },
        }
        scored.append((final, card))
        logger.debug("picker score url=%s base=%.3f decay=%.3f boost=%.3f final=%.3f dup=%s",
                     norm_url, base, decay, boost, final, is_dup)

    scored.sort(key=lambda t: t[0], reverse=True)
    cards = [card for _, card in scored[:top_n]]

    urls_to_record = [c["post"].get("url", "#") for c in cards if not c["picker"]["is_duplicate"]]
    history_index = indexer.record_urls(urls_to_record, history_index, today=today)

    logger.info("picker: %d posts → top %d selected (hero_focus=%s, bypass_dedup=%s)",
                len(analyzed_posts), len(cards), hero_focus, bypass_dedup)
    return cards, history_index
