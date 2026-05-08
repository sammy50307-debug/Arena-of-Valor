"""firecrawl-dynamic-breacher — CLI entry point (P71.3).

Usage:
  python __main__.py https://example.com
  python __main__.py https://example.com --wait 5000
  python __main__.py https://example.com --output json
  echo "https://example.com" | python __main__.py --stdin
  NO_COLOR=1 python __main__.py https://example.com
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


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="firecrawl-dynamic-breacher",
        description="透過 Firecrawl API 渲染 JS 動態網頁並提取 Markdown",
    )
    parser.add_argument("url", nargs="?", help="目標 URL")
    parser.add_argument("--stdin", action="store_true", help="從 stdin 讀取 URL")
    parser.add_argument("--wait", type=int, default=3000, metavar="MS", help="等待 JS 執行的毫秒數（預設 3000）")
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    args = parser.parse_args()
    mode = _output_mode(args.output)

    if args.stdin:
        url = sys.stdin.read().strip()
    elif args.url:
        url = args.url
    else:
        parser.print_help()
        return 1

    from breacher import FirecrawlBreacher
    b = FirecrawlBreacher()
    markdown = b.breach_and_extract(url, wait_time=args.wait)

    if mode == "json":
        print(json.dumps({"url": url, "markdown": markdown}, ensure_ascii=False, indent=2))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
