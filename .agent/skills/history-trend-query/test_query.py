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


# ─────────────────────────────────────────────────────────────
# Test 9：R8 加權 vs 算術平均（造假 fixture）
# ─────────────────────────────────────────────────────────────
@test("T9 R8 加權平均：count=100 sent=0.3 與 count=1 sent=0.9 應加權為 ≈0.306")
def t9():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        def _make(date_str: str, hero_count: int, sentiment: float) -> None:
            payload = {
                "date": date_str,
                "total_posts": hero_count,
                "overall": {"sentiment_score": sentiment, "trend": "Stable"},
                "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
                "platform_breakdown": {},
                "hero_stats": {
                    "小明": {"count": hero_count, "avg_sentiment": sentiment}
                },
            }
            fname = f"analysis_{date_str.replace('-', '')}.json"
            (tmp_dir / fname).write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )

        _make("2030-06-01", hero_count=100, sentiment=0.3)
        _make("2030-06-02", hero_count=1, sentiment=0.9)

        q = HistoryTrendQuery(data_dir=tmp_dir)

        r_arith = q.hero_trend("小明", 2, until="2030-06-02", weighted=False)
        r_wt = q.hero_trend("小明", 2, until="2030-06-02", weighted=True)

    # 算術平均 = (0.3 + 0.9) / 2 = 0.6
    assert abs(r_arith["summary"]["avg_sentiment_mean"] - 0.6) < 1e-6, \
        f"arithmetic expected 0.6, got {r_arith['summary']['avg_sentiment_mean']}"
    assert r_arith["summary"]["avg_sentiment_mode"] == "arithmetic"

    # 加權平均 = (0.3*100 + 0.9*1) / 101 = 30.9/101 ≈ 0.30594
    expected_w = (0.3 * 100 + 0.9 * 1) / 101
    got_w = r_wt["summary"]["avg_sentiment_mean"]
    assert abs(got_w - expected_w) < 1e-6, f"weighted expected {expected_w}, got {got_w}"
    assert r_wt["summary"]["avg_sentiment_mode"] == "weighted"


# ─────────────────────────────────────────────────────────────
# Test 10：weighted=True 無資料 → None（不除零）
# ─────────────────────────────────────────────────────────────
@test("T10 weighted=True 全缺日 → avg_sentiment_mean=None，不觸發除零")
def t10():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)
    r = q.hero_trend("不存在XYZ", 3, until="2026-03-31", weighted=True)
    assert r["summary"]["avg_sentiment_mean"] is None
    assert r["summary"]["avg_sentiment_mode"] == "weighted"


