from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import check_root_legacy_hygiene as hygiene


def _categories(paths: list[str]) -> set[str]:
    return {finding.category for finding in hygiene.find_root_hygiene_advisories(paths)}


def test_flags_root_debug_outputs_and_loose_scripts():
    categories = _categories(["run_log.txt", "preview_report_script.py", "check_health.py"])

    assert "root_debug_output" in categories
    assert "root_loose_legacy_script" in categories
    assert "root_test_health_helper" in categories


def test_flags_static_assets_but_not_nested_files():
    categories = _categories(["yaya_bg.png", "data/reports/yaya_bg.png", "docs/PHASE_100_PLAN.md"])

    assert "root_static_asset_decision" in categories
    assert len(categories) == 1


def test_normal_root_and_project_paths_are_quiet():
    findings = hygiene.find_root_hygiene_advisories(
        [
            "main.py",
            "config.py",
            "index.html",
            "README.md",
            "scripts/check_generated_artifact_hygiene.py",
            "tests/test_generated_artifact_hygiene.py",
        ]
    )

    assert findings == []


def test_cli_json_output_for_explicit_paths(capsys):
    rc = hygiene.main(["--paths", "run_log.txt", "docs/PHASE_100_PLAN.md", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert len(payload) == 1
    assert payload[0]["category"] == "root_debug_output"


def test_strict_mode_only_fails_when_findings_exist():
    assert hygiene.main(["--paths", "run_log.txt"]) == 0
    assert hygiene.main(["--paths", "run_log.txt", "--strict"]) == 1
    assert hygiene.main(["--paths", "main.py", "--strict"]) == 0
