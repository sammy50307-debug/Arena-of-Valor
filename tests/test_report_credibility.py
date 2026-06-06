"""P108 報告數據可信度測試：真實平台統計 + advisory checker。"""
from __future__ import annotations

from analyzer.local_analyzer import compute_platform_breakdown
from scripts.check_report_credibility import check_report_credibility


def _entry(platform: str, score: float = 0.7):
    return {"post": {"platform": platform}, "analysis": {"sentiment_score": score}}


# ── compute_platform_breakdown ──────────────────────────────

def test_platform_breakdown_counts_real_platforms():
    posts = [_entry("bahamut"), _entry("bahamut"), _entry("youtube"), _entry("instagram")]
    pb = compute_platform_breakdown(posts)
    assert pb["bahamut"]["post_count"] == 2
    assert pb["youtube"]["post_count"] == 1
    assert pb["instagram"]["post_count"] == 1


def test_platform_breakdown_no_hallucinated_platforms():
    """只統計真實出現的平台，不憑空生出 facebook/threads。"""
    posts = [_entry("bahamut") for _ in range(5)]
    pb = compute_platform_breakdown(posts)
    assert set(pb.keys()) == {"bahamut"}
    assert "facebook" not in pb


def test_platform_breakdown_canonicalizes_aliases():
    posts = [_entry("fb"), _entry("ig"), _entry("FB")]
    pb = compute_platform_breakdown(posts)
    assert pb["facebook"]["post_count"] == 2
    assert pb["instagram"]["post_count"] == 1


def test_platform_breakdown_empty_input():
    assert compute_platform_breakdown([]) == {}


# ── check_report_credibility (advisory) ──────────────────────

def test_checker_flags_empty_hot_topics():
    summary = {"real_hot_topics": [], "platform_breakdown": {"bahamut": {"post_count": 3}}}
    warnings = check_report_credibility(summary)
    assert any("real_hot_topics" in w for w in warnings)


def test_checker_flags_missing_platform():
    """platform_breakdown 漏掉真實平台時警告（LLM 幻覺子集回潮）。"""
    summary = {
        "real_hot_topics": [{"word": "芽芽", "count": 3}],
        "platform_breakdown": {"facebook": {"post_count": 2}},
    }
    posts = [_entry("bahamut"), _entry("bahamut")]
    warnings = check_report_credibility(summary, posts)
    assert any("bahamut" in w for w in warnings)


def test_checker_passes_clean_report():
    summary = {
        "real_hot_topics": [{"word": "芽芽", "count": 3}],
        "platform_breakdown": {"bahamut": {"post_count": 2}, "youtube": {"post_count": 1}},
    }
    posts = [_entry("bahamut"), _entry("bahamut"), _entry("youtube")]
    assert check_report_credibility(summary, posts) == []


def test_checker_does_not_raise_on_missing_keys():
    """advisory 韌性：缺欄位也不爆，回報警告即可。"""
    assert check_report_credibility({}) != []  # 兩項都缺 → 有警告但不 raise
