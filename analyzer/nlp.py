"""
NLP 關鍵詞萃取引擎 (Sentiment WordCloud Engine)。
採用輕量化正規分詞與停用詞過濾，為輿情報告提供標籤雲數據。
"""

import re
import logging
from collections import Counter
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 停用詞庫：排除無意義的語意填充詞 (Phase 32)
STOP_WORDS = {
    "的", "了", "是", "在", "我", "你", "他", "和", "與", "或", "都", "就", "也", 
    "有", "給", "吧", "哈", "這", "那", "個", "很", "會", "好", "不", "被", "讓",
    "傳說", "遊戲", "英雄", "對決", "今日", "看到", "覺得", "感覺", "所以", "因為"
}

def analyze_keywords(texts: List[str], limit: int = 15) -> List[Dict[str, Any]]:
    """
    從文本列表中提取高頻詞，並返回帶有權重的字典列表。
    
    Args:
        texts: 原始文本列表
        limit: 返回的關鍵詞數量上限
        
    Returns:
        List[Dict] 格式: [{"text": "關鍵詞", "weight": 10}, ...]
    """
    if not texts:
        return []

    # 1. 文本清洗：移除標點符號與特殊字符
    clean_text = " ".join(texts)
    # 只保留中文、英文、數字 (正規表達式)
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,8}', clean_text)
    
    # 2. 過濾停用詞與單字詞
    filtered_words = [
        word for word in words 
        if word not in STOP_WORDS and len(word) > 1
    ]
    
    # 3. 詞頻統計
    counts = Counter(filtered_words)
    top_words = counts.most_common(limit)
    
    # 4. 權重歸一化 (用於前端字級調整)
    if not top_words:
        return []
        
    max_count = top_words[0][1]
    
    # 封裝結果：權重範圍 10 ~ 24 (對應 CSS pt/px)
    results = []
    for text, count in top_words:
        weight = int(12 + (count / max_count) * 12) if max_count > 0 else 12
        results.append({
            "text": text,
            "weight": weight,
            "count": count
        })
        
    return results
