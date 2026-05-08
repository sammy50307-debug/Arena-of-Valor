"""api-quota-guardian — CLI entry point (P71.3).

Usage:
  python __main__.py status
  python __main__.py status --provider tavily --output json
  python __main__.py record --count 5
  python __main__.py reset
  NO_COLOR=1 python __main__.py status
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


def _fmt(data: dict, mode: str) -> str:
    if mode == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)
    lines = []
    for k, v in data.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)


def cmd_status(args: argparse.Namespace) -> int:
    from guardian import APIQuotaGuardian
    mode = _output_mode(args.output)
    g = APIQuotaGuardian(provider=args.provider, monthly_limit=args.limit)
    info = g.status()
    print(_fmt(info, mode))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    from guardian import APIQuotaGuardian
    mode = _output_mode(args.output)
    g = APIQuotaGuardian(provider=args.provider, monthly_limit=args.limit)
    info = g.record(count=args.count)
    print(_fmt(info, mode))
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    from guardian import APIQuotaGuardian
    g = APIQuotaGuardian(provider=args.provider, monthly_limit=args.limit)
    g.reset()
    print(f"[api-quota-guardian] {args.provider} 額度已重置")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="api-quota-guardian",
        description="Tavily API 月額度守衛 — 追蹤用量、80%/95% 門檻警示",
    )
    parser.add_argument("--provider", default="tavily", help="API 提供商（預設 tavily）")
    parser.add_argument("--limit", type=int, default=1000, metavar="N", help="月額度上限（預設 1000）")
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    sub = parser.add_subparsers(dest="cmd", help="操作")

    p_status = sub.add_parser("status", help="查詢當前額度狀態")
    p_status.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_status.set_defaults(func=cmd_status)

    p_record = sub.add_parser("record", help="記錄 API 呼叫次數")
    p_record.add_argument("--count", type=int, default=1, help="本次呼叫次數（預設 1）")
    p_record.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_record.set_defaults(func=cmd_record)

    p_reset = sub.add_parser("reset", help="重置本月額度計數")
    p_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
