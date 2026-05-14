"""cot-prompt-compactor — CLI entry point (P71.9).

Usage:
  python __main__.py list               # 列出可用的 compact prompt 模板
  python __main__.py single-post        # 印出單篇分析用 compact prompt
  python __main__.py daily-summary      # 印出每日彙總用 compact prompt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))


def main() -> None:
    parser = argparse.ArgumentParser(description="cot-prompt-compactor: Pydantic 結構化 Prompt 模板庫")
    parser.add_argument("template", nargs="?", default="list",
                        choices=["list", "single-post", "daily-summary"],
                        help="要印出的 prompt 模板 (default: list)")
    args = parser.parse_args()

    import compactor

    print("[cot-prompt-compactor 已啟動]")

    if args.template == "list":
        print("可用模板：")
        print("  single-post   — 單篇貼文情緒分析（含 CoT 推論）")
        print("  daily-summary — 每日輿情彙總報告")
        return

    if args.template == "single-post":
        prompt = getattr(compactor, "SYSTEM_SINGLE_POST_COMPACT", None)
    else:
        prompt = getattr(compactor, "SYSTEM_DAILY_SUMMARY_COMPACT", None)

    if prompt:
        print(prompt)
    else:
        print(f"找不到模板：{args.template}", file=sys.stderr)
        sys.exit(1)


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
        _rec("cot-prompt-compactor", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
