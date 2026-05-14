"""auto-proxy-evader — CLI entry point (P71.9).

Usage:
  python __main__.py "https://example.com"
  python __main__.py "https://example.com" --retries 5
  python __main__.py --demo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))


def main() -> None:
    parser = argparse.ArgumentParser(description="auto-proxy-evader: UA 輪替 + 退避重試爬蟲")
    parser.add_argument("url", nargs="?", help="目標 URL")
    parser.add_argument("--retries", type=int, default=3, help="最大重試次數 (default: 3)")
    parser.add_argument("--demo", action="store_true", help="顯示 UA 池範例")
    args = parser.parse_args()

    from evader import UAPool, EvaderClient

    if args.demo:
        print("[auto-proxy-evader 已啟動] UA 池範例：")
        for _ in range(3):
            print(f"  {UAPool.get_random()}")
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    print(f"[auto-proxy-evader 已啟動] 目標：{args.url}")
    client = EvaderClient(max_retries=args.retries)
    resp = client.get(args.url)
    print(f"狀態碼：{resp.status_code}  長度：{len(resp.text)} chars")


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
        _rec("auto-proxy-evader", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
