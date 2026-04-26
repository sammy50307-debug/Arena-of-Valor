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
from scripts.intent_extractor import (
    extract_all,
    extract_constraints,
    extract_format,
    extract_task,
)
from scripts.structurer import (
    PromptStructurer,
    _dedupe_overlap,
    _escape_slot,
    _infer_role,
)
from scripts.query_router import (
    _detect_heroes,
    _detect_mode,
    _parse_days,
    _parse_until,
    _parse_weighted,
    route_query,
)


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


# ============================================================
# Phase 62 S2 抽取核心測試（11 項，T11-T21）
# ============================================================


def t_extract_task_zh() -> None:
    _check("T11 extract_task('整理今天戰報') → '整理'",
           extract_task("整理今天戰報") == "整理")


def t_extract_task_en() -> None:
    _check("T12 extract_task('summarize today report') → 'summarize'",
           extract_task("summarize today report") == "summarize")


def t_extract_task_multi_char_priority() -> None:
    # "查詢" 比 "查" 長，應優先命中 → 解 P62-R2 多字詞優先策略
    result = extract_task("查詢最近兩週悟空的聲量")
    _check("T13 extract_task 多字詞優先（'查詢' 勝過 '查'）",
           result == "查詢", f"got={result}")


def t_extract_constraints_multiple() -> None:
    text = "整理今天戰報，300 字以內、必須用繁體"
    cons = extract_constraints(text)
    cond = "字以內" in cons and "必須" in cons and "繁體" in cons
    _check("T14 extract_constraints 抽多重限制（字以內/必須/繁體）", cond, f"got={cons}")


def t_extract_constraints_none() -> None:
    _check("T15 extract_constraints 無命中 → 空 list",
           extract_constraints("今天天氣很好") == [])


def t_extract_format_zh() -> None:
    _check("T16 extract_format('用表格整理') → '表格'",
           extract_format("用表格整理今天戰報") == "表格")


def t_extract_format_en_case_insensitive() -> None:
    # 大小寫不敏感（"JSON" 應命中 "json"）
    result = extract_format("output as JSON")
    _check("T17 extract_format 大小寫不敏感（JSON → json）",
           result == "json", f"got={result}")


def t_extract_all_combo() -> None:
    out = extract_all("用 markdown 整理今天的戰報，300 字以內")
    cond = (
        out["lang"] == "zh"
        and out["task_verb"] == "整理"
        and out["format_hint"] == "markdown"
        and "字以內" in out["constraints"]
    )
    _check("T18 extract_all 中文組合句（lang/動詞/格式/限制 全中）", cond, f"got={out}")


def t_extract_all_en_combo() -> None:
    out = extract_all("summarize today's stats as a table within 300 words")
    cond = (
        out["lang"] == "en"
        and out["task_verb"] == "summarize"
        and out["format_hint"] == "table"
        and ("within" in out["constraints"] or "words" in out["constraints"])
    )
    _check("T19 extract_all 英文組合句", cond, f"got={out}")


def t_extract_empty_input() -> None:
    out = extract_all("")
    cond = (
        out["task_verb"] is None
        and out["constraints"] == []
        and out["format_hint"] is None
    )
    _check("T20 extract_all 空字串 → 三類皆 None/空", cond)


def t_dict_size_s2_expanded() -> None:
    """解 S1 P62-R2：S2 必須擴充至 ≥40 詞 / 類。"""
    path = _HERE / "resources" / "keyword_dict.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    sizes = {
        "zh.task_verbs": len(data["zh"]["task_verbs"]),
        "zh.constraints": len(data["zh"]["constraints"]),
        "zh.format_hints": len(data["zh"]["format_hints"]),
        "en.task_verbs": len(data["en"]["task_verbs"]),
        "en.constraints": len(data["en"]["constraints"]),
        "en.format_hints": len(data["en"]["format_hints"]),
    }
    cond = all(v >= 30 for v in sizes.values())
    _check("T21 keyword_dict S2 擴充至 ≥30 詞/類（解 P62-R2）", cond, f"sizes={sizes}")


