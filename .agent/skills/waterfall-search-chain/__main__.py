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


def _run_with_metrics() -> None:
    import time as _time
    _t0 = _time.perf_counter()
    _rc = 0
    try:
        _ret = main()
        _rc = _ret if isinstance(_ret, int) else 0
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else (0 if _e.code is None else 1)
    except Exception:
        _rc = 1
    finally:
        _dur = (_time.perf_counter() - _t0) * 1000
    try:
        _scripts = str(Path(__file__).resolve().parents[3] / "scripts")
        if _scripts not in sys.path:
            sys.path.insert(0, _scripts)
        from skill_metrics_logger import record as _rec
        _rec("waterfall-search-chain", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
