"""hot-deployer — CLI entry point (P71.3).

Usage:
  python __main__.py deploy
  python __main__.py deploy --dry-run
  python __main__.py deploy --output json
  NO_COLOR=1 python __main__.py deploy --dry-run
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


def _fmt(result: dict, mode: str) -> str:
    if mode == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    lines = []
    ok = result.get("success", False)
    lines.append(f"部署結果：{'✅ 成功' if ok else '❌ 失敗'}")
    for k, v in result.items():
        if k != "success":
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def cmd_deploy(args: argparse.Namespace) -> int:
    from deployer import HotDeployer
    mode = _output_mode(args.output)
    d = HotDeployer(dry_run=args.dry_run)
    result = d.deploy()
    print(_fmt(result, mode))
    return 0 if result.get("success") else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="hot-deployer",
        description="自動偵測最新報表並部署至 GitHub Pages",
    )
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    sub = parser.add_subparsers(dest="cmd", help="操作")

    p_deploy = sub.add_parser("deploy", help="部署最新報表")
    p_deploy.add_argument("--dry-run", action="store_true", help="模擬執行，不實際 push")
    p_deploy.add_argument("--output", choices=["json", "plain", "rich"], default=None)
    p_deploy.set_defaults(func=cmd_deploy)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

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
        _rec("hot-deployer", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