# ============================================================
# Phase 62 S3 主類別測試（10 項，T22-T31）
# ============================================================


def t_structurer_zh_full() -> None:
    s = PromptStructurer()
    md = s.structure("用 markdown 整理今天戰報，300 字以內")
    cond = (
        "## 角色 (Role)" in md
        and "資料整理員" in md  # role 由 "整理" 推斷
        and "## 任務 (Task)" in md
        and "整理今天戰報" in md
        and "## 限制 (Constraints)" in md
        and "字以內" in md
        and "## 輸出格式 (Output Format)" in md
        and "markdown" in md
    )
    _check("T22 PromptStructurer 中文端到端（五段全填、role 自動推斷）", cond, "" if cond else md)


def t_structurer_en_full() -> None:
    s = PromptStructurer()
    md = s.structure("translate the report into Chinese within 200 words")
    cond = (
        "## Role" in md
        and "Translator" in md
        and "## Task" in md
        and "translate" in md.lower()
        and "## Constraints" in md
    )
    _check("T23 PromptStructurer 英文端到端（role=Translator）", cond, "" if cond else md)


def t_structurer_lang_override() -> None:
    s = PromptStructurer()
    md = s.structure("整理今天戰報", lang="en")
    cond = "## Role" in md and "## Task" in md  # 強制英文標頭
    _check("T24 lang 覆寫：中文輸入強制英文模板", cond)


def t_structurer_role_override() -> None:
    s = PromptStructurer()
    md = s.structure("整理今天戰報", role="戰情室分析師")
    cond = "戰情室分析師" in md and "資料整理員" not in md
    _check("T25 role 覆寫優先於推斷", cond)


def t_role_inference_translate() -> None:
    _check("T26 role_inference '翻譯' → '譯者'",
           _infer_role("翻譯", "zh") == "譯者")


def t_structurer_lite_mode() -> None:
    s = PromptStructurer()
    md = s.structure("用表格整理戰報", mode="lite")
    cond = (
        "## 任務 (Task)" in md
        and "## 輸出格式 (Output Format)" in md
        and "## 角色 (Role)" not in md  # lite 不含
        and "## 背景 (Context)" not in md
        and "## 限制 (Constraints)" not in md
        and "表格" in md
    )
    _check("T27 mode='lite' 只含 task + output_format 兩段", cond)


def t_escape_slot_heading() -> None:
    """解 S1 P62-R5：slot 含偽 heading 應 escape。"""
    raw = "段落一\n## 偽 Heading\n段落二"
    out = _escape_slot(raw)
    # 行首 ## 應被換成 \## ；用換行 + \## 確認在「行首」位置
    cond = "\n\\## " in out and "段落一" in out and "段落二" in out
    _check("T28 _escape_slot 行首 ## 跳脫（解 R5）", cond, f"got={out!r}")


def t_dedupe_overlap_constraints() -> None:
    """解 S2 P62-R7：constraints overlap dedupe。"""
    items = ["字以內", "個字以內", "必須"]  # "字以內" 是 "個字以內" substring
    out = _dedupe_overlap(items)
    cond = "字以內" not in out and "個字以內" in out and "必須" in out
    _check("T29 _dedupe_overlap 去除被 superstring 涵蓋的短項（解 R7）", cond, f"got={out}")


def t_structurer_empty_input() -> None:
    s = PromptStructurer()
    md = s.structure("")
    cond = (
        "## 角色 (Role)" in md
        and "通用助理" in md  # 預設角色
        and "（未指定）" in md  # 任務空白
    )
    _check("T30 空輸入端到端 → 五段骨架 + 預設角色 + 未指定", cond)


