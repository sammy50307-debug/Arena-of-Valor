from __future__ import annotations

from scrapers.tavily_searcher import SearchResult
from analyzer.source_selection import (
    REASON_DUPLICATE_SIGNATURE,
    REASON_DUPLICATE_URL,
    REASON_LOW_SIGNAL,
    REASON_TOPN_OVERFLOW,
    build_source_selection,
    merge_local_only_entries,
    validate_selection_snapshot,
)


def _post(title: str, content: str, url: str, platform: str = "dcard", score: float = 0.8) -> SearchResult:
    return SearchResult(
        title=title,
        content=content,
        url=url,
        platform=platform,
        source=platform,
        region="TW",
        score=score,
    )


def test_source_selection_exact_url_duplicate_stays_local_only():
    posts = [
        _post("芽芽改版討論", "護盾增強後排位很好用，討論串持續升溫。", "https://example.com/a?utm=1"),
        _post("芽芽改版討論 copy", "同一篇來源重複進來，不應再送 LLM 深讀。", "https://example.com/a?utm=2"),
    ]

    selection = build_source_selection(posts, max_llm_posts=5, budget_remaining=5, hero_focus="芽芽")

    assert len(selection.llm_posts) == 1
    assert len(selection.local_only_posts) == 1
    assert selection.snapshot["duplicate_posts"] == 1
    assert selection.snapshot["reason_counts"][REASON_DUPLICATE_URL] == 1
    assert validate_selection_snapshot(selection.snapshot) == (True, [])


def test_source_selection_near_duplicate_signature_stays_local_only():
    posts = [
        _post("芽芽輔助出裝解析", "這篇討論芽芽輔助出裝、護盾厚度與團戰站位，玩家反應正面。", "https://example.com/1"),
        _post("芽芽輔助出裝解析！", "這篇討論芽芽輔助出裝 護盾厚度 與團戰站位 玩家反應正面", "https://example.com/2"),
    ]

    selection = build_source_selection(posts, max_llm_posts=5, budget_remaining=5, hero_focus="芽芽")

    assert len(selection.llm_posts) == 1
    assert selection.snapshot["reason_counts"][REASON_DUPLICATE_SIGNATURE] == 1


def test_source_selection_preserves_platform_diversity_before_filling_cap():
    posts = [
        _post("Dcard 高分 1", "芽芽玩家討論護盾體感與排位勝率，內容完整可分析。", "https://dcard.tw/a", "dcard", 0.99),
        _post("Dcard 高分 2", "芽芽玩家討論輔助裝與團戰打法，內容完整可分析。", "https://dcard.tw/b", "dcard", 0.98),
        _post("巴哈低分", "巴哈玩家討論版本活動與芽芽搭配，內容完整可分析。", "https://forum.gamer.com.tw/c", "bahamut", 0.2),
    ]

    selection = build_source_selection(posts, max_llm_posts=2, budget_remaining=2, hero_focus="芽芽")
    platforms = {post.platform for post in selection.llm_posts}

    assert platforms == {"dcard", "bahamut"}
    assert selection.snapshot["reason_counts"][REASON_TOPN_OVERFLOW] == 1


def test_source_selection_respects_budget_aware_cap():
    contents = [
        "芽芽輔助裝測試，玩家討論護盾厚度與冷卻收益。",
        "新造型美術回饋，社群聚焦特效、語音與收藏價值。",
        "職業賽事戰術文章，分析保排站位與射手搭配。",
        "新手教學心得，整理遊走路線、視野控制與會戰進場。",
        "版本活動整理，討論登入獎勵、任務節奏與玩家回流。",
    ]
    posts = [
        _post(
            "芽芽討論 %s" % i,
            contents[i],
            "https://example.com/%s" % i,
            score=0.9 - i * 0.01,
        )
        for i in range(5)
    ]

    selection = build_source_selection(posts, max_llm_posts=5, budget_remaining=2, hero_focus="芽芽")

    assert len(selection.llm_posts) == 2
    assert len(selection.local_only_posts) == 3
    assert selection.snapshot["max_llm_items"] == 2


def test_source_selection_low_signal_post_does_not_consume_llm_call():
    posts = [
        _post("ok", "", "https://example.com/short", score=1.0),
        _post("芽芽完整討論", "護盾、團戰與排位玩家心得內容完整，可以進行深讀。", "https://example.com/full", score=0.5),
    ]

    selection = build_source_selection(posts, max_llm_posts=5, budget_remaining=5, hero_focus="芽芽")

    assert len(selection.llm_posts) == 1
    assert selection.local_only_posts[0].url == "https://example.com/short"
    assert selection.snapshot["reason_counts"][REASON_LOW_SIGNAL] == 1


def test_merge_local_only_entries_marks_mixed_without_dropping_posts():
    llm_entry = {"post": {"url": "https://example.com/llm"}, "analysis": {"summary": "llm"}}
    local_entry = {"post": {"url": "https://example.com/local"}, "analysis": {"summary": "local"}}

    result = merge_local_only_entries({"posts": [llm_entry], "contract_status": "ok"}, [local_entry])

    assert [entry["post"]["url"] for entry in result["posts"]] == [
        "https://example.com/llm",
        "https://example.com/local",
    ]
    assert result["analysis_source"] == "mixed"
    assert result["local_analysis_status"] == "ok"
