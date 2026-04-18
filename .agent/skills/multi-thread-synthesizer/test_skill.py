import os
import sys
import asyncio
import time

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from synthesizer import AsyncSynthesizer


# ── 模擬各論壇的非同步抓取函數 ──────────────────────────────
async def mock_fetch(platform: str, delay: float, content: str) -> dict:
    """模擬一個需要等待網路的非同步抓取任務"""
    await asyncio.sleep(delay)  # 模擬網路延遲
    return {"platform": platform, "posts": [content], "count": 1}


async def run_test():
    print("[*] 啟動跨維度多線程聚合兵壓力測試...\n")

    # ── 建立 12 個平行任務 (模擬同時監控多個論壇) ─────────
    # 每個任務設計不同的等待時間來模擬真實網路延遲
    tasks = {
        "PTT-AoV板":      mock_fetch("PTT", 0.5, "最近芽芽被動真的很噁心"),
        "Dcard遊戲板":    mock_fetch("Dcard", 0.7, "有人覺得這次版本 ADC 系強化很棒嗎"),
        "巴哈姆特-AoV":   mock_fetch("Bahamut", 0.3, "求教芽芽出裝攻略"),
        "FB粉絲頁":        mock_fetch("Facebook", 0.6, "今日官方更新已上線！"),
        "Threads-AoV":    mock_fetch("Threads", 0.4, "有打GCS嗎 台服今天加油"),
        "Instagram-AoV":  mock_fetch("Instagram", 0.8, "官方曬出新皮膚 超美"),
        "Discord-TW":     mock_fetch("Discord", 0.2, "組隊找輔助"),
        "YouTube-AoV":    mock_fetch("YouTube", 0.9, "新賽季新手指南 百萬播放"),
        "Reddit-AOV":     mock_fetch("Reddit", 0.35, "yaya too strong please nerf"),
        "Twitter-AoV":    mock_fetch("Twitter", 0.55, "AoV patch notes dropped!"),
        "TikTok-AoV":     mock_fetch("TikTok", 0.45, "芽芽無限護盾連殺 超帥"),
        "App reviews":    mock_fetch("AppStore", 0.65, "1 star - matchmaking is broken"),
    }

    synthesizer = AsyncSynthesizer(max_concurrency=10)

    # ── 計時並行執行 ─────────────────────────────────────
    wall_start = time.perf_counter()
    results = await synthesizer.gather(tasks)
    wall_elapsed = time.perf_counter() - wall_start

    # ── 打印結果 ─────────────────────────────────────────
    print(f"[+] 全部 {len(results)} 個任務完成！總耗時: {wall_elapsed:.3f} 秒")
    print(f"[*] 序列等候理論基準: ~6.25 秒，並行只花了: {wall_elapsed:.3f} 秒\n")

    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"[+] 成功率: {success_count}/{len(results)}")
    print("-" * 50)
    for r in results:
        status_icon = "✅" if r['status'] == 'success' else "❌"
        platform = r['result']['platform'] if r.get('result') else "N/A"
        print(f"  {status_icon} [{r['task']}] ({platform}) - 耗時: {r['elapsed_sec']}s | 抓取時間戳: {r['fetched_at'][:19]}")

    # ── 效能驗證 ─────────────────────────────────────────
    # 最慢的任務是 0.9 秒，若完全序列執行會需要 sum(delays)≈6.25 秒
    SEQUENTIAL_BASELINE = 6.25
    assert wall_elapsed < SEQUENTIAL_BASELINE * 0.3, \
        f"❌ 並行效能不達標！預期應 < {SEQUENTIAL_BASELINE * 0.3:.1f} 秒，實際花了 {wall_elapsed:.2f} 秒"

    print(f"\n[+] ✅ 效能大幅提升！序列基準: {SEQUENTIAL_BASELINE:.1f}s → 並行完成: {wall_elapsed:.3f}s (節省 {((SEQUENTIAL_BASELINE - wall_elapsed)/SEQUENTIAL_BASELINE)*100:.1f}% 等待時間)")
    print("\n[✓] ALL TESTS PASSED - 跨維度多線程聚合兵已正式就位！")


if __name__ == "__main__":
    asyncio.run(run_test())
