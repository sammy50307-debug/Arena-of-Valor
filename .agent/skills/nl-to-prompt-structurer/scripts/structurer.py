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

import json
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional

from .intent_extractor import extract_all
from .lang_detector import detect_lang
from .templates import render_skeleton

_ROLE_MAP_PATH = Path(__file__).resolve().parent.parent / "resources" / "role_map.json"
_ROLE_MAP_CACHE: Optional[dict] = None
_ROLE_MAP_LOCK = threading.Lock()

_DEFAULT_ROLE = {"zh": "通用助理", "en": "Generalist Assistant"}


def _load_role_map() -> dict:
    global _ROLE_MAP_CACHE
    if _ROLE_MAP_CACHE is None:
        with _ROLE_MAP_LOCK:
            if _ROLE_MAP_CACHE is None:
                if _ROLE_MAP_PATH.exists():
                    _ROLE_MAP_CACHE = json.loads(_ROLE_MAP_PATH.read_text(encoding="utf-8"))
                else:
                    _ROLE_MAP_CACHE = {"zh": {}, "en": {}}
    return _ROLE_MAP_CACHE


def _infer_role(task_verb: Optional[str], lang: str) -> str:
    role_map = _load_role_map()
    if task_verb and task_verb in role_map.get(lang, {}):
        return role_map[lang][task_verb]
    return _DEFAULT_ROLE.get(lang, _DEFAULT_ROLE["zh"])


def _escape_slot(value: str) -> str:
    """跳脫 slot 內會破壞五段式結構的元字元（行首 `#` heading、`>` blockquote、```` ` 圍欄）。
    
    保留 caller 原始輸入彈性，防止被 Markdown 渲染當作結構破壞。
    """
    if not value:
        return value
    # 防禦 `#`
    value = re.sub(r"(^|\n)(#+)\s", lambda m: f"{m.group(1)}\\{m.group(2)} ", value)
    # 防禦 `>` (blockquote)
    value = re.sub(r"(^|\n)>\s", lambda m: f"{m.group(1)}\\> ", value)
    # 防禦 ```` ` (code fences)
    value = re.sub(r"(^|\n)(```+)", lambda m: f"{m.group(1)}\\{m.group(2)}", value)
    return value


def _dedupe_overlap(items: List[str]) -> List[str]:
    """若 A 是 B 的 substring，刪短的 A，保長的 B（順序保留長者首見位置）。"""
    if not items:
        return []
    keep: List[str] = []
    for x in items:
        if any((x in k) and (x != k) for k in keep):
            continue
        keep = [k for k in keep if not ((k in x) and (k != x))]
        keep.append(x)
    return keep


def _format_constraints(items: List[str], lang: str) -> str:
    if not items:
        return "（未指定）" if lang == "zh" else "(unspecified)"
    if len(items) == 1:
        return items[0]  # 若只有 1 條，不加 bullet
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
        format_hint_list = info["format_hint"]  # list returned by updated extractor
        format_hint = " / ".join(format_hint_list) if format_hint_list else None # type: ignore

        chosen_role = role or _infer_role(task_verb, chosen_lang)

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
            return render_skeleton(chosen_lang, slots, sections=["task", "output_format"])

        return render_skeleton(chosen_lang, slots)

