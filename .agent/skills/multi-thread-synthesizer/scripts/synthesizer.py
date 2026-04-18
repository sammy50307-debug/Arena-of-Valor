import asyncio
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Callable, Awaitable

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class AsyncSynthesizer:
    """
    跨維度多線程聚合兵
    接受一批異步任務函數，並行執行後統一融合結果。
    """
    def __init__(self, max_concurrency: int = 10):
        """
        max_concurrency: 最大同時並發數，防止對目標伺服器的衝擊過大
        """
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_with_semaphore(self, task_name: str, coro: Awaitable) -> Dict[str, Any]:
        """用 Semaphore 管制最大並發數，並自動標記來源與時間"""
        async with self._semaphore:
            start = time.perf_counter()
            try:
                result = await coro
                elapsed = time.perf_counter() - start
                return {
                    "task": task_name,
                    "status": "success",
                    "result": result,
                    "elapsed_sec": round(elapsed, 3),
                    "fetched_at": datetime.now().isoformat()
                }
            except Exception as e:
                elapsed = time.perf_counter() - start
                return {
                    "task": task_name,
                    "status": "error",
                    "result": None,
                    "error": str(e),
                    "elapsed_sec": round(elapsed, 3),
                    "fetched_at": datetime.now().isoformat()
                }

    async def gather(self, tasks: Dict[str, Awaitable]) -> List[Dict[str, Any]]:
        """
        接受 {任務名稱: 協程} 字典，並行執行後回傳帶有融合標記的結果列表。
        tasks = {
            "PTT-AoV板": fetch_ptt(),
            "Dcard遊戲板": fetch_dcard(),
            ...
        }
        """
        wrapped = [
            self._run_with_semaphore(name, coro)
            for name, coro in tasks.items()
        ]
        results = await asyncio.gather(*wrapped)
        return list(results)
