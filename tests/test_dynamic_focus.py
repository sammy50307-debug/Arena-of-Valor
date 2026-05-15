"""
P68 — test_dynamic_focus.py

5 cases:
  1. 無資料（analyzed_posts=[], platform_breakdown={}）→ 至少 1 條保底文案
  2. 僅 D：只有芽芽文章，無 B 頭條、無 E 平台 → 出現芽芽篇數句（首日）
  3. 僅 E：只有平台資料，無 B/D → 出現平台熱度句
  4. 滿三條 + 溢位：B/D/E 全有，AI 回傳 4 句 → main ≤ 3、overflow ≥ 1
  5. AI 失敗 fallback：llm_client.chat 丟例外 → 仍回傳模板句，不空

mock news_history_indexer.load_index 讓測試不依賴磁碟狀態。
"""

import asyncio
from unittest.mock import patch

import pytest

from analyzer.dynamic_focus import (
    _collect_B,
    _collect_D,
    _collect_E,
    _build_template_sentences,
    build_dynamic_alerts,
)

_EMPTY_INDEX = {}


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_post(title: str, relevance: float = 0.8, is_yaya: bool = False):
    return {
        "post": {
            "title": title,
            "content": f"內容：{title}",
            "is_hero_focus": is_yaya,
        },
        "analysis": {
            "relevance_score": relevance,
            "is_hero_focus": is_yaya,
        },
    }


def _summary_with_pb(platform_breakdown: dict) -> dict:
    return {
        "platform_breakdown": platform_breakdown,
        "history_delta": {"alerts": []},
    }


class _FailLLM:
    async def chat(self, **kwargs):
        raise RuntimeError("模擬 AI 失敗")


# ── test 1: 無資料保底 ────────────────────────────────────────────────────────

def test_case1_no_data():
    """無 B/D/E 時，build_dynamic_alerts 補保底一句，不回傳空列表。"""
    with patch("analyzer.news_history_indexer.load_index", return_value=_EMPTY_INDEX):
        result = asyncio.run(
            build_dynamic_alerts(
                summary=_summary_with_pb({}),
                analyzed_posts=[],
                date_str="2026-05-07",
                llm_client=None,
            )
        )
    assert len(result["dynamic_alerts"]) >= 1
    assert "今日" in result["dynamic_alerts"][0]["label"]


# ── test 2: 僅 D ─────────────────────────────────────────────────────────────

def test_case2_only_D():
    """只有芽芽文章（無 title → B 不出）、沒有平台資料；index 空 → 首日。"""
    posts = [
        _make_post("", relevance=0.9, is_yaya=True),
        _make_post("", relevance=0.7, is_yaya=True),
    ]
    with patch("analyzer.news_history_indexer.load_index", return_value=_EMPTY_INDEX):
        B = _collect_B(posts)
        D = _collect_D(posts, date_str="2026-05-07")
        E = _collect_E({})
        sentences = _build_template_sentences(B, D, E)

    assert len(sentences) == 1
    assert "芽芽" in sentences[0]
    assert "2" in sentences[0]
    assert "首日" in sentences[0]


# ── test 3: 僅 E ─────────────────────────────────────────────────────────────

def test_case3_only_E():
    """只有平台資料，無文章；D today=0, yesterday=0 → 不出；只出 E 句。"""
    pb = {
        "facebook": {"post_count": 10, "avg_sentiment": 0.7},
        "ptt": {"post_count": 5, "avg_sentiment": 0.6},
        "dcard": {"post_count": 3, "avg_sentiment": 0.5},
        "instagram": {"post_count": 0, "avg_sentiment": 0.5},
    }
    with patch("analyzer.news_history_indexer.load_index", return_value=_EMPTY_INDEX):
        B = _collect_B([])
        D = _collect_D([], date_str="2026-05-07")
        E = _collect_E({"platform_breakdown": pb})
        sentences = _build_template_sentences(B, D, E)

    assert len(sentences) == 1
    assert "平台熱度" in sentences[0]
    assert "FB" in sentences[0]


# ── test 4: 滿三條 + 溢位 ────────────────────────────────────────────────────

def test_case4_overflow():
    """AI 回傳 4 行時，main ≤ 3，overflow ≥ 1，合計 ≥ 1。"""
    class _LLMFour:
        async def chat(self, system_prompt, user_prompt, **kwargs):
            return "句一\n句二\n句三\n句四"

    posts = [_make_post("芽芽新皮膚登場", relevance=0.95, is_yaya=True)]
    pb = {"facebook": {"post_count": 8}, "dcard": {"post_count": 4}}

    with patch("analyzer.news_history_indexer.load_index", return_value=_EMPTY_INDEX):
        result = asyncio.run(
            build_dynamic_alerts(
                summary=_summary_with_pb(pb),
                analyzed_posts=posts,
                date_str="2026-05-07",
                llm_client=_LLMFour(),
            )
        )
    assert len(result["dynamic_alerts"]) <= 3
    total = len(result["dynamic_alerts"]) + len(result["overflow_alerts"])
    assert total >= 1


# ── test 5: AI 失敗 fallback ─────────────────────────────────────────────────

def test_case5_ai_failure_fallback():
    """AI 丟例外 → 仍回傳模板句（不空），overview 不受影響。"""
    posts = [_make_post("芽芽近況彙整", relevance=0.9, is_yaya=True)]
    pb = {"facebook": {"post_count": 6}}

    with patch("analyzer.news_history_indexer.load_index", return_value=_EMPTY_INDEX):
        result = asyncio.run(
            build_dynamic_alerts(
                summary=_summary_with_pb(pb),
                analyzed_posts=posts,
                date_str="2026-05-07",
                llm_client=_FailLLM(),
            )
        )
    assert len(result["dynamic_alerts"]) >= 1
    for alert in result["dynamic_alerts"]:
        assert isinstance(alert["label"], str)
        assert len(alert["label"]) > 0
