"""hallucination-judge — CLI entry point (P71.3).

Usage:
  python __main__.py "芽芽勝率 85%，雷獅討論量 1234"
  echo "文章內容..." | python __main__.py --stdin
  python __main__.py "文字" --output json
  NO_COLOR=1 python __main__.py "文字"
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


def _fmt_result(result: dict, mode: str) -> str:
    if mode == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    lines = []
    verdict = result.get("verdict", "UNKNOWN")
    score = result.get("confidence_score", 0)
    emoji = "✅" if verdict == "PASS" else ("⚠️" if verdict == "WARN" else "❌")
    lines.append(f"{emoji} 判決：{verdict}  可信度：{score}/100")
    for issue in result.get("issues", []):
        lines.append(f"  - {issue}")
    if not result.get("issues"):
        lines.append("  （無問題）")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="hallucination-judge",
        description="校驗 AI 生成戰報中英雄名稱與數值合理性",
    )
    parser.add_argument(
        "text", nargs="*", default=[],
        help="要校驗的文字（可多段，空白分隔）",
    )
    parser.add_argument("--stdin", action="store_true", help="從 stdin 讀取輸入（pipe 模式）")
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    args = parser.parse_args()
    mode = _output_mode(args.output)

    if args.stdin:
        text = sys.stdin.read().strip()
    elif args.text:
        text = " ".join(args.text).strip()
    else:
        parser.print_help()
        return 1

    from judge import HallucinationJudge
    j = HallucinationJudge()
    result = j.judge(text)
    print(_fmt_result(result, mode))
    return 0 if result.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
