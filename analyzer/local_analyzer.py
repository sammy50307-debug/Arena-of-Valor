"""
Deterministic local baseline analyzer.

This module is intentionally rule-based and dependency-free. It is a fallback
for real source posts when the LLM path is unavailable; it does not pretend to
be a semantic LLM analysis.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

import config


ANALYSIS_SOURCE = "local_deterministic"

POSITIVE_TERMS = [
    "好用",
    "期待",
    "喜歡",
    "推薦",
    "穩",
    "加強",
    "增強",
    "爽",
    "佛",
    "讚",
    "精彩",
    "可愛",
    "回流",
    "高勝率",
    "大優勢",
    "保護",
    "護盾",
]

NEGATIVE_TERMS = [
    "爛",
    "弱",
    "糞",
    "抱怨",
    "削弱",
    "延遲",
    "卡頓",
    "卡",
    "掛機",
    "檢舉",
    "不平衡",
    "退坑",
    "問題",
    "難用",
    "崩",
    "失敗",
    "討厭",
    "ban",
]

KEYWORD_RULES: List[Tuple[str, List[str]]] = [
    ("平衡調整", ["平衡", "削弱", "加強", "增強", "調整", "改版", "buff", "nerf"]),
    ("造型內容", ["造型", "skin", "繪畫", "聯名", "櫻花", "美術"]),
    ("賽事", ["GCS", "職業聯賽", "比賽", "戰隊", "奪冠", "決賽", "社群盃"]),
    ("新手教學", ["教學", "指南", "新手", "入坑", "實測", "解析"]),
    ("遊戲體驗", ["延遲", "卡頓", "掛機", "檢舉", "問題", "退坑"]),
    ("版本活動", ["活動", "更新", "公告", "下載量", "回流", "預告"]),
]

EVENT_RULES: List[Tuple[str, str, List[str]]] = [
    ("平衡調整", "balance_update", ["平衡", "削弱", "加強", "增強", "調整", "改版"]),
    ("賽事話題", "esports", ["GCS", "職業聯賽", "比賽", "戰隊", "奪冠", "決賽", "社群盃"]),
    ("造型/聯名", "content_event", ["造型", "skin", "聯名", "繪畫"]),
    ("系統問題", "issue_report", ["延遲", "卡頓", "掛機", "檢舉", "問題", "崩"]),
    ("版本活動", "campaign", ["活動", "更新", "公告", "下載量", "回流", "預告"]),
]


def analyze_posts_locally(
    posts: Iterable[Any],
    hero_watchlist: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Return reporter-compatible local analysis entries for source posts."""
    heroes = _normalize_heroes(hero_watchlist)
    return [analyze_local_post(post, heroes) for post in posts]


