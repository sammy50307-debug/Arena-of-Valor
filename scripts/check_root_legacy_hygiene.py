"""Advisory root legacy hygiene checker for P100.

This checker is path-only. It warns when a commit stages root-level debug
outputs or loose legacy helper scripts, but it does not read file contents,
modify the git index, delete files, or decide cleanup.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEVERITY_ADVISORY = "ADVISORY"


ROOT_DEBUG_OUTPUTS = {
    "compile_errors.txt",
    "debug_output.txt",
    "diff_result.txt",
    "encoding_errors.txt",
    "err.log",
    "err.txt",
    "error.log",
    "error.txt",
    "full_diff.txt",
    "out.txt",
    "output.log",
    "run_log.txt",
    "syntax_out.txt",
    "test_handoff_out.txt",
    "ver.txt",
}

ROOT_LOOSE_SCRIPTS = {
    "css_compare.py",
    "diag_boot.py",
    "force_gen.py",
    "generate_final_demo.py",
    "generate_final_full_preview.py",
    "generate_flagship_report.py",
    "patch.py",
    "patch_generate.py",
    "preview_phase33.py",
    "preview_report_script.py",
    "push_now.py",
    "quick_demo.py",
}

ROOT_TEST_HEALTH_HELPERS = {
    "check_health.py",
    "syntax_check.py",
    "test_data_writer.py",
    "test_gemini.py",
    "test_imports.py",
    "test_run.py",
    "test_tg.py",
    "validate_data_dir.py",
}

ROOT_STATIC_ASSETS = {
    "step.jpg",
    "yaya_bg.png",
}

ROOT_KEEP_PATHS = {
    ".env.example",
    ".gitignore",
    ".nojekyll",
    ".pre-commit-config.yaml",
    ".secrets.baseline",
    ".cursorrules",
    ".windsurfrules",
    "AGENTS.md",
    "CLAUDE.md",
    "COMMAND_GUIDE.md",
    "GEMINI.md",
    "NEXT_SESSION_HANDOFF.md",
    "PROJECT_RULES.md",
    "Phase40_Flagship_Bible.md",
    "README.md",
    "TASK_HISTORY.md",
    "config.py",
    "dev_claude.ps1",
    "index.html",
    "main.py",
    "pyrightconfig.json",
    "requirements.txt",
}


@dataclass(frozen=True)
class RootHygieneFinding:
    path: str
    severity: str
    category: str
    action: str
    reason: str


def _normalize(path: str) -> str:
    normalized = str(path).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def _finding(path: str, category: str, action: str, reason: str) -> RootHygieneFinding:
    return RootHygieneFinding(
        path=path,
        severity=SEVERITY_ADVISORY,
        category=category,
        action=action,
        reason=reason,
    )


def classify_path(path: str) -> Optional[RootHygieneFinding]:
    normalized = _normalize(path)
    if not normalized or "/" in normalized:
        return None

    lower = normalized.lower()

    if lower in ROOT_DEBUG_OUTPUTS:
        return _finding(
            normalized,
            "root_debug_output",
            "Unstage unless this Phase explicitly approved root debug evidence.",
            "root debug outputs are quarantine candidates and should not change casually.",
        )

    if lower in ROOT_LOOSE_SCRIPTS:
        return _finding(
            normalized,
            "root_loose_legacy_script",
            "Require reference review before staging changes to this loose root helper.",
            "loose root scripts may be legacy phase helpers rather than active runtime.",
        )

    if lower in ROOT_TEST_HEALTH_HELPERS:
        return _finding(
            normalized,
            "root_test_health_helper",
            "Document the owner or move decision before staging root helper changes.",
            "root test/health helpers need ownership clarity before cleanup or edits.",
        )

    if lower in ROOT_STATIC_ASSETS:
        return _finding(
            normalized,
            "root_static_asset_decision",
            "Do not stage static asset changes without a dedicated asset-source decision.",
            "root static assets are outside P100 cleanup and may affect UI/deployment.",
        )

    if normalized in ROOT_KEEP_PATHS:
        return None

    return None


def find_root_hygiene_advisories(paths: Iterable[str]) -> list[RootHygieneFinding]:
    findings: list[RootHygieneFinding] = []
    seen: set[str] = set()
    for path in paths:
        normalized = _normalize(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        finding = classify_path(normalized)
        if finding is not None:
            findings.append(finding)
    return findings


def staged_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff --cached failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _print_table(findings: list[RootHygieneFinding]) -> None:
    if not findings:
        print("No root legacy hygiene advisories.")
        return

    print("| severity | category | path | action | reason |")
    print("|---|---|---|---|---|")
    for item in findings:
        print(
            "| %s | %s | %s | %s | %s |"
            % (item.severity, item.category, item.path, item.action, item.reason)
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Advisory root legacy hygiene checker.")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--paths", nargs="*", help="Explicit paths to check instead of staged git paths.")
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when advisories are present.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    paths = args.paths if args.paths is not None else staged_paths(repo_root)
    findings = find_root_hygiene_advisories(paths)

    if args.json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        _print_table(findings)

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
