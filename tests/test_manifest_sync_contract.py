from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_gitignore_allows_run_manifests_to_be_versioned():
    text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "!data/runs/" in text
    assert "!data/runs/**/" in text
    assert "!data/runs/**/run_manifest.json" in text


def test_sync_paths_include_run_manifests():
    main_text = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    workflow_text = (PROJECT_ROOT / ".github" / "workflows" / "daily_report.yml").read_text(encoding="utf-8")

    assert '"data/runs/"' in main_text
    assert "git add data/reports/ data/runs/ data/llm_cache.json index.html" in workflow_text


def test_workflow_reports_llm_secret_presence_without_secret_values():
    workflow_text = (PROJECT_ROOT / ".github" / "workflows" / "daily_report.yml").read_text(encoding="utf-8")

    assert "LLM Secret Preflight (Advisory)" in workflow_text
    assert "::warning::GEMINI_API_KEY missing" in workflow_text
    assert "::warning::OPENAI_API_KEY missing" in workflow_text
