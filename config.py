"""
集中管理所有設定值，從 .env 讀取敏感資訊。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ── LLM ─────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── 搜尋 ────────────────────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

# ── LINE Messaging API ──────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

# ── Telegram Bot ────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ── 搜尋設定 ─────────────────────────────────────────
SEARCH_KEYWORDS = [
    kw.strip()
    for kw in os.getenv("SEARCH_KEYWORDS", "傳說對決,Arena of Valor,AOV").split(",")
    if kw.strip()
]

# ── 排程設定 ─────────────────────────────────────────
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "9"))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

# ── 路徑 ─────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "aov_monitor.db"

# 確保必要資料夾存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
