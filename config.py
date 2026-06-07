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
PUBLISH_GATE_MODE = os.getenv("PUBLISH_GATE_MODE", "shadow").lower()

# ── P105 provider 切換（首發 provider+model 一行配置；換首發只改這裡或 .env）──
PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "gemini")  # gemini│openai│openrouter
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "")  # 空＝用該 provider 內建預設 model
FALLBACK_PROVIDERS = [
    p.strip() for p in os.getenv("FALLBACK_PROVIDERS", "openai").split(",") if p.strip()
]


# ── P105.1 B 架構：provider:model 鏈 + per-model 額度（向後相容 S1）──
def parse_provider_chain(raw):
    """解析 PROVIDER_CHAIN：逗號分級、冒號分 provider:model（model 的 / 不是分隔符）。

    例 "openrouter:deepseek/deepseek-chat, gemini"
      → [("openrouter", "deepseek/deepseek-chat"), ("gemini", None)]。
    空字串／全空白 → []（呼叫端據此退回 S1 PRIMARY_PROVIDER 路徑，不破 S1 切換）。
    """
    chain = []
    for level in raw.split(","):
        level = level.strip()
        if not level:
            continue
        provider, sep, model = level.partition(":")
        model = model.strip() if sep else ""
        chain.append((provider.strip().lower(), model or None))
    return chain


def parse_openrouter_model_budgets(raw):
    """解析 OPENROUTER_MODEL_BUDGETS：逗號分項、最右冒號分 model:budget。

    例 "deepseek/deepseek-chat:80000, deepseek/deepseek-r1:20000"
      → {"deepseek/deepseek-chat": 80000, "deepseek/deepseek-r1": 20000}。
    rpartition：model 含 / 不被切錯（budget 取最右段）；無效 budget 略過。
    """
    budgets = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        model, sep, amount = item.rpartition(":")
        if not sep:
            continue
        try:
            budgets[model.strip()] = int(amount.strip())
        except ValueError:
            continue
    return budgets


# 鏈每級 provider:model（首級＝首發、其餘＝多級 fallback）；無此值退回 S1 路徑。
PROVIDER_CHAIN = parse_provider_chain(os.getenv("PROVIDER_CHAIN", ""))

# ── P105 OpenRouter（OpenAI-compatible；API key 只進 .env，絕不進版控）──
AOV_PROVIDER_OPENROUTER_ENABLED = os.getenv("AOV_PROVIDER_OPENROUTER_ENABLED", "false").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "")
OPENROUTER_MODEL_PRO = os.getenv("OPENROUTER_MODEL_PRO", "")
OPENROUTER_MODEL_FLASH = os.getenv("OPENROUTER_MODEL_FLASH", "")
OPENROUTER_MODEL_MINIMAX = os.getenv("OPENROUTER_MODEL_MINIMAX", "")
# OpenRouter 獨立 budget 停損（R-P105-5）：上限預設設高純防 bug 失控燒爆，正常燒不到；
# 獨立 state 檔避免與 Gemini「省額度」ledger 互相干擾。要燒更多可在 .env 調高。
OPENROUTER_BUDGET_STATE_FILE = os.getenv("OPENROUTER_BUDGET_STATE_FILE", "data/openrouter_budget_state.json")
OPENROUTER_DAILY_BUDGET = int(os.getenv("OPENROUTER_DAILY_BUDGET", "100000"))
# per-model 額度上限（覆寫 OPENROUTER_DAILY_BUDGET）；無對應 model 時退回總上限。
OPENROUTER_MODEL_BUDGETS = parse_openrouter_model_budgets(os.getenv("OPENROUTER_MODEL_BUDGETS", ""))

# P93 provider abstraction：所有非既有 provider 預設關閉。
PROVIDER_ROUTER_ENABLED = os.getenv("PROVIDER_ROUTER_ENABLED", "false").lower() == "true"
EXPERIMENTAL_FREE_PROVIDERS_ENABLED = os.getenv("EXPERIMENTAL_FREE_PROVIDERS_ENABLED", "false").lower() == "true"
PROVIDER_ROUTER_MAX_ATTEMPTS = int(os.getenv("PROVIDER_ROUTER_MAX_ATTEMPTS", "1"))
AOV_PROVIDER_GROQ_ENABLED = os.getenv("AOV_PROVIDER_GROQ_ENABLED", "false").lower() == "true"
AOV_PROVIDER_CLOUDFLARE_AI_ENABLED = os.getenv("AOV_PROVIDER_CLOUDFLARE_AI_ENABLED", "false").lower() == "true"
AOV_PROVIDER_GITHUB_MODELS_ENABLED = os.getenv("AOV_PROVIDER_GITHUB_MODELS_ENABLED", "false").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
GITHUB_MODELS_TOKEN = os.getenv("GITHUB_MODELS_TOKEN", os.getenv("GITHUB_TOKEN", ""))

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
LLM_BUDGET_STATE_FILE = DATA_DIR / "llm_budget_state.json"
LLM_DAILY_BUDGET = int(os.getenv("LLM_DAILY_BUDGET", "20"))
LLM_ANALYSIS_TOP_N = int(os.getenv("LLM_ANALYSIS_TOP_N", "18"))
LLM_BUDGET_COOLDOWN_MINUTES = int(os.getenv("LLM_BUDGET_COOLDOWN_MINUTES", "360"))
LLM_BUDGET_RETENTION_DAYS = int(os.getenv("LLM_BUDGET_RETENTION_DAYS", "14"))
ENRICHMENT_QUEUE_DIR = DATA_DIR / "enrichment_queue"
ENRICHMENT_REPLAY_MAX_POSTS = int(os.getenv("ENRICHMENT_REPLAY_MAX_POSTS", "4"))
ENRICHMENT_ARTIFACT_RETENTION_DAYS = int(os.getenv("ENRICHMENT_ARTIFACT_RETENTION_DAYS", "3"))
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
TOP5_MAX_AGE_DAYS = int(os.getenv("TOP5_MAX_AGE_DAYS", "14"))
# P108.4：無日期文（非巴哈搜尋結果，時間無法解析）的差異化 decay——芽芽相關較高（能被看到）、無關墊底（不壓過巴哈真實新文）
TOP5_NODATE_DECAY_YAYA = float(os.getenv("TOP5_NODATE_DECAY_YAYA", "0.6"))
TOP5_NODATE_DECAY_OTHER = float(os.getenv("TOP5_NODATE_DECAY_OTHER", "0.3"))
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

# ── P106.2 combat_stats 真戰績 ──
HERO_COMBAT_STATS_PATH = BASE_DIR / "configs" / "hero_combat_stats.yaml"
HERO_STATS_STALE_DAYS = int(os.getenv("HERO_STATS_STALE_DAYS", "30"))

# 確保必要資料夾存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ENRICHMENT_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
