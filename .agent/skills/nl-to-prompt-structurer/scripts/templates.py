"""五段式 Prompt 模板（Phase 62 S1 地基）。

中英雙語、未填欄位顯示明確 placeholder（不空白），對應計畫書 R2。
"""

from __future__ import annotations

from typing import Dict, Optional

SECTIONS = ("role", "context", "task", "constraints", "output_format")

_HEADERS = {
    "zh": {
        "role": "角色 (Role)",
        "context": "背景 (Context)",
        "task": "任務 (Task)",
        "constraints": "限制 (Constraints)",
        "output_format": "輸出格式 (Output Format)",
    },
    "en": {
        "role": "Role",
        "context": "Context",
        "task": "Task",
        "constraints": "Constraints",
        "output_format": "Output Format",
    },
}

_DEFAULTS = {
    "zh": {
        "role": "通用助理",
        "context": "（未指定）",
        "task": "（未指定）",
        "constraints": "（未指定）",
        "output_format": "（未指定）",
    },
    "en": {
        "role": "Generalist Assistant",
        "context": "(unspecified)",
        "task": "(unspecified)",
        "constraints": "(unspecified)",
        "output_format": "(unspecified)",
    },
}


def render_skeleton(lang: str, slots: Optional[Dict[str, str]] = None) -> str:
    """組出五段式 Markdown。

    lang：'zh' 或 'en'；其他值依 R1 fallback 至 'zh'。
    slots：欲填入的欄位，key 為 SECTIONS 之一；缺欄位用 _DEFAULTS 補。
    """
    if lang not in ("zh", "en"):
        lang = "zh"
    slots = slots or {}

    headers = _HEADERS[lang]
    defaults = _DEFAULTS[lang]

    lines = []
    for sec in SECTIONS:
        value = slots.get(sec)
        if value is None or (isinstance(value, str) and not value.strip()):
            value = defaults[sec]
        lines.append(f"## {headers[sec]}")
        lines.append(value)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
