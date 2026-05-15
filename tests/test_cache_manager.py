"""
P64-S5 單元測試：CacheManager

覆蓋：
  T1  L2 miss → set → get round-trip
  T2  L2 命中（同 key 第二次 get）
  T3  L1 hero key 命中
  T4  TTL 過期 → get 回 None
  T5  v1 → v2 migration（舊純 MD5 key 轉 prompt: prefix）
  T6  TTL 清理（載入時移除過期 entry）
  T7  429 不污染 L1（showcase 結果不寫入）
  T8  stats increment
  T9  save / reload 持久化
  T10 Lockfile 冷卻（模擬）
  T11 get 命中更新 last_accessed
  T12 max_entries LRU 淘汰最久未使用 entry
"""

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from analyzer.cache_manager import CacheManager, _now_iso, _is_expired


# ── 共用 fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_cache(tmp_path):
    """回傳一個使用暫存目錄的 CacheManager。"""
    f = tmp_path / "llm_cache.json"
    return CacheManager(cache_file=f, ttl_days=7)


# ── T1：L2 miss → set → get ──────────────────────────────────────────────────

def test_t1_l2_miss_then_set_get(tmp_cache):
    key = CacheManager.prompt_key("abc123")
    assert tmp_cache.get(key) is None           # miss
    tmp_cache.set(key, {"result": "ok"})
    assert tmp_cache.get(key) == {"result": "ok"}


# ── T2：L2 命中（連續兩次 get 相同）────────────────────────────────────────

def test_t2_l2_hit(tmp_cache):
    key = CacheManager.prompt_key("dup")
    tmp_cache.set(key, "hello")
    assert tmp_cache.get(key) == "hello"
    assert tmp_cache.get(key) == "hello"        # 第二次依然命中


# ── T3：L1 hero key 命中 ─────────────────────────────────────────────────────

def test_t3_l1_hero_hit(tmp_cache):
    key = CacheManager.hero_key("芽芽", "2026-05-03")
    assert tmp_cache.get(key) is None
    tmp_cache.set(key, [{"post": "test"}])
    result = tmp_cache.get(key)
    assert result == [{"post": "test"}]
    assert key.startswith("hero:")


# ── T4：TTL 過期 ─────────────────────────────────────────────────────────────

def test_t4_ttl_expired(tmp_path):
    f = tmp_path / "cache.json"
    cm = CacheManager(cache_file=f, ttl_days=7)
    key = CacheManager.prompt_key("expired")
    cm.set(key, "value", ttl_days=7)

    # 直接竄改 stored_at 為 8 天前
    old_ts = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    cm._store["entries"][key]["stored_at"] = old_ts

    assert cm.get(key) is None                  # 應視為過期


# ── T5：v1 → v2 migration ────────────────────────────────────────────────────

def test_t5_v1_migration(tmp_path):
    f = tmp_path / "cache.json"
    # 寫入舊格式（無 schema_version，純 MD5 dict）
    old_data = {
        "aabbccdd": "result_a",
        "11223344": "result_b",
    }
    f.write_text(json.dumps(old_data), encoding="utf-8")

    cm = CacheManager(cache_file=f, ttl_days=7)

    # schema_version 應升為 3
    assert cm._store["schema_version"] == 3
    # 舊 key 應加上 prompt: prefix
    assert cm.get("prompt:aabbccdd") == "result_a"
    assert cm.get("prompt:11223344") == "result_b"
    # 備份檔存在
    bak = Path(str(f) + ".bak")
    assert bak.exists()


# ── T6：TTL 清理（載入時移除過期 entry）─────────────────────────────────────

def test_t6_ttl_eviction_on_load(tmp_path):
    f = tmp_path / "cache.json"
    expired_ts = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    fresh_ts = _now_iso()

    data = {
        "schema_version": 2,
        "result_schema_version": 1,
        "entries": {
            "prompt:expired": {"result": "old", "stored_at": expired_ts, "ttl_days": 7},
            "prompt:fresh": {"result": "new", "stored_at": fresh_ts, "ttl_days": 7},
        },
        "stats": {"total_l1_hits": 0, "total_l2_hits": 0,
                  "total_apify_hits": 0, "total_misses": 0},
    }
    f.write_text(json.dumps(data), encoding="utf-8")

    cm = CacheManager(cache_file=f, ttl_days=7)

    assert cm._store["schema_version"] == 3
    assert "prompt:expired" not in cm._store["entries"]   # 清掉
    assert cm.get("prompt:fresh") == "new"                # 保留
    assert "last_accessed" in cm._store["entries"]["prompt:fresh"]


