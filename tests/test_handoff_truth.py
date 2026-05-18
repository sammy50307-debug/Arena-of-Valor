from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import check_handoff_truth


def _handoff(step: str = "P84.3 Handoff truth checker", anti_step: str | None = None, mode: str = "APPROVED") -> str:
    anti_step = anti_step or step
    return """<!-- ACTIVE_BOOTSTRAP_START -->
# ACTIVE_BOOTSTRAP — READ THIS FIRST

| 欄位 | 內容 |
|---|---|
| **Status** | ACTIVE |
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P84（Long-Term Governance） |
| **Current Step** | %s |
| **Mode** | %s |
| **Latest Verified Commit** | `HEAD feat: test` |
| **Updated At** | 2026-05-18 Asia/Taipei |

## Six Anti-Drift Fields

| 欄位 | 內容 |
|---|---|
| **Current Phase** | P84（%s） |
| **Current Step** | %s |
| **Allowed Files** | `NEXT_SESSION_HANDOFF.md` |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md` |
| **Exit Criteria** | checker passes |
| **Resume Rule** | read active bootstrap only |

<!-- ACTIVE_BOOTSTRAP_END -->

<!-- ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION -->

# old notes
""" % (step, mode, mode, anti_step)


def _active_operation(step: str = "P84.3 Handoff truth checker", mode: str = "APPROVED") -> str:
    return """# ACTIVE OPERATION

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | P77-P84 Daily Monitoring Reliability Program |
| **Current Phase** | P84（Long-Term Governance） |
| **Current Step** | %s |
| **Mode** | %s |
| **Latest Verified Commit** | `HEAD feat: test` |

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P84（%s） |
| **Current Step** | %s |
| **Allowed Files** | `NEXT_SESSION_HANDOFF.md` |
| **Forbidden Work** | none |
| **Exit Criteria** | checker passes |
| **Resume Rule** | read active bootstrap only |
""" % (step, mode, mode, step)


def _write_pair(tmp_path: Path, handoff_text: str, active_text: str | None = None) -> tuple[Path, Path]:
    handoff = tmp_path / "NEXT_SESSION_HANDOFF.md"
    active = tmp_path / "docs" / "ACTIVE_OPERATION.md"
    active.parent.mkdir(parents=True, exist_ok=True)
    handoff.write_text(handoff_text, encoding="utf-8")
    active.write_text(active_text or _active_operation(), encoding="utf-8")
    return handoff, active


def _codes(result):
    return {issue.code for issue in result.issues}


def test_handoff_truth_passes_valid_active_bootstrap(tmp_path: Path):
    handoff, active = _write_pair(tmp_path, _handoff())

    result = check_handoff_truth.check_handoff_truth(handoff, active)

    assert result.issues == []
    assert check_handoff_truth.exit_code_for(result) == 0


def test_handoff_truth_blocks_missing_markers(tmp_path: Path):
    handoff, active = _write_pair(tmp_path, "# no markers\n")

    result = check_handoff_truth.check_handoff_truth(handoff, active)

    assert "HND001" in _codes(result)
    assert check_handoff_truth.exit_code_for(result) == 1


def test_handoff_truth_blocks_missing_anti_drift_field(tmp_path: Path):
    text = _handoff().replace("| **Resume Rule** | read active bootstrap only |\n", "")
    handoff, active = _write_pair(tmp_path, text)

    result = check_handoff_truth.check_handoff_truth(handoff, active)

    assert "HND004" in _codes(result)


def test_handoff_truth_detects_step_mismatch_inside_bootstrap(tmp_path: Path):
    handoff, active = _write_pair(tmp_path, _handoff(anti_step="P84.4 Risk registry"))

    result = check_handoff_truth.check_handoff_truth(handoff, active)

    assert "HND005" in _codes(result)


def test_handoff_truth_detects_active_operation_mismatch(tmp_path: Path):
    handoff, active = _write_pair(tmp_path, _handoff(), _active_operation(step="P84.4 Risk registry"))

    result = check_handoff_truth.check_handoff_truth(handoff, active)

    assert "HND007" in _codes(result)


def test_handoff_truth_cli_json(tmp_path: Path, capsys):
    _write_pair(tmp_path, _handoff())

    rc = check_handoff_truth.main(["--repo-root", str(tmp_path), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert payload["issues"] == []
    assert payload["bootstrap_fields"]["Mode"] == "APPROVED"
