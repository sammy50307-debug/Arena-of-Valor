from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_report_content_trust as trust


def _write_report(root: Path, html: str) -> Path:
    report = root / "data" / "reports" / "aov_report_2026-05-25.html"
    report.parent.mkdir(parents=True)
    report.write_text(html, encoding="utf-8")
    return report


def test_content_trust_checker_passes_clean_focus_report(tmp_path: Path):
    _write_report(
        tmp_path,
        """
        <h2 class="hero-focus-title">芽芽 觀察室</h2>
        <h3>📰 芽芽近期動態</h3>
        <div>芽芽輔助護盾討論</div><span>2026-05-25 10:00:00</span>
        <!-- Combat Stats Dashboard -->
        """,
    )

    results = trust.run_checks(tmp_path, "2026-05-25")

    assert not any(r.failed for r in results)
    assert {r.status for r in results} == {"PASS"}


def test_content_trust_checker_fails_tulen_in_focus_recent(tmp_path: Path):
    _write_report(
        tmp_path,
        """
        <h2 class="hero-focus-title">芽芽 觀察室</h2>
        <h3>📰 芽芽近期動態</h3>
        <div>圖倫完整教學</div><span>時間未知</span>
        <!-- Combat Stats Dashboard -->
        """,
    )

    results = trust.run_checks(tmp_path, "2026-05-25")
    by_name = {r.name: r for r in results}

    assert by_name["focus recent forbidden terms"].status == "FAIL"
    assert by_name["focus recent unknown dates"].status == "WARN"
