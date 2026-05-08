#!/usr/bin/env python3
"""
lint_phase_plan.py — P71.1 STR10 實作
強制驗證 Phase 計畫書是否通過 Pre-flight 多視角體檢（M1+M2）。

M1 強制填表：X4-A ~ X4-I 九個視角，每項不能空白或含禁詞
M2 紅藍對抗：≥5 條質疑，≥2 條 S 級攻擊力

用法：
  python scripts/lint_phase_plan.py docs/P71_PLAN.md
  python scripts/lint_phase_plan.py docs/P72_PLAN.md --allow-skip  # 緊急時跳過，自動記錄至 RISK_REGISTRY
"""

import re
import sys
import argparse
import json
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).parent.parent
RISK_REGISTRY_PATH = PROJECT_ROOT / "docs" / "RISK_REGISTRY.md"

BANNED_PHRASES = ["無風險", "N/A", "都好", "TBD", "無", "略"]
MIN_CONTENT_LEN = 20
MIN_RED_TEAM_ROWS = 5
MIN_S_LEVEL_ROWS = 2

PREFLIGHT_ANCHORS = [
    ("X4-A", "攻擊者視角"),
    ("X4-B", "接手者視角"),
    ("X4-C", "災難情境"),
    ("X4-D", "5 年後視角"),
    ("X4-E", "終端 vs IDE"),
    ("X4-F", "跨平台"),
    ("X4-G", "主公個人視角"),
    ("X4-H", "觀測"),
    ("X4-I", "主公可見性"),
]

errors = []
warnings = []
skipped = False


def err(msg: str):
    errors.append(f"  ❌ {msg}")


def warn(msg: str):
    warnings.append(f"  ⚠️  {msg}")


PLACEHOLDER = "_______________________"


def extract_m1_cell(content: str, anchor: str) -> str | None:
    """
    支援兩種 M1 格式，並在多次出現時取最後一個有內容的匹配
    （避免模板展示區的空白欄位干擾驗證）：
    1. Table 格式：| **X4-A 攻擊者** | 具體內容 |
    2. 章節格式：### X4-A 攻擊者視角\n- [ ] 內容
    """
    candidates = []

    # Table 格式：findall 取所有匹配
    table_pat = rf"\|\s*\*{{0,2}}{anchor}[^\|]*\*{{0,2}}\s*\|([^\|]+)\|"
    for m in re.finditer(table_pat, content):
        candidates.append(m.group(1).strip())

    # 章節格式：findall 取所有匹配
    section_pat = rf"###\s*{anchor}[^\n]*\n(.*?)(?=###|\Z)"
    for m in re.finditer(section_pat, content, re.DOTALL):
        candidates.append(m.group(1).strip())

    if not candidates:
        return None

    # 取最後一個非空 / 非佔位符的候選
    for c in reversed(candidates):
        clean = re.sub(r"-\s*\[\s*[xX ]?\s*\]", "", c).strip()
        if clean and clean != PLACEHOLDER and len(clean) >= 5:
            return c

    # 全是空的，回傳第一個讓後續報錯
    return candidates[0]


def lint_preflight_m1(content: str):
    """M1 強制填表驗證"""
    has_preflight = "Pre-flight" in content or "✈️" in content
    if not has_preflight:
        err("找不到 Pre-flight 多視角體檢章節（M1）— 計畫書缺少此區塊")
        return

    for anchor, label in PREFLIGHT_ANCHORS:
        cell_text = extract_m1_cell(content, anchor)

        if cell_text is None:
            err(f"M1 缺少視角 {anchor}（{label}）")
            continue

        # 空白 / 佔位符檢查
        placeholder = "_______________________"
        if not cell_text or cell_text == placeholder or cell_text == f"- [ ] {placeholder}":
            err(f"M1 {anchor}（{label}）內容為空")
            continue

        # 長度檢查（去掉 checkbox 語法後）
        actual = re.sub(r"-\s*\[\s*[xX ]?\s*\]", "", cell_text).strip()
        if len(actual) < MIN_CONTENT_LEN:
            err(f"M1 {anchor}（{label}）內容過短（< {MIN_CONTENT_LEN} 字元）：'{actual[:30]}'")
            continue

        # 禁詞檢查（短文字才卡，長說明允許含這些詞）
        if len(actual) < 30:
            for phrase in BANNED_PHRASES:
                if phrase in actual:
                    err(f"M1 {anchor}（{label}）含禁詞 '{phrase}' 且說明不足")
                    break


