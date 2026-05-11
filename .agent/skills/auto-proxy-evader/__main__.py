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


if __name__ == "__main__":
    main()
