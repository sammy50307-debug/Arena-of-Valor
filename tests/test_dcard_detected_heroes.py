"""
P107 S2 根因 C 回歸測試：Dcard 爬蟲建立 SearchResult 時要正確填入 detected_heroes。

過去 _parse_ddg_results 沒設 detected_heroes（預設空 []），導致 Dcard 來源的
英雄偵測全失效。此測試用最小 mock HTML 直接驗證解析邏輯，不依賴真實 DDG 搜尋。
"""
from __future__ import annotations

from bs4 import BeautifulSoup

import config
from scrapers.dcard_scraper import DcardScraper


def _parse(html: str, keyword: str):
    """以最小 HTML 餵入 _parse_ddg_results，回傳 SearchResult 列表。"""
    soup = BeautifulSoup(html, "html.parser")
    return DcardScraper()._parse_ddg_results(soup, keyword=keyword, max_results=10, region="TW")


def test_detects_focus_hero_in_title():
    # 焦點英雄「芽芽」在預設 watchlist 內，確保前提成立
    assert "芽芽" in config.HERO_WATCHLIST

    html = (
        '<a class="result__a" href="https://www.dcard.tw/f/aov/p/123">'
        "芽芽改版後排位心得分享</a>"
    )
    results = _parse(html, keyword="芽芽")

    assert len(results) == 1
    assert results[0].detected_heroes == ["芽芽"]


def test_no_focus_hero_yields_empty_list():
    # 標題不含任何 watchlist 英雄，detected_heroes 應為空
    html = (
        '<a class="result__a" href="https://www.dcard.tw/f/aov/p/456">'
        "傳說對決新賽季更新總整理</a>"
    )
    results = _parse(html, keyword="傳說對決")

    assert len(results) == 1
    assert results[0].detected_heroes == []
