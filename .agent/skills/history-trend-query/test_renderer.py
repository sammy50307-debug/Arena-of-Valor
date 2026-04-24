"""
Phase 61 Stage 3 渲染器測試 — TrendRenderer

驗收項：
T1 Unicode sparkline：ok 資料出對應柱、最高最低值落在 palette 兩端
T2 ASCII fallback：輸出僅含 ASCII 字元（+`?`、`.`）
T3 hero_absent → 灰點字元（Unicode `·` / ASCII `.`）
T4 missing / invalid → `?`
T5 Markdown 表格完整 4 欄、summary 含 avg_sentiment_mode
T6 HTML SVG 有效：含 <svg>/</svg>、灰點 fill=#aaaaaa、ok 點 fill=#db2777
T7 空 points → '(no data)' / SVG 顯 no data
T8 單一 ok 點（len=1）不除零
T9 全 ok 同值（span=0）→ 中層 palette 字元、不除零
T10 metric 可切換 count / avg_sentiment
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from renderer import TrendRenderer, _UNICODE_BLOCKS, _ASCII_LEVELS  # noqa: E402

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


def _make_trend(points, hero="測試", mode="arithmetic", avg=None):
    ok_counts = [p["count"] for p in points if p.get("status") == "ok" and isinstance(p.get("count"), (int, float))]
    ok_sents = [p["avg_sentiment"] for p in points if p.get("status") == "ok" and isinstance(p.get("avg_sentiment"), (int, float))]
    return {
        "hero": hero,
        "days": len(points),
        "range": {"start": points[0]["date"] if points else "", "end": points[-1]["date"] if points else ""},
        "points": points,
        "summary": {
            "days_requested": len(points),
            "days_ok": sum(1 for p in points if p.get("status") == "ok"),
            "days_missing": sum(1 for p in points if p.get("status") == "missing"),
            "days_invalid": sum(1 for p in points if p.get("status") == "invalid"),
            "days_hero_absent": sum(1 for p in points if p.get("status") == "hero_absent"),
            "total_count": sum(ok_counts),
            "avg_sentiment_mean": avg if avg is not None else (sum(ok_sents) / len(ok_sents) if ok_sents else None),
            "avg_sentiment_mode": mode,
            "coverage_ratio": (sum(1 for p in points if p.get("status") == "ok") / len(points)) if points else 0.0,
        },
    }


# ────────────────────────────────────────────────────────────
@test("T1 Unicode sparkline：count=[1,5,10] 應出 palette 最低→最高三字元")
def t1():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 1, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "ok", "count": 5, "avg_sentiment": 0.6},
        {"date": "2026-01-03", "status": "ok", "count": 10, "avg_sentiment": 0.7},
    ])
    out = TrendRenderer().sparkline(trend)
    assert len(out) == 3
    assert out[0] == _UNICODE_BLOCKS[0], f"最低應是 {_UNICODE_BLOCKS[0]}，got {out[0]}"
    assert out[-1] == _UNICODE_BLOCKS[-1], f"最高應是 {_UNICODE_BLOCKS[-1]}，got {out[-1]}"


@test("T2 ASCII fallback：輸出不含 Unicode block 字元")
def t2():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 1, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "ok", "count": 10, "avg_sentiment": 0.7},
    ])
    out = TrendRenderer().sparkline(trend, ascii_fallback=True)
    for ch in _UNICODE_BLOCKS:
        assert ch not in out, f"ASCII 模式不該出現 Unicode block {ch!r}"
    # 每字元皆 ord < 128（純 ASCII）
    assert all(ord(c) < 128 for c in out), f"含非 ASCII 字元：{out!r}"


@test("T3 hero_absent → 灰點字元（Unicode `·` / ASCII `.`）")
def t3():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "hero_absent", "count": 0, "avg_sentiment": None},
        {"date": "2026-01-03", "status": "ok", "count": 10, "avg_sentiment": 0.7},
    ])
    uni = TrendRenderer().sparkline(trend)
    assert uni[1] == "·", f"Unicode absent 應為 ·，got {uni[1]!r}"

    ascii_ = TrendRenderer().sparkline(trend, ascii_fallback=True)
    assert ascii_[1] == ".", f"ASCII absent 應為 .，got {ascii_[1]!r}"


@test("T4 missing / invalid → `?`")
def t4():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "missing", "count": None, "avg_sentiment": None},
        {"date": "2026-01-03", "status": "invalid", "count": None, "avg_sentiment": None},
    ])
    out = TrendRenderer().sparkline(trend)
    assert out[1] == "?", f"missing 應 ?，got {out[1]!r}"
    assert out[2] == "?", f"invalid 應 ?，got {out[2]!r}"


@test("T5 Markdown 表格：4 欄 header + summary 含 avg_sentiment_mode")
def t5():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "missing", "count": None, "avg_sentiment": None},
        {"date": "2026-01-03", "status": "hero_absent", "count": 0, "avg_sentiment": None},
    ], mode="weighted")
    md = TrendRenderer().markdown_table(trend)
    assert "| 日期 | 狀態 | 聲量 | 情緒 |" in md
    assert "|------|------|------|------|" in md
    assert "2026-01-01" in md and "ok" in md
    assert "— (no data)" in md, "missing 列標應為 — (no data)"
    assert "· (absent)" in md, "absent 列標應為 · (absent)"
    assert "weighted" in md, "summary 應標註 mode"


@test("T6 HTML SVG：有效 <svg>、灰點 #aaaaaa、ok 點 #db2777")
def t6():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "hero_absent", "count": 0, "avg_sentiment": None},
        {"date": "2026-01-03", "status": "ok", "count": 10, "avg_sentiment": 0.7},
    ], hero="芽芽")
    svg = TrendRenderer().html_svg(trend)
    assert svg.startswith("<svg"), "應以 <svg 開頭"
    assert svg.endswith("</svg>"), "應以 </svg> 結尾"
    assert 'fill="#aaaaaa"' in svg, "灰點 fill 應為 #aaaaaa"
    assert 'fill="#db2777"' in svg, "ok 點 fill 應為 #db2777"
    assert "芽芽" in svg, "title 應含 hero name"
    # 點數：ok=2 + absent=1 = 3 個 circle（不含任何 rect/text 的）
    circle_count = len(re.findall(r"<circle ", svg))
    assert circle_count == 3, f"應有 3 個 circle，got {circle_count}"


@test("T7 空 points → '(no data)' / SVG 顯 no data")
def t7():
    trend = _make_trend([])
    r = TrendRenderer()
    assert r.sparkline(trend) == "(no data)"
    svg = r.html_svg(trend)
    assert ">no data<" in svg


@test("T8 單一 ok 點不除零")
def t8():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ])
    r = TrendRenderer()
    # 不應噴 ZeroDivisionError
    out = r.sparkline(trend)
    assert len(out) == 1
    svg = r.html_svg(trend)
    assert "<circle" in svg


@test("T9 全 ok 同值（span=0）→ 中層 palette 字元、不除零")
def t9():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-03", "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ])
    out = TrendRenderer().sparkline(trend)
    mid = _UNICODE_BLOCKS[len(_UNICODE_BLOCKS) // 2]
    assert all(c == mid for c in out), f"同值應全為中層 {mid!r}，got {out!r}"


@test("T10 metric 可切換 count / avg_sentiment")
def t10():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 100, "avg_sentiment": 0.1},
        {"date": "2026-01-02", "status": "ok", "count": 1, "avg_sentiment": 0.9},
    ])
    by_count = TrendRenderer(metric="count").sparkline(trend)
    by_sent = TrendRenderer(metric="avg_sentiment").sparkline(trend)
    # count 遞減 → 第一點高、第二點低；sentiment 遞增 → 相反
    assert by_count[0] == _UNICODE_BLOCKS[-1] and by_count[1] == _UNICODE_BLOCKS[0]
    assert by_sent[0] == _UNICODE_BLOCKS[0] and by_sent[1] == _UNICODE_BLOCKS[-1]


@test("T11 invalid metric → ValueError")
def t11():
    try:
        TrendRenderer(metric="bogus")
    except ValueError:
        return
    raise AssertionError("應噴 ValueError 但沒有")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 61 Stage 3 — TrendRenderer 驗收測試")
    print("=" * 60)

    print("-" * 60)
    print(f"通過 {len(PASSED)} / {len(PASSED) + len(FAILED)}")
    if FAILED:
        print("失敗項：")
        for n, msg in FAILED:
            print(f"  - {n}: {msg}")
        sys.exit(1)
    print("S3 渲染器測試全綠 ✅")
