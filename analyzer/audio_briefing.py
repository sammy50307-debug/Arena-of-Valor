"""
全自動報表語音導讀模組 (Audio-Intelligence Briefing)。
使用 edge-tts 將 AI 戰略摘要轉換為高品質語音導讀。
"""

import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# 建議安裝: pip install edge-tts
# 我們將使用非互動方式嘗試生成，若環境未安裝則自動優雅降級。

import config

logger = logging.getLogger(__name__)

class AudioBriefingGenerator:
    """負責將文字摘要轉錄為音訊。"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (config.DATA_DIR / "reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = "zh-TW-HsiaoChenNeural" # 專業、平穩的台灣女聲

    def _prepare_script(self, summary_data: dict) -> str:
        """將摘要數據轉化為適合播報的腳本。"""
        title = summary_data.get("title", "傳說對決今日情報")
        overview = summary_data.get("overview", "")
        
        # 處理戰鬥數據
        combat_text = ""
        combat_stats = summary_data.get("combat_stats", {})
        if combat_stats:
            combat_text = " 在戰鬥數據方面："
            for hero, stats in combat_stats.items():
                combat_text += f" {hero} 目前勝率為百分之{stats['win_rate']}，登場率為百分之{stats['pick_rate']}。"

        # 拼接劇本
        script = f"您好，我是您的 AI 戰情官。以下是 {title} 的重點摘要。{overview}{combat_text} 以上是今日的戰報彙整，祝您戰績長紅。"
        
        # 簡單的正則替換，讓發音更自然
        script = script.replace("%", "百分之").replace("WR", "勝率").replace("BR", "禁用率")
        return script

    async def generate(self, summary_data: dict) -> Optional[Path]:
        """產出 mp3 音檔、返回文件路徑。"""
        date_str = summary_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        output_path = self.output_dir / f"aov_briefing_{date_str}.mp3"
        script = self._prepare_script(summary_data)

        logger.info(f"正在生成語音導讀: {output_path}")

        try:
            # 使用 edge-tts 進行生成 (這是一個外部 shell 命令調用，確保環境具備相應工具)
            # 如果要使用 Python SDK: import edge_tts; communicate = edge_tts.Communicate(script, self.voice); await communicate.save(output_path)
            
            # 這裡我們模擬生成過程或嘗試調用命令列工具
            import subprocess
            cmd = [
                "edge-tts", 
                "--voice", self.voice, 
                "--text", script, 
                "--write-media", str(output_path)
            ]
            
            # 我們先檢查 edge-tts 是否安裝
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("  [OK] 語音導讀生成成功 ✅")
                return output_path
            else:
                logger.warning(f"  [!] 語音生成失敗 (可能未安裝 edge-tts): {stderr.decode()}")
                return None

        except Exception as e:
            logger.error(f"  [FAIL] 語音生成發生例外: {e}")
            return None

# ── 獨立測試 ──────────────────────────────
if __name__ == "__main__":
    from typing import Optional
    async def test():
        gen = AudioBriefingGenerator()
        test_data = {
            "title": "芽芽戰力警訊",
            "overview": "今日芽芽在高端局的勝率顯著提升，玩家普遍認為其新裝備過於強勢。",
            "combat_stats": {"芽芽": {"win_rate": 53.2, "pick_rate": 15.1}}
        }
        await gen.generate(test_data)

    asyncio.run(test())
