"""ai-news-radar — CLI entry point (P71.3).

Delegates to scripts/fetch_news.py (already has full argparse).

Usage:
  python __main__.py
  python __main__.py --lang zh-TW --limit 5
  python __main__.py --format json
  python __main__.py --topic "LLM" --format summary
  NO_COLOR=1 python __main__.py  # forces --format markdown
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))

# NO_COLOR → inject --format markdown before parsing
if os.environ.get("NO_COLOR") and "--format" not in sys.argv:
    sys.argv += ["--format", "markdown"]


def main() -> int:
    from fetch_news import main as _main
    asyncio.run(_main())
    return 0


if __name__ == "__main__":
    sys.exit(main())
