"""
Rich Push Formatter — 戰報推播格式化儀。

把 daily-diff-radar 輸出的 diff dict 或單日 analysis JSON，
轉成人類可讀的 Markdown 日報，含 emoji 警戒燈號與 Δ 箭頭。
"""

import sys
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


ALERT_EMOJI = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}


def arrow(delta, fmt: str = "+.2f") -> str:
    """回傳含方向箭頭的 Δ 字串。fmt='+d' 表示整數格式。"""
    if "d" in fmt:
        delta = int(delta)
        val = f"{delta:{fmt}}"
    else:
        val = f"{float(delta):{fmt}}"
    if delta > 0:
        return f"⬆️ {val}"
    if delta < 0:
        return f"⬇️ {val}"
    return f"➡️ {val}"


class RichPushFormatter:
    """把冷冰冰的 JSON 變成會說話的日報。"""

    def format_diff(self, diff: Dict) -> str:
        """將 daily-diff-radar 的輸出轉成 Markdown。"""
        if "error" in diff:
            return f"⚠️ **雷達錯誤**：{diff['error']}"

        alert = diff.get("alert_level", "LOW")
        emoji = ALERT_EMOJI.get(alert, "⚪")

        today = diff.get("today_date", "?")
        yesterday = diff.get("yesterday_date", "?")

        lines: List[str] = []
        lines.append(f"# {emoji} 芽芽戰情室每日簡報 · {today}")
        lines.append("")
        lines.append(f"> 對照日期：**{yesterday} → {today}** ｜ 警戒等級：**{alert}**")
        lines.append("")

        # ── 總體指標 ──
        lines.append("## 📊 總體指標")
        lines.append("")
        lines.append("| 指標 | 變化 |")
        lines.append("|------|------|")
        lines.append(f"| 情緒分數 Δ | {arrow(diff.get('sentiment_delta', 0), '+.3f')} |")
        vol_delta = diff.get("volume_delta", 0)
        vol_pct = diff.get("volume_delta_pct", 0)
        vol_arrow = arrow(vol_delta, "+d")
        lines.append(f"| 聲量 Δ | {vol_arrow}（{vol_pct:+.1f}%）|")
        lines.append(f"| 趨勢 | {diff.get('trend_change', 'N/A')} |")
        lines.append("")

        # ── 英雄變動 ──
        new_heroes = diff.get("new_heroes", [])
        dropped = diff.get("dropped_heroes", [])
        shifts = diff.get("hero_sentiment_shifts", {})

        if new_heroes or dropped or shifts:
            lines.append("## 🦸 英雄動態")
            lines.append("")
            if new_heroes:
                lines.append(f"- **新上榜**：{'、'.join(new_heroes)}")
            if dropped:
                lines.append(f"- **下榜**：{'、'.join(dropped)}")
            if shifts:
                lines.append("- **情緒變動 Top**：")
                for hero, d in list(shifts.items())[:5]:
                    lines.append(f"  - {hero} {arrow(d, '+.2f')}")
            lines.append("")

        # ── 平台變化 ──
        plat = diff.get("platform_changes", {})
        if plat:
            lines.append("## 📡 各平台聲量")
            lines.append("")
            lines.append("| 平台 | 昨日 | 今日 | Δ |")
            lines.append("|------|------|------|---|")
            for name, stats in plat.items():
                d = stats.get("delta", 0)
                lines.append(
                    f"| {name} | {stats.get('yesterday', 0)} | "
                    f"{stats.get('today', 0)} | {arrow(d, '+d')} |"
                )
            lines.append("")

        lines.append("---")
        lines.append("*由 rich-push-formatter 自動產生*")
        return "\n".join(lines)

    def format_analysis(self, analysis: Dict, date: Optional[str] = None) -> str:
        """將單日 analysis JSON 轉成 briefing Markdown。"""
        overall = analysis.get("overall", {})
        sentiment = overall.get("sentiment_score", 0)
        trend = overall.get("trend", "Unknown")
        total = analysis.get("total_posts", 0)

        date_str = date or analysis.get("date", "今日")

        lines: List[str] = []
        lines.append(f"# 📋 {date_str} AOV 輿情快照")
        lines.append("")
        lines.append(f"- **總貼文數**：{total}")
        lines.append(f"- **情緒分數**：{sentiment:.2f}")
        lines.append(f"- **趨勢**：{trend}")
        lines.append("")

        heroes = analysis.get("hero_stats", {})
        if heroes:
            lines.append("## 🦸 Top 英雄")
            lines.append("")
            lines.append("| 英雄 | 平均情緒 |")
            lines.append("|------|---------|")
            top = sorted(
                heroes.items(),
                key=lambda kv: kv[1].get("avg_sentiment", 0),
                reverse=True,
            )[:5]
            for name, stats in top:
                lines.append(f"| {name} | {stats.get('avg_sentiment', 0):+.2f} |")
            lines.append("")

        plat = analysis.get("platform_breakdown", {})
        if plat:
            lines.append("## 📡 平台分布")
            lines.append("")
            for name, stats in plat.items():
                lines.append(f"- {name}：{stats.get('post_count', 0)} 則")
            lines.append("")

        return "\n".join(lines)


if __name__ == "__main__":
    # 示範輸出
    demo = {
        "today_date": "2026-04-19",
        "yesterday_date": "2026-04-18",
        "sentiment_delta": 0.15,
        "volume_delta": 8,
        "volume_delta_pct": 40.0,
        "trend_change": "Stable → Upward",
        "new_heroes": ["克里希", "凱恩"],
        "dropped_heroes": ["悟空"],
        "hero_sentiment_shifts": {"芽芽": 0.2, "超人": -0.15},
        "platform_changes": {
            "dcard": {"today": 12, "yesterday": 8, "delta": 4},
            "bahamut": {"today": 6, "yesterday": 7, "delta": -1},
        },
        "alert_level": "MEDIUM",
    }
    print(RichPushFormatter().format_diff(demo))
