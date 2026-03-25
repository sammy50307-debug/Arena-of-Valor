"""
è¦–è¦º?–å ±?Šç??å™¨??
è®€??LLM ?†æ??„æ??¥å?ç¸½ç??œï?æ³¨å…¥ Jinja2 HTML æ¨¡æ¿ï¼??¢å‡º?¯ç›´?¥ç”¨?è¦½?¨é??Ÿç?ç²¾ç?ç¶²é??±å???"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)

# æ¨¡æ¿?®é?
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class ReportGenerator:
    """å°‡æ??¥å??ç??œè??–ç‚º HTML ?±å???""

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
        ?¢å‡º HTML ?±å?æª”æ???
        Args:
            daily_summary: SentimentAnalyzer.generate_daily_summary() ?„è¼¸??            analyzed_posts: ?Ÿå??„è²¼?‡å??å?è¡?(?…å« URL ç­‰è©³ç´°è?è¨?
            output_dir: è¼¸å‡º?®é?ï¼Œé?è¨­ç‚º data/reports/

        Returns:
            ?Ÿæ???HTML æª”æ?è·¯å?
        """
        output_dir = output_dir or config.REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        report_date = daily_summary.get("date", datetime.now().strftime("%Y-%m-%d"))

        # æº–å?æ¨¡æ¿è®Šæ•¸
        template_vars = {
            "date": report_date,
            "total_posts": sum(
                daily_summary.get("sentiment_distribution", {}).values()
            ),
            "overview": daily_summary.get("overview", "?¡è???),
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
            "alerts": daily_summary.get("alerts", []),
            "recommendation": daily_summary.get("recommendation", ""),
            "posts": analyzed_posts,
        }

        # æ¸²æ?æ¨¡æ¿
        template = self.env.get_template("report.html")
        html_content = template.render(**template_vars)

        # å¯«å…¥æª”æ?
        filename = f"aov_report_{report_date}.html"
        output_path = output_dir / filename
        output_path.write_text(html_content, encoding="utf-8")

        self.logger.info(f"?±å?å·²ç??? {output_path}")
        return output_path
