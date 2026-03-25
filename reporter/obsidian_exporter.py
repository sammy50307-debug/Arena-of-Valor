import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ObsidianExporter:
    """Â∞áÊ??•Ëºø?ÖÊ?Ë¶ÅÂåØ?∫ÁÇ∫ Obsidian Markdown ?ºÂ???""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.logger = logging.getLogger(f"{__name__}.ObsidianExporter")

    def export(self, summary: dict) -> bool:
        """
        Â∞áÊ?Ë¶ÅÊ??ÖÊ? Markdown ÂØ´ÂÖ•?ÆÊ? Obsidian Ë≥áÊ?Â§æ„Ä?        """
        if not self.vault_path:
            self.logger.error("?™Ë®≠ÂÆ?OBSIDIAN_VAULT_PATHÔºåÁÑ°Ê≥ïÈÄ≤Ë? Obsidian ?ô‰ªΩ??)
            return False

        vault_dir = Path(self.vault_path)
        if not vault_dir.exists():
            try:
                vault_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"?°Ê?Âª∫Á? Obsidian Ë≥áÊ?Â§?{self.vault_path}: {e}")
                return False

        date = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # ÁµÑÂ? Markdown ?ßÂÆπ
        md_content = self._build_markdown(summary, date)
        
        file_name = f"?? AoV ËºøÊ??±Â? {date}.md"
        file_path = vault_dir / file_name
        
        try:
            file_path.write_text(md_content, encoding="utf-8")
            self.logger.info(f"?êÂ??ô‰ªΩ Markdown ??Obsidian: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"ÂØ´ÂÖ• Obsidian Markdown ?ºÁ??ØË™§: {e}")
            return False

    def _build_markdown(self, summary: dict, date: str) -> str:
        """?¢Á??´Ê? YAML Frontmatter ??Obsidian Á≠ÜË???""
        overview = summary.get("overview", "?°Ë???)
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
        md.append("  - ËºøÊ??ÜÊ?")
        md.append("  - Á≥ªÁµ±?±Â?")
        md.append(f"date: {date}")
        md.append("---")
        md.append("")
        
        md.append(f"# ?éÆ ?≥Ë™™Â∞çÊ±∫ ÊØèÊó•ËºøÊ??±Â? ({date})")
        md.append("")
        
        md.append(f"> [!info] **Á∏ΩË≤º?áÂ??êÊï∏:** {total} ÁØ?)
        md.append(f"> ?? Ê≠?ù¢: {pos} | ?? Ë≤†Èù¢: {neg} | ?? ‰∏≠ÊÄ? {neu}")
        md.append("")
        
        md.append("## ?? Á∏ΩÈ?Ê¶ÇËø∞")
        md.append(f"{overview}")
        md.append("")
        
        # ?±È?Ë©±È?
        hot_topics = summary.get("hot_topics", [])
        if hot_topics:
            md.append("## ?î• ?±È?Ë©±È?")
            for topic in hot_topics:
                name = topic.get("topic", "N/A")
                sent = topic.get("sentiment", "neutral")
                emoji = {"positive": "?ü¢", "negative": "?î¥", "neutral": "?ü°"}.get(sent, "??)
                md.append(f"- {emoji} **{name}**")
            md.append("")
            
        # Ê¥ªÂ??µÊ∏¨
        events = summary.get("detected_events", [])
        if events:
            md.append("## ?ì¢ ?µÊ∏¨?∞Á?Ê¥ªÂ??á‰?‰ª?)
            for event in events:
                md.append(f"- **{event.get('name', 'N/A')}** ({event.get('type', '')})")
            md.append("")
            
        # Ë≠¶Ë??áÂª∫Ë≠?        alerts = summary.get("alerts", [])
        if alerts:
            md.append("## ?ö® ?çË?Ë≠¶Ë?")
            for alert in alerts:
                md.append(f"- ?†Ô? {alert}")
            md.append("")
            
        recommendation = summary.get("recommendation", "")
        if recommendation:
            md.append("## ?í° AI Âª∫Ë≠∞")
            md.append(f"{recommendation}")
            md.append("")
            
        # Á≤æÈÅ∏???
        top_links = summary.get("top_links", [])
        if top_links:
            md.append("## ?? Á≤æÈÅ∏?ÖÂ†±‰æÜÊ?")
            for link in top_links:
                md.append(f"- [{link['platform']}] [{link['title']}]({link['url']})")
                
        return "\n".join(md)
