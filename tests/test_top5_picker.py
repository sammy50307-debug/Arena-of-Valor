"""
T1 單元測試 — top5_picker (P65-S2 / P66.1)
Exit Criteria: ≥ 29 cases 全綠（P65-S2 23 + P66.1 6+）
"""

import pytest
from datetime import datetime

from analyzer.top5_picker import (
    _extract_score,
    _compute_decay,
    _compute_boost,
    _compute_source_boost,
    _is_yaya_related,
    _is_blacklisted,
    _reset_blacklist_cache,
    pick_top5,
    enforce_diversity,
)
from analyzer.url_normalizer import normalize


# ────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────

def _make_post(
    url="https://example.com/article/1",
    score=0.8,
    timestamp="2026-05-03 10:00:00",
    hero_focus=False,
    title="測試標題",
    content="測試內文",
    region="TW",
    sentiment="neutral",
    relevance_score=None,
):
    analysis_score = relevance_score if relevance_score is not None else score
    return {
        "post": {
            "url": url,
            "title": title,
            "content": content,
            "timestamp": timestamp,
            "platform": "ptt",
            "region": region,
            "is_hero_focus": hero_focus,
            "detected_heroes": ["芽芽"] if hero_focus else [],
        },
        "analysis": {
            "sentiment": sentiment,
            "relevance_score": analysis_score,
            "summary": f"{title} 的摘要",
            "is_hero_focus": hero_focus,
        },
    }


NOW = datetime(2026, 5, 3, 12, 0, 0)
TODAY = "2026-05-03"


# ────────────────────────────────────────────────────────
# 1. _extract_score
# ────────────────────────────────────────────────────────

def test_extract_score_from_analysis():
    entry = _make_post(score=0.9, relevance_score=0.9)
    assert _extract_score(entry) == pytest.approx(0.9)


def test_extract_score_fallback_to_post_score():
    entry = {"post": {"score": 0.75}, "analysis": {}}
    assert _extract_score(entry) == pytest.approx(0.75)


def test_extract_score_default_when_missing():
    assert _extract_score({}) == pytest.approx(0.5)


# ────────────────────────────────────────────────────────
# 2. _compute_decay
# ────────────────────────────────────────────────────────

def test_decay_fresh_post():
    ts = "2026-05-03 11:00:00"
    d = _compute_decay(ts, now=NOW)
    assert d == pytest.approx(1.0 - 1.0 / 72, abs=0.01)


def test_decay_old_post_floored():
    ts = "2026-04-01 00:00:00"
    d = _compute_decay(ts, now=NOW)
    assert d == pytest.approx(0.3)


def test_decay_missing_timestamp():
    assert _compute_decay(None) == pytest.approx(0.3)


def test_decay_dateonly_format():
    ts = "2026-05-03"
    d = _compute_decay(ts, now=NOW)
    assert 0.3 <= d <= 1.0


# ────────────────────────────────────────────────────────
# 3. _compute_boost
# ────────────────────────────────────────────────────────

def test_boost_hero_focus_post():
    entry = _make_post(hero_focus=True)
    b = _compute_boost(entry, "芽芽")
    assert b == pytest.approx(1.2)


def test_boost_non_hero_post():
    entry = _make_post(hero_focus=False)
    b = _compute_boost(entry, "芽芽")
    assert b == pytest.approx(1.0)


def test_boost_hero_in_title():
    entry = _make_post(title="芽芽新造型來了", hero_focus=False)
    b = _compute_boost(entry, "芽芽")
    assert b == pytest.approx(1.2)


def test_boost_no_focus_hero():
    entry = _make_post(hero_focus=True)
    b = _compute_boost(entry, "")
    assert b == pytest.approx(1.0)


# ────────────────────────────────────────────────────────
# 4. pick_top5 — 核心邏輯
# ────────────────────────────────────────────────────────

def test_pick_top5_returns_top_n():
    posts = [_make_post(url=f"https://example.com/{i}", score=i * 0.1 + 0.1) for i in range(10)]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index={})
    assert len(cards) == 5


