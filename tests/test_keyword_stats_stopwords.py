"""P108.1 熱詞治本測試：jieba 詞典納入多字詞 + 英文虛詞過濾。

jieba 缺失時 skip（不假過——否則 compute_hot_topics 回空列表會讓斷言 vacuously 通過）。
"""
from __future__ import annotations

import pytest

pytest.importorskip("jieba")

from analyzer.keyword_stats import compute_hot_topics


def _posts(title: str, n: int = 3):
    return [{"id": str(i), "title": title, "content": ""} for i in range(n)]


def test_multichar_platform_name_not_split_into_noise():
    """治本核心：「巴哈姆特」整詞切出後被 stopword 擋，不留切殘「巴哈姆」。"""
    rht, _ = compute_hot_topics(_posts("巴哈姆特論壇的芽芽攻略心得"))
    words = [r["word"] for r in rht]
    assert "巴哈姆" not in words
    assert "巴哈姆特" not in words


def test_english_function_words_excluded():
    rht, _ = compute_hot_topics(_posts("Arena of Valor the best game on it"))
    words = [r["word"] for r in rht]
    for stop in ["of", "the", "on", "it"]:
        assert stop not in words


def test_meaningful_words_survive():
    """治本不該誤殺有意義詞（芽芽焦點英雄 + 造型術語）。"""
    rht, _ = compute_hot_topics(_posts("芽芽新造型技能加強"))
    words = [r["word"] for r in rht]
    # 造型/技能 屬有意義熱詞，應保留（至少一個存活，證明沒過度過濾）
    assert any(w in words for w in ["造型", "技能", "芽芽", "加強"])
