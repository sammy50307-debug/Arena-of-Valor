"""rich-push-formatter — CLI entry point (P71.9).

Usage:
  python __main__.py path/to/diff.json       # 格式化 diff JSON
  python __main__.py path/to/analysis.json --mode analysis
  echo '{}' | python __main__.py --stdin
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))


def main() -> None:
    parser = argparse.ArgumentParser(description="rich-push-formatter: JSON → Markdown 日報")
    parser.add_argument("input_file", nargs="?", help="輸入 JSON 檔路徑")
    parser.add_argument("--mode", choices=["diff", "analysis"], default="diff",
                        help="輸入格式 (default: diff)")
    parser.add_argument("--stdin", action="store_true", help="從 stdin 讀取 JSON")
    args = parser.parse_args()

    from formatter import RichPushFormatter

    if args.stdin:
        data = json.load(sys.stdin)
    elif args.input_file:
        data = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    else:
        parser.print_help()
        sys.exit(1)

    print("[rich-push-formatter 已啟動]")
    fmt = RichPushFormatter()
    if args.mode == "diff":
        print(fmt.format_diff(data))
    else:
        print(fmt.format_analysis(data))


if __name__ == "__main__":
    main()
