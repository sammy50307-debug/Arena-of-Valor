"""
Top-5 新聞精選器 (P65-S2 / P66.1)。

排序公式：final_score = relevance_score × decay × boost
  - relevance_score: analysis.relevance_score（LLM 評分）或 post.score（原始搜尋評分）
  - decay: max(DECAY_MIN, 1 - age_hours / DECAY_HOURS)  — 越新越好
  - boost: HERO_BOOST_FACTOR × source_boost（Dcard 微 boost）

跨日去重：透過 news_history_indexer；重複文章仍可入選但帶「↻」徽章（R4）。

P66.1 新增：
  - 黑名單過濾（configs/personal_blacklist.yaml，芽芽豁免）
  - Dcard 微 source boost（分數平手時 Dcard 優先）
  - enforce_diversity：5 卡至少 N 平台，只動「2 張一般卡」段
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import lru_cache
from typing import Any

import yaml

import config
from analyzer import url_normalizer
from analyzer import news_history_indexer as indexer

logger = logging.getLogger(__name__)

_DECAY_HOURS: int = config.TOP5_SCORE_DECAY_HOURS
_DECAY_MIN: float = config.TOP5_SCORE_DECAY_MIN
_BOOST: float = config.HERO_BOOST_FACTOR
_DCARD_BOOST: float = getattr(config, "DCARD_SOURCE_BOOST", 1.05)
_DIVERSITY_MIN: int = getattr(config, "DIVERSITY_MIN_PLATFORMS", 3)

# P70.1
_DUP_PENALTY: dict[str, float] = {
    "day1": getattr(config, "DUP_PENALTY_DAY1", 0.3),
    "day3": getattr(config, "DUP_PENALTY_DAY3", 0.2),
    "day7": getattr(config, "DUP_PENALTY_DAY7", 0.1),
}
_PLATFORM_RANK_DECAY: float = getattr(config, "PLATFORM_RANK_DECAY", 0.1)
_PLATFORM_RANK_MIN: float = getattr(config, "PLATFORM_RANK_MIN", 0.3)
_YAYA_REPEAT_BONUS: float = getattr(config, "YAYA_REPEAT_BONUS", 1.5)


# ── P66.1 黑名單載入 ─────────────────────────────────────

@lru_cache(maxsize=1)
def _load_blacklist() -> tuple[str, ...]:
    """載入個人黑名單詞表（lru_cache，程式生命週期只讀一次）。"""
    path = getattr(config, "PERSONAL_BLACKLIST_PATH", None)
    if not path:
        return ()
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        words = data.get("blacklist", []) or []
        return tuple(str(w).strip() for w in words if str(w).strip())
    except FileNotFoundError:
        logger.warning("personal_blacklist.yaml not found at %s", path)
        return ()
    except (yaml.YAMLError, OSError) as e:
        logger.warning("failed to load personal_blacklist.yaml: %s", e)
        return ()


def _reset_blacklist_cache() -> None:
    """測試用：清除 blacklist lru_cache。"""
    _load_blacklist.cache_clear()


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
        return _DECAY_MIN
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
        return _DECAY_MIN
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


def _compute_source_boost(post_entry: dict) -> float:
    """P66.1 — Dcard 來源微 boost（分數平手時 Dcard 優先進榜）。"""
    post = post_entry.get("post", post_entry)
    platform = (post.get("platform", "") or "").lower()
    return _DCARD_BOOST if platform == "dcard" else 1.0


def _is_yaya_related(post_entry: dict, hero_focus: str) -> bool:
    """P66.1 — 是否芽芽（焦點英雄）相關文章；用於黑名單豁免。"""
    if not hero_focus:
        return False
    post = post_entry.get("post", post_entry)
    analysis = post_entry.get("analysis", {})
    heroes = post.get("detected_heroes", []) or analysis.get("detected_heroes", [])
    return bool(
        post.get("is_hero_focus")
        or analysis.get("is_hero_focus")
        or hero_focus in (post.get("title", "") or "")
        or hero_focus in (post.get("content", "") or "")
        or hero_focus in heroes
    )


def _is_blacklisted(post_entry: dict, blacklist: tuple[str, ...]) -> str | None:
    """
    P66.1 — 標題或內文 contains 任一黑名單詞 → 回傳命中詞，否則 None。

    比對範圍：post.title + post.content
    """
    if not blacklist:
        return None
    post = post_entry.get("post", post_entry)
    haystack = (post.get("title", "") or "") + " " + (post.get("content", "") or "")
    for word in blacklist:
        if word and word in haystack:
            return word
    return None


def _get_platform(card: dict) -> str:
    """P66.1 — 抓 card 的平台（多樣性檢查用）。"""
    post = card.get("post", card)
    return (post.get("platform", "") or "").lower()


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
    record_history: bool = True,
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

    # P66.1 黑名單過濾（芽芽豁免）
    blacklist = _load_blacklist()
    filtered_posts: list[dict] = []
    for entry in analyzed_posts:
        if _is_yaya_related(entry, hero_focus):
            filtered_posts.append(entry)
            continue
        hit = _is_blacklisted(entry, blacklist)
        if hit:
            post = entry.get("post", entry)
            logger.info("filtered by blacklist: %s | post=%s", hit, post.get("url", "?"))
            continue
        filtered_posts.append(entry)

    scored: list[tuple[float, dict]] = []

    for entry in filtered_posts:
        url = _get_url(entry)
        norm_url = url_normalizer.normalize(url)
        is_dup, dup_badge = (False, "") if bypass_dedup else indexer.is_duplicate(url, history_index, today=today)

        base = _extract_score(entry)
        ts = _get_timestamp(entry)
        decay = _compute_decay(ts, now=now)
        boost = _compute_boost(entry, hero_focus) * _compute_source_boost(entry)
        is_yaya = _is_yaya_related(entry, hero_focus)

        # P70.1 A — 去重懲罰 / 芽芽重複加成
        if is_yaya and is_dup:
            dup_factor = _YAYA_REPEAT_BONUS
        elif is_dup:
            dup_factor = _DUP_PENALTY.get(dup_badge, 1.0)
        else:
            dup_factor = 1.0

        final = base * decay * boost * dup_factor

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
                "dup_factor": round(dup_factor, 4),
                "is_duplicate": is_dup,
                "dup_badge": dup_badge,
                "norm_url": norm_url,
            },
        }
        scored.append((final, card))
        logger.debug("picker score url=%s base=%.3f decay=%.3f boost=%.3f dup_factor=%.3f final=%.3f dup=%s",
                     norm_url, base, decay, boost, dup_factor, final, is_dup)

    # P70.1 B — 同平台排名衰減（芽芽豁免，不計入 platform_rank 計數）
    scored.sort(key=lambda t: t[0], reverse=True)
    platform_seen: dict[str, int] = {}
    adjusted: list[tuple[float, dict]] = []
    for score, card in scored:
        if _is_yaya_related(card, hero_focus):
            adjusted.append((score, card))
            continue
        plat = _get_platform(card)
        rank = platform_seen.get(plat, 0) + 1
        platform_seen[plat] = rank
        penalty = max(_PLATFORM_RANK_MIN, 1.0 - _PLATFORM_RANK_DECAY * (rank - 1))
        adj_score = score * penalty
        card["picker"]["platform_rank"] = rank
        card["picker"]["platform_penalty"] = round(penalty, 4)
        card["picker"]["final_score"] = round(adj_score, 4)
        adjusted.append((adj_score, card))
    adjusted.sort(key=lambda t: t[0], reverse=True)
    cards = [card for _, card in adjusted[:top_n]]

    if record_history:
        urls_to_record = [c["post"].get("url", "#") for c in cards if not c["picker"]["is_duplicate"]]
        history_index = indexer.record_urls(urls_to_record, history_index, today=today)

    logger.info("picker: %d posts (raw) → %d after blacklist → top %d selected (hero_focus=%s, bypass_dedup=%s)",
                len(analyzed_posts), len(filtered_posts), len(cards), hero_focus, bypass_dedup)
    return cards, history_index


# ── P66.1 多樣性 ─────────────────────────────────────────

def enforce_diversity(
    yaya_cards: list[dict],
    other_cards: list[dict],
    candidate_pool: list[dict],
    *,
    min_platforms: int | None = None,
) -> list[dict]:
    """
    P66.1 — 確保 5 卡至少 N 個不同平台。

    規則：
      - 只動 other_cards（一般卡），不動 yaya_cards（芽芽卡保留優先順序）
      - 若 unique_platforms(yaya + other) < min_platforms：
          找 other_cards 分數最低那張 → 替換為 candidate_pool 中「未出現平台 + 分數最高」者
          重複直到滿足 min_platforms 或候選池耗盡
      - 候選池無未出現平台 → 接受不滿足，log warning

    Args:
        yaya_cards: 芽芽卡（不動）
        other_cards: 一般卡（可換）
        candidate_pool: 一般卡的完整候選池（含已選中的，picker 已給好 picker metadata）
        min_platforms: 最少平台數（預設 config.DIVERSITY_MIN_PLATFORMS=3）

    Returns:
        替換後的 other_cards 列表（長度不變）
    """
    if min_platforms is None:
        min_platforms = _DIVERSITY_MIN

    if not other_cards:
        return other_cards

    selected_urls = {url_normalizer.normalize(c["post"].get("url", "#"))
                     for c in (yaya_cards + other_cards)}
    # 已被換出去的 URL 不再考慮（防止 A↔B 無限循環互換）
    swapped_out_urls: set[str] = set()

    other = list(other_cards)
    max_iterations = max(len(other) * 2, 4)  # 安全保險：迭代上限

    for _ in range(max_iterations):
        platforms = {_get_platform(c) for c in (yaya_cards + other) if _get_platform(c)}
        if len(platforms) >= min_platforms:
            return other

        # 找未出現平台中分數最高的候選
        replacement = None
        for cand in sorted(candidate_pool,
                           key=lambda c: c["picker"]["final_score"],
                           reverse=True):
            cand_url = url_normalizer.normalize(cand["post"].get("url", "#"))
            if cand_url in selected_urls or cand_url in swapped_out_urls:
                continue
            if _get_platform(cand) in platforms:
                continue
            replacement = cand
            break

        if replacement is None:
            logger.warning("enforce_diversity: 候選池無未出現平台，接受不滿足（current=%d, target=%d）",
                           len(platforms), min_platforms)
            return other

        # 替換 other 中分數最低那張
        lowest_idx = min(range(len(other)),
                         key=lambda i: other[i]["picker"]["final_score"])
        removed_url = url_normalizer.normalize(other[lowest_idx]["post"].get("url", "#"))
        selected_urls.discard(removed_url)
        swapped_out_urls.add(removed_url)  # 永久標記，不再選回
        replacement_url = url_normalizer.normalize(replacement["post"].get("url", "#"))
        selected_urls.add(replacement_url)
        logger.info("enforce_diversity: swap %s (%s) → %s (%s) for platform diversity",
                    removed_url, _get_platform(other[lowest_idx]),
                    replacement_url, _get_platform(replacement))
        other[lowest_idx] = replacement

    logger.warning("enforce_diversity: 達迭代上限 %d，回傳當前 other_cards", max_iterations)
    return other
