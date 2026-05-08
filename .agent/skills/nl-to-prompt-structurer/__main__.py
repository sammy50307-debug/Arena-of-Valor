"""nl-to-prompt-structurer — CLI entry point (P71.3).

Delegates to scripts/cli.py (Phase 62 S4 完整 CLI).

Usage:
  python __main__.py prompt "用 markdown 整理今天戰報"
  python __main__.py prompt --stdin
  python __main__.py prompt --lang en --role Translator "translate this"
  python __main__.py route "芽芽最近兩週的聲量"
  python __main__.py route --stdin
  echo "整理戰報" | python __main__.py prompt --stdin
"""
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from scripts.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
