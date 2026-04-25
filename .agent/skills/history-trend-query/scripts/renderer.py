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
_COLOR_ANOMALY = "#dc2626"   # S5 F7 anomaly overlay：紅圈外環

# S4 多軌 palette（5 色，與 query.py 上限呼應；首色維持桃紅領銜）
_MULTI_PALETTE = [
    "#db2777",  # 桃紅（旗艦主色）
    "#0ea5e9",  # 青
    "#f59e0b",  # 琥珀
    "#8b5cf6",  # 紫
    "#10b981",  # 翠
]


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
        anomaly_flags: Optional[List[bool]] = None,
    ) -> str:
        """
        參數 anomaly_flags（S5 F7）：
            可選 list[bool]，長度需等於 trend['points']；True 的位置在 ok 點外
            畫一圈紅色外環（{_COLOR_ANOMALY}）。長度不符會 raise ValueError。
            常與 anomaly_marker.mark_anomalies(trend['points']) 搭配使用。
        """
        points = trend.get("points", [])
        hero_raw = trend.get("hero", "—")
        hero = html.escape(str(hero_raw), quote=True)   # R15：防 XSS

        # S5 F7：anomaly_flags 長度與 points 必須一致（防呆）
        if anomaly_flags is not None and len(anomaly_flags) != len(points):
            raise ValueError(
                f"anomaly_flags 長度 {len(anomaly_flags)} 與 points 長度 "
                f"{len(points)} 不符"
            )
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
                # S5 F7：anomaly overlay 紅圈
                if anomaly_flags is not None and anomaly_flags[i]:
                    parts.append(
                        f'<circle cx="{_x(i):.2f}" cy="{_y(v):.2f}" r="7" '
                        f'fill="none" stroke="{_COLOR_ANOMALY}" '
                        f'stroke-width="1.5"><title>{title}: anomaly</title></circle>'
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

    # ────────────────────────────────────────────────────────────
    # S4 R16：多軌渲染（heroes_trend / platform_trend）
    # ────────────────────────────────────────────────────────────
    @staticmethod
    def _multi_extract_tracks(multi: Dict[str, Any]):
        """
        統一 heroes_trend / platform_trend 為 List[(track_name, points, value_key, normalized_key)]。
        """
        mode = multi.get("mode")
        if mode == "heroes":
            tracks = []
            for h in multi.get("heroes", []):
                tracks.append((h.get("hero", "—"), h.get("points", []),
                               "count", "normalized_count"))
            title = "多英雄聲量比對"
        elif mode == "platform":
            tracks = []
            for p_name, pts in (multi.get("platform_data") or {}).items():
                tracks.append((p_name, pts, "post_count", "normalized_count"))
            title = "平台別走勢"
        else:
            raise ValueError(
                f"render_multi 不支援 mode={mode!r}（限 'heroes' / 'platform'）"
            )
        return tracks, title

    def render_multi_svg(
        self,
        multi: Dict[str, Any],
        width: int = 720,
        height: int = 220,
        pad: int = 30,
    ) -> str:
        """多軌 SVG（多色 palette + 圖例 + x 軸刻度）。"""
        tracks, title = self._multi_extract_tracks(multi)
        rng = multi.get("range", {}) or {}
        full_title = (
            f'{title} — '
            f'{html.escape(str(rng.get("start", "")), quote=True)} ~ '
            f'{html.escape(str(rng.get("end", "")), quote=True)}'
        )

        if not tracks:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}"><text x="{width//2}" y="{height//2}" '
                f'text-anchor="middle" fill="{_COLOR_TEXT}" font-family="sans-serif">'
                f'no data</text></svg>'
            )

        # 共用 x 軸：取所有 track points 中第一條的長度當基準（query 層對齊過日期）
        n = max((len(pts) for _, pts, _, _ in tracks), default=0)
        if n == 0:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}"><text x="{width//2}" y="{height//2}" '
                f'text-anchor="middle" fill="{_COLOR_TEXT}" font-family="sans-serif">'
                f'no data</text></svg>'
            )

        legend_h = 22
        x_axis_h = 18
        inner_w = width - 2 * pad
        inner_h = height - pad - legend_h - x_axis_h - pad
        step = inner_w / (n - 1) if n > 1 else 0

        def _x(i: int) -> float:
            return pad + i * step if n > 1 else width / 2

        def _y(v: float) -> float:
            # v ∈ [0,1] normalized；y 軸由下往上增高
            return pad + inner_h - v * inner_h

        # 取 normalized 值（raw=True 模式下會 fallback 到原值，並做 on-the-fly 正規化以求視覺可比）
        raw_mode = bool(multi.get("raw", False))
        if raw_mode:
            # raw 模式：渲染端臨時 cross-normalize 以畫圖（不寫回 query 結果）
            all_vals = []
            for _, pts, vk, _ in tracks:
                for p in pts:
                    if p.get("status") == "ok" and isinstance(p.get(vk), (int, float)):
                        all_vals.append(float(p[vk]))
            if all_vals:
                lo_, hi_ = min(all_vals), max(all_vals)
                span_ = (hi_ - lo_) or 1.0
            else:
                lo_, span_ = 0.0, 1.0

            def _norm(p: Dict[str, Any], vk: str):
                v = p.get(vk)
                if not isinstance(v, (int, float)):
                    return None
                return (float(v) - lo_) / span_ if span_ else 0.5
        else:
            def _norm(p: Dict[str, Any], vk: str):
                _ = vk
                return p.get("normalized_count") if "normalized_count" in p else p.get("normalized_total")

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="sans-serif">',
            f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" '
            f'fill="white" stroke="{_COLOR_GRID}"/>',
            f'<text x="{pad}" y="{pad - 8}" fill="{_COLOR_TEXT}" font-size="12">'
            f'{html.escape(full_title, quote=True)}</text>',
        ]

        # 畫每一軌
        for ti, (name, pts, vk, _) in enumerate(tracks):
            color = _MULTI_PALETTE[ti % len(_MULTI_PALETTE)]
            name_safe = html.escape(str(name), quote=True)

            # 折線：相鄰兩點皆有 normalized 值才連
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                va, vb = _norm(a, vk), _norm(b, vk)
                if va is None or vb is None:
                    continue
                parts.append(
                    f'<line x1="{_x(i):.2f}" y1="{_y(va):.2f}" '
                    f'x2="{_x(i+1):.2f}" y2="{_y(vb):.2f}" '
                    f'stroke="{color}" stroke-width="1.5"/>'
                )
            # 點
            for i, p in enumerate(pts):
                v = _norm(p, vk)
                if v is None:
                    continue
                date_safe = html.escape(str(p.get("date", "")), quote=True)
                raw_v = p.get(vk)
                parts.append(
                    f'<circle cx="{_x(i):.2f}" cy="{_y(v):.2f}" r="3.5" '
                    f'fill="{color}"><title>{name_safe} {date_safe}: {raw_v}</title></circle>'
                )

        # x 軸刻度（用第一條軌的日期，所有軌 query 層已對齊）
        ref_pts = tracks[0][1]
        if n >= 1:
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
                tick_indices.append(n - 1)
            tick_y_line = pad + inner_h
            tick_y_text = tick_y_line + 12
            for i in tick_indices:
                date_str = str(ref_pts[i].get("date", "")) if i < len(ref_pts) else ""
                short = html.escape(
                    date_str[5:] if len(date_str) >= 10 else date_str, quote=True
                )
                parts.append(
                    f'<line x1="{_x(i):.2f}" y1="{tick_y_line:.2f}" '
                    f'x2="{_x(i):.2f}" y2="{tick_y_line + 3:.2f}" '
                    f'stroke="{_COLOR_GRID}" stroke-width="1"/>'
                )
                parts.append(
                    f'<text x="{_x(i):.2f}" y="{tick_y_text:.2f}" '
                    f'text-anchor="middle" fill="#666666" font-size="9">{short}</text>'
                )

        # S5 F6 R19：圖例自動換行——超出 width 邊界時折下一列、SVG height 動態擴增
        def _legend_width(name: Any) -> int:
            return max(80, len(str(name)) * 12 + 30)

        legend_layout: List[Dict[str, Any]] = []  # [{x, row, name, color}]
        cur_x = pad
        cur_row = 0
        right_bound = width - pad
        for ti, (name, _pts, _vk, _) in enumerate(tracks):
            w = _legend_width(name)
            if cur_x + w > right_bound and cur_x > pad:
                cur_x = pad
                cur_row += 1
            legend_layout.append({
                "x": cur_x,
                "row": cur_row,
                "name": name,
                "color": _MULTI_PALETTE[ti % len(_MULTI_PALETTE)],
            })
            cur_x += w

        legend_row_step = 16
        extra_h = max(0, cur_row) * legend_row_step
        final_height = height + extra_h

        # legend 起點 y 用「主圖區底部」為基準，避免被 x 軸刻度壓住
        legend_y_base = height - legend_h + 4
        for item in legend_layout:
            y_top = legend_y_base + item["row"] * legend_row_step
            name_safe = html.escape(str(item["name"]), quote=True)
            parts.append(
                f'<rect x="{item["x"]:.2f}" y="{y_top:.2f}" '
                f'width="10" height="10" fill="{item["color"]}"/>'
            )
            parts.append(
                f'<text x="{item["x"] + 14:.2f}" y="{y_top + 9:.2f}" '
                f'font-size="11" fill="{_COLOR_TEXT}">{name_safe}</text>'
            )

        parts.append("</svg>")

        # 動態 height：覆寫 SVG 開頭與背景框，使其反映 final_height
        if final_height != height:
            parts[0] = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{final_height}" '
                f'viewBox="0 0 {width} {final_height}" font-family="sans-serif">'
            )
            parts[1] = (
                f'<rect x="0.5" y="0.5" width="{width-1}" height="{final_height-1}" '
                f'fill="white" stroke="{_COLOR_GRID}"/>'
            )
        return "".join(parts)

    def render_multi_markdown(self, multi: Dict[str, Any]) -> str:
        """多軌 Markdown 表格：日期為列、各軌為欄。"""
        e = self._md_escape
        tracks, title = self._multi_extract_tracks(multi)
        rng = multi.get("range", {}) or {}

        if not tracks:
            return f"### {title}\n\n(no data)"

        # 統一日期軸（聯集保序，query 層通常已對齊）
        date_seen: List[str] = []
        seen: set = set()
        for _, pts, _, _ in tracks:
            for p in pts:
                d = p.get("date")
                if d and d not in seen:
                    seen.add(d)
                    date_seen.append(d)

        if not date_seen:
            return f"### {title}\n\n(no data)"

        track_names_e = [e(name) for name, _, _, _ in tracks]
        header = "| 日期 | " + " | ".join(track_names_e) + " |"
        sep = "|------|" + "------|" * len(tracks)
        lines = [
            f"### {e(title)} — {e(rng.get('start', ''))} ~ {e(rng.get('end', ''))}",
            "",
            header,
            sep,
        ]

        for d in date_seen:
            cells: List[str] = [e(d)]
            for _name, pts, vk, _ in tracks:
                cell = "—"
                for p in pts:
                    if p.get("date") == d:
                        st = p.get("status")
                        if st == "ok":
                            v = p.get(vk)
                            cell = str(v) if v is not None else "—"
                        elif st in ("hero_absent", "absent"):
                            cell = "·"
                        elif st == "missing":
                            cell = "—"
                        elif st == "invalid":
                            cell = "⚠"
                        else:
                            cell = e(str(st))
                        break
                cells.append(cell)
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from query import HistoryTrendQuery  # noqa: E402

    parser = argparse.ArgumentParser(description="TrendRenderer CLI")
    parser.add_argument("--mode", choices=["hero", "heroes", "overall", "platform"], default="hero")
    parser.add_argument("--hero", help="mode=hero")
    parser.add_argument("--heroes", help="mode=heroes，逗號分隔")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--until", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument(
        "--format",
        choices=["spark", "spark-ascii", "md", "svg", "multi-svg", "multi-md"],
        default="spark",
    )
    parser.add_argument("--raw", action="store_true")
    args = parser.parse_args()

    q = HistoryTrendQuery(data_dir=args.data_dir) if args.data_dir else HistoryTrendQuery()
    renderer = TrendRenderer()

    if args.mode == "hero":
        if not args.hero:
            parser.error("--mode=hero 需要 --hero")
        trend = q.hero_trend(args.hero, args.days, until=args.until)
        if args.format == "spark":
            print(renderer.sparkline(trend))
        elif args.format == "spark-ascii":
            print(renderer.sparkline(trend, ascii_fallback=True))
        elif args.format == "md":
            print(renderer.markdown_table(trend))
        elif args.format == "svg":
            print(renderer.html_svg(trend))
        else:
            parser.error(f"--mode=hero 不支援 format={args.format}")
    else:
        if args.mode == "heroes":
            if not args.heroes:
                parser.error("--mode=heroes 需要 --heroes")
            names = [s.strip() for s in args.heroes.split(",") if s.strip()]
            multi = q.heroes_trend(names, args.days, until=args.until, raw=args.raw)
        elif args.mode == "overall":
            multi = q.overall_trend(args.days, until=args.until, raw=args.raw)
        else:
            multi = q.platform_trend(args.days, until=args.until, raw=args.raw)

        if args.mode == "overall":
            # overall_trend 是單軌語意（無多 hero/platform），用 markdown_table 略；這裡 fallback
            print(json.dumps(multi, ensure_ascii=False, indent=2))
        elif args.format == "multi-svg":
            print(renderer.render_multi_svg(multi))
        elif args.format == "multi-md":
            print(renderer.render_multi_markdown(multi))
        else:
            parser.error(f"--mode={args.mode} 請用 --format multi-svg 或 multi-md")
