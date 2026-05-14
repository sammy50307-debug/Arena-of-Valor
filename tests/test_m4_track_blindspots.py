"""Tests for scripts/m4_track_blindspots.py (P72.3 — M4 自動化)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

m4 = importlib.import_module("m4_track_blindspots")


# ---------------------------------------------------------------------------
# Phase id extraction
# ---------------------------------------------------------------------------

class TestExtractPhaseId:
    def test_phase_dash(self):
        assert m4.extract_phase_id("2026-05-14-phase-71-blindspots.md") == "71"

    def test_phase_dashdot(self):
        assert m4.extract_phase_id("2026-05-08-p70.3-line-scroll-postmortem.md") == "70.3"

    def test_pprefix(self):
        assert m4.extract_phase_id("2026-05-08-p69-showcase-forced-rootcause.md") == "69"

    def test_phase_no_dash(self):
        assert m4.extract_phase_id("phase71-something.md") == "71"

    def test_no_match(self):
        assert m4.extract_phase_id("random-postmortem.md") is None

    def test_compound_subphase(self):
        assert m4.extract_phase_id("2026-05-03-phase-63-4-showcase-rootcause.md") == "63"


# ---------------------------------------------------------------------------
# Blindspot file detection
# ---------------------------------------------------------------------------

class TestIsBlindspotFile:
    def test_filename_contains_blindspot(self, tmp_path: Path):
        p = tmp_path / "phase-71-blindspots.md"
        p.write_text("# header", encoding="utf-8")
        assert m4.is_blindspot_file(p) is True

    def test_header_marks_blindspot(self, tmp_path: Path):
        p = tmp_path / "phase-99-postmortem.md"
        p.write_text("# P99 Blindspots — M4\n\nbody", encoding="utf-8")
        assert m4.is_blindspot_file(p) is True

    def test_regular_postmortem(self, tmp_path: Path):
        p = tmp_path / "phase-64-success.md"
        p.write_text("# P64 success postmortem\n\ncore lesson body", encoding="utf-8")
        assert m4.is_blindspot_file(p) is False


# ---------------------------------------------------------------------------
# B-NNN rule extraction
# ---------------------------------------------------------------------------

_BLINDSPOT_SAMPLE = """# P99 Blindspots

## 計畫書沒寫、實際撞到的問題

### B-001：第一個盲點

**計畫書原寫**：略。

**實際撞到**：略。

**通則化**：
> 第一條通則化規則的內容。

**已加入**：略

---

### B-002：第二個盲點

**實際撞到**：略。

**通則化**：
> 第二條規則。

---

### B-003：第三個盲點（無通則化）

**實際撞到**：略。
"""


class TestExtractBlindspotRules:
    def test_extract_three(self):
        rules = m4.extract_blindspot_rules(_BLINDSPOT_SAMPLE)
        assert len(rules) == 3
        assert [r["id"] for r in rules] == ["B-001", "B-002", "B-003"]

    def test_rule_text(self):
        rules = m4.extract_blindspot_rules(_BLINDSPOT_SAMPLE)
        assert rules[0]["rule"] == "第一條通則化規則的內容。"
        assert rules[1]["rule"] == "第二條規則。"

    def test_missing_rule_is_empty(self):
        rules = m4.extract_blindspot_rules(_BLINDSPOT_SAMPLE)
        assert rules[2]["rule"] == ""

    def test_headline_captured(self):
        rules = m4.extract_blindspot_rules(_BLINDSPOT_SAMPLE)
        assert "第一個盲點" in rules[0]["headline"]


# ---------------------------------------------------------------------------
# Anchor picking heuristic
# ---------------------------------------------------------------------------

class TestPickAnchor:
    def test_picks_longest_cjk_run(self):
        # 中文字串會被 ASCII（空格/英文/標點）切段；取最長段
        text = "前段 中段較長 機械化驗證項目"
        anchor = m4._pick_anchor(text)
        assert anchor == "機械化驗證項目"

    def test_empty_when_no_cjk(self):
        assert m4._pick_anchor("just ASCII text 123") == ""

    def test_respects_min_len(self):
        # 短於 min_len=4 的中文片段不採用
        assert m4._pick_anchor("a 中b 文c 字", min_len=4) == ""


# ---------------------------------------------------------------------------
# Scan postmortems (integration with tmp_path)
# ---------------------------------------------------------------------------

class TestScanPostmortems:
    def test_pair_detection(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        pm_dir = tmp_path / "postmortems"
        pm_dir.mkdir()
        (pm_dir / "2026-05-01-phase-64-success.md").write_text("# P64 success", encoding="utf-8")
        (pm_dir / "2026-05-14-phase-71-blindspots.md").write_text("# blindspots", encoding="utf-8")
        (pm_dir / "2026-05-14-phase-71-skill-deployment-decay.md").write_text(
            "# P71 postmortem regular", encoding="utf-8"
        )

        monkeypatch.setattr(m4, "POSTMORTEM_DIR", pm_dir)
        grouped = m4.scan_postmortems()

        assert "64" in grouped
        assert "71" in grouped
        assert len(grouped["64"]["postmortems"]) == 1
        assert len(grouped["64"]["blindspots"]) == 0
        assert len(grouped["71"]["blindspots"]) == 1

    def test_empty_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        empty = tmp_path / "empty"
        empty.mkdir()
        monkeypatch.setattr(m4, "POSTMORTEM_DIR", empty)
        assert m4.scan_postmortems() == {}


# ---------------------------------------------------------------------------
# Scaffold command (E2E via cmd_scaffold)
# ---------------------------------------------------------------------------

class TestScaffold:
    def test_creates_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        pm_dir = tmp_path / "postmortems"
        pm_dir.mkdir()
        monkeypatch.setattr(m4, "POSTMORTEM_DIR", pm_dir)
        monkeypatch.setattr(m4, "PROJECT_ROOT", tmp_path)

        rc = m4.cmd_scaffold("p99")
        assert rc == 0

        created = list(pm_dir.glob("*phase-99-blindspots.md"))
        assert len(created) == 1
        body = created[0].read_text(encoding="utf-8")
        assert "P99 Blindspots" in body
        assert "B-XXX" in body  # placeholder markers present

    def test_rejects_bad_phase(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        pm_dir = tmp_path / "postmortems"
        pm_dir.mkdir()
        monkeypatch.setattr(m4, "POSTMORTEM_DIR", pm_dir)

        rc = m4.cmd_scaffold("not-a-phase")
        assert rc == 1
        assert list(pm_dir.glob("*.md")) == []

    def test_no_overwrite(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        pm_dir = tmp_path / "postmortems"
        pm_dir.mkdir()
        monkeypatch.setattr(m4, "POSTMORTEM_DIR", pm_dir)
        monkeypatch.setattr(m4, "PROJECT_ROOT", tmp_path)

        assert m4.cmd_scaffold("p99") == 0
        assert m4.cmd_scaffold("p99") == 1  # second call refuses overwrite
