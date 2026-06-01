"""tests/test_shadow_ledger.py — G3a：shadow 顯式分支 + ledger 寫入的契約測試。

先寫測試再實作（TDD）。P104.3 / G3a（飛輪 v2：含 A 三分支矩陣鎖、B schema+容錯）。
測試慣例對齊 test_assertions.py：sys.path 注入、tmp_path 隔離、write_text 一律 utf-8。

涵蓋：
- A. check() 三分支行為矩陣（advisory/shadow/strict）契約鎖——未來改 check() 動到三分支就紅
- shadow 失敗分流到 shadow_findings（不混 failures、不 FAIL、exit 0）
- B. shadow_ledger append/read_records + schema version(v) + 壞行容錯 + silent no-op on error
- check(ledger_path=) 整合：shadow 判定寫入 ledger；預設 None 不寫（既有測試零污染）
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from gov.assertions import check
from gov import shadow_ledger


def _write_cfg(root: Path, gid: str, status: str, token: str) -> None:
    """造 tmp repo，含一個 status guard，assert 檢查 README 是否含 token。"""
    (root / "README.md").write_text("hello", encoding="utf-8")
    (root / "governance_config.yaml").write_text(
        f"guards:\n  - id: {gid}\n    status: {status}\n    asserts:\n"
        f"      - 'contains: README.md::{token}'\n",
        encoding="utf-8",
    )


# ── A. 三分支行為矩陣（契約鎖：advisory/shadow/strict 三行為定死）──
@pytest.mark.parametrize("status,checked,fails,shadow,st", [
    ("advisory", 0, 0, 0, "PASS"),   # skip：不評估、不計入 checked
    ("shadow",   1, 0, 1, "PASS"),   # 失敗→shadow_findings，不混 failures、不 FAIL、exit 0
    ("strict",   1, 1, 0, "FAIL"),   # 失敗→failures + FAIL
])
def test_status_branch_matrix(tmp_path: Path, status, checked, fails, shadow, st):
    _write_cfg(tmp_path, f"G-{status}", status, "NOPE_TOKEN_NOT_PRESENT")  # 必失敗
    rep = check(tmp_path)
    assert rep["checked"] == checked, f"{status}: checked 應={checked}"
    assert len(rep["failures"]) == fails, f"{status}: failures 應={fails}"
    assert len(rep.get("shadow_findings", [])) == shadow, f"{status}: shadow_findings 應={shadow}"
    assert rep["status"] == st, f"{status}: status 應={st}"


# ── shadow 命中時 shadow_findings 空（不誤報，呼應既有 test_assertions 真實 repo）──
def test_shadow_hit_no_findings(tmp_path: Path):
    _write_cfg(tmp_path, "G-SH", "shadow", "hello")  # README 含 hello → 命中
    rep = check(tmp_path)
    assert rep["shadow_findings"] == []
    assert rep["failures"] == []
    assert rep["status"] == "PASS"


# ── B. ledger append + read_records + schema version + ts ──
def test_ledger_append_and_read(tmp_path: Path):
    led = tmp_path / "shadow_ledger.jsonl"
    recs = [{"guard": "G1", "assert": "a::b", "ok": True},
            {"guard": "G2", "assert": "c::d", "ok": False}]
    shadow_ledger.append(recs, led)
    out = shadow_ledger.read_records(led)
    assert len(out) == 2
    assert out[0]["guard"] == "G1" and out[0]["ok"] is True
    assert out[1]["ok"] is False
    assert all("v" in r for r in out), "每筆須帶 schema version v"
    assert all("ts" in r for r in out), "每筆須帶 ts 時間戳"


# ── B. 壞行容錯：ledger 含壞 json 行，read_records skip 不崩 ──
def test_ledger_read_tolerates_bad_lines(tmp_path: Path):
    led = tmp_path / "shadow_ledger.jsonl"
    shadow_ledger.append([{"guard": "G1", "assert": "a", "ok": True}], led)
    with led.open("a", encoding="utf-8") as f:
        f.write("THIS IS NOT JSON\n")  # 壞行
    shadow_ledger.append([{"guard": "G2", "assert": "b", "ok": False}], led)
    out = shadow_ledger.read_records(led)
    assert len(out) == 2, "壞行應被 skip、好行全保留"


# ── B. silent no-op on error：父目錄不存在不拋；讀不存在的 ledger 回空 list ──
def test_ledger_silent_on_error(tmp_path: Path):
    bad = tmp_path / "nonexistent" / "x" / "led.jsonl"  # 父目錄不存在
    shadow_ledger.append([{"guard": "G", "assert": "a", "ok": True}], bad)  # 不應拋
    assert shadow_ledger.read_records(tmp_path / "nope.jsonl") == []


# ── check(ledger_path=) 整合：shadow 判定寫入 ledger ──
def test_check_writes_shadow_to_ledger(tmp_path: Path):
    _write_cfg(tmp_path, "G-SH", "shadow", "hello")  # 命中
    led = tmp_path / "shadow_ledger.jsonl"
    check(tmp_path, ledger_path=led)
    out = shadow_ledger.read_records(led)
    assert len(out) >= 1
    assert out[0]["guard"] == "G-SH"
    assert out[0]["ok"] is True  # hello 命中


# ── check() 預設不寫 ledger（既有測試零污染）──
def test_check_default_no_ledger(tmp_path: Path):
    _write_cfg(tmp_path, "G-SH", "shadow", "hello")
    rep = check(tmp_path)  # 不傳 ledger_path
    assert not (tmp_path / "shadow_ledger.jsonl").exists(), "預設不應產生 ledger 檔"
    assert "shadow_findings" in rep, "回傳仍須有 shadow_findings 欄位"