def test_pick_top5_sorted_by_final_score():
    posts = [_make_post(url=f"https://example.com/{i}", score=float(i) * 0.1 + 0.05) for i in range(7)]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index={})
    scores = [c["picker"]["final_score"] for c in cards]
    assert scores == sorted(scores, reverse=True)


def test_pick_top5_hero_post_ranked_higher():
    normal = _make_post(url="https://example.com/normal", score=0.7, hero_focus=False)
    yaya = _make_post(url="https://example.com/yaya", score=0.7, hero_focus=True)
    cards, _ = pick_top5([normal, yaya], hero_focus="芽芽", today=TODAY, now=NOW, history_index={}, top_n=2)
    assert cards[0]["post"]["url"] == "https://example.com/yaya"


def test_pick_top5_empty_input():
    cards, idx = pick_top5([], today=TODAY, now=NOW, history_index={})
    assert cards == []
    assert idx == {}


def test_pick_top5_fewer_than_5_posts():
    posts = [_make_post(url=f"https://example.com/{i}", score=0.5) for i in range(3)]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index={})
    assert len(cards) == 3


def test_pick_top5_dedup_marks_duplicate():
    url = "https://example.com/old-news"
    history = {normalize(url): {"first_seen": "2026-05-02"}}
    post = _make_post(url=url, score=0.9)
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index=history)
    assert cards[0]["picker"]["is_duplicate"] is True
    assert cards[0]["picker"]["dup_badge"] == "day1"


def test_pick_top5_bypass_dedup_ignores_history():
    url = "https://example.com/old-news"
    history = {normalize(url): {"first_seen": "2026-05-01"}}
    post = _make_post(url=url, score=0.9)
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index=history, bypass_dedup=True)
    assert cards[0]["picker"]["is_duplicate"] is False


def test_pick_top5_new_urls_recorded_in_index():
    post = _make_post(url="https://example.com/brand-new", score=0.8)
    _, updated_idx = pick_top5([post], today=TODAY, now=NOW, history_index={})
    assert normalize("https://example.com/brand-new") in updated_idx


def test_pick_top5_picker_metadata_present():
    post = _make_post()
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index={})
    picker = cards[0]["picker"]
    for key in ("final_score", "base_score", "decay", "boost", "is_duplicate", "dup_badge", "norm_url"):
        assert key in picker, f"missing picker key: {key}"


# ────────────────────────────────────────────────────────
# 5. url_normalizer
# ────────────────────────────────────────────────────────

def test_normalize_strips_utm():
    raw = "https://example.com/article?utm_source=fb&utm_medium=social&id=123"
    assert "utm_source" not in normalize(raw)
    assert "id=123" in normalize(raw)


def test_normalize_strips_trailing_slash():
    assert normalize("https://example.com/article/") == "https://example.com/article"


def test_normalize_empty_url():
    assert normalize("") == ""
    assert normalize("#") == "#"


# ────────────────────────────────────────────────────────
# 6. P66.1 — 黑名單過濾 + 芽芽豁免
# ────────────────────────────────────────────────────────

@pytest.fixture
def patched_blacklist(monkeypatch):
    """Patch _load_blacklist 為固定詞表，繞過 yaml 與 lru_cache。"""
    from analyzer import top5_picker as _picker
    _reset_blacklist_cache()  # 清掉舊 cache（test 之間隔離）
    monkeypatch.setattr(_picker, "_load_blacklist", lambda: ("星展", "貝殼幣"))
    yield
    # monkeypatch 自動還原；還原後再 clear 一次以保證下個 test 乾淨
    monkeypatch.undo()
    _reset_blacklist_cache()


def test_blacklist_filters_post_with_keyword_in_title(patched_blacklist):
    posts = [
        _make_post(url="https://example.com/a", title="星展銀行新活動", score=0.9),
        _make_post(url="https://example.com/b", title="正常文章", score=0.5),
    ]
    cards, _ = pick_top5(posts, hero_focus="芽芽", today=TODAY, now=NOW, history_index={})
    urls = [c["post"]["url"] for c in cards]
    assert "https://example.com/a" not in urls
    assert "https://example.com/b" in urls


