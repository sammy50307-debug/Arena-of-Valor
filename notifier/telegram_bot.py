"""
Telegram Bot 推播模組。

使用 python-telegram-bot 套件，將每日輿情摘要
以 Markdown 格式推送到指定的 Chat ID。
"""

import logging
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode

import config

logger = logging.getLogger(__name__)


class TelegramBotNotifier:
    """透過 Telegram Bot API 推播訊息。"""

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
        將每日摘要以 Markdown 格式推送到 Telegram。

        Args:
            daily_summary: 每日彙總報告 dict

        Returns:
            是否推播成功
        """
        if not self.bot_token or not self.chat_id:
            self.logger.error(
                "Telegram Bot Token 或 Chat ID 未設定，無法推播。"
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
            self.logger.info("Telegram 推播成功 ✅")
            return True

        except Exception as e:
            self.logger.error(f"Telegram 推播失敗: {e}")
            # 嘗試不帶 Markdown 格式重送（避免格式解析失敗）
            try:
                bot = Bot(token=self.bot_token)
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=self._build_plain_message(daily_summary),
                )
                self.logger.info("Telegram 推播成功（純文字回退） ✅")
                return True
            except Exception as e2:
                self.logger.error(f"Telegram 純文字推播也失敗: {e2}")
                return False

    def _build_message(self, summary: dict) -> str:
        """組建 Markdown 格式的推播訊息。"""
        date = summary.get("date", "N/A")
        overview = summary.get("overview", "無資料")
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        total = pos + neg + neu

        lines = [
            "🎮 *傳說對決 每日輿情報告*",
            f"📅 {date}",
            "",
            f"📊 *總貼文:* {total}",
            f"👍 正面: {pos}  |  👎 負面: {neg}  |  😐 中性: {neu}",
            "",
            "━━━━━━━━━━━━━━━━━━",
            "",
            f"📝 *概述*",
            overview[:300],
        ]

        # 熱門話題
        hot_topics = summary.get("hot_topics", [])[:5]
        if hot_topics:
            lines.append("")
            lines.append("🔥 *熱門話題*")
            for i, topic in enumerate(hot_topics, 1):
                name = topic.get("topic", "N/A")
                sent = topic.get("sentiment", "neutral")
                emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(
                    sent, "⚪"
                )
                lines.append(f"  {i}. {emoji} {name}")

        # 活動偵測
        events = summary.get("detected_events", [])[:5]
        if events:
            lines.append("")
            lines.append("📢 *偵測到的活動/事件*")
            for event in events:
                lines.append(
                    f"  • {event.get('name', 'N/A')} ({event.get('type', '')})"
                )

        # 平台數據
        platform = summary.get("platform_breakdown", {})
        lines.append("")
        lines.append("📱 *各平台數據*")
        for p_name, p_data in platform.items():
            icon = {"instagram": "📸", "threads": "🧵", "facebook": "👤"}.get(
                p_name, "📌"
            )
            lines.append(
                f"  {icon} {p_name}: {p_data.get('post_count', 0)} 篇 "
                f"(情緒: {p_data.get('avg_sentiment', 0):.2f})"
            )

        # 警訊
        alerts = summary.get("alerts", [])
        if alerts:
            lines.append("")
            lines.append("🚨 *重要警訊*")
            for alert in alerts:
                lines.append(f"  ⚠️ {alert}")

        # 建議
        recommendation = summary.get("recommendation", "")
        if recommendation:
            lines.append("")
            lines.append(f"💡 *建議:* {recommendation[:200]}")

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("_由 AoV 輿情監測系統自動生成_")

        return "\n".join(lines)

    def _build_plain_message(self, summary: dict) -> str:
        """純文字版本（Markdown 解析失敗時的回退）。"""
        date = summary.get("date", "N/A")
        overview = summary.get("overview", "無資料")
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)

        return (
            f"🎮 傳說對決 每日輿情報告\n"
            f"📅 {date}\n\n"
            f"📊 正面: {pos} | 負面: {neg} | 中性: {neu}\n\n"
            f"📝 概述: {overview[:300]}\n\n"
            f"— 由 AoV 輿情監測系統自動生成"
        )


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test():
        notifier = TelegramBotNotifier()
        test_summary = {
            "date": "2026-03-18",
            "overview": "這是一條測試訊息，確認 Telegram 推播功能正常運作。",
            "sentiment_distribution": {"positive": 10, "negative": 3, "neutral": 7},
            "hot_topics": [{"topic": "測試話題", "sentiment": "positive"}],
            "detected_events": [],
            "platform_breakdown": {
                "instagram": {"post_count": 5, "avg_sentiment": 0.7},
                "threads": {"post_count": 8, "avg_sentiment": 0.6},
                "facebook": {"post_count": 7, "avg_sentiment": 0.5},
            },
            "alerts": [],
            "recommendation": "系統測試中",
        }
        success = await notifier.send_daily_report(test_summary)
        print(f"推播測試結果: {'成功' if success else '失敗'}")

    asyncio.run(test())
