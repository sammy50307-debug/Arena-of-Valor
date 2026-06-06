"""
P108.3 S2 整合測試 — BahamutScraper._parse_row 接入 date_normalizer。

驗證巴哈爬蟲輸出的 published_date 經正規化為 ISO（相對/短格式），
無法正規化時保留原值（D3 回退，不丟資料），無時間元素維持空字串。
"""
import re

from bs4 import BeautifulSoup

from scrapers.bahamut_scraper import BahamutScraper

_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def _row_with_time(title: str, time_text: str):
    """造含時間元素的巴哈文章列 <tr>。"""
    html = (
        '<table><tr class="b-list__row">'
        '<td class="b-list__main">'
        f'<a href="C.php?bsn=30518&snA=1"><p class="b-list__main__title">{title}</p></a>'
        '</td>'
        f'<td class="b-list__time"><a>{time_text}</a></td>'
        '</tr></table>'
    )
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one("tr.b-list__row")


def test_parse_row_relative_time_normalized_to_iso():
    """相對格式「昨天 22:39」→ published_date 為 ISO（R-030 治本核心）。"""
    scraper = BahamutScraper()
    row = _row_with_time("芽芽改版討論", "昨天 22:39")
    result = scraper._parse_row(row, keyword="芽芽", region="TW")
    assert result is not None
    assert _ISO_RE.match(result.published_date), f"非 ISO: {result.published_date!r}"


def test_parse_row_short_time_normalized_to_iso():
    """短格式「05-29 11:39」→ published_date 為 ISO（月日時分對；年份由補年/回退決定）。"""
    scraper = BahamutScraper()
    row = _row_with_time("芽芽新皮膚", "05-29 11:39")
    result = scraper._parse_row(row, keyword="芽芽", region="TW")
    assert result is not None
    assert _ISO_RE.match(result.published_date)
    assert result.published_date.endswith("05-29 11:39:00")


def test_parse_row_unparseable_time_kept_as_is():
    """無法正規化的時間字串 → 保留原值（D3 回退，不丟資料）。"""
    scraper = BahamutScraper()
    row = _row_with_time("芽芽討論", "某種新格式XYZ")
    result = scraper._parse_row(row, keyword="芽芽", region="TW")
    assert result is not None
    assert result.published_date == "某種新格式XYZ"


def test_parse_row_no_time_element_empty():
    """無時間元素 → published_date 維持空字串（不變）。"""
    scraper = BahamutScraper()
    html = (
        '<table><tr class="b-list__row">'
        '<td class="b-list__main">'
        '<a href="C.php?bsn=30518&snA=1"><p class="b-list__main__title">芽芽討論</p></a>'
        '</td></tr></table>'
    )
    soup = BeautifulSoup(html, "html.parser")
    row = soup.select_one("tr.b-list__row")
    result = scraper._parse_row(row, keyword="芽芽", region="TW")
    assert result is not None
    assert result.published_date == ""
