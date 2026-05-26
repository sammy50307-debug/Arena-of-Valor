"""Content trust checker for P96 / R-017 reports.

This checker is deterministic and raw-free: it inspects rendered HTML only and
reports whether known content-trust issues are visible in the final report.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def report_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / "data" / "reports" / ("aov_report_%s.html" % date_str)


def _load_rules(repo_root: Path) -> dict:
    path = repo_root / "configs" / "content_trust_known_issues.yaml"
    if not path.exists():
        return {"expected_focus_hero": "芽芽", "forbidden_focus_terms": ["圖倫"]}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    expected = "芽芽"
    forbidden_terms: list[str] = []
    for issue in data.get("issues", []) or []:
        expected = issue.get("expected_focus_hero") or expected
        forbidden_terms.extend(issue.get("forbidden_focus_recent_terms", []) or [])
        for title in issue.get("forbidden_focus_hero_titles", []) or []:
            forbidden_terms.append(str(title).replace("觀察室", "").strip())
    return {
        "expected_focus_hero": expected,
        "forbidden_focus_terms": sorted({t for t in forbidden_terms if t}),
    }


def _focus_recent_section(html: str, expected_focus_hero: str) -> str:
    header = "📰 %s近期動態" % expected_focus_hero
    start = html.find(header)
    if start < 0:
        return ""
    end = html.find("Combat Stats Dashboard", start)
    if end < 0:
        return html[start:]
    return html[start:end]


def run_checks(repo_root: Path, date_str: str, report_file: Optional[Path] = None) -> list[CheckResult]:
    rules = _load_rules(repo_root)
    expected = rules["expected_focus_hero"]
    report = report_file or report_path(repo_root, date_str)
    if not report.exists():
        return [CheckResult("report exists", "FAIL", "missing %s" % report)]

    html = report.read_text(encoding="utf-8", errors="replace")
    results: list[CheckResult] = []

    expected_titles = ("%s 觀察室" % expected, "%s觀察室" % expected)
    results.append(
        CheckResult(
            "focus room title",
            "PASS" if any(title in html for title in expected_titles) else "FAIL",
            "expected one of %s" % ", ".join(expected_titles),
        )
    )

    forbidden_titles = [("%s 觀察室" % term, "%s觀察室" % term) for term in rules["forbidden_focus_terms"]]
    visible_forbidden_titles = [
        title
        for pair in forbidden_titles
        for title in pair
        if title and title in html
    ]
    results.append(
        CheckResult(
            "forbidden focus title",
            "FAIL" if visible_forbidden_titles else "PASS",
            "visible=%s" % (visible_forbidden_titles or []),
        )
    )
    results.append(
        CheckResult(
            "report unknown dates",
            "FAIL" if "時間未知" in html else "PASS",
            "contains_time_unknown=%s" % ("時間未知" in html),
        )
    )

    focus_section = _focus_recent_section(html, expected)
    if not focus_section:
        results.append(CheckResult("focus recent section", "PASS", "section absent"))
        return results

    forbidden_recent = [term for term in rules["forbidden_focus_terms"] if term in focus_section]
    results.append(
        CheckResult(
            "focus recent forbidden terms",
            "FAIL" if forbidden_recent else "PASS",
            "visible=%s" % (forbidden_recent or []),
        )
    )
    results.append(
        CheckResult(
            "focus recent unknown dates",
            "WARN" if "時間未知" in focus_section else "PASS",
            "contains_time_unknown=%s" % ("時間未知" in focus_section),
        )
    )
    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--date", required=True)
    parser.add_argument("--report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    report = Path(args.report) if args.report else None
    results = run_checks(repo_root, args.date, report)

    if args.json:
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
    else:
        print("| check | status | detail |")
        print("|---|---|---|")
        for result in results:
            print("| %s | %s | %s |" % (result.name, result.status, result.detail))
    return 1 if any(r.failed for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
