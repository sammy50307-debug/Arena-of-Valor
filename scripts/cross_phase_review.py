"""cross_phase_review.py — P72.2: M3 歷史交叉審查 (自動化).

從 docs/postmortems/ 讀最近 N 個 Phase 的盲點與教訓，
生成 M3 體檢清單供新 Phase 計畫書使用。

Usage:
    python scripts/cross_phase_review.py                  # 預設最近 5 個 postmortem
    python scripts/cross_phase_review.py --recent 3       # 最近 3 個
    python scripts/cross_phase_review.py --output json    # JSON 輸出
    python scripts/cross_phase_review.py --list           # 列出可用 postmortem 檔案

M3 整合到 Phase 開工流程:
    Phase 計畫書草稿完成後，執行本腳本，將輸出的 checklist 加入計畫書的
    「M3 歷史交叉審查」段落，逐條確認「本 Phase 是否重蹈過去漏洞」。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from scripts.governance_utils import extract_blindspot_entries

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTMORTEM_DIR = PROJECT_ROOT / "docs" / "postmortems"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_blindspots(text: str) -> list[dict]:
    """Extract B-NNN entries from blindspot files. Delegates to governance_utils."""
    return extract_blindspot_entries(text)


def _extract_next_phase_reminders(text: str) -> list[str]:
    """Extract '給下一個 Phase 的提醒' bullet items."""
    m = re.search(r"## 給下一個 Phase 的提醒\n(.*?)(?=\n## |$)", text, re.DOTALL)
    if not m:
        return []
    lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
    return [ln.lstrip("0123456789. ") for ln in lines if ln]


def _extract_core_lessons(text: str) -> list[str]:
    """Extract 核心教訓 from regular postmortems (deduplicated)."""
    seen: set[str] = set()
    lessons: list[str] = []
    # Pattern: > **「...」**  (prefer this — most specific)
    for m in re.finditer(r">\s*\*\*「(.+?)」\*\*", text):
        candidate = m.group(1).strip()
        key = candidate.replace(" ", "")
        if key not in seen:
            seen.add(key)
            lessons.append(candidate)
    return lessons


def _extract_iya_list(text: str) -> list[str]:
    """Extract '以為' items (G2-3 cognitive bias list)."""
    m = re.search(r"## .*?以為.*?清單.*?\n(.*?)(?=\n## |$)", text, re.DOTALL)
    if not m:
        return []
    raw_lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
    items: list[str] = []
    for ln in raw_lines:
        ln = re.sub(r"^\d+\.\s*", "", ln).strip()
        # Remove leading **以為** markup
        ln = re.sub(r"^\*\*以為\*\*\s*", "", ln).strip()
        # Skip separator lines or short noise
        if not ln or ln == "---" or len(ln) < 8:
            continue
        items.append(ln)
    return items[:6]  # cap at 6 to avoid noise


# ---------------------------------------------------------------------------
# Main parse logic
# ---------------------------------------------------------------------------

def parse_postmortem(path: Path) -> dict:
    """Parse a postmortem file and return structured lesson data."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    is_blindspot = "blindspot" in path.name.lower() or "盲點" in text[:200]

    result: dict = {
        "file": path.name,
        "is_blindspot": is_blindspot,
        "blindspots": [],
        "next_phase_reminders": [],
        "core_lessons": [],
        "iya_items": [],
    }

    if is_blindspot:
        result["blindspots"] = _extract_blindspots(text)
        result["next_phase_reminders"] = _extract_next_phase_reminders(text)
    else:
        result["core_lessons"] = _extract_core_lessons(text)
        result["iya_items"] = _extract_iya_list(text)

    return result


def list_postmortems(recent: int | None = None) -> list[Path]:
    """Return postmortem files sorted newest-first."""
    if not POSTMORTEM_DIR.exists():
        return []
    files = sorted(POSTMORTEM_DIR.glob("*.md"), key=lambda p: p.name, reverse=True)
    if recent:
        files = files[:recent]
    return files


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_checklist(parsed: list[dict], today: str) -> str:
    lines: list[str] = [
        f"# M3 歷史交叉審查清單",
        f"# 生成時間：{today}  |  來源：最近 {len(parsed)} 個 postmortem",
        f"# 用法：逐條確認「本 Phase 是否重蹈過去漏洞」",
        "",
    ]
    total_items = 0
    for p in parsed:
        fname = p["file"]
        lines.append(f"## {fname}")
        lines.append("")

        if p["is_blindspot"]:
            # 只顯示 B-xxx 通則化版本（next_phase_reminders 是相同內容的縮略版，省略避免重複）
            for bs in p["blindspots"]:
                check_text = bs["rule"] or bs["headline"]
                lines.append(f"- [ ] **{bs['id']}**: {check_text}")
                total_items += 1
        else:
            for lesson in p["core_lessons"]:
                lines.append(f"- [ ] [教訓] {lesson}")
                total_items += 1
            for iya in p["iya_items"]:
                lines.append(f"- [ ] [以為] {iya}")
                total_items += 1

        lines.append("")

    if total_items == 0:
        lines.append("（未抽取到任何教訓 — 請確認 postmortem 格式符合預期）")
    else:
        lines += [
            f"---",
            f"共 {total_items} 條歷史教訓需逐一確認。",
            f"將以上 checklist 貼入新 Phase 計畫書 §M3 段落，逐條勾選後才視為 Pre-flight 通過。",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="P72.2: M3 歷史交叉審查 (自動化)")
    parser.add_argument("--recent", type=int, default=5, metavar="N",
                        help="讀最近 N 個 postmortem 檔案 (default: 5)")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--list", action="store_true", dest="list_only",
                        help="只列出可用 postmortem 檔案")
    args = parser.parse_args()

    if not POSTMORTEM_DIR.exists():
        print(f"❌ postmortems 目錄不存在：{POSTMORTEM_DIR}", file=sys.stderr)
        return 1

    files = list_postmortems()

    if args.list_only:
        print(f"📁 {POSTMORTEM_DIR}")
        for f in files:
            tag = "[blindspot]" if "blindspot" in f.name else "[postmortem]"
            print(f"  {tag:12s} {f.name}")
        return 0

    recent_files = files[:args.recent]
    if not recent_files:
        print("⚠️  無 postmortem 檔案可讀", file=sys.stderr)
        return 1

    parsed = [parse_postmortem(f) for f in recent_files]
    today = datetime.now().strftime("%Y-%m-%d")

    if args.output == "json":
        print(json.dumps({"generated": today, "sources": parsed}, ensure_ascii=False, indent=2))
        return 0

    print(render_checklist(parsed, today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
