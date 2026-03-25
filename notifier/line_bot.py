"""
Line Messaging API ?®Êí≠Ê®°Á???
‰ΩøÁî® LINE Messaging API ??Push Message ?üËÉΩÔº?Â∞áÊ??•Ëºø?ÖÊ?Ë¶Å‰ª• Flex Message ?ºÂ??®ÈÄÅÁµ¶?áÂ?‰ΩøÁî®?Ö„Ä?"""

import json
import logging
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)


class LineBotNotifier:
    """?èÈ? LINE Messaging API ?®Êí≠Ë®äÊÅØ??""

    PUSH_URL = "https://api.line.me/v2/bot/message/push"

    def __init__(
        self,
        channel_access_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.token = channel_access_token or config.LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = user_id or config.LINE_USER_ID
        self.logger = logging.getLogger(f"{__name__}.LineBotNotifier")

    async def send_daily_report(self, daily_summary: dict) -> bool:
        """
        Â∞áÊ??•Ê?Ë¶Å‰ª• Flex Message ?®ÈÄÅÂà∞ LINE??
        Args:
            daily_summary: ÊØèÊó•ÂΩôÁ∏Ω?±Â? dict

        Returns:
            ?ØÂê¶?®Êí≠?êÂ?
        """
        if not self.token or not self.user_id:
            self.logger.error(
                "LINE Channel Access Token ??User ID ?™Ë®≠ÂÆöÔ??°Ê??®Êí≠??
            )
            return False

        flex_message = self._build_flex_message(daily_summary)
        payload = {
            "to": self.user_id,
            "messages": [flex_message],
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.PUSH_URL,
                    headers=headers,
                    json=payload,
                    timeout=10,
                )

                if response.status_code == 200:
                    self.logger.info("LINE ?®Êí≠?êÂ? ??)
                    return True
                else:
                    self.logger.error(
                        f"LINE ?®Êí≠Â§±Ê?: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"LINE ?®Êí≠?ºÁ?‰æãÂ?: {e}")
            return False

    def _build_flex_message(self, summary: dict) -> dict:
        """ÁµÑÂª∫ LINE Flex Message ?ºÂ??ÑÊ??•Ê?Ë¶Å„Ä?""
        date = summary.get("date", "N/A")
        overview = summary.get("overview", "?°Ë???)
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        total = pos + neg + neu

        # ?±È?Ë©±È?ÔºàÂ???3 ?ãÔ?
        hot_topics = summary.get("hot_topics", [])[:3]
        topic_texts = []
        for t in hot_topics:
            topic_texts.append(f"??{t.get('topic', 'N/A')} ({t.get('sentiment', 'N/A')})")

        # Ê¥ªÂ??µÊ∏¨
        events = summary.get("detected_events", [])[:3]
        event_texts = []
        for e in events:
            event_texts.append(f"??{e.get('name', 'N/A')}")

        recommendation = summary.get("recommendation", "")
        alerts = summary.get("alerts", [])

        # ÁµÑÂª∫ Flex Message body
        body_contents = [
            {
                "type": "text",
                "text": "?éÆ ?≥Ë™™Â∞çÊ±∫ ÊØèÊó•ËºøÊ??±Â?",
                "weight": "bold",
                "size": "lg",
                "color": "#1DB446",
            },
            {
                "type": "text",
                "text": f"?? {date}",
                "size": "sm",
                "color": "#aaaaaa",
                "margin": "md",
            },
            {"type": "separator", "margin": "lg"},
            # ?ÖÁ??ÜÂ?
            {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": f"?? Á∏ΩË≤º?? {total}",
                        "size": "sm",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": f"?? Ê≠?ù¢: {pos}  ?? Ë≤†Èù¢: {neg}  ?? ‰∏≠ÊÄ? {neu}",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                    },
                ],
            },
            {"type": "separator", "margin": "lg"},
            # Ê¶ÇËø∞
            {
                "type": "text",
                "text": overview[:200],
                "size": "sm",
                "color": "#555555",
                "wrap": True,
                "margin": "lg",
            },
        ]

        # ?±È?Ë©±È?
        if topic_texts:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": "?î• ?±È?Ë©±È?",
                    "weight": "bold",
                    "size": "sm",
                    "margin": "lg",
                }
            )
            for tt in topic_texts:
                body_contents.append(
                    {
                        "type": "text",
                        "text": tt,
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                    }
                )

        # Ê¥ªÂ??µÊ∏¨
        if event_texts:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": "?ì¢ ?µÊ∏¨?∞Á?Ê¥ªÂ?",
                    "weight": "bold",
                    "size": "sm",
                    "margin": "lg",
                }
            )
            for et in event_texts:
                body_contents.append(
                    {
                        "type": "text",
                        "text": et,
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                    }
                )

        # Ë≠¶Ë?
        if alerts:
            body_contents.append({"type": "separator", "margin": "lg"})
            for alert in alerts[:2]:
                body_contents.append(
                    {
                        "type": "text",
                        "text": f"?†Ô? {alert}",
                        "size": "sm",
                        "color": "#FF5555",
                        "wrap": True,
                        "margin": "sm",
                    }
                )

        # Âª∫Ë≠∞
        if recommendation:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": f"?í° {recommendation[:150]}",
                    "size": "sm",
                    "color": "#7c3aed",
                    "wrap": True,
                    "margin": "lg",
                }
            )

        # ‰æÜÊ?????âÈ??ÄÂ°?        top_links = summary.get("top_links")
        if top_links:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": "?? Á≤æÈÅ∏?ÖÂ†±‰æÜÊ?",
                    "weight": "bold",
                    "size": "sm",
                    "margin": "lg",
                }
            )
            for link in top_links:
                # LINE Flex button uri must be http or https
                safe_url = link["url"] if link["url"].startswith("http") else "https://" + link["url"]
                body_contents.append(
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": f"?•Á? {link['platform']} Ë≤ºÊ?",
                            "uri": safe_url
                        },
                        "style": "link",
                        "height": "sm",
                        "color": "#0ea5e9"
                    }
                )

        # ÂÆåÊï¥Á∂≤È??±Â??âÈ?
        report_url = summary.get("report_url")
        if report_url:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#1DB446",
                    "margin": "lg",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "?? ?•Á?ÂÆåÊï¥Á∂≤È??±Â?",
                        "uri": report_url
                    }
                }
            )

        flex_message = {
            "type": "flex",
            "altText": f"?éÆ ?≥Ë™™Â∞çÊ±∫ ÊØèÊó•ËºøÊ??±Â? ({date})",
            "contents": {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": body_contents,
                },
            },
        }

        return flex_message


# ?Ä?Ä ?ØÁõ¥?•Âü∑Ë°åÁ??®Á?Ê∏¨Ë©¶ ?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test():
        notifier = LineBotNotifier()
        test_summary = {
            "date": "2026-03-18",
            "overview": "?ôÊòØ‰∏ÄÊ¢ùÊ∏¨Ë©¶Ë??ØÔ?Á¢∫Ë? LINE ?®Êí≠?üËÉΩÊ≠?∏∏?ã‰???,
            "sentiment_distribution": {"positive": 10, "negative": 3, "neutral": 7},
            "hot_topics": [{"topic": "Ê∏¨Ë©¶Ë©±È?", "sentiment": "positive"}],
            "detected_events": [],
            "alerts": [],
            "recommendation": "Á≥ªÁµ±Ê∏¨Ë©¶‰∏?,
        }
        success = await notifier.send_daily_report(test_summary)
        print(f"?®Êí≠Ê∏¨Ë©¶ÁµêÊ?: {'?êÂ?' if success else 'Â§±Ê?'}")

    asyncio.run(test())
