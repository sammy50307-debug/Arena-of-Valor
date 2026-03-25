import asyncio
import json
import os
import sys
from pathlib import Path

# ── Windows 終端 UTF-8 強制修正 ────────────────────────
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from notifier.line_bot import LineBotNotifier

async def main():
    try:
        # Find the latest analysis JSON file
        data_dir = Path(__file__).resolve().parent / "data"
        analysis_files = sorted(data_dir.glob("analysis_*.json"))
        
        if not analysis_files:
            print("找不到任何 analysis_*.json 檔案。")
            return
            
        latest_file = analysis_files[-1]
        print(f"Reading from {latest_file.name} ...")
        
        daily_summary = json.loads(latest_file.read_text(encoding="utf-8"))
        
        # Send to LINE
        line_bot = LineBotNotifier()
        success = await line_bot.send_daily_report(daily_summary)
        
        if success:
            print("LINE 推播測試成功！")
        else:
            print("LINE 推播測試失敗，請檢查 Token 或 User ID。")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
