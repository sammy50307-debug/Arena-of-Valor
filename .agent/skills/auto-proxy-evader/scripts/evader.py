import sys
import time
import random
import requests
from typing import Dict, Any

# 強制指定標準輸出支援 utf-8，避免 Windows 亂碼
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class UAPool:
    """使用者代理 (User-Agent) 隨機池"""
    AGENTS = [
        # Windows / Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Mac / Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
        # Mobile iOS
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        # Mobile Android
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    ]

    @classmethod
    def get_random(cls) -> str:
        return random.choice(cls.AGENTS)


class EvaderClient:
    """抗封鎖請求外殼 (Exponential Backoff Wrapper)"""
    def __init__(self, max_retries: int = 3, base_wait: float = 1.0):
        self.max_retries = max_retries
        self.base_wait = base_wait

    def get(self, url: str, **kwargs) -> requests.Response:
        retries = 0
        last_exception = None

        while retries <= self.max_retries:
            # 每次重試都換一件衣服 (User-Agent)
            headers = kwargs.get("headers", {})
            headers["User-Agent"] = UAPool.get_random()
            kwargs["headers"] = headers

            try:
                # 設定預設 timeout，防止卡死
                if "timeout" not in kwargs:
                    kwargs["timeout"] = 10

                response = requests.get(url, **kwargs)
                
                # 如果是 403 或是 429 就當作爬蟲被抓包了，觸發重試
                if response.status_code in [403, 429]:
                    print(f"[!] 遭遇封鎖 (Status {response.status_code})。正在準備指數退避重試...")
                    raise requests.exceptions.RequestException(f"Blocked with status {response.status_code}")
                
                # 若為其他錯誤（例如 500 系列），也會拋出異常
                response.raise_for_status()
                
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                if retries == self.max_retries:
                    print(f"[-] 已達最大重試次數 ({self.max_retries})，放棄任務。")
                    break
                
                # Exponential Backoff 演算法 (加上一點 jitter 擾動，避免被規律偵測)
                sleep_time = (self.base_wait * (2 ** retries)) + random.uniform(0.1, 0.5)
                print(f"[*] 第 {retries + 1} 次嘗試失敗，睡眠 {sleep_time:.2f} 秒後換個身份再試...")
                time.sleep(sleep_time)
                retries += 1

        raise last_exception

# 向下相容的快速使用入口
def safe_get(url: str, **kwargs) -> requests.Response:
    client = EvaderClient()
    return client.get(url, **kwargs)
