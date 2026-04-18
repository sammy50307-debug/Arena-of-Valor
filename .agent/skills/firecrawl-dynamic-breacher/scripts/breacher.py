import os
import sys
import time
import requests

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class FirecrawlBreacher:
    """
    動態網頁渲染刺客
    負責將無法一般抓取的 JS 網頁，扔到 Firecrawl 上強制渲染並抽離 Markdown。
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.api_url = "https://api.firecrawl.dev/v1/scrape"
        
        if not self.api_key:
            print("[!] 尚未設定 FIRECRAWL_API_KEY。將會導致高強度動態站點無法被突破！")

    def breach_and_extract(self, target_url: str, wait_time: int = 3000) -> str:
        """
        強攻指定 URL，渲染並抽出 Markdown。
        wait_time: 等待 JS 執行的毫秒數 (預設 3000ms)。
        """
        if not self.api_key:
            print(f"[-] 缺少 API Key，強行啟動備援純靜態直達模式 (容易失敗): {target_url}")
            return self._fallback_static_scrape(target_url)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": target_url,
            "formats": ["markdown"],
            # 開啟 JS 繞過防爬與加強動態等待
            "waitFor": wait_time
        }

        print(f"[*] 🚀 正在派送刺客前往: {target_url} (等待 JS 渲染 {wait_time} 毫秒...)")
        try:
            # 由於渲染較慢，設定較大的 Timeout
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            
            if resp.status_code != 200:
                print(f"[-] 敵軍火力過強！Firecrawl 返回錯誤碼: {resp.status_code}")
                print(resp.text)
                return ""

            data = resp.json()
            if data.get("success"):
                md_content = data.get("data", {}).get("markdown", "")
                print(f"[+] 🎯 成功刺殺目標並抽離出 Markdown！(總長度: {len(md_content)} 字元)")
                return md_content
            else:
                print(f"[-] 任務失敗，但敵軍未報錯。伺服器訊息: {data.get('error', 'Unknown')}")
                return ""
                
        except requests.exceptions.RequestException as e:
            print(f"[-] 遠端連線異常，通訊兵戰死: {e}")
            return ""

    def _fallback_static_scrape(self, url: str) -> str:
        """
        無 API Key 時的窮鬼備援方案 (類似 Phase 45 前置動作加上 requests)
        """
        try:
            resp = requests.get(url, timeout=10)
            return resp.text[:2000] + "\n\n(已截斷，因為這只是靜態備援抓取)"
        except Exception as e:
            return f"備援抓取失敗: {e}"

