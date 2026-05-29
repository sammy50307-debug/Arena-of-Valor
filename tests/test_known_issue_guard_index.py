from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import check_known_issue_guard_index as guard_index


def test_actual_index_covers_required_entries_without_advisories():
    findings = guard_index.check_index(PROJECT_ROOT / "docs" / "KNOWN_ISSUE_GUARD_INDEX.md")

    assert findings == []


def test_missing_required_entry_is_reported(tmp_path: Path):
    index = tmp_path / "index.md"
    index.write_text(
        """<!-- GUARD_INDEX_START -->
| Risk ID | Issue | Human Doc | Machine Guard | Focused Command | State | Gap | Next Action |
|---|---|---|---|---|---|---|---|
| R-016 | Production SLO | `docs/RISK_REGISTRY.md` R-016 | `scripts/slo_checker.py`; `scripts/system_doctor.py`; `scripts/cost_cache_governance.py` | `py scripts\\slo_checker.py --repo-root .` | Open Monitoring | observation-window | Review |
<!-- GUARD_INDEX_END -->
""",
        encoding="utf-8",
    )

    findings = guard_index.check_index(index)

    assert "missing_required_entry" in {finding.category for finding in findings}
    assert "R-017" in {finding.risk_id for finding in findings}


def test_human_only_rows_must_mark_the_gap(tmp_path: Path):
    index = tmp_path / "index.md"
    index.write_text(
        """<!-- GUARD_INDEX_START -->
| Risk ID | Issue | Human Doc | Machine Guard | Focused Command | State | Gap | Next Action |
|---|---|---|---|---|---|---|---|
| R-018 | RTK | `docs/PHASE_97_RTK_EVALUATION.md`; `docs/RISK_REGISTRY.md` | N/A | N/A | Open Install blocked | install-blocked | Pilot only |
<!-- GUARD_INDEX_END -->
""",
        encoding="utf-8",
    )

    findings = guard_index.check_index(index)

    assert "human_only_gap_unmarked" in {finding.category for finding in findings}
    assert "missing_gap_token" in {finding.category for finding in findings}


def test_cli_json_and_strict_mode_for_explicit_index(tmp_path: Path, capsys):
    index = tmp_path / "index.md"
    index.write_text(
        """<!-- GUARD_INDEX_START -->
| Risk ID | Issue | Human Doc | Machine Guard | Focused Command | State | Gap | Next Action |
|---|---|---|---|---|---|---|---|
| R-016 | Production SLO | `docs/RISK_REGISTRY.md` R-016 | `scripts/slo_checker.py`; `scripts/system_doctor.py`; `scripts/cost_cache_governance.py` | `py scripts\\slo_checker.py --repo-root .` | Open Monitoring | observation-window | Review |
<!-- GUARD_INDEX_END -->
""",
        encoding="utf-8",
    )

    rc = guard_index.main(["--index", str(index), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert payload
    assert guard_index.main(["--index", str(index), "--strict"]) == 1
    assert guard_index.main(["--index", str(PROJECT_ROOT / "docs" / "KNOWN_ISSUE_GUARD_INDEX.md"), "--strict"]) == 0
