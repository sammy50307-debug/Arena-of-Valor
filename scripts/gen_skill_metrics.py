"""gen_skill_metrics.py — P72.0: O1/O2/O3 metrics reader.

Reads ~/.claude/skill_metrics.jsonl and produces a summary table.

Usage:
    python scripts/gen_skill_metrics.py
    python scripts/gen_skill_metrics.py --output json
    python scripts/gen_skill_metrics.py --last 7d
    python scripts/gen_skill_metrics.py --skill history-trend-query
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_metrics_logger import METRICS_FILE, load_all, summarize


def _parse_window(window: str) -> datetime | None:
    """Parse '7d', '30d', '24h' → cutoff datetime (UTC). None = no filter."""
    if not window:
        return None
    unit = window[-1].lower()
    try:
        n = int(window[:-1])
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    if unit == "d":
        return now - timedelta(days=n)
    if unit == "h":
        return now - timedelta(hours=n)
    return None


def _filter_records(records: list[dict], cutoff: datetime | None, skill: str | None) -> list[dict]:
    out = []
    for r in records:
        if skill and r.get("skill") != skill:
            continue
        if cutoff:
            try:
                ts = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
                if ts < cutoff:
                    continue
            except Exception:
                pass
        out.append(r)
    return out


def _render_table(stats: dict[str, dict]) -> str:
    if not stats:
        return "(no data — run a skill via __main__.py first)"
    header = "| Skill | Calls | Fail% | Avg ms | Tok-in | Tok-out |"
    sep    = "|---|---:|---:|---:|---:|---:|"
    rows = []
    for skill, s in sorted(stats.items()):
        fail = f"{s['failure_rate_pct']:.1f}%"
        rows.append(
            f"| {skill} | {s['calls']} | {fail} | {s['avg_duration_ms']} |"
            f" {s['avg_tokens_in']} | {s['avg_tokens_out']} |"
        )
    return "\n".join([header, sep] + rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="P72.0 Skill Metrics — O1/O2/O3 summary")
    parser.add_argument("--output", choices=["table", "json"], default="table")
    parser.add_argument("--last", default="", metavar="WINDOW",
                        help="Time window: 7d / 24h / 30d (default: all time)")
    parser.add_argument("--skill", default="", help="Filter to one skill name")
    args = parser.parse_args()

    if not METRICS_FILE.exists():
        print(f"⚠️  metrics log not found: {METRICS_FILE}")
        print("   Run any skill via its __main__.py to start collecting data.")
        return 0

    records = load_all()
    cutoff = _parse_window(args.last)
    records = _filter_records(records, cutoff, args.skill or None)

    stats = summarize(records)

    window_label = f"last {args.last}" if args.last else "all time"
    skill_label = f" / skill={args.skill}" if args.skill else ""

    if args.output == "json":
        print(json.dumps({"window": window_label, "stats": stats}, ensure_ascii=False, indent=2))
        return 0

    print(f"# Skill Metrics — {window_label}{skill_label}")
    print(f"# Source: {METRICS_FILE}")
    print(f"# Total records: {len(records)}")
    print()
    print(_render_table(stats))
    print()
    print("Columns: Calls / Fail% (O2) / Avg ms (O1) / Tok-in avg (O3) / Tok-out avg (O3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
