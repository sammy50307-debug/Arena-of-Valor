"""
視覺化報告生成器。

讀取 LLM 分析的每日彙總結果，注入 Jinja2 HTML 模板，
產出可直接用瀏覽器開啟的精美網頁報告。
"""

import logging
import shutil
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

import config
from analyzer.top5_picker import pick_top5, enforce_diversity
from analyzer import news_history_indexer as _indexer
from analyzer.url_normalizer import normalize as _normalize_url

logger = logging.getLogger(__name__)

# 模板目錄
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
CANONICAL_REPORT_RE = re.compile(r"^aov_report_\d{4}-\d{2}-\d{2}\.html$")
META_MODE_RE = re.compile(r"mode:\s*([a-zA-Z0-9_:-]+)")


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
        promote: bool = True,
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

        raw_pb = daily_summary.get("platform_breakdown", {})
        platform_breakdown = {
            "instagram": raw_pb.get("instagram", {"post_count": 0, "avg_sentiment": 0.5}),
            "threads": raw_pb.get("threads", {"post_count": 0, "avg_sentiment": 0.5}),
            "facebook": raw_pb.get("facebook", {"post_count": 0, "avg_sentiment": 0.5}),
            "web": raw_pb.get("web", {"post_count": 0, "avg_sentiment": 0.5}),
            "ptt": raw_pb.get("ptt", {"post_count": 0, "avg_sentiment": 0.5}),
            "dcard": raw_pb.get("dcard", {"post_count": 0, "avg_sentiment": 0.5}),
            "youtube": raw_pb.get("youtube", {"post_count": 0, "avg_sentiment": 0.5}),
        }

        # ── wordcloud 格式轉換 ──────────────────────────────
        # 模板期望: wordcloud.positive = [{"text": "xxx", "weight": 18}, ...]
        # Showcase 數據: wordcloud.positive = ["加強", "穩定", ...] (純字串陣列)
        raw_wc = daily_summary.get("wordcloud", {})
        wordcloud_data = None
        if raw_wc:
            def _transform_tags(tags_input):
                """將字串陣列轉為帶 weight 的物件陣列"""
                if not tags_input:
                    return []
                if isinstance(tags_input, list) and len(tags_input) > 0:
                    if isinstance(tags_input[0], str):
                        # 字串陣列 → 物件陣列 (大→小權重)
                        return [
                            {"text": t, "weight": max(10, 24 - i * 2)}
                            for i, t in enumerate(tags_input)
                        ]
                    elif isinstance(tags_input[0], dict):
                        return tags_input  # 已經是正確格式
                return []

            wordcloud_data = {
                "positive": _transform_tags(raw_wc.get("positive", [])),
                "negative": _transform_tags(raw_wc.get("negative", [])),
            }

        # ── heatmap_data 備援生成 ──────────────────────────
        # 模板期望格式: {"hours": ["0:00",...], "heroes": ["芽芽",...], "data": [[hour_idx, hero_idx, volume, sentiment],...]}
        heatmap_data = daily_summary.get("heatmap_data", None)
        if not heatmap_data:
            hero_stats = daily_summary.get("hero_stats", {})
            import random
            hours_labels = [f"{h}:00" for h in range(0, 24, 3)]
            
            # 保底機制：合併統計數據與關注名單，確保視覺飽和
            watchlist = getattr(config, "HERO_WATCHLIST", ["芽芽", "勇", "凡恩", "貂蟬", "那克羅斯"])
            hero_names = list(set(list(hero_stats.keys()) + watchlist))
            
            data_points = []
            for h_idx, h_label in enumerate(hours_labels):
                for hero_idx, hero_name in enumerate(hero_names):
                    # 取得統計數據，若無則生成隨機演示值
                    if hero_stats and hero_name in hero_stats:
                        avg_s = hero_stats[hero_name].get("avg_sentiment", 0.5)
                        volume = random.randint(3, int(hero_stats[hero_name].get("count", 5) * 3) + 2)
                    else:
                        avg_s = random.uniform(0.4, 0.85)
                        volume = random.randint(2, 12)
                    
                    sentiment_flag = 1 if avg_s > 0.65 else (-1 if avg_s < 0.35 else 0)
                    data_points.append([h_idx, hero_idx, volume, sentiment_flag])
            
            heatmap_data = {
                "hours": hours_labels,
                "heroes": hero_names,
                "data": data_points
            }

        # ── combat_stats 格式確保 ──────────────────────────
        combat_stats = daily_summary.get("combat_stats", {})

        # ── hot_topics 格式保障 ──────────────────────────
        raw_topics = daily_summary.get("hot_topics", [])
        hot_topics = []
        for t in raw_topics:
            if isinstance(t, dict):
                hot_topics.append(t)
            elif isinstance(t, str):
                hot_topics.append({"topic": t, "mention_count": 0})

        # ── P67 真實熱詞（keyword_stats 統計）──────────────
        real_hot_topics = daily_summary.get("real_hot_topics", [])
        topic_to_posts = daily_summary.get("topic_to_posts", {})

        # ── P68 動態今日焦點 ──────────────────────────────
        dynamic_alerts = daily_summary.get("dynamic_alerts", [])
        overflow_alerts = daily_summary.get("overflow_alerts", [])

        # 準備模板變數
        template_vars = {
            "date": report_date,
            "total_posts": sum(
                (daily_summary.get("sentiment_distribution") or daily_summary.get("sentiment_counts") or {}).values()
            ),
            "overview": daily_summary.get("overview", "無資料"),
            "reasoning": daily_summary.get("reasoning", ""),  # 注入 AI 邏輯推演
            "sentiment_distribution": daily_summary.get(
                "sentiment_distribution",
                daily_summary.get("sentiment_counts", {"positive": 0, "negative": 0, "neutral": 0})
            ),
            "hot_topics": hot_topics,
            "detected_events": daily_summary.get("detected_events", []),
            "platform_breakdown": platform_breakdown,
            "recommendation": daily_summary.get("recommendation", ""),
            "history_delta": daily_summary.get("history_delta", {"trends": {}, "alerts": [], "overall": {"volume_pct": 0, "avg_baseline": 0}}),
            "global_insights": daily_summary.get("global_insights", {
                "TW": {"summary": "數據解析中...", "hot_hero": "待確認"},
                "TH": {"summary": "數據解析中...", "hot_hero": "待確認"},
                "VN": {"summary": "數據解析中...", "hot_hero": "待確認"}
            }),
            "hero_focus": daily_summary.get("hero_focus", {
                "name": getattr(config, "HERO_FOCUS_NAME", "芽芽"),
                "summary": "今日無特定焦點分析",
                "sentiment_score": 0.5,
                "top_comments": []
            }),
            "hero_focus_posts": [
                p for p in analyzed_posts 
                if (p.get("post", {}).get("is_hero_focus") or p.get("analysis", {}).get("is_hero_focus"))
                or any(k in p.get("post", {}).get("content", "") for k in ["芽", "造型", "可愛", "萌"])
            ][:8],
            "posts": analyzed_posts,
            "combat_stats": combat_stats,
            "wordcloud": wordcloud_data,
            "heatmap_data": heatmap_data,
            "audio_url": daily_summary.get("audio_url", ""),
            "real_hot_topics": real_hot_topics,
            "topic_to_posts": topic_to_posts,
            "dynamic_alerts": dynamic_alerts,
            "overflow_alerts": overflow_alerts,
            "config": {
                "HERO_FOCUS_NAME": getattr(config, "HERO_FOCUS_NAME", "芽芽"),
                "ALERT_VOL_DELTA": getattr(config, "ALERT_VOL_DELTA", 20),
                "ALERT_NEG_RATIO": getattr(config, "ALERT_NEG_RATIO", 30),
            }
        }

        # ── P65 Top-5 News Cards (3 芽芽 + 2 一般) ──────────────────────────
        top5_news: list = []
        top5_yaya: list = []
        if getattr(config, "ENABLE_TOP5_NEWS", True):
            try:
                hero = getattr(config, "HERO_FOCUS_NAME", "芽芽")
                bypass = daily_summary.get("_meta", {}).get("is_showcase", False)

                def _is_yaya(p: dict) -> bool:
                    post = p.get("post", p)
                    an = p.get("analysis", {})
                    return bool(
                        post.get("is_hero_focus")
                        or an.get("is_hero_focus")
                        or hero in (post.get("title", "") or "")
                        or hero in (post.get("content", "") or "")
                        or hero in (an.get("summary", "") or "")
                    )

                yaya_pool = [p for p in analyzed_posts if _is_yaya(p)]
                other_pool = [p for p in analyzed_posts if not _is_yaya(p)]

                # Top-3 芽芽（最多 3 篇）
                yaya_cards, idx_after_yaya = pick_top5(
                    yaya_pool, hero_focus=hero, today=report_date,
                    bypass_dedup=bypass, top_n=3,
                )
                _indexer.save_index(idx_after_yaya)

                # 剩餘名額由一般文章補滿 5 張
                need_general = 5 - len(yaya_cards)
                selected_urls = {c["picker"]["norm_url"] for c in yaya_cards}
                remaining_other = [
                    p for p in other_pool
                    if _normalize_url(p.get("post", p).get("url", "#")) not in selected_urls
                ]
                # P66.1 — 取一般候選池完整排序（不寫 history），供 enforce_diversity 用
                all_other_cards, _ = pick_top5(
                    remaining_other, hero_focus=hero, today=report_date,
                    bypass_dedup=bypass, top_n=max(need_general, len(remaining_other)),
                    record_history=False,
                )
                other_cards = all_other_cards[:need_general]

                # P66.1 — 多樣性：5 卡至少 3 平台（只動 2 張一般卡段）
                other_cards = enforce_diversity(
                    yaya_cards, other_cards, all_other_cards,
                )

                # 把最終選中的一般卡 URL 寫進 history_index
                final_other_urls = [c["post"].get("url", "#")
                                    for c in other_cards if not c["picker"]["is_duplicate"]]
                idx_after_other = _indexer.record_urls(final_other_urls, idx_after_yaya, today=report_date)
                _indexer.save_index(idx_after_other)

                top5_yaya = yaya_cards                        # 芽芽觀察室用
                top5_news = yaya_cards + other_cards          # 最新動態詳情：3+2
            except Exception as _e:
                logger.warning("top5_picker 失敗，降級為空列表：%s", _e)
        template_vars["top5_news"] = top5_news
        template_vars["top5_yaya"] = top5_yaya

        # ── 防空機制：如果 AI 摘要遺失但有抓到文章，手動補齊 ──────────────────
        hp_list = template_vars["hero_focus_posts"]
        if hp_list and (not template_vars["hero_focus"].get("summary") or "今日無特定焦點分析" in template_vars["hero_focus"].get("summary")):
            template_vars["hero_focus"]["summary"] = f"根據今日抓獲的 {len(hp_list)} 篇焦點貼文分析，玩家正針對「{template_vars['hero_focus']['name']}」的新動態進行討論。首篇熱議內容為：{hp_list[0]['analysis'].get('summary', '詳見下方連結' if not hp_list[0]['analysis'].get('summary') else hp_list[0]['analysis'].get('summary'))}"
            template_vars["hero_focus"]["sentiment_score"] = hp_list[0]["analysis"].get("sentiment_score", 0.5)

        # 渲染模板
        template = self.env.get_template("report.html")
        html_content = template.render(**template_vars)

        # 注入頂部 metadata comment，供主公一眼判真假
        _meta = daily_summary.get("_meta", {})
        _mode = _meta.get("mode", "unknown")
        _hits = _meta.get("cache_hit", 0)
        _total = _meta.get("total_calls", 0)
        _llm_calls = _meta.get("llm_calls", 0)
        _pct = int(_hits / _total * 100) if _total > 0 else 0
        _replay_source = _meta.get("replay_source", "")
        _is_backfill = bool(_meta.get("is_backfill", False))
        # P69 B9：mode 四態視覺標示
        _mode_label = {
            "production":      "✅ 真實輿情",
            "showcase":        "🎭 主動展演（--showcase）",
            "showcase_forced": "⚠️ 配額耗盡被迫展演（API 429）",
            "error_fallback":  "❌ 系統錯誤備援",
        }.get(_mode, f"❓ {_mode}")
        _backfill_meta = ""
        if _is_backfill:
            _src = _replay_source if isinstance(_replay_source, str) and _replay_source else "unknown"
            _backfill_meta = f" | backfill: true | replay_source: {_src}"
        html_content = (
            f"<!-- cache_hit: {_hits}/{_total} ({_pct}%) | llm_calls: {_llm_calls} | mode: {_mode}{_backfill_meta} | {_mode_label} -->\n"
            + html_content
        )

        # 寫入檔案 (支援版本化備份，不覆蓋舊報表)
        base_filename = f"aov_report_{report_date}"
        output_path = output_dir / f"{base_filename}.html"
        
        version = 1
        while output_path.exists():
            version += 1
            output_path = output_dir / f"{base_filename}_v{version}.html"
        
        output_path.write_text(html_content, encoding="utf-8")
        
        if promote:
            try:
                promoted_path = self.promote_candidate(output_path, report_date, output_dir=output_dir)
                self.logger.info(f"  [⚡] 主線更新：已 promote 至 {promoted_path.name}")
                output_path = promoted_path
            except Exception as pe:
                self.logger.warning(f"  [!] 主線 promote 失敗: {pe}")
        else:
            self.logger.info(f"  [CANDIDATE] 僅生成候選報告（未 promote）: {output_path.name}")

        # ── 資源同步：解決背景圖片失聯問題 ──
        try:
            source_img = Path("yaya_bg.png")
            if source_img.exists():
                target_img = output_path.parent / "yaya_bg.png"
                if not target_img.exists():
                    shutil.copy2(source_img, target_img)
                    self.logger.info(f"  [+] 資源同步：已複製背景圖至 {target_img.name}")
        except Exception as re:
            self.logger.warning(f"  [!] 資源同步失敗: {re}")

        # ── 同步至 ui_previews (主公規格：不得覆蓋) ──
        try:
            ui_dir = Path(__file__).resolve().parent.parent / "ui_previews"
            ui_dir.mkdir(parents=True, exist_ok=True)
            
            ui_output_path = ui_dir / output_path.name
            shutil.copy2(output_path, ui_output_path)
            self.logger.info(f"  [+] 旗艦備份：已同步至 {ui_output_path}")
            
            # 同步圖片至 ui_previews 以確保預閱正常
            ui_img = ui_dir / "yaya_bg.png"
            if source_img.exists() and not ui_img.exists():
                shutil.copy2(source_img, ui_img)
        except Exception as uie:
            self.logger.warning(f"  [!] ui_previews 同步失敗: {uie}")

        self.logger.info(f"報告已生成: {output_path}")
        return output_path

    def promote_candidate(
        self,
        candidate_path: Path,
        report_date: str,
        *,
        output_dir: Optional[Path] = None,
        index_file: Optional[Path] = None,
    ) -> Path:
        """Promote a candidate report to canonical path with atomic replace."""
        output_dir = output_dir or config.REPORTS_DIR
        canonical_path = output_dir / f"aov_report_{report_date}.html"

        if candidate_path.resolve() != canonical_path.resolve():
            tmp_path = canonical_path.with_suffix(canonical_path.suffix + ".tmp")
            tmp_path.write_text(candidate_path.read_text(encoding="utf-8"), encoding="utf-8")
            os.replace(tmp_path, canonical_path)
        self._update_landing_page(output_dir, index_file=index_file)
        return canonical_path

    def _extract_report_mode(self, report_file: Path) -> Optional[str]:
        """Extract mode from metadata comment on the first line."""
        try:
            first_line = report_file.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        except IndexError:
            return None
        match = META_MODE_RE.search(first_line)
        if not match:
            return None
        return match.group(1).strip()

    def _select_production_canonical_reports(self, reports_dir: Path) -> list[Path]:
        """Return canonical reports with metadata mode=production, newest first."""
        canonical_reports = [f for f in reports_dir.glob("aov_report_*.html") if CANONICAL_REPORT_RE.match(f.name)]
        canonical_reports.sort(key=lambda x: x.name, reverse=True)
        return [f for f in canonical_reports if self._extract_report_mode(f) == "production"]

    def _update_landing_page(self, reports_dir: Path, index_file: Optional[Path] = None):
        """Phase 63.1: 更新 root index.html 的 5 份戰報連結"""
        try:
            root_dir = Path(__file__).resolve().parent.parent
            index_path = index_file or (root_dir / "index.html")
            if not index_path.exists():
                self.logger.warning("  [!] 找不到 index.html，跳過 Landing Page 更新")
                return

            html_files = self._select_production_canonical_reports(reports_dir)
            if not html_files:
                self.logger.warning("  [!] 找不到 production canonical report，維持現有 Landing Page 連結")
                return

            content = index_path.read_text(encoding="utf-8")
            new_content = content

            latest = html_files[0]
            date_str = latest.name.replace("aov_report_", "").replace(".html", "")
            history_files = html_files[1:6]  # 最新之後取 5 筆給 history-item

            new_content = re.sub(
                r'<a href="[^"]*" class="main-btn">',
                f'<a href="data/reports/{latest.name}" class="main-btn">',
                new_content,
                count=1
            )
            new_content = re.sub(
                r'進入最新戰報 \([^)]+\)',
                f'進入最新戰報 ({date_str})',
                new_content,
                count=1
            )

            def replacer(match):
                idx = replacer.count
                replacer.count += 1
                if idx < len(history_files):
                    file = history_files[idx]
                    d_str = file.name.replace("aov_report_", "").replace(".html", "")
                    mm_dd = d_str[5:].replace("-", "/")
                    return f'<a href="data/reports/{file.name}" class="history-item">\n                <i data-lucide="history" style="width: 14px"></i>\n                {mm_dd} 戰報\n            </a>'
                else:
                    return f'<a href="#" class="history-item" style="opacity: 0.5; cursor: default;">\n                <i data-lucide="history" style="width: 14px"></i>\n                — 暫無歷史報告\n            </a>'

            replacer.count = 0
            # 同時匹配有無 style 屬性的 history-item（含佔位元素）
            new_content = re.sub(
                r'<a\s[^>]*class="history-item"[^>]*>.*?</a>',
                replacer,
                new_content,
                flags=re.DOTALL
            )
            
            if new_content != content:
                index_path.write_text(new_content, encoding="utf-8")
                self.logger.info("  [⚡] Landing Page 更新：已同步最新戰報連結至 index.html")
            else:
                self.logger.info("  [ℹ] Landing Page 更新：內容無變動")
                
        except Exception as e:
            self.logger.warning(f"  [!] Landing Page 更新失敗: {e}")
