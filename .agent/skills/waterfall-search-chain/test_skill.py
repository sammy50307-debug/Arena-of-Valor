"""
瀑布式輪用搜尋鏈 測試套件 (Phase 56)

執行：py .agent/skills/waterfall-search-chain/test_skill.py
"""
import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import httpx
from scrapers.tavily_searcher import SearchResult
from scrapers.waterfall_searcher import WaterfallSearcher, _is_quota_error

logging.basicConfig(level=logging.WARNING)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results_log = []


def test(name: str, ok: bool, detail: str = ""):
    status = PASS if ok else FAIL
    msg = f"  {status}  {name}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    results_log.append(ok)


# ── Test 1：額度耗盡偵測（429）──────────────────────────
def t1_quota_detection_429():
    req = httpx.Request("GET", "https://api.tavily.com/search")
    resp = httpx.Response(429, request=req)
    exc = httpx.HTTPStatusError("429", request=req, response=resp)
    test("額度偵測：429 → is_quota_error=True", _is_quota_error(exc))


# ── Test 2：額度耗盡偵測（402）──────────────────────────
def t2_quota_detection_402():
    req = httpx.Request("GET", "https://api.tavily.com/search")
    resp = httpx.Response(402, request=req)
    exc = httpx.HTTPStatusError("402", request=req, response=resp)
    test("額度偵測：402 → is_quota_error=True", _is_quota_error(exc))


# ── Test 3：非額度錯誤（500）不誤判 ──────────────────────
def t3_non_quota_500():
    req = httpx.Request("GET", "https://api.tavily.com/search")
    resp = httpx.Response(500, request=req)
    exc = httpx.HTTPStatusError("500", request=req, response=resp)
    test("非額度錯誤：500 → is_quota_error=False", not _is_quota_error(exc))


# ── Test 4：Tavily 成功 → 直接回傳，不觸碰 DDG ──────────
async def t4_tavily_success_no_ddg():
    mock_results = [
        SearchResult(title="測試文章", content="...", url="https://example.com/1", platform="web")
    ]
    searcher = WaterfallSearcher()
    # 替換 Tavily source 為 mock
    if not searcher._sources:
        test("Tavily 成功不觸碰 DDG", False, "無搜尋源")
        return
    original_sources = searcher._sources[:]
    first_name, first_src = original_sources[0]
    first_src.search = AsyncMock(return_value=mock_results)
    if len(original_sources) > 1:
        second_name, second_src = original_sources[1]
        second_src.search = AsyncMock(return_value=[])

    results = await searcher.search(max_results_per_region=1)
    ok = (len(results) == 1 and results[0].title == "測試文章")
    if len(original_sources) > 1:
        second_src.search.assert_not_called() if ok else None
    test("Tavily 成功 → 直接回傳，DDG 未被呼叫", ok)


# ── Test 5：Tavily 429 → 自動切換 DDG ───────────────────
async def t5_tavily_429_fallback_ddg():
    mock_ddg_results = [
        SearchResult(title="DDG文章", content="...", url="https://dcard.tw/1", platform="dcard")
    ]
    searcher = WaterfallSearcher()
    if len(searcher._sources) < 2:
        test("Tavily 429 → 切換 DDG", False, "搜尋源不足 2 個")
        return

    req = httpx.Request("GET", "https://api.tavily.com/search")
    resp = httpx.Response(429, request=req)
    quota_exc = httpx.HTTPStatusError("429", request=req, response=resp)

    _, tavily_src = searcher._sources[0]
    _, ddg_src = searcher._sources[1]
    tavily_src.search = AsyncMock(side_effect=quota_exc)
    ddg_src.search = AsyncMock(return_value=mock_ddg_results)

    results = await searcher.search(max_results_per_region=1)
    ok = (len(results) == 1 and results[0].title == "DDG文章")
    test("Tavily 429 → 自動切換 DDG 並取得結果", ok)


# ── 執行 ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  Phase 56：瀑布式輪用搜尋鏈 — 自動化測試")
print("=" * 55)

t1_quota_detection_429()
t2_quota_detection_402()
t3_non_quota_500()
asyncio.run(t4_tavily_success_no_ddg())
asyncio.run(t5_tavily_429_fallback_ddg())

print("=" * 55)
passed = sum(results_log)
total = len(results_log)
print(f"  結果：{passed}/{total} 通過\n")
if passed < total:
    sys.exit(1)
