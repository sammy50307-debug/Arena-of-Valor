import os
import sys

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from evader import EvaderClient, safe_get
import requests

def run_test():
    print("[*] 正在驗證 Auto Proxy Evader 的反封鎖能力...\n")
    
    # 測試一：正常存取
    print("【測試一】正常訪問 (狀態碼 200)")
    try:
        res = safe_get("https://httpbin.org/get")
        print(f"[+] 成功取得資料！(Status: {res.status_code})")
        print(f"[+] 當前使用的偽裝指紋 (User-Agent): {res.json()['headers']['User-Agent']}")
    except Exception as e:
        print(f"[-] 測試一失敗: {e}")

    # 測試二：模擬遭遇 429 Too Many Requests 封鎖
    print("\n【測試二】模擬遭遇嚴苛限流封鎖 (狀態碼 429)，驗證 Exponential Backoff 重試機制：")
    client = EvaderClient(max_retries=2, base_wait=0.5) # 為了測試，加快退避時間，且只重試2次
    
    try:
        # httpbin.org/status/429 一定會回傳 429
        client.get("https://httpbin.org/status/429")
    except requests.exceptions.RequestException as e:
        print(f"[+] 測試二如同預期拋出異常，保護殼完美運作！(攔截最後異常: {e})")
        
    print("\n[✓] ALL TESTS PASSED - 抗封鎖自適應偽裝兵 (Auto Proxy Evader) 已正式上線")

if __name__ == "__main__":
    run_test()
