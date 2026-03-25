"""
Telegram Bot ?¨æ’­æ¨¡ç???
ä½¿ç”¨ python-telegram-bot å¥—ä»¶ï¼Œå?æ¯æ—¥è¼¿æ??˜è?
ä»?Markdown ?¼å??¨é€åˆ°?‡å???Chat ID??"""

import logging
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode

import config

logger = logging.getLogger(__name__)


class TelegramBotNotifier:
    """?é? Telegram Bot API ?¨æ’­è¨Šæ¯??""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.logger = logging.getLogger(f"{__name__}.TelegramBotNotifier")

    async def send_daily_report(self, daily_summary: dict) -> bool:
        """
        å°‡æ??¥æ?è¦ä»¥ Markdown ?¼å??¨é€åˆ° Telegram??
        Args:
            daily_summary: æ¯æ—¥å½™ç¸½?±å? dict

        Returns:
            ?¯å¦?¨æ’­?å?
        """
        if not self.bot_token or not self.chat_id:
            self.logger.error(
                "Telegram Bot Token ??Chat ID ?ªè¨­å®šï??¡æ??¨æ’­??
            )
            return False

        message = self._build_message(daily_summary)

        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
            )
            self.logger.info("Telegram ?¨æ’­?å? ??)
            return True

        except Exception as e:
            self.logger.error(f"Telegram ?¨æ’­å¤±æ?: {e}")
            # ?—è©¦ä¸å¸¶ Markdown ?¼å??é€ï??¿å??¼å?è§??å¤±æ?ï¼?            try:
                bot = Bot(token=self.bot_token)
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=self._build_plain_message(daily_summary),
                )
                self.logger.info("Telegram ?¨æ’­?å?ï¼ˆç??‡å??é€€ï¼???)
                return True
            except Exception as e2:
                self.logger.error(f"Telegram ç´”æ?å­—æ¨?­ä?å¤±æ?: {e2}")
                return False

    def _build_message(self, summary: dict) -> str:
        """çµ„å»º Markdown ?¼å??„æ¨?­è??¯ã€?""
        date = summary.get("date", "N/A")
        overview = summary.get("overview", "?¡è???)
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        total = pos + neg + neu

        lines = [
            "?® *?³èªªå°æ±º æ¯æ—¥è¼¿æ??±å?*",
            f"?? {date}",
            "",
            f"?? *ç¸½è²¼??* {total}",
            f"?? æ­?¢: {pos}  |  ?? è² é¢: {neg}  |  ?? ä¸­æ€? {neu}",
            "",
            "?â??â??â??â??â??â??â??â??â?",
            "",
            f"?? *æ¦‚è¿°*",
            overview[:300],
        ]

        # ?±é?è©±é?
        hot_topics = summary.get("hot_topics", [])[:5]
        if hot_topics:
            lines.append("")
            lines.append("?”¥ *?±é?è©±é?*")
            for i, topic in enumerate(hot_topics, 1):
                name = topic.get("topic", "N/A")
                sent = topic.get("sentiment", "neutral")
                emoji = {"positive": "?Ÿ¢", "negative": "?”´", "neutral": "?Ÿ¡"}.get(
                    sent, "??
                )
                lines.append(f"  {i}. {emoji} {name}")

        # æ´»å??µæ¸¬
        events = summary.get("detected_events", [])[:5]
        if events:
            lines.append("")
            lines.append("?“¢ *?µæ¸¬?°ç?æ´»å?/äº‹ä»¶*")
            for event in events:
                lines.append(
                    f"  ??{event.get('name', 'N/A')} ({event.get('type', '')})"
                )

        # å¹³å°?¸æ?
        platform = summary.get("platform_breakdown", {})
        lines.append("")
        lines.append("?“± *?„å¹³?°æ•¸??")
        for p_name, p_data in platform.items():
            icon = {"instagram": "?“¸", "threads": "?§µ", "facebook": "?‘¤"}.get(
                p_name, "??"
            )
            lines.append(
                f"  {icon} {p_name}: {p_data.get('post_count', 0)} ç¯?"
                f"(?…ç?: {p_data.get('avg_sentiment', 0):.2f})"
            )

        # è­¦è?
        alerts = summary.get("alerts", [])
        if alerts:
            lines.append("")
            lines.append("?š¨ *?è?è­¦è?*")
            for alert in alerts:
                lines.append(f"  ? ï? {alert}")

        # å»ºè­°
        recommendation = summary.get("recommendation", "")
        if recommendation:
            lines.append("")
            lines.append(f"?’¡ *å»ºè­°:* {recommendation[:200]}")

        # ç²¾é¸?…å ±ä¾†æ?
        top_links = summary.get("top_links")
        if top_links:
            lines.append("")
            lines.append("?? *ç²¾é¸?…å ±ä¾†æ?*")
            for link in top_links:
                # ?ºä??¿å? Telegram markdown è§???¯èª¤ï¼Œæ? title ?¹æ?ç¬¦è?æ¿¾æ?
                safe_title = link['title'].replace('[', '').replace(']', '').replace('*', '').replace('_', '')
                lines.append(f"??[{link['platform']}] [{safe_title}]({link['url']})")

        lines.append("")
        lines.append("?â??â??â??â??â??â??â??â??â?")
        
        # å®Œæ•´ç¶²é??±å????
        report_url = summary.get("report_url")
        if report_url:
            lines.append(f"?? [*é»æ??¥ç?ä»Šæ—¥å®Œæ•´?–è¡¨ç¶²é??±å?*]({report_url})")
            lines.append("?â??â??â??â??â??â??â??â??â?")
            
        lines.append("_??AoV è¼¿æ???¸¬ç³»çµ±?ªå??Ÿæ?_")

        return "\n".join(lines)

    def _build_plain_message(self, summary: dict) -> str:
        """ç´”æ?å­—ç??¬ï?Markdown è§??å¤±æ??‚ç??é€€ï¼‰ã€?""
        date = summary.get("date", "N/A")
        overview = summary.get("overview", "?¡è???)
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)

        return (
            f"?® ?³èªªå°æ±º æ¯æ—¥è¼¿æ??±å?\n"
            f"?? {date}\n\n"
            f"?? æ­?¢: {pos} | è² é¢: {neg} | ä¸­æ€? {neu}\n\n"
            f"?? æ¦‚è¿°: {overview[:300]}\n\n"
            f"????AoV è¼¿æ???¸¬ç³»çµ±?ªå??Ÿæ?"
        )


# ?€?€ ?¯ç›´?¥åŸ·è¡Œç??¨ç?æ¸¬è©¦ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test():
        notifier = TelegramBotNotifier()
        test_summary = {
            "date": "2026-03-18",
            "overview": "?™æ˜¯ä¸€æ¢æ¸¬è©¦è??¯ï?ç¢ºè? Telegram ?¨æ’­?Ÿèƒ½æ­?¸¸?‹ä???,
            "sentiment_distribution": {"positive": 10, "negative": 3, "neutral": 7},
            "hot_topics": [{"topic": "æ¸¬è©¦è©±é?", "sentiment": "positive"}],
            "detected_events": [],
            "platform_breakdown": {
                "instagram": {"post_count": 5, "avg_sentiment": 0.7},
                "threads": {"post_count": 8, "avg_sentiment": 0.6},
                "facebook": {"post_count": 7, "avg_sentiment": 0.5},
            },
            "alerts": [],
            "recommendation": "ç³»çµ±æ¸¬è©¦ä¸?,
        }
        success = await notifier.send_daily_report(test_summary)
        print(f"?¨æ’­æ¸¬è©¦çµæ?: {'?å?' if success else 'å¤±æ?'}")

    asyncio.run(test())
