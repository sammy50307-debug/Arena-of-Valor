#!/usr/bin/env python3
"""Generate docs/SKILL_HEALTH.md from skills/registry.json.

Usage:
    python scripts/gen_skill_health.py
    python scripts/gen_skill_health.py --output path/to/output.md
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent

P71_PHASES = [
    ("P71.0", "SKILL_INVENTORY.md 盤點（20 skill 分類）", "✅"),
    ("P71.1", "registry.json + lint + Pre-flight 體檢", "✅"),
    ("P71.2", "S1 schema × 11 SKILL.md + S2/V1 觸發協議", "✅"),
    ("P71.3", "11 skill 自包含化 + `__main__.py` + 終端適配", "✅"),
    ("P71.4", "deploy_skills.py + pre-commit + CI + SA1/SA4", "✅"),
    ("P71.5", "8 shared → `D:/skills-shared/` + registry 絕對路徑", "✅"),
    ("P71.6", "smart-task-router 救活（L2 路由引擎）", "✅"),
    ("P71.7", "SKILL_HEALTH.md Dashboard（本腳本）", "✅"),
    ("P71.8", "7 個 Gemini diff 主公裁決", "⏳"),
    ("P71.9", "8 個 orphan 處置", "⏳"),
    ("P71.10", "Postmortem + R-009~011", "⏳"),
]


def resolve_skill_path(claude_path: str) -> Path:
    p = Path(claude_path)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / claude_path


def has_test(claude_path: str) -> Optional[bool]:
    """
    Returns True if test_skill.py found, False if dir exists but no test,
    None if the skill directory is not accessible (shows as ❓).
    """
    if not claude_path:
        return None
    base = resolve_skill_path(claude_path)
    if not base.exists():
        return None
    return (base / "test_skill.py").exists() or (base / "scripts" / "test_skill.py").exists()


def env_str(environments: dict) -> str:
    mapping = [("ide", "IDE"), ("terminal", "CLI"), ("antigravity", "AG"), ("pure_llm", "LLM")]
    parts = [label for key, label in mapping if environments.get(key)]
    return "+".join(parts) if parts else "—"


def deployed_str(deployed_to: list) -> str:
    if not deployed_to:
        return "—"
    alias = {"claude-project": "claude", "gemini-global": "gemini"}
    return "+".join(alias.get(d, d) for d in deployed_to)


def test_emoji(test_result: Optional[bool]) -> str:
    if test_result is True:
        return "✅"
    if test_result is False:
        return "❌"
    return "❓"


def health_emoji(status: str, deployed_to: list, test_result: Optional[bool]) -> str:
    if status in ("orphan", "archived"):
        return "🔴"
    if test_result is False:
        return "🔴"
    if status == "stale":
        return "🟡"
    if not deployed_to:
        return "🟡"
    if test_result is None:
        return "🟡"
    return "🟢"


def generate(registry_path: Path, output_path: Path) -> None:
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    skills = registry["skills"]
    today = datetime.now().strftime("%Y-%m-%d")

    lines: list[str] = []

    lines += [
        "# 🩺 SKILL_HEALTH.md Dashboard",
        "",
        f"> 自動生成 by `scripts/gen_skill_health.py` | 更新：{today}",
        f"> {len(skills)} skills 狀態一覽：雙端同步 / 測試燈號 / P71 進度看板",
        "",
    ]

    # P71 progress bar (hardcoded per P71.7 spec)
    lines += [
        "## 📊 P71 進度看板",
        "",
        "| 階段 | 內容 | 狀態 |",
        "|---|---|---|",
    ]
    for phase, desc, status in P71_PHASES:
        lines.append(f"| **{phase}** | {desc} | {status} |")
    lines.append("")

    # Skill health table
    lines += [
        "## 🧬 Skill 狀態總覽",
        "",
        "| Skill | Status | Env | Deployed | Test | Last Used | Health |",
        "|---|---|---|---|---|---|---|",
    ]

    counts = {"🟢": 0, "🟡": 0, "🔴": 0}
    for skill in skills:
        name = skill["name"]
        status = skill.get("status", "unknown")
        claude_path = skill.get("claude_path", "")
        environments = skill.get("environments", {})
        deployed_to = skill.get("deployed_to", [])
        last_used = skill.get("last_used") or "—"

        test_result = has_test(claude_path)
        env = env_str(environments) if environments else "—"
        deployed = deployed_str(deployed_to)
        test = test_emoji(test_result)
        health = health_emoji(status, deployed_to, test_result)
        counts[health] = counts.get(health, 0) + 1

        lines.append(f"| {name} | {status} | {env} | {deployed} | {test} | {last_used} | {health} |")

    lines.append("")

    # Summary
    lines += [
        "## 📈 統計摘要",
        "",
        f"| 燈號 | 數量 | 說明 |",
        "|---|---|---|",
        f"| 🟢 | {counts.get('🟢', 0)} | in-use + deployed + test 全齊 |",
        f"| 🟡 | {counts.get('🟡', 0)} | stale 或 deployed 為空 |",
        f"| 🔴 | {counts.get('🔴', 0)} | orphan / archived / test 缺失 |",
        "",
    ]

    # Legend
    lines += [
        "## 💡 燈號說明",
        "",
        "| 燈號 | 觸發條件 |",
        "|---|---|",
        "| 🟢 | `in-use` + `deployed_to` 非空 + test 存在 |",
        "| 🟡 | `stale` 或 `deployed_to` 為空（但有 test）或 test 路徑不可達（❓）|",
        "| 🔴 | `orphan` / `archived` 或 test 確認不存在（❌）|",
        "",
        "**Test 欄位**：✅ 有 `test_skill.py` ／ ❌ 確認無 ／ ❓ 路徑不可達（CI 環境常見）",
        "",
        "**Env 縮寫**：`IDE` = VS Code 插件 ／ `CLI` = Terminal ／ `AG` = Gemini Antigravity ／ `LLM` = 純語言模型",
        "",
        "---",
        f"*Generated by `scripts/gen_skill_health.py` · {today}*",
    ]

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 生成完成：{output_path}")
    print(f"   🟢 {counts.get('🟢', 0)}  🟡 {counts.get('🟡', 0)}  🔴 {counts.get('🔴', 0)}  共 {len(skills)} skills")


def main():
    parser = argparse.ArgumentParser(description="Generate SKILL_HEALTH.md from registry.json")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "docs" / "SKILL_HEALTH.md"))
    parser.add_argument("--registry", default=str(PROJECT_ROOT / "skills" / "registry.json"))
    args = parser.parse_args()

    registry_path = Path(args.registry)
    output_path = Path(args.output)

    if not registry_path.exists():
        print(f"❌ registry.json not found: {registry_path}", file=sys.stderr)
        sys.exit(1)

    generate(registry_path, output_path)


if __name__ == "__main__":
    main()
