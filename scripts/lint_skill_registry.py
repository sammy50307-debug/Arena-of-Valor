#!/usr/bin/env python3
"""
lint_skill_registry.py — P71.2 升級版
驗證 skills/registry.json 的格式完整性 + 實體存在性 + S1 schema 欄位。

P71.1：基礎格式 + V1-5 啟動標記 trace check
P71.2：S1 完整欄位驗證（when_to_use / trigger_keywords / environments 等）

用法：
  python scripts/lint_skill_registry.py
  python scripts/lint_skill_registry.py --fix-report   # 輸出缺失項目的修復清單
  python scripts/lint_skill_registry.py --s1-only      # 僅檢查 in-use/stale 的 S1 完整欄位
"""

import json
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "skills" / "registry.json"

REQUIRED_FIELDS = ["name", "type", "status", "claude_path", "deployed_to"]
VALID_TYPES = {"exec", "pipe", "prompt", "data"}
VALID_STATUSES = {"in-use", "stale", "orphan", "archived"}

# S1 欄位：in-use / stale 狀態的 skill 必須有完整 S1 schema
S1_REQUIRED_STATUSES = {"in-use", "stale"}
S1_REQUIRED_FIELDS = [
    "schema_version",
    "version",
    "description",
    "when_to_use",
    "when_NOT_to_use",
    "trigger_keywords",
    "entry_points",
    "environments",
    "deployed_to",
    "requires",
    "depends_on",
    "last_used",
]
S1_ENTRY_POINT_KEYS = ["cli", "import", "prompt_paste", "claude_slash"]
S1_ENVIRONMENT_KEYS = ["ide", "terminal", "antigravity", "pure_llm"]

errors = []
warnings = []
_WARN_ONLY = False  # D4: 2026-05-23 後改 pre-commit hook 移除 --warn-only 升為 block


def err(msg: str):
    errors.append(f"  ❌ {msg}")


def warn(msg: str):
    warnings.append(f"  ⚠️  {msg}")


def lint_s1_schema(skill: dict, prefix: str):
    """驗證 S1 schema 必填欄位（in-use / stale 必過）。"""
    for field in S1_REQUIRED_FIELDS:
        if field not in skill:
            err(f"{prefix} 缺少 S1 必填欄位：{field}")
            continue

        val = skill[field]

        # when_to_use / when_NOT_to_use — 非空 list
        if field in ("when_to_use", "when_NOT_to_use"):
            if not isinstance(val, list) or len(val) == 0:
                err(f"{prefix} {field} 必須是非空陣列")

        # trigger_keywords — 非空 list，至少 2 個關鍵字
        if field == "trigger_keywords":
            if not isinstance(val, list) or len(val) < 2:
                err(f"{prefix} trigger_keywords 至少需要 2 個關鍵字，現有：{len(val) if isinstance(val, list) else 0}")

        # entry_points — 必須有 cli / import / prompt_paste / claude_slash
        if field == "entry_points":
            if not isinstance(val, dict):
                err(f"{prefix} entry_points 必須是物件")
            else:
                for key in S1_ENTRY_POINT_KEYS:
                    if key not in val:
                        err(f"{prefix} entry_points 缺少 {key} 欄位")

        # environments — 四個布林欄位必須全有
        if field == "environments":
            if not isinstance(val, dict):
                err(f"{prefix} environments 必須是物件")
            else:
                for key in S1_ENVIRONMENT_KEYS:
                    if key not in val:
                        err(f"{prefix} environments 缺少 {key} 欄位")
                    elif not isinstance(val[key], bool):
                        err(f"{prefix} environments.{key} 必須是布林值")

        # schema_version — 整數 >= 1
        if field == "schema_version":
            if not isinstance(val, int) or val < 1:
                err(f"{prefix} schema_version 必須是整數 >= 1")

        # description — 非空字串
        if field == "description":
            if not isinstance(val, str) or len(val.strip()) == 0:
                err(f"{prefix} description 不能為空")


