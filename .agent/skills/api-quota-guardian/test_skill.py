"""
API Quota Guardian 測試套件 (Phase 57)

執行：py .agent/skills/api-quota-guardian/test_skill.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from importlib import util
spec = util.spec_from_file_location(
    "guardian",
    Path(__file__).parent / "scripts" / "guardian.py",
)
guardian_mod = util.module_from_spec(spec)
spec.loader.exec_module(guardian_mod)

APIQuotaGuardian = guardian_mod.APIQuotaGuardian

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


def new_guardian(limit=100):
    """為每個測試建立獨立 state 檔。"""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    tmp.write("{}")
    tmp.close()
    return APIQuotaGuardian(
        provider="tavily",
        monthly_limit=limit,
        state_path=Path(tmp.name),
    )


# ── Test 1：初始狀態 used=0, verdict=OK ────────────────
def t1_initial_state():
    g = new_guardian()
    s = g.status()
    test("初始狀態：used=0 / verdict=OK",
         s["used"] == 0 and s["verdict"] == "OK")


# ── Test 2：record(n) 正確累加 ────────────────────────
def t2_record_increments():
    g = new_guardian()
    g.record(3)
    g.record(2)
    s = g.status()
    test("record 累加：3+2=5", s["used"] == 5)


# ── Test 3：OK → WARN 門檻 ────────────────────────────
def t3_warn_threshold():
    g = new_guardian(limit=100)
    g.record(79)
    v79 = g.status()["verdict"]
    g.record(1)  # 80
    v80 = g.status()["verdict"]
    test("79%=OK, 80%=WARN", v79 == "OK" and v80 == "WARN",
         detail=f"79→{v79}, 80→{v80}")


# ── Test 4：CRITICAL 門檻 + should_fallback ─────────────
def t4_critical_threshold():
    g = new_guardian(limit=100)
    g.record(94)
    v94 = g.status()["verdict"]
    sf94 = g.should_fallback()
    g.record(1)  # 95
    v95 = g.status()["verdict"]
    sf95 = g.should_fallback()
    ok = (v94 == "WARN" and not sf94 and v95 == "CRITICAL" and sf95)
    test("94%=WARN/should_fallback=False, 95%=CRITICAL/True", ok,
         detail=f"94→{v94}/{sf94}, 95→{v95}/{sf95}")


# ── Test 5：持久化（同檔案讀兩次得一致）──────────────
def t5_persistence():
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    tmp.write("{}")
    tmp.close()
    g1 = APIQuotaGuardian("tavily", 100, state_path=Path(tmp.name))
    g1.record(42)
    g2 = APIQuotaGuardian("tavily", 100, state_path=Path(tmp.name))
    test("持久化：新實例讀檔 used=42", g2.status()["used"] == 42)


# ── Test 6：月份 rollover（模擬舊月份資料）────────────
def t6_month_rollover():
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    # 手動寫入 1999-01 的舊狀態
    tmp.write(json.dumps({
        "tavily": {"month": "1999-01", "used": 999, "limit": 100}
    }))
    tmp.close()
    g = APIQuotaGuardian("tavily", 100, state_path=Path(tmp.name))
    s = g.status()
    test("月份 rollover：1999-01 舊資料自動歸零",
         s["used"] == 0 and s["month"] != "1999-01",
         detail=f"月份={s['month']}, used={s['used']}")


# ── 執行 ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  Phase 57：API Quota Guardian — 自動化測試")
print("=" * 55)

t1_initial_state()
t2_record_increments()
t3_warn_threshold()
t4_critical_threshold()
t5_persistence()
t6_month_rollover()

print("=" * 55)
passed = sum(results_log)
total = len(results_log)
print(f"  結果：{passed}/{total} 通過\n")
if passed < total:
    sys.exit(1)
