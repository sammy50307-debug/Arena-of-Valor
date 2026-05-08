#!/usr/bin/env python3
"""
lint_skill_registry.py — P71.1 基礎版
驗證 skills/registry.json 的格式完整性 + 實體存在性。

P71.2 升級：加 S1 完整 schema 驗證（when_to_use / trigger_keywords 等）
P71.2 升級：加 V1-5 trace check（SKILL.md 啟動標記存在性）

用法：
  python scripts/lint_skill_registry.py
  python scripts/lint_skill_registry.py --fix-report   # 輸出缺失項目的修復清單
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

errors = []
warnings = []


def err(msg: str):
    errors.append(f"  ❌ {msg}")


def warn(msg: str):
    warnings.append(f"  ⚠️  {msg}")


def lint_registry(fix_report: bool = False):
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

        # 必填欄位
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

        # deployed_to 合法值
        deployed = skill.get("deployed_to", [])
        if not isinstance(deployed, list):
            err(f"{prefix} deployed_to 必須是陣列")
        for d in deployed:
            if d not in {"claude-project", "gemini-global", "claude-global"}:
                warn(f"{prefix} deployed_to 含未知值：'{d}'")

    print_result(fix_report, skills)


def print_result(fix_report: bool = False, skills: list = None):
    total = len(skills) if skills else 0
    print(f"\n🔍 lint_skill_registry — {total} skills 掃描完畢")

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
        print(f"\n❌ FAIL — {len(errors)} 條錯誤須修正後才能通過")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Lint skills/registry.json")
    parser.add_argument("--fix-report", action="store_true", help="輸出缺失項目修復清單")
    args = parser.parse_args()
    lint_registry(fix_report=args.fix_report)


if __name__ == "__main__":
    main()
