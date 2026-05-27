from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import check_generated_artifact_hygiene as hygiene


def _categories(paths: list[str]) -> set[str]:
    return {finding.category for finding in hygiene.find_hygiene_advisories(paths)}


def test_flags_scratch_preview_report_and_root_debug_output():
    categories = _categories(
        [
            "scratch/rtk_eval/log.txt",
            "data/reports/PREVIEW_yaya.html",
            "run_log.txt",
        ]
    )

    assert "scratch_local_artifact" in categories
    assert "preview_report" in categories
    assert "root_debug_output" in categories


def test_flags_report_variants_and_deploy_decision_paths():
    categories = _categories(
        [
            r"data\reports\aov_report_2026-05-06_v3.html",
            "ui_previews/p65/index.html",
            "backups/index_before_p63_3.html",
            ".github/workflows/daily_report.yml",
            ".gitignore",
        ]
    )

    assert "report_variant" in categories
    assert "ui_preview" in categories
    assert "backup_artifact" in categories
    assert "decision_required" in categories


def test_normal_docs_and_code_paths_are_quiet():
    findings = hygiene.find_hygiene_advisories(
        [
            "docs/PHASE_99_PLAN.md",
            "analyzer/source_selection.py",
            "tests/test_source_selection.py",
            "data/reports/aov_report_2026-05-27.html",
        ]
    )

    assert findings == []


def test_cli_json_output_for_explicit_paths(capsys):
    rc = hygiene.main(["--paths", "scratch/demo.txt", "docs/PHASE_99_PLAN.md", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert len(payload) == 1
    assert payload[0]["category"] == "scratch_local_artifact"


def test_strict_mode_only_fails_when_findings_exist():
    assert hygiene.main(["--paths", "scratch/demo.txt"]) == 0
    assert hygiene.main(["--paths", "scratch/demo.txt", "--strict"]) == 1
    assert hygiene.main(["--paths", "docs/PHASE_99_PLAN.md", "--strict"]) == 0
