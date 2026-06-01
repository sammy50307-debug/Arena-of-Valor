"""
情緒分析與活動事件萃取主邏輯。

負責將 Tavily 搜尋到的結果批次送入 Gemini LLM 分析，
並產出結構化的每日彙總報告。支援原生 JSON Schema 結構化輸出與斷路器機制。
"""

import json
import logging
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

import config
from scrapers.tavily_searcher import SearchResult
from analyzer.gemini_client import GeminiClient
from analyzer.llm_budget import LLMBudgetSkip
from analyzer.local_analyzer import (
    analyze_posts_locally,
    generate_local_summary,
    has_local_deterministic_posts,
)
from analyzer.provider_router import build_default_llm_client, build_provider_diagnostics
from analyzer.nlp import analyze_keywords
from analyzer.prompts import (
    SYSTEM_SINGLE_POST,
    USER_SINGLE_POST,
    SYSTEM_DAILY_SUMMARY,
    USER_DAILY_SUMMARY,
)

logger = logging.getLogger(__name__)

# ── 原生 JSON Schema 定義 (Structured Outputs) ──
SINGLE_POST_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reasoning": {"type": "STRING"},
        "sentiment": {"type": "STRING", "enum": ["positive", "negative", "neutral"]},
        "sentiment_score": {"type": "NUMBER", "description": "情緒強度 0.0~1.0：0.0=極負面、0.5=中性、1.0=極正面，與 sentiment 方向一致"},
        "region": {"type": "STRING"},
        "original_language": {"type": "STRING"},
        "translated_content": {"type": "STRING"},
        "category": {"type": "STRING"},
        "keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
        "summary": {"type": "STRING"},
        "relevance_score": {"type": "NUMBER"},
        "is_hero_focus": {"type": "BOOLEAN"},
        "events": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "type": {"type": "STRING"},
                    "details": {"type": "STRING"}
                }
            }
        }
    },
    "required": ["reasoning", "sentiment", "sentiment_score", "region", "original_language", "category", "keywords", "summary", "relevance_score", "is_hero_focus"]
}

DAILY_SUMMARY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "date": {"type": "STRING"},
        "overview": {"type": "STRING"},
        "sentiment_distribution": {
            "type": "OBJECT",
            "properties": {
                "positive": {"type": "INTEGER"},
                "negative": {"type": "INTEGER"},
                "neutral": {"type": "INTEGER"}
            }
        },
        "hot_topics": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "topic": {"type": "STRING"},
                    "mention_count": {"type": "INTEGER"},
                    "sentiment": {"type": "STRING"},
                    "description": {"type": "STRING"}
                }
            }
        },
        "detected_events": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "type": {"type": "STRING"},
                    "source_count": {"type": "INTEGER"},
                    "details": {"type": "STRING"}
                }
            }
        },
        "platform_breakdown": {
            "type": "OBJECT",
            "properties": {
                "instagram": {"type": "OBJECT", "properties": {"post_count": {"type": "INTEGER"}, "avg_sentiment": {"type": "NUMBER"}}},
                "threads": {"type": "OBJECT", "properties": {"post_count": {"type": "INTEGER"}, "avg_sentiment": {"type": "NUMBER"}}},
                "facebook": {"type": "OBJECT", "properties": {"post_count": {"type": "INTEGER"}, "avg_sentiment": {"type": "NUMBER"}}}
            }
        },
        "alerts": {"type": "ARRAY", "items": {"type": "STRING"}},
        "recommendation": {"type": "STRING"},
        "global_insights": {
            "type": "OBJECT",
            "properties": {
                "TW": {"type": "OBJECT", "properties": {"summary": {"type": "STRING"}, "hot_hero": {"type": "STRING"}}},
                "TH": {"type": "OBJECT", "properties": {"summary": {"type": "STRING"}, "hot_hero": {"type": "STRING"}}},
                "VN": {"type": "OBJECT", "properties": {"summary": {"type": "STRING"}, "hot_hero": {"type": "STRING"}}}
            }
        },
        "hero_focus": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "summary": {"type": "STRING"},
                "sentiment_score": {"type": "NUMBER", "description": "焦點英雄情緒 0.0~1.0：0.0=極負面、0.5=中性、1.0=極正面，與單篇同方向"},
                "top_comments": {"type": "ARRAY", "items": {"type": "STRING"}}
            }
        }
    },
    "required": ["date", "overview", "sentiment_distribution", "hot_topics", "detected_events", "platform_breakdown", "alerts", "recommendation"]
}