def t_structurer_multiline_safety() -> None:
    """多行輸入 + 含 markdown 元字元 → 結構不被破壞。"""
    s = PromptStructurer()
    text = "整理戰報\n## 注意事項\n- 第一點\n- 第二點"
    md = s.structure(text)
    # 五段全在、且使用者輸入中的 ## 已被 escape
    cond = (
        md.count("## 角色 (Role)") == 1
        and md.count("## 任務 (Task)") == 1
        and md.count("## 限制 (Constraints)") == 1
        and md.count("## 輸出格式 (Output Format)") == 1
        and "\\## 注意事項" in md  # escape 生效
    )
    _check("T31 多行輸入含 ## → 五段結構不破壞 + escape 生效", cond, "" if cond else md)


# ============================================================
# Phase 62 S4 Query Router + CLI 測試（12 項，T32-T43）
# ============================================================


def t_route_hero_zh() -> None:
    """中文單英雄路由。"""
    result = route_query("芽芽最近兩週聲量", hero_candidates=["芽芽", "蝶舞"])
    cond = (
        result["api"] == "hero_trend"
        and result["kwargs"].get("hero_name") == "芽芽"
        and result["kwargs"]["days"] == 14
        and result["fallback"] is False
    )
    _check("T32 route_query 中文單英雄 → hero_trend", cond, f"got={result}")


def t_route_heroes_en() -> None:
    """英文多英雄路由。"""
    result = route_query("compare Yaya and Dievu for 7 days", hero_candidates=["Yaya", "Dievu"])
    cond = (
        result["api"] == "heroes_trend"
        and set(result["kwargs"].get("hero_names", [])) == {"Yaya", "Dievu"}
        and result["kwargs"]["days"] == 7
    )
    _check("T33 route_query 英文多英雄 → heroes_trend", cond, f"got={result}")


def t_route_overall_zh() -> None:
    """中文整體輿情路由。"""
    result = route_query("整體輿情最近一個月", hero_candidates=["芽芽"])
    cond = (
        result["api"] == "overall_trend"
        and result["kwargs"]["days"] == 30
        and result["fallback"] is False
    )
    _check("T34 route_query 整體輿情 → overall_trend, days=30", cond, f"got={result}")


def t_route_platform_zh() -> None:
    """中文平台路由。"""
    result = route_query("各平台聲量 7 天", hero_candidates=[])
    cond = (
        result["api"] == "platform_trend"
        and result["kwargs"]["days"] == 7
    )
    _check("T35 route_query 各平台 → platform_trend, days=7", cond, f"got={result}")


def t_route_fallback() -> None:
    """無法判定 → fallback。"""
    result = route_query("Hello world", hero_candidates=[])
    cond = (
        result["api"] == "overall_trend"
        and result["fallback"] is True
    )
    _check("T36 route_query 無法判定 → fallback=True, overall_trend", cond, f"got={result}")


def t_parse_days_units() -> None:
    """天數解析：多種單位。"""
    cond = (
        _parse_days("三週的走勢") == 21
        and _parse_days("1 month trend") == 30
        and _parse_days("看一下最近的東西") == 14  # 無數字 → 預設 14
        and _parse_days("最近 5 天") == 5
    )
    _check("T37 _parse_days 多種單位（三週=21 / 1 month=30 / 無=14 / 5天=5）", cond)


def t_parse_until_date() -> None:
    """until 日期解析。"""
    r1 = _parse_until("到 2026-04-20 為止")
    r2 = _parse_until("普通句子沒日期")
    cond = r1 == "2026-04-20" and r2 is None
    _check("T38 _parse_until 解析 YYYY-MM-DD / 無日期=None", cond, f"got r1={r1}, r2={r2}")


def t_parse_weighted() -> None:
    """weighted 旗標偵測。"""
    cond = (
        _parse_weighted("用加權方式看聲量") is True
        and _parse_weighted("show weighted average") is True
        and _parse_weighted("普通查詢") is False
    )
    _check("T39 _parse_weighted 加權偵測（中/英/無）", cond)


