"""
P67 — 真實熱詞統計模組。

使用 jieba + 自訂詞庫，對當日所有抓取文章進行分詞，
統計詞彙的「文章覆蓋率」（同篇文章同詞出現多次只算 1 次），
回傳 real_hot_topics 列表及 topic_to_posts mapping 供 side panel 使用。
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_HERO_WHITELIST = _ROOT / ".agent/skills/hallucination-judge/resources/hero_whitelist.json"
_AOV_TERMS = _ROOT / "configs/aov_terms.yaml"
_BLACKLIST = _ROOT / "configs/personal_blacklist.yaml"

# jieba posseg 詞性白名單前綴（名詞 + 動詞）
_POS_KEEP = {"n", "v", "nr", "ns", "nt", "nz", "vn", "eng"}


@lru_cache(maxsize=1)
def _load_custom_words() -> List[str]:
    """載入英雄名 + AOV 術語詞庫（lru_cache 避免重複 I/O）。"""
    words: List[str] = []
    try:
        data = json.loads(_HERO_WHITELIST.read_text(encoding="utf-8"))
        words.extend(data.get("all_names", []))
        words.extend(data.get("heroes", {}).get("english_aliases", []))
    except Exception as e:
        logger.warning("hero_whitelist 載入失敗：%s", e)
    try:
        terms_data = yaml.safe_load(_AOV_TERMS.read_text(encoding="utf-8"))
        words.extend(terms_data.get("terms", []))
    except Exception as e:
        logger.warning("aov_terms 載入失敗：%s", e)
    return words


@lru_cache(maxsize=1)
def _load_stopwords() -> frozenset:
    """從 personal_blacklist.yaml 載入停用詞。"""
    try:
        data = yaml.safe_load(_BLACKLIST.read_text(encoding="utf-8"))
        return frozenset(data.get("blacklist", []))
    except Exception as e:
        logger.warning("personal_blacklist 載入失敗：%s", e)
        return frozenset()


def _get_jieba():
    """初始化 jieba 並注入自訂詞庫，回傳 jieba 模組。

    每次呼叫都重用同一個已初始化的模組（jieba 本身是 module-level singleton）。
    自訂詞因 _load_custom_words 有 lru_cache，不會重複寫入。
    """
    import jieba
    import jieba.posseg  # noqa: F401 — 確保 posseg 子模組已載入
    for word in _load_custom_words():
        jieba.add_word(word)
    return jieba


def compute_hot_topics(
    posts: List[dict],
    top_n: int = 10,
    min_word_len: int = 2,
) -> Tuple[List[dict], Dict[str, List[str]]]:
    """
    對文章列表進行分詞，回傳熱詞排行及 topic→post_ids mapping。

    文章覆蓋率口徑：同篇文章同詞出現多次只算 1 次（用 set 去重）。

    Args:
        posts: List of post dicts，包含 "id"/"url"、"title"、"content" 欄位
        top_n: 回傳前 N 名熱詞
        min_word_len: 詞長下限（過濾單字垃圾詞）

    Returns:
        (real_hot_topics, topic_to_posts)
        real_hot_topics: [{"word": "...", "count": N}, ...]
        topic_to_posts:  {"word": ["post_id_1", ...], ...}
    """
    try:
        jieba = _get_jieba()
    except ImportError:
        # jieba 未安裝時 fallback 空列表，不中斷整個報告流程
        logger.warning("jieba 未安裝，keyword_stats 降級為空列表")
        return [], {}
    except Exception as e:
        logger.warning("jieba 初始化失敗（%s），keyword_stats 降級", e)
        return [], {}

    stopwords = _load_stopwords()
    word_post_map: Dict[str, set] = {}

    for post in posts:
        post_id = str(post.get("id") or post.get("url") or id(post))
        text = " ".join(filter(None, [
            post.get("title", "") or "",
            post.get("content", "") or "",
        ]))
        if not text.strip():
            continue

        seen_in_post: set = set()
        for pair in jieba.posseg.cut(text):
            word, flag = pair.word, pair.flag
            if not any(flag.startswith(p) for p in _POS_KEEP):
                continue
            if len(word) < min_word_len:
                continue
            if word in stopwords:
                continue
            if word.isdigit():
                continue
            if word in seen_in_post:
                continue
            seen_in_post.add(word)
            word_post_map.setdefault(word, set()).add(post_id)

    sorted_words = sorted(word_post_map.items(), key=lambda x: len(x[1]), reverse=True)

    real_hot_topics = [
        {"word": w, "count": len(post_ids)}
        for w, post_ids in sorted_words[:top_n]
    ]
    topic_to_posts = {
        w: list(post_ids)
        for w, post_ids in sorted_words[:top_n]
    }

    logger.info("keyword_stats: %d posts → %d unique words (top %d returned)", len(posts), len(word_post_map), top_n)
    return real_hot_topics, topic_to_posts
