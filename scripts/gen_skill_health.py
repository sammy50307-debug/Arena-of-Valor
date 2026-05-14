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

# Metrics integration (P72.4) — graceful fallback if logger unavailable
sys.path.insert(0, str(Path(__file__).parent))
try:
    from skill_metrics_logger import load_all, summarize, METRICS_FILE
    _METRICS_OK = True
except ImportError:
    _METRICS_OK = False
    METRICS_FILE = None  # type: ignore[assignment]

P71_PHASES = [
    ("P71.0", "SKILL_INVENTORY.md 盤點（20 skill 分類）", "✅"),
    ("P71.1", "registry.json + lint + Pre-flight 體檢", "✅"),
    ("P71.2", "S1 schema × 11 SKILL.md + S2/V1 觸發協議", "✅"),
    ("P71.3", "11 skill 自包含化 + `__main__.py` + 終端適配", "✅"),
    ("P71.4", "deploy_skills.py + pre-commit + CI + SA1/SA4", "✅"),
    ("P71.5", "8 shared → `D:/skills-shared/` + registry 絕對路徑", "✅"),
    ("P71.6", "smart-task-router 救活（L2 路由引擎）", "✅"),
    ("P71.7", "SKILL_HEALTH.md Dashboard（本腳本）", "✅"),
    ("P71.8", "6 stale shared skills Gemini 同步", "✅"),
    ("P71.9", "7 orphan → in-use + 補 S1 schema + __main__.py", "✅"),
    ("P71.10", "Postmortem + R-009~011 風險登記", "✅"),
    ("P72.0", "metrics 基礎建設（O1/O2/O3）", "✅"),
    ("P72.4", "metrics 接入 SKILL_HEALTH.md（本行）", "✅"),
]


def load_metrics_stats() -> dict[str, dict]:
    """Load and aggregate metrics. Returns empty dict on any failure."""
    if not _METRICS_OK:
        return {}
    try:
        return summarize(load_all())
    except Exception:
        return {}


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


def _metric_cells(m: dict) -> tuple[str, str, str, str]:
    """Return (calls, avg_ms, fail_pct, avg_tok) display strings."""
    if not m:
        return "—", "—", "—", "—"
    calls = str(m["calls"])
    avg_ms = f"{m['avg_duration_ms']}ms"
    fail_pct = f"{m['failure_rate_pct']:.1f}%"
    avg_in = m.get("avg_tokens_in", 0)
    avg_out = m.get("avg_tokens_out", 0)
    avg_tok = str(avg_in + avg_out) if (avg_in + avg_out) > 0 else "—"
    return calls, avg_ms, fail_pct, avg_tok


def generate(registry_path: Path, output_path: Path) -> None:
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    skills = registry["skills"]
    today = datetime.now().strftime("%Y-%m-%d")
    metrics_stats = load_metrics_stats()
    has_metrics = bool(metrics_stats)

    lines: list[str] = []

    lines += [
        "# 🩺 SKILL_HEALTH.md Dashboard",
        "",
        f"> 自動生成 by `scripts/gen_skill_health.py` | 更新：{today}",
        f"> {len(skills)} skills 狀態一覽：雙端同步 / 測試燈號 / P71-P72 進度看板",
        "",
    ]

    # Phase progress bar
    lines += [
        "## 📊 P71-P72 進度看板",
        "",
        "| 階段 | 內容 | 狀態 |",
        "|---|---|---|",
    ]
    for phase, desc, status in P71_PHASES:
        lines.append(f"| **{phase}** | {desc} | {status} |")
    lines.append("")

    # Skill health table — with metrics columns when data exists
    if has_metrics:
        lines += [
            "## 🧬 Skill 狀態總覽（含 O1/O2/O3 Metrics）",
            "",
            "| Skill | Status | Env | Deployed | Test | Last Used | Calls | Avg ms | Fail% | Avg Tok | Health |",
            "|---|---|---|---|---|---|---:|---:|---:|---:|---|",
        ]
    else:
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

        if has_metrics:
            m = metrics_stats.get(name, {})
            calls, avg_ms, fail_pct, avg_tok = _metric_cells(m)
            lines.append(
                f"| {name} | {status} | {env} | {deployed} | {test} | {last_used}"
                f" | {calls} | {avg_ms} | {fail_pct} | {avg_tok} | {health} |"
            )
        else:
            lines.append(f"| {name} | {status} | {env} | {deployed} | {test} | {last_used} | {health} |")

    lines.append("")

    # Summary
    lines += [
        "## 📈 統計摘要",
        "",
        "| 燈號 | 數量 | 說明 |",
        "|---|---|---|",
        f"| 🟢 | {counts.get('🟢', 0)} | in-use + deployed + test 全齊 |",
        f"| 🟡 | {counts.get('🟡', 0)} | stale 或 deployed 為空 |",
        f"| 🔴 | {counts.get('🔴', 0)} | orphan / archived / test 缺失 |",
        "",
    ]

    # Metrics status
    metrics_file_label = str(METRICS_FILE) if METRICS_FILE else "~/.claude/skill_metrics.jsonl"
    if has_metrics:
        total_calls = sum(s["calls"] for s in metrics_stats.values())
        lines += [
            "## 📊 Metrics 狀態（O1/O2/O3）",
            "",
            "| 項目 | 值 |",
            "|---|---|",
            f"| 來源 | `{metrics_file_label}` |",
            f"| 總呼叫次數 | {total_calls} |",
            f"| 有資料 skill 數 | {len(metrics_stats)} |",
            "| O3 Avg Tok | placeholder（待 skill 回報真實 token 用量）|",
            "",
        ]
    else:
        lines += [
            "## 📊 Metrics 狀態（O1/O2/O3）",
            "",
            f"> ⚠️ 尚無 metrics 資料（`{metrics_file_label}` 不存在）",
            "> 透過 `python __main__.py` 執行任何 skill 後即開始累積。",
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
        "**Metrics 欄位**：`Calls` 累計呼叫次數 ／ `Avg ms` 平均執行時長 (O1) ／ `Fail%` 失敗率 (O2) ／ `Avg Tok` 平均 token 估算 (O3)",
        "",
        "---",
        f"*Generated by `scripts/gen_skill_health.py` · {today}*",
    ]

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 生成完成：{output_path}")
    metrics_note = f"  📊 metrics: {len(metrics_stats)} skills with data" if has_metrics else "  📊 metrics: no data yet"
    print(f"   🟢 {counts.get('🟢', 0)}  🟡 {counts.get('🟡', 0)}  🔴 {counts.get('🔴', 0)}  共 {len(skills)} skills")
    print(metrics_note)


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
