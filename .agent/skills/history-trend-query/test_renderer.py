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


# ────────────────────────────────────────────────────────────
# R12：SVG x 軸刻度
# ────────────────────────────────────────────────────────────
@test("T12 R12：SVG 7 天圖含 x 軸刻度，每日一標")
def t12():
    points = [
        {"date": f"2026-01-0{i+1}", "status": "ok",
         "count": 5, "avg_sentiment": 0.5}
        for i in range(7)
    ]
    svg = TrendRenderer().html_svg(_make_trend(points))
    # 7 天 → 每點一標 → 7 條 tick line
    tick_lines = re.findall(r'<line[^>]*stroke="#e5e5e5"', svg)
    assert len(tick_lines) == 7, f"應有 7 條 tick line，got {len(tick_lines)}"
    # 每個日期末尾 MM-DD 應現身
    for i in range(1, 8):
        assert f"01-0{i}" in svg, f"01-0{i} 應出現在 SVG 刻度"


@test("T13 R12：SVG 30 天圖刻度自適應（每 7 天一標 + 末點）")
def t13():
    points = []
    for i in range(30):
        d = 1 + i
        iso = f"2026-01-{d:02d}" if d <= 31 else f"2026-02-{d-31:02d}"
        points.append({"date": iso, "status": "ok", "count": 5, "avg_sentiment": 0.5})
    svg = TrendRenderer().html_svg(_make_trend(points))
    tick_lines = re.findall(r'<line[^>]*stroke="#e5e5e5"', svg)
    # 每 7 天：0, 7, 14, 21, 28 → 5 + 末點 29 = 6 條
    assert len(tick_lines) == 6, f"30 天應有 6 條 tick，got {len(tick_lines)}"


@test("T14 R12：x_axis=False 不出刻度")
def t14():
    points = [
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "ok", "count": 8, "avg_sentiment": 0.7},
    ]
    svg = TrendRenderer().html_svg(_make_trend(points), x_axis=False)
    tick_lines = re.findall(r'<line[^>]*stroke="#e5e5e5"', svg)
    assert len(tick_lines) == 0, f"x_axis=False 不應有 tick，got {len(tick_lines)}"


# ────────────────────────────────────────────────────────────
# R15：HTML escape 防 XSS
# ────────────────────────────────────────────────────────────
@test("T15 R15：hero name 含 <script> 被 escape，SVG 不含裸 <script>")
def t15():
    points = [
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ]
    trend = _make_trend(points, hero='<script>alert("xss")</script>')
    svg = TrendRenderer().html_svg(trend)
    assert "<script>" not in svg, "裸 <script> 絕不應進入 SVG"
    assert "&lt;script&gt;" in svg, "應被轉為 &lt;script&gt;"
    # quote 版本也要 escape（防 attr 注入）
    assert '"xss"' not in svg or "&quot;xss&quot;" in svg


