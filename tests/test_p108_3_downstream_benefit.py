"""
P108.3 S3 下游受益確認 — 正規化後 picker decay / age / generator gate 對巴哈生效。

鎖住治本端到端效果（R-030）：巴哈相對格式經 date_normalizer 正規化後，
top5_picker._compute_decay 不再觸底 _DECAY_MIN、_is_too_old 對舊文生效，
generator._has_known_post_date 對巴哈值仍 True。防止未來改動回退治本效果。
"""
from datetime import datetime

from scrapers.date_normalizer import normalize_published_date
from analyzer.top5_picker import _compute_decay, _is_too_old, _DECAY_MIN
from reporter.generator import _has_known_post_date

NOW = datetime(2026, 6, 2, 23, 0, 0)


def test_decay_effective_after_normalization():
    """修前『昨天 22:39』decay 觸底 _DECAY_MIN；正規化後顯著 > _DECAY_MIN（R-030 治本生效）。"""
    raw = "昨天 22:39"
    decay_before = _compute_decay(raw, now=NOW)
    iso = normalize_published_date(raw, now=NOW)
    decay_after = _compute_decay(iso, now=NOW)
    assert decay_before == _DECAY_MIN            # 修前：picker 不認 → 觸底並列
    assert decay_after > _DECAY_MIN + 0.1        # 修後：差異化高值
    assert decay_after > decay_before


def test_fresh_post_higher_decay_than_older():
    """正規化後，越新的巴哈文 decay 越高（排序不再退化為純 score）。"""
    iso_2h = normalize_published_date("2 小時前", now=NOW)
    iso_yesterday = normalize_published_date("昨天 12:03", now=NOW)
    assert _compute_decay(iso_2h, now=NOW) > _compute_decay(iso_yesterday, now=NOW)


def test_age_filter_effective_after_normalization():
    """正規化後 age filter 對巴哈舊文生效：>14 天舊文判定過期、新文不過期。"""
    iso_old = normalize_published_date("01-24 14:04", now=NOW)   # 約 4 個月前
    assert _is_too_old(iso_old, max_age_days=14, now=NOW) is True
    iso_fresh = normalize_published_date("昨天 22:39", now=NOW)
    assert _is_too_old(iso_fresh, max_age_days=14, now=NOW) is False


def test_generator_gate_still_passes_for_bahamut():
    """generator _has_known_post_date 對正規化後巴哈值仍 True（受益：值更乾淨，不被誤擋）。"""
    iso = normalize_published_date("05-29 11:39", now=NOW)
    entry = {"post": {"published_date": iso}}
    assert _has_known_post_date(entry) is True
