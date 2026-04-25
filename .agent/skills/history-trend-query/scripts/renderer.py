"""
TrendRenderer — Phase 61 Stage 3 渲染統一

同一份 hero_trend 輸出（來自 query.py）吃四種渲染格式：
    1. sparkline (Unicode block chars)
    2. sparkline_ascii (ASCII fallback)
    3. markdown_table
    4. html_svg

灰點策略（R9）：
    ok          → 正常柱高 / 桃紅圓點
    hero_absent → · (Unicode) / . (ASCII) / 灰色小圓點
    missing     → ? / 虛線斷線
    invalid     → 視同 missing（無數值可畫）
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional

# Unicode block chars — 8 levels (低→高)
_UNICODE_BLOCKS = "▁▂▃▄▅▆▇█"
_ASCII_LEVELS = "_.-~^"
_ABSENT_UNICODE = "·"
_ABSENT_ASCII = "."
_MISSING_CHAR = "?"

# 色盤
_COLOR_OK = "#db2777"        # 旗艦桃紅（Phase40 視覺真經）
_COLOR_ABSENT = "#aaaaaa"    # 灰點（R9 主公裁示）
_COLOR_GRID = "#e5e5e5"
_COLOR_TEXT = "#333333"


class TrendRenderer:
    """hero_trend 字典 → 多格式渲染。"""

    def __init__(self, metric: str = "count") -> None:
        if metric not in ("count", "avg_sentiment"):
            raise ValueError(f"metric 必須是 'count' 或 'avg_sentiment'，got {metric!r}")
        self.metric = metric

    # ────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────
    @staticmethod
    def _extract_value(point: Dict[str, Any], metric: str) -> Optional[float]:
        """從單點取出要畫的數值；非 ok 且非 absent 一律 None。"""
        status = point.get("status")
        if status == "ok":
            v = point.get(metric)
            return float(v) if isinstance(v, (int, float)) else None
        if status == "hero_absent" and metric == "count":
            return 0.0  # absent 的 count 語意為 0
        return None

    # ────────────────────────────────────────────
    # Format 1 & 2：sparkline
    # ────────────────────────────────────────────
    def sparkline(self, trend: Dict[str, Any], ascii_fallback: bool = False) -> str:
        """單行 sparkline。空資料回 '(no data)'。"""
        points = trend.get("points", [])
        if not points:
            return "(no data)"

        palette = _ASCII_LEVELS if ascii_fallback else _UNICODE_BLOCKS
        absent_ch = _ABSENT_ASCII if ascii_fallback else _ABSENT_UNICODE

        values: List[Optional[float]] = [self._extract_value(p, self.metric) for p in points]
        # 只拿 ok 的值做正規化範圍（absent 的 0 不參與，否則低值區間被吃掉）
        ok_values = [
            self._extract_value(p, self.metric)
            for p in points
            if p.get("status") == "ok"
        ]

        if not ok_values:
            # 全無 ok 資料 → 每點依 status 標示
            chars = []
            for p in points:
                st = p.get("status")
                if st == "hero_absent":
                    chars.append(absent_ch)
                else:
                    chars.append(_MISSING_CHAR)
            return "".join(chars)

        lo, hi = min(ok_values), max(ok_values)
        span = hi - lo
        levels = len(palette)
        chars = []
        for p, v in zip(points, values):
            st = p.get("status")
            if st == "ok" and v is not None:
                if span == 0:
                    chars.append(palette[levels // 2])
                else:
                    idx = int(round((v - lo) / span * (levels - 1)))
                    chars.append(palette[max(0, min(levels - 1, idx))])
            elif st == "hero_absent":
                chars.append(absent_ch)
            else:
                chars.append(_MISSING_CHAR)
        return "".join(chars)

    # ────────────────────────────────────────────
    # Format 3：markdown_table
    # ────────────────────────────────────────────
    @staticmethod
    def _md_escape(s: Any) -> str:
        """R14：cell 內 `|` 會破表格，跳脫成 `\\|`。"""
        return str(s).replace("|", "\\|")

    def markdown_table(self, trend: Dict[str, Any]) -> str:
        e = self._md_escape
        hero = e(trend.get("hero", "—"))
        points = trend.get("points", [])
        summary = trend.get("summary", {})

        lines = [
            f"### 走勢表 — {hero}",
            "",
            "| 日期 | 狀態 | 聲量 | 情緒 |",
            "|------|------|------|------|",
        ]
        for p in points:
            st = p.get("status", "—")
            date = e(p.get("date", "—"))
            if st == "ok":
                cnt = p.get("count")
                sent = p.get("avg_sentiment")
                lines.append(
                    f"| {date} | ok | {cnt if cnt is not None else '—'} | "
                    f"{f'{sent:.2f}' if isinstance(sent, (int, float)) else '—'} |"
                )
            elif st == "hero_absent":
                lines.append(f"| {date} | · (absent) | 0 | — |")
            elif st == "missing":
                lines.append(f"| {date} | — (no data) | — | — |")
            elif st == "invalid":
                lines.append(f"| {date} | ⚠ (invalid) | — | — |")
            else:
                lines.append(f"| {date} | {e(st)} | — | — |")

        lines.append("")
        lines.append(
            f"**Summary**：days_requested={summary.get('days_requested')}、"
            f"ok={summary.get('days_ok')}、missing={summary.get('days_missing')}、"
            f"invalid={summary.get('days_invalid')}、absent={summary.get('days_hero_absent')}"
        )
        if summary.get("avg_sentiment_mean") is not None:
            lines.append(
                f"**avg_sentiment_mean**（{summary.get('avg_sentiment_mode', 'arithmetic')}）= "
                f"{summary['avg_sentiment_mean']:.3f}；total_count={summary.get('total_count')}；"
                f"coverage={summary.get('coverage_ratio', 0):.1%}"
            )
        return "\n".join(lines)

    # ────────────────────────────────────────────
    # Format 4：html_svg
    # ────────────────────────────────────────────
    def html_svg(
        self,
        trend: Dict[str, Any],
        width: int = 600,
        height: int = 160,
        pad: int = 20,
        x_axis: bool = True,
    ) -> str:
        points = trend.get("points", [])
        hero_raw = trend.get("hero", "—")
        hero = html.escape(str(hero_raw), quote=True)   # R15：防 XSS
        range_info = trend.get("range", {}) or {}
        range_start = html.escape(str(range_info.get("start", "")), quote=True)
        range_end = html.escape(str(range_info.get("end", "")), quote=True)
        n = len(points)

        if n == 0:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}"><text x="{width//2}" y="{height//2}" '
                f'text-anchor="middle" fill="{_COLOR_TEXT}" font-family="sans-serif">'
                f'no data</text></svg>'
            )

        # R12：x 軸保留底部額外空間放刻度 label
        bottom_pad = pad + 18 if x_axis else pad
        inner_w = width - 2 * pad
        inner_h = height - pad - bottom_pad
        step = inner_w / (n - 1) if n > 1 else 0

        # 正規化 ok 值
        ok_values = [
            self._extract_value(p, self.metric)
            for p in points if p.get("status") == "ok"
        ]
        has_ok = bool(ok_values)
        if has_ok:
            lo, hi = min(ok_values), max(ok_values)
            span = hi - lo or 1.0
        else:
            lo, hi, span = 0.0, 1.0, 1.0

        def _x(i: int) -> float:
            return pad + i * step if n > 1 else width / 2

        def _y(v: float) -> float:
            return pad + inner_h - ((v - lo) / span) * inner_h

        # 組件：背景框、折線（相連 ok 段用實線、跨 missing/invalid 用虛線或跳過）、點
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="sans-serif">',
            f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" '
            f'fill="white" stroke="{_COLOR_GRID}"/>',
            f'<text x="{pad}" y="{pad - 6}" fill="{_COLOR_TEXT}" font-size="12">'
            f'{hero} — {range_start} ~ {range_end}</text>',
        ]

        # 折線：相鄰兩點若皆為 ok 畫實線、一端為 absent 畫灰虛線、含 missing/invalid 跳過
        for i in range(n - 1):
            a, b = points[i], points[i + 1]
            sa, sb = a.get("status"), b.get("status")
            if sa in ("ok", "hero_absent") and sb in ("ok", "hero_absent"):
                va = self._extract_value(a, self.metric)
                vb = self._extract_value(b, self.metric)
                if va is None or vb is None:
                    continue
                stroke = _COLOR_OK if sa == "ok" and sb == "ok" else _COLOR_ABSENT
                dash = "" if stroke == _COLOR_OK else ' stroke-dasharray="3,3"'
                parts.append(
                    f'<line x1="{_x(i):.2f}" y1="{_y(va):.2f}" '
                    f'x2="{_x(i+1):.2f}" y2="{_y(vb):.2f}" '
                    f'stroke="{stroke}" stroke-width="1.5"{dash}/>'
                )

        # 點
        for i, p in enumerate(points):
            st = p.get("status")
            v = self._extract_value(p, self.metric)
            title = html.escape(f'{p.get("date")} {st}', quote=True)   # R15
            if st == "ok" and v is not None:
                parts.append(
                    f'<circle cx="{_x(i):.2f}" cy="{_y(v):.2f}" r="4" '
                    f'fill="{_COLOR_OK}"><title>{title}: {v}</title></circle>'
                )
            elif st == "hero_absent":
                parts.append(
                    f'<circle cx="{_x(i):.2f}" cy="{_y(0.0):.2f}" r="2" '
                    f'fill="{_COLOR_ABSENT}"><title>{title}</title></circle>'
                )
            else:
                # missing / invalid：不畫點
                pass

        # R12：x 軸刻度（自適應間距：n<=7 每點一標、n<=31 每週、n<=90 每兩週、>90 每月）
        if x_axis and n >= 1:
            if n <= 7:
                tick_every = 1
            elif n <= 31:
                tick_every = 7
            elif n <= 90:
                tick_every = 14
            else:
                tick_every = 30

            tick_indices = list(range(0, n, tick_every))
            if (n - 1) not in tick_indices:
                tick_indices.append(n - 1)   # 最末點一律標

            tick_y_line = pad + inner_h
            tick_y_text = tick_y_line + 12
            for i in tick_indices:
                date_str = str(points[i].get("date", ""))
                short = html.escape(date_str[5:] if len(date_str) >= 10 else date_str, quote=True)
                parts.append(
                    f'<line x1="{_x(i):.2f}" y1="{tick_y_line:.2f}" '
                    f'x2="{_x(i):.2f}" y2="{tick_y_line + 3:.2f}" '
                    f'stroke="{_COLOR_GRID}" stroke-width="1"/>'
                )
                parts.append(
                    f'<text x="{_x(i):.2f}" y="{tick_y_text:.2f}" '
                    f'text-anchor="middle" fill="#666666" font-size="9">{short}</text>'
                )

        parts.append("</svg>")
        return "".join(parts)


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from query import HistoryTrendQuery  # noqa: E402

    parser = argparse.ArgumentParser(description="TrendRenderer CLI")
    parser.add_argument("--hero", required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--until", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--format", choices=["spark", "spark-ascii", "md", "svg"], default="spark")
    args = parser.parse_args()

    q = HistoryTrendQuery(data_dir=args.data_dir) if args.data_dir else HistoryTrendQuery()
    trend = q.hero_trend(args.hero, args.days, until=args.until)
    renderer = TrendRenderer()

    if args.format == "spark":
        print(renderer.sparkline(trend))
    elif args.format == "spark-ascii":
        print(renderer.sparkline(trend, ascii_fallback=True))
    elif args.format == "md":
        print(renderer.markdown_table(trend))
    elif args.format == "svg":
        print(renderer.html_svg(trend))
