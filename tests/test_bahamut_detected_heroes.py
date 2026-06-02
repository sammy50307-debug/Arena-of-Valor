"""
P107 S2 根因 C — 巴哈爬蟲 SearchResult.detected_heroes 偵測測試。

驗證 BahamutScraper 在建立 SearchResult 時，會依 config.HERO_WATCHLIST
掃描標題並填入 detected_heroes（先前漏設，導致英雄偵測全失效）。

涵蓋兩處建立 SearchResult 的路徑：_parse_row 與 _parse_latest_fallback。
"""

from bs4 import BeautifulSoup

import config
from scrapers.bahamut_scraper import BahamutScraper


def _row(title: str):
    """構造一個最小的巴哈文章列 <tr>，回傳對應的 BeautifulSoup 元素。"""
    html = (
        '<table><tr class="b-list__row">'
        '<td class="b-list__main">'
        f'<a href="C.php?bsn=30518&snA=1"><p class="b-list__main__title">{title}</p></a>'
        '</td>'
        '</tr></table>'
    )
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one("tr.b-list__row")


def test_parse_row_detects_watchlist_hero():
    """標題含焦點英雄「芽芽」→ detected_heroes == ['芽芽']。"""
    scraper = BahamutScraper()
    result = scraper._parse_row(_row("芽芽改版後超強"), keyword="芽芽", region="TW")
    assert result is not None
    assert result.detected_heroes == ["芽芽"]


def test_parse_row_no_focus_hero_is_empty():
    """標題無任何焦點英雄 → detected_heroes == []。"""
    scraper = BahamutScraper()
    # keyword 必須出現在標題（_parse_row 的過濾條件），但「改版」不在 watchlist
    result = scraper._parse_row(_row("新版本改版討論串"), keyword="改版", region="TW")
    assert result is not None
    assert result.detected_heroes == []


def test_parse_latest_fallback_detects_watchlist_hero():
    """fallback 路徑：標題含「皮皮」→ detected_heroes == ['皮皮']。"""
    scraper = BahamutScraper()
    html = (
        '<div><a href="C.php?bsn=30518&snA=2">皮皮新皮膚情報</a></div>'
    )
    soup = BeautifulSoup(html, "html.parser")
    results = scraper._parse_latest_fallback(soup, keyword="皮皮", max_results=5, region="TW")
    assert len(results) == 1
    assert results[0].detected_heroes == ["皮皮"]


def test_watchlist_sanity():
    """前提檢查：config.HERO_WATCHLIST 至少含芽芽，否則上面斷言失去意義。"""
    assert "芽芽" in config.HERO_WATCHLIST
