#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Session Handoff Packager — 7 項自動化測試

測試項目：
  1. 最小打包：只傳 doing → lite/full 兩版皆有效 Markdown
  2. 全參數打包：傳齊所有欄位 → 各層級皆出現在輸出中
  3. Git 快照：正確擷取 branch / commit / uncommitted
  4. Bootstrap lite：僅含路徑列表，不含檔案全文
  5. Bootstrap full：內嵌至少 1 份檔案全文（embed_in_full=true 的檔案）
  6. 三路寫入：專案 + Antigravity 全域 + Claude 全域 共 6 檔皆成功
  7. 檔頭自檢指引：兩版都含「⚠️ 先執行 L-1 Bootstrap」提示
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# 移除強制 reconfigure，改由外部環境變數控制，避免靜默崩潰

# 將 scripts/ 加入路徑
SKILL_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from packager import SessionHandoffPackager

# ── 全域測試計數 ──
_passed = 0
_failed = 0


def _report(test_id, name, ok, detail=""):
    global _passed, _failed
    if ok:
        _passed += 1
        print(f"  [✓] Test {test_id}: {name}")
    else:
        _failed += 1
        print(f"  [✗] Test {test_id}: {name} — {detail}")


def _get_project_root():
    """從本檔向上找到含 .git 的目錄"""
    current = SKILL_DIR
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    return SKILL_DIR


def test_1_minimal_pack():
    """最小打包：只傳 doing → lite/full 兩版皆有效 Markdown"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)
    result = p.pack(doing="測試用最小打包")

    ok = (
        isinstance(result, dict)
        and "lite" in result
        and "full" in result
        and len(result["lite"]) > 50
        and len(result["full"]) > 50
        and "測試用最小打包" in result["lite"]
        and "測試用最小打包" in result["full"]
    )
    _report(1, "最小打包（lite/full 皆有效）", ok,
            f"lite={len(result.get('lite', ''))}c, full={len(result.get('full', ''))}c")


def test_2_full_params_pack():
    """全參數打包：各層級皆出現"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)
    result = p.pack(
        doing="Phase 60 全參數測試",
        stuck_at="bootstrap 路徑有誤",
        next_step="修正後重跑測試",
        decisions=["選項 A：走 Antigravity 體系"],
        rejected=["選項 B：走 Claude 體系"],
        pending=["是否同步至 Obsidian"],
        glossary={"芽芽": "傳說對決角色 Yena", "戰情室": "本專案暱稱"},
        quotes=["主公：開始 P60 吧"],
    )

    full = result["full"]
    checks = {
        "L0 doing": "Phase 60 全參數測試" in full,
        "L0 stuck": "bootstrap 路徑有誤" in full,
        "L0 next": "修正後重跑測試" in full,
        "L1 decision": "選項 A" in full,
        "L1 rejected": "選項 B" in full,
        "L1 glossary": "芽芽" in full and "Yena" in full,
        "L2 pending": "是否同步至 Obsidian" in full,
        "L2 git": "Branch" in full,
        "L3 quote": "主公" in full and "P60" in full,
    }

    all_ok = all(checks.values())
    failed_items = [k for k, v in checks.items() if not v]
    _report(2, "全參數打包（9 項子檢查）", all_ok,
            f"失敗: {failed_items}" if failed_items else "")


def test_3_git_snapshot():
    """Git 快照：正確擷取基本資訊"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)
    git = p.collect_git_snapshot()

    ok = (
        isinstance(git, dict)
        and "branch" in git
        and "head_commit" in git
        and len(git["branch"]) > 0
        and len(git["head_commit"]) >= 7  # 至少 7 字元的 short SHA
    )
    branch = git.get('branch', 'N/A')
    commit = git.get('head_commit', 'N/A')
    _report(3, f"Git 快照（branch={branch}, commit={commit}）", ok)


def test_4_bootstrap_lite():
    """Bootstrap lite：僅含路徑列表"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)
    section = p.build_bootstrap_section(mode="lite")

    ok = (
        "L-1 Bootstrap" in section
        and "請依序 Read" in section
        and "```markdown" not in section  # lite 不應包含內嵌全文
    )
    _report(4, "Bootstrap lite（僅列路徑、無內嵌全文）", ok)


def test_5_bootstrap_full():
    """Bootstrap full：內嵌至少 1 份檔案全文"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)
    section = p.build_bootstrap_section(mode="full")

    ok = (
        "L-1 Bootstrap" in section
        and "```markdown" in section  # full 應包含內嵌全文
    )
    _report(5, "Bootstrap full（含內嵌全文）", ok)


def test_6_triple_write():
    """三路寫入：專案 + Antigravity 全域 + Claude 全域 共 6 檔皆成功"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)

    # 使用臨時目錄避免污染真實資料
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        p.project_handoff_dir = tmp / "project_handoff"
        p.global_handoff_dir = tmp / "global_handoff"
        p.claude_handoff_dir = tmp / "claude_handoff"

        result = p.pack(doing="三路寫入測試")
        paths = p.save(result)

        ok = (
            len(paths) == 6
            and all(Path(v).exists() for v in paths.values())
            and all(Path(v).stat().st_size > 0 for v in paths.values())
        )
        sizes = {k: v.stat().st_size for k, v in paths.items()}
        _report(6, f"三路寫入（6 檔皆存在）", ok,
                f"paths={len(paths)}, sizes={sizes}" if not ok else "")


def test_7_header_warning():
    """檔頭自檢指引：兩版都含警告提示"""
    root = _get_project_root()
    p = SessionHandoffPackager(project_root=root)
    result = p.pack(doing="檔頭測試")

    warning_text = "先執行 L-1 Bootstrap"
    ok = (
        warning_text in result["lite"]
        and warning_text in result["full"]
    )
    _report(7, "檔頭自檢指引（兩版皆含 Bootstrap 警告）", ok)


# ── 主測試入口 ──

def main():
    print()
    print("=" * 60)
    print("  📦 Session Handoff Packager — 自動化測試")
    print("=" * 60)
    print()

    test_1_minimal_pack()
    test_2_full_params_pack()
    test_3_git_snapshot()
    test_4_bootstrap_lite()
    test_5_bootstrap_full()
    test_6_triple_write()
    test_7_header_warning()

    print()
    print("-" * 60)
    total = _passed + _failed
    if _failed == 0:
        print(f"  [✓] ALL TESTS PASSED — {_passed}/{total} 通過")
        print("  📦 Session Handoff Packager 已就位，跨視窗銜接無死角！")
    else:
        print(f"  [!] {_failed}/{total} 項測試失敗")
    print("-" * 60)
    print()

    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
