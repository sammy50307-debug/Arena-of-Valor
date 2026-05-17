from __future__ import annotations

from pathlib import Path

import config
from reporter.generator import ReportGenerator


def test_report_escapes_post_text_and_blocks_dangerous_urls(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(config, "ENABLE_TOP5_NEWS", False, raising=False)

    payload = '"><script>alert("P83XSS")</script>'
    summary = {
        "date": "2026-05-17",
        "overview": payload,
        "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 1},
        "platform_breakdown": {},
        "hot_topics": [],
        "detected_events": [],
        "recommendation": payload,
        "hero_focus": {
            "name": "芽芽",
            "summary": payload,
            "sentiment_score": 0.5,
            "top_comments": [payload],
        },
        "_meta": {"mode": "production"},
    }
    analyzed_posts = [
        {
            "post": {
                "platform": "PTT",
                "author": "tester",
                "url": "javascript:alert('P83URL')",
                "title": payload,
                "content": payload,
                "timestamp": "2026-05-17 00:00:00",
                "region": "TW",
            },
            "analysis": {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "summary": payload,
                "relevance_score": 0.5,
            },
        }
    ]

    out = ReportGenerator().generate(summary, analyzed_posts, output_dir=tmp_path, promote=False)
    html = out.read_text(encoding="utf-8")

    assert payload not in html
    assert "&lt;script&gt;alert" in html
    assert "javascript:alert" not in html
    assert 'href="#"' in html
