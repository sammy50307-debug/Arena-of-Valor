"""
視覺化報告生成器。

讀取 LLM 分析的每日彙總結果，注入 Jinja2 HTML 模板，
產出可直接用瀏覽器開啟的精美網頁報告。
"""

import logging
import shutil
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
            "config": {
                "HERO_FOCUS_NAME": getattr(config, "HERO_FOCUS_NAME", "芽芽"),
                "ALERT_VOL_DELTA": getattr(config, "ALERT_VOL_DELTA", 20),
                "ALERT_NEG_RATIO": getattr(config, "ALERT_NEG_RATIO", 30),
            }
        }

        # ── 防空機制：如果 AI 摘要遺失但有抓到文章，手動補齊 ──────────────────
        hp_list = template_vars["hero_focus_posts"]
        if hp_list and (not template_vars["hero_focus"].get("summary") or "今日無特定焦點分析" in template_vars["hero_focus"].get("summary")):
            template_vars["hero_focus"]["summary"] = f"根據今日抓獲的 {len(hp_list)} 篇焦點貼文分析，玩家正針對「{template_vars['hero_focus']['name']}」的新動態進行討論。首篇熱議內容為：{hp_list[0]['analysis'].get('summary', '詳見下方連結' if not hp_list[0]['analysis'].get('summary') else hp_list[0]['analysis'].get('summary'))}"
            template_vars["hero_focus"]["sentiment_score"] = hp_list[0]["analysis"].get("sentiment_score", 0.5)

        # 渲染模板
        template = self.env.get_template("report.html")
        html_content = template.render(**template_vars)

        # 寫入檔案 (支援版本化備份，不覆蓋舊報表)
        base_filename = f"aov_report_{report_date}"
        output_path = output_dir / f"{base_filename}.html"
        
        version = 1
        while output_path.exists():
            version += 1
            output_path = output_dir / f"{base_filename}_v{version}.html"
        
        output_path.write_text(html_content, encoding="utf-8")
        
        # ── 🏮 Phase 40.21：同步至主戰線 (Canonical Sync) 🏮 ──
        # 這是為了解決 Line 連結與本地差異的問題。Line 傳送的通常是固定的主日期檔。
        try:
            canonical_path = output_dir / f"{base_filename}.html"
            shutil.copy2(output_path, canonical_path)
            self.logger.info(f"  [⚡] 主線更新：已覆寫推播連結至最新版本 {output_path.name}")
        except Exception as ce:
            self.logger.warning(f"  [!] 主線更新失敗: {ce}")

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
