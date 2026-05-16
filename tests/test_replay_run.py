from __future__ import annotations

import json
from pathlib import Path

import scripts.replay_run as replay


def test_replay_run_fails_when_analysis_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(replay.config, "DATA_DIR", tmp_path / "data")
    rc = replay.main(["--date", "2026-05-16"])
    assert rc == 1


def test_replay_run_generates_report_and_manifest(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    analysis_path = data_dir / "analysis_20260516.json"
    analysis_path.write_text(
        json.dumps(
            {
                "date": "2026-05-16",
                "overview": "ok",
                "overall": {"sentiment_score": 0.5, "trend": "Stable"},
                "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
                "_meta": {"mode": "production"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(replay.config, "DATA_DIR", data_dir)
    monkeypatch.setattr(replay.config, "REPORTS_DIR", data_dir / "reports")

    def _fake_generate(self, daily_summary, analyzed_posts, output_dir=None):
        out_dir = output_dir or (data_dir / "reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        report = out_dir / "aov_report_2026-05-16.html"
        report.write_text("<!-- mode: production -->\n<html></html>\n", encoding="utf-8")
        return report

    monkeypatch.setattr(replay.ReportGenerator, "generate", _fake_generate)

    rc = replay.main(["--date", "2026-05-16"])
    assert rc == 0

    report = data_dir / "reports" / "aov_report_2026-05-16.html"
    manifest = data_dir / "runs" / "2026-05-16" / "run_manifest.json"
    assert report.exists()
    assert manifest.exists()
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["run_date"] == "2026-05-16"
    assert manifest_data["replay_source"] == "analysis_json"
    assert manifest_data["is_backfill"] is True


def test_replay_run_quarantines_invalid_json(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    bad_analysis = data_dir / "analysis_20260516.json"
    bad_analysis.write_text("{bad json", encoding="utf-8")

    monkeypatch.setattr(replay.config, "DATA_DIR", data_dir)
    rc = replay.main(["--date", "2026-05-16"])
    assert rc == 1
    assert not bad_analysis.exists()

    qdir = data_dir / "quarantine" / "invalid_json"
    qfiles = list(qdir.glob("analysis_20260516__*.json"))
    assert qfiles
    meta_files = list(qdir.glob("analysis_20260516__*.meta.json"))
    assert meta_files


def test_replay_run_quarantines_schema_violation(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    analysis_path = data_dir / "analysis_20260516.json"
    analysis_path.write_text(json.dumps({"date": "2026-05-16", "overall": {}}, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(replay.config, "DATA_DIR", data_dir)
    rc = replay.main(["--date", "2026-05-16"])
    assert rc == 1
    assert not analysis_path.exists()

    qdir = data_dir / "quarantine" / "analysis_schema_violation"
    qfiles = list(qdir.glob("analysis_20260516__*.json"))
    assert qfiles


def test_replay_run_emits_debug_bundle_when_requested(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    analysis_path = data_dir / "analysis_20260516.json"
    analysis_path.write_text(
        json.dumps(
            {
                "date": "2026-05-16",
                "overview": "ok",
                "overall": {"sentiment_score": 0.5, "trend": "Stable"},
                "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
                "_meta": {"mode": "production"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(replay.config, "DATA_DIR", data_dir)
    monkeypatch.setattr(replay.config, "REPORTS_DIR", data_dir / "reports")

    def _fake_generate(self, daily_summary, analyzed_posts, output_dir=None):
        out_dir = output_dir or (data_dir / "reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        report = out_dir / "aov_report_2026-05-16.html"
        report.write_text("<!-- mode: production -->\n<html></html>\n", encoding="utf-8")
        return report

    monkeypatch.setattr(replay.ReportGenerator, "generate", _fake_generate)

    rc = replay.main(["--date", "2026-05-16", "--debug-bundle"])
    assert rc == 0

    bundles = list((data_dir / "debug_bundles" / "2026-05-16").glob("debug_bundle_*.json"))
    assert bundles
    payload = json.loads(bundles[0].read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["manifest"]["is_backfill"] is True
