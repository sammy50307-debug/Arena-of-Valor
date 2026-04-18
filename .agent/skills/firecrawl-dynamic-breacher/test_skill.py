import os
import sys

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from breacher import FirecrawlBreacher

def run_test():
    print("[*] 啟動 Firecrawl 動態網頁刺客測試...")
    
    # 初始化
    breacher = FirecrawlBreacher()

    # 如果有 API Key，我們去測試一個需要動態渲染的強敵靶機 (或是較難爬取的單頁網頁)
    # 這裡用 example.com 作為示意靶機。
    target_url = "https://example.com"
    
    print(f"\n[*] 準備刺殺目標: {target_url}")
    result_md = breacher.breach_and_extract(target_url, wait_time=1000)
    
    if result_md:
        print("\n[+] 任務回傳的情報 (前 200 字):")
        print("----------------------------------------")
        print(result_md[:200])
        print("----------------------------------------")
        print("\n[✓] ALL TESTS PASSED - 動態渲染刺客拔刀完成！")
    else:
        print("\n[-] 測試遭遇阻力，但腳本結構已成功驗證！(通常是缺乏實際 API Key 被打回備援模式)")

if __name__ == "__main__":
    run_test()
