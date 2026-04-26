"""CLI 入口 — Phase 62 S4 安全命令列（解 R15）。

子命令：
  prompt  — 自然語言 → 五段式 Markdown Prompt
  route   — 自然語言 → P61 呼叫規格 JSON

支援 positional arg 或 --stdin，徹底免疫單引號/換行等 shell 元字元。

用法：
  py cli.py prompt "用 markdown 整理今天戰報"
  py cli.py prompt --stdin                       # 從 stdin 讀取
  py cli.py prompt --lang en --role Translator "translate this"
  py cli.py route "芽芽最近兩週的聲量"
  py cli.py route --stdin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 確保 scripts/ 的父目錄在 sys.path 中
_HERE = Path(__file__).resolve().parent
_SKILL_DIR = _HERE.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from scripts.structurer import PromptStructurer
from scripts.query_router import route_query


def _read_text(args: argparse.Namespace) -> str:
    """從 args.text 或 stdin 讀取輸入文字。"""
    if getattr(args, "stdin", False):
        return sys.stdin.read().strip()
    text_parts = getattr(args, "text", [])
    if isinstance(text_parts, list):
        return " ".join(text_parts).strip()
    return str(text_parts or "").strip()


def cmd_prompt(args: argparse.Namespace) -> int:
    """子命令 prompt：結構化 Prompt 生成。"""
    text = _read_text(args)
    s = PromptStructurer()
    md = s.structure(
        text,
        lang=getattr(args, "lang", None),
        role=getattr(args, "role", None),
        mode=getattr(args, "mode", "full"),
        context=getattr(args, "context", None),
    )
    print(md)
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    """子命令 route：查詢路由。"""
    text = _read_text(args)
    result = route_query(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NL-to-Prompt Structurer CLI（Phase 62 S4）",
        prog="cli.py",
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # prompt 子命令
    p_prompt = sub.add_parser("prompt", help="自然語言 → 五段式 Markdown Prompt")
    p_prompt.add_argument("text", nargs="*", default=[], help="輸入文字（可多詞）")
    p_prompt.add_argument("--stdin", action="store_true", help="從 stdin 讀取（安全模式）")
    p_prompt.add_argument("--lang", choices=["zh", "en"], default=None, help="強制語言")
    p_prompt.add_argument("--role", default=None, help="覆寫角色")
    p_prompt.add_argument("--mode", choices=["full", "lite"], default="full", help="輸出模式")
    p_prompt.add_argument("--context", default=None, help="補背景")
    p_prompt.set_defaults(func=cmd_prompt)

    # route 子命令
    p_route = sub.add_parser("route", help="自然語言 → P61 呼叫規格 JSON")
    p_route.add_argument("text", nargs="*", default=[], help="查詢文字")
    p_route.add_argument("--stdin", action="store_true", help="從 stdin 讀取")
    p_route.set_defaults(func=cmd_route)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
