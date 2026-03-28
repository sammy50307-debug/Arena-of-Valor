"""
情緒分析與活動事件萃取主邏輯。

負責將 Tavily 搜尋到的結果批次送入 Gemini LLM 分析，
並產出結構化的每日彙總報告。
"""

import json
import logging
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

import config
from scrapers.tavily_searcher import SearchResult
from analyzer.gemini_client import GeminiClient
from analyzer.nlp import analyze_keywords
from analyzer.prompts import (
    SYSTEM_SINGLE_POST,
    USER_SINGLE_POST,
    SYSTEM_DAILY_SUMMARY,
    USER_DAILY_SUMMARY,
)

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    輿情分析器：將搜尋結果送入 Gemini 進行情緒分析與事件偵測，
    最終產出每日彙總報告。
    """

    def __init__(self, llm_client: Optional[GeminiClient] = None):
        self.llm = llm_client or GeminiClient()
        self.logger = logging.getLogger(f"{__name__}.SentimentAnalyzer")

    async def analyze_posts(self, search_results: List[SearchResult]) -> List[dict]:
        """
        批次分析搜尋結果的情緒與事件。

        Args:
            search_results: Tavily 搜集到的結果列表

        Returns:
            每篇內容的分析結果列表
        """
        if not search_results:
            self.logger.warning("沒有搜尋結果可以分析")
            return []

        self.logger.info(f"開始分析 {len(search_results)} 筆結果...")

        # 建構每筆結果的 user prompt
        user_prompts = []
        for res in search_results:
            # 傳遞預設區域以輔助 AI 判定
            region_hint = f"區域提示: {res.region}"
            content = f"[{res.title}] {res.content}"
            user_prompts.append(
                f"{region_hint}\n" + 
                USER_SINGLE_POST.format(
                    platform=res.platform or "web",
                    author=res.source or "unknown",
                    content=content[:1000], 
                )
            )

        # 批次呼叫 Gemini (設定低 concurrency 避免觸發免費版 rate limit)
        results = await self.llm.batch_chat(
            system_prompt=SYSTEM_SINGLE_POST,
            user_prompts=user_prompts,
            json_mode=True,
            concurrency=1,
        )

        # 將分析結果與原始資料合併
        analyzed = []
        for res, analysis in zip(search_results, results):
            if isinstance(analysis, dict) and "error" not in analysis:
                entry = {
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "content": res.content,
                        "timestamp": getattr(res, "timestamp", "時間未知"),
                        "is_hero_focus": getattr(res, "is_hero_focus", False),
                        "region": analysis.get("region", res.region), # 使用 AI 修正或原始標籤
                        "original_language": analysis.get("original_language", "zh"),
                        "translated_content": analysis.get("translated_content", "")
                    },
                    "analysis": analysis,
                }
                analyzed.append(entry)
            else:
                self.logger.warning(
                    f"分析失敗 ({res.platform} - {res.url}): {analysis}"
                )
                # 使用預設值
                analyzed.append({
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "content": res.content,
                        "timestamp": getattr(res, "timestamp", getattr(res, "published_date", getattr(res, "date", "時間未知"))),
                    },
                    "analysis": {
                        "sentiment": "neutral",
                        "sentiment_score": 0.5,
                        "category": "其他",
                        "keywords": [],
                        "events": [],
                        "summary": "分析失敗",
                        "relevance_score": 0.0,
                    },
                })

        self.logger.info(f"完成 {len(analyzed)} 筆結果分析")
        return analyzed

    async def generate_daily_summary(
        self,
        analyzed_posts: List[dict],
        date: Optional[str] = None,
    ) -> dict:
        """
        根據分析結果產出每日彙總報告。
        """
        if not analyzed_posts:
            return self._empty_summary(date)

        report_date = date or datetime.now().strftime("%Y-%m-%d")

        # 彙整分析結果成文字形式，送入 LLM 產出彙總
        analysis_text = self._format_analysis_for_summary(analyzed_posts)

        # ── Phase 33: 區域分組資訊注入 ──
        regional_summary_data = {}
        for r in ["TW", "TH", "VN"]:
            r_posts = [p for p in analyzed_posts if p["post"].get("region") == r]
            if r_posts:
                regional_summary_data[r] = f"文章數: {len(r_posts)} | 核心情緒: {r_posts[0]['analysis'].get('summary', '無')}"

        user_prompt = USER_DAILY_SUMMARY.format(
            date=report_date,
            total_posts=len(analyzed_posts),
            analysis_results=analysis_text + f"\n\n區域統計預覽: {json.dumps(regional_summary_data, ensure_ascii=False)}"
        )

        try:
            summary = await self.llm.chat(
                system_prompt=SYSTEM_DAILY_SUMMARY,
                user_prompt=user_prompt,
                json_mode=True,
                temperature=0.4,
            )
            if not isinstance(summary, dict):
                raise ValueError(f"Gemini 回傳了非字典格式: {summary}")
                
            # 統計監視名單中的英雄熱度與情緒
            hero_stats = {}
            for hero in config.HERO_WATCHLIST:
                hero_posts = [p for p in analyzed_posts if hero in p["post"].get("detected_heroes", [])]
                if hero_posts:
                    avg_score = sum(p["analysis"].get("sentiment_score", 0.5) for p in hero_posts) / len(hero_posts)
                    
                    # 英雄個人詞雲 (Phase 32)
                    hero_pos = [p["post"]["content"] for p in hero_posts if p["analysis"].get("sentiment") == "positive"]
                    hero_neg = [p["post"]["content"] for p in hero_posts if p["analysis"].get("sentiment") == "negative"]
                    
                    hero_stats[hero] = {
                        "count": len(hero_posts),
                        "avg_sentiment": avg_score,
                        "wordcloud": {
                            "positive": analyze_keywords(hero_pos, limit=8),
                            "negative": analyze_keywords(hero_neg, limit=8)
                        }
                    }
            summary["hero_stats"] = hero_stats
            
            # 全域詞雲數據 (Phase 32)
            pos_texts = [p["post"]["content"] for p in analyzed_posts if p["analysis"].get("sentiment") == "positive"]
            neg_texts = [p["post"]["content"] for p in analyzed_posts if p["analysis"].get("sentiment") == "negative"]
            summary["wordcloud"] = {
                "positive": analyze_keywords(pos_texts, limit=12),
                "negative": analyze_keywords(neg_texts, limit=12)
            }
            
            # 將熱度最高的 3 篇貼文連結抓出來放進 summary 裡，供 Line/Telegram 推播使用
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
            self.logger.error(f"每日摘要生成失敗: {e}")
            return self._generate_fallback_summary(analyzed_posts, report_date)

    def _format_analysis_for_summary(self, analyzed_posts: List[dict]) -> str:
        """將分析結果格式化為 LLM 可讀的文字。"""
        lines = []
        for i, entry in enumerate(analyzed_posts, 1):
            post = entry["post"]
            analysis = entry["analysis"]
            lines.append(
                f"平台: {post['platform']} | "
                f"焦點標記: {'是' if post.get('is_hero_focus') or analysis.get('is_hero_focus') else '否'} | "
                f"情緒: {analysis.get('sentiment', 'N/A')} ({analysis.get('sentiment_score', 'N/A')}) | "
                f"分類: {analysis.get('category', 'N/A')} | "
                f"摘要: {analysis.get('summary', 'N/A')}"
            )
            events = analysis.get("events", [])
            if events:
                for evt in events:
                    lines.append(
                        f"    → 活動: {evt.get('name', 'N/A')} ({evt.get('type', 'N/A')})"
                    )
        # 如果結果太多可能超過 token 上限，截斷
        full_text = "\n".join(lines)
        if len(full_text) > 10000:
            full_text = full_text[:10000] + "\n... (資料過多已截斷)"
        return full_text

    def _generate_fallback_summary(self, analyzed_posts: List[dict], date: str) -> dict:
        """LLM 失敗時的回退方案：用程式邏輯直接統計並生成具備『旗艦結構』的摘要。"""
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        platforms = {"instagram": [], "threads": [], "facebook": [], "web": [], "ptt": [], "dcard": [], "youtube": []}
        all_events = []
        hero_posts = []

        for entry in analyzed_posts:
            analysis = entry["analysis"]
            sentiment = analysis.get("sentiment", "neutral")
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

            post = entry.get("post", {})
            platform = post.get("platform", "web")
            score = analysis.get("sentiment_score", 0.5)
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(score)

            if post.get("is_hero_focus"):
                hero_posts.append(entry)

            events = analysis.get("events", [])
            all_events.extend(events)

        platform_breakdown = {}
        for p, scores in platforms.items():
            if scores:
                platform_breakdown[p] = {
                    "post_count": len(scores),
                    "avg_sentiment": round(sum(scores) / len(scores), 2),
                }

        # 建立較自然的備援 Overview
        top_titles = [p["post"]["title"][:20] + "..." for p in analyzed_posts if len(p.get("post", {}).get("title", "")) > 5][:3]
        overview = f"今日輿情焦點包含「{', '.join(top_titles)}」等議題。"
        overview += f" 在總計 {len(analyzed_posts)} 筆討論中，正面情緒佔 {sentiments['positive']} 筆。"
        overview += " (AI 分析暫時中斷，此為系統備援統計)"

        return {
            "date": date,
            "overview": overview,
            "sentiment_distribution": sentiments,
            "hot_topics": ["賽事焦點", "活動更新", "社群熱議"] if analyzed_posts else [],
            "detected_events": all_events[:5],
            "platform_breakdown": platform_breakdown,
            "hero_focus": {
                "name": "芽芽",
                "summary": f"偵測到 {len(hero_posts)} 筆焦點英雄相關討論。目前的社群情感與活動連動緊密，請參考詳細貼文列表。",
                "sentiment_score": 0.5,
                "top_comments": [p["post"]["title"] for p in hero_posts[:2]] if hero_posts else []
            },
            "recommendation": "偵測到 API 頻率限制 (429)，建議後續手動檢查 GCS 賽事標籤以補足深度情報。",
        }

    def _empty_summary(self, date: Optional[str] = None) -> dict:
        """空報告模板。"""
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "overview": "今日無搜集到任何資料。",
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "hot_topics": [],
            "detected_events": [],
            "platform_breakdown": {},
            "alerts": [],
            "recommendation": "今日無資料可供分析。",
        }
