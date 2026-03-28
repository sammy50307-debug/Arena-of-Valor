import sys
import os

# 強制刷新輸出，確保即使崩潰也能看到最後一行
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

print("--- [1/5] 開始系統自我診斷 ---")
try:
    import config
    print("[OK] 配置模組載入成功")
except Exception as e:
    print(f"[FAIL] 配置模組載入失敗: {e}")

print("--- [2/5] 檢查核心分析引擎 ---")
try:
    from analyzer.sentiment import SentimentAnalyzer
    print("[OK] 分析引擎 (Sentiment) 載入成功")
except Exception as e:
    print(f"[FAIL] 分析引擎載入失敗，錯誤細節如下:")
    import traceback
    traceback.print_exc()

print("--- [3/5] 檢查搜尋引擎 ---")
try:
    from scrapers.tavily_searcher import TavilySearcher
    print("[OK] 搜尋引擎 (Tavily) 載入成功")
except Exception as e:
    print(f"[FAIL] 搜尋引擎載入失敗: {e}")

print("--- [4/5] 檢查外部套件依賴 ---")
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from rich.console import Console
    print("[OK] 第三方套件 (Rich/APScheduler) 載入成功")
except Exception as e:
    print(f"[FAIL] 套件缺失或版本衝突: {e}")

print("--- [5/5] 最終環境測試 ---")
try:
    import io
    # 測試 Windows 緩衝區是否正常
    if hasattr(sys.stdout, 'buffer'):
        test_console = sys.stdout.buffer
        print(f"[OK] 終端機緩衝區狀態: {test_console}")
    else:
         print("[!] 終端機無緩衝區屬性")
except Exception as e:
    print(f"[FAIL] 終端機環境異常: {e}")

print("\n診斷結束。請檢查上方是否有任何 [FAIL] 標記。")
