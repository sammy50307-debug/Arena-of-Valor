import os
import sys
import sqlite3
import hashlib
import json
import re

# 強制指定標準輸出支援 utf-8，避免 Windows cmd / PowerShell 預設為 Big5 導致亂碼
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class SemanticCacheShield:
    def __init__(self, db_path: str = None):
        if db_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, '..', 'resources', 'yaya_cache.db')
        
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semantic_cache (
                text_hash TEXT PRIMARY KEY,
                original_text TEXT,
                analysis_result TEXT,
                hit_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _normalize_and_hash(self, text: str) -> str:
        # 去除全半角空白、換行與特殊符號，將核心文意提取，並全轉為小寫
        normalized = re.sub(r'\W+', '', text).lower()
        # 進行 SHA-256 雜湊
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def check_cache(self, text: str):
        text_hash = self._normalize_and_hash(text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT analysis_result FROM semantic_cache WHERE text_hash = ?", (text_hash,))
        result = cursor.fetchone()
        
        if result:
            # 更新命中次數 (Hit count) + 1
            cursor.execute("UPDATE semantic_cache SET hit_count = hit_count + 1 WHERE text_hash = ?", (text_hash,))
            conn.commit()
            conn.close()
            return json.loads(result[0])
            
        conn.close()
        return None

    def store_cache(self, text: str, analysis_result: dict):
        text_hash = self._normalize_and_hash(text)
        result_json = json.dumps(analysis_result, ensure_ascii=False)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO semantic_cache (text_hash, original_text, analysis_result)
            VALUES (?, ?, ?)
        ''', (text_hash, text, result_json))
        conn.commit()
        conn.close()
