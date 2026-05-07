"""P63.1.2 hotfix 測試：_update_landing_page 與 canonical sync 同檔守衛。

根因背景：generator.py 的 canonical sync 在 GHA 第一次跑時 output_path == canonical_path
（aov_report_YYYY-MM-DD.html 不存在 → 不走 _v2 命名）→ shutil.copy2 拋 SameFileError →
原本與 _update_landing_page 共用同一個 try → landing page 從未更新（連 3 天 GHA 都沒帶 index.html）。

修補：拆 try + same-file 守衛。本檔測 _update_landing_page 在獨立呼叫下行為正確。
"""

from pathlib import Path

import pytest

from reporter.generator import ReportGenerator


def _make_report(reports_dir: Path, date_str: str) -> Path:
    p = reports_dir / f"aov_report_{date_str}.html"
    p.write_text(f"<html>fake report {date_str}</html>", encoding="utf-8")
    return p


def _make_minimal_index(index_path: Path) -> None:
    """寫一份結構符合 _update_landing_page regex 的最小 index.html"""
    index_path.write_text(
        """<html><body>
<a href="data/reports/aov_report_2026-01-01.html" class="main-btn">進入最新戰報 (2026-01-01)</a>
<a href="data/reports/x.html" class="history-item"><i></i>1/2 戰報</a>
<a href="data/reports/x.html" class="history-item"><i></i>1/3 戰報</a>
<a href="data/reports/x.html" class="history-item"><i></i>1/4 戰報</a>
<a href="data/reports/x.html" class="history-item"><i></i>1/5 戰報</a>
<a href="data/reports/x.html" class="history-item"><i></i>1/6 戰報</a>
</body></html>""",
        encoding="utf-8",
    )


def test_update_landing_page_picks_latest_and_top5_history(tmp_path, monkeypatch):
    """主路徑：給 6 份報告，main-btn 指向最新、history 5 筆指向次新到第 6 新。"""
    repo_root = tmp_path
    reports_dir = repo_root / "data" / "reports"
    reports_dir.mkdir(parents=True)

    dates = ["2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06"]
    for d in dates:
        _make_report(reports_dir, d)

    index_path = repo_root / "index.html"
    _make_minimal_index(index_path)

    # ReportGenerator._update_landing_page 用 Path(__file__).resolve().parent.parent 找 repo root
    # 我們改 monkeypatch reporter.generator 模組的 __file__ 指向 tmp 內的偽 reporter/
    fake_reporter_dir = repo_root / "reporter"
    fake_reporter_dir.mkdir()
    fake_module_file = fake_reporter_dir / "generator.py"
    fake_module_file.write_text("# placeholder", encoding="utf-8")
    monkeypatch.setattr("reporter.generator.__file__", str(fake_module_file))

    g = ReportGenerator()
    g._update_landing_page(reports_dir)

    out = index_path.read_text(encoding="utf-8")
    assert 'href="data/reports/aov_report_2026-05-06.html" class="main-btn"' in out
    assert "進入最新戰報 (2026-05-06)" in out
    assert 'href="data/reports/aov_report_2026-05-05.html" class="history-item"' in out
    assert 'href="data/reports/aov_report_2026-05-01.html" class="history-item"' in out


def test_update_landing_page_no_throw_when_index_missing(tmp_path, monkeypatch, caplog):
    """邊界：index.html 不存在時，不拋例外，僅 log warning（修補後 landing 在獨立 try 內，
    保證即使這層失敗也不會拖累上游 generate() 流程）。"""
    repo_root = tmp_path
    reports_dir = repo_root / "data" / "reports"
    reports_dir.mkdir(parents=True)
    _make_report(reports_dir, "2026-05-06")

    fake_reporter_dir = repo_root / "reporter"
    fake_reporter_dir.mkdir()
    fake_module_file = fake_reporter_dir / "generator.py"
    fake_module_file.write_text("# placeholder", encoding="utf-8")
    monkeypatch.setattr("reporter.generator.__file__", str(fake_module_file))

    g = ReportGenerator()
    # 不應拋例外
    g._update_landing_page(reports_dir)
    # index.html 應仍不存在
    assert not (repo_root / "index.html").exists()
