"""
Phase 61 Stage 5 F7 — anomaly_marker 驗收測試

驗收項：
T1 z-score 邊界：含明顯離群值 → 對應 idx 為 True
T2 空 list / 樣本不足（n<2）→ 全 False
T3 全相同值（std=0）→ 全 False
T4 含 missing/invalid/hero_absent/bool/字串 → 該位置略過視為 False；不噴錯
T5 mark_anomalies_with_scores：合格點回 z-score、不合格回 None；std=0 全 0.0
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from anomaly_marker import mark_anomalies, mark_anomalies_with_scores  # noqa: E402

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


def _ok(value: float, key: str = "count") -> dict:
    return {"date": "x", "status": "ok", key: value}


@test("T1 z-score 邊界：含離群值（10 個 5、1 個 100）→ 100 那點為 True")
def t1():
    points = [_ok(5.0)] * 10 + [_ok(100.0)]
    flags = mark_anomalies(points, z_threshold=2.0)
    assert len(flags) == 11
    assert flags[-1] is True, f"離群值應標 True，flags={flags}"
    assert sum(flags) == 1, f"只應有 1 個 True，got {sum(flags)}"


@test("T2 空 list / n=1 → 全 False、不噴錯")
def t2():
    assert mark_anomalies([]) == []
    assert mark_anomalies([_ok(5.0)]) == [False]


@test("T3 全相同值（std=0）→ 全 False")
def t3():
    points = [_ok(7.0) for _ in range(5)]
    flags = mark_anomalies(points)
    assert flags == [False] * 5, f"std=0 應全 False，got {flags}"


@test("T4 混合 status / 非數值：missing/invalid/hero_absent/bool/str/None → 該位置 False、計算只用 ok 數值")
def t4():
    points = [
        _ok(5.0),
        {"status": "missing", "count": None},
        {"status": "invalid", "count": 999},      # invalid 不算（合約 R5）
        {"status": "hero_absent", "count": 0},
        {"status": "ok", "count": True},          # bool 排除
        {"status": "ok", "count": "abc"},         # 字串排除
        {"status": "ok", "count": None},          # None 排除
        _ok(5.0),
        _ok(5.0),
        _ok(100.0),                               # 真離群
    ]
    flags = mark_anomalies(points, z_threshold=2.0)
    assert len(flags) == 10
    # 非 ok 或非數值位置必為 False
    for i in [1, 2, 3, 4, 5, 6]:
        assert flags[i] is False, f"idx={i} 應為 False，got {flags[i]}"
    # 第 9 點是真離群（5,5,5,100 → mean=28.75 std≈41 → z≈1.74 不一定觸 2.0；
    # 用 4 個樣本 std 較大，故再加幾個樣本確保觸發；本案 ok 樣本 = [5,5,5,100]
    # 此測試重點是「不噴錯 + 排除非 ok」，z 結果為附帶觀察）
    # 不對 flags[9] 強制斷言（樣本太少 z 不一定達 2.0），改驗 with_scores 有算到
    scores = mark_anomalies_with_scores(points)
    assert scores[9] is not None and scores[9] > 0, f"離群點應有正 z-score，got {scores[9]}"
    for i in [1, 2, 3, 4, 5, 6]:
        assert scores[i] is None, f"idx={i} score 應 None，got {scores[i]}"


@test("T5 mark_anomalies_with_scores：合格回 z-score、不合格回 None；std=0 全 0.0")
def t5():
    # std > 0 案例
    points = [_ok(5.0), _ok(5.0), _ok(5.0), _ok(100.0)]
    scores = mark_anomalies_with_scores(points)
    assert all(s is not None for s in scores)
    assert scores[3] > scores[0], "100 的 z-score 應比 5 高"

    # std == 0 案例
    points = [_ok(7.0)] * 4
    scores = mark_anomalies_with_scores(points)
    assert scores == [0.0, 0.0, 0.0, 0.0], f"std=0 應全 0.0，got {scores}"

    # value_key 切換
    points = [
        {"status": "ok", "post_count": 1.0},
        {"status": "ok", "post_count": 1.0},
        {"status": "ok", "post_count": 1.0},
        {"status": "ok", "post_count": 50.0},
    ]
    scores = mark_anomalies_with_scores(points, value_key="post_count")
    assert scores[3] > 1.5, f"切 post_count 應正常算 z，got {scores[3]}"


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 61 Stage 5 F7 — anomaly_marker 驗收測試")
    print("=" * 60)
    print("-" * 60)
    print(f"通過 {len(PASSED)} / {len(PASSED) + len(FAILED)}")
    if FAILED:
        print("失敗項：")
        for n, msg in FAILED:
            print(f"  - {n}: {msg}")
        sys.exit(1)
    print("F7 anomaly_marker 測試全綠 ✅")
