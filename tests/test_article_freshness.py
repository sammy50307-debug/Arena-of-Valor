"""P110 v2 防復發測試：文章凍結修復（撈新文 + 去重 + 凍結偵測器）。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from scrapers.date_normalizer import normalize_published_date
from scrapers.bahamut_scraper import BahamutScraper


# ── S1: date_normalizer 裸 MM-DD（板列表新文時間格式）──────────────
def test_date_normalizer_bare_mmdd():
    now = datetime(2026, 6, 13, 12, 0)
    assert normalize_published_date("06-10", now=now) == "2026-06-10 00:00:00"
    # 跨年回退：12-25 在 6 月視為去年
    assert normalize_published_date("12-25", now=now) == "2025-12-25 00:00:00"
    # 既有格式不回歸
    assert normalize_published_date("06-10 14:30", now=now) == "2026-06-10 14:30:00"
    assert normalize_published_date("昨天 17:24", now=now) == "2026-06-12 17:24:00"
    assert normalize_published_date("2026-06-01", now=now) == "2026-06-01 00:00:00"
    assert normalize_published_date("亂碼xyz", now=now) is None


# ── S3: 凍結偵測器 lint_freshness（純函式）─────────────────────────
def _import_freshness():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import check_report_freshness as crf
    return crf


def test_freshness_detector_frozen():
    crf = _import_freshness()
    sidecars = [
        {"report_date": "2026-06-10", "top5_hash": "AAA"},
        {"report_date": "2026-06-11", "top5_hash": "AAA"},
        {"report_date": "2026-06-12", "top5_hash": "AAA"},
    ]
    frozen, streak, detail = crf.lint_freshness(sidecars, threshold=3)
    assert frozen is True
    assert "最近 3 筆報告相同" in detail


def test_freshness_detector_rotating():
    crf = _import_freshness()
    sidecars = [
        {"report_date": "2026-06-10", "top5_hash": "AAA"},
        {"report_date": "2026-06-11", "top5_hash": "BBB"},
        {"report_date": "2026-06-12", "top5_hash": "CCC"},
    ]
    frozen, streak, detail = crf.lint_freshness(sidecars, threshold=3)
    assert frozen is False


def test_freshness_detector_insufficient():
    crf = _import_freshness()
    sidecars = [{"report_date": "2026-06-12", "top5_hash": "AAA"}]
    frozen, streak, detail = crf.lint_freshness(sidecars, threshold=3)
    assert frozen is False
    assert "資料不足" in detail


# ── S1: fetch_board_latest 跳過 sticky 置頂列 ─────────────────────
class _FakeResp:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class _FakeClient:
    def __init__(self, html, *, raise_exc=None, captured=None):
        self._html = html
        self._raise = raise_exc
        self._captured = captured if captured is not None else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, params=None):
        self._captured["params"] = params
        if self._raise:
            raise self._raise
        return _FakeResp(self._html)


_BOARD_HTML = """
<table>
  <tr class="b-list__row b-list__row--sticky">
    <td class="b-list__main"><a href="C.php?bsn=30518&snA=1">
      <p class="b-list__main__title">【置頂】板務公告</p></a></td>
  </tr>
  <tr class="b-list__row">
    <td class="b-list__main"><a href="C.php?bsn=30518&snA=2">
      <p class="b-list__main__title">最新討論文章</p></a></td>
    <td class="b-list__time"><span class="b-list__time__edittime"><a>1 小時前</a></span></td>
  </tr>
