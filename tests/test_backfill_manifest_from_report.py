from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import backfill_manifest_from_report


def test_backfill_manifest_from_existing_showcase_report(tmp_path: Path):
    reports = tmp_path / "data" / "reports"
    reports.mkdir(parents=True)
    report = reports / "aov_report_2026-05-19.html"
    report.write_text(
        "<!-- cache_hit: 2/5 (40%) | llm_calls: 3 | mode: showcase_forced -->\n<html></html>\n",
        encoding="utf-8",
    )

    manifest_path = backfill_manifest_from_report.backfill_manifest(tmp_path, "2026-05-19")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["run_date"] == "2026-05-19"
    assert payload["mode"] == "showcase_forced"
    assert payload["is_backfill"] is True
    assert payload["replay_source"] == "report_metadata"
    assert payload["paths"]["raw"] == ""
    assert payload["paths"]["analysis"] == ""
    assert payload["metrics"]["cache_hit"] == 2
    assert payload["metrics"]["total_calls"] == 5
    assert payload["metrics"]["llm_calls"] == 3
    assert payload["publish_eligible"] is False
    assert "manifest backfilled from canonical report only" in payload["eligibility"]["reasons"]


def test_backfill_manifest_fails_when_report_missing(tmp_path: Path):
    try:
        backfill_manifest_from_report.backfill_manifest(tmp_path, "2026-05-19")
    except FileNotFoundError as exc:
        assert "missing canonical report" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")
