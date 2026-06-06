"""
P108.4 — 無日期文差異化 decay + 時間欄位契約 guard。

S2：_is_parseable_time 單元 + picker 對無日期文差異化 decay（芽芽 0.6/無關 0.3）。
S4 契約 guard：picker 對「可解析時間 vs 無日期」的 decay 處理契約——
與 P108.3.1 的 sentiment 端到端契約（test_sentiment_published_date）共同守 P108.3/3.1/4 三修：
時間要嘛有效（走 _compute_decay）、要嘛無日期（走 NODATE_DECAY），不退化成全 _DECAY_MIN 並列。
"""
import pytest
from datetime import datetime

from analyzer.top5_picker import (
    _is_parseable_time, _parse_timestamp, _compute_decay, pick_top5,
    _NODATE_DECAY_YAYA, _NODATE_DECAY_OTHER, _DECAY_MIN,
)

NOW = datetime(2026, 6, 7, 12, 0, 0)
TODAY = "2026-06-07"


def _entry(timestamp, title="一般新聞", hero_focus=False, score=0.8, url=None):
    return {
        "post": {
            "url": url or f"https://example.com/{title}",
            "title": title, "content": "內容",
            "timestamp": timestamp, "platform": "web",
            "is_hero_focus": hero_focus,
            "detected_heroes": ["芽芽"] if hero_focus else [],
        },
        "analysis": {"relevance_score": score, "is_hero_focus": hero_focus},
    }


def _pick(entries):
    cards, _ = pick_top5(entries, hero_focus="芽芽", today=TODAY, now=NOW,
                         history_index={}, bypass_dedup=True, top_n=5, record_history=False)
    return cards


# ── S2：_is_parseable_time（單一來源解析）──
@pytest.mark.parametrize("ts,ok", [
    ("2026-06-01 22:39:00", True),
    ("2026-06-01", True),
    ("2026/06/01", True),
    ("時間未知", False),
    ("", False),
    (None, False),
    ("昨天 22:39", False),   # 相對格式 picker 不認（爬蟲端才正規化）
])
def test_is_parseable_time(ts, ok):
    assert _is_parseable_time(ts) is ok


def test_parse_timestamp_consistency_with_compute_decay():
    """契約：_parse_timestamp 與 _compute_decay 共用同一 _FMTS，可解析者 decay > _DECAY_MIN。"""
    assert _parse_timestamp("2026-06-07 11:00:00") is not None
    assert _compute_decay("2026-06-07 11:00:00", now=NOW) > _DECAY_MIN


# ── S2：無日期文差異化 decay ──
def test_nodate_yaya_decay_is_0_6():
    cards = _pick([_entry("時間未知", title="芽芽改版討論", hero_focus=True)])
    assert cards[0]["picker"]["decay"] == _NODATE_DECAY_YAYA == 0.6


def test_nodate_other_decay_is_0_3():
    cards = _pick([_entry("時間未知", title="一般新聞", hero_focus=False)])
    assert cards[0]["picker"]["decay"] == _NODATE_DECAY_OTHER == 0.3


def test_empty_and_none_timestamp_also_nodate_decay():
    """空/None timestamp 也走 NODATE（非 magic string 限定）。"""
    cards = _pick([_entry("", title="空日期文", hero_focus=False)])
    assert cards[0]["picker"]["decay"] == _NODATE_DECAY_OTHER


# ── S2：無日期文不壓過真實當天新文（核心 M2 質疑 #2）──
def test_nodate_does_not_beat_real_fresh_post():
    fresh = _entry("2026-06-07 10:00:00", title="真實當天文", hero_focus=False, url="https://e.com/fresh")
    nodate = _entry("時間未知", title="無日期文", hero_focus=False, url="https://e.com/nodate")
    cards = _pick([nodate, fresh])
    assert cards[0]["post"]["title"] == "真實當天文"
    assert cards[0]["picker"]["decay"] > cards[1]["picker"]["decay"]


# ── S4 契約 guard：可解析 vs 無日期 decay 處理對應（守三修）──
def test_time_handling_contract():
    """契約不變式：可解析時間→_compute_decay；無日期→NODATE_DECAY。防整條時間鏈退化。"""
    entries = [
        _entry("2026-06-06 12:00:00", title="有效時間文", hero_focus=False, url="https://e.com/valid"),
        _entry("時間未知", title="無日期文", hero_focus=False, url="https://e.com/nd"),
    ]
    cards = _pick(entries)
    by_title = {c["post"]["title"]: c["picker"]["decay"] for c in cards}
    # 有效時間：decay 來自 _compute_decay（非 NODATE 常數）
    assert by_title["有效時間文"] == round(_compute_decay("2026-06-06 12:00:00", now=NOW), 4)
    assert by_title["有效時間文"] > _NODATE_DECAY_OTHER
    # 無日期：decay = NODATE_OTHER（不退化成與有效文並列、也非 _DECAY_MIN 巧合）
    assert by_title["無日期文"] == _NODATE_DECAY_OTHER


def test_nodate_yaya_outranks_nodate_other():
    """同為無日期，芽芽相關（0.6）排在無關（0.3）前——呼應芽芽優先。"""
    yaya = _entry("時間未知", title="芽芽攻略", hero_focus=True, url="https://e.com/y")
    other = _entry("時間未知", title="路人閒聊", hero_focus=False, url="https://e.com/o")
    cards = _pick([other, yaya])
    assert cards[0]["post"]["title"] == "芽芽攻略"