# ─────────────────────────────────────────────────────────────
# S4 — T11~T16：多英雄 / 整體 / 平台 / raw / normalized / 上限
# ─────────────────────────────────────────────────────────────
def _make_overall_fixture(tmp_dir: Path) -> None:
    """造 3 日 overall 測試資料：聲量遞增、情緒分布變化。"""
    for ds, total, pos, neg, neu, plats in [
        ("2030-07-01", 10, 5, 2, 3, {"facebook": 6, "youtube": 4}),
        ("2030-07-02", 50, 30, 5, 15, {"facebook": 25, "youtube": 15, "ptt": 10}),
        ("2030-07-03", 100, 70, 10, 20, {"facebook": 50, "ptt": 30, "dcard": 20}),
    ]:
        payload = {
            "date": ds,
            "total_posts": total,
            "overall": {"sentiment_score": 0.7, "trend": "Upward"},
            "sentiment_distribution": {"positive": pos, "negative": neg, "neutral": neu},
            "platform_breakdown": {
                k: {"post_count": v, "sentiment_ratio": 0.5}
                for k, v in plats.items()
            },
            "hero_stats": {
                "甲": {"count": total // 2, "avg_sentiment": 0.6},
                "乙": {"count": total // 4, "avg_sentiment": 0.4},
            },
        }
        fname = f"analysis_{ds.replace('-', '')}.json"
        (tmp_dir / fname).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )


@test("T11 heroes_trend：多英雄回傳 list 長度=names、順序保留、跨軌 normalize")
def t11():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _make_overall_fixture(tmp_dir)
        q = HistoryTrendQuery(data_dir=tmp_dir)
        r = q.heroes_trend(["甲", "乙"], 3, until="2030-07-03")

    assert r["mode"] == "heroes"
    assert r["hero_names"] == ["甲", "乙"]
    assert len(r["heroes"]) == 2
    assert r["heroes"][0]["hero"] == "甲"
    assert r["heroes"][1]["hero"] == "乙"

    # normalized_count 跨英雄共軸：甲最高（07-03 count=50）→ 1.0；乙最低（07-01 count=2）
    all_norms = [
        p.get("normalized_count")
        for h in r["heroes"]
        for p in h["points"]
        if p.get("status") == "ok" and "normalized_count" in p
    ]
    assert max(all_norms) == 1.0, f"跨軌最高應為 1.0，got {max(all_norms)}"
    assert min(all_norms) == 0.0, f"跨軌最低應為 0.0，got {min(all_norms)}"


@test("T12 heroes_trend：raw=True 不產 normalized_count 欄")
def t12():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _make_overall_fixture(tmp_dir)
        q = HistoryTrendQuery(data_dir=tmp_dir)
        r = q.heroes_trend(["甲", "乙"], 3, until="2030-07-03", raw=True)

    assert r["raw"] is True
    for h in r["heroes"]:
        for p in h["points"]:
            assert "normalized_count" not in p, \
                f"raw=True 不應有 normalized_count，但 {h['hero']} 有"


@test("T13 heroes_trend：上限 5 軌、空 list / 重複 / 空字串 → ValueError")
def t13():
    q = HistoryTrendQuery(data_dir=PROJECT_DATA_DIR)

    # 6 個 → 噴
    try:
        q.heroes_trend(["a", "b", "c", "d", "e", "f"], 1, until="2026-04-05")
    except ValueError:
        pass
    else:
        raise AssertionError("6 軌應噴 ValueError")

    # 空 list → 噴
    try:
        q.heroes_trend([], 1)
    except ValueError:
        pass
    else:
        raise AssertionError("空 list 應噴 ValueError")

    # 重複 → 噴
    try:
        q.heroes_trend(["甲", "甲"], 1)
    except ValueError:
        pass
    else:
        raise AssertionError("重複名稱應噴 ValueError")

    # 空字串 → 噴
    try:
        q.heroes_trend(["甲", "  "], 1)
    except ValueError:
        pass
    else:
        raise AssertionError("空字串名稱應噴 ValueError")


@test("T14 overall_trend：三情緒欄齊全、缺日 missing")
def t14():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _make_overall_fixture(tmp_dir)
        q = HistoryTrendQuery(data_dir=tmp_dir)
        # 5 天區間（前後各蓋一天缺）：06-30 ~ 07-04
        r = q.overall_trend(5, until="2030-07-04")

    assert r["mode"] == "overall"
    assert len(r["points"]) == 5
    statuses = [p["status"] for p in r["points"]]
    # 06-30、07-04 缺；07-01~03 ok
    assert statuses[0] == "missing", f"06-30 應 missing，got {statuses[0]}"
    assert statuses[-1] == "missing", f"07-04 應 missing"
    assert statuses[1:4] == ["ok", "ok", "ok"]

    # 三情緒欄齊全
    p = r["points"][1]  # 07-01: pos=5, neg=2, neu=3
    assert p["positive"] == 5 and p["negative"] == 2 and p["neutral"] == 3
    assert p["total_posts"] == 10

    s = r["summary"]
    assert s["positive_sum"] == 5 + 30 + 70
    assert s["negative_sum"] == 2 + 5 + 10
    assert s["neutral_sum"] == 3 + 15 + 20
    assert s["total_posts_sum"] == 10 + 50 + 100

    # normalize：07-03 total=100 最高 → 1.0；07-01 total=10 最低 → 0.0
    assert r["points"][1]["normalized_total"] == 0.0
    assert r["points"][3]["normalized_total"] == 1.0


@test("T15 platform_trend：聯集平台、缺平台 absent、跨平台 normalize")
def t15():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _make_overall_fixture(tmp_dir)
        q = HistoryTrendQuery(data_dir=tmp_dir)
        r = q.platform_trend(3, until="2030-07-03")

    assert r["mode"] == "platform"
    # 聯集：facebook, youtube, ptt, dcard
    assert set(r["platforms"]) == {"facebook", "youtube", "ptt", "dcard"}, \
        f"got {r['platforms']}"

    # 07-03 沒 youtube → absent
    yt = r["platform_data"]["youtube"]
    assert yt[2]["status"] == "absent", f"07-03 youtube 應 absent，got {yt[2]['status']}"
    assert yt[2]["post_count"] == 0

    # 07-01 沒 dcard → absent
    dc = r["platform_data"]["dcard"]
    assert dc[0]["status"] == "absent"

    # 跨平台 normalize：facebook 07-03 post_count=50 是全局最大 → 1.0
    fb = r["platform_data"]["facebook"]
    assert fb[2]["normalized_count"] == 1.0, \
        f"facebook 07-03 應為 1.0（全局最大），got {fb[2].get('normalized_count')}"

    # 全局最小是 youtube 07-01 的 4 → 0.0
    yt2 = r["platform_data"]["youtube"]
    assert yt2[0]["normalized_count"] == 0.0, \
        f"youtube 07-01 應為 0.0（全局最小=4），got {yt2[0].get('normalized_count')}"


@test("T16 platform_trend / overall_trend：raw=True 不產 normalized_*")
def t16():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _make_overall_fixture(tmp_dir)
        q = HistoryTrendQuery(data_dir=tmp_dir)
        r_p = q.platform_trend(3, until="2030-07-03", raw=True)
        r_o = q.overall_trend(3, until="2030-07-03", raw=True)

    for pts in r_p["platform_data"].values():
        for p in pts:
            assert "normalized_count" not in p
    for p in r_o["points"]:
        assert "normalized_total" not in p


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 61 Stage 2/4 — HistoryTrendQuery 驗收測試")
    print("=" * 60)

    print("-" * 60)
    print(f"通過 {len(PASSED)} / {len(PASSED) + len(FAILED)}")
    if FAILED:
        print("失敗項：")
        for n, msg in FAILED:
            print(f"  - {n}: {msg}")
        sys.exit(1)
    print("S2 查詢核心測試全綠 ✅")
