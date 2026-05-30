"""m4_track_blindspots.py — P72.3: M4 時效追溯機制自動化.

M4 協議（P71.1 定義）：每 Phase 收官後寫 docs/postmortems/<phase>_blindspots.md，
記錄「計畫書沒寫但實際撞到的問題」≥ 3 條，通則化加入 PHASE_TEMPLATE.md 體檢清單。

本腳本提供三項機械化追溯：
  1. --status        列出 phase × postmortem × blindspot 對照表
  2. --scaffold <ph> 為缺 blindspot 的 Phase 生成樣板（B-NNN 結構）
  3. --sync-rules    dry-run 比對 B-NNN 通則化規則 vs PHASE_TEMPLATE.md，印建議

⚠️ 不可逆動作隔離：
  PHASE_TEMPLATE.md 是凍結文件，本腳本【不會】自動寫入。
  --sync-rules 僅印「建議納入」清單供主公人工審核。

Usage:
    python scripts/m4_track_blindspots.py --status
    python scripts/m4_track_blindspots.py --scaffold p72
    python scripts/m4_track_blindspots.py --sync-rules
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from scripts.governance_utils import extract_blindspot_entries

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTMORTEM_DIR = PROJECT_ROOT / "docs" / "postmortems"
PHASE_TEMPLATE = PROJECT_ROOT / "docs" / "PHASE_TEMPLATE.md"

PHASE_RE = re.compile(r"(?:phase[-_]?|\bp)(\d+(?:\.\d+)*)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Phase ID extraction
# ---------------------------------------------------------------------------

def extract_phase_id(filename: str) -> str | None:
    """Extract phase id (e.g. '71', '70.3') from a postmortem filename."""
    m = PHASE_RE.search(filename)
    return m.group(1) if m else None


def is_blindspot_file(path: Path) -> bool:
    if "blindspot" in path.name.lower():
        return True
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:300]
    except OSError:
        return False
    return "blindspots" in head.lower() or "盲點" in head


# ---------------------------------------------------------------------------
# Postmortem pairing
# ---------------------------------------------------------------------------

def scan_postmortems() -> dict[str, dict]:
    """Group postmortem files by phase id.

    Returns: {phase_id: {'postmortems': [Path], 'blindspots': [Path]}}
    """
    grouped: dict[str, dict] = {}
    if not POSTMORTEM_DIR.exists():
        return grouped
    for path in sorted(POSTMORTEM_DIR.glob("*.md")):
        phase_id = extract_phase_id(path.name)
        if not phase_id:
            continue
        bucket = grouped.setdefault(phase_id, {"postmortems": [], "blindspots": []})
        if is_blindspot_file(path):
            bucket["blindspots"].append(path)
        else:
            bucket["postmortems"].append(path)
    return grouped


# ---------------------------------------------------------------------------
# B-NNN rule extraction
# ---------------------------------------------------------------------------

def extract_blindspot_rules(text: str) -> list[dict]:
    """Extract B-NNN entries with headline + 通則化 rule. Delegates to governance_utils."""
    return extract_blindspot_entries(text)


def collect_all_rules() -> list[dict]:
    """Collect B-NNN rules across all blindspot files."""
    rules: list[dict] = []
    for path in sorted(POSTMORTEM_DIR.glob("*.md")):
        if not is_blindspot_file(path):
            continue
        phase_id = extract_phase_id(path.name) or "?"
        text = path.read_text(encoding="utf-8", errors="ignore")
        for r in extract_blindspot_rules(text):
            r["phase"] = phase_id
            r["source"] = path.name
            rules.append(r)
    return rules


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status() -> int:
    grouped = scan_postmortems()
    if not grouped:
        print("⚠️  postmortems 目錄為空或不存在")
        return 1

    print("📋 M4 時效追溯對照表")
    print(f"   來源：{POSTMORTEM_DIR.relative_to(PROJECT_ROOT)}")
    print()
    print(f"{'Phase':<10} {'Postmortem':<12} {'Blindspot':<12} {'狀態'}")
    print("-" * 60)

    missing: list[str] = []
    for phase_id in sorted(grouped.keys(), key=lambda p: [int(x) for x in p.split(".")]):
        bucket = grouped[phase_id]
        n_pm = len(bucket["postmortems"])
        n_bs = len(bucket["blindspots"])
        if n_bs > 0:
            tag = "✅ 已配對"
        elif n_pm > 0:
            tag = "⚠️ 缺 blindspot"
            missing.append(phase_id)
        else:
            tag = "—"
        print(f"P{phase_id:<9} {n_pm:<12} {n_bs:<12} {tag}")

    print()
    print(f"共 {len(grouped)} 個 Phase / 缺 blindspot：{len(missing)} 個")
    if missing:
        print()
        print("💡 為缺 blindspot 的 Phase 生成樣板：")
        for ph in missing[:5]:
            print(f"   python scripts/m4_track_blindspots.py --scaffold p{ph}")
    return 0


_SCAFFOLD_TEMPLATE = """# P{phase_id} Blindspots — M4 追溯

> **M4 協議**：每個 Phase 收官後寫此檔，記錄「計畫書沒寫但實際撞到的問題」≥ 3 條，
> 通則化後加入 PHASE_TEMPLATE 體檢清單並升版。

- **Phase**：P{phase_id}
- **日期**：{today}
- **對應 Postmortem**：（請填入 postmortem 檔名連結）

---

## 計畫書沒寫、實際撞到的問題

### B-XXX：（盲點 headline）

**計畫書原寫**：（原計畫書怎麼描述這項任務）

**實際撞到**：（實際遇到什麼問題、為什麼計畫書沒涵蓋）