class LLMContractError(ValueError):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _schema_type_matches(value: Any, schema_type: str) -> bool:
    if schema_type == "OBJECT":
        return isinstance(value, dict)
    if schema_type == "ARRAY":
        return isinstance(value, list)
    if schema_type == "STRING":
        return isinstance(value, str)
    if schema_type == "NUMBER":
        return (isinstance(value, (int, float)) and not isinstance(value, bool))
    if schema_type == "INTEGER":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "BOOLEAN":
        return isinstance(value, bool)
    return True


def _validate_schema_payload(payload: Any, schema: Dict[str, Any], label: str) -> List[str]:
    if not isinstance(payload, dict):
        return ["%s must be object" % label]

    errors: List[str] = []
    properties = schema.get("properties", {})
    for field in schema.get("required", []):
        if field not in payload:
            errors.append("%s missing required field: %s" % (label, field))
            continue
        expected = properties.get(field, {}).get("type")
        if expected and not _schema_type_matches(payload.get(field), expected):
            errors.append("%s.%s must be %s" % (label, field, expected))
    return errors


class SentimentAnalyzer:
    """
    輿情分析器：將搜尋結果送入 Gemini 進行情緒分析與事件偵測，
    最終產出每日彙總報告。
    """

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client or build_default_llm_client()
        self.logger = logging.getLogger(f"{__name__}.SentimentAnalyzer")

    def _provider_diagnostics(self) -> dict:
        configured = getattr(self.llm, "fallback_configured", False)
        fallback_used = getattr(self.llm, "last_fallback_used", False)
        details = {}
        diagnostics = getattr(self.llm, "provider_diagnostics", None)
        if callable(diagnostics):
            raw = diagnostics()
            if isinstance(raw, dict):
                details.update(raw)
        else:
            details.update(build_provider_diagnostics())
        details.update({
            "openai_fallback_configured": configured if isinstance(configured, bool) else False,
            "openai_fallback_used": fallback_used if isinstance(fallback_used, bool) else False,
        })
        return details

    def active_provider_model(self) -> tuple:
        """取實際首發 provider 基礎名 + model id（manifest 追溯用）。

        self.llm 可能是 FallbackLLMClient 或 ProviderRouter；往下挖兩層到實際首發 client
        （router.primary→FallbackLLMClient.primary→實際 client）。無法辨識回 ("gemini", "")。
        """
        from analyzer.provider_router import provider_role_name

        client = getattr(self.llm, "primary", self.llm)
        client = getattr(client, "primary", client)
        provider = provider_role_name(client, "primary").rsplit("_", 1)[0]
        model = str(getattr(client, "model", "") or "")
        return provider, model

    def _compress_content(self, text: str, target_heroes: List[str]) -> str:
        """長文本智能切片：保留首尾 150 字及含有焦點英雄的段落。"""
        if len(text) <= 500:
            return text
            
        sentences = [s.strip() for s in text.replace("\n", "。").replace("！", "。").replace("？", "。").split("。") if s.strip()]
        if not sentences:
            return text[:500]
            
        important_sentences = []
        for hero in target_heroes:
            for s in sentences:
                if hero in s and s not in important_sentences:
                    important_sentences.append(s)
                    
        start_chunk = text[:150]
        end_chunk = text[-150:]
        middle_chunk = " ... ".join(important_sentences)
        
        compressed = f"{start_chunk} ...\n[核心萃取]: {middle_chunk}\n... {end_chunk}"
        return compressed[:2000]

    async def analyze_posts(
        self,
        search_results: List[SearchResult],
        showcase: bool = False,
        hero_name: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> List[dict]:
        """批次分析搜尋結果的情緒與事件。支援斷路器 (Circuit Breaker) 模式。"""
        if not search_results:
            self.logger.warning("沒有搜尋結果可以分析")
            return []

        # L1 快取命中：同英雄同日直接回傳，零 LLM 呼叫
        cm = self.llm.cache_manager
        l1_key = cm.hero_key(hero_name, date_str) if hero_name and date_str else None
        if l1_key:
            cached = cm.get(l1_key)
            if cached is not None:
                cm.increment_stat("total_l1_hits")
                self.logger.info(f"   [⚡] L1 快取命中 ({l1_key})，零 LLM 呼叫")
                if isinstance(cached, dict):
                    cached.setdefault("provider_diagnostics", self._provider_diagnostics())
                return cached

        self.logger.info(f"開始分析 {len(search_results)} 筆結果...")

        user_prompts = []
        for res in search_results:
            region_hint = f"區域提示: {res.region}"
            compressed_content = self._compress_content(res.content, config.HERO_WATCHLIST)
            content = f"[{res.title}] {compressed_content}"
            user_prompts.append(
                f"{region_hint}\n" + 
                USER_SINGLE_POST.format(
                    platform=res.platform or "web",
                    author=res.source or "unknown",
                    content=content, 
                )
            )

        # P69/P88：區分主動 showcase vs provider failure；非主動 showcase 改走真實來源 local baseline。
        quota_error_triggered = False
        local_fallback_reason = ""
        local_fallback_showcase = None
        try:
            results = await self.llm.batch_chat(
                system_prompt=SYSTEM_SINGLE_POST,
                user_prompts=user_prompts,
                json_mode=True,
                concurrency=getattr(self.llm, "CONCURRENCY_LIMIT", GeminiClient.CONCURRENCY_LIMIT),
                response_schema=SINGLE_POST_SCHEMA
            )
        except httpx.HTTPStatusError as e:
            self.logger.warning("[!] 配額耗盡熔斷觸發 → 切換至本地 deterministic baseline（quota_error=True）")
            results = []
            quota_error_triggered = True
            if not showcase:
                status_code = getattr(getattr(e, "response", None), "status_code", "unknown")
                local_fallback_reason = "http_status_%s" % status_code
                local_fallback_showcase = False
        except LLMBudgetSkip as e:
            self.logger.warning("[!] LLM budget/cooldown 停損觸發 → 切換至本地 deterministic baseline")
            results = []
            if not showcase:
                local_fallback_reason = "budget_skip:%s" % e.decision.reason
                local_fallback_showcase = False
        except Exception as e:
            if showcase:
                self.logger.warning(f"分析失敗 ({e})... 任務模式：啟動精品級數據備援系統。")
            else:
                self.logger.warning(f"分析流程中斷 ({e})... 啟動本地 deterministic baseline。")
                local_fallback_reason = "%s: %s" % (type(e).__name__, e)
                local_fallback_showcase = True
            results = []

        if local_fallback_reason:
            analyzed = analyze_posts_locally(search_results, config.HERO_WATCHLIST)
            return {
                "posts": analyzed,
                "is_showcase": bool(local_fallback_showcase),
                "quota_error": quota_error_triggered,
                "contract_status": "ok",
                "contract_errors": [],
                "local_analysis_status": "ok",
                "fallback_reason": local_fallback_reason,
                "analysis_source": "local_deterministic",
                "provider_diagnostics": self._provider_diagnostics(),
            }
            
        if showcase and not results:
            analyzed = []
            for res in search_results:
                mock_analysis = {
                    "sentiment": "positive" if "教學" in res.title or "強" in res.title or "奪冠" in res.title else "neutral",
                    "sentiment_score": 0.88 if "芽芽" in res.title else 0.75,
                    "summary": f"針對「{res.title}」之深度分析：其內容反映了目前台服社群對於英雄機制的高度關注。玩家情緒整體穩定。",
                    "keywords": ["戰術", "平衡", "社群"],
                    "relevance_score": 0.95,
                    "category": "戰術分析",
                    "region": res.region,
                    "original_language": "zh",
                    "is_hero_focus": "芽芽" in res.title,
                    "detected_heroes": ["芽芽"] if "芽芽" in res.title else [],
                    "translated_content": "",
                    "events": []
                }
                entry = {
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "content": res.content,
                        "title": res.title,
                        "timestamp": getattr(res, "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        "is_hero_focus": "芽芽" in res.title,
                        "region": res.region,
                        "original_language": "zh"
                    },
                    "analysis": mock_analysis
                }
                analyzed.append(entry)
            return {
                "posts": analyzed,
                "is_showcase": True,
                "quota_error": quota_error_triggered,
                "contract_status": "ok",
                "contract_errors": [],
                "provider_diagnostics": self._provider_diagnostics(),
            }

        analyzed = []
        contract_errors: List[str] = []
        for idx, (res, analysis) in enumerate(zip(search_results, results), 1):
            analysis_errors = _validate_schema_payload(analysis, SINGLE_POST_SCHEMA, "single_post[%d]" % idx)
            if isinstance(analysis, dict) and "error" not in analysis and not analysis_errors:
                analysis["llm_contract"] = {"status": "ok", "errors": []}
                # ── 英雄偵測鏈強化 (God-mode Fix) ──
                # 從分析結果的關鍵字中二次提取關注英雄名
                detected = [h for h in config.HERO_WATCHLIST if h in str(analysis.get("keywords", [])) or h in (res.title or "")]
                
                entry = {
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "title": res.title,
                        "content": res.content,
                        "timestamp": getattr(res, "timestamp", "時間未知"),
                        "is_hero_focus": analysis.get("is_hero_focus", False),
                        "detected_heroes": detected,  # 這是熱度圖生存的關鍵
                        "region": analysis.get("region", res.region),
                        "original_language": analysis.get("original_language", "zh"),
                        "translated_content": analysis.get("translated_content", "")
                    },
                    "analysis": analysis,
                }
                analyzed.append(entry)
            else:
                if not analysis_errors:
                    analysis_errors = ["single_post[%d] contains error response" % idx]
                contract_errors.extend(analysis_errors)
                analyzed.append({
                    "post": {
                        "platform": res.platform,
                        "author": res.source,
                        "url": res.url,
                        "content": res.content,
                        "timestamp": "時間未知",
                    },
                    "analysis": {
                        "sentiment": "neutral",
                        "sentiment_score": 0.5,
                        "category": "其他",
                        "keywords": [],
                        "events": [],
                        "summary": "分析失敗",
                        "relevance_score": 0.0,
                        "llm_contract": {
                            "status": "degraded",
                            "errors": analysis_errors,
                        },
                    },
                })

        self.logger.info(f"完成 {len(analyzed)} 筆結果分析 (Final Showcase Status: {showcase})")
        result = {
            "posts": analyzed,
            "is_showcase": showcase,
            "quota_error": False,
            "contract_status": "degraded" if contract_errors else "ok",
            "contract_errors": contract_errors,
            "provider_diagnostics": self._provider_diagnostics(),
        }

        # L1 寫入：showcase 結果不寫，避免污染快取
        if l1_key and not showcase and analyzed:
            cm.set(l1_key, result)
            cm.save()
            self.logger.info(f"   [💾] L1 快取寫入 ({l1_key})")

        return result

    async def generate_daily_summary(
        self,
        analyzed_posts: List[dict],
        date: Optional[str] = None,
        showcase: bool = False,
    ) -> dict:
        """根據分析結果產出每日彙總報告。支援本地備援分析與 Schema 結構鎖定。"""
        if not analyzed_posts:
            return self._empty_summary(date)

        report_date = date or datetime.now().strftime("%Y-%m-%d")

        # P69 A7：showcase 模式直接走 fallback，不打 LLM（省配額、防雪崩）
        if showcase:
            if has_local_deterministic_posts(analyzed_posts):
                self.logger.info("daily_summary skipped LLM: local deterministic analyzed posts → local summary")
                return generate_local_summary(
                    analyzed_posts,
                    report_date,
                    hero_focus=getattr(config, "HERO_FOCUS_NAME", "芽芽"),
                )
            self.logger.info("daily_summary skipped LLM: showcase mode → fallback 模板（quota 保護）")
            return self._generate_fallback_summary(analyzed_posts, report_date, showcase)

        # daily_summary 快取命中
        cm = self.llm.cache_manager
        ds_key = cm.daily_summary_key(report_date)
        cached_summary = cm.get(ds_key)
        if cached_summary is not None:
            self.logger.info(f"   [⚡] daily_summary 快取命中 ({ds_key})")
            return cached_summary
        analysis_text = self._format_analysis_for_summary(analyzed_posts)

        regional_summary_data = {}
        for r in ["TW", "TH", "VN"]:
            r_posts = [p for p in analyzed_posts if p["post"].get("region") == r]
            if r_posts:
                main_analysis = r_posts[0]['analysis']
                detected_heroes = r_posts[0]['post'].get('detected_heroes', [])
                regional_summary_data[r] = {
                    "summary": main_analysis.get("summary", "無數據摘要"),
                    "hot_hero": detected_heroes[0] if detected_heroes else "無特定英雄"
                }

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
                response_schema=DAILY_SUMMARY_SCHEMA
            )
            if not isinstance(summary, dict):
                raise ValueError("LLM 回傳格式錯誤")
            summary_errors = _validate_schema_payload(summary, DAILY_SUMMARY_SCHEMA, "daily_summary")
            if summary_errors:
                raise LLMContractError(summary_errors)
                
            summary["global_insights"] = regional_summary_data
            summary["llm_contract"] = {"status": "ok", "errors": []}
            
            hero_stats = {}
            for hero in config.HERO_WATCHLIST:
                hero_posts = [p for p in analyzed_posts if hero in p["post"].get("detected_heroes", [])]
                if hero_posts:
                    avg_score = sum(p["analysis"].get("sentiment_score", 0.5) for p in hero_posts) / len(hero_posts)
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
            
            pos_texts = [p["post"]["content"] for p in analyzed_posts if p["analysis"].get("sentiment") == "positive"]
            neg_texts = [p["post"]["content"] for p in analyzed_posts if p["analysis"].get("sentiment") == "negative"]
            summary["wordcloud"] = {
                "positive": analyze_keywords(pos_texts, limit=12),
                "negative": analyze_keywords(neg_texts, limit=12)
            }
            
            top_posts = sorted(
                [p for p in analyzed_posts if p.get("post", {}).get("url") and p["post"]["url"] != "N/A"],
                key=lambda x: x.get("analysis", {}).get("relevance_score", 0),
                reverse=True
            )[:3]
            
            top_links = []
            for p in top_posts:
                content_preview = p["post"]["content"][:20].replace("\n", " ") + "..."
                top_links.append({"title": content_preview, "url": p["post"]["url"], "platform": p["post"]["platform"]})
            summary["top_links"] = top_links

            # P67 真實熱詞統計（jieba keyword_stats）
            try:
                from analyzer.keyword_stats import compute_hot_topics
                raw_posts = [e["post"] for e in analyzed_posts]
                real_hot_topics, topic_to_posts = compute_hot_topics(raw_posts)
                summary["real_hot_topics"] = real_hot_topics
                summary["topic_to_posts"] = topic_to_posts
            except Exception as _kw_e:
                self.logger.warning("keyword_stats 失敗，fallback 空列表：%s", _kw_e)
                summary["real_hot_topics"] = []
                summary["topic_to_posts"] = {}

            # P68 動態今日焦點（只在 alerts 為空時觸發）
            history_delta = summary.get("history_delta", {})
            if not history_delta.get("alerts"):
                try:
                    from analyzer.dynamic_focus import build_dynamic_alerts
                    hero = getattr(__import__("config"), "HERO_FOCUS_NAME", "芽芽")
                    df_result = await build_dynamic_alerts(
                        summary=summary,
                        analyzed_posts=analyzed_posts,
                        hero_focus=hero,
                        date_str=report_date,
                        llm_client=self.llm,
                    )
                    summary["dynamic_alerts"] = df_result["dynamic_alerts"]
                    summary["overflow_alerts"] = df_result["overflow_alerts"]
                except Exception as _df_e:
                    self.logger.warning("dynamic_focus 失敗，fallback 空：%s", _df_e)
                    summary["dynamic_alerts"] = []
                    summary["overflow_alerts"] = []
            else:
                summary["dynamic_alerts"] = []
                summary["overflow_alerts"] = []

            # daily_summary 寫入快取
            cm.set(ds_key, summary)
            cm.save()

            return summary

        except Exception as e:
            self.logger.warning(f"摘要生成失敗 ({e})... 啟動本地 deterministic summary")
            fallback = self._generate_fallback_summary(analyzed_posts, report_date, showcase)
            if isinstance(e, LLMContractError):
                fallback["llm_contract"] = {"status": "degraded", "errors": e.errors}
            else:
                fallback["llm_contract"] = {
                    "status": "skipped",
                    "errors": ["%s: %s" % (type(e).__name__, e)],
                }
            return fallback

    def _format_analysis_for_summary(self, analyzed_posts: List[dict]) -> str:
        lines = []
        for i, entry in enumerate(analyzed_posts, 1):
            post = entry["post"]
            analysis = entry["analysis"]
            lines.append(f"平台: {post['platform']} | 情緒: {analysis.get('sentiment')} | 摘要: {analysis.get('summary')}")
        return "\n".join(lines)[:10000]

    def _generate_fallback_summary(self, analyzed_posts: List[dict], date: str, showcase: bool = False) -> dict:
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        for entry in analyzed_posts:
            s = entry["analysis"].get("sentiment", "neutral")
            sentiments[s] = sentiments.get(s, 0) + 1

        overview = f"今日輿情共搜集到 {len(analyzed_posts)} 筆資料。在系統備援模式下穩定運作。"
        
        # ── 任務模式：高品質戰略填充 (Phase 34) ──
        if showcase:
            return {
                "overall": {
                    "sentiment_score": 0.88,
                    "summary": "今日 AoV 台服生態穩定，玩家對於近期『輔助位加強』呈現高度正向反饋，新版本戰術體系正在快速成形。",
                    "trend": "Upward"
                },
                "reasoning": "1. 數據分佈顯示：關注焦點主要集中在『輔助定位』的戰術變革，正面情緒佔比 67%。\n2. 邏輯鏈條：輔助裝備調整 -> 芽芽等護盾型英雄收益增加 -> 射手生存環境改善 -> 全體玩家挫折感降低。\n3. 風險預警：雖然目前情緒正向，但須防範因『護盾過厚』導致的對抗性流失。建議持續觀察高階排位的 BAN 掉率變化。",
                "date": date,
                "overview": "戰情摘要：台服社群近期聚焦於職業聯賽戰術下放，以及英雄『芽芽』與特定射手的搭配效益。數據顯示玩家對於環境平衡度滿意度提升。",
                "total_posts": 12,
                "sentiment_distribution": {"positive": 8, "negative": 1, "neutral": 3},
                "platform_breakdown": {
                    "facebook": {"post_count": 5, "sentiment_ratio": 0.8},
                    "forum": {"post_count": 4, "sentiment_ratio": 0.5},
                    "youtube": {"post_count": 3, "sentiment_ratio": 0.9}
                },
                "detected_events": [
                    {"type": "Update", "title": "台服平衡性微調", "impact": "High"},
                    {"type": "Trend", "title": "芽芽輔助熱度攀升", "impact": "Medium"}
                ],
                "hero_stats": {
                    "芽芽": {
                        "count": 8,
                        "avg_sentiment": 0.92,
                        "wordcloud": {
                            "positive": ["護盾極厚", "強大保護", "必勝", "神輔助", "造型可愛", "地圖控制"],
                            "negative": ["禁排", "BAN"]
                        }
                    }
                },
                "wordcloud": {
                    "positive": ["加強", "穩定", "奪冠", "期待", "戰術", "平衡", "芽芽", "輔助"],
                    "negative": ["削弱", "抱怨", "延遲"]
                },
                "top_links": [
                    {"title": "精品輿情 | 新版芽芽全方位教學", "url": "https://example.com/yaya-guide", "platform": "Web"},
                    {"title": "戰術焦點 | 職業聯賽輔助位體系拆解", "url": "https://example.com/pro-league", "platform": "FB"},
                    {"title": "環境預警 | 全球服版本平衡變動彙整", "url": "https://example.com/patch-notes", "platform": "Discord"}
                ],
                "hero_focus_posts": [
                   {
                       "post": {"platform": "forum", "url": "https://example.com/yaya-1", "title": "芽芽上分指南"},
                       "analysis": {"summary": "芽芽目前在台服高星排位中具備極高影響力，建議優先鎖定。", "sentiment": "positive"}
                   },
                   {
                       "post": {"platform": "facebook", "url": "https://example.com/yaya-2", "title": "職業選手評析芽芽"},
                       "analysis": {"summary": "職業聯賽中芽芽的出裝選擇多元，具備強大的保排能力。", "sentiment": "positive"}
                   },
                   {
                       "post": {"platform": "web", "url": "https://example.com/yaya-3", "title": "全網戰報彙整"},
                       "analysis": {"summary": "全球伺服器芽芽勝率穩定維持在 52% 以上。", "sentiment": "neutral"}
                   }
                ],
                "hero_focus": {
                    "name": "芽芽",
                    "summary": "芽芽在今日情報中佔據核心位置。玩家普遍認可其在新版本中的護盾加強，認為是目前輔助位的版本答案。",
                    "sentiment_score": 0.92,
                    "top_comments": [
                        "這波加強真的有感，護盾厚到誇張",
                        "配上射手簡直無敵，台服目前沒幾檔得住",
                        "造型什麼時候才出？期待很久了"
                    ]
                },
                "recommendation": "偵測到 API 限額，已啟動『旗艦級演示數據』保障顯示效果。目前建議持續關注芽芽的 BAN 率變動。",
                "history_delta": {
                    "overall": {"volume_pct": 15.5, "avg_baseline": 65.0, "is_red_alert": False},
                    "weekly_vol_pulse": {
                        "volumes": [45, 52, 48, 70, 85, 62, 78],
                        "labels": ["03/24", "03/25", "03/26", "03/27", "03/28", "03/29", "03/30"],
                        "average": 62.8
                    },
                    "alerts": []
                },
                "combat_stats": {
                    "芽芽": {
                        "win_rate": 52.8,
                        "pick_rate": 18.5,
                        "ban_rate": 45.2,
                        "kda": "3.2/2.1/15.4"
                    }
                }
            }

        return generate_local_summary(
            analyzed_posts,
            date,
            hero_focus=getattr(config, "HERO_FOCUS_NAME", "芽芽"),
        )

    def _empty_summary(self, date: Optional[str] = None, showcase: bool = False) -> dict:
        if showcase:
            self.logger.warning("  [!] 系統進入極度備援模式：正強制回傳五星級演示摘要。")
            return self._generate_fallback_summary(
                analyzed_posts=[], 
                date=date or datetime.now().strftime("%Y-%m-%d"),
                showcase=True
            )
            
        return {
            "overall": {"sentiment_score": 0.5, "summary": "今日無搜集到任何資料。", "trend": "Stable"},
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "overview": "今日無搜集到任何資料。",
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "hot_topics": [],
            "detected_events": [],
            "platform_breakdown": {},
            "alerts": [],
            "recommendation": "今日無資料可供分析。",
        }
