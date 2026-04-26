"""意圖抽取（Phase 62 S2 抽取核心）。

純規則式：對輸入文字依語言查 keyword_dict.json，抽出三類關鍵訊號：
- task_verb：第一個出現的動詞（決定整段任務的主動作）
- constraints：所有命中的限制詞（用 list 保留多重約束）
- format_hint：第一個出現的格式詞（決定輸出格式建議）

策略：先抽 multi-char 多字詞（避免 "查詢" 被 "查" 提前命中），
再抽 single-char 動詞 / 短詞。命中時記錄出現位置以保排序。
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .lang_detector import detect_lang

_DICT_PATH = Path(__file__).resolve().parent.parent / "resources" / "keyword_dict.json"
_DICT_CACHE: Optional[dict] = None
_DICT_LOCK = threading.Lock()


def _load_dict() -> dict:
    global _DICT_CACHE
    if _DICT_CACHE is None:
        with _DICT_LOCK:
            if _DICT_CACHE is None:
                _DICT_CACHE = json.loads(_DICT_PATH.read_text(encoding="utf-8"))
    return _DICT_CACHE


def _is_english_word(word: str) -> bool:
    """判斷候選詞是否全為英文字母組合（用於決定是否加上詞邊界防禦）"""
    return bool(re.match(r"^[a-zA-Z\s]+$", word))


def _find_first(text: str, candidates: List[str]) -> Optional[Tuple[int, str]]:
    """於 text 找最早出現的 candidate；回 (位置, 詞) 或 None。

    候選詞先按長度遞減排序。
    若為純英文詞，將加上 word boundary 防禦 (例：避免 plan 命中 plant)。
    """
    sorted_cands = sorted(set(candidates), key=lambda s: -len(s))
    best: Optional[Tuple[int, str]] = None
    
    for cand in sorted_cands:
        if _is_english_word(cand):
            # 英文詞使用 regex word boundary
            pattern = re.compile(rf"\b{re.escape(cand)}\b", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                idx = match.start()
                if best is None or idx < best[0]:
                    best = (idx, cand)
        else:
            # 中文或混合詞使用一般的子串比對
            idx = text.lower().find(cand.lower())
            if idx != -1:
                if best is None or idx < best[0]:
                    best = (idx, cand)
    return best


def _find_all(text: str, candidates: List[str]) -> List[str]:
    """於 text 找所有命中 candidate（去重，按出現順序）。"""
    sorted_cands = sorted(set(candidates), key=lambda s: -len(s))
    hits: List[Tuple[int, str]] = []
    seen = set()
    
    for cand in sorted_cands:
        if cand in seen:
            continue
            
        if _is_english_word(cand):
            pattern = re.compile(rf"\b{re.escape(cand)}\b", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                hits.append((match.start(), cand))
                seen.add(cand)
        else:
            idx = text.lower().find(cand.lower())
            if idx != -1:
                hits.append((idx, cand))
                seen.add(cand)
                
    hits.sort(key=lambda x: x[0])
    return [w for _, w in hits]


def extract_task(text: str, lang: Optional[str] = None) -> Optional[str]:
    """抽第一個任務動詞。沒命中回 None。"""
    if not text:
        return None
    lang = lang or detect_lang(text)
    if lang not in ("zh", "en"):
        lang = "zh"
    verbs = _load_dict()[lang]["task_verbs"]
    hit = _find_first(text, verbs)
    return hit[1] if hit else None


def extract_constraints(text: str, lang: Optional[str] = None) -> List[str]:
    """抽所有限制詞。沒命中回空 list。"""
    if not text:
        return []
    lang = lang or detect_lang(text)
    if lang not in ("zh", "en"):
        lang = "zh"
    cons = _load_dict()[lang]["constraints"]
    return _find_all(text, cons)


def extract_format(text: str, lang: Optional[str] = None) -> List[str]:
    """抽所有格式詞。改為回傳 list 解決 R9 單選遺漏。沒命中回空 list。"""
    if not text:
        return []
    lang = lang or detect_lang(text)
    if lang not in ("zh", "en"):
        lang = "zh"
    fmts = _load_dict()[lang]["format_hints"]
    return _find_all(text, fmts)


def extract_all(text: str, lang: Optional[str] = None) -> Dict[str, object]:
    """一次抽三類，回 dict：

    {
      "lang": "zh" | "en",
      "task_verb": str | None,
      "constraints": [str, ...],
      "format_hint": [str, ...],
    }
    """
    lang = lang or detect_lang(text)
    if lang not in ("zh", "en"):
        lang = "zh"
    return {
        "lang": lang,
        "task_verb": extract_task(text, lang),
        "constraints": extract_constraints(text, lang),
        "format_hint": extract_format(text, lang),
    }
