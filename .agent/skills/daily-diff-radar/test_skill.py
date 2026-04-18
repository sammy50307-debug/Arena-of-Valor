"""
Daily Diff Radar 測試套件 (Phase 58)

執行：py .agent/skills/daily-diff-radar/test_skill.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from importlib import util
spec = util.spec_from_file_location(
    "radar",
    Path(__file__).parent / "scripts" / "radar.py",
)
radar_mod = util.module_from_spec(spec)
spec.loader.exec_module(radar_mod)

DailyDiffRadar = radar_mod.DailyDiffRadar

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


def make_sample(data_dir: Path, date: str, payload: dict):
    p = data_dir / f"analysis_{date}.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def fresh_radar():
    tmp = Path(tempfile.mkdtemp())
    return DailyDiffRadar(data_dir=tmp), tmp


# ── Test 1：無檔案 → 回傳 error ────────────────────────
def t1_empty_dir():
    r, _ = fresh_radar()
    out = r.radar()
    test("空目錄：回傳 error 欄位", "error" in out)


# ── Test 2：只有一份 → 回傳 error ─────────────────────
def t2_only_one():
    r, d = fresh_radar()
    make_sample(d, "20260418", {"overall": {"sentiment_score": 0.8}, "total_posts": 10})
    out = r.radar()
    test("僅一份檔：回傳 error（需至少 2）", "error" in out)


# ── Test 3：基本差異計算 ──────────────────────────────
def t3_basic_diff():
    r, d = fresh_radar()
    make_sample(d, "20260418", {
        "overall": {"sentiment_score": 0.70, "trend": "Stable"},
        "total_posts": 10,
        "hero_stats": {"芽芽": {"avg_sentiment": 0.8}},
        "platform_breakdown": {"dcard": {"post_count": 3}},
    })
    make_sample(d, "20260419", {
        "overall": {"sentiment_score": 0.85, "trend": "Upward"},
        "total_posts": 13,
        "hero_stats": {"芽芽": {"avg_sentiment": 0.9}, "克里希": {"avg_sentiment": 0.5}},
        "platform_breakdown": {"dcard": {"post_count": 5}, "bahamut": {"post_count": 2}},
    })
    out = r.radar()
    ok = (
        abs(out["sentiment_delta"] - 0.15) < 0.001
        and out["volume_delta"] == 3
        and abs(out["volume_delta_pct"] - 30.0) < 0.1
        and out["new_heroes"] == ["克里希"]
        and out["dropped_heroes"] == []
        and "芽芽" in out["hero_sentiment_shifts"]
        and out["trend_change"] == "Stable → Upward"
    )
    test("基本差異：sentiment/volume/hero/trend 皆正確", ok,
         detail=f"Δsent={out['sentiment_delta']}, Δvol={out['volume_delta']}, new={out['new_heroes']}")


# ── Test 4：Alert HIGH 門檻 (Δvol ≥ 50%) ───────────────
def t4_alert_high_volume():
    r, d = fresh_radar()
    make_sample(d, "20260418", {
        "overall": {"sentiment_score": 0.5}, "total_posts": 10,
    })
    make_sample(d, "20260419", {
        "overall": {"sentiment_score": 0.5}, "total_posts": 20,  # +100%
    })
    out = r.radar()
    test("Alert HIGH：聲量 +100% → HIGH",
         out["alert_level"] == "HIGH",
         detail=f"level={out['alert_level']}, Δvol%={out['volume_delta_pct']}")


# ── Test 5：Alert HIGH 門檻 (Δsentiment ≥ 0.3) ─────────
def t5_alert_high_sentiment():
    r, d = fresh_radar()
    make_sample(d, "20260418", {
        "overall": {"sentiment_score": 0.8}, "total_posts": 10,
    })
    make_sample(d, "20260419", {
        "overall": {"sentiment_score": 0.4}, "total_posts": 10,  # Δ=-0.4
    })
    out = r.radar()
    test("Alert HIGH：情緒 Δ=-0.4 → HIGH",
         out["alert_level"] == "HIGH",
         detail=f"level={out['alert_level']}, Δsent={out['sentiment_delta']}")


# ── Test 6：Alert LOW（小幅變化）──────────────────────
def t6_alert_low():
    r, d = fresh_radar()
    make_sample(d, "20260418", {
        "overall": {"sentiment_score": 0.80}, "total_posts": 100,
    })
    make_sample(d, "20260419", {
        "overall": {"sentiment_score": 0.82}, "total_posts": 105,  # +5%
    })
    out = r.radar()
    test("Alert LOW：微小變化", out["alert_level"] == "LOW",
         detail=f"level={out['alert_level']}")


# ── 執行 ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  Phase 58：Daily Diff Radar — 自動化測試")
print("=" * 55)

t1_empty_dir()
t2_only_one()
t3_basic_diff()
t4_alert_high_volume()
t5_alert_high_sentiment()
t6_alert_low()

print("=" * 55)
passed = sum(results_log)
total = len(results_log)
print(f"  結果：{passed}/{total} 通過\n")
if passed < total:
    sys.exit(1)