def lint_red_team_m2(content: str):
    """M2 紅藍對抗驗證"""
    has_redteam = "紅隊" in content or "🔴" in content or "Red Team" in content
    if not has_redteam:
        err("找不到紅藍對抗章節（M2）— 計畫書缺少此區塊")
        return

    # 找表格行（含「|」且非標題行）
    table_rows = re.findall(r"\|\s*\d+\s*\|.*\|", content)
    if len(table_rows) < MIN_RED_TEAM_ROWS:
        err(f"M2 紅藍對抗行數不足：找到 {len(table_rows)} 條，需 ≥ {MIN_RED_TEAM_ROWS} 條")
        return

    # 統計 S 級行數
    s_level_rows = [r for r in table_rows if "**S**" in r or "S 級" in r]
    if len(s_level_rows) < MIN_S_LEVEL_ROWS:
        err(f"M2 S 級攻擊力不足：找到 {len(s_level_rows)} 條，需 ≥ {MIN_S_LEVEL_ROWS} 條 S 級")

    # 檢查未解決質疑（無處置標記的行）
    # 允許：入計畫、入 RISK、入 P7x.x、入 lint、入 postmortem、N/A、達標
    resolved_patterns = ["入計畫", "入 RISK", "入 P", "入 lint", "入 post", "達標", "N/A", "—"]
    unresolved = [
        r for r in table_rows
        if not any(p in r for p in resolved_patterns)
    ]
    if unresolved:
        warn(f"M2 有 {len(unresolved)} 條質疑未明確標示處置（應標『入計畫範圍』或『入 RISK_REGISTRY』）")


def append_to_risk_registry(plan_path: Path):
    """--allow-skip 時自動追加至 RISK_REGISTRY.md"""
    today = date.today().isoformat()
    entry = (
        f"\n| R-SKIP-{today} | lint_phase_plan --allow-skip 跳過體檢 | 3 | "
        f"下個 Phase 開工前必須補回 Pre-flight 體檢 | {plan_path.name} | {today} |\n"
    )
    if RISK_REGISTRY_PATH.exists():
        with open(RISK_REGISTRY_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"⚠️  已記錄至 RISK_REGISTRY.md：{entry.strip()}")
    else:
        warn(f"RISK_REGISTRY.md 不存在，跳過記錄（{RISK_REGISTRY_PATH}）")


def main():
    parser = argparse.ArgumentParser(description="Lint Phase 計畫書 Pre-flight 體檢（STR10）")
    parser.add_argument("plan_file", help="Phase 計畫書 Markdown 路徑")
    parser.add_argument(
        "--allow-skip",
        action="store_true",
        help="緊急時跳過體檢（自動記錄至 RISK_REGISTRY，下 Phase 前必補）",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan_file)
    if not plan_path.exists():
        print(f"❌ 找不到計畫書：{plan_path}")
        sys.exit(1)

    content = plan_path.read_text(encoding="utf-8")

    if args.allow_skip:
        print(f"⚠️  --allow-skip 啟用：跳過 Pre-flight 體檢，自動記錄至 RISK_REGISTRY")
        append_to_risk_registry(plan_path)
        sys.exit(0)

    print(f"🔍 lint_phase_plan — 掃描：{plan_path.name}")

    lint_preflight_m1(content)
    lint_red_team_m2(content)

    print(f"\n掃描完畢")

    if errors:
        print(f"\n錯誤（{len(errors)} 條）：")
        for e in errors:
            print(e)

    if warnings:
        print(f"\n警告（{len(warnings)} 條）：")
        for w in warnings:
            print(w)

    if not errors and not warnings:
        print("✅ 通過 Pre-flight 體檢（M1 + M2）")
    elif not errors:
        print(f"\n✅ 無阻擋性錯誤（{len(warnings)} 條警告）")
    else:
        print(f"\n❌ FAIL — {len(errors)} 條錯誤，計畫書不得凍結")
        print("   修正後重跑，或使用 --allow-skip（緊急情況）")
        sys.exit(1)


if __name__ == "__main__":
    main()
