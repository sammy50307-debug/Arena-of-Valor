"""
P67 — analyzer/keyword_stats.py 單元測試。

覆蓋：分詞基本流程、停用詞過濾、詞性過濾、文章覆蓋率去重、空語料、英雄別名注入。
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── jieba mock 工廠 ──────────────────────────────────────────────
def _make_jieba_mock(cut_pairs: list):
    """回傳一個模擬 jieba 模組，posseg.cut 回傳固定的 (word, flag) list。"""
    Word = types.SimpleNamespace
    mock_jieba = MagicMock()
    mock_jieba.posseg.cut.return_value = [Word(word=w, flag=f) for w, f in cut_pairs]
    return mock_jieba


# ── 測試輔助：patch _get_jieba + _load_stopwords + _load_custom_words ──
def _run(posts, cut_pairs, stopwords=None, custom_words=None, top_n=10):
    """執行 compute_hot_topics，並 mock 所有外部依賴。"""
    # 清除 lru_cache 狀態
    from analyzer import keyword_stats as ks
    ks._load_custom_words.cache_clear()
    ks._load_stopwords.cache_clear()

    mock_jieba = _make_jieba_mock(cut_pairs)

    with patch.object(ks, "_get_jieba", return_value=mock_jieba), \
         patch.object(ks, "_load_stopwords", return_value=frozenset(stopwords or [])), \
         patch.object(ks, "_load_custom_words", return_value=list(custom_words or [])):
        return ks.compute_hot_topics(posts, top_n=top_n)


# ── Case 1：基本分詞 + 覆蓋率統計 ──────────────────────────────────
def test_basic_coverage():
    posts = [
        {"url": "p1", "title": "芽芽加強", "content": ""},
        {"url": "p2", "title": "芽芽削弱", "content": ""},
        {"url": "p3", "title": "更新公告", "content": ""},
    ]
    # 每篇文章都回傳「芽芽(nr) 加強(v)」，p3 只有「更新(v)」
    def _cut_side_effect(text):
        Word = types.SimpleNamespace
        if "芽芽" in text:
            return [Word(word="芽芽", flag="nr"), Word(word="加強", flag="v")]
        return [Word(word="更新", flag="v")]

    from analyzer import keyword_stats as ks
    ks._load_custom_words.cache_clear()
    ks._load_stopwords.cache_clear()

    mock_jieba = MagicMock()
    mock_jieba.posseg.cut.side_effect = _cut_side_effect

    with patch.object(ks, "_get_jieba", return_value=mock_jieba), \
         patch.object(ks, "_load_stopwords", return_value=frozenset()), \
         patch.object(ks, "_load_custom_words", return_value=[]):
        topics, mapping = ks.compute_hot_topics(posts, top_n=10)

    words = {t["word"]: t["count"] for t in topics}
    assert words["芽芽"] == 2, "芽芽應出現在 2 篇文章"
    assert words["加強"] == 2
    assert words["更新"] == 1
    assert "芽芽" in mapping
    assert len(mapping["芽芽"]) == 2


# ── Case 2：停用詞過濾 ──────────────────────────────────────────────
def test_stopword_filter():
    posts = [{"url": "p1", "title": "星展活動", "content": ""}]
    cut_pairs = [("星展", "n"), ("活動", "n")]
    topics, _ = _run(posts, cut_pairs, stopwords=["星展"])
    words = {t["word"] for t in topics}
    assert "星展" not in words
    assert "活動" in words


# ── Case 3：詞性過濾（副詞/助詞不入榜）──────────────────────────────
def test_pos_filter():
    posts = [{"url": "p1", "title": "非常厲害", "content": ""}]
    # "非常" 是副詞 d，"厲害" 是形容詞 a — 兩者都不在 _POS_KEEP
    cut_pairs = [("非常", "d"), ("厲害", "a"), ("英雄", "n")]
    topics, _ = _run(posts, cut_pairs)
    words = {t["word"] for t in topics}
    assert "非常" not in words
    assert "厲害" not in words
    assert "英雄" in words


# ── Case 4：同篇同詞只算一次（文章覆蓋率去重）──────────────────────
def test_intra_post_dedup():
    """同一篇文章中「芽芽」出現兩次，覆蓋率只計 1 篇。"""
    posts = [{"url": "p1", "title": "芽芽 芽芽 超強", "content": ""}]
    cut_pairs = [("芽芽", "nr"), ("芽芽", "nr"), ("超強", "v")]
    topics, _ = _run(posts, cut_pairs)
    words = {t["word"]: t["count"] for t in topics}
    assert words.get("芽芽") == 1, "同篇重複出現應只算 1 篇"


# ── Case 5：空語料 ──────────────────────────────────────────────────
def test_empty_posts():
    topics, mapping = _run([], cut_pairs=[])
    assert topics == []
    assert mapping == {}


# ── Case 6：top_n 截斷 ──────────────────────────────────────────────
def test_top_n_truncation():
    posts = [{"url": f"p{i}", "title": f"英雄{i}", "content": ""} for i in range(20)]

    def _cut(text):
        Word = types.SimpleNamespace
        # 每篇回傳獨特詞 + "遊戲"（高頻詞）
        import re
        m = re.search(r"英雄(\d+)", text)
        idx = m.group(1) if m else "x"
        return [Word(word=f"英雄{idx}", flag="n"), Word(word="遊戲", flag="n")]

    from analyzer import keyword_stats as ks
    ks._load_custom_words.cache_clear()
    ks._load_stopwords.cache_clear()

    mock_jieba = MagicMock()
    mock_jieba.posseg.cut.side_effect = _cut

    with patch.object(ks, "_get_jieba", return_value=mock_jieba), \
         patch.object(ks, "_load_stopwords", return_value=frozenset()), \
         patch.object(ks, "_load_custom_words", return_value=[]):
        topics, _ = ks.compute_hot_topics(posts, top_n=5)

    assert len(topics) == 5
    # "遊戲" 覆蓋所有 20 篇，應排第 1
    assert topics[0]["word"] == "遊戲"
    assert topics[0]["count"] == 20


# ── Case 7：jieba ImportError → fallback 空列表 ────────────────────
def test_jieba_import_error_fallback():
    posts = [{"url": "p1", "title": "測試", "content": ""}]

    from analyzer import keyword_stats as ks
    ks._load_custom_words.cache_clear()
    ks._load_stopwords.cache_clear()

    with patch.object(ks, "_get_jieba", side_effect=ImportError("jieba not installed")):
        topics, mapping = ks.compute_hot_topics(posts)

    assert topics == []
    assert mapping == {}