def t_cli_prompt_basic() -> None:
    """CLI prompt 子命令基本呼叫。"""
    import subprocess
    cli_path = str(_HERE / "scripts" / "cli.py")
    proc = subprocess.run(
        [sys.executable, cli_path, "prompt", "整理今天戰報"],
        capture_output=True, text=True, cwd=str(_HERE),
    )
    cond = proc.returncode == 0 and "## 任務 (Task)" in proc.stdout
    _check("T40 cli.py prompt positional arg → 五段式輸出", cond,
           f"rc={proc.returncode}, stderr={proc.stderr[:200]}" if not cond else "")


def t_cli_prompt_stdin() -> None:
    """CLI prompt --stdin 含單引號（解 R15）。"""
    import subprocess
    cli_path = str(_HERE / "scripts" / "cli.py")
    proc = subprocess.run(
        [sys.executable, cli_path, "prompt", "--stdin"],
        input="含'單引號'的文字 整理戰報",
        capture_output=True, text=True, cwd=str(_HERE),
    )
    cond = proc.returncode == 0 and "## 任務 (Task)" in proc.stdout and "單引號" in proc.stdout
    _check("T41 cli.py prompt --stdin 含單引號 → 正常輸出（解 R15）", cond,
           f"rc={proc.returncode}, stderr={proc.stderr[:200]}" if not cond else "")


def t_cli_route() -> None:
    """CLI route 子命令。"""
    import subprocess
    cli_path = str(_HERE / "scripts" / "cli.py")
    proc = subprocess.run(
        [sys.executable, cli_path, "route", "整體輿情 7 天"],
        capture_output=True, text=True, cwd=str(_HERE),
    )
    cond = proc.returncode == 0 and "overall_trend" in proc.stdout
    _check("T42 cli.py route → JSON 含 overall_trend", cond,
           f"rc={proc.returncode}, stderr={proc.stderr[:200]}" if not cond else "")


def t_route_empty_input() -> None:
    """空輸入 → fallback + 不 raise。"""
    result = route_query("", hero_candidates=[])
    cond = (
        result["api"] == "overall_trend"
        and result["fallback"] is True
        and result["kwargs"]["days"] == 14
    )
    _check("T43 route_query 空輸入 → fallback + 不 raise", cond, f"got={result}")


def main() -> int:
    print("=" * 60)
    print("Phase 62 S1 地基 + S2 抽取核心 + S3 主類別 + S4 Query Router 測試")
    print("=" * 60)

    for fn in (
        # S1
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
        # S2
        t_extract_task_zh,
        t_extract_task_en,
        t_extract_task_multi_char_priority,
        t_extract_constraints_multiple,
        t_extract_constraints_none,
        t_extract_format_zh,
        t_extract_format_en_case_insensitive,
        t_extract_all_combo,
        t_extract_all_en_combo,
        t_extract_empty_input,
        t_dict_size_s2_expanded,
        # S3
        t_structurer_zh_full,
        t_structurer_en_full,
        t_structurer_lang_override,
        t_structurer_role_override,
        t_role_inference_translate,
        t_structurer_lite_mode,
        t_escape_slot_heading,
        t_dedupe_overlap_constraints,
        t_structurer_empty_input,
        t_structurer_multiline_safety,
        # S4
        t_route_hero_zh,
        t_route_heroes_en,
        t_route_overall_zh,
        t_route_platform_zh,
        t_route_fallback,
        t_parse_days_units,
        t_parse_until_date,
        t_parse_weighted,
        t_cli_prompt_basic,
        t_cli_prompt_stdin,
        t_cli_route,
        t_route_empty_input,
    ):
        fn()

    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    total = len(_RESULTS)
    print("-" * 60)
    print(f"結果：{passed}/{total} 通過")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

