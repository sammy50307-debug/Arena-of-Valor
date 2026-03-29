import traceback
import sys

print("--- 啟動深度診斷 (Deep Diagnostics) ---", flush=True)

try:
    from analyzer.sentiment import SentimentAnalyzer
    print("[+] SentimentAnalyzer 導入成功", flush=True)
    
    from analyzer.history import HistoryResolver
    print("[+] HistoryResolver 導入成功", flush=True)
    
    import main
    print("[+] main.py 導入成功", flush=True)
    
    print("--- 所有核心模組語法校準完畢 ---", flush=True)
except Exception:
    print("--- !!! 偵測到致命衝突 !!! ---", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
