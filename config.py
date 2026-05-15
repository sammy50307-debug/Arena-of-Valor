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
OPENAI_FALLBACK_ENABLED = os.getenv("OPENAI_FALLBACK_ENABLED", "true").lower() == "true"
OPENAI_FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")

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

# ── 區域化設定 (Phase 34.2: TW Single-Core Focus) ──────────────────────────
REGIONS = ["TW"]
REGIONAL_KEYWORDS = {
    "TW": ["傳說對決", "AOV 台服", "Garena Arena of Valor TW"]
}
# 各區專屬 Slang (現僅保留台服核心)
REGIONAL_SLANG = {} 

# ── 排程設定 ─────────────────────────────────────────
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "9"))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

# ── 路徑 ─────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "aov_monitor.db"

# ── 快取設定 (P64) ────────────────────────────────────
CACHE_FILE = DATA_DIR / "llm_cache.json"
CACHE_TTL_DAYS = 7
CACHE_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "500"))
LOCKFILE_PATH = DATA_DIR / ".last_successful_run"
LOCKFILE_COOLDOWN_MINUTES = 30
RESULT_SCHEMA_VERSION = 1

# ── 預警門檻 (Alert Thresholds - Phase 30) ──────────────
ALERT_VOL_DELTA = 50.0  # 比週均值高出 50% 觸發紅頭警報
ALERT_NEG_RATIO = 70.0  # 負面論調佔比超過 70% 觸發示警
ALERT_WR_DROP = 3.0     # 勝率在 24H 內下滑超過 3% 觸發警告

# ── P65 Top-5 News Cards ─────────────────────────────────
ENABLE_TOP5_NEWS = os.getenv("ENABLE_TOP5_NEWS", "true").lower() == "true"
HERO_BOOST_FACTOR = float(os.getenv("HERO_BOOST_FACTOR", "1.2"))
OG_FETCH_DAILY_LIMIT = int(os.getenv("OG_FETCH_DAILY_LIMIT", "50"))
NEWS_HISTORY_INDEX_PATH = DATA_DIR / "news_history_index.json"
NEWS_HISTORY_MAX_DAYS = int(os.getenv("NEWS_HISTORY_MAX_DAYS", "14"))
TOP5_SCORE_DECAY_HOURS = int(os.getenv("TOP5_SCORE_DECAY_HOURS", "72"))
TOP5_SCORE_DECAY_MIN = float(os.getenv("TOP5_SCORE_DECAY_MIN", "0.3"))
TOP5_DEDUP_THRESHOLD = float(os.getenv("TOP5_DEDUP_THRESHOLD", "0.85"))

# ── P66.1 Top-5 Picker 個人化過濾與多樣性 ────────────────
PERSONAL_BLACKLIST_PATH = BASE_DIR / "configs" / "personal_blacklist.yaml"
DCARD_SOURCE_BOOST = float(os.getenv("DCARD_SOURCE_BOOST", "1.05"))
DIVERSITY_MIN_PLATFORMS = int(os.getenv("DIVERSITY_MIN_PLATFORMS", "3"))

# ── P70.1 Picker 品質強化：去重懲罰 + 同平台排名衰減 ─────
# 重複文章懲罰因子（越舊懲罰越重；芽芽豁免）
DUP_PENALTY_DAY1 = float(os.getenv("DUP_PENALTY_DAY1", "0.3"))
DUP_PENALTY_DAY3 = float(os.getenv("DUP_PENALTY_DAY3", "0.2"))
DUP_PENALTY_DAY7 = float(os.getenv("DUP_PENALTY_DAY7", "0.1"))
# 同平台每多一篇的衰減率（第 N 篇 × max(MIN, 1 - DECAY×(N-1))；芽芽豁免）
PLATFORM_RANK_DECAY = float(os.getenv("PLATFORM_RANK_DECAY", "0.1"))
PLATFORM_RANK_MIN = float(os.getenv("PLATFORM_RANK_MIN", "0.3"))
# 芽芽重複文章加成（即使重複仍加分，確保芽芽優先）
YAYA_REPEAT_BONUS = float(os.getenv("YAYA_REPEAT_BONUS", "1.5"))

# 確保必要資料夾存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
