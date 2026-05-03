"""
Phase 61 Stage 1 地基測試 — TimeSeriesLoader

驗收項：
1. 真實資料載入：analysis_20260405.json 可正確 parse + validate
2. 缺日偵測：指定範圍含不存在日期 → 回 status='missing' + warning log
3. Schema contract：壞資料缺必要欄位 → status='invalid' + missing_fields 列出
4. 區間掃描：load_range 回傳長度等於區間天數（含缺日 placeholder）
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from time_series_loader import TimeSeriesLoader, logger as loader_logger  # noqa: E402


PROJECT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

PASSED: list[str] = []
FAILED: list[tuple[str, str]] = []


def _capture_warnings():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.WARNING)
    loader_logger.addHandler(handler)
    return stream, handler


def _release_warnings(handler):
    loader_logger.removeHandler(handler)


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
# Test 1：真實資料載入
# ─────────────────────────────────────────────────────────────
@test("T1 真實資料載入 analysis_20260405.json")
def t1():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    entry = loader.load_day("2026-04-05")
    assert entry["status"] == "ok", f"expected ok, got {entry['status']}"
    assert entry["data"] is not None, "data 應存在"
    assert entry["data"]["total_posts"] == 12, "total_posts 應為 12"
    assert "芽芽" in entry["data"]["hero_stats"], "hero_stats 應含芽芽"


# ─────────────────────────────────────────────────────────────
# Test 2：缺日偵測 + warning
# ─────────────────────────────────────────────────────────────
@test("T2 缺日偵測 (未來日期不存在 → status='missing' + warning)")
def t2():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    stream, handler = _capture_warnings()
    try:
        entry = loader.load_day("2099-12-31")
    finally:
        _release_warnings(handler)

    assert entry["status"] == "missing", f"expected missing, got {entry['status']}"
    assert entry["data"] is None, "缺日 data 應為 None"
    assert entry["reason"] == "file_not_found"
    log_text = stream.getvalue()
    assert "缺日資料" in log_text, f"應有缺日 warning，實際 log=「{log_text}」"


# ─────────────────────────────────────────────────────────────
# Test 3：Schema contract 驗證 (壞資料)
# ─────────────────────────────────────────────────────────────
@test("T3 Schema contract：缺必要欄位 → status='invalid' + missing_fields")
def t3():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        bad_payload = {
            "date": "2030-01-01",
            "total_posts": 5,
            # 故意缺 overall / sentiment_distribution / platform_breakdown / hero_stats
        }
        (tmp_dir / "analysis_20300101.json").write_text(
            json.dumps(bad_payload, ensure_ascii=False),
            encoding="utf-8",
        )

        loader = TimeSeriesLoader(data_dir=tmp_dir)
        entry = loader.load_day("2030-01-01")

    assert entry["status"] == "invalid", f"expected invalid, got {entry['status']}"
    assert entry["reason"] == "schema_mismatch"
    missing = entry["missing_fields"]
    for key in ["overall", "sentiment_distribution", "platform_breakdown", "hero_stats"]:
        assert key in missing, f"missing_fields 應含 {key}，實際 {missing}"


# ─────────────────────────────────────────────────────────────
# Test 4：load_range 含缺日 placeholder
# ─────────────────────────────────────────────────────────────
@test("T4 load_range：7 天區間含缺日，長度=7、缺日標 missing")
def t4():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    series = loader.load_range("2026-03-30", "2026-04-05")
    assert len(series) == 7, f"expected 7 天，got {len(series)}"

    by_date = {s["date"]: s["status"] for s in series}
    assert by_date["2026-03-30"] == "ok", "03/30 實檔應 ok"
    assert by_date["2026-04-05"] == "ok", "04/05 實檔應 ok"
    # 03/31~04/04 無檔，皆應 missing
    for d in ["2026-03-31", "2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04"]:
        assert by_date[d] == "missing", f"{d} 應 missing，實際 {by_date[d]}"


# ─────────────────────────────────────────────────────────────
# Test 5：validate() 單元測試 (好資料)
# ─────────────────────────────────────────────────────────────
@test("T5 validate() 好資料 → (True, [])")
def t5():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    good = {
        "date": "2026-01-01",
        "total_posts": 10,
        "overall": {"sentiment_score": 0.5, "trend": "Stable"},
        "sentiment_distribution": {"positive": 5, "negative": 2, "neutral": 3},
        "platform_breakdown": {},
        "hero_stats": {},
    }
    ok, missing = loader.validate(good)
    assert ok is True, f"好資料應 valid，實際 missing={missing}"
    assert missing == []


# ─────────────────────────────────────────────────────────────
# Test 6：load_last_n_days
# ─────────────────────────────────────────────────────────────
@test("T6 load_last_n_days(3, until='2026-04-05') → 3 天")
def t6():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    series = loader.load_last_n_days(3, until="2026-04-05")
    assert len(series) == 3
    dates = [s["date"] for s in series]
    assert dates == ["2026-04-03", "2026-04-04", "2026-04-05"], f"got {dates}"


# ─────────────────────────────────────────────────────────────
# Test 7：區間反序應報錯
# ─────────────────────────────────────────────────────────────
@test("T7 start > end 應報 ValueError")
def t7():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR)
    try:
        loader.load_range("2026-04-05", "2026-04-01")
    except ValueError:
        return
    raise AssertionError("應噴 ValueError 但沒有")


# ─────────────────────────────────────────────────────────────
# S5 F1 — T8~T10：LRU cache 行為
# ─────────────────────────────────────────────────────────────
@test("T8 load_range cache 命中：同區間第二次呼叫不重掃磁碟")
def t8():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR, cache_size=8)
    s1 = loader.load_range("2026-04-03", "2026-04-05")
    stat1 = loader.cache_stats()
    assert stat1["misses"] == 1 and stat1["hits"] == 0, f"first call → 1 miss / 0 hit, got {stat1}"
    assert stat1["size"] == 1

    s2 = loader.load_range("2026-04-03", "2026-04-05")
    stat2 = loader.cache_stats()
    assert stat2["hits"] == 1 and stat2["misses"] == 1, f"second call → +1 hit, got {stat2}"
    # R23: deepcopy 回傳，s1 is not s2，但資料內容相等
    assert s1 == s2, "cache 命中應回傳相同內容（deepcopy，非同一物件）"
    assert s1 is not s2, "R23: 應回新 copy 防止 caller 污染 cache"


@test("T9 clear_cache 清空 + 不同區間獨立計入")
def t9():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR, cache_size=8)
    loader.load_range("2026-04-03", "2026-04-05")
    loader.load_range("2026-04-04", "2026-04-05")  # 不同 key
    assert loader.cache_stats()["size"] == 2
    assert loader.cache_stats()["misses"] == 2

    loader.clear_cache()
    assert loader.cache_stats() == {"size": 0, "max_size": 8, "hits": 0, "misses": 0}

    # 清空後再呼叫應 miss
    loader.load_range("2026-04-03", "2026-04-05")
    assert loader.cache_stats()["misses"] == 1


@test("T10 cache_size 上限：超出時 LRU 淘汰最舊")
def t10():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR, cache_size=2)
    loader.load_range("2026-04-03", "2026-04-03")  # k1
    loader.load_range("2026-04-04", "2026-04-04")  # k2
    loader.load_range("2026-04-05", "2026-04-05")  # k3 → 應淘汰 k1
    stat = loader.cache_stats()
    assert stat["size"] == 2, f"size 應卡 2，got {stat}"
    # k1 已淘汰：再呼叫應 miss（misses 從 3 → 4）
    misses_before = stat["misses"]
    loader.load_range("2026-04-03", "2026-04-03")
    assert loader.cache_stats()["misses"] == misses_before + 1, "k1 應已被淘汰、再次呼叫 miss"


# ─────────────────────────────────────────────────────────────
# P61.1 — T11~T13：R20/R23/R24 修補驗收
# ─────────────────────────────────────────────────────────────
@test("T11 R23: cache 回傳 deepcopy，caller 修改不污染 cache")
def t11():
    loader = TimeSeriesLoader(data_dir=PROJECT_DATA_DIR, cache_size=8)
    s1 = loader.load_range("2026-04-03", "2026-04-05")
    # 修改 caller 取得的 list（新增元素、修改 dict field）
    s1.append({"date": "INJECTED", "status": "ok"})
    s1[0]["status"] = "CORRUPTED"
    # 再次取得（cache hit）應還是原始資料
    s2 = loader.load_range("2026-04-03", "2026-04-05")
    assert loader.cache_stats()["hits"] == 1
    assert all(r.get("status") != "CORRUPTED" for r in s2), "cache 被 caller 污染"
    assert not any(r.get("date") == "INJECTED" for r in s2), "cache 被 caller append 污染"


@test("T12 R24: data 檔更新後 cache key 改變（mtime 失效）")
def t12():
    import tempfile, json, time
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "analysis_20260403.json"
        payload = {
            "date": "2026-04-03",
            "overall": {"avg_sentiment": 0.5, "total_posts": 10},
            "sentiment_distribution": {"positive": 5, "negative": 3, "neutral": 2},
            "heroes": [],
            "platform_stats": {},
        }
        p.write_text(json.dumps(payload), encoding="utf-8")
        schema_path = (
            Path(__file__).resolve().parent / "resources" / "schema_version.json"
        )
        loader = TimeSeriesLoader(data_dir=Path(tmp), schema_path=schema_path, cache_size=8)
        loader.load_range("2026-04-03", "2026-04-03")
        assert loader.cache_stats()["misses"] == 1
        # 修改檔案（改 mtime）
        time.sleep(0.05)
        p.write_text(json.dumps(payload), encoding="utf-8")
        # 再次 load_range：mtime 不同 → cache miss，不命中舊 key
        loader.load_range("2026-04-03", "2026-04-03")
        assert loader.cache_stats()["misses"] == 2, "R24: 檔案更新後應 cache miss"
        assert loader.cache_stats()["hits"] == 0, "R24: 不應命中舊 mtime key"


@test("T13 R20: render_multi_markdown 多軌日期不同步 → 輸出列依日期排序")
def t13():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
    from renderer import TrendRenderer
    renderer = TrendRenderer()
    multi = {
        "mode": "heroes",
        "range": {"start": "2026-04-01", "end": "2026-04-03"},
        "heroes": [
            {
                "hero": "A",
                "points": [
                    {"date": "2026-04-01", "status": "ok", "count": 1, "avg_sentiment": 0.5},
                    {"date": "2026-04-03", "status": "ok", "count": 3, "avg_sentiment": 0.5},
                ],
            },
            {
                "hero": "B",
                "points": [
                    {"date": "2026-04-01", "status": "ok", "count": 10, "avg_sentiment": 0.5},
                    {"date": "2026-04-02", "status": "ok", "count": 20, "avg_sentiment": 0.5},
                ],
            },
        ],
    }
    md = renderer.render_multi_markdown(multi)
    rows = [ln for ln in md.splitlines() if ln.startswith("| 20")]
    dates_in_output = [r.split("|")[1].strip() for r in rows]
    assert dates_in_output == sorted(dates_in_output), f"R20: 日期列未排序 {dates_in_output}"
    assert len(dates_in_output) == 3, f"應有 3 列，got {len(dates_in_output)}"


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 61 Stage 1 + S5 F1 — TimeSeriesLoader 驗收測試")
    print("=" * 60)

    for name, fn in list(globals().items()):
        if name.startswith("t") and callable(fn) and name[1:].isdigit():
            pass  # 測試已在 decorator 執行時跑完

    print("-" * 60)
    print(f"通過 {len(PASSED)} / {len(PASSED) + len(FAILED)}")
    if FAILED:
        print("失敗項：")
        for n, msg in FAILED:
            print(f"  - {n}: {msg}")
        sys.exit(1)
    print("S1 地基測試全綠 ✅")
