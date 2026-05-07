"""
P68 — 動態今日焦點生成器

當 history_delta.alerts 為空時，從以下三個資料源組裝今日焦點文案：
  B: top5_news 頭條（最高相關度前 3 篇標題）
  D: 芽芽相關文章數今日 vs 昨日（從 news_history_indexer 讀昨日數量）
  E: 平台熱度前三名（platform_breakdown 篇數）

文案組裝策略（解法 B）：模板組句 → Gemini 潤飾成自然中文
條目上限 3 條，超出部分放入 overflow_alerts。
AI 失敗時直接用模板組句（不空）。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# 平台顯示名
_PLATFORM_LABELS = {
    "facebook": "FB",
    "instagram": "IG",
    "threads": "Threads",
    "ptt": "PTT",
    "dcard": "Dcard",
    "youtube": "YouTube",
    "web": "Web",
}


def _collect_B(analyzed_posts: list) -> list[str]:
    """從 analyzed_posts 取最高 relevance_score 前 3 篇頭條。"""
    scored = []
    for entry in analyzed_posts:
        post = entry.get("post", {})
        analysis = entry.get("analysis", {})
        title = post.get("title", "").strip()
        if not title or title == "時間未知":
            continue
        score = analysis.get("relevance_score", 0.0)
        scored.append((score, title))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:3]]


def _collect_D(analyzed_posts: list, hero_focus: str = "芽芽", date_str: Optional[str] = None) -> dict:
    """
    計算今日 hero_focus 相關文章數，並與昨日比較。
    昨日數量從 news_history_indexer 讀取（first_seen == yesterday）。
    回傳 {"today": N, "yesterday": M, "delta": N-M, "has_yesterday": bool}
    """
    try:
        from analyzer import news_history_indexer as _idx
        index = _idx.load_index()
    except Exception:
        index = {}

    today_str = date_str or datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    # 今日：從 analyzed_posts 直接計算（含 hero_focus 的文章）
    today_count = sum(
        1 for entry in analyzed_posts
        if hero_focus in (entry.get("post", {}).get("title", "") or "")
        or entry.get("post", {}).get("is_hero_focus", False)
        or entry.get("analysis", {}).get("is_hero_focus", False)
    )

    # 昨日：從 history_index 找 first_seen == yesterday 且 title 含 hero_focus
    yesterday_entries = [
        meta for meta in index.values()
        if meta.get("first_seen") == yesterday_str
    ]
    yesterday_count = sum(1 for m in yesterday_entries if hero_focus in (m.get("title", "") or ""))
    has_yesterday = bool(yesterday_entries)

    return {
        "today": today_count,
        "yesterday": yesterday_count,
        "delta": today_count - yesterday_count,
        "has_yesterday": has_yesterday,
    }


def _collect_E(summary: dict) -> list[tuple[str, int]]:
    """
    從 platform_breakdown 取篇數前三平台。
    回傳 [(platform_label, count), ...]，只含 count > 0 的平台。
    """
    pb = summary.get("platform_breakdown", {})
    platforms = []
    for key, val in pb.items():
        if isinstance(val, dict):
            count = val.get("post_count", 0)
        else:
            count = 0
        if count > 0:
            label = _PLATFORM_LABELS.get(key, key.upper())
            platforms.append((label, count))
    platforms.sort(key=lambda x: x[1], reverse=True)
    return platforms[:3]


def _build_template_sentences(
    B: list[str],
    D: dict,
    E: list[tuple[str, int]],
    hero_focus: str = "芽芽",
) -> list[str]:
    """
    把 B/D/E 組成模板句子列表（無 AI 潤飾版，最多 3 條）。
    有資料才出、沒資料略過。
    """
    sentences = []

    # B：頭條
    if B:
        top_title = B[0][:30] + ("…" if len(B[0]) > 30 else "")
        sentences.append(f"今日熱議：{top_title}")

    # D：芽芽文章數（today 或 yesterday 任一 > 0 才有意義）
    if D["today"] > 0 or (D["has_yesterday"] and D["yesterday"] > 0):
        count = D["today"]
        delta = D["delta"]
        if not D["has_yesterday"]:
            delta_str = "（首日）"
        elif delta > 0:
            delta_str = f"（較昨日 +{delta}）"
        elif delta < 0:
            delta_str = f"（較昨日 {delta}）"
        else:
            delta_str = "（與昨日持平）"
        sentences.append(f"{hero_focus} 今日相關文章 {count} 篇{delta_str}")

    # E：平台熱度
    if E:
        parts = "、".join(f"{label} {cnt} 篇" for label, cnt in E)
        sentences.append(f"平台熱度：{parts}")

    return sentences[:3]


async def _ai_polish(sentences: list[str], llm_client) -> list[str]:
    """
    呼叫 Gemini 將模板句潤飾為自然中文。
    單次呼叫 ~300 token；失敗直接回傳原句。
    """
    if not sentences or llm_client is None:
        return sentences

    raw = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    system_prompt = (
        "你是 AoV（傳說對決）台服每日戰報的文案編輯。"
        "請把以下幾條機器產生的模板句，改寫成自然流暢的繁體中文簡短一句話，"
        "保留數字和事實，不要加入沒有根據的資訊，不加標題，每條一行。"
    )
    user_prompt = f"原始條目：\n{raw}\n\n請直接輸出改寫後的條目（每條一行，不加編號）："

    try:
        result = await llm_client.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
            temperature=0.5,
        )
        if isinstance(result, str):
            polished = [line.strip() for line in result.strip().splitlines() if line.strip()]
            # 確保筆數不超過原始數量，避免 AI 發散
            return polished[: len(sentences)] or sentences
    except Exception as e:
        logger.warning("dynamic_focus AI 潤飾失敗，使用模板原句：%s", e)

    return sentences


async def build_dynamic_alerts(
    summary: dict,
    analyzed_posts: list,
    hero_focus: str = "芽芽",
    date_str: Optional[str] = None,
    llm_client=None,
) -> dict:
    """
    主入口。回傳 {"dynamic_alerts": [...], "overflow_alerts": [...]}
    每個 alert 為 {"label": "..."}。

    dynamic_alerts：前 3 條（進今日焦點欄）
    overflow_alerts：第 4 條起（進 overview 下方 sub-block，理論上不會出現，因為模板最多 3 句）
    """
    B = _collect_B(analyzed_posts)
    D = _collect_D(analyzed_posts, hero_focus, date_str)
    E = _collect_E(summary)

    logger.info(
        "dynamic_focus: B=%d titles, D=today%d/yest%d/delta%+d, E=%s, n_analyzed=%d",
        len(B), D["today"], D["yesterday"], D["delta"],
        [(lbl, cnt) for lbl, cnt in E],
        len(analyzed_posts),
    )

    sentences = _build_template_sentences(B, D, E, hero_focus)

    if not sentences:
        # 完全無資料 — 最低保底
        sentences = [f"今日 {hero_focus} 台服輿情平穩，暫無異常警報。"]

    polished = await _ai_polish(sentences, llm_client)

    overflow_count = max(0, len(polished) - 3)
    main_alerts = [{"label": s} for s in polished[:3]]
    overflow_alerts = [{"label": s} for s in polished[3:]]

    logger.info(
        "dynamic_focus: n_alerts=%d, overflow=%d",
        len(main_alerts), overflow_count,
    )

    return {"dynamic_alerts": main_alerts, "overflow_alerts": overflow_alerts}