def test_blacklist_filters_post_with_keyword_in_content(patched_blacklist):
    posts = [
        _make_post(url="https://example.com/c", title="標題", content="內文提到貝殼幣很有趣", score=0.9),
        _make_post(url="https://example.com/d", title="標題", content="正常內文", score=0.5),
    ]
    cards, _ = pick_top5(posts, hero_focus="芽芽", today=TODAY, now=NOW, history_index={})
    urls = [c["post"]["url"] for c in cards]
    assert "https://example.com/c" not in urls
    assert "https://example.com/d" in urls


def test_blacklist_yaya_exemption(patched_blacklist):
    """芽芽相關文章命中黑名單詞時仍保留（is_yaya_related 優先）。"""
    yaya_post = _make_post(
        url="https://example.com/yaya",
        title="芽芽推薦星展卡",  # 同時含黑名單詞 + 芽芽
        score=0.9,
        hero_focus=True,
    )
    cards, _ = pick_top5([yaya_post], hero_focus="芽芽", today=TODAY, now=NOW, history_index={})
    assert len(cards) == 1
    assert cards[0]["post"]["url"] == "https://example.com/yaya"


# ────────────────────────────────────────────────────────
# 7. P66.1 — Dcard source boost
# ────────────────────────────────────────────────────────

def test_source_boost_dcard():
    entry = _make_post()
    entry["post"]["platform"] = "dcard"
    assert _compute_source_boost(entry) == pytest.approx(1.05)


def test_source_boost_non_dcard():
    entry = _make_post()
    entry["post"]["platform"] = "ptt"
    assert _compute_source_boost(entry) == pytest.approx(1.0)


def test_dcard_boost_breaks_tie_in_pick_top5(patched_blacklist):
    """分數平手時 Dcard 文章排序高於非 Dcard。"""
    ptt_post = _make_post(url="https://ptt.cc/x", score=0.7, title="PTT 文")
    ptt_post["post"]["platform"] = "ptt"
    dcard_post = _make_post(url="https://dcard.tw/x", score=0.7, title="Dcard 文")
    dcard_post["post"]["platform"] = "dcard"
    cards, _ = pick_top5([ptt_post, dcard_post], hero_focus="芽芽",
                         today=TODAY, now=NOW, history_index={}, top_n=2)
    assert cards[0]["post"]["url"] == "https://dcard.tw/x"


# ────────────────────────────────────────────────────────
# 8. P66.1 — _is_yaya_related / _is_blacklisted helpers
# ────────────────────────────────────────────────────────

def test_is_yaya_related_by_title():
    entry = _make_post(title="芽芽新造型")
    assert _is_yaya_related(entry, "芽芽") is True


def test_is_yaya_related_by_is_hero_focus_flag():
    entry = _make_post(hero_focus=True)
    assert _is_yaya_related(entry, "芽芽") is True


def test_is_yaya_related_negative():
    entry = _make_post(title="一般文章", content="無關內文")
    assert _is_yaya_related(entry, "芽芽") is False


def test_is_blacklisted_hits():
    entry = _make_post(title="星展卡推薦")
    hit = _is_blacklisted(entry, ("星展", "貝殼幣"))
    assert hit == "星展"


def test_is_blacklisted_misses():
    entry = _make_post(title="正常標題", content="正常內文")
    assert _is_blacklisted(entry, ("星展", "貝殼幣")) is None


# ────────────────────────────────────────────────────────
# 9. P66.1 — enforce_diversity
# ────────────────────────────────────────────────────────

def _card(url: str, platform: str, score: float) -> dict:
    """簡化版 card factory（picker metadata 直接填）。"""
    return {
        "post": {"url": url, "platform": platform, "title": f"t-{url}"},
        "analysis": {},
        "picker": {
            "final_score": score,
            "base_score": score,
            "decay": 1.0,
            "boost": 1.0,
            "is_duplicate": False,
            "dup_badge": "",
            "norm_url": normalize(url),
        },
    }


