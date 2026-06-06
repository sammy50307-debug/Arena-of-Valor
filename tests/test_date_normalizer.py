"""
P108.3 S1 單元測試 — scrapers/date_normalizer.normalize_published_date

驗證巴哈時間字串正規化成 ISO：
  - PoC 真實全集 37 種格式 100% 涵蓋（見 docs/P108.3_PLAN.md 附錄）
  - 相對時間以注入 now 為基準
  - MM-DD 無年份補年 + 跨年回退（+1 天容差）
  - 邊界：閏日、畸形輸入、空值 → graceful 回 None（呼叫端保留原值）
"""
import pytest
from datetime import datetime

from scrapers.date_normalizer import normalize_published_date

# 代表性「爬取當下」基準（與 PoC 一致；2026 非閏年）
NOW = datetime(2026, 6, 2, 23, 0, 0)


# ── ① ISO 完整（now 不影響）──
@pytest.mark.parametrize("raw,expected", [
    ("2025-12-26", "2025-12-26 00:00:00"),
    ("2023-05-16", "2023-05-16 00:00:00"),
    ("2026-06-02 22:39:00", "2026-06-02 22:39:00"),
    ("2026-06-02 22:39", "2026-06-02 22:39:00"),   # 無秒
])
def test_iso_full(raw, expected):
    assert normalize_published_date(raw, now=NOW) == expected


# ── ② 相對：N 小時前 ──
@pytest.mark.parametrize("raw,expected", [
    ("2 小時前", "2026-06-02 21:00:00"),
    ("10 小時前", "2026-06-02 13:00:00"),
    ("8 小時前", "2026-06-02 15:00:00"),
    ("11 小時前", "2026-06-02 12:00:00"),
])
def test_hours_ago(raw, expected):
    assert normalize_published_date(raw, now=NOW) == expected


# ── ③④ 昨天 / 前天 HH:MM ──
@pytest.mark.parametrize("raw,expected", [
    ("昨天 22:39", "2026-06-01 22:39:00"),
    ("昨天 22:19", "2026-06-01 22:19:00"),
    ("昨天 12:03", "2026-06-01 12:03:00"),
    ("前天 15:17", "2026-05-31 15:17:00"),
    ("前天 22:19", "2026-05-31 22:19:00"),
])
def test_relative_day(raw, expected):
    assert normalize_published_date(raw, now=NOW) == expected


# ── ⑤ MM-DD HH:MM 無年份 → 補當年 ──
@pytest.mark.parametrize("raw,expected", [
    ("05-29 11:39", "2026-05-29 11:39:00"),
    ("04-27 17:58", "2026-04-27 17:58:00"),
    ("01-07 07:50", "2026-01-07 07:50:00"),
    ("01-24 14:04", "2026-01-24 14:04:00"),
])
def test_mmdd_current_year(raw, expected):
    assert normalize_published_date(raw, now=NOW) == expected


# ── ⑤ 跨年回退：6 月遇到未來月份 → 去年 ──
def test_mmdd_cross_year_rollback():
    assert normalize_published_date("12-26 10:00", now=NOW) == "2025-12-26 10:00:00"
    assert normalize_published_date("11-15 08:00", now=NOW) == "2025-11-15 08:00:00"


# ── ⑤ 當日附近不誤判回退（+1 天容差，吸收爬取機時鐘微差）──
def test_mmdd_today_not_rollback():
    assert normalize_published_date("06-02 10:00", now=NOW) == "2026-06-02 10:00:00"
    assert normalize_published_date("06-03 10:00", now=NOW) == "2026-06-03 10:00:00"


# ── 同源防禦性格式（PoC 真實樣本未出現，但巴哈論壇同源相對格式）──
def test_minutes_and_days_ago_defensive():
    assert normalize_published_date("30 分鐘前", now=NOW) == "2026-06-02 22:30:00"
    assert normalize_published_date("3 天前", now=NOW) == "2026-05-30 23:00:00"


# ── 邊界：閏日在非閏年 → graceful 回 None（呼叫端保留原值，不崩）──
def test_leap_day_non_leap_year_graceful():
    assert normalize_published_date("02-29 10:00", now=NOW) is None


# ── 邊界：空值 / None / 畸形 → None ──
@pytest.mark.parametrize("raw", [
    None, "", "   ", "未知", "時間未知", "abc", "2026",
    "99-99 99:99", "13-45 10:00",
])
def test_malformed_returns_none(raw):
    assert normalize_published_date(raw, now=NOW) is None


# ── 涵蓋性回歸：PoC 真實去重全集 37 種（防回歸）──
_POC_REAL_FULL_SET = [
    # 20 種 MM-DD HH:MM
    "01-07 07:50", "01-24 14:04", "01-30 09:23", "02-07 14:10", "02-20 17:33",
    "03-21 09:36", "04-14 21:55", "04-22 10:02", "04-24 02:19", "04-24 19:56",
    "04-25 22:25", "04-27 17:58", "04-28 19:11", "05-05 22:19", "05-09 12:20",
    "05-12 22:30", "05-13 07:50", "05-13 17:56", "05-14 18:27", "05-29 11:39",
    # 4 種 N 小時前
    "10 小時前", "11 小時前", "2 小時前", "8 小時前",
    # 8 種 ISO 完整
    "2023-05-16", "2023-12-20", "2025-02-22", "2025-02-23", "2025-06-01",
    "2025-07-14", "2025-08-26", "2025-12-26",
    # 5 種 昨天 / 前天
    "昨天 12:03", "昨天 22:19", "昨天 22:39", "前天 15:17", "前天 22:19",
]


def test_poc_full_set_count():
    """前提檢查：全集確實 37 種（與 PoC 鐵證一致）。"""
    assert len(_POC_REAL_FULL_SET) == 37


def test_poc_full_set_coverage():
    """PoC 真實全集 37 種 100% 可正規化（非 None），防回歸。"""
    failed = [r for r in _POC_REAL_FULL_SET if normalize_published_date(r, now=NOW) is None]
    assert failed == [], f"未涵蓋格式: {failed}"
