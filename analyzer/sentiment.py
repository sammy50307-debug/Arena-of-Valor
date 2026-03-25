"""
?…ç??†æ??‡æ´»?•ä?ä»¶è??–ä¸»?è¼¯??
è² è²¬å°?Tavily ?œå??°ç?çµæ??¹æ¬¡?å…¥ Gemini LLM ?†æ?ï¼?ä¸¦ç”¢?ºç?æ§‹å??„æ??¥å?ç¸½å ±?Šã€?"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from scrapers.tavily_searcher import SearchResult
from analyzer.gemini_client import GeminiClient
from analyzer.prompts import (
    SYSTEM_SINGLE_POST,
    USER_SINGLE_POST,
    SYSTEM_DAILY_SUMMARY,
    USER_DAILY_SUMMARY,
)

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    è¼¿æ??†æ??¨ï?å°‡æ?å°‹ç??œé€å…¥ Gemini ?²è??…ç??†æ??‡ä?ä»¶åµæ¸¬ï?
    ?€çµ‚ç”¢?ºæ??¥å?ç¸½å ±?Šã€?    """

    def __init__(self, llm_client: Optional[GeminiClient] = None):
        self.llm = llm_client or GeminiClient()
        self.logger = logging.getLogger(f"{__name__}.SentimentAnalyzer")

    async def analyze_posts(self, search_results: List[SearchResult]) -> List[dict]:
        """
        ?¹æ¬¡?†æ??œå?çµæ??„æ?ç·’è?äº‹ä»¶??
        Args:
            search_results: Tavily ?œé??°ç?çµæ??—è¡¨

        Returns:
            æ¯ç??§å®¹?„å??ç??œå?è¡?        """
        if not search_results:
            self.logger.warning("æ²’æ??œå?çµæ??¯ä»¥?†æ?")
            return []

        self.logger.info(f"?‹å??†æ? {len(search_results)} ç­†ç???..")

        # å»ºæ?æ¯ç?çµæ???user prompt
        user_prompts = []
        for res in search_results:
            content = f"[{res.title}] {res.content}"
            user_prompts.append(
                USER_SINGLE_POST.format(
                    platform=res.platform or "web",
                    author=res.source or "unknown",
                    content=content[:1000],  # ?åˆ¶?·åº¦
                )
            )

        # ?¹æ¬¡?¼å« Gemini (è¨­å?ä½?concurrency ?¿å?è§¸ç™¼?è²»??rate limit)
        results = await self.llm.batch_chat(
            system_prompt=SYSTEM_SINGLE_POST,
            user_prompts=user_prompts,
            json_mode=True,
            concurrency=1,
        )

        # å°‡å??ç??œè??Ÿå?è³‡æ??ˆä½µ
        analyzed = []
        for res, analysis in zip(search_results, results):
            if isinstance(analysis, dict) and "error" not in analysis:
                entry = {
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "content": res.content,
                        "timestamp": getattr(res, "timestamp", getattr(res, "published_date", getattr(res, "date", "?‚é??ªçŸ¥"))),
                    },
                    "analysis": analysis,
                }
                analyzed.append(entry)
            else:
                self.logger.warning(
                    f"?†æ?å¤±æ? ({res.platform} - {res.url}): {analysis}"
                )
                # ä½¿ç”¨?è¨­??                analyzed.append({
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "content": res.content,
                        "timestamp": getattr(res, "timestamp", getattr(res, "published_date", getattr(res, "date", "?‚é??ªçŸ¥"))),
                    },
                    "analysis": {
                        "sentiment": "neutral",
                        "sentiment_score": 0.5,
                        "category": "?¶ä?",
                        "keywords": [],
                        "events": [],
                        "summary": "?†æ?å¤±æ?",
                        "relevance_score": 0.0,
                    },
                })

        self.logger.info(f"å®Œæ? {len(analyzed)} ç­†ç??œå???)
        return analyzed

    async def generate_daily_summary(
        self,
        analyzed_posts: List[dict],
        date: Optional[str] = None,
    ) -> dict:
        """
        ?¹æ??†æ?çµæ??¢å‡ºæ¯æ—¥å½™ç¸½?±å???        """
        if not analyzed_posts:
            return self._empty_summary(date)

        report_date = date or datetime.now().strftime("%Y-%m-%d")

        # å½™æ•´?†æ?çµæ??æ?å­—å½¢å¼ï??å…¥ LLM ?¢å‡ºå½™ç¸½
        analysis_text = self._format_analysis_for_summary(analyzed_posts)

        user_prompt = USER_DAILY_SUMMARY.format(
            date=report_date,
            total_posts=len(analyzed_posts),
            analysis_results=analysis_text,
        )

        try:
            summary = await self.llm.chat(
                system_prompt=SYSTEM_DAILY_SUMMARY,
                user_prompt=user_prompt,
                json_mode=True,
                temperature=0.4,
            )
            if not isinstance(summary, dict):
                raise ValueError(f"Gemini ?å‚³äº†é?å­—å…¸?¼å?: {summary}")
                
            # å°‡ç†±åº¦æ?é«˜ç? 3 ç¯‡è²¼?‡é€???“å‡ºä¾†æ”¾??summary è£¡ï?ä¾?Line/Telegram ?¨æ’­ä½¿ç”¨
            top_posts = sorted(
                [p for p in analyzed_posts if p.get("post", {}).get("url") and p["post"]["url"] != "N/A"],
                key=lambda x: x.get("analysis", {}).get("relevance_score", 0),
                reverse=True
            )[:3]
            
            top_links = []
            for p in top_posts:
                content_preview = p["post"]["content"][:20].replace("\n", " ") + "..."
                top_links.append({
                    "title": content_preview,
                    "url": p["post"]["url"],
                    "platform": p["post"]["platform"]
                })
            summary["top_links"] = top_links
            
            return summary
        except Exception as e:
            self.logger.error(f"æ¯æ—¥?˜è??Ÿæ?å¤±æ?: {e}")
            return self._generate_fallback_summary(analyzed_posts, report_date)

    def _format_analysis_for_summary(self, analyzed_posts: List[dict]) -> str:
        """å°‡å??ç??œæ ¼å¼å???LLM ?¯è??„æ?å­—ã€?""
        lines = []
        for i, entry in enumerate(analyzed_posts, 1):
            post = entry["post"]
            analysis = entry["analysis"]
            lines.append(
                f"[{i}] å¹³å°: {post['platform']} | "
                f"?…ç?: {analysis.get('sentiment', 'N/A')} ({analysis.get('sentiment_score', 'N/A')}) | "
                f"?†é?: {analysis.get('category', 'N/A')} | "
                f"?˜è?: {analysis.get('summary', 'N/A')}"
            )
            events = analysis.get("events", [])
            if events:
                for evt in events:
                    lines.append(
                        f"    ??æ´»å?: {evt.get('name', 'N/A')} ({evt.get('type', 'N/A')})"
                    )
        # å¦‚æ?çµæ?å¤ªå??¯èƒ½è¶…é? token ä¸Šé?ï¼Œæˆª??        full_text = "\n".join(lines)
        if len(full_text) > 10000:
            full_text = full_text[:10000] + "\n... (è³‡æ??å?å·²æˆª??"
        return full_text

    def _generate_fallback_summary(self, analyzed_posts: List[dict], date: str) -> dict:
        """LLM å¤±æ??‚ç??é€€?¹æ?ï¼šç”¨ç¨‹å??è¼¯?´æ¥çµ±è???""
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        platforms = {"instagram": [], "threads": [], "facebook": [], "web": [], "ptt": [], "dcard": [], "youtube": []}
        all_events = []

        for entry in analyzed_posts:
            analysis = entry["analysis"]
            sentiment = analysis.get("sentiment", "neutral")
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

            platform = entry.get("post", {}).get("platform", "web")
            score = analysis.get("sentiment_score", 0.5)
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(score)

            events = analysis.get("events", [])
            all_events.extend(events)

        platform_breakdown = {}
        for p, scores in platforms.items():
            platform_breakdown[p] = {
                "post_count": len(scores),
                "avg_sentiment": round(sum(scores) / len(scores), 2) if scores else 0.5,
            }

        return {
            "date": date,
            "overview": f"ä»Šæ—¥?±æ”¶??{len(analyzed_posts)} ç­†æ?å°‹ç??œã€?
            f"æ­?¢ {sentiments['positive']} ç­†ã€è???{sentiments['negative']} ç­†ã€?
            f"ä¸­æ€?{sentiments['neutral']} ç­†ã€‚ï?æ­¤ç‚ºç³»çµ±?ªå?çµ±è?ï¼Œé? AI ?†æ?ï¼?,
            "sentiment_distribution": sentiments,
            "hot_topics": [],
            "detected_events": all_events[:5],
            "platform_breakdown": platform_breakdown,
            "alerts": [],
            "recommendation": "å»ºè­°?ç?è§€å¯Ÿã€?,
        }

    def _empty_summary(self, date: Optional[str] = None) -> dict:
        """ç©ºå ±?Šæ¨¡?¿ã€?""
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "overview": "ä»Šæ—¥?¡æ??†åˆ°ä»»ä?è³‡æ???,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "hot_topics": [],
            "detected_events": [],
            "platform_breakdown": {},
            "alerts": [],
            "recommendation": "ä»Šæ—¥?¡è??™å¯ä¾›å??ã€?,
        }