**通則化**：
> （把這個盲點抽象成可套用到未來 Phase 的規則）

**待加入**：（PHASE_TEMPLATE 的哪一段／哪個 checklist 應該補進此規則）

---

### B-XXX：（第二個盲點，按 B-001/B-002 編號續寫）

（同上格式）

---

### B-XXX：（第三個盲點）

（同上格式）

---

## 體檢清單升版摘要

| 版本 | 升版內容 | 驅動 Phase |
|---|---|---|
| v1.x（待議）| （列出本 Phase 驅動的 PHASE_TEMPLATE 升版項）| **P{phase_id}** |

---

## 給下一個 Phase 的提醒

1. **B-XXX**：（一句話總結，給未來 Phase 開工前掃過）
2. **B-XXX**：
3. **B-XXX**：
"""


def cmd_scaffold(phase_arg: str) -> int:
    phase_id = phase_arg.lstrip("Pp").strip()
    if not re.match(r"^\d+(\.\d+)*$", phase_id):
        print(f"❌ Phase 格式錯誤：{phase_arg}（範例：p72 / P71.5 / 73）", file=sys.stderr)
        return 1

    today = datetime.now().strftime("%Y-%m-%d")
    target = POSTMORTEM_DIR / f"{today}-phase-{phase_id}-blindspots.md"
    if target.exists():
        print(f"⚠️  檔案已存在，未覆寫：{target.relative_to(PROJECT_ROOT)}")
        return 1

    POSTMORTEM_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(_SCAFFOLD_TEMPLATE.format(phase_id=phase_id, today=today), encoding="utf-8")
    print(f"✅ 已生成 blindspots scaffold：{target.relative_to(PROJECT_ROOT)}")
    print()
    print("下一步：")
    print("  1. 編輯該檔，填入 ≥ 3 條 B-NNN 盲點")
    print("  2. 收官 commit 時一併納入")
    print("  3. 若有通則化規則需進 PHASE_TEMPLATE.md：")
    print("     python scripts/m4_track_blindspots.py --sync-rules")
    return 0


def cmd_sync_rules() -> int:
    """Dry-run: compare B-NNN rules vs PHASE_TEMPLATE.md, print suggestions."""
    rules = collect_all_rules()
    if not rules:
        print("⚠️  未找到任何 B-NNN 規則（檢查 docs/postmortems/*_blindspots.md）")
        return 1

    template_text = ""
    if PHASE_TEMPLATE.exists():
        template_text = PHASE_TEMPLATE.read_text(encoding="utf-8", errors="ignore")
    else:
        print(f"⚠️  PHASE_TEMPLATE.md 不存在：{PHASE_TEMPLATE}", file=sys.stderr)

    print("🔎 M4 規則同步檢查（dry-run，不寫入 PHASE_TEMPLATE.md）")
    print(f"   B-NNN 規則來源：{len(rules)} 條")
    print(f"   PHASE_TEMPLATE：{PHASE_TEMPLATE.relative_to(PROJECT_ROOT)}")
    print()

    covered: list[dict] = []
    missing: list[dict] = []

    for r in rules:
        rule_text = r["rule"]
        if not rule_text:
            continue
        # 簡單啟發式：取規則中最長的中文連續詞作為錨點，看 template 是否含
        anchor = _pick_anchor(rule_text)
        if anchor and anchor in template_text:
            covered.append({**r, "anchor": anchor})
        else:
            missing.append({**r, "anchor": anchor or "(無)"})

    print(f"✅ 已涵蓋（PHASE_TEMPLATE 已含相關描述）：{len(covered)} 條")
    for r in covered:
        print(f"   [{r['id']}] (P{r['phase']}) anchor「{r['anchor']}」")

    print()
    print(f"⚠️  建議納入（未在 PHASE_TEMPLATE 找到對應）：{len(missing)} 條")
    for r in missing:
        print(f"   [{r['id']}] (P{r['phase']}) {r['headline'][:50]}")
        if r["rule"]:
            preview = r["rule"][:80].replace("\n", " ")
            print(f"        通則：{preview}")
        print(f"        來源：{r['source']}")
        print()

    print("---")
    print("⚠️ 不可逆動作隔離：本腳本不會自動寫入 PHASE_TEMPLATE.md。")
    print("   主公審核後，請人工把建議納入的規則加進 PHASE_TEMPLATE.md，")
    print("   並更新「體檢清單升版摘要」表格的版本號（v1.x → v1.(x+1)）。")
    return 0


def _pick_anchor(rule_text: str, min_len: int = 4) -> str:
    """Pick a meaningful CJK substring as a search anchor."""
    matches = re.findall(r"[一-鿿]{%d,}" % min_len, rule_text)
    return max(matches, key=len) if matches else ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="P72.3: M4 時效追溯自動化")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="列出 phase × postmortem × blindspot 對照表")
    group.add_argument("--scaffold", metavar="PHASE", help="為指定 Phase 生成 blindspots 樣板 (e.g. p72)")
    group.add_argument("--sync-rules", action="store_true", dest="sync_rules",
                       help="dry-run: 對比 B-NNN 規則 vs PHASE_TEMPLATE.md")
    args = parser.parse_args()

    if not POSTMORTEM_DIR.exists():
        print(f"❌ postmortems 目錄不存在：{POSTMORTEM_DIR}", file=sys.stderr)
        return 1

    if args.status:
        return cmd_status()
    if args.scaffold:
        return cmd_scaffold(args.scaffold)
    if args.sync_rules:
        return cmd_sync_rules()
    return 1


if __name__ == "__main__":
    sys.exit(main())
