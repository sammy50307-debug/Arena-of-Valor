#!/usr/bin/env python3
"""
deploy_skills.py — P71.4 Skill 同步工具（copy + lockfile，Windows-safe）
含 Path traversal 防護（SA1）+ 部署清單 lockfile。

不用 symlink（Windows 需 admin）；改用 shutil.copytree + .deploy_manifest.json。

用法：
  python scripts/deploy_skills.py                         # 預覽（dry-run，預設）
  python scripts/deploy_skills.py --execute               # 實際執行
  python scripts/deploy_skills.py --execute --backup      # 執行 + 備份舊目錄
  python scripts/deploy_skills.py --skill history-trend-query --execute
  python scripts/deploy_skills.py --direction gemini2claude --execute
  python scripts/deploy_skills.py --list                  # 顯示可部署清單
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "skills" / "registry.json"
MANIFEST_PATH = PROJECT_ROOT / ".deploy_manifest.json"

# SA1: 允許的根目錄（path traversal 只能打到這些範圍內）
ALLOWED_ROOTS: list[Path] = [
    PROJECT_ROOT.resolve(),
    Path.home().resolve() / ".gemini",
    Path("D:/skills-shared").resolve(),
]


# ── SA1 path traversal 防護 ──────────────────────────────────────────────────

def safe_path(raw: str) -> Path | None:
    """
    SA1 Path traversal protection.
    展開 ~ 並 resolve，確認最終路徑在 ALLOWED_ROOTS 之一的子節點或本身。
    傳入 None / 空字串 → 回傳 None（代表未設定，非攻擊）。
    """
    if not raw:
        return None
    resolved = Path(raw).expanduser().resolve()
    if any(
        resolved == root or root in resolved.parents
        for root in ALLOWED_ROOTS
    ):
        return resolved
    raise ValueError(
        f"[SA1] 路徑超出允許範圍：{raw!r} → {resolved}\n"
        f"      允許根目錄：{[str(r) for r in ALLOWED_ROOTS]}"
    )


# ── Registry 讀取 ─────────────────────────────────────────────────────────────

def load_skills() -> list[dict]:
    if not REGISTRY_PATH.exists():
        print(f"❌ registry.json 不存在：{REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        reg = json.load(f)
    return reg.get("skills", [])


# ── 核心：複製單一 skill ───────────────────────────────────────────────────────

def deploy_one(
    skill: dict,
    direction: str,
    dry_run: bool,
    backup: bool,
) -> dict | None:
    """
    複製 skill 目錄。
    回傳部署紀錄 dict；跳過時回傳 None。
    """
    name = skill.get("name", "?")
    claude_raw = skill.get("claude_path")
    gemini_raw = skill.get("gemini_path")

    # 解析 SA1 safe paths（支援絕對路徑 claude_path，如 D:/skills-shared/X）
    try:
        if claude_raw:
            _cp = Path(claude_raw)
            claude_path = safe_path(
                str(_cp) if _cp.is_absolute() else str(PROJECT_ROOT / claude_raw)
            )
        else:
            claude_path = None
        gemini_path = safe_path(gemini_raw)
    except ValueError as e:
        print(f"  ❌ [{name}] {e}")
        return None

    if direction == "claude2gemini":
        src, dst = claude_path, gemini_path
    else:
        src, dst = gemini_path, claude_path

    if src is None or dst is None:
        print(f"  ⏭  [{name}] claude_path 或 gemini_path 未設定，跳過")
        return None

    if not src.exists():
        print(f"  ⚠️  [{name}] 來源目錄不存在：{src}，跳過")
        return None

    arrow = "claude→gemini" if direction == "claude2gemini" else "gemini→claude"
    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"  {prefix}📦 [{name}] {arrow}")
    print(f"       src: {src}")
    print(f"       dst: {dst}")

    if not dry_run:
        if backup and dst.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dst = dst.parent / f"{dst.name}.bak_{ts}"
            shutil.copytree(str(dst), str(backup_dst))
            print(f"       💾 已備份至：{backup_dst}")

        if dst.exists():
            shutil.rmtree(str(dst))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(src), str(dst))
        print(f"       ✅ 完成")

    return {
        "name": name,
        "direction": direction,
        "src": str(src),
        "dst": str(dst),
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
    }


# ── Lockfile（.deploy_manifest.json）────────────────────────────────────────

def save_manifest(records: list[dict]) -> None:
    existing: list[dict] = []
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open(encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    merged = {(r["name"], r["direction"]): r for r in existing}
    for r in records:
        merged[(r["name"], r["direction"])] = r

    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)
    print(f"\n📋 Lockfile 已更新：{MANIFEST_PATH}")


# ── List 模式 ─────────────────────────────────────────────────────────────────

def list_skills(skills: list[dict]) -> None:
    print(f"\n{'Skill':<35} {'Claude Path':<40} {'Gemini Path':<45} Status")
    print("-" * 130)
    for s in skills:
        name = s.get("name", "?")
        cp = s.get("claude_path") or "—"
        gp = s.get("gemini_path") or "—"
        st = s.get("status", "?")
        print(f"{name:<35} {cp:<40} {gp:<45} {st}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="deploy_skills.py — P71.4 Skill 同步工具（copy + lockfile，Windows-safe）"
    )
    parser.add_argument("--execute", action="store_true",
                        help="實際執行（預設 dry-run，不動任何檔案）")
    parser.add_argument("--backup", action="store_true",
                        help="覆蓋前備份目標目錄（名稱加 .bak_<timestamp>）")
    parser.add_argument("--skill", metavar="NAME",
                        help="只部署指定 skill（完整 kebab-case 名稱）")
    parser.add_argument("--direction",
                        choices=["claude2gemini", "gemini2claude"],
                        default="claude2gemini",
                        help="同步方向（預設 claude→gemini）")
    parser.add_argument("--list", action="store_true",
                        help="列出所有 skill 的路徑資訊後離開")
    args = parser.parse_args()

    skills = load_skills()

    if args.list:
        list_skills(skills)
        return

    dry_run = not args.execute
    if dry_run:
        print("🔍 [DRY-RUN 模式] 不實際複製任何檔案。加 --execute 才真正執行。\n")

    if args.skill:
        matched = [s for s in skills if s.get("name") == args.skill]
        if not matched:
            print(f"❌ 找不到 skill：{args.skill!r}", file=sys.stderr)
            sys.exit(1)
        skills = matched

    records: list[dict] = []
    for skill in skills:
        rec = deploy_one(skill, args.direction, dry_run, args.backup)
        if rec:
            records.append(rec)

    verb = "預覽" if dry_run else "已同步"
    print(f"\n📊 結果：{len(records)} 個 skill {verb}")

    if not dry_run and records:
        save_manifest(records)


if __name__ == "__main__":
    main()
