"""
CacheManager — 雙層快取（L1 hero-level / L2 prompt-level）。

schema v3:
  {
    "schema_version": 3,
    "result_schema_version": <int>,
    "entries": {
      <key>: {
        "result": ...,
        "stored_at": <iso>,
        "last_accessed": <iso>,
        "ttl_days": <int>
      }
    },
    "stats": {"total_l1_hits": 0, "total_l2_hits": 0, "total_apify_hits": 0, "total_misses": 0}
  }

Key 命名慣例：
  hero:{hero_name}:{YYYY-MM-DD}        ← L1 英雄當日分析結果
  daily_summary:{YYYY-MM-DD}           ← 當日彙總
  apify:{hero_name}:{YYYY-MM-DD}       ← Apify 爬蟲結果
  prompt:{md5(system|user)}            ← L2 單次 LLM 呼叫結果（相容舊 key）
"""

import json
import logging
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 3
_EMPTY_STORE = lambda: {
    "schema_version": SCHEMA_VERSION,
    "result_schema_version": config.RESULT_SCHEMA_VERSION,
    "entries": {},
    "stats": {
        "total_l1_hits": 0,
        "total_l2_hits": 0,
        "total_apify_hits": 0,
        "total_misses": 0,
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_expired(stored_at: str, ttl_days: int) -> bool:
    try:
        stored = datetime.fromisoformat(stored_at)
        return datetime.now(timezone.utc) - stored > timedelta(days=ttl_days)
    except Exception:
        return True


class CacheManager:
    """
    執行緒安全的 JSON 快取，支援 L1/L2/apify/daily_summary 四種 key 類型。
    讀寫均為同步（GeminiClient 的 asyncio lock 在上層處理）。
    """

    def __init__(
        self,
        cache_file: Optional[Path] = None,
        ttl_days: Optional[int] = None,
        max_entries: Optional[int] = None,
    ):
        self._file = cache_file or config.CACHE_FILE
        self._ttl_days = ttl_days if ttl_days is not None else config.CACHE_TTL_DAYS
        self._max_entries = (
            max_entries if max_entries is not None else config.CACHE_MAX_ENTRIES
        )
        self._store = self._load()

    # ── 載入 / 遷移 ──────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if not self._file.exists():
            return _EMPTY_STORE()
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            logger.warning(f"快取載入失敗: {e}，重建空快取")
            return _EMPTY_STORE()

        version = raw.get("schema_version")
        if version == SCHEMA_VERSION:
            store = raw
        elif version == 2:
            store = self._migrate_v2(raw)
        elif version is None:
            store = self._migrate_v1(raw)
        else:
            logger.warning(f"未知 schema_version={version}，重建空快取")
            store = _EMPTY_STORE()

        self._evict_expired(store)
        self._enforce_max_entries(store)
        return store

    def _migrate_v1(self, old: dict) -> dict:
        """把無 schema_version 的舊格式（純 MD5 key dict）遷移到 v2。"""
        logger.info(f"偵測到 v1 快取，開始 migration（{len(old)} 筆）")
        try:
            bak = Path(str(self._file) + ".bak")
            shutil.copy2(self._file, bak)
            logger.info(f"v1 備份寫入 {bak}")
        except Exception as e:
            logger.warning(f"備份失敗: {e}，繼續 migration")

        store = _EMPTY_STORE()
        now = _now_iso()
        for k, v in old.items():
            new_key = f"prompt:{k}" if not k.startswith("prompt:") else k
            store["entries"][new_key] = {
                "result": v,
                "stored_at": now,
                "last_accessed": now,
                "ttl_days": self._ttl_days,
            }
        logger.info(f"migration 完成，{len(store['entries'])} 筆已遷移")
        return store

    def _migrate_v2(self, old: dict) -> dict:
        """把 v2 entry 補上 last_accessed，升為 v3。"""
        entries = old.get("entries", {})
        logger.info(f"偵測到 v2 快取，開始 v3 migration（{len(entries)} 筆）")
        store = _EMPTY_STORE()
        store["result_schema_version"] = old.get(
            "result_schema_version", config.RESULT_SCHEMA_VERSION
        )
        store["stats"].update(old.get("stats", {}))
        for key, value in entries.items():
            if not isinstance(value, dict):
                continue
            stored_at = value.get("stored_at") or _now_iso()
            store["entries"][key] = {
                "result": value.get("result"),
                "stored_at": stored_at,
                "last_accessed": value.get("last_accessed") or stored_at,
                "ttl_days": value.get("ttl_days", self._ttl_days),
            }
        logger.info(f"v3 migration 完成，{len(store['entries'])} 筆已遷移")
        return store

    def _evict_expired(self, store: dict) -> None:
        entries = store.get("entries", {})
        expired_keys = [
            k for k, v in entries.items()
            if _is_expired(v.get("stored_at", ""), v.get("ttl_days", self._ttl_days))
        ]
        for k in expired_keys:
            del entries[k]
        if expired_keys:
            logger.info(f"TTL 清理：移除 {len(expired_keys)} 筆過期 entry")

    def _enforce_max_entries(self, store: dict) -> None:
        entries = store.get("entries", {})
        if self._max_entries is None or self._max_entries <= 0:
            return
        overflow = len(entries) - self._max_entries
        if overflow <= 0:
            return

        def lru_sort_key(item):
            key, value = item
            marker = value.get("last_accessed") or value.get("stored_at") or ""
            return (marker, key)

        victims = [key for key, _ in sorted(entries.items(), key=lru_sort_key)[:overflow]]
        for key in victims:
            del entries[key]
        logger.info(f"LRU 清理：移除 {len(victims)} 筆最久未使用 entry")

    # ── 公開 API ─────────────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        entry = self._store["entries"].get(key)
        if entry is None:
            return None
        if _is_expired(entry.get("stored_at", ""), entry.get("ttl_days", self._ttl_days)):
            del self._store["entries"][key]
            return None
        entry["last_accessed"] = _now_iso()
        return entry["result"]

    def set(self, key: str, value: Any, ttl_days: Optional[int] = None) -> None:
        now = _now_iso()
        self._store["entries"][key] = {
            "result": value,
            "stored_at": now,
            "last_accessed": now,
            "ttl_days": ttl_days if ttl_days is not None else self._ttl_days,
        }
        self._enforce_max_entries(self._store)

    def increment_stat(self, stat: str) -> None:
        if stat in self._store["stats"]:
            self._store["stats"][stat] += 1

    def get_stats(self) -> dict:
        return dict(self._store["stats"])

    def save(self) -> None:
        try:
            self._evict_expired(self._store)
            self._enforce_max_entries(self._store)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._store, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"快取寫入失敗: {e}")

    # ── Key 工廠（集中管理命名慣例）─────────────────────────────────────────

    @staticmethod
    def hero_key(hero_name: str, date_str: str) -> str:
        return f"hero:{hero_name}:{date_str}"

    @staticmethod
    def daily_summary_key(date_str: str) -> str:
        return f"daily_summary:{date_str}"

    @staticmethod
    def apify_key(hero_name: str, date_str: str) -> str:
        return f"apify:{hero_name}:{date_str}"

    @staticmethod
    def prompt_key(md5_hex: str) -> str:
        return f"prompt:{md5_hex}"
