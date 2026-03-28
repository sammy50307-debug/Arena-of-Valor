"""
Line Messaging API 推播模組。

使用 LINE Messaging API 的 Push Message 功能，
將每日輿情摘要以 Flex Message 格式推送給指定使用者。
"""

import json
import logging
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)


class LineBotNotifier:
    """透過 LINE Messaging API 推播訊息。"""

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
        將每日摘要以 Flex Message 推送到 LINE。

        Args:
            daily_summary: 每日彙總報告 dict

        Returns:
            是否推播成功
        """
        if not self.token or not self.user_id:
            self.logger.error(
                "LINE Channel Access Token 或 User ID 未設定，無法推播。"
            )
            return False

        # 採用使用者要求的「標題 + 快速連結」格式
        title = daily_summary.get("title", "傳說對決 每日情報戰報")
        report_url = daily_summary.get("report_url", config.GITHUB_PAGES_URL)
        
        message_text = (
            f"📢 {title}\n"
            f"🔗 旗艦網頁報告：{report_url}"
        )

        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message_text
                }
            ],
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
                    self.logger.info("LINE 推播成功 ✅")
                    return True
                else:
                    self.logger.error(
                        f"LINE 推播失敗: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"LINE 推播發生例外: {e}")
            return False

    def _build_flex_message(self, summary: dict) -> dict:
        """組建 LINE Flex Message 格式的每日摘要。"""
        date = summary.get("date", "N/A")
        overview = summary.get("overview", "無資料")
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        total = pos + neg + neu

        # 熱門話題（取前 3 個）
        hot_topics = summary.get("hot_topics", [])[:3]
        topic_texts = []
        for t in hot_topics:
            topic_texts.append(f"• {t.get('topic', 'N/A')} ({t.get('sentiment', 'N/A')})")

        # 活動偵測
        events = summary.get("detected_events", [])[:3]
        event_texts = []
        for e in events:
            event_texts.append(f"• {e.get('name', 'N/A')}")

        recommendation = summary.get("recommendation", "")
        alerts = summary.get("alerts", [])

        # 組建 Flex Message body
        body_contents = [
            {
                "type": "text",
                "text": "🎮 傳說對決 每日輿情報告",
                "weight": "bold",
                "size": "lg",
                "color": "#1DB446",
            },
            {
                "type": "text",
                "text": f"📅 {date}",
                "size": "sm",
                "color": "#aaaaaa",
                "margin": "md",
            },
            {"type": "separator", "margin": "lg"},
            # 情緒分布
            {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": f"📊 總貼文: {total}",
                        "size": "sm",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": f"👍 正面: {pos}  👎 負面: {neg}  😐 中性: {neu}",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                    },
                ],
            },
            {"type": "separator", "margin": "lg"},
            # 概述
            {
                "type": "text",
                "text": overview[:200],
                "size": "sm",
                "color": "#555555",
                "wrap": True,
                "margin": "lg",
            },
        ]

        # 熱門話題
        if topic_texts:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": "🔥 熱門話題",
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

        # 活動偵測
        if event_texts:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": "📢 偵測到的活動",
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

        # 警訊
        if alerts:
            body_contents.append({"type": "separator", "margin": "lg"})
            for alert in alerts[:2]:
                body_contents.append(
                    {
                        "type": "text",
                        "text": f"⚠️ {alert}",
                        "size": "sm",
                        "color": "#FF5555",
                        "wrap": True,
                        "margin": "sm",
                    }
                )

        # 建議
        if recommendation:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": f"💡 {recommendation[:150]}",
                    "size": "sm",
                    "color": "#7c3aed",
                    "wrap": True,
                    "margin": "lg",
                }
            )

        # 🌸 英雄焦點 (芽芽專區)
        hero_focus = summary.get("hero_focus")
        if hero_focus and hero_focus.get("summary") and hero_focus.get("summary") != "今日無特定焦點分析":
            body_contents.append({"type": "separator", "margin": "xl"})
            body_contents.append(
                {
                    "type": "text",
                    "text": f"🌸 英雄焦點：{hero_focus.get('name', '芽芽')}",
                    "weight": "bold",
                    "size": "md",
                    "color": "#db2777",
                    "margin": "lg",
                }
            )
            body_contents.append(
                {
                    "type": "text",
                    "text": hero_focus.get("summary", ""),
                    "size": "sm",
                    "color": "#831843",
                    "wrap": True,
                    "margin": "md",
                }
            )
            
            # 如果有推薦的文章連結，放一個按鈕進去
            top_comments = hero_focus.get("top_comments", [])
            if top_comments:
                 body_contents.append(
                    {
                        "type": "text",
                        "text": f"💬 熱議：{top_comments[0][:60]}...",
                        "size": "xs",
                        "color": "#9d174d",
                        "margin": "sm",
                        "style": "italic"
                    }
                )

        # 來源連結按鈕區塊
        top_links = summary.get("top_links")
        if top_links:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append(
                {
                    "type": "text",
                    "text": "🔗 精選情報來源",
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
                            "label": f"查看 {link['platform']} 貼文",
                            "uri": safe_url
                        },
                        "style": "link",
                        "height": "sm",
                        "color": "#0ea5e9"
                    }
                )

        # 完整網頁報告按鈕
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
                        "label": "🌍 查看完整網頁報告",
                        "uri": report_url
                    }
                }
            )

        flex_message = {
            "type": "flex",
            "altText": f"🎮 傳說對決 每日輿情報告 ({date})",
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


# ── 可直接執行的獨立測試 ──────────────────────────────
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test():
        notifier = LineBotNotifier()
        test_summary = {
            "date": "2026-03-18",
            "overview": "這是一條測試訊息，確認 LINE 推播功能正常運作。",
            "sentiment_distribution": {"positive": 10, "negative": 3, "neutral": 7},
            "hot_topics": [{"topic": "測試話題", "sentiment": "positive"}],
            "detected_events": [],
            "alerts": [],
            "recommendation": "系統測試中",
        }
        success = await notifier.send_daily_report(test_summary)
        print(f"推播測試結果: {'成功' if success else '失敗'}")

    asyncio.run(test())
