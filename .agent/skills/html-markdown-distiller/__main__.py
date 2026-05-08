"""html-markdown-distiller — CLI entry point (P71.3).

Usage:
  python __main__.py --input page.html
  python __main__.py --input page.html --output result.md
  cat page.html | python __main__.py --stdin
  python __main__.py --stdin --output-format json < page.html
  NO_COLOR=1 python __main__.py --stdin < page.html
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
        prog="html-markdown-distiller",
        description="HTML → Markdown 精餾器，清除雜訊保留正文",
    )
    parser.add_argument("--input", "-i", help="輸入 HTML 檔案路徑")
    parser.add_argument("--stdin", action="store_true", help="從 stdin 讀取 HTML（pipe 模式）")
    parser.add_argument("--output", "-o", help="輸出 Markdown 檔案路徑（不填則印至 stdout）")
    parser.add_argument(
        "--output-format", choices=["json", "plain", "rich"], default=None,
        dest="output_format",
        help="stdout 輸出格式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    args = parser.parse_args()
    mode = _output_mode(args.output_format)

    if args.stdin:
        html_data = sys.stdin.read()
    elif args.input:
        try:
            html_data = Path(args.input).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"[Error] 找不到檔案：{args.input}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 1

    from html_to_md import HTMLDistiller
    distiller = HTMLDistiller()
    result_md = distiller.process(html_data)

    if args.output:
        Path(args.output).write_text(result_md, encoding="utf-8")
        print(f"[Success] 已儲存至 {args.output}")
        return 0

    if mode == "json":
        print(json.dumps({"markdown": result_md}, ensure_ascii=False, indent=2))
    else:
        print(result_md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
