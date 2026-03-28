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

# ── 網頁代管 ─────────────────────────────────────────
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", "")

# ── 英雄監視清單 (Hero Watchlist) ──────────────────────────────
HERO_WATCHLIST = [
    name.strip()
    for name in os.getenv("HERO_WATCHLIST", "芽芽, 皮皮").split(",")
    if name.strip()
]
# 為相容舊版，保留第一個為預設焦點
HERO_FOCUS_NAME = HERO_WATCHLIST[0] if HERO_WATCHLIST else "芽芽"

HERO_FOCUS_KEYWORDS = [
    kw.strip()
    for kw in os.getenv("HERO_FOCUS_KEYWORDS", "傳說對決 芽芽").split(",")
    if kw.strip()
]

# ── 搜尋設定 ─────────────────────────────────────────
SEARCH_KEYWORDS = [
    kw.strip()
    for kw in os.getenv("SEARCH_KEYWORDS", "傳說對決,Arena of Valor,AOV").split(",")
    if kw.strip()
]

# ── 區域化設定 (Phase 33) ──────────────────────────────
REGIONS = ["TW", "TH", "VN"]
REGIONAL_KEYWORDS = {
    "TW": ["傳說對決", "AOV 台服"],
    "TH": ["Garena RoV", "RoV Thailand"],
    "VN": ["Garena Liên Quân Mobile", "Liên Quân Vietnam"]
}
# 各區專屬 Slang/核心詞 (Scraper 使用)
REGIONAL_SLANG = {
    "TH": "เห็ดป่า, แครี่, เมจ", # 泰文: 野區, 射手, 法師
    "VN": "Rừng, Xạ thủ, Pháp sư" # 越南文: 打野, 射手, 法師
}

# ── 排程設定 ─────────────────────────────────────────
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "9"))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

# ── 路徑 ─────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "aov_monitor.db"

# ── 預警門檻 (Alert Thresholds - Phase 30) ──────────────
ALERT_VOL_DELTA = 50.0  # 比週均值高出 50% 觸發紅頭警報
ALERT_NEG_RATIO = 70.0  # 負面論調佔比超過 70% 觸發示警
ALERT_WR_DROP = 3.0     # 勝率在 24H 內下滑超過 3% 觸發警告

# 確保必要資料夾存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
