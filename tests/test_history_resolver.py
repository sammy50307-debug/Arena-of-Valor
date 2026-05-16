from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from analyzer.history import HistoryResolver


def _history_date(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")


def _history_iso_date(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _write_archive(root: Path, days_ago: int, payload: dict) -> None:
    path = root / f"analysis_{_history_date(days_ago)}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_resolve_trends_without_archives_returns_fallback(tmp_path: Path):
    resolver = HistoryResolver(data_dir=tmp_path)
    today = {"total_posts": 12}

    result = resolver.resolve_trends(today, showcase=False)

    assert result["overall"]["volume_pct"] == 0.0
    assert result["overall"]["avg_baseline"] == 12
    assert result["weekly_vol_pulse"]["volumes"] == [12]
    assert len(result["weekly_vol_pulse"]["labels"]) == 1
    assert result["alerts"] == []
    assert result["diagnostics"]["status"] == "degraded"
    assert result["diagnostics"]["source_dates"] == []
    assert len(result["diagnostics"]["missing_dates"]) == resolver.history_days


def test_resolve_trends_with_archives_computes_delta(tmp_path: Path):
    resolver = HistoryResolver(data_dir=tmp_path)
    _write_archive(
        tmp_path,
        days_ago=1,
        payload={
            "total_posts": 10,
            "hero_focus": {"name": "芽芽", "sentiment_score": 0.4},
        },
    )
    _write_archive(
        tmp_path,
        days_ago=2,
        payload={
            "total_mention_count": 30,  # 舊 schema，驗證向下相容
            "hero_focus": {"name": "芽芽", "sentiment_score": 0.6},
        },
    )
    today = {
        "total_posts": 20,
        "hero_focus": {"name": "芽芽", "sentiment_score": 0.7},
        "sentiment_distribution": {"positive": 3, "neutral": 2, "negative": 1},
    }

    result = resolver.resolve_trends(today, showcase=False)

    assert result["overall"]["avg_baseline"] == 20.0
    assert result["overall"]["volume_pct"] == 0.0
    assert "芽芽" in result["heroes"]
    assert result["heroes"]["芽芽"]["sentiment_delta"] == 20.0
    assert result["weekly_vol_pulse"]["volumes"][-1] == 20
    assert len(result["weekly_vol_pulse"]["volumes"]) == 3
    assert result["diagnostics"]["status"] == "partial"
    assert _history_iso_date(1) in result["diagnostics"]["source_dates"]
    assert _history_iso_date(2) in result["diagnostics"]["source_dates"]
    assert len(result["diagnostics"]["missing_dates"]) == resolver.history_days - 2


def test_resolve_trends_skips_bad_archive_json(tmp_path: Path):
    resolver = HistoryResolver(data_dir=tmp_path)
    bad_path = tmp_path / f"analysis_{_history_date(1)}.json"
    bad_path.write_text("{bad json", encoding="utf-8")
    today = {"total_posts": 5}

    result = resolver.resolve_trends(today, showcase=False)

    assert result["overall"]["avg_baseline"] == 5
    assert result["weekly_vol_pulse"]["volumes"] == [5]
    assert _history_iso_date(1) in result["diagnostics"]["missing_dates"]


def test_resolve_trends_showcase_mode_returns_weekly_series(tmp_path: Path):
    resolver = HistoryResolver(data_dir=tmp_path)
    today = {"total_posts": 99}

    result = resolver.resolve_trends(today, showcase=True)

    assert len(result["weekly_vol_pulse"]["volumes"]) == 7
    assert len(result["weekly_vol_pulse"]["labels"]) == 7
    assert "overall" in result
    assert "heroes" in result
    assert result["diagnostics"]["status"] == "showcase"
