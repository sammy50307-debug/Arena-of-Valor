"""multi-thread-synthesizer — CLI entry point (P71.3).

AsyncSynthesizer is a library component — this entry point provides
a demo mode with configurable concurrency.

Usage:
  python __main__.py --demo
  python __main__.py --demo --concurrency 5
  python __main__.py --demo --output json
  NO_COLOR=1 python __main__.py --demo
"""
from __future__ import annotations

import argparse
import asyncio
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


async def _demo_tasks(concurrency: int) -> list:
    from synthesizer import AsyncSynthesizer
    import asyncio

    async def fake_task(i: int) -> str:
        await asyncio.sleep(0.01)
        return f"task_{i}_ok"

    synth = AsyncSynthesizer(max_concurrency=concurrency)
    tasks = {f"task_{i}": fake_task(i) for i in range(concurrency)}
    return await synth.gather(tasks)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="multi-thread-synthesizer",
        description="跨維度多線程聚合兵 — 並行執行多個非同步任務並統一融合結果",
    )
    parser.add_argument("--demo", action="store_true", help="執行示範模式（N 個 fake tasks）")
    parser.add_argument("--concurrency", type=int, default=5, metavar="N",
                        help="最大並發數（預設 5）")
    parser.add_argument(
        "--output", choices=["json", "plain", "rich"], default=None,
        help="輸出模式（預設：TTY=rich, pipe/NO_COLOR=plain）",
    )

    args = parser.parse_args()
    mode = _output_mode(args.output)

    if not args.demo:
        parser.print_help()
        return 1

    results = asyncio.run(_demo_tasks(args.concurrency))

    if mode == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"[multi-thread-synthesizer] 並發 {args.concurrency} 任務完成")
        if isinstance(results, list):
            for r in results:
                print(f"  {r}")
        else:
            print(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
