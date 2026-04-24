#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Session Handoff Packager — 跨視窗 / 跨模型對話打包器

Phase 60 特種兵。在一個對話視窗收工前，自動打包「任務快照」，
產出 lite / full 兩版 Markdown，讓下個視窗（Claude / GPT / Gemini）零摩擦接手。

Usage (CLI):
    py packager.py --doing "Phase 60 開發中" --stuck "測試第 3 項失敗" --next "修正 bootstrap 路徑"

Usage (Python API):
    from packager import SessionHandoffPackager
    p = SessionHandoffPackager(project_root=Path("."))
    result = p.pack(doing="Phase 60 開發中")
    paths = p.save(result)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SessionHandoffPackager:
    """跨視窗 / 跨模型對話打包器"""

    def __init__(self, project_root: Optional[Path] = None):
        # 自動偵測專案根目錄
        if project_root is None:
            project_root = self._find_project_root()
        self.project_root = Path(project_root).resolve()

        # 載入 Bootstrap 清單
        self.bootstrap_config = self._load_bootstrap_config()

        # 全域 handoff 輸出目錄（Antigravity 體系）
        self.global_handoff_dir = Path.home() / ".gemini" / "antigravity" / "handoff"

        # 全域 handoff 輸出目錄（Claude Code 體系）
        self.claude_handoff_dir = Path.home() / ".claude" / "handoff"

        # 專案內 handoff 輸出目錄
        self.project_handoff_dir = self.project_root / "handoff"

    def _find_project_root(self) -> Path:
        """從 CWD 向上搜尋含 .git 的目錄作為專案根"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists():
                return parent
        return current

    def _load_bootstrap_config(self) -> dict:
        """載入 bootstrap_files.json"""
        config_path = (
            self.project_root
            / ".agent"
            / "skills"
            / "session-handoff-packager"
            / "resources"
            / "bootstrap_files.json"
        )
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        # 若找不到，回傳空結構
        return {"files": []}

    # ────────────────────────────────────────────
    # Git 快照
    # ────────────────────────────────────────────

    def collect_git_snapshot(self) -> Dict:
        """擷取 git branch / HEAD commit / uncommitted files"""
        snapshot = {
            "branch": "",
            "head_commit": "",
            "head_message": "",
            "uncommitted_files": [],
            "unpushed_count": 0,
        }

        try:
            # 當前分支
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                snapshot["branch"] = result.stdout.strip()

            # HEAD commit SHA + message
            result = subprocess.run(
                ["git", "log", "--oneline", "-1"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                line = result.stdout.strip()
                parts = line.split(" ", 1)
                snapshot["head_commit"] = parts[0] if len(parts) >= 1 else ""
                snapshot["head_message"] = parts[1] if len(parts) >= 2 else ""

            # 未提交的檔案
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = [
                    l.strip()
                    for l in result.stdout.strip().split("\n")
                    if l.strip()
                ]
                snapshot["uncommitted_files"] = lines

            # 未推送的 commit 數
            result = subprocess.run(
                ["git", "rev-list", "origin/main..HEAD", "--count"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                snapshot["unpushed_count"] = int(result.stdout.strip())

        except Exception:
            pass  # Git 不存在或不在 repo 中，靜默處理

        return snapshot

    # ────────────────────────────────────────────
    # Bootstrap 段落生成
    # ────────────────────────────────────────────

    def build_bootstrap_section(self, mode: str = "lite") -> str:
        """
        L-1 Bootstrap 段落

        mode="lite": 僅列出路徑（讓 Claude Code 自行 Read）
        mode="full": 對 embed_in_full=true 的檔案內嵌全文
        """
        files = sorted(
            self.bootstrap_config.get("files", []),
            key=lambda f: f.get("order", 99),
        )

        lines = []
        lines.append("## 🔑 L-1 Bootstrap — 開局必讀清單")
        lines.append("")

        if mode == "lite":
            lines.append("> 請依序 Read 以下檔案（專案根目錄起算）：")
            lines.append("")
            for f in files:
                lines.append(
                    f"| {f['order']} | `{f['relative_path']}` | {f['purpose']} |"
                )
        else:
            lines.append(
                "> 以下含部分檔案全文；無法讀取本地檔的模型請直接使用內嵌內容。"
            )
            lines.append("")

            for f in files:
                path = self.project_root / f["relative_path"]
                if f.get("embed_in_full", False) and path.exists():
                    try:
                        content = path.read_text(encoding="utf-8")
                        lines.append(
                            f"### 📄 [{f['order']}] {f['name']} — {f['purpose']}"
                        )
                        lines.append("")
                        lines.append("```markdown")
                        lines.append(content.rstrip())
                        lines.append("```")
                        lines.append("")
                    except Exception:
                        lines.append(
                            f"| {f['order']} | `{f['relative_path']}` | {f['purpose']} | ⚠️ 無法讀取 |"
                        )
                else:
                    lines.append(
                        f"| {f['order']} | `{f['relative_path']}` | {f['purpose']} |"
                    )

        lines.append("")
        return "\n".join(lines)

    # ────────────────────────────────────────────
    # 主打包邏輯
    # ────────────────────────────────────────────

    def pack(
        self,
        doing: str,
        stuck_at: str = "",
        next_step: str = "",
        decisions: Optional[List[str]] = None,
        rejected: Optional[List[str]] = None,
        pending: Optional[List[str]] = None,
        glossary: Optional[Dict[str, str]] = None,
        quotes: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        打包當前任務快照，回傳 {"lite": "...", "full": "..."} 兩版 Markdown。

        Args:
            doing: 「正在做什麼」（必填）
            stuck_at: 「卡在哪」
            next_step: 「建議下一步」
            decisions: 本輪核心決策清單
            rejected: 已否決/禁區選項
            pending: 待決議岔路
            glossary: 名詞表（黑話→解釋）
            quotes: 關鍵原話引用
        """
        decisions = decisions or []
        rejected = rejected or []
        pending = pending or []
        glossary = glossary or {}
        quotes = quotes or []

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        git = self.collect_git_snapshot()

        # ── 組裝各層級 ──

        # 檔頭自檢指引
        header = self._build_header(timestamp)

        # L0 開場引信
        l0 = self._build_l0(doing, stuck_at, next_step)

        # L1 核心決策 + 名詞表 + 禁區
        l1 = self._build_l1(decisions, rejected, glossary)

        # L2 待決議 + 環境快照
        l2 = self._build_l2(pending, git)

        # L3 關鍵原話
        l3 = self._build_l3(quotes)

        # ── lite 版 ──
        bootstrap_lite = self.build_bootstrap_section(mode="lite")
        lite_parts = [header, bootstrap_lite, l0]
        # lite 版只含 L1 的名詞表和待決議
        if glossary:
            lite_parts.append(self._build_glossary_section(glossary))
        if pending:
            lite_parts.append(self._build_pending_section(pending))
        lite = "\n---\n\n".join([p for p in lite_parts if p.strip()])

        # ── full 版 ──
        bootstrap_full = self.build_bootstrap_section(mode="full")
        full_parts = [header, bootstrap_full, l0, l1, l2]
        if quotes:
            full_parts.append(l3)
        full = "\n---\n\n".join([p for p in full_parts if p.strip()])

        return {"lite": lite, "full": full}

    def _build_header(self, timestamp: str) -> str:
        """檔頭自檢指引"""
        return (
            f"# 📦 Session Handoff — {timestamp}\n"
            f"\n"
            f"> ⚠️ **先執行 L-1 Bootstrap 讀檔清單，讀完才看 L0 以下內容**\n"
            f"> - 你是能讀取本地檔的 AI（如 Claude Code）→ Bootstrap 走 **lite 清單**、Read 本地檔\n"
            f"> - 你是其他模型或無法讀檔 → 請使用 **handoff_full.md** 版本（含內嵌全文）\n"
            f"> - 讀完 Bootstrap + L0 即可接手；L1–L3 按需深入\n"
            f"\n"
            f"*打包時間：{timestamp}*\n"
            f"*打包工具：session-handoff-packager (Phase 60)*"
        )

    def _build_l0(self, doing: str, stuck_at: str, next_step: str) -> str:
        """L0 開場引信"""
        lines = ["## 🚀 L0 — 開場引信"]
        lines.append("")
        lines.append(f"**正在做**：{doing}")
        if stuck_at:
            lines.append(f"**卡在**：{stuck_at}")
        if next_step:
            lines.append(f"**建議下一步**：{next_step}")
        else:
            lines.append("**建議下一步**：請先確認 L0 狀態後向主公詢問方向")
        return "\n".join(lines)

    def _build_l1(
        self,
        decisions: List[str],
        rejected: List[str],
        glossary: Dict[str, str],
    ) -> str:
        """L1 核心決策 + 禁區 + 名詞表"""
        lines = ["## 📋 L1 — 核心決策與脈絡"]
        lines.append("")

        if decisions:
            lines.append("### ✅ 本輪核心決策")
            for d in decisions:
                lines.append(f"- {d}")
            lines.append("")

        if rejected:
            lines.append("### 🚫 禁區 / 已否決選項")
            for r in rejected:
                lines.append(f"- ~~{r}~~")
            lines.append("")

        if glossary:
            lines.append(self._build_glossary_section(glossary))

        return "\n".join(lines)

    def _build_glossary_section(self, glossary: Dict[str, str]) -> str:
        """名詞表段落"""
        lines = ["### 📖 名詞表（專案黑話）"]
        lines.append("")
        lines.append("| 術語 | 意思 |")
        lines.append("|---|---|")
        for term, meaning in glossary.items():
            lines.append(f"| {term} | {meaning} |")
        return "\n".join(lines)

    def _build_pending_section(self, pending: List[str]) -> str:
        """待決議段落"""
        lines = ["### ❓ 待決議岔路"]
        lines.append("")
        for p in pending:
            lines.append(f"- [ ] {p}")
        return "\n".join(lines)

    def _build_l2(self, pending: List[str], git: Dict) -> str:
        """L2 待決議 + 環境快照"""
        lines = ["## 🔧 L2 — 待決議與環境快照"]
        lines.append("")

        if pending:
            lines.append(self._build_pending_section(pending))
            lines.append("")

        lines.append("### 💻 Git 環境快照")
        lines.append("")
        lines.append(f"- **Branch**：`{git.get('branch', 'N/A')}`")
        lines.append(f"- **HEAD**：`{git.get('head_commit', 'N/A')}` — {git.get('head_message', '')}")
        lines.append(f"- **未推送 commit 數**：{git.get('unpushed_count', 0)}")

        uncommitted = git.get("uncommitted_files", [])
        if uncommitted:
            lines.append(f"- **未提交變更**（{len(uncommitted)} 項）：")
            for uf in uncommitted[:15]:  # 最多顯示 15 項
                lines.append(f"  - `{uf}`")
            if len(uncommitted) > 15:
                lines.append(f"  - ...還有 {len(uncommitted) - 15} 項")
        else:
            lines.append("- **未提交變更**：工作區乾淨 ✨")

        return "\n".join(lines)

    def _build_l3(self, quotes: List[str]) -> str:
        """L3 關鍵原話引用"""
        lines = ["## 💬 L3 — 關鍵原話引用"]
        lines.append("")
        for i, q in enumerate(quotes, 1):
            lines.append(f"> **[{i}]** {q}")
            lines.append("")
        return "\n".join(lines)

    # ────────────────────────────────────────────
    # 儲存
    # ────────────────────────────────────────────

    def save(self, packed: Dict[str, str]) -> Dict[str, Path]:
        """
        三路寫入（專案內 + Antigravity 全域 + Claude 全域）。

        回傳 {
            "project_lite": Path, "project_full": Path,
            "global_lite": Path,  "global_full": Path,
            "claude_lite": Path,  "claude_full": Path
        }
        """
        now = datetime.now()
        date_stamp = now.strftime("%Y%m%d_%H%M")
        filename_lite = f"handoff_{date_stamp}.md"
        filename_full = f"handoff_{date_stamp}_full.md"

        paths = {}

        # ① 專案內
        self.project_handoff_dir.mkdir(parents=True, exist_ok=True)
        p_lite = self.project_handoff_dir / filename_lite
        p_full = self.project_handoff_dir / filename_full
        p_lite.write_text(packed["lite"], encoding="utf-8")
        p_full.write_text(packed["full"], encoding="utf-8")
        paths["project_lite"] = p_lite
        paths["project_full"] = p_full

        # ② Antigravity 全域
        self.global_handoff_dir.mkdir(parents=True, exist_ok=True)
        g_lite = self.global_handoff_dir / filename_lite
        g_full = self.global_handoff_dir / filename_full
        g_lite.write_text(packed["lite"], encoding="utf-8")
        g_full.write_text(packed["full"], encoding="utf-8")
        paths["global_lite"] = g_lite
        paths["global_full"] = g_full

        # ③ Claude Code 全域
        self.claude_handoff_dir.mkdir(parents=True, exist_ok=True)
        c_lite = self.claude_handoff_dir / filename_lite
        c_full = self.claude_handoff_dir / filename_full
        c_lite.write_text(packed["lite"], encoding="utf-8")
        c_full.write_text(packed["full"], encoding="utf-8")
        paths["claude_lite"] = c_lite
        paths["claude_full"] = c_full

        return paths


