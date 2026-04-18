"""
Waterfall Search Chain — Skill 包裝入口。

直接代理 scrapers.waterfall_searcher.WaterfallSearcher，
讓 Smart Task Router 能透過 skill_id 呼叫。
"""
import sys
from pathlib import Path

# 確保 project root 在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scrapers.waterfall_searcher import WaterfallSearcher  # noqa: E402

__all__ = ["WaterfallSearcher"]
