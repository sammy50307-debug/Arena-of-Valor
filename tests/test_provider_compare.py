"""P105 S4 provider 對比 CLI 測試（mock，不真發 API）。

驗 load_posts（內建樣本/JSON/limit）與 format_comparison 並排結構 + X4-J 免責。
真實對比（燒額度）走手動指令：
    py -m analyzer.provider_compare --provider-a gemini --provider-b openrouter --limit 3
"""

import json

from analyzer.provider_compare import _SAMPLE_POSTS, format_comparison, load_posts
from scrapers.tavily_searcher import SearchResult


def test_load_posts_builtin_samples():
    posts = load_posts(None, None)
    assert len(posts) == len(_SAMPLE_POSTS) >= 3
    assert all(isinstance(p, SearchResult) for p in posts)


def test_load_posts_limit():
    assert len(load_posts(None, 1)) == 1


def test_load_posts_from_json(tmp_path):
    path = tmp_path / "posts.json"
    path.write_text(
        json.dumps(
            [{"title": "測試文章", "content": "內容", "url": "http://x", "platform": "PTT", "region": "TW"}]
        ),
        encoding="utf-8",
    )
    posts = load_posts(str(path), None)
    assert len(posts) == 1
    assert posts[0].title == "測試文章"
    assert posts[0].platform == "PTT"


def test_format_comparison_side_by_side():
    posts = [SearchResult(title="芽芽強", content="x", url="http://x")]
    res_a = {"posts": [{"analysis": {"sentiment": "positive", "sentiment_score": 0.9, "relevance_score": 0.8, "category": "戰術", "summary": "A 的分析"}}]}
    res_b = {"posts": [{"analysis": {"sentiment": "neutral", "sentiment_score": 0.5, "relevance_score": 0.6, "category": "一般", "summary": "B 的分析"}}]}
    out = format_comparison(posts, res_a, res_b, "gemini:default", "openrouter:deepseek/deepseek-chat")
    assert "芽芽強" in out
    assert "gemini:default" in out and "openrouter:deepseek/deepseek-chat" in out
    assert "positive" in out and "neutral" in out
    assert "人工判斷" in out  # X4-J 免責


def test_format_comparison_handles_missing_posts():
    """容錯：某 provider 回空 posts 不該爆。"""
    posts = [SearchResult(title="標題X", content="y", url="http://x")]
    out = format_comparison(posts, {"posts": []}, {"posts": []}, "a", "b")
    assert "標題X" in out
    assert "人工判斷" in out
