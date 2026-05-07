"""
去重歷史索引管理 (P65-D2)。

index 格式：
  {
    "<normalized_url>": {"first_seen": "YYYY-MM-DD", "title": "..."},
    ...
  }

atomic write + .bak 備份，防損毀 (R12)。
14 天滾動視窗後自動 prune (D2)。
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import config
from analyzer.url_normalizer import normalize

logger = logging.getLogger(__name__)

_INDEX_PATH: Path = config.NEWS_HISTORY_INDEX_PATH
_MAX_DAYS: int = config.NEWS_HISTORY_MAX_DAYS


def load_index() -> dict:
    if not _INDEX_PATH.exists():
        return {}
    try:
        return json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("history_index 讀取失敗，重置為空：%s", e)
        return {}


def save_index(index: dict) -> None:
    """Atomic write：先寫 .tmp，再 rename，並備份 .bak。"""
    tmp_path = _INDEX_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    if _INDEX_PATH.exists():
        shutil.copy2(_INDEX_PATH, _INDEX_PATH.with_suffix(".bak"))
    os.replace(tmp_path, _INDEX_PATH)


def prune_old(index: dict, *, today: str | None = None) -> dict:
    today_str = today or datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=_MAX_DAYS)).strftime("%Y-%m-%d")
    return {url: meta for url, meta in index.items() if meta.get("first_seen", today_str) >= cutoff}


def is_duplicate(url: str, index: dict, *, today: str | None = None) -> tuple[bool, str]:
    """
    Returns (is_dup, badge_level).
    badge_level: "" | "day1" | "day3" | "day7"
    """
    norm = normalize(url)
    if norm not in index:
        return False, ""
    first_seen = index[norm].get("first_seen", "")
    if not first_seen:
        return True, "day1"
    today_str = today or datetime.now().strftime("%Y-%m-%d")
    try:
        age_days = (datetime.strptime(today_str, "%Y-%m-%d") - datetime.strptime(first_seen, "%Y-%m-%d")).days
    except ValueError:
        return True, "day1"
    if age_days <= 1:
        badge = "day1"
    elif age_days <= 3:
        badge = "day3"
    else:
        badge = "day7"
    return True, badge


def record_urls(urls: list[str], index: dict, *, today: str | None = None) -> dict:
    """將 url 列表記入索引（僅寫入尚未存在的），回傳更新後的 index。"""
    today_str = today or datetime.now().strftime("%Y-%m-%d")
    for url in urls:
        norm = normalize(url)
        if norm and norm not in index:
            index[norm] = {"first_seen": today_str}
    return index
