"""語言偵測（Phase 62 S1 地基）。

策略：以 CJK Unified Ideographs（U+4E00–U+9FFF）+ 常用標點為「中文訊號」，
ASCII letters 為「英文訊號」。CJK 數量 / (CJK + 英文字母) 之比例 ≥ 0.3 視為中文。
短句（< 5 個有效字元）或全空字串：依 R1 預設回 "zh"。
"""

from __future__ import annotations

_CJK_THRESHOLD = 0.3
_SHORT_INPUT_LEN = 5


def _is_cjk(ch: str) -> bool:
    code = ord(ch)
    if 0x4E00 <= code <= 0x9FFF:
        return True
    if 0x3400 <= code <= 0x4DBF:
        return True
    if 0xF900 <= code <= 0xFAFF:
        return True
    return False


def detect_lang(text: str) -> str:
    """偵測文字主要語言。

    回 "zh" 或 "en"。短句 / 空字串預設 "zh"。
    """
    if not text:
        return "zh"

    cjk = 0
    en = 0
    for ch in text:
        if _is_cjk(ch):
            cjk += 1
        elif ch.isascii() and ch.isalpha():
            en += 1

    total = cjk + en
    if total < _SHORT_INPUT_LEN:
        return "zh" if cjk > 0 else ("en" if en >= total and en > 0 else "zh")

    if total == 0:
        return "zh"

    ratio = cjk / total
    return "zh" if ratio >= _CJK_THRESHOLD else "en"