</table>
"""


@pytest.mark.asyncio
async def test_board_latest_skips_sticky(monkeypatch):
    import scrapers.bahamut_scraper as bs
    captured = {}
    monkeypatch.setattr(bs.httpx, "AsyncClient",
                        lambda **kw: _FakeClient(_BOARD_HTML, captured=captured))
    results = await BahamutScraper().fetch_board_latest(max_results=10)
    titles = [r.title for r in results]
    assert "最新討論文章" in titles          # 非 sticky 收入
    assert not any("置頂" in t for t in titles)  # sticky 置頂跳過
    # 鎖根因①核心契約：板最新列表 ≠ 標題搜尋（B.php 不帶 q/qt，防有人退回搜尋常青舊文而測試仍綠）
    assert captured["params"].get("bsn")
    assert "q" not in captured["params"]
    assert "qt" not in captured["params"]


@pytest.mark.asyncio
async def test_board_latest_graceful_on_exception(monkeypatch):
    """fetch_board_latest 抓取例外時回 []（main 雙軌靠關鍵字 search 兜底）。"""
    import scrapers.bahamut_scraper as bs
    monkeypatch.setattr(bs.httpx, "AsyncClient",
                        lambda **kw: _FakeClient("", raise_exc=RuntimeError("boom")))
    assert await BahamutScraper().fetch_board_latest(max_results=10) == []


@pytest.mark.asyncio
async def test_board_latest_graceful_on_dom_drift(monkeypatch):
    """板列表 DOM 漂移（無 tr.b-list__row）時回 [] 而非拋例外。"""
    import scrapers.bahamut_scraper as bs
    monkeypatch.setattr(bs.httpx, "AsyncClient",
                        lambda **kw: _FakeClient("<html><body>no rows</body></html>"))
    assert await BahamutScraper().fetch_board_latest(max_results=10) == []


# ── S2: top5_news 去重——同篇芽芽文不一頁渲染兩次 ──────────────────
def test_top5_news_excludes_yaya(tmp_path):
    from reporter.generator import ReportGenerator
    gen = ReportGenerator()
    yaya_url = "https://forum.gamer.com.tw/C.php?bsn=30518&snA=YAYA"
    analyzed = [
        {"post": {"platform": "bahamut", "url": yaya_url, "title": "芽芽攻略教學",
                  "published_date": "2026-06-12", "region": "TW"},
         "analysis": {"summary": "芽芽很強", "sentiment": "positive"}},
    ]
    # 4 篇一般文（不同平台、有日期）湊最新動態
    for i, plat in enumerate(["dcard", "youtube", "facebook", "bahamut"]):
        analyzed.append({
            "post": {"platform": plat, "url": f"https://example.com/g{i}",
                     "title": f"一般新聞{i}", "published_date": "2026-06-12", "region": "TW"},
            "analysis": {"summary": f"一般{i}", "sentiment": "neutral"},
        })
    daily_summary = {
        "date": "2026-06-12", "overview": "測試去重",
        "hero_focus": {"name": "芽芽"},
        "combat_stats": {},
        "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 4},
    }
    report_file = gen.generate(daily_summary, analyzed_posts=analyzed, output_dir=tmp_path, promote=False)
    html = report_file.read_text(encoding="utf-8")

    # 芽芽文卡片連結（<a href>）應只出現 1 次（芽芽觀察室），不在最新動態詳情重複渲染
    import re
    card_links = re.findall(r'href="[^"]*snA=YAYA[^"]*"', html)
    assert len(card_links) == 1, (
        f"芽芽文卡片連結應只出現 1 次（只在芽芽觀察室），實際 {len(card_links)} 次"
        f"（>1 = 同篇芽芽文一頁渲染兩次未修）"
    )


# ── P110 v2 一致性硬化：freshness 指紋對 utm 參數穩定（與 dedup 身分同源）──────
def _read_sidecar(gen, tmp_path, news, yaya):
    import json
    gen._write_freshness_sidecar(tmp_path, "2026-06-12", news, yaya)
    return json.loads(
        (tmp_path / "aov_report_2026-06-12.freshness.json").read_text(encoding="utf-8")
    )


def test_freshness_hash_stable_across_utm(tmp_path):
    """同一文章 raw URL 僅差 utm_* 參數 → top5_hash 必須相同（指紋對齊 dedup 身分）。"""
    from reporter.generator import ReportGenerator
    gen = ReportGenerator()
    base = "https://example.com/article-1"

    # A 組：raw url 帶 utm，無 picker.norm_url → 走 fallback _normalize_url 路徑
    cards_a = [{"post": {"url": f"{base}?utm_source=fb&utm_campaign=x"}}]
    # B 組：raw url 乾淨且帶 picker.norm_url → 走 norm_url 優先路徑
    cards_b = [{"post": {"url": base}, "picker": {"norm_url": base}}]

    hash_a = _read_sidecar(gen, tmp_path, cards_a, [])["top5_hash"]
    hash_b = _read_sidecar(gen, tmp_path, cards_b, [])["top5_hash"]

    assert hash_a == hash_b, (
        f"raw URL 僅差 utm_* 參數應產生相同 top5_hash，"
        f"實際 A={hash_a} B={hash_b}（指紋與 dedup 身分分歧 = 未正規化）"
    )


def test_freshness_prefers_picker_norm_url(tmp_path):
    """picker.norm_url 存在時優先採用（即使 raw url 帶追蹤參數），確保與去重管線同源。"""
    from reporter.generator import ReportGenerator
    gen = ReportGenerator()
    norm = "https://example.com/post-9"
    # raw url 帶 utm/ref，但 picker.norm_url 已是乾淨值 → sidecar 應收正規化後的 norm
    cards = [{"post": {"url": f"{norm}?utm_medium=email&ref=nl"},
              "picker": {"norm_url": norm}}]
    sc = _read_sidecar(gen, tmp_path, cards, [])
    assert sc["news_urls"] == [norm], (
        f"應採用 picker.norm_url={norm}，實際 {sc['news_urls']}"
    )
