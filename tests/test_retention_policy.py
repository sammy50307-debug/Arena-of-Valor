from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import retention_policy


TODAY = "2026-05-17"


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _set_mtime(path: Path, date_str: str) -> None:
    ts = datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    path.touch()
    import os

    os.utime(path, (ts, ts))


def _summary_map(inventory):
    return {item["policy"]: item for item in inventory["summaries"]}


def test_inventory_is_dry_run_and_never_deletes(tmp_path: Path):
    _write(tmp_path / "data" / "reports" / "aov_report_2026-05-16.html")
    _write(tmp_path / "data" / "reports" / "aov_report_2026-03-01_v2.html")
    _write(tmp_path / "data" / "reports" / "aov_report_2025-01-01.html")
    _write(tmp_path / "data" / "runs" / "2025-01-01" / "run_manifest.json", "{}")
    _write(tmp_path / "data" / "debug_bundles" / "2026-03-01" / "debug_bundle_x.json", "{}")

    qfile = tmp_path / "data" / "quarantine" / "invalid_json" / "analysis.json"
    _write(qfile, "{}")
    _set_mtime(qfile, "2026-01-01")

    inventory = retention_policy.collect_inventory(tmp_path, today=TODAY, max_candidates=50)

    assert inventory["mode"] == "dry-run"
    assert inventory["dry_run"] is True
    assert inventory["will_delete"] is False
    paths = {item["path"] for item in inventory["candidates"]}
    assert "data/reports/aov_report_2026-03-01_v2.html" in paths
    assert "data/reports/aov_report_2025-01-01.html" in paths
    assert "data/runs/2025-01-01" in paths
    assert "data/debug_bundles/2026-03-01" in paths
    assert "data/quarantine/invalid_json/analysis.json" in paths
    assert "data/reports/aov_report_2026-05-16.html" not in paths


def test_missing_directories_are_reported_without_candidates(tmp_path: Path):
    inventory = retention_policy.collect_inventory(tmp_path, today=TODAY)
    summaries = _summary_map(inventory)

    assert summaries["reports"]["status"] == "missing"
    assert summaries["run_manifests"]["status"] == "missing"
    assert summaries["debug_bundles"]["status"] == "missing"
    assert inventory["candidate_count"] == 0


def test_llm_cache_is_reported_but_not_deletion_candidate(tmp_path: Path):
    cache_file = tmp_path / "data" / "llm_cache.json"
    _write(cache_file, json.dumps({"entries": {"k": "v"}}, ensure_ascii=False))
    _set_mtime(cache_file, "2025-01-01")

    inventory = retention_policy.collect_inventory(tmp_path, today=TODAY)
    summaries = _summary_map(inventory)

    assert summaries["llm_cache"]["status"] == "ok"
    assert summaries["llm_cache"]["candidate_count"] == 0
    assert "data/llm_cache.json" not in {item["path"] for item in inventory["candidates"]}


def test_cli_json_output_contains_dry_run_flags(tmp_path: Path, capsys):
    rc = retention_policy.main(["--repo-root", str(tmp_path), "--today", TODAY, "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert payload["dry_run"] is True
    assert payload["will_delete"] is False
