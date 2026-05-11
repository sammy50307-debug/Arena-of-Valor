"""waterfall-search-chain — CLI entry point (P71.9).

Usage:
  python __main__.py "傳說對決 芽芽削弱"
  python __main__.py "query" --max-results 5
  python __main__.py "query" --output json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SKILL_DIR.parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_SKILL_DIR / "scripts"))


def main() -> None:
    parser = argparse.ArgumentParser(description="waterfall-search-chain: Tavily→DDG 瀑布備援搜尋")
    parser.add_argument("query", help="搜尋關鍵字")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    print(f"[waterfall-search-chain 已啟動] 搜尋：{args.query}")

    try:
        from waterfall import WaterfallSearcher
        searcher = WaterfallSearcher()
    except ImportError:
        # fallback: scrapers.waterfall_searcher
        from scrapers.waterfall_searcher import WaterfallSearcher
        searcher = WaterfallSearcher()

    results = searcher.search(args.query, max_results=args.max_results)

    if args.output == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for i, r in enumerate(results, 1):
        title = r.get("title", r.get("url", "—"))
        url = r.get("url", "")
        print(f"  {i}. {title}")
        if url:
            print(f"     {url}")


if __name__ == "__main__":
    main()
