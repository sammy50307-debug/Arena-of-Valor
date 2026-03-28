"""
視覺化報告生成器。

讀取 LLM 分析的每日彙總結果，注入 Jinja2 HTML 模板，
產出可直接用瀏覽器開啟的精美網頁報告。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)

# 模板目錄
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class ReportGenerator:
    """將每日分析結果轉化為 HTML 報告。"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )
        self.logger = logging.getLogger(f"{__name__}.ReportGenerator")

    def generate(
        self,
        daily_summary: dict,
        analyzed_posts: list,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        產出 HTML 報告檔案。

        Args:
            daily_summary: SentimentAnalyzer.generate_daily_summary() 的輸出
            analyzed_posts: 原始的貼文分析列表 (包含 URL 等詳細資訊)
            output_dir: 輸出目錄，預設為 data/reports/

        Returns:
            生成的 HTML 檔案路徑
        """
        output_dir = output_dir or config.REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        report_date = daily_summary.get("date", datetime.now().strftime("%Y-%m-%d"))

        # 準備模板變數
        template_vars = {
            "date": report_date,
            "total_posts": sum(
                daily_summary.get("sentiment_distribution", {}).values()
            ),
            "overview": daily_summary.get("overview", "無資料"),
            "sentiment_distribution": daily_summary.get(
                "sentiment_distribution",
                {"positive": 0, "negative": 0, "neutral": 0},
            ),
            "hot_topics": daily_summary.get("hot_topics", []),
            "detected_events": daily_summary.get("detected_events", []),
            "platform_breakdown": daily_summary.get(
                "platform_breakdown",
                {
                    "instagram": {"post_count": 0, "avg_sentiment": 0},
                    "threads": {"post_count": 0, "avg_sentiment": 0},
                    "facebook": {"post_count": 0, "avg_sentiment": 0},
                },
            ),
            "recommendation": daily_summary.get("recommendation", ""),
            "hero_focus": daily_summary.get("hero_focus", {
                "name": getattr(config, "HERO_FOCUS_NAME", "芽芽"),
                "summary": "今日無特定焦點分析",
                "sentiment_score": 0.5,
                "top_comments": []
            }),
            "hero_focus_posts": [
                p for p in analyzed_posts 
                if (p.get("post", {}).get("is_hero_focus") or p.get("analysis", {}).get("is_hero_focus"))
                and (
                    getattr(config, "HERO_FOCUS_NAME", "芽芽") in p.get("post", {}).get("content", "") or
                    getattr(config, "HERO_FOCUS_NAME", "芽芽") in p.get("analysis", {}).get("summary", "")
                )
            ][:5],
            "posts": analyzed_posts,
        }

        # ── 防空機制：如果 AI 摘要遺失但有抓到文章，手動補齊 ──────────────────
        hp_list = template_vars["hero_focus_posts"]
        if hp_list and (not template_vars["hero_focus"].get("summary") or "今日無特定焦點分析" in template_vars["hero_focus"].get("summary")):
            template_vars["hero_focus"]["summary"] = f"根據今日抓獲的 {len(hp_list)} 篇焦點貼文分析，玩家正針對「{template_vars['hero_focus']['name']}」的新動態進行討論。首篇熱議內容為：{hp_list[0]['analysis'].get('summary', '詳見下方連結' if not hp_list[0]['analysis'].get('summary') else hp_list[0]['analysis'].get('summary'))}"
            template_vars["hero_focus"]["sentiment_score"] = hp_list[0]["analysis"].get("sentiment_score", 0.5)

        # 渲染模板
        template = self.env.get_template("report.html")
        html_content = template.render(**template_vars)

        # 寫入檔案
        filename = f"aov_report_{report_date}.html"
        output_path = output_dir / filename
        output_path.write_text(html_content, encoding="utf-8")

        self.logger.info(f"報告已生成: {output_path}")
        return output_path
