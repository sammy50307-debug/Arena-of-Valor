import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
PREVIEWS_DIR = PROJECT_ROOT / "ui_previews"
INDEX_PATH = PROJECT_ROOT / "index.html"


class HotDeployer:
    """
    熱部署儀
    自動偵測最新報表，同步至 ui_previews，並執行 Git Push 部署至 GitHub Pages。
    """

    def __init__(self, dry_run: bool = False):
        """
        dry_run: True = 僅本地同步，不執行 git push
        """
        self.dry_run = dry_run
        self.project_root = PROJECT_ROOT

    def find_latest_report(self) -> Optional[Path]:
        """尋找 data/reports/ 中最新的 HTML 戰報"""
        if not REPORTS_DIR.exists():
            return None
        reports = sorted(REPORTS_DIR.glob("aov_report_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
        return reports[0] if reports else None

    def sync_to_previews(self, report_path: Path) -> Path:
        """將報表同步複製到 ui_previews/"""
        PREVIEWS_DIR.mkdir(exist_ok=True)
        dest = PREVIEWS_DIR / report_path.name
        shutil.copy2(report_path, dest)

        bg_src = report_path.parent.parent / "yaya_bg.png"
        if bg_src.exists():
            shutil.copy2(bg_src, PREVIEWS_DIR / "yaya_bg.png")

        return dest

    def update_index(self, report_path: Path) -> bool:
        """更新 index.html 中指向最新報表的連結"""
        if not INDEX_PATH.exists():
            return False

        try:
            content = INDEX_PATH.read_text(encoding="utf-8")
            old_pattern = "data/reports/aov_report_"
            if old_pattern in content:
                import re
                new_content = re.sub(
                    r'data/reports/aov_report_[\w\-\.]+\.html',
                    f"data/reports/{report_path.name}",
                    content
                )
                INDEX_PATH.write_text(new_content, encoding="utf-8")
                return True
        except Exception:
            pass
        return False

    def git_push(self, report_path: Path) -> Dict[str, Any]:
        """執行 git add / commit / push"""
        if self.dry_run:
            return {"status": "skipped", "reason": "dry_run 模式，跳過 git push"}

        try:
            subprocess.run(["git", "add", str(report_path)], cwd=str(self.project_root), check=True, capture_output=True)
            subprocess.run(["git", "add", str(PREVIEWS_DIR)], cwd=str(self.project_root), capture_output=True)
            subprocess.run(["git", "add", str(INDEX_PATH)], cwd=str(self.project_root), capture_output=True)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"deploy: 自動熱部署戰報 {report_path.name} [{timestamp}]"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(self.project_root), capture_output=True, text=True, encoding="utf-8"
            )

            if "nothing to commit" in result.stdout:
                return {"status": "skipped", "reason": "無新變更，跳過推送"}

            push_result = subprocess.run(
                ["git", "push"],
                cwd=str(self.project_root), capture_output=True, text=True, encoding="utf-8"
            )

            if push_result.returncode == 0:
                return {"status": "success", "commit_message": commit_msg}
            else:
                return {"status": "error", "stderr": push_result.stderr}

        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": str(e)}

    def deploy(self) -> Dict[str, Any]:
        """一鍵執行完整部署流程：偵測 → 同步 → 更新索引 → 推送"""
        report = self.find_latest_report()
        if not report:
            return {"status": "error", "reason": "找不到任何報表，請先執行 main.py 生成報表"}

        synced = self.sync_to_previews(report)
        index_updated = self.update_index(report)
        git_result = self.git_push(report)

        return {
            "status": "success" if git_result["status"] in ("success", "skipped") else "error",
            "report": str(report.name),
            "synced_to": str(synced),
            "index_updated": index_updated,
            "git": git_result,
            "dry_run": self.dry_run,
            "deployed_at": datetime.now().isoformat()
        }
