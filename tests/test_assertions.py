from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gov.assertions import check
from gov.utils import find_repo_root, load_config


# ── 防空轉契約：guards 非空（防 G1 悄悄退回 []）──
def test_governance_config_guards_not_empty():
    cfg = load_config(find_repo_root())
    guards = cfg.get("guards") or []
    assert isinstance(guards, list)
    assert len(guards) >= 1, "governance_config.yaml 的 guards 不可為空（G1 防空轉契約）"


# ── 引擎有實際覆蓋：advisory 會被 skip 不計入 checked，故 G1 用 shadow 才有覆蓋 ──
def test_engine_actually_evaluates_asserts():
    rep = check(find_repo_root())
    assert rep["checked"] >= 1, (
        "checked=0 代表引擎空轉；advisory guard 不計入 checked，G1 須用 shadow"
    )


# ── shadow 不誤擋正常 repo：不得 FAIL，且所有標的命中（0 失敗，證明標的正確）──
def test_shadow_does_not_block_real_repo():
    rep = check(find_repo_root())
    assert rep["status"] != "FAIL", f"正常 repo 不應被擋下，failures={rep['failures']}"
    assert rep["failures"] == [], f"G1 guard 標的應全部命中真實檔案，failures={rep['failures']}"
    # G3a：shadow 標的也應全部命中（失敗會分流到 shadow_findings 而非 failures）
    assert rep["shadow_findings"] == [], f"shadow 標的應全部命中，shadow_findings={rep['shadow_findings']}"


# ── 負面對照：advisory guard 即使斷言不成立也絕不進 failures、不計入 checked ──
def test_advisory_guard_skipped_even_when_assert_broken(tmp_path: Path):
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    (tmp_path / "governance_config.yaml").write_text(
        "guards:\n"
        "  - id: G-ADV\n"
        "    status: advisory\n"
        "    asserts:\n"
        "      - 'contains: README.md::THIS_TOKEN_DOES_NOT_EXIST'\n",
        encoding="utf-8",
    )
    rep = check(tmp_path)
    assert rep["status"] == "PASS"
    assert rep["failures"] == []
    assert rep["checked"] == 0  # advisory 整個被 skip（assertions.py:86 continue）


# ── 正向對照：shadow guard 斷言成立時 checked 累加且不 FAIL ──
def test_shadow_guard_evaluated_and_passes_when_satisfied(tmp_path: Path):
    (tmp_path / "README.md").write_text("hello GUARD_TOKEN_XYZ", encoding="utf-8")
    (tmp_path / "governance_config.yaml").write_text(
        "guards:\n"
        "  - id: G-SHADOW\n"
        "    status: shadow\n"
        "    asserts:\n"
        "      - 'contains: README.md::GUARD_TOKEN_XYZ'\n",
        encoding="utf-8",
    )
    rep = check(tmp_path)
    assert rep["checked"] == 1
    assert rep["status"] == "PASS"
    assert rep["failures"] == []
