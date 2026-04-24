"""
Phase 61 Stage 2 查詢核心測試 — HistoryTrendQuery.hero_trend

驗收項：
1. 實資料單日查詢：芽芽 2026-04-05 → count=8, avg=0.92
2. 含缺日的區間：points 中缺日標 missing、不汙染 summary
3. 英雄不在 hero_stats → status='hero_absent'、count=0、不進 sentiment 平均
4. R5 合約：invalid 資料絕不進統計（造假 fixture 驗證）
5. 參數防呆：hero_name 空 / days<1 / days 非 int → ValueError
6. summary 統計正確：days_ok + days_missing + days_invalid + days_hero_absent == days_requested
7. coverage_ratio 計算正確
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from query import HistoryTrendQuery  # noqa: E402
from time_series_loader import TimeSeriesLoader  # noqa: E402


PROJECT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

PASSED: list[str] = []
FAILED: list[tuple[str, str]] = []


def test(name: str):
    def deco(fn):
        try:
            fn()
            PASSED.append(name)
            print(f"  [PASS] {name}")
        except AssertionError as e:
            FAILED.append((name, str(e)))
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            FAILED.append((name, f"{type(e).__name__}: {e}"))
            print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
        return fn
    return deco


# ─────────────────────────────────────────────────────────────
# Test 1：實資料單日查詢
# ─────────────────────────────────────────────────────────────
@test("T1 實資料單日 hero_trend('芽芽', 1, until='2026-04-05')")
def t1():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)
    r = q.hero_trend("芽芽", 1, until="2026-04-05")

    assert r["hero"] == "芽芽"
    assert r["days"] == 1
    assert r["range"]["start"] == "2026-04-05"
    assert r["range"]["end"] == "2026-04-05"
    assert len(r["points"]) == 1

    p = r["points"][0]
    assert p["status"] == "ok", f"expected ok, got {p['status']}"
    assert p["count"] == 8, f"count expected 8, got {p['count']}"
    assert abs(p["avg_sentiment"] - 0.92) < 1e-6

    s = r["summary"]
    assert s["days_ok"] == 1
    assert s["days_missing"] == 0
    assert s["total_count"] == 8
    assert abs(s["avg_sentiment_mean"] - 0.92) < 1e-6
    assert s["coverage_ratio"] == 1.0


# ─────────────────────────────────────────────────────────────
# Test 2：含缺日區間
# ─────────────────────────────────────────────────────────────
@test("T2 含缺日區間：芽芽 7 天 (03-30~04-05)，中間 5 日缺不汙染 summary")
def t2():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)
    r = q.hero_trend("芽芽", 7, until="2026-04-05")

    assert len(r["points"]) == 7

    status_counts: dict[str, int] = {}
    for p in r["points"]:
        status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1

    # 03-30 和 04-05 有實檔（是否英雄在是另一回事），中間 5 日缺
    assert status_counts.get("missing", 0) == 5, f"expected 5 missing, got {status_counts}"

    s = r["summary"]
    assert s["days_requested"] == 7
    assert s["days_missing"] == 5
    # days_ok + hero_absent == 2（兩天實檔）
    assert s["days_ok"] + s["days_hero_absent"] == 2


# ─────────────────────────────────────────────────────────────
# Test 3：英雄不在 hero_stats
# ─────────────────────────────────────────────────────────────
@test("T3 英雄不在 hero_stats → status='hero_absent'、count=0、不進 sentiment 平均")
def t3():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)
    # 04-05 的 hero_stats 只有「芽芽」，沒有「假英雄」
    r = q.hero_trend("不存在的英雄XYZ", 1, until="2026-04-05")

    p = r["points"][0]
    assert p["status"] == "hero_absent", f"got {p['status']}"
    assert p["count"] == 0
    assert p["avg_sentiment"] is None

    s = r["summary"]
    assert s["days_hero_absent"] == 1
    assert s["days_ok"] == 0
    assert s["total_count"] == 0
    assert s["avg_sentiment_mean"] is None  # 無資料點 → None 而非 0


# ─────────────────────────────────────────────────────────────
# Test 4：R5 合約 — invalid 資料絕不進統計
# ─────────────────────────────────────────────────────────────
@test("T4 R5 合約：invalid 資料即使 data 存在也不進 summary")
def t4():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # 故意造「schema 不合但 hero_stats 有內容」的壞資料
        bad = {
            "date": "2030-01-01",
            "total_posts": 99,
            # 缺 overall、sentiment_distribution、platform_breakdown（必要欄位）
            "hero_stats": {
                "測試英雄": {"count": 999, "avg_sentiment": 0.99}
            },
        }
        (tmp_dir / "analysis_20300101.json").write_text(
            json.dumps(bad, ensure_ascii=False), encoding="utf-8"
        )

        q = HistoryTrendQuery(data_dir=tmp_dir)
        r = q.hero_trend("測試英雄", 1, until="2030-01-01")

    p = r["points"][0]
    assert p["status"] == "invalid", f"expected invalid, got {p['status']}"
    assert p["count"] is None, "invalid 絕不回傳 count，即使 data 有"
    assert p["avg_sentiment"] is None

    s = r["summary"]
    assert s["days_invalid"] == 1
    assert s["days_ok"] == 0
    assert s["total_count"] == 0, f"invalid 的 count=999 絕不應加進 total，got {s['total_count']}"
    assert s["avg_sentiment_mean"] is None


# ─────────────────────────────────────────────────────────────
# Test 5：參數防呆
# ─────────────────────────────────────────────────────────────
@test("T5 參數防呆：空 hero_name / days<1 / days 非 int → ValueError")
def t5():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)

    for bad_hero in ["", "   "]:
        try:
            q.hero_trend(bad_hero, 1)
        except ValueError:
            pass
        else:
            raise AssertionError(f"hero_name={bad_hero!r} 應噴 ValueError")

    for bad_days in [0, -1]:
        try:
            q.hero_trend("芽芽", bad_days)
        except ValueError:
            pass
        else:
            raise AssertionError(f"days={bad_days} 應噴 ValueError")

    try:
        q.hero_trend("芽芽", 3.5)  # type: ignore[arg-type]
    except ValueError:
        pass
    else:
        raise AssertionError("days=3.5 應噴 ValueError（必須 int）")


# ─────────────────────────────────────────────────────────────
# Test 6：summary 加總恆等式
# ─────────────────────────────────────────────────────────────
@test("T6 summary 恆等式：ok+missing+invalid+hero_absent == days_requested")
def t6():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)
    for hero, days, until in [
        ("芽芽", 7, "2026-04-05"),
        ("不存在XYZ", 14, "2026-04-05"),
        ("芽芽", 3, "2026-04-05"),
    ]:
        r = q.hero_trend(hero, days, until=until)
        s = r["summary"]
        total = s["days_ok"] + s["days_missing"] + s["days_invalid"] + s["days_hero_absent"]
        assert total == s["days_requested"], (
            f"hero={hero}, days={days}, until={until} → "
            f"ok={s['days_ok']} + missing={s['days_missing']} + "
            f"invalid={s['days_invalid']} + absent={s['days_hero_absent']} = {total} "
            f"!= days_requested={s['days_requested']}"
        )


# ─────────────────────────────────────────────────────────────
# Test 7：coverage_ratio 計算
# ─────────────────────────────────────────────────────────────
@test("T7 coverage_ratio = days_ok / days_requested")
def t7():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)
    r = q.hero_trend("芽芽", 1, until="2026-04-05")
    assert r["summary"]["coverage_ratio"] == 1.0

    r = q.hero_trend("芽芽", 7, until="2026-04-05")
    # 04-05 有芽芽 ok=1，03-30 檔存在但未必含芽芽
    s = r["summary"]
    expected = s["days_ok"] / s["days_requested"]
    assert abs(s["coverage_ratio"] - expected) < 1e-9


# ─────────────────────────────────────────────────────────────
# Test 8：loader 與 data_dir 互斥
# ─────────────────────────────────────────────────────────────
@test("T8 loader 與 data_dir 同時指定 → ValueError")
def t8():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    try:
        HistoryTrendQuery(loader=loader, data_dir=PROJECT_DATA_DIR)
    except ValueError:
        return
    raise AssertionError("應噴 ValueError 但沒有")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 61 Stage 2 — HistoryTrendQuery.hero_trend 驗收測試")
    print("=" * 60)

    print("-" * 60)
    print(f"通過 {len(PASSED)} / {len(PASSED) + len(FAILED)}")
    if FAILED:
        print("失敗項：")
        for n, msg in FAILED:
            print(f"  - {n}: {msg}")
        sys.exit(1)
    print("S2 查詢核心測試全綠 ✅")
