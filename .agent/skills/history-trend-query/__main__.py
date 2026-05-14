"""history-trend-query — CLI entry point (P71.3).

Usage:
  python __main__.py hero 芽芽 --days 7
  python __main__.py heroes 芽芽 雷獅 --days 14
  python __main__.py overall --days 7
  python __main__.py platform --days 7
  python __main__.py hero 芽芽 --output json
  NO_COLOR=1 python __main__.py hero 芽芽  # plain mode
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


def _run_hero(args: argparse.Namespace) -> int:
    from query import HistoryTrendQuery
    from renderer import TrendRenderer

    mode = _output_mode(args.output)
    q = HistoryTrendQuery(data_dir=_SKILL_DIR.parent.parent.parent / "data")
    result = q.hero_trend(hero=args.hero, days=args.days)

    if mode == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    r = TrendRenderer()
    if mode == "plain":
        print(r.markdown_table(result))
    else:
        print(r.sparkline(result))
        print(r.markdown_table(result))
    return 0


def _run_heroes(args: argparse.Namespace) -> int:
    from query import HistoryTrendQuery
    from renderer import TrendRenderer

    mode = _output_mode(args.output)
    q = HistoryTrendQuery(data_dir=_SKILL_DIR.parent.parent.parent / "data")
    result = q.heroes_trend(heroes=args.heroes, days=args.days)

    if mode == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    r = TrendRenderer()
    print(r.render_multi_markdown(result))
    return 0


def _run_overall(args: argparse.Namespace) -> int:
    from query import HistoryTrendQuery
    from renderer import TrendRenderer

    mode = _output_mode(args.output)
    q = HistoryTrendQuery(data_dir=_SKILL_DIR.parent.parent.parent / "data")
    result = q.overall_trend(days=args.days)

    if mode == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    r = TrendRenderer()
    print(r.markdown_table(result))
    return 0


def _run_platform(args: argparse.Namespace) -> int:
    from query import HistoryTrendQuery
    from renderer import TrendRenderer

    mode = _output_mode(args.output)
    q = HistoryTrendQuery(data_dir=_SKILL_DIR.parent.parent.parent / "data")
    result = q.platform_trend(days=args.days)

    if mode == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    r = TrendRenderer()
    print(r.markdown_table(result))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="history-trend-query",
        description="查詢英雄 / 整體輿情 / 平台別走勢（P61 時序引擎）",
    )
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )
    sub = parser.add_subparsers(dest="cmd", help="查詢模式")

    # hero
    p_hero = sub.add_parser("hero", help="單英雄走勢")
    p_hero.add_argument("hero", help="英雄名稱，例：芽芽")
    p_hero.add_argument("--days", type=int, default=7, metavar="N", help="查詢天數（預設 7）")
    p_hero.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_hero.set_defaults(func=_run_hero)

    # heroes
    p_heroes = sub.add_parser("heroes", help="多英雄比較走勢（最多 5 個）")
    p_heroes.add_argument("heroes", nargs="+", help="英雄名稱列表")
    p_heroes.add_argument("--days", type=int, default=7, metavar="N")
    p_heroes.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_heroes.set_defaults(func=_run_heroes)

    # overall
    p_overall = sub.add_parser("overall", help="整體輿情走勢")
    p_overall.add_argument("--days", type=int, default=7, metavar="N")
    p_overall.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_overall.set_defaults(func=_run_overall)

    # platform
    p_platform = sub.add_parser("platform", help="平台別走勢")
    p_platform.add_argument("--days", type=int, default=7, metavar="N")
    p_platform.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_platform.set_defaults(func=_run_platform)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

    # --output at top-level overrides subcommand default
    if args.output and not getattr(args, "output", None):
        args.output = args.output

    return args.func(args)


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
        _rec("history-trend-query", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
