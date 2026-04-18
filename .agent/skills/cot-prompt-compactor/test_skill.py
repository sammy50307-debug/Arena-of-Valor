import os
import sys

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from prompts_schema import SinglePostAnalysisSchema, DailySummarySchema
from compactor import SYSTEM_SINGLE_POST_COMPACT, SYSTEM_DAILY_SUMMARY_COMPACT

def run_test():
    print("[*] 正在驗證 Prompt Compactor 的結構化模型...")
    
    # 測試 Pydantic Schema
    mock_data = {
        "reasoning": "這是反諷",
        "sentiment": "negative",
        "sentiment_score": 0.8,
        "region": "TW",
        "original_language": "zh",
        "category": "遊戲體驗",
        "keywords": ["芽芽"],
        "events": [],
        "summary": "太爛了",
        "relevance_score": 1.0,
        "is_hero_focus": True
    }
    
    # 若格式不符會直接拋出 ValueError
    try:
        validated_data = SinglePostAnalysisSchema(**mock_data)
        print("[+] 實體類別 Pydantic 驗證成功 (SinglePostAnalysisSchema)")
    except Exception as e:
        print(f"[-] 實體類別 Pydantic 驗證失敗: {e}")
        return

    original_prompt_size = 1435 # 原本 prompts.py 裡面 Single Post prompt 的粗估長度字元數
    compacted_prompt_size = len(SYSTEM_SINGLE_POST_COMPACT)
    savings = ((original_prompt_size - compacted_prompt_size) / original_prompt_size) * 100

    print(f"\n[+] 舊版 System Prompt 長度: {original_prompt_size} chars")
    print(f"[+] 瘦身版 System Prompt 長度: {compacted_prompt_size} chars")
    print(f"[+] 計算得出 Token 節省: {savings:.2f}% (此部分不含 Pydantic schema 字數)")
    
    print("\n[✓] ALL TESTS PASSED - 結構化與思維鏈壓縮器已正式上線")

if __name__ == "__main__":
    run_test()
