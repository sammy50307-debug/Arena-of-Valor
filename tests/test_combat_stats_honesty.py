import pytest
from pathlib import Path
import json
import yaml
from dataclasses import asdict
from datetime import datetime

from scrapers.hero_stats import HeroStatsScraper, HeroCombatStats
from analyzer.history import HistoryResolver
from reporter.generator import ReportGenerator
import config

def test_no_hardcoded_fake_stats_in_source():
    """1. 確保 hero_stats.py 原始碼中無寫死的 52.8, 12.5, 45.2 假數據"""
    source_file = Path(config.BASE_DIR) / "scrapers" / "hero_stats.py"
    content = source_file.read_text(encoding="utf-8")
    assert "52.8" not in content
    assert "12.5" not in content
    assert "45.2" not in content

@pytest.mark.asyncio
async def test_loader_reads_valid_yaml(tmp_path, monkeypatch):
    """2. loader 讀正常 yaml → 回正確真值 + data_source=manual_yaml"""
    temp_yaml = tmp_path / "temp_stats.yaml"
    yaml_data = {
        "updated_date": "2026-06-07",
        "source": "測試戰績數據",
        "heroes": {
            "芽芽": {
                "tier": "T1",
                "win_rate": 51.2,
                "pick_rate": 13.41,
                "ban_rate": 36.32
            }
        }
    }
    with open(temp_yaml, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
        
    monkeypatch.setattr(config, "HERO_COMBAT_STATS_PATH", temp_yaml)
    monkeypatch.setattr(config, "HERO_WATCHLIST", ["芽芽"])
    
    scraper = HeroStatsScraper()
    res = await scraper.fetch_watchlist_stats()
    
    assert "芽芽" in res
    stats = res["芽芽"]
    assert stats.win_rate == 51.2
    assert stats.pick_rate == 13.41
    assert stats.ban_rate == 36.32
    assert stats.data_source == "manual_yaml"
    assert stats.update_time == "2026-06-07"
    assert stats.tier == "T1"

@pytest.mark.asyncio
async def test_loader_handles_errors_gracefully(tmp_path, monkeypatch):
    """3. loader 遇缺檔/缺英雄/壞 yaml → 回空 dict（不 crash）"""
    # case a: 缺檔
    monkeypatch.setattr(config, "HERO_COMBAT_STATS_PATH", tmp_path / "non_existent.yaml")
    scraper = HeroStatsScraper()
    res = await scraper.fetch_watchlist_stats()
    assert res == {}
    
    # case b: 壞 yaml
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("{bad yaml", encoding="utf-8")
    monkeypatch.setattr(config, "HERO_COMBAT_STATS_PATH", bad_yaml)
    res = await scraper.fetch_watchlist_stats()
    assert res == {}
    
    # case c: 缺英雄
    empty_yaml = tmp_path / "empty.yaml"
    empty_yaml.write_text("updated_date: '2026-06-07'\nheroes: {}\n", encoding="utf-8")
    monkeypatch.setattr(config, "HERO_COMBAT_STATS_PATH", empty_yaml)
    monkeypatch.setattr(config, "HERO_WATCHLIST", ["芽芽"])
    res = await scraper.fetch_watchlist_stats()
    assert res == {}

def test_template_renders_empty_state_when_no_stats(tmp_path):
    """4. 空 combat_stats → 模板渲染空態「暫無可靠來源」"""
    generator = ReportGenerator()
    daily_summary = {
        "date": "2026-06-07",
        "overview": "測試空態",
        "combat_stats": {},
        "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
    }
    
    report_file = generator.generate(
        daily_summary, 
        analyzed_posts=[], 
        output_dir=tmp_path, 
        promote=False
    )
    html_content = report_file.read_text(encoding="utf-8")
    assert "戰績數據暫無可靠來源" in html_content
    assert "WIN RATE" not in html_content

def test_template_renders_stale_warning(tmp_path, monkeypatch):
    """5. 有資料且 updated_date 超過 30 天 → 顯示過期警示"""
    generator = ReportGenerator()
    monkeypatch.setattr(config, "HERO_STATS_STALE_DAYS", 30)
    
    # case a: 沒過期
    summary_fresh = {
        "date": "2026-06-07",
        "overview": "測試沒過期",
        "combat_stats": {
            "芽芽": {
                "name": "芽芽",
                "win_rate": 51.2,
                "pick_rate": 13.41,
                "ban_rate": 36.32,
                "rank": 1,
                "update_time": "2026-06-07",
                "data_source": "manual_yaml",
                "tier": "T1"
            }
        },
        "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
    }
    
    report_fresh = generator.generate(summary_fresh, [], tmp_path, promote=False)
    content_fresh = report_fresh.read_text(encoding="utf-8")
    assert "真實官方數據・更新於 2026-06-07" in content_fresh
    assert "數據可能過時" not in content_fresh
    assert "熱度 T1" in content_fresh
    
    # case b: 已過期
    summary_stale = {
        "date": "2026-06-07",
        "overview": "測試過期",
        "combat_stats": {
            "芽芽": {
                "name": "芽芽",
                "win_rate": 51.2,
                "pick_rate": 13.41,
                "ban_rate": 36.32,
                "rank": 1,
                "update_time": "2026-05-01",
                "data_source": "manual_yaml"
            }
        },
        "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
    }
    report_stale = generator.generate(summary_stale, [], tmp_path, promote=False)
    content_stale = report_stale.read_text(encoding="utf-8")
    assert "真實官方數據・更新於 2026-05-01" in content_stale
    assert "數據可能過時" in content_stale

def test_template_renders_showcase_badge(tmp_path):
    """6. showcase → 模板顯示「演示數據」標籤"""
    generator = ReportGenerator()
    summary_showcase = {
        "date": "2026-06-07",
        "overview": "測試演示模式",
        "_meta": {"mode": "showcase"},
        "combat_stats": {
            "芽芽": {
                "name": "芽芽",
                "win_rate": 52.8,
                "pick_rate": 18.5,
                "ban_rate": 45.2,
                "rank": 5,
                "update_time": "2026-06-07",
                "data_source": "showcase_demo"
            }
        },
        "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
    }
    
    report_showcase = generator.generate(summary_showcase, [], tmp_path, promote=False)
    content_showcase = report_showcase.read_text(encoding="utf-8")
    assert "演示數據" in content_showcase
    assert "真實官方數據" not in content_showcase

def test_history_win_rate_alerts_only_for_real_data():
    """7. history 勝率預警：manual_yaml 真數據會觸發、showcase_demo/空數據不觸發"""
    resolver = HistoryResolver()
    
    # case a: manual_yaml 且勝率低於 47% (例如 45.0) -> 觸發警報
    today_real = {
        "total_posts": 10,
        "combat_stats": {
            "芽芽": {
                "win_rate": 45.0,
                "data_source": "manual_yaml"
            }
        }
    }
    alerts_real = resolver._detect_alerts(trends={}, today=today_real)
    assert any("勝率異常偏低" in a["label"] for a in alerts_real)
    
    # case b: showcase_demo 即使勝率低於 47% (例如 45.0) -> 不觸發
    today_showcase = {
        "total_posts": 10,
        "combat_stats": {
            "芽芽": {
                "win_rate": 45.0,
                "data_source": "showcase_demo"
            }
        }
    }
    alerts_showcase = resolver._detect_alerts(trends={}, today=today_showcase)
    assert not any("勝率異常偏低" in a["label"] for a in alerts_showcase)
    
    # case c: data_source 為空/none -> 不觸發
    today_empty = {
        "total_posts": 10,
        "combat_stats": {
            "芽芽": {
                "win_rate": 45.0,
                "data_source": "none"
            }
        }
    }
    alerts_empty = resolver._detect_alerts(trends={}, today=today_empty)
    assert not any("勝率異常偏低" in a["label"] for a in alerts_empty)
