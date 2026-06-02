"""governance_utils.py — P103 共享治理工具函式（從 cross_phase_review + m4 去重合併）.

來源：skills-governance G0_DEEPDIVE_BLUEPRINT §一（三層融合架構）
快照日期：2026-05-31（複製非引用，非 live link to skills-governance）
"""
from __future__ import annotations

import re


def extract_blindspot_entries(text: str) -> list[dict]:
    """Extract B-NNN entries with headline + 通則化 rule from blindspot file text.

    回傳格式：[{"id": "B-NNN", "headline": "...", "rule": "..."}]
    原出處：cross_phase_review._extract_blindspots + m4_track_blindspots.extract_blindspot_rules
    兩函式邏輯完全等價（P103 A2 驗證），合併於此消除重複。
    """
    items: list[dict] = []
    pattern = re.compile(r"### (B-\d+)：(.+?)(?=\n### B-|\n## |$)", re.DOTALL)
    for m in pattern.finditer(text):
        bid = m.group(1)
        body = m.group(2)
        headline = body.strip().splitlines()[0].strip() if body.strip() else ""
        norm_m = re.search(
            r"\*\*通則化\*\*：\s*\n+>\s*(.+?)(?=\n\n|\n\*\*)", body, re.DOTALL
        )
        rule = norm_m.group(1).strip().replace("\n> ", " ") if norm_m else ""
        items.append({"id": bid, "headline": headline, "rule": rule})
    return items
