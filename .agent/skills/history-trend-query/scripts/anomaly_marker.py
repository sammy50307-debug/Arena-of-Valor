"""
anomaly_marker — Phase 61 Stage 5 F7 薄介面外掛

純函式異常標記器：給一條 trend points list、回傳同長度 bool list。
與 Phase 50 trend-anomaly-detector 解耦——任何模組（renderer / detector / 第三方）
皆可呼叫，無依賴 query.py、無依賴 detector 內部演算法。

設計約束：
    - 不依賴 numpy / scipy（純標準庫）
    - 對 status != 'ok' 或 value 非數值的點，回 False（既不算異常、也不噴錯）
    - 樣本數 < 2 或標準差為 0 → 全 False（無從談異常）
    - z-score 預設門檻 2.0（約 95% 置信區間外）
"""

from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Optional


def mark_anomalies(
    points: List[Dict[str, Any]],
    z_threshold: float = 2.0,
    value_key: str = "count",
) -> List[bool]:
    """
    對 trend points 算 z-score、回傳異常布林旗標。

    參數：
        points:        list of dict，至少含 {"status": ..., value_key: ...}
        z_threshold:   |z-score| 超過此值即視為異常（預設 2.0）
        value_key:     哪一欄取值（hero=count、overall=total_posts、platform=post_count）

    回傳：
        List[bool]，長度與 points 一致；True 表示該點異常。
        非 ok / 非數值 / 樣本不足 → False。
    """
    n = len(points)
    flags = [False] * n
    if n == 0:
        return flags

    # 收集合格樣本（status=ok 且 value 為數值）
    indices: List[int] = []
    values: List[float] = []
    for i, p in enumerate(points):
        if p.get("status") != "ok":
            continue
        v = p.get(value_key)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        indices.append(i)
        values.append(float(v))

    if len(values) < 2:
        return flags

    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = sqrt(var)
    if std == 0:
        return flags

    threshold = abs(float(z_threshold))
    for idx, v in zip(indices, values):
        z = (v - mean) / std
        if abs(z) >= threshold:
            flags[idx] = True
    return flags


def mark_anomalies_with_scores(
    points: List[Dict[str, Any]],
    z_threshold: float = 2.0,
    value_key: str = "count",
) -> List[Optional[float]]:
    """
    回傳每點的 z-score（同長度 list）；非 ok / 不合格 → None。
    Detector 端若需要詳細分數可呼叫此版本；renderer 端用 mark_anomalies 即可。
    """
    n = len(points)
    scores: List[Optional[float]] = [None] * n
    if n == 0:
        return scores

    indices: List[int] = []
    values: List[float] = []
    for i, p in enumerate(points):
        if p.get("status") != "ok":
            continue
        v = p.get(value_key)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        indices.append(i)
        values.append(float(v))

    if len(values) < 2:
        return scores

    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = sqrt(var)
    if std == 0:
        # 全相同值：scores 用 0.0（無偏離）而非 None，方便 renderer 區分
        for idx in indices:
            scores[idx] = 0.0
        return scores

    _ = z_threshold  # 與 mark_anomalies 簽名對齊；本 helper 回原始分數
    for idx, v in zip(indices, values):
        scores[idx] = (v - mean) / std
    return scores


if __name__ == "__main__":
    import argparse
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from query import HistoryTrendQuery  # noqa: E402

    parser = argparse.ArgumentParser(description="anomaly_marker CLI（debug 用）")
    parser.add_argument("--hero", required=True)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--until", default=None)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args()

    q = HistoryTrendQuery(data_dir=args.data_dir) if args.data_dir else HistoryTrendQuery()
    trend = q.hero_trend(args.hero, args.days, until=args.until)
    flags = mark_anomalies(trend["points"], z_threshold=args.threshold)
    scores = mark_anomalies_with_scores(trend["points"], z_threshold=args.threshold)
    out = [
        {**p, "anomaly": f, "z_score": s}
        for p, f, s in zip(trend["points"], flags, scores)
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))
