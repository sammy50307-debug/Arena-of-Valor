"""Rich Push Formatter 測試套件 (Phase 59)"""
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from formatter import RichPushFormatter, arrow

results = []

def test(name, ok, detail=""):
    mark = "✅" if ok else "❌"
    print(f"  {mark} {name}" + (f"  ({detail})" if detail else ""))
    results.append(ok)


def t1_arrow():
    test("箭頭：正值顯示 ⬆️", "⬆️" in arrow(0.5, "+.2f"))
    test("箭頭：負值顯示 ⬇️", "⬇️" in arrow(-0.5, "+.2f"))
    test("箭頭：零值顯示 ➡️", "➡️" in arrow(0.0, "+.2f"))


def t2_format_diff_basic():
    f = RichPushFormatter()
    diff = {
        "today_date": "2026-04-19",
        "yesterday_date": "2026-04-18",
        "sentiment_delta": 0.15,
        "volume_delta": 5,
        "volume_delta_pct": 25.0,
        "trend_change": "Stable → Upward",
        "new_heroes": ["凱恩"],
        "dropped_heroes": [],
        "hero_sentiment_shifts": {"芽芽": 0.2},
        "platform_changes": {"dcard": {"today": 8, "yesterday": 5, "delta": 3}},
        "alert_level": "MEDIUM",
    }
    md = f.format_diff(diff)
    ok = all(k in md for k in ["🟡", "2026-04-19", "MEDIUM", "凱恩", "芽芽", "dcard"])
    test("format_diff：關鍵欄位齊全", ok)


def t3_format_diff_error():
    f = RichPushFormatter()
    md = f.format_diff({"error": "no data"})
    test("format_diff：error 有警示圖示", "⚠️" in md and "no data" in md)


def t4_format_diff_alert_emoji():
    f = RichPushFormatter()
    base = {"today_date": "t", "yesterday_date": "y", "sentiment_delta": 0,
            "volume_delta": 0, "volume_delta_pct": 0, "trend_change": "-"}
    for level, emoji in [("HIGH", "🔴"), ("MEDIUM", "🟡"), ("LOW", "🟢")]:
        md = f.format_diff({**base, "alert_level": level})
        test(f"alert {level} → {emoji}", emoji in md)


def t5_format_analysis():
    f = RichPushFormatter()
    ana = {
        "overall": {"sentiment_score": 0.72, "trend": "Upward"},
        "total_posts": 25,
        "hero_stats": {"芽芽": {"avg_sentiment": 0.8}, "悟空": {"avg_sentiment": 0.5}},
        "platform_breakdown": {"dcard": {"post_count": 10}, "bahamut": {"post_count": 15}},
    }
    md = f.format_analysis(ana, date="2026-04-19")
    ok = all(k in md for k in ["2026-04-19", "0.72", "Upward", "芽芽", "bahamut", "25"])
    test("format_analysis：單日快照輸出完整", ok)


print("\n" + "=" * 55)
print("  Phase 59：Rich Push Formatter — 自動化測試")
print("=" * 55)
t1_arrow()
t2_format_diff_basic()
t3_format_diff_error()
t4_format_diff_alert_emoji()
t5_format_analysis()
print("=" * 55)
passed = sum(results)
total = len(results)
print(f"  結果：{passed}/{total} 通過\n")
if passed < total:
    sys.exit(1)
