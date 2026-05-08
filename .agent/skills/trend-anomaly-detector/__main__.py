"""trend-anomaly-detector — CLI entry point (P71.3).

Usage:
  python __main__.py 100 120 95 110 300
  echo "[100, 120, 95, 110, 300]" | python __main__.py --stdin
  python __main__.py 100 120 95 110 300 --output json
  python __main__.py 100 120 300 --red 2.5 --yellow 1.5
  NO_COLOR=1 python __main__.py 100 120 300
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))


def _output_mode(forced: str | None) -> str:
    if forced:
        return forced
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return "plain"
    return "rich"


_ALERT_EMOJI = {"none": "✅", "yellow": "🟡", "red": "🔴"}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="trend-anomaly-detector",
        description="輿情核爆觀測儀 — Z-Score 異常偵測，最後一個數值為待判斷點",
    )
    parser.add_argument(
        "values", nargs="*", type=float,
        help="數值序列（最後一個為當前值，其餘為歷史基準）",
    )
    parser.add_argument("--stdin", action="store_true",
                        help="從 stdin 讀取 JSON 數列，例：[100, 120, 300]")
    parser.add_argument("--red", type=float, default=3.0, metavar="Z",
                        help="紅色警報 Z-Score 閾值（預設 3.0）")
    parser.add_argument("--yellow", type=float, default=2.0, metavar="Z",
                        help="黃色警報 Z-Score 閾值（預設 2.0）")
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    args = parser.parse_args()
    mode = _output_mode(args.output)

    if args.stdin:
        raw = sys.stdin.read().strip()
        try:
            values = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[Error] stdin 必須是 JSON 數列，例 [100, 120, 300]：{e}", file=sys.stderr)
            return 1
    elif args.values:
        values = args.values
    else:
        parser.print_help()
        return 1

    if len(values) < 2:
        print("[Error] 至少需要 2 個數值（1 個歷史 + 1 個當前）", file=sys.stderr)
        return 1

    from anomaly_detector import TrendAnomalyDetector
    d = TrendAnomalyDetector(
        red_alert_threshold=args.red,
        yellow_alert_threshold=args.yellow,
    )
    historical = values[:-1]
    current = values[-1]
    raw = d.detect(historical, current)

    result = {
        "current": raw.get("current_value", current),
        "historical_count": len(historical),
        "baseline_mean": raw.get("baseline_mean", 0),
        "baseline_std": raw.get("baseline_std", 0),
        "z_score": raw.get("z_score", 0),
        "severity": raw.get("severity", "UNKNOWN"),
        "trigger_alert": raw.get("trigger_alert", False),
    }
    severity = result["severity"]

    if mode == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emoji = "🔴" if "RED" in severity else ("🟡" if "YELLOW" in severity else "✅")
        print(f"{emoji} {severity}  Z-Score={result['z_score']}")
        print(f"   當前值：{current}  歷史均值：{result['baseline_mean']}  σ：{result['baseline_std']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
