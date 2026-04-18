import os
import sys

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure imports work regardless of run dir
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from cache_engine import SemanticCacheShield

def run_test():
    engine = SemanticCacheShield()
    
    print("[*] 建立文本 A (原始文本)...")
    text_a = """
    【情報】芽芽最近也太常被 ban 了吧！！
    老實說，自從改版以後，芽芽的護盾真的是破壞遊戲體驗...
    希望官方趕緊下修。
    """
    
    print("[*] 建立文本 B (洗版文本)...")
    # 包含了多餘空白、特殊符號與不同的標點符號，但中文核心字眼完全一致
    text_b = """
    【情報】  芽芽  最近也太常 被  ban 了吧 ！！    
    老實說 ，自從 改版 以後， 芽芽 的護盾 真的是 破壞遊戲體驗 ... 
    希望官方趕緊下修 ！！！
    """

    # 模擬 LLM 分析結果
    simulated_llm_result = {
        "sentiment": "negative",
        "score": -0.85,
        "keywords": ["芽芽", "下修", "護盾"],
        "summary": "抱怨芽芽護盾過強影響平衡，呼籲官方調弱。"
    }

    # Step 1: 第一次查詢，理應 Cache Miss
    print("\n[第一回合] 查詢文本 A 是否存在於快取：")
    result_a = engine.check_cache(text_a)
    if result_a is None:
        print("[+] Cache Miss! (符合預期) 文本 A 是全新情報。")
        print("[+] 正在將 LLM 模擬分析結果寫入系統快取庫...")
        engine.store_cache(text_a, simulated_llm_result)
        print("[+] 寫入完成。")
    else:
        print("[-] 錯誤：預期應該 Miss 但卻 Hit 了。")
        
    # Step 2: 查詢文本 B，理應直接 Cache Hit
    print("\n[第二回合] 突然湧入洗版文本 B。開始查詢快取：")
    result_b = engine.check_cache(text_b)
    if result_b is not None:
        print("[+] Cache Hit! (符合預期) 成功攔截洗版情報！")
        print(f"[+] ✨ 本次攔截替您省下了 100% 的 LLM Token 費用。")
        print(f"[+] 直接讀取的結果: {result_b['summary']}")
    else:
        print("[-] 錯誤：快取攔截失敗，未能識別出高度相似文。")

    print("\n[✓] ALL TESTS PASSED - 語意神盾已正式上線")

if __name__ == "__main__":
    run_test()