def lint_registry(s1_only: bool = False):
    if not REGISTRY_PATH.exists():
        print(f"❌ registry.json 不存在：{REGISTRY_PATH}")
        sys.exit(1)

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        try:
            reg = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ registry.json JSON 解析失敗：{e}")
            sys.exit(1)

    # 頂層 schema
    if "schema_version" not in reg:
        err("缺少頂層 schema_version 欄位")
    if "skills" not in reg or not isinstance(reg["skills"], list):
        err("缺少 skills 陣列或格式錯誤")
        print_result()
        sys.exit(1)

    skills = reg["skills"]
    names_seen = set()

    for i, skill in enumerate(skills):
        name = skill.get("name", f"<skill[{i}]>")
        prefix = f"[{name}]"

        # 重複名稱
        if name in names_seen:
            err(f"{prefix} 重複的 skill name")
        names_seen.add(name)

        # 必填欄位（所有 skill 共用）
        for field in REQUIRED_FIELDS:
            if field not in skill:
                err(f"{prefix} 缺少必填欄位：{field}")

        # type 合法值
        t = skill.get("type", "")
        if t not in VALID_TYPES:
            err(f"{prefix} type 值無效：'{t}'（允許：{VALID_TYPES}）")

        # status 合法值
        s = skill.get("status", "")
        if s not in VALID_STATUSES:
            err(f"{prefix} status 值無效：'{s}'（允許：{VALID_STATUSES}）")

        # S1 schema 驗證（僅 in-use / stale）
        if s in S1_REQUIRED_STATUSES:
            lint_s1_schema(skill, prefix)

        # claude_path 目錄存在性
        claude_path_str = skill.get("claude_path")
        if claude_path_str:
            claude_path = PROJECT_ROOT / claude_path_str
            if not claude_path.exists():
                err(f"{prefix} claude_path 目錄不存在：{claude_path}")
            else:
                # SKILL.md 存在性
                skill_md = claude_path / "SKILL.md"
                if not skill_md.exists():
                    err(f"{prefix} 缺少 SKILL.md：{skill_md}")
                else:
                    # V1-5 trace check：SKILL.md 必須有啟動標記
                    content = skill_md.read_text(encoding="utf-8")
                    if "已啟動" not in content:
                        warn(f"{prefix} SKILL.md 缺少啟動標記（V1-5）：'[{name} 已啟動]'")
                    # S1 trace check：in-use/stale skill 的 SKILL.md 必須有完整 frontmatter
                    if s in S1_REQUIRED_STATUSES:
                        if "schema_version:" not in content:
                            warn(f"{prefix} SKILL.md frontmatter 缺少 schema_version（S1 未升級）")
                        if "when_to_use:" not in content:
                            warn(f"{prefix} SKILL.md frontmatter 缺少 when_to_use（S1 未升級）")
                        if "trigger_keywords:" not in content:
                            warn(f"{prefix} SKILL.md frontmatter 缺少 trigger_keywords（S1 未升級）")

        # deployed_to 合法值
        deployed = skill.get("deployed_to", [])
        if not isinstance(deployed, list):
            err(f"{prefix} deployed_to 必須是陣列")
        for d in deployed:
            if d not in {"claude-project", "gemini-global", "claude-global"}:
                warn(f"{prefix} deployed_to 含未知值：'{d}'")

    print_result(skills)


def print_result(skills: list | None = None):
    total = len(skills) if skills else 0
    s1_count = sum(1 for s in (skills or []) if s.get("status") in S1_REQUIRED_STATUSES)
    print(f"\n🔍 lint_skill_registry (P71.2) — {total} skills 掃描（{s1_count} 個需過 S1 schema 驗證）")

    if errors:
        print(f"\n錯誤（{len(errors)} 條）：")
        for e in errors:
            print(e)

    if warnings:
        print(f"\n警告（{len(warnings)} 條）：")
        for w in warnings:
            print(w)

    if not errors and not warnings:
        print("✅ 全部通過，無錯誤、無警告")
    elif not errors:
        print(f"\n✅ 無阻擋性錯誤（{len(warnings)} 條警告）")
    else:
        if _WARN_ONLY:
            print(f"\n⚠️  WARN-ONLY — {len(errors)} 條錯誤（D4 warning 模式，2026-05-23 後升 block）")
        else:
            print(f"\n❌ FAIL — {len(errors)} 條錯誤須修正後才能通過")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Lint skills/registry.json（P71.2 含 S1 schema 驗證）")
    parser.add_argument("--s1-only", action="store_true", help="僅檢查 in-use/stale 的 S1 完整欄位（目前 flag 保留，行為與完整模式相同）")
    parser.add_argument("--warn-only", action="store_true", help="D4：印出錯誤但 exit 0（warning 模式，2026-05-23 後升 block）")
    args = parser.parse_args()
    if args.warn_only:
        global _WARN_ONLY
        _WARN_ONLY = True
    lint_registry(s1_only=args.s1_only)


if __name__ == "__main__":
    main()
