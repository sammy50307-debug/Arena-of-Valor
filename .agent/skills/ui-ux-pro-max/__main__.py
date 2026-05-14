"""ui-ux-pro-max — CLI entry point (P71.9).

Usage:
  python __main__.py list               # 列出可用的設計類別
  python __main__.py styles             # 列出 50 種 UI 風格
  python __main__.py palettes           # 列出 21 種配色盤
  python __main__.py fonts              # 列出字體配對建議
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))


def main() -> None:
    parser = argparse.ArgumentParser(description="ui-ux-pro-max: UI/UX 設計情報庫")
    parser.add_argument("category", nargs="?", default="list",
                        choices=["list", "styles", "palettes", "fonts", "charts", "stacks"],
                        help="查詢類別 (default: list)")
    parser.add_argument("--query", default="", help="關鍵字篩選")
    args = parser.parse_args()

    print("[ui-ux-pro-max 已啟動]")

    try:
        from core import UIUXProMax
        lib = UIUXProMax()
    except Exception:
        lib = None

    if args.category == "list":
        print("可用類別：styles / palettes / fonts / charts / stacks")
        return

    if lib and hasattr(lib, args.category):
        items = getattr(lib, args.category)
        if args.query:
            items = [i for i in items if args.query.lower() in str(i).lower()]
        for item in items:
            print(f"  {item}")
    else:
        print(f"（{args.category} 類別尚無資料，請直接向 LLM 詢問設計建議）")


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
        _rec("ui-ux-pro-max", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
