"""semantic-cache-shield — CLI entry point (P71.3).

Usage:
  python __main__.py stats
  python __main__.py lookup "芽芽最近走勢"
  python __main__.py store "芽芽最近走勢" "回答內容..."
  python __main__.py stats --output json
  NO_COLOR=1 python __main__.py stats
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


def cmd_stats(args: argparse.Namespace) -> int:
    from cache_engine import SemanticCacheShield
    mode = _output_mode(args.output)
    c = SemanticCacheShield()
    stats = c.get_stats() if hasattr(c, "get_stats") else {"note": "stats() not available"}
    if mode == "json":
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        for k, v in stats.items():
            print(f"{k}: {v}")
    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    from cache_engine import SemanticCacheShield
    mode = _output_mode(args.output)
    c = SemanticCacheShield()
    query = " ".join(args.query)
    hit = c.lookup(query) if hasattr(c, "lookup") else None
    if mode == "json":
        print(json.dumps({"query": query, "hit": hit}, ensure_ascii=False, indent=2))
    else:
        if hit:
            print(f"[CACHE HIT]\n{hit}")
        else:
            print("[CACHE MISS]")
    return 0


def cmd_store(args: argparse.Namespace) -> int:
    from cache_engine import SemanticCacheShield
    c = SemanticCacheShield()
    query = args.query
    response = " ".join(args.response)
    if hasattr(c, "store"):
        c.store(query, response)
        print(f"[semantic-cache-shield] 已儲存：{query[:40]}...")
    else:
        print("[semantic-cache-shield] store() not available", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="semantic-cache-shield",
        description="語意快取護盾 — LLM 回應語意去重快取",
    )
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    sub = parser.add_subparsers(dest="cmd", help="操作")

    p_stats = sub.add_parser("stats", help="查詢快取統計")
    p_stats.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_stats.set_defaults(func=cmd_stats)

    p_lookup = sub.add_parser("lookup", help="查詢快取命中")
    p_lookup.add_argument("query", nargs="+", help="查詢字串")
    p_lookup.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_lookup.set_defaults(func=cmd_lookup)

    p_store = sub.add_parser("store", help="儲存查詢結果至快取")
    p_store.add_argument("query", help="查詢字串")
    p_store.add_argument("response", nargs="+", help="回應內容")
    p_store.set_defaults(func=cmd_store)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