def test_enforce_diversity_already_satisfied():
    """yaya + other 已 >= 3 平台 → 不動。"""
    yaya = [_card("https://a/1", "巴哈", 0.9)]
    other = [_card("https://b/1", "ptt", 0.8), _card("https://c/1", "dcard", 0.7)]
    pool = list(other)
    result = enforce_diversity(yaya, other, pool, min_platforms=3)
    assert [c["post"]["url"] for c in result] == [c["post"]["url"] for c in other]


def test_enforce_diversity_swap_for_third_platform():
    """only 2 platforms → 替換最低分為候選池中未出現平台的最高分。"""
    yaya = [_card("https://a/1", "巴哈", 0.9)]
    other = [
        _card("https://b/1", "ptt", 0.8),
        _card("https://b/2", "ptt", 0.6),
    ]
    pool = list(other) + [
        _card("https://d/1", "dcard", 0.5),  # 候選池有 dcard
    ]
    result = enforce_diversity(yaya, other, pool, min_platforms=3)
    platforms = {c["post"]["platform"] for c in (yaya + result)}
    assert "dcard" in platforms
    assert len(platforms) >= 3
    # 被換掉的應是最低分 (https://b/2)
    urls = [c["post"]["url"] for c in result]
    assert "https://b/2" not in urls
    assert "https://b/1" in urls


def test_enforce_diversity_pool_lacks_other_platforms():
    """候選池無未出現平台 → 接受不滿足，不報錯。"""
    yaya = [_card("https://a/1", "巴哈", 0.9)]
    other = [
        _card("https://b/1", "ptt", 0.8),
        _card("https://b/2", "ptt", 0.6),
    ]
    pool = list(other)  # 候選池只有 ptt，沒第三平台可換
    result = enforce_diversity(yaya, other, pool, min_platforms=3)
    # 應原樣返回
    assert [c["post"]["url"] for c in result] == [c["post"]["url"] for c in other]


def test_enforce_diversity_empty_other():
    """other_cards 為空 → 直接返回。"""
    yaya = [_card("https://a/1", "巴哈", 0.9)]
    result = enforce_diversity(yaya, [], [], min_platforms=3)
    assert result == []


def test_enforce_diversity_no_infinite_swap():
    """
    迴歸測試：實機 log 顯示 web↔youtube 無限互換。
    根因：candidate_pool 含 other_cards 自身，被換出的卡又被選回來。
    修補：swapped_out_urls 永久標記 + max_iterations 保險。
    """
    # yaya 平台 = web（與 other 重疊）
    yaya = [_card("https://gamer.com.tw/y", "web", 0.9)]
    # other 一張 web 一張 youtube，兩平台都已被 yaya/other 涵蓋
    other = [
        _card("https://gamer.com.tw/o1", "web", 0.7),
        _card("https://yt.com/o2", "youtube", 0.6),
    ]
    # 候選池只有 web/youtube，沒有第三平台
    pool = list(other) + [
        _card("https://gamer.com.tw/p1", "web", 0.5),
        _card("https://yt.com/p2", "youtube", 0.4),
    ]
    # 應該優雅退出（不滿足但不無限循環），且不超時
    result = enforce_diversity(yaya, other, pool, min_platforms=3)
    assert len(result) == 2  # 仍是 2 張一般卡


# ────────────────────────────────────────────────────────
# P70.1 — 去重懲罰 + 同平台排名衰減
# ────────────────────────────────────────────────────────

def test_dup_penalty_day1():
    """day1 重複文章 dup_factor=0.3。"""
    url = "https://example.com/dup-day1"
    history = {normalize(url): {"first_seen": TODAY}}
    post = _make_post(url=url, score=0.8)
    cards, _ = pick_top5([post], today=TODAY, now=NOW, history_index=history)
    assert cards[0]["picker"]["dup_factor"] == pytest.approx(0.3)
    assert cards[0]["picker"]["is_duplicate"] is True


