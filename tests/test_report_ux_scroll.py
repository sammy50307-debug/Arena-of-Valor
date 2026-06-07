from __future__ import annotations

from pathlib import Path
from reporter.generator import ReportGenerator

def test_report_feed_container_scroll(tmp_path: Path):
    # 用極簡的 daily_summary 和 analyzed_posts 跑 generator
    daily_summary = {
        "date": "2026-06-07",
        "overview": "這是今日輿情分析概述",
        "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
        "hero_focus": {
            "name": "芽芽",
            "summary": "今日無特定焦點分析",
            "sentiment_score": 0.5,
            "top_comments": []
        },
        "wordcloud": {
            "positive": ["加強"],
            "negative": []
        },
        "real_hot_topics": [],
        "topic_to_posts": {},
        "dynamic_alerts": [],
        "overflow_alerts": [],
        "_meta": {
            "mode": "production",
            "quality_tier": "production_full",
            "analysis_source": "llm",
            "llm_coverage": "100%",
            "cache_hit": 1,
            "total_calls": 1,
            "llm_calls": 1
        }
    }
    analyzed_posts = [
        {
            "post": {
                "title": "測試最新動態標題",
                "content": "這是測試最新動態內容",
                "published_date": "2026-06-07",
                "url": "https://www.dcard.tw/f/garena_aov/p/123"
            },
            "analysis": {
                "summary": "玩家討論測試最新動態",
                "sentiment_score": 0.8
            }
        }
    ]

    generator = ReportGenerator()
    # 產出報告至暫存路徑，不 promote (避免動到 index.html)
    output_path = generator.generate(
        daily_summary=daily_summary,
        analyzed_posts=analyzed_posts,
        output_dir=tmp_path,
        promote=False,
    )

    assert output_path.exists()
    html_content = output_path.read_text(encoding="utf-8")

    # 驗證生成的 HTML 中 .feed-container 包含 max-height 和 overflow-y 樣式
    assert ".feed-container {" in html_content
    # 搜尋樣式，必須是 max-height: 70vh; 與 overflow-y: auto;
    # 為了避免空白字元影響，可以用 strip 空白或正則，但我們是 hardcoded CSS，直接比對即可
    assert "max-height: 70vh;" in html_content
    assert "overflow-y: auto;" in html_content
