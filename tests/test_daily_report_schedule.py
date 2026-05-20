from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "daily_report.yml"


def test_p86_daily_report_cron_runs_after_pacific_rpd_reset_window():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "cron: '30 8 * * *'" in workflow_text
    assert "UTC 08:30" in workflow_text
    assert "台北時間 16:30" in workflow_text
    assert "Pacific midnight RPD reset" in workflow_text


def test_p86_daily_report_keeps_manual_dispatch():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow_text