def analyze_local_post(
    post: Any,
    hero_watchlist: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Analyze one source post using deterministic string rules."""
    heroes = _normalize_heroes(hero_watchlist)
    title = _text(_get(post, "title"))
    content = _text(_get(post, "content"))
    platform = _canonical_platform(_get(post, "platform", "web"))
    source = _text(_get(post, "source"))
    url = _text(_get(post, "url"))
    region = _text(_get(post, "region", "TW")) or "TW"
    timestamp = _text(_get(post, "timestamp") or _get(post, "published_date") or "時間未知")
    text = " ".join(part for part in [title, content] if part)

    detected_heroes = _detect_heroes(text, heroes, _get(post, "detected_heroes", []))
    positive_hits = _find_terms(text, POSITIVE_TERMS)
    negative_hits = _find_terms(text, NEGATIVE_TERMS)
    sentiment, sentiment_score = _score_sentiment(positive_hits, negative_hits)
    keywords = _build_keywords(text, detected_heroes)
    events = _detect_events(text)
    category = _category_from_keywords(keywords, events, detected_heroes)
    relevance_score = _score_relevance(post, detected_heroes, keywords, events, text)
    is_hero_focus = bool(detected_heroes)

    analysis = {
        "reasoning": "本地 deterministic baseline：依情緒詞、英雄名、事件詞與來源欄位做可追溯初判。",
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "region": region,
        "original_language": _detect_language(text),
        "translated_content": "",
        "category": category,
        "keywords": keywords,
        "summary": _build_summary(title, content),
        "relevance_score": relevance_score,
        "is_hero_focus": is_hero_focus,
        "detected_heroes": detected_heroes,
        "events": events,
        "analysis_source": ANALYSIS_SOURCE,
        "llm_contract": {
            "status": "skipped",
            "errors": ["local deterministic fallback"],
        },
    }

    return {
        "post": {
            "platform": platform,
            "author": source,
            "source": source,
            "url": url,
            "title": title,
            "content": content,
            "timestamp": timestamp,
            "is_hero_focus": is_hero_focus,
            "detected_heroes": detected_heroes,
            "region": region,
            "original_language": analysis["original_language"],
            "translated_content": "",
        },
        "analysis": analysis,
    }


def generate_local_summary(
    analyzed_posts: Iterable[Dict[str, Any]],
    date: str,
    hero_focus: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate local analyzed posts into reporter-compatible daily summary."""
    posts = list(analyzed_posts)
    hero_focus = hero_focus or getattr(config, "HERO_FOCUS_NAME", "芽芽")
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    keyword_counts: Counter = Counter()
    keyword_sentiments: Dict[str, Counter] = defaultdict(Counter)
    event_counts: Dict[Tuple[str, str], Dict[str, Any]] = {}
    hero_scores: Dict[str, List[float]] = defaultdict(list)
    hero_comments: Dict[str, List[str]] = defaultdict(list)
    positive_words: Counter = Counter()
    negative_words: Counter = Counter()

    for entry in posts:
        post = entry.get("post", {})
        analysis = entry.get("analysis", {})
        sentiment = analysis.get("sentiment", "neutral")
        if sentiment not in sentiment_distribution:
            sentiment = "neutral"
        score = _safe_float(analysis.get("sentiment_score"), 0.5)

        sentiment_distribution[sentiment] += 1

        for keyword in analysis.get("keywords", []) or []:
            key = _text(keyword)
            if not key:
                continue
            keyword_counts[key] += 1
            keyword_sentiments[key][sentiment] += 1
            if sentiment == "positive":
                positive_words[key] += 1
            elif sentiment == "negative":
                negative_words[key] += 1

        for event in analysis.get("events", []) or []:
            name = _text(event.get("name"))
            event_type = _text(event.get("type"))
            if not name or not event_type:
                continue
            event_key = (name, event_type)
            existing = event_counts.setdefault(
                event_key,
                {"name": name, "type": event_type, "source_count": 0, "details": event.get("details", "")},
            )
            existing["source_count"] += 1

        detected_heroes = post.get("detected_heroes") or analysis.get("detected_heroes") or []
        for hero in detected_heroes:
            hero_name = _text(hero)
            if not hero_name:
                continue
            hero_scores[hero_name].append(score)
            title = _text(post.get("title") or post.get("content"))
            if title:
                hero_comments[hero_name].append(_truncate(title, 48))

    platform_breakdown = compute_platform_breakdown(posts)

    hot_topics = []
    for keyword, count in keyword_counts.most_common(6):
        sentiment = _dominant_sentiment(keyword_sentiments[keyword])
        hot_topics.append(
            {
                "topic": keyword,
                "mention_count": int(count),
                "sentiment": sentiment,
                "description": "本地規則偵測到 %s 次相關討論。" % count,
            }
        )

    hero_stats = {}
    for hero, scores in sorted(hero_scores.items()):
        hero_stats[hero] = {
            "count": len(scores),
            "avg_sentiment": round(sum(scores) / len(scores), 3) if scores else 0.5,
            "wordcloud": {
                "positive": _counter_terms_for_hero(posts, hero, "positive"),
                "negative": _counter_terms_for_hero(posts, hero, "negative"),
            },
        }

    top_links = []
    link_candidates = sorted(
        [entry for entry in posts if _text(entry.get("post", {}).get("url")) and _text(entry.get("post", {}).get("url")) != "N/A"],
        key=lambda entry: _safe_float(entry.get("analysis", {}).get("relevance_score"), 0.0),
        reverse=True,
    )
    for entry in link_candidates[:3]:
        post = entry.get("post", {})
        title = _text(post.get("title") or post.get("content") or "來源貼文")
        top_links.append(
            {
                "title": _truncate(title, 36),
                "url": _text(post.get("url")),
                "platform": _canonical_platform(post.get("platform", "web")),
            }
        )

    avg_score = _average([_safe_float(entry.get("analysis", {}).get("sentiment_score"), 0.5) for entry in posts], 0.5)
    overview = "今日輿情共搜集到 %d 筆資料；LLM 不可用時由本地 deterministic baseline 產生可追溯初判。" % len(posts)
    focus_scores = hero_scores.get(hero_focus, [])
    focus_score = _average(focus_scores, avg_score)

    return {
        "overall": {
            "sentiment_score": round(avg_score, 3),
            "summary": overview,
            "trend": "Stable",
        },
        "reasoning": "P88 local deterministic baseline：統計真實來源貼文的情緒詞、英雄詞、事件詞與平台分佈。",
        "date": date,
        "overview": overview,
        "total_posts": len(posts),
        "sentiment_distribution": sentiment_distribution,
        "platform_breakdown": platform_breakdown,
        "global_insights": {
            "TW": {
                "summary": "本地 baseline 已完成台服來源聚合，語意深度待 LLM enrichment 補強。",
                "hot_hero": hero_focus if focus_scores else "無特定英雄",
            }
        },
        "hot_topics": hot_topics,
        "detected_events": list(event_counts.values()),
        "alerts": [],
        "hero_stats": hero_stats,
        "wordcloud": {
            "positive": [term for term, _count in positive_words.most_common(12)],
            "negative": [term for term, _count in negative_words.most_common(12)],
        },
        "top_links": top_links,
        "hero_focus": {
            "name": hero_focus,
            "summary": _hero_focus_summary(hero_focus, focus_scores),
            "sentiment_score": round(focus_score, 3),
            "top_comments": hero_comments.get(hero_focus, [])[:3],
        },
        "recommendation": "本日使用本地 deterministic baseline，適合做營運初判；需要語意深讀時交由後續 LLM enrichment 補強。",
        "analysis_source": ANALYSIS_SOURCE,
        "local_analysis_status": "ok",
        "llm_contract": {
            "status": "skipped",
            "errors": ["local deterministic summary"],
        },
    }


def compute_platform_breakdown(analyzed_posts: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """從真實貼文統計平台分布（篇數 + 平均情緒）。

    口徑：以 post.platform 經 _canonical_platform 正規化後計數。
    P108：LLM 版 platform_breakdown 只吐固定子集（ig/threads/fb）不可信，
    報告圖表與 dynamic_focus 今日焦點皆應改用本函式的真實統計。
    """
    platform_scores: Dict[str, List[float]] = defaultdict(list)
    for entry in analyzed_posts:
        post = entry.get("post", {})
        analysis = entry.get("analysis", {})
        platform = _canonical_platform(post.get("platform", "web"))
        score = _safe_float(analysis.get("sentiment_score"), 0.5)
        platform_scores[platform].append(score)
    return {
        platform: {
            "post_count": len(scores),
            "avg_sentiment": round(sum(scores) / len(scores), 3) if scores else 0.5,
        }
        for platform, scores in sorted(platform_scores.items())
    }


def has_local_deterministic_posts(analyzed_posts: Iterable[Dict[str, Any]]) -> bool:
    for entry in analyzed_posts:
        if entry.get("analysis", {}).get("analysis_source") == ANALYSIS_SOURCE:
            return True
    return False


def _get(post: Any, key: str, default: Any = "") -> Any:
    if isinstance(post, dict):
        return post.get(key, default)
    return getattr(post, key, default)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_heroes(hero_watchlist: Optional[Iterable[str]]) -> List[str]:
    source = hero_watchlist if hero_watchlist is not None else getattr(config, "HERO_WATCHLIST", [])
    heroes = [_text(hero) for hero in source if _text(hero)]
    focus = _text(getattr(config, "HERO_FOCUS_NAME", "芽芽"))
    if focus and focus not in heroes:
        heroes.insert(0, focus)
    return list(dict.fromkeys(heroes))


def _canonical_platform(platform: Any) -> str:
    value = _text(platform).lower() or "web"
    aliases = {
        "website": "web",
        "forum": "web",
        "fb": "facebook",
        "facebook": "facebook",
        "ig": "instagram",
        "instagram": "instagram",
        "thread": "threads",
        "threads": "threads",
        "ptt": "ptt",
        "dcard": "dcard",
        "youtube": "youtube",
    }
    return aliases.get(value, value)


def _detect_heroes(text: str, hero_watchlist: Iterable[str], existing: Any) -> List[str]:
    detected = []
    for hero in _listify(existing):
        hero_name = _text(hero)
        if hero_name:
            detected.append(hero_name)
    for hero in hero_watchlist:
        if hero and hero in text:
            detected.append(hero)
    return list(dict.fromkeys(detected))


def _find_terms(text: str, terms: Iterable[str]) -> List[str]:
    lower_text = text.lower()
    return [term for term in terms if term.lower() in lower_text]


def _score_sentiment(positive_hits: List[str], negative_hits: List[str]) -> Tuple[str, float]:
    delta = len(positive_hits) - len(negative_hits)
    if delta > 0:
        return "positive", round(min(0.92, 0.58 + min(delta, 4) * 0.08), 3)
    if delta < 0:
        return "negative", round(max(0.08, 0.42 - min(abs(delta), 4) * 0.08), 3)
    return "neutral", 0.5


def _build_keywords(text: str, detected_heroes: List[str]) -> List[str]:
    keywords = list(detected_heroes)
    for label, terms in KEYWORD_RULES:
        if _find_terms(text, terms):
            keywords.append(label)
    for term in POSITIVE_TERMS + NEGATIVE_TERMS:
        if term in text and term not in keywords:
            keywords.append(term)
    return list(dict.fromkeys(keywords))[:10]


def _detect_events(text: str) -> List[Dict[str, str]]:
    events = []
    for name, event_type, terms in EVENT_RULES:
        hits = _find_terms(text, terms)
        if not hits:
            continue
        events.append(
            {
                "name": name,
                "type": event_type,
                "details": "命中本地事件詞：%s" % "、".join(hits[:4]),
            }
        )
    return events


def _category_from_keywords(keywords: List[str], events: List[Dict[str, str]], detected_heroes: List[str]) -> str:
    if any(event.get("type") == "issue_report" for event in events):
        return "問題回報"
    if "平衡調整" in keywords:
        return "平衡更新"
    if "賽事" in keywords:
        return "賽事活動"
    if "造型內容" in keywords:
        return "造型內容"
    if detected_heroes:
        return "英雄討論"
    return "一般討論"


def _score_relevance(post: Any, detected_heroes: List[str], keywords: List[str], events: List[Dict[str, str]], text: str) -> float:
    base = _safe_float(_get(post, "score", 0.5), 0.5)
    score = 0.42 + min(max(base, 0.0), 1.0) * 0.22
    if detected_heroes:
        score += 0.16
    if events:
        score += 0.12
    if keywords:
        score += min(len(keywords), 5) * 0.025
    if len(text) > 80:
        score += 0.03
    return round(min(score, 0.98), 3)


def _build_summary(title: str, content: str) -> str:
    title = title or "無標題來源"
    preview = _truncate(content.replace("\n", " "), 96)
    if preview:
        return "本地基線：%s；%s" % (_truncate(title, 42), preview)
    return "本地基線：%s" % _truncate(title, 80)


def _detect_language(text: str) -> str:
    return "zh" if any("\u4e00" <= ch <= "\u9fff" for ch in text) else "en"


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _average(values: Iterable[float], default: float) -> float:
    values = list(values)
    if not values:
        return default
    return sum(values) / len(values)


def _dominant_sentiment(counter: Counter) -> str:
    if not counter:
        return "neutral"
    return counter.most_common(1)[0][0]


def _counter_terms_for_hero(posts: List[Dict[str, Any]], hero: str, sentiment: str) -> List[str]:
    counter: Counter = Counter()
    for entry in posts:
        post = entry.get("post", {})
        analysis = entry.get("analysis", {})
        heroes = post.get("detected_heroes") or analysis.get("detected_heroes") or []
        if hero not in heroes or analysis.get("sentiment") != sentiment:
            continue
        for keyword in analysis.get("keywords", []) or []:
            if keyword != hero:
                counter[_text(keyword)] += 1
    return [term for term, _count in counter.most_common(8) if term]


def _hero_focus_summary(hero_focus: str, focus_scores: List[float]) -> str:
    if focus_scores:
        return "%s 今日被本地 baseline 偵測到 %d 筆相關討論。" % (hero_focus, len(focus_scores))
    return "今日本地 baseline 未偵測到 %s 的明確討論。" % hero_focus


def _truncate(text: str, limit: int) -> str:
    text = _text(text)
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 0)] + "…"


def _listify(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
