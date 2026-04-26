"""
test_data_writer.py — Phase 56.5 Stage 4 自動化防護

涵蓋：
  - validate_summary 契約檢查（含巢狀缺欄）
  - coerce_to_schema 補齊（含巢狀補齊）
  - atomic_write_json（正常 / 失敗清 .tmp / 自動建父目錄）
  - 標準 fallback 修補後通過契約（R21 anti-regression）
  - P61 loader 不會載入 _quarantine/ 內容（S3-R10 anti-regression）
  - schema_version.json 路徑守門（S2-R7 anti-regression）
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".agent" / "skills" / "history-trend-query" / "scripts"))

from analyzer.data_writer import (  # noqa: E402
    _SCHEMA_PATH,
    atomic_write_json,
    coerce_to_schema,
    validate_summary,
)


def _healthy() -> dict:
    return {
        "date": "2026-04-26",
        "total_posts": 10,
        "overall": {"sentiment_score": 0.5, "trend": "Stable"},
        "sentiment_distribution": {"positive": 5, "negative": 2, "neutral": 3},
        "platform_breakdown": {},
        "hero_stats": {},
    }


def t1_validate_healthy():
    ok, missing = validate_summary(_healthy())
    assert ok and missing == [], f"健康 dict 應通過：{missing}"


def t2_validate_missing_total_posts():
    d = _healthy(); del d["total_posts"]
    ok, missing = validate_summary(d)
    assert not ok and missing == ["total_posts"], f"應只缺 total_posts：{missing}"


def t3_validate_missing_nested_overall_trend():
    d = _healthy(); del d["overall"]["trend"]
    ok, missing = validate_summary(d)
    assert not ok and "overall.trend" in missing, f"應抓出 overall.trend：{missing}"


def t4_coerce_fills_total_posts():
    d = _healthy(); del d["total_posts"]
    fixed, filled = coerce_to_schema(d)
    ok, missing = validate_summary(fixed)
    assert ok and missing == [], f"coerce 後應通過：{missing}"
    assert "total_posts" in filled, f"應記錄補了 total_posts：{filled}"
    assert fixed["total_posts"] == 0, "預設值應為 0"


def t5_coerce_fills_nested():
    d = _healthy(); del d["overall"]["trend"]
    fixed, filled = coerce_to_schema(d)
    ok, _ = validate_summary(fixed)
    assert ok, "coerce 後應通過巢狀檢查"
    assert "overall.trend" in filled, f"應記錄補了 overall.trend：{filled}"


def t6_atomic_write_normal():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "out.json"
        atomic_write_json(p, _healthy())
        assert p.exists() and p.stat().st_size > 0, "檔案應存在且非空"
        assert not (p.with_suffix(".json.tmp")).exists(), ".tmp 不該殘留"
        loaded = json.loads(p.read_text(encoding="utf-8"))
        assert loaded["total_posts"] == 10


def t7_atomic_write_clean_tmp_on_failure():
    """模擬 json 序列化失敗（含不可序列化物件），確認 .tmp 被清。"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "out.json"
        bad = {"x": object()}
        try:
            atomic_write_json(p, bad)
        except Exception:
            pass
        assert not (p.with_suffix(".json.tmp")).exists(), "失敗後 .tmp 不該殘留"
        assert not p.exists(), "失敗時不該產出目標檔"


def t8_atomic_write_creates_parent_dir():
    with tempfile.TemporaryDirectory() as td:
        nested = Path(td) / "a" / "b" / "c" / "out.json"
        atomic_write_json(nested, _healthy())
        assert nested.exists() and nested.stat().st_size > 0


def t9_fallback_path_passes_contract():
    """R21 anti-regression：標準 fallback 修補後產出必過契約。"""
    import types
    fake = types.ModuleType("dotenv"); fake.load_dotenv = lambda *a, **k: None
    sys.modules["dotenv"] = fake
    from analyzer.sentiment import SentimentAnalyzer  # noqa: E402
    import logging
    a = SentimentAnalyzer.__new__(SentimentAnalyzer); a.logger = logging.getLogger("t")

    posts = [{"analysis": {"sentiment": "neutral"}}] * 12
    out = a._generate_fallback_summary(posts, "2026-03-29", showcase=False)
    ok, missing = validate_summary(out)
    assert ok and missing == [], f"R21 退化：fallback 又缺欄 {missing}"
    assert out["total_posts"] == 12, "total_posts 應等於 posts 長度"


def t10_loader_does_not_scan_quarantine():
    """S3-R10 anti-regression：loader 只掃 data/analysis_*.json、不進 _quarantine/。"""
    from time_series_loader import TimeSeriesLoader

    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td)
        # 健康日
        atomic_write_json(data_dir / "analysis_20260401.json", {**_healthy(), "date": "2026-04-01"})
        # 隔離區放一個會通過契約的檔，loader 若誤掃就會回 ok
        qdir = data_dir / "_quarantine"
        qdir.mkdir()
        atomic_write_json(qdir / "analysis_20260402.json", {**_healthy(), "date": "2026-04-02"})

        loader = TimeSeriesLoader(data_dir=data_dir)
        e1 = loader.load_day("2026-04-01")
        e2 = loader.load_day("2026-04-02")
        assert e1["status"] == "ok", f"健康日應 ok：{e1}"
        assert e2["status"] == "missing", (
            f"隔離區檔不該被當作 04-02 資料載入：{e2}（pattern 漏洞警報）"
        )


def t11_schema_path_exists():
    """S2-R7 anti-regression：契約檔路徑變動會立刻被測試抓到。"""
    assert _SCHEMA_PATH.exists(), (
        f"契約檔不見了：{_SCHEMA_PATH}（P61 skill 改路徑會炸 P56.5）"
    )
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "total_posts" in schema["required_fields"]["top_level"], (
        "schema top_level 必須含 total_posts"
    )


TESTS: List[Tuple[str, callable]] = [
    ("T1 validate 健康 dict", t1_validate_healthy),
    ("T2 validate 缺 total_posts", t2_validate_missing_total_posts),
    ("T3 validate 缺 overall.trend (巢狀)", t3_validate_missing_nested_overall_trend),
    ("T4 coerce 補 total_posts", t4_coerce_fills_total_posts),
    ("T5 coerce 補 overall.trend (巢狀)", t5_coerce_fills_nested),
    ("T6 atomic_write 正常路徑", t6_atomic_write_normal),
    ("T7 atomic_write 失敗清 .tmp", t7_atomic_write_clean_tmp_on_failure),
    ("T8 atomic_write 自動建父目錄", t8_atomic_write_creates_parent_dir),
    ("T9 R21 anti-regression: fallback 過契約", t9_fallback_path_passes_contract),
    ("T10 S3-R10 anti-regression: loader 不掃 _quarantine/", t10_loader_does_not_scan_quarantine),
    ("T11 S2-R7 anti-regression: schema 路徑存在", t11_schema_path_exists),
]


def main() -> int:
    passed = failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
            failed += 1
    print("=" * 60)
    print(f"Phase 56.5 — data/ 上游髒檔治本 自動化防護")
    print("=" * 60)
    print("-" * 60)
    print(f"通過 {passed} / {passed + failed}")
    if failed == 0:
        print("S4 自動化防護全綠 ✅")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
