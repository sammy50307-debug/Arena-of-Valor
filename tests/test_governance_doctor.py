from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import governance_doctor


GOOD_RISK_REGISTRY = """# 跨 Phase 風險登記簿（STR6）

## 開放風險（Open）

### R-001：Open risk

- **來源**：P84.4
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：open risk
- **緩解策略**：watch it

## 已關閉風險（Closed）

### R-002：Closed risk

- **來源**：P84.4
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-18）
- **描述**：closed risk
- **緩解策略**：fixed
"""


def _write_repo(
    tmp_path: Path,
    source_text: str = 'ISSUE_CATALOG = {"x": {"code": "DOC001"}, "y": {"code": "GOV001"}}',
    runbook_text: str = '<a id="doc001"></a>DOC001\n<a id="gov001"></a>GOV001\n<a id="gov000"></a>GOV000\n',
    risk_text: str = GOOD_RISK_REGISTRY,
) -> None:
    scripts = tmp_path / "scripts"
    docs = tmp_path / "docs"
    scripts.mkdir()
    docs.mkdir()
    (scripts / "example.py").write_text(source_text, encoding="utf-8")
    (docs / "OPERATIONS_RUNBOOK.md").write_text(runbook_text, encoding="utf-8")
    (docs / "RISK_REGISTRY.md").write_text(risk_text, encoding="utf-8")


def _codes(result):
    return {issue.code for issue in result.issues}


def test_governance_passes_when_issue_codes_have_anchors_and_risks_match(tmp_path: Path):
    _write_repo(tmp_path)

    result = governance_doctor.check_governance(tmp_path, issue_source_paths=["scripts/example.py"])

    assert result.issues == []
    assert "DOC001" in result.issue_codes
    assert "doc001" in result.runbook_anchors
    assert governance_doctor.exit_code_for(result) == 0


def test_governance_blocks_missing_runbook_anchor(tmp_path: Path):
    _write_repo(tmp_path, runbook_text='<a id="doc001"></a>DOC001\n')

    result = governance_doctor.check_governance(tmp_path, issue_source_paths=["scripts/example.py"])

    assert "GOV001" in _codes(result)
    assert governance_doctor.exit_code_for(result) == 1


def test_governance_blocks_duplicate_runbook_anchor(tmp_path: Path):
    _write_repo(
        tmp_path,
        runbook_text='<a id="doc001"></a>DOC001\n<a id="doc001"></a>DOC001 duplicate\n<a id="gov001"></a>GOV001\n',
    )

    result = governance_doctor.check_governance(tmp_path, issue_source_paths=["scripts/example.py"])

    assert "GOV002" in _codes(result)


def test_governance_blocks_risk_status_section_mismatch(tmp_path: Path):
    risk_text = GOOD_RISK_REGISTRY.replace("- **狀態**：Open", "- **狀態**：✅ 已修補（2026-05-18）", 1)
    _write_repo(tmp_path, risk_text=risk_text)

    result = governance_doctor.check_governance(tmp_path, issue_source_paths=["scripts/example.py"])

    assert "GOV003" in _codes(result)


def test_governance_blocks_duplicate_risk_id(tmp_path: Path):
    risk_text = GOOD_RISK_REGISTRY.replace("### R-002：Closed risk", "### R-001：Duplicate risk")
    _write_repo(tmp_path, risk_text=risk_text)

    result = governance_doctor.check_governance(tmp_path, issue_source_paths=["scripts/example.py"])

    assert "GOV004" in _codes(result)


def test_governance_cli_json(tmp_path: Path, capsys):
    _write_repo(tmp_path)

    rc = governance_doctor.main(["--repo-root", str(tmp_path), "--issue-source", "scripts/example.py", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 0
    assert payload["issues"] == []
    assert "DOC001" in payload["issue_codes"]
