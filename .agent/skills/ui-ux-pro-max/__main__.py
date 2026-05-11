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


if __name__ == "__main__":
    main()
