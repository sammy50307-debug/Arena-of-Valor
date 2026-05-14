"""Tests for scripts/skill_metrics_logger.py (P72.0)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import skill_metrics_logger as sml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect METRICS_FILE to a temp location for each test."""
    f = tmp_path / "skill_metrics.jsonl"
    monkeypatch.setattr(sml, "METRICS_FILE", f)
    return f


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------

class TestRecord:
    def test_creates_file_on_first_call(self, tmp_metrics: Path):
        assert not tmp_metrics.exists()
        sml.record("test-skill", 123.4, 0)
        assert tmp_metrics.exists()

    def test_appends_valid_json(self, tmp_metrics: Path):
        sml.record("test-skill", 123.0, 0)
        lines = tmp_metrics.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["skill"] == "test-skill"
        assert entry["duration_ms"] == 123
        assert entry["exit_code"] == 0

    def test_multiple_calls_append(self, tmp_metrics: Path):
        sml.record("s1", 100.0, 0)
        sml.record("s2", 200.0, 1)
        lines = tmp_metrics.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_tokens_stored(self, tmp_metrics: Path):
        sml.record("s1", 50.0, 0, tokens_in=100, tokens_out=200)
        entry = json.loads(tmp_metrics.read_text(encoding="utf-8").strip())
        assert entry["tokens_in"] == 100
        assert entry["tokens_out"] == 200

    def test_tokens_default_zero(self, tmp_metrics: Path):
        sml.record("s1", 50.0, 0)
        entry = json.loads(tmp_metrics.read_text(encoding="utf-8").strip())
        assert entry["tokens_in"] == 0
        assert entry["tokens_out"] == 0

    def test_duration_rounded(self, tmp_metrics: Path):
        sml.record("s1", 99.7, 0)
        entry = json.loads(tmp_metrics.read_text(encoding="utf-8").strip())
        assert entry["duration_ms"] == 100

    def test_silently_noops_on_bad_path(self, monkeypatch: pytest.MonkeyPatch):
        # Point METRICS_FILE to a non-writable path
        monkeypatch.setattr(sml, "METRICS_FILE", Path("/no/such/dir/metrics.jsonl"))
        # Should not raise
        sml.record("s1", 10.0, 0)

    def test_ts_format(self, tmp_metrics: Path):
        sml.record("s1", 10.0, 0)
        entry = json.loads(tmp_metrics.read_text(encoding="utf-8").strip())
        ts = entry["ts"]
        # Expect ISO8601-ish: 2026-05-14T10:00:00Z
        assert ts.endswith("Z")
        assert "T" in ts


# ---------------------------------------------------------------------------
# load_all()
# ---------------------------------------------------------------------------

class TestLoadAll:
    def test_empty_when_no_file(self, tmp_metrics: Path):
        assert sml.load_all(tmp_metrics) == []

    def test_returns_all_records(self, tmp_metrics: Path):
        sml.record("a", 100.0, 0)
        sml.record("b", 200.0, 1)
        records = sml.load_all(tmp_metrics)
        assert len(records) == 2

    def test_skips_malformed_lines(self, tmp_metrics: Path):
        tmp_metrics.write_text('{"skill":"a","ts":"x","duration_ms":1,"exit_code":0,"tokens_in":0,"tokens_out":0}\nNOT_JSON\n', encoding="utf-8")
        records = sml.load_all(tmp_metrics)
        assert len(records) == 1


# ---------------------------------------------------------------------------
# summarize()
# ---------------------------------------------------------------------------

class TestSummarize:
    def test_empty_input(self):
        assert sml.summarize([]) == {}

    def test_single_skill_success(self):
        records = [
            {"skill": "a", "duration_ms": 100, "exit_code": 0, "tokens_in": 0, "tokens_out": 0},
            {"skill": "a", "duration_ms": 200, "exit_code": 0, "tokens_in": 0, "tokens_out": 0},
        ]
        stats = sml.summarize(records)
        assert stats["a"]["calls"] == 2
        assert stats["a"]["failures"] == 0
        assert stats["a"]["failure_rate_pct"] == 0.0
        assert stats["a"]["avg_duration_ms"] == 150

    def test_failure_rate(self):
        records = [
            {"skill": "b", "duration_ms": 100, "exit_code": 0, "tokens_in": 0, "tokens_out": 0},
            {"skill": "b", "duration_ms": 100, "exit_code": 1, "tokens_in": 0, "tokens_out": 0},
        ]
        stats = sml.summarize(records)
        assert stats["b"]["failures"] == 1
        assert stats["b"]["failure_rate_pct"] == 50.0

    def test_multiple_skills(self):
        records = [
            {"skill": "x", "duration_ms": 50, "exit_code": 0, "tokens_in": 0, "tokens_out": 0},
            {"skill": "y", "duration_ms": 200, "exit_code": 0, "tokens_in": 0, "tokens_out": 0},
        ]
        stats = sml.summarize(records)
        assert "x" in stats
        assert "y" in stats

    def test_token_aggregation(self):
        records = [
            {"skill": "c", "duration_ms": 100, "exit_code": 0, "tokens_in": 100, "tokens_out": 50},
            {"skill": "c", "duration_ms": 100, "exit_code": 0, "tokens_in": 200, "tokens_out": 100},
        ]
        stats = sml.summarize(records)
        assert stats["c"]["total_tokens_in"] == 300
        assert stats["c"]["avg_tokens_out"] == 75