# ────────────────────────────────────────────
# CLI 介面
# ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Session Handoff Packager — 跨視窗對話打包器"
    )
    parser.add_argument(
        "--doing", required=True, help="正在做什麼（必填）"
    )
    parser.add_argument(
        "--stuck", default="", help="卡在哪"
    )
    parser.add_argument(
        "--next", dest="next_step", default="", help="建議下一步"
    )
    parser.add_argument(
        "--decisions", nargs="*", default=[], help="核心決策（可多筆）"
    )
    parser.add_argument(
        "--rejected", nargs="*", default=[], help="已否決選項（可多筆）"
    )
    parser.add_argument(
        "--pending", nargs="*", default=[], help="待決議岔路（可多筆）"
    )
    parser.add_argument(
        "--project-root", default=None, help="專案根目錄（預設自動偵測）"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只印出不儲存"
    )

    args = parser.parse_args()

    root = Path(args.project_root) if args.project_root else None
    packager = SessionHandoffPackager(project_root=root)

    result = packager.pack(
        doing=args.doing,
        stuck_at=args.stuck,
        next_step=args.next_step,
        decisions=args.decisions,
        rejected=args.rejected,
        pending=args.pending,
    )

    if args.dry_run:
        print("=" * 60)
        print("=== LITE 版 ===")
        print("=" * 60)
        print(result["lite"])
        print()
        print("=" * 60)
        print("=== FULL 版 ===")
        print("=" * 60)
        print(result["full"])
    else:
        paths = packager.save(result)
        print("[✓] Session Handoff 打包完成！")
        for key, path in paths.items():
            print(f"    {key}: {path}")


if __name__ == "__main__":
    main()
