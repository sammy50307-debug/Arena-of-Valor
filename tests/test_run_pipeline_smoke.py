"""P114 run_pipeline 編排層 smoke 測試（體檢 #1）。

補 main.run_pipeline 的「搜集→分析→報告→manifest」編排接線迴歸網——這條接線過去零測試覆蓋，
是「綠燈假象/待 cron 終驗」（STR8 收斂、B-023/027）的結構性根因。

兩條路徑（阿喜核准）：
- production：dry_run=True + monkeypatch 真實爬蟲（Step1）
- showcase：showcase=True（Step1 寫死 12 筆，零爬蟲 mock）
共用：Step2 analyzer mock（showcase 也會打 LLM，故兩條都要 mock）+ tmp dirs + indexer/copy2 no-op。

誠實邊界：本測試覆蓋【編排接線】，不覆蓋 analyze_posts 內部（B-023 那類 LLM 重建 bug 由
tests/test_sentiment_published_date.py 契約測試守）；後段（報告→閘門→promote）已由
test_self_heal_replay / test_replay_run 覆蓋。本測試聚焦上游 + 編排。
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import main as aov_main
import reporter.generator as gen_mod
from scrapers.tavily_searcher import SearchResult

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git_porcelain():
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                         capture_output=True, text=True)
    return out.stdout


def _fixture_results():
    return [
        SearchResult(title="芽芽護盾教學", content="芽芽的護盾增強很有感", url="https://example.com/p1",
                     region="TW", platform="Website", score=0.95),
        SearchResult(title="台服平衡調整公告", content="多名射手遭削弱", url="https://example.com/p2",
                     region="TW", platform="Facebook", score=0.90),
        SearchResult(title="芽芽出裝討論", content="半坦還是全法", url="https://example.com/p3",
                     region="TW", platform="Forum", score=0.85),
    ]


# ── 假元件（控 Step1/Step2 的 IO 邊界，避真實網路/LLM）──
class _FakeCacheMgr:
    def get_stats(self):
        return {"total_l1_hits": 0, "total_l2_hits": 0, "total_apify_hits": 0, "total_misses": 0}

    def increment_stat(self, *a, **k):
        pass

    def hero_key(self, *a, **k):
        return None

    def get(self, *a, **k):
        return None


class _FakeLLM:
    def __init__(self):
        self.cache_manager = _FakeCacheMgr()
        self.last_fallback_used = False


class _FakeAnalyzer:
    def __init__(self, *a, **k):
        self.llm = _FakeLLM()

    def _provider_diagnostics(self):
        return {}

    async def analyze_posts(self, search_results, showcase=False, hero_name=None, date_str=None):
        posts = []
        for r in search_results:
            p = r.to_dict() if hasattr(r, "to_dict") else dict(r)
            posts.append({"post": p, "analysis": {"sentiment": "neutral", "summary": "smoke",
                                                  "sentiment_score": 0.5}})
        return {
            "posts": posts,
            "is_showcase": bool(showcase),
            "quota_error": False,
            "contract_status": "ok",
            "contract_errors": [],
            "local_analysis_status": "ok",
            "fallback_reason": "",
            "analysis_source": "llm",
            "provider_diagnostics": {},
        }

    async def generate_daily_summary(self, analyzed_posts, date=None, showcase=False):
        return {
            "date": date,
            "overview": "smoke 編排測試",
            "overall": {"sentiment_score": 0.5, "trend": "Stable"},
            "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 1},
            "hero_focus": {"name": "芽芽", "summary": "smoke"},
            "_meta": {"mode": "showcase" if showcase else "production"},
        }

    def _empty_summary(self, date=None, showcase=False):
        return {
            "date": date, "overview": "", "overall": {"sentiment_score": 0.5, "trend": "Stable"},
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}, "_meta": {},
        }


class _FakeStats:
    def __init__(self, *a, **k):
        pass


class _FakeAudio:
    def __init__(self, *a, **k):
        pass

    async def generate(self, *a, **k):
        return None


class _FakeWaterfall:
    def __init__(self, *a, **k):
        pass

    async def search(self, *a, **k):
        return _fixture_results()


class _FakeEmptyScraper:
    """Dcard/巴哈：smoke 回空（上游主力走 WaterfallSearcher fixture）。"""
    def __init__(self, *a, **k):
        pass

    async def search(self, *a, **k):
        return []

    async def fetch_board_latest(self, *a, **k):
        return []


def _isolate(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    reports_dir = data_dir / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(aov_main.config, "DATA_DIR", data_dir)
    monkeypatch.setattr(aov_main.config, "REPORTS_DIR", reports_dir)
    # Step2 共用 mock（showcase 也打 LLM，兩條都要）
    monkeypatch.setattr(aov_main, "SentimentAnalyzer", _FakeAnalyzer)
    monkeypatch.setattr(aov_main, "HeroStatsScraper", _FakeStats)
    monkeypatch.setattr(aov_main, "AudioBriefingGenerator", _FakeAudio)
    # 隔離真 repo 寫入（沿用 P112 手法）
    monkeypatch.setattr(gen_mod._indexer, "save_index", lambda *a, **k: None)
    import types
    monkeypatch.setattr(gen_mod, "shutil", types.SimpleNamespace(copy2=lambda *a, **k: None))
    monkeypatch.chdir(tmp_path)
    return data_dir, reports_dir


def _assert_pipeline_artifacts(data_dir, reports_dir):
    import glob
    compact = None
    raws = list(data_dir.glob("raw_*.json"))
    assert raws, "Step1 應產出 raw_*.json"
    analyses = list(data_dir.glob("analysis_*.json"))
    assert analyses, "Step2 應產出 analysis_*.json"
    reports = list(reports_dir.glob("aov_report_*.html"))
    assert reports, "Step3 應產出報告 html"
    manifests = list(data_dir.glob("runs/*/run_manifest.json"))
    assert manifests, "Step4.5 應產出 run_manifest.json"
    m = json.loads(manifests[0].read_text(encoding="utf-8"))
    for key in ("schema_version", "run_date", "status", "mode", "paths", "quality", "eligibility"):
        assert key in m, f"manifest 缺合約欄位 {key}"


def test_run_pipeline_production_wiring(tmp_path, monkeypatch):
    """production 路徑（dry_run=True）：monkeypatch 真實爬蟲，跑完編排產出四檔。"""
    data_dir, reports_dir = _isolate(tmp_path, monkeypatch)
    monkeypatch.setattr(aov_main, "WaterfallSearcher", _FakeWaterfall)
    monkeypatch.setattr(aov_main, "DcardScraper", _FakeEmptyScraper)
    monkeypatch.setattr(aov_main, "BahamutScraper", _FakeEmptyScraper)
    before = _git_porcelain()

    asyncio.run(aov_main.run_pipeline(dry_run=True))

    _assert_pipeline_artifacts(data_dir, reports_dir)
    assert _git_porcelain() == before, "run_pipeline 編排不得弄髒真 repo（git status 零新增）"


def test_run_pipeline_showcase_wiring(tmp_path, monkeypatch):
    """showcase 路徑：Step1 寫死資料，零爬蟲 mock，跑完編排產出四檔。"""
    data_dir, reports_dir = _isolate(tmp_path, monkeypatch)

    asyncio.run(aov_main.run_pipeline(showcase=True, dry_run=True))

    _assert_pipeline_artifacts(data_dir, reports_dir)