@test("T16 R15：range 與 title 內容也經 escape")
def t16():
    points = [
        {"date": '2026"><bad', "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ]
    trend = _make_trend(points)
    svg = TrendRenderer().html_svg(trend)
    assert '"><bad' not in svg, "date 欄位的注入嘗試應被 escape"


# ────────────────────────────────────────────────────────────
# R14：Markdown pipe 跳脫
# ────────────────────────────────────────────────────────────
@test("T17 R14：hero name 含 `|` → 跳脫為 `\\|`，表格不破")
def t17():
    points = [
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ]
    trend = _make_trend(points, hero="毒|招")
    md = TrendRenderer().markdown_table(trend)
    assert "毒\\|招" in md, f"hero `|` 應跳脫為 \\|，實際：{md}"
    # 標題行統計欄位數正確
    header_line = next(l for l in md.split("\n") if l.startswith("| 日期"))
    assert header_line.count("|") == 5, "header 應 5 個 pipe（4 欄）"


@test("T18 R14：date 含 `|` 也跳脫")
def t18():
    points = [
        {"date": "2026|01|01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ]
    trend = _make_trend(points)
    md = TrendRenderer().markdown_table(trend)
    assert "2026\\|01\\|01" in md, "date `|` 應跳脫"


# ────────────────────────────────────────────────────────────
# S4 R16 — T19~T22：多軌渲染
# ────────────────────────────────────────────────────────────
def _make_heroes_multi(hero_specs, raw: bool = False):
    """造 heroes_trend 風格的 multi 結構。
    hero_specs: List[(hero_name, points)]，points 已含 status/count。
    自動補 normalized_count（若 raw=False）。
    """
    heroes = []
    for name, pts in hero_specs:
        heroes.append({
            "hero": name,
            "days": len(pts),
            "range": {"start": pts[0]["date"] if pts else "",
                      "end": pts[-1]["date"] if pts else ""},
            "points": [dict(p) for p in pts],  # 深拷貝避免污染
            "summary": {},
        })
    multi = {
        "mode": "heroes",
        "hero_names": [n for n, _ in hero_specs],
        "days": len(hero_specs[0][1]) if hero_specs else 0,
        "raw": raw,
        "range": {
            "start": hero_specs[0][1][0]["date"] if hero_specs and hero_specs[0][1] else "",
            "end": hero_specs[0][1][-1]["date"] if hero_specs and hero_specs[0][1] else "",
        },
        "heroes": heroes,
    }
    if not raw:
        # 跨軌 min-max
        all_v = [p["count"] for h in multi["heroes"] for p in h["points"]
                 if p.get("status") == "ok" and isinstance(p.get("count"), (int, float))]
        if all_v:
            lo, hi = min(all_v), max(all_v)
            span = hi - lo
            for h in multi["heroes"]:
                for p in h["points"]:
                    if p.get("status") == "ok" and isinstance(p.get("count"), (int, float)):
                        p["normalized_count"] = (
                            (float(p["count"]) - lo) / span if span > 0 else 0.5
                        )
    return multi


@test("T19 R16：render_multi_svg 多英雄 → palette 至少出現 2 種顏色")
def t19():
    multi = _make_heroes_multi([
        ("甲", [
            {"date": "2026-01-01", "status": "ok", "count": 5},
            {"date": "2026-01-02", "status": "ok", "count": 10},
            {"date": "2026-01-03", "status": "ok", "count": 15},
        ]),
        ("乙", [
            {"date": "2026-01-01", "status": "ok", "count": 50},
            {"date": "2026-01-02", "status": "ok", "count": 30},
            {"date": "2026-01-03", "status": "ok", "count": 20},
        ]),
    ])
    svg = TrendRenderer().render_multi_svg(multi)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    # 至少 2 種 palette 顏色（桃紅 #db2777 + 青 #0ea5e9）
    assert "#db2777" in svg, "首軌應為桃紅"
    assert "#0ea5e9" in svg, "次軌應為青"
    # 圖例：兩個 hero name 都應出現
    assert "甲" in svg and "乙" in svg


@test("T20 R16：render_multi_markdown 多英雄並列欄位、header 含所有 hero name")
def t20():
    multi = _make_heroes_multi([
        ("甲", [
            {"date": "2026-01-01", "status": "ok", "count": 5},
            {"date": "2026-01-02", "status": "missing", "count": None},
        ]),
        ("乙", [
            {"date": "2026-01-01", "status": "hero_absent", "count": 0},
            {"date": "2026-01-02", "status": "ok", "count": 30},
        ]),
    ])
    md = TrendRenderer().render_multi_markdown(multi)
    # header 形如 "| 日期 | 甲 | 乙 |"
    header_line = next(l for l in md.split("\n") if l.startswith("| 日期"))
    assert "甲" in header_line and "乙" in header_line
    assert header_line.count("|") == 4, f"header 應 4 個 pipe（3 欄），got: {header_line}"

    # 01-01 列：甲=5、乙=· (absent)
    assert "| 5 | · |" in md or "5" in md and "·" in md
    # 01-02 列：甲=missing(—)、乙=30
    assert "30" in md


@test("T21 R16：render_multi 單軌 fallback 不崩")
def t21():
    multi = _make_heroes_multi([
        ("甲", [
            {"date": "2026-01-01", "status": "ok", "count": 5},
            {"date": "2026-01-02", "status": "ok", "count": 10},
        ]),
    ])
    svg = TrendRenderer().render_multi_svg(multi)
    md = TrendRenderer().render_multi_markdown(multi)
    assert "<svg" in svg and "</svg>" in svg
    assert "#db2777" in svg
    assert "甲" in md and "2026-01-01" in md


@test("T22 R16：raw=True multi → 渲染端臨時 normalize 不噴錯")
def t22():
    multi = _make_heroes_multi([
        ("甲", [
            {"date": "2026-01-01", "status": "ok", "count": 5},
            {"date": "2026-01-02", "status": "ok", "count": 10},
        ]),
        ("乙", [
            {"date": "2026-01-01", "status": "ok", "count": 100},
            {"date": "2026-01-02", "status": "ok", "count": 200},
        ]),
    ], raw=True)
    # raw=True 時 points 不應有 normalized_count
    for h in multi["heroes"]:
        for p in h["points"]:
            assert "normalized_count" not in p
    svg = TrendRenderer().render_multi_svg(multi)
    # 渲染端應 fallback 自己 normalize，至少有 4 個 circle（2 軌 × 2 點）
    assert len(re.findall(r"<circle ", svg)) == 4
    assert "#db2777" in svg and "#0ea5e9" in svg


@test("T23 R16：render_multi 平台模式（mode=platform）")
def t23():
    multi = {
        "mode": "platform",
        "days": 2,
        "raw": False,
        "platforms": ["facebook", "youtube"],
        "range": {"start": "2026-01-01", "end": "2026-01-02"},
        "platform_data": {
            "facebook": [
                {"date": "2026-01-01", "status": "ok", "post_count": 10, "normalized_count": 0.0},
                {"date": "2026-01-02", "status": "ok", "post_count": 50, "normalized_count": 1.0},
            ],
            "youtube": [
                {"date": "2026-01-01", "status": "ok", "post_count": 20, "normalized_count": 0.25},
                {"date": "2026-01-02", "status": "absent", "post_count": 0},
            ],
        },
    }
    svg = TrendRenderer().render_multi_svg(multi)
    md = TrendRenderer().render_multi_markdown(multi)
    assert "facebook" in svg and "youtube" in svg
    assert "facebook" in md and "youtube" in md
    # 01-02 youtube absent 在 markdown 應顯 ·
    assert "·" in md


@test("T24 R16：mode 不合法 → ValueError")
def t24():
    bad = {"mode": "bogus", "heroes": []}
    try:
        TrendRenderer().render_multi_svg(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("不合法 mode 應噴 ValueError")


# ─────────────────────────────────────────────────────────────
# S5 F6 — T25：legend 自動換行（R19）
# ─────────────────────────────────────────────────────────────
@test("T25 R19：5 軌長名 legend 自動換行 → SVG height 動態擴增")
def t25():
    long_names = [
        "超級長英雄名稱A_AAAAAAAAA",
        "超級長英雄名稱B_BBBBBBBBB",
        "超級長英雄名稱C_CCCCCCCCC",
        "超級長英雄名稱D_DDDDDDDDD",
        "超級長英雄名稱E_EEEEEEEEE",
    ]
    multi = {
        "mode": "heroes",
        "raw": False,
        "range": {"start": "2026-01-01", "end": "2026-01-02"},
        "heroes": [
            {
                "hero": n,
                "points": [
                    {"date": "2026-01-01", "status": "ok", "count": i + 1, "normalized_count": 0.5},
                    {"date": "2026-01-02", "status": "ok", "count": i + 2, "normalized_count": 0.7},
                ],
            }
            for i, n in enumerate(long_names)
        ],
    }
    base_h = 220  # render_multi_svg 預設 height
    svg = TrendRenderer().render_multi_svg(multi, width=400, height=base_h)

    # 5 軌長名 width=400 必然觸發換行 → SVG height 大於預設
    m = re.search(r'<svg [^>]*height="(\d+)"', svg)
    assert m, "SVG 應有 height 屬性"
    final_h = int(m.group(1))
    assert final_h > base_h, f"legend 換行後 height 應 > {base_h}，got {final_h}"

    # 對照組：寬度足夠時不換行 → height == 預設
    svg_wide = TrendRenderer().render_multi_svg(multi, width=2000, height=base_h)
    m2 = re.search(r'<svg [^>]*height="(\d+)"', svg_wide)
    assert m2 and int(m2.group(1)) == base_h, f"寬度足夠時 height 應維持 {base_h}"

    # 所有英雄名都應出現在 svg
    for n in long_names:
        assert n in svg, f"legend 應含 {n}"


# ─────────────────────────────────────────────────────────────
# S5 F7 — T26~T27：anomaly overlay 紅圈
# ─────────────────────────────────────────────────────────────
@test("T26 R7：anomaly_flags=True 的 ok 點外圍多畫紅圈 #dc2626")
def t26():
    points = [
        {"date": "2026-01-01", "status": "ok", "count": 5,   "avg_sentiment": 0.5},
        {"date": "2026-01-02", "status": "ok", "count": 5,   "avg_sentiment": 0.5},
        {"date": "2026-01-03", "status": "ok", "count": 100, "avg_sentiment": 0.5},
    ]
    trend = _make_trend(points)
    flags = [False, False, True]
    svg = TrendRenderer().html_svg(trend, anomaly_flags=flags)

    assert "#dc2626" in svg, "anomaly 點外環應為 #dc2626"
    # 應有恰好 1 個 r=7 stroke 紅圈（其他點不該被加）
    red_rings = re.findall(r'stroke="#dc2626"', svg)
    assert len(red_rings) == 1, f"應只有 1 個紅圈，got {len(red_rings)}"

    # 對照組：不傳 anomaly_flags → SVG 不含紅色
    svg_clean = TrendRenderer().html_svg(trend)
    assert "#dc2626" not in svg_clean


@test("T27 anomaly_flags 長度與 points 不符 → ValueError")
def t27():
    trend = _make_trend([
        {"date": "2026-01-01", "status": "ok", "count": 5, "avg_sentiment": 0.5},
    ])
    try:
        TrendRenderer().html_svg(trend, anomaly_flags=[True, False])
    except ValueError:
        pass
    else:
        raise AssertionError("長度不符應噴 ValueError")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 61 S3/S4 + S5 F6/F7 — TrendRenderer 驗收測試")
    print("=" * 60)

    print("-" * 60)
    print(f"通過 {len(PASSED)} / {len(PASSED) + len(FAILED)}")
    if FAILED:
        print("失敗項：")
        for n, msg in FAILED:
            print(f"  - {n}: {msg}")
        sys.exit(1)
    print("S3 渲染器測試全綠 ✅")
