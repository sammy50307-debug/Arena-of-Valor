from __future__ import annotations

from pathlib import Path

from reporter.generator import ReportGenerator


def _write_report(path: Path, mode: str) -> None:
    path.write_text(
        f"<!-- cache_hit: 1/2 (50%) | llm_calls: 1 | mode: {mode} -->\n<html></html>\n",
        encoding="utf-8",
    )


def _write_index(path: Path, main_date: str = "2026-05-01") -> None:
    path.write_text(
        (
            '<a href="data/reports/aov_report_%s.html" class="main-btn">進入最新戰報 (%s)</a>\n'
            '<a href="#" class="history-item">A</a>\n'
            '<a href="#" class="history-item">B</a>\n'
        )
        % (main_date, main_date),
        encoding="utf-8",
    )


def test_update_landing_uses_latest_production_only(tmp_path: Path):
    reports = tmp_path / "reports"
    reports.mkdir()
    _write_report(reports / "aov_report_2026-05-16.html", mode="preview")
    _write_report(reports / "aov_report_2026-05-15.html", mode="production")
    _write_report(reports / "aov_report_2026-05-14.html", mode="production")

    index_file = tmp_path / "index.html"
    _write_index(index_file)

    gen = ReportGenerator()
    gen._update_landing_page(reports, index_file=index_file)

    updated = index_file.read_text(encoding="utf-8")
    assert 'href="data/reports/aov_report_2026-05-15.html" class="main-btn"' in updated
    assert "進入最新戰報 (2026-05-15)" in updated
    assert 'href="data/reports/aov_report_2026-05-14.html" class="history-item"' in updated
    assert "aov_report_2026-05-16.html" not in updated


def test_update_landing_keeps_content_when_no_production(tmp_path: Path):
    reports = tmp_path / "reports"
    reports.mkdir()
    _write_report(reports / "aov_report_2026-05-16.html", mode="preview")
    _write_report(reports / "aov_report_2026-05-15.html", mode="showcase")

    index_file = tmp_path / "index.html"
    _write_index(index_file, main_date="2026-05-06")
    before = index_file.read_text(encoding="utf-8")

    gen = ReportGenerator()
    gen._update_landing_page(reports, index_file=index_file)

    after = index_file.read_text(encoding="utf-8")
    assert after == before


def test_promote_candidate_updates_canonical_and_landing(tmp_path: Path):
    reports = tmp_path / "reports"
    reports.mkdir()
    candidate = reports / "aov_report_2026-05-16_v2.html"
    _write_report(candidate, mode="production")
    _write_report(reports / "aov_report_2026-05-15.html", mode="production")

    index_file = tmp_path / "index.html"
    _write_index(index_file, main_date="2026-05-06")

    gen = ReportGenerator()
    promoted = gen.promote_candidate(candidate, "2026-05-16", output_dir=reports, index_file=index_file)

    assert promoted == reports / "aov_report_2026-05-16.html"
    assert promoted.exists()
    assert promoted.read_text(encoding="utf-8") == candidate.read_text(encoding="utf-8")

    updated = index_file.read_text(encoding="utf-8")
    assert 'href="data/reports/aov_report_2026-05-16.html" class="main-btn"' in updated
