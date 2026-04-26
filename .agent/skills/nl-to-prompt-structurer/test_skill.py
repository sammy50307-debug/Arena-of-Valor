"""Phase 62 S1 地基測試（10 項）。

涵蓋：lang_detector x5、templates x4、keyword_dict 完整性 x1。
執行：`py .agent/skills/nl-to-prompt-structurer/test_skill.py`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from scripts.lang_detector import detect_lang
from scripts.templates import SECTIONS, render_skeleton


_RESULTS = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    _RESULTS.append((name, cond, detail))
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""))


def t_lang_zh_pure() -> None:
    _check("T1 lang_detector 純中文 → zh",
           detect_lang("最近兩週悟空的聲量怎麼樣") == "zh")


def t_lang_en_pure() -> None:
    _check("T2 lang_detector 純英文 → en",
           detect_lang("How is Wukong trending in the last two weeks") == "en")


def t_lang_mixed_zh_dominant() -> None:
    result = detect_lang("用 markdown 整理今天的戰報")
    _check("T3 lang_detector 中文為主夾英文 → zh",
           result == "zh", f"got={result}")


def t_lang_empty() -> None:
    _check("T4 lang_detector 空字串 → zh（R1 預設）",
           detect_lang("") == "zh")


def t_lang_short_cjk() -> None:
    _check("T5 lang_detector 短中文（< 5 字）→ zh",
           detect_lang("查戰報") == "zh")


def t_template_zh_empty() -> None:
    md = render_skeleton(lang="zh")
    cond = (
        "## 角色 (Role)" in md
        and "## 背景 (Context)" in md
        and "## 任務 (Task)" in md
        and "## 限制 (Constraints)" in md
        and "## 輸出格式 (Output Format)" in md
        and "（未指定）" in md
        and "通用助理" in md
    )
    _check("T6 templates zh 空 slots → 五段全在 + 通用助理 + 未指定", cond)


def t_template_en_empty() -> None:
    md = render_skeleton(lang="en")
    cond = (
        "## Role" in md
        and "## Context" in md
        and "## Task" in md
        and "## Constraints" in md
        and "## Output Format" in md
        and "(unspecified)" in md
        and "Generalist Assistant" in md
    )
    _check("T7 templates en 空 slots → 五段全在 + Generalist + (unspecified)", cond)


def t_template_partial_slots() -> None:
    md = render_skeleton(lang="zh", slots={"task": "整理今天戰報", "constraints": "300 字以內"})
    cond = (
        "整理今天戰報" in md
        and "300 字以內" in md
        and "（未指定）" in md  # 其他欄位仍補預設
    )
    _check("T8 templates zh 部分 slots → 已填欄位顯實值 + 未填欄位補預設", cond)


def t_template_invalid_lang_fallback() -> None:
    md = render_skeleton(lang="ja")
    cond = "## 角色 (Role)" in md and "通用助理" in md
    _check("T9 templates 無效 lang → fallback zh", cond)


def t_keyword_dict_integrity() -> None:
    path = _HERE / "resources" / "keyword_dict.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cond = (
        "zh" in data and "en" in data
        and all(cat in data["zh"] for cat in ("task_verbs", "constraints", "format_hints"))
        and all(cat in data["en"] for cat in ("task_verbs", "constraints", "format_hints"))
        and len(data["zh"]["task_verbs"]) >= 10
        and len(data["en"]["task_verbs"]) >= 10
    )
    _check("T10 keyword_dict.json 雙語三類齊全 + 動詞 ≥10", cond)


def main() -> int:
    print("=" * 60)
    print("Phase 62 S1 地基測試")
    print("=" * 60)

    for fn in (
        t_lang_zh_pure,
        t_lang_en_pure,
        t_lang_mixed_zh_dominant,
        t_lang_empty,
        t_lang_short_cjk,
        t_template_zh_empty,
        t_template_en_empty,
        t_template_partial_slots,
        t_template_invalid_lang_fallback,
        t_keyword_dict_integrity,
    ):
        fn()

    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    total = len(_RESULTS)
    print("-" * 60)
    print(f"結果：{passed}/{total} 通過")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
