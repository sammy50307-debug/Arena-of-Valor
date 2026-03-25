import asyncio
import io
import json
import os
import sys
from pathlib import Path

# ?Ä?Ä Windows ÁµÇÁ´Ø UTF-8 Âº∑Âà∂‰øÆÊ≠£ (?ÄÂº∑Á?) ?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from notifier.line_bot import LineBotNotifier

async def main():
    try:
        # Find the latest analysis JSON file
        data_dir = Path(__file__).resolve().parent / "data"
        analysis_files = sorted(data_dir.glob("analysis_*.json"))
        
        if not analysis_files:
            print("?æ‰??∞‰ªª‰Ω?analysis_*.json Ê™îÊ???)
            return
            
        latest_file = analysis_files[-1]
        print(f"ËÆÄ?ñÊ?Ê°àÔ?{latest_file.name} ...")
        
        daily_summary = json.loads(latest_file.read_text(encoding="utf-8"))
        
        # Send to LINE
        line_bot = LineBotNotifier()
        success = await line_bot.send_daily_report(daily_summary)
        
        if success:
            print("??LINE ?®Êí≠Ê∏¨Ë©¶?êÂ?Ôº?)
        else:
            print("??LINE ?®Êí≠Ê∏¨Ë©¶Â§±Ê?ÔºåË?Ê™¢Êü• Token ??User ID??)
            
    except Exception as e:
        print(f"???ØË™§Ôºö{e}")

if __name__ == "__main__":
    asyncio.run(main())
