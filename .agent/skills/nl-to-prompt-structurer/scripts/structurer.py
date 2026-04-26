"""PromptStructurer 主類別（Phase 62 S3 主類別）。

把 lang_detector + intent_extractor + templates 串成端到端：
自然語言 text → 五段式 Markdown prompt。

附加處理：
- role_inference：依 task_verb 規則映射出對應角色（解 S1 P62-R3）
- _escape_slot：跳脫 slot 內可能破壞五段式結構的元字元（解 S1 P62-R5）
- _dedupe_overlap：去除 constraints 中互為 substring 的重複命中（解 S2 P62-R7）
- mode='lite'：只輸出任務 + 輸出格式兩段（精簡場景）
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .intent_extractor import extract_all
from .lang_detector import detect_lang
from .templates import render_skeleton

_ROLE_MAP = {
    "zh": {
        "翻譯": "譯者",
        "撰寫": "寫手", "寫": "寫手", "改寫": "寫手", "重寫": "寫手", "潤飾": "寫手", "校對": "寫手",
        "分析": "分析師", "評估": "分析師", "比較": "分析師", "對比": "分析師",
        "整理": "資料整理員", "歸納": "資料整理員", "排序": "資料整理員",
        "查詢": "情報員", "查": "情報員", "找": "情報員", "找出": "情報員", "搜尋": "情報員",
        "規劃": "策略顧問", "設計": "策略顧問", "預測": "策略顧問",
        "解釋": "說明員", "說明": "說明員", "回答": "說明員", "回覆": "說明員",
        "推薦": "推薦顧問", "建議": "推薦顧問",
        "繪製": "視覺設計師", "畫": "視覺設計師",
        "計算": "計算員", "統計": "計算員",
    },
    "en": {
        "translate": "Translator",
        "write": "Writer", "rewrite": "Writer", "polish": "Writer", "proofread": "Writer", "edit": "Writer",
        "analyze": "Analyst", "analyse": "Analyst", "evaluate": "Analyst", "assess": "Analyst", "compare": "Analyst",
        "summarize": "Summarizer", "summarise": "Summarizer", "outline": "Summarizer",
        "query": "Researcher", "find": "Researcher", "search": "Researcher", "extract": "Researcher",
        "plan": "Strategist", "design": "Strategist", "predict": "Strategist",
        "explain": "Explainer", "describe": "Explainer", "answer": "Explainer",
        "recommend": "Advisor", "suggest": "Advisor",
        "calculate": "Calculator", "compute": "Calculator",
        "classify": "Classifier", "categorize": "Classifier", "rank": "Classifier",
    },
}

_DEFAULT_ROLE = {"zh": "通用助理", "en": "Generalist Assistant"}


def _infer_role(task_verb: Optional[str], lang: str) -> str:
    if task_verb and task_verb in _ROLE_MAP.get(lang, {}):
        return _ROLE_MAP[lang][task_verb]
    return _DEFAULT_ROLE.get(lang, _DEFAULT_ROLE["zh"])


def _escape_slot(value: str) -> str:
    """跳脫 slot 內會破壞五段式結構的元字元（行首 `#` heading）。

    僅 escape 行首的 `#`（防止被 Markdown 渲染當 heading 取代外層五段式）。
    其他字元不動，保留 caller 原始輸入彈性。
    """
    if not value:
        return value
    return re.sub(r"(^|\n)(#+)\s", lambda m: f"{m.group(1)}\\{m.group(2)} ", value)


def _dedupe_overlap(items: List[str]) -> List[str]:
    """若 A 是 B 的 substring，刪短的 A，保長的 B（順序保留長者首見位置）。"""
    if not items:
        return []
    keep: List[str] = []
    for x in items:
        # 若已有任一保留項是 x 的 superstring → 跳過 x
        if any((x in k) and (x != k) for k in keep):
            continue
        # 若 x 是任一保留項的 superstring → 移除被涵蓋者
        keep = [k for k in keep if not ((k in x) and (k != x))]
        keep.append(x)
    return keep


def _format_constraints(items: List[str], lang: str) -> str:
    if not items:
        return "（未指定）" if lang == "zh" else "(unspecified)"
    bullet = "- "
    return "\n".join(f"{bullet}{it}" for it in items)


class PromptStructurer:
    """自然語言 → 五段式 Markdown prompt（純規則式，零 LLM）。"""

    def __init__(self, lang: Optional[str] = None) -> None:
        self._default_lang = lang  # None = 每次呼叫自動偵測

    def structure(
        self,
        text: str,
        lang: Optional[str] = None,
        role: Optional[str] = None,
        mode: str = "full",
        context: Optional[str] = None,
    ) -> str:
        """主 API：把 text 轉成五段式 Markdown。

        - lang：'zh' / 'en' / None（自動偵測）；priority: arg > 預設 > 自動
        - role：手動覆寫角色；None → 依 task_verb 推斷 → fallback 預設角色
        - mode：'full'（五段全在）/ 'lite'（只 task + output_format）
        - context：手動補背景；None 則該段顯示「（未指定）」
        """
        chosen_lang = lang or self._default_lang or detect_lang(text or "")
        if chosen_lang not in ("zh", "en"):
            chosen_lang = "zh"

        info: Dict[str, object] = extract_all(text or "", chosen_lang)
        task_verb = info["task_verb"]  # type: ignore[assignment]
        constraints = _dedupe_overlap(info["constraints"])  # type: ignore[arg-type]
        format_hint = info["format_hint"]  # type: ignore[assignment]

        # 角色決議：手動 > 推斷 > 預設
        chosen_role = role or _infer_role(task_verb, chosen_lang)

        # 任務段：原始 text（escape 後）；若空則用偵測到的 verb 或預設
        if text and text.strip():
            task_text = _escape_slot(text.strip())
        elif task_verb:
            task_text = task_verb
        else:
            task_text = "（未指定）" if chosen_lang == "zh" else "(unspecified)"

        slots: Dict[str, str] = {
            "role": _escape_slot(chosen_role),
            "task": task_text,
            "constraints": _format_constraints(constraints, chosen_lang),
        }

        if format_hint:
            slots["output_format"] = format_hint
        if context:
            slots["context"] = _escape_slot(context)

        if mode == "lite":
            # 只保留 task + output_format（其他走預設）
            lite_slots = {"task": slots["task"]}
            if "output_format" in slots:
                lite_slots["output_format"] = slots["output_format"]
            return _render_lite(chosen_lang, lite_slots)

        return render_skeleton(chosen_lang, slots)


def _render_lite(lang: str, slots: Dict[str, str]) -> str:
    """精簡兩段式：任務 + 輸出格式。"""
    if lang == "en":
        task_h, fmt_h = "Task", "Output Format"
        unspec = "(unspecified)"
    else:
        task_h, fmt_h = "任務 (Task)", "輸出格式 (Output Format)"
        unspec = "（未指定）"

    return (
        f"## {task_h}\n{slots.get('task', unspec)}\n\n"
        f"## {fmt_h}\n{slots.get('output_format', unspec)}\n"
    )
