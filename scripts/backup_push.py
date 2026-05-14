"""backup_push.py — P72.1: 雙 remote 自動 backup.

推送目前 branch 到所有已設定的 remote，保護 GitHub 誤刪 / 帳號被駭風險。

Usage:
    python scripts/backup_push.py                    # push 當前 branch 到所有 remote
    python scripts/backup_push.py --branch main      # push 指定 branch
    python scripts/backup_push.py --status           # 只顯示 remote 狀態，不 push
    python scripts/backup_push.py --dry-run          # 模擬執行

First-time setup（第一次使用前）:
    git remote add backup https://github.com/YOUR_BACKUP_ACCOUNT/Arena-of-Valor-backup.git
    python scripts/backup_push.py
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_SETUP_GUIDE = """
⚠️  目前只有一個 remote，雙 remote backup 尚未設定。

設定步驟：
  1. 建立第二個 GitHub repo（建議 private + 不同帳號，避免單點失效）
     例：https://github.com/YOUR_BACKUP/Arena-of-Valor-backup

  2. 加入 backup remote：
     git remote add backup https://github.com/YOUR_BACKUP/Arena-of-Valor-backup.git

  3. 第一次推送：
     python scripts/backup_push.py

詳見 docs/BACKUP_SETUP.md（待主公確認帳號後建立）
"""


def get_remotes() -> list[tuple[str, str]]:
    """Return list of (name, push_url) for all remotes."""
    result = subprocess.run(
        ["git", "remote", "-v"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    seen: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2] == "(push)":
            seen[parts[0]] = parts[1]
    return list(seen.items())


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "main"


def push_to_remote(remote_name: str, branch: str, dry_run: bool) -> bool:
    """Push branch to remote. Returns True on success."""
    cmd = ["git", "push", remote_name, branch]
    if dry_run:
        print(f"  [dry-run] would run: {' '.join(cmd)}")
        return True

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"  ✅ {remote_name} → {branch}")
        if result.stderr.strip():
            print(f"     {result.stderr.strip()[:120]}")
        return True
    else:
        print(f"  ❌ {remote_name} → FAILED")
        err = (result.stderr or result.stdout).strip()
        if err:
            for line in err.splitlines()[:5]:
                print(f"     {line}")
        return False


def cmd_status(remotes: list[tuple[str, str]]) -> None:
    print("📡 Remote 狀態：")
    for name, url in remotes:
        print(f"  {name:12s}  {url}")
    if len(remotes) < 2:
        print(_SETUP_GUIDE)
    else:
        print(f"\n✅ 共 {len(remotes)} 個 remote，雙 backup 已就緒")


def main() -> int:
    parser = argparse.ArgumentParser(description="P72.1: push to all remotes (dual backup)")
    parser.add_argument("--branch", default=None, help="Branch to push (default: current)")
    parser.add_argument("--status", action="store_true", help="Show remote status only")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without pushing")
    args = parser.parse_args()

    remotes = get_remotes()
    branch = args.branch or get_current_branch()

    if args.status or not remotes:
        cmd_status(remotes)
        return 0

    print(f"🔄 backup_push: branch={branch}  remotes={[r for r, _ in remotes]}")
    if len(remotes) < 2:
        print(_SETUP_GUIDE)

    successes = 0
    for name, _url in remotes:
        if push_to_remote(name, branch, args.dry_run):
            successes += 1

    total = len(remotes)
    print(f"\n{'✅' if successes == total else '⚠️'} {successes}/{total} remote(s) pushed successfully")
    return 0 if successes == total else 1


if __name__ == "__main__":
    sys.exit(main())