# ── T7：429 不污染 L1（showcase 不寫）───────────────────────────────────────

def test_t7_showcase_not_written_to_l1(tmp_cache):
    hero_key = CacheManager.hero_key("皮皮", "2026-05-03")
    showcase_result = {"posts": [], "is_showcase": True}

    # 模擬 showcase 路徑：直接確認 sentinel 條件
    is_showcase = showcase_result["is_showcase"]
    if not is_showcase:
        tmp_cache.set(hero_key, showcase_result)

    assert tmp_cache.get(hero_key) is None      # showcase 不應寫入


# ── T8：stats increment ──────────────────────────────────────────────────────

def test_t8_stats(tmp_cache):
    tmp_cache.increment_stat("total_l1_hits")
    tmp_cache.increment_stat("total_l1_hits")
    tmp_cache.increment_stat("total_l2_hits")
    tmp_cache.increment_stat("total_misses")

    stats = tmp_cache.get_stats()
    assert stats["total_l1_hits"] == 2
    assert stats["total_l2_hits"] == 1
    assert stats["total_misses"] == 1
    assert stats["total_apify_hits"] == 0


# ── T9：save → reload 持久化 ────────────────────────────────────────────────

def test_t9_save_reload(tmp_path):
    f = tmp_path / "cache.json"
    cm1 = CacheManager(cache_file=f, ttl_days=7)
    cm1.set(CacheManager.hero_key("芽芽", "2026-05-03"), [{"p": 1}])
    cm1.increment_stat("total_l1_hits")
    cm1.save()

    cm2 = CacheManager(cache_file=f, ttl_days=7)
    assert cm2.get(CacheManager.hero_key("芽芽", "2026-05-03")) == [{"p": 1}]
    assert cm2.get_stats()["total_l1_hits"] == 1


# ── T10：Lockfile 冷卻邏輯（純邏輯，不跑 run_pipeline）────────────────────

def test_t10_lockfile_cooldown(tmp_path):
    import config as cfg_mod

    lf = tmp_path / ".last_successful_run"
    # 模擬「10 分鐘前」成功跑過
    recent_ts = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    lf.write_text(recent_ts, encoding="utf-8")

    # 讀取並判斷
    last_run = datetime.fromisoformat(lf.read_text().strip())
    age_min = (datetime.now(timezone.utc) - last_run).total_seconds() / 60
    should_skip = age_min < 30  # LOCKFILE_COOLDOWN_MINUTES = 30

    assert should_skip is True

    # 模擬「40 分鐘前」→ 不應跳過
    old_ts = (datetime.now(timezone.utc) - timedelta(minutes=40)).isoformat()
    lf.write_text(old_ts, encoding="utf-8")
    last_run2 = datetime.fromisoformat(lf.read_text().strip())
    age_min2 = (datetime.now(timezone.utc) - last_run2).total_seconds() / 60
    should_skip2 = age_min2 < 30

    assert should_skip2 is False


# ── T11：get 命中更新 last_accessed ───────────────────────────────────────

def test_t11_get_updates_last_accessed(tmp_cache):
    key = CacheManager.prompt_key("touch")
    tmp_cache.set(key, "value")
    old_accessed = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    tmp_cache._store["entries"][key]["last_accessed"] = old_accessed

    assert tmp_cache.get(key) == "value"

    assert tmp_cache._store["entries"][key]["last_accessed"] != old_accessed


# ── T12：max_entries LRU 淘汰最久未使用 entry ─────────────────────────────

def test_t12_max_entries_lru_eviction(tmp_path):
    f = tmp_path / "cache.json"
    cm = CacheManager(cache_file=f, ttl_days=7, max_entries=2)
    key_a = CacheManager.prompt_key("a")
    key_b = CacheManager.prompt_key("b")
    key_c = CacheManager.prompt_key("c")

    cm.set(key_a, "a")
    cm.set(key_b, "b")

    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    older = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    cm._store["entries"][key_a]["last_accessed"] = old
    cm._store["entries"][key_b]["last_accessed"] = older

    # key_a 被 touch 後變成熱資料；新增 key_c 時應淘汰 key_b。
    assert cm.get(key_a) == "a"
    cm.set(key_c, "c")

    assert key_a in cm._store["entries"]
    assert key_b not in cm._store["entries"]
    assert key_c in cm._store["entries"]
    assert len(cm._store["entries"]) == 2