def test_dup_penalty_gradient():
    """day7 懲罰 > day3 > day1（dup_factor 遞減）。"""
    urls = {
        "day1": "https://example.com/grad-d1",
        "day3": "https://example.com/grad-d3",
        "day7": "https://example.com/grad-d7",
    }
    history = {
        normalize(urls["day1"]): {"first_seen": "2026-05-02"},   # age=1 → day1
        normalize(urls["day3"]): {"first_seen": "2026-05-01"},   # age=2 → day3
        normalize(urls["day7"]): {"first_seen": "2026-04-26"},   # age=7 → day7
    }
    posts = [_make_post(url=u, score=0.8) for u in urls.values()]
    cards, _ = pick_top5(posts, today=TODAY, now=NOW, history_index=history, top_n=3)
    factors = {c["post"]["url"]: c["picker"]["dup_factor"] for c in cards}
    assert factors[urls["day1"]] == pytest.approx(0.3)
    assert factors[urls["day3"]] == pytest.approx(0.2)
    assert factors[urls["day7"]] == pytest.approx(0.1)
    assert factors[urls["day7"]] < factors[urls["day3"]] < factors[urls["day1"]]


def test_dup_yaya_bonus():
    """芽芽重複文章 dup_factor=1.5（加分而非懲罰）。"""
    url = "https://example.com/yaya-dup"
    history = {normalize(url): {"first_seen": TODAY}}
    post = _make_post(url=url, score=0.8, hero_focus=True)
    cards, _ = pick_top5([post], hero_focus="芽芽", today=TODAY, now=NOW, history_index=history)
    assert cards[0]["picker"]["dup_factor"] == pytest.approx(1.5)
    assert cards[0]["picker"]["is_duplicate"] is True


def test_platform_rank_decay_basic():
    """同平台 3 篇：排名越後 penalty 越大、final_score 越低。"""
    posts = [_make_post(url=f"https://example.com/ptt{i}", score=0.8) for i in range(3)]
    cards, _ = pick_top5(posts, hero_focus="芽芽", today=TODAY, now=NOW, history_index={}, top_n=3)
    ptt_cards = sorted(
        [c for c in cards if c["picker"].get("platform_rank") is not None],
        key=lambda c: c["picker"]["platform_rank"],
    )
    assert len(ptt_cards) >= 2
    assert ptt_cards[0]["picker"]["platform_penalty"] == pytest.approx(1.0)
    assert ptt_cards[1]["picker"]["platform_penalty"] == pytest.approx(0.9)
    assert ptt_cards[0]["picker"]["final_score"] > ptt_cards[1]["picker"]["final_score"]


def test_platform_rank_yaya_exempt():
    """芽芽文章不計入同平台排名計數，一般文章仍是第 1 篇（penalty=1.0）。"""
    yaya = _make_post(url="https://example.com/yaya-ptt", score=0.9, hero_focus=True)
    normal = _make_post(url="https://example.com/normal-ptt", score=0.8)
    cards, _ = pick_top5([yaya, normal], hero_focus="芽芽", today=TODAY, now=NOW, history_index={}, top_n=2)
    normal_card = next(c for c in cards if c["post"]["url"] == "https://example.com/normal-ptt")
    assert normal_card["picker"].get("platform_rank") == 1
    assert normal_card["picker"].get("platform_penalty") == pytest.approx(1.0)


def test_combined_dup_and_platform():
    """day1 重複 + 同平台第 2 篇：final_score 遠低於新鮮第 1 篇。"""
    url_dup = "https://example.com/dup-p2"
    url_fresh = "https://example.com/fresh-p1"
    history = {normalize(url_dup): {"first_seen": TODAY}}
    posts = [
        _make_post(url=url_fresh, score=0.8),
        _make_post(url=url_dup, score=0.8),
    ]
    cards, _ = pick_top5(posts, hero_focus="芽芽", today=TODAY, now=NOW, history_index=history, top_n=2)
    dup_card = next(c for c in cards if c["post"]["url"] == url_dup)
    fresh_card = next(c for c in cards if c["post"]["url"] == url_fresh)
    assert dup_card["picker"]["dup_factor"] == pytest.approx(0.3)
    assert dup_card["picker"].get("platform_rank") == 2
    assert dup_card["picker"]["final_score"] < fresh_card["picker"]["final_score"]
