import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ObsidianExporter:
    """將每日輿情摘要匯出為 Obsidian Markdown 格式。"""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.logger = logging.getLogger(f"{__name__}.ObsidianExporter")

    def export(self, summary: dict) -> bool:
        """
        將摘要打包成 Markdown 寫入目標 Obsidian 資料夾。
        """
        if not self.vault_path:
            self.logger.error("未設定 OBSIDIAN_VAULT_PATH，無法進行 Obsidian 備份。")
            return False

        vault_dir = Path(self.vault_path)
        if not vault_dir.exists():
            try:
                vault_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"無法建立 Obsidian 資料夾 {self.vault_path}: {e}")
                return False

        date = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 組合 Markdown 內容
        md_content = self._build_markdown(summary, date)
        
        file_name = f"📊 AoV 輿情報告 {date}.md"
        file_path = vault_dir / file_name
        
        try:
            file_path.write_text(md_content, encoding="utf-8")
            self.logger.info(f"成功備份 Markdown 至 Obsidian: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"寫入 Obsidian Markdown 發生錯誤: {e}")
            return False

    def _build_markdown(self, summary: dict, date: str) -> str:
        """產生含有 YAML Frontmatter 的 Obsidian 筆記。"""
        overview = summary.get("overview", "無資料")
        sentiment = summary.get("sentiment_distribution", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        total = pos + neg + neu

        md = []
        # Obsidian Frontmatter
        md.append("---")
        md.append("tags:")
        md.append("  - AoV")
        md.append("  - 輿情分析")
        md.append("  - 系統報告")
        md.append(f"date: {date}")
        md.append("---")
        md.append("")
        
        md.append(f"# 🎮 傳說對決 每日輿情報告 ({date})")
        md.append("")
        
        md.append(f"> [!info] **總貼文分析數:** {total} 篇")
        md.append(f"> 👍 正面: {pos} | 👎 負面: {neg} | 😐 中性: {neu}")
        md.append("")
        
        md.append("## 📝 總體概述")
        md.append(f"{overview}")
        md.append("")
        
        # 熱門話題
        hot_topics = summary.get("hot_topics", [])
        if hot_topics:
            md.append("## 🔥 熱門話題")
            for topic in hot_topics:
                name = topic.get("topic", "N/A")
                sent = topic.get("sentiment", "neutral")
                emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(sent, "⚪")
                md.append(f"- {emoji} **{name}**")
            md.append("")
            
        # 活動偵測
        events = summary.get("detected_events", [])
        if events:
            md.append("## 📢 偵測到的活動與事件")
            for event in events:
                md.append(f"- **{event.get('name', 'N/A')}** ({event.get('type', '')})")
            md.append("")
            
        # 警訊與建議
        alerts = summary.get("alerts", [])
        if alerts:
            md.append("## 🚨 重要警訊")
            for alert in alerts:
                md.append(f"- ⚠️ {alert}")
            md.append("")
            
        recommendation = summary.get("recommendation", "")
        if recommendation:
            md.append("## 💡 AI 建議")
            md.append(f"{recommendation}")
            md.append("")
            
        # 精選連結
        top_links = summary.get("top_links", [])
        if top_links:
            md.append("## 🔗 精選情報來源")
            for link in top_links:
                md.append(f"- [{link['platform']}] [{link['title']}]({link['url']})")
                
        return "\n".join(md)
