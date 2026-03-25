"""
AoV ?ªå??–è¼¿?…ç›£æ¸¬ç³»çµ???ä¸»ç?å¼å…¥??

?Ÿèƒ½ï¼?
  1. ä½¿ç”¨ APScheduler è¨­å?æ¯æ—¥ 09:00 ?’ç?
  2. ä¸²æ¥å®Œæ•´æµç?ï¼šTavily ?œé? ??Gemini ?†æ? ???±å? ???¨æ’­
  3. ?¯æ´ --run-now ?‹å?ç«‹å³?·è?
  4. ?¯æ´ --dry-run ä¸æ¨?­ï??…ç”¢?ºå ±??

?¨æ?ï¼?
  python main.py             # ?Ÿå??’ç?ï¼ˆæ???09:00 ?·è?ï¼?
  python main.py --run-now   # ç«‹å³?·è?ä¸€è¼ªå??´æ?ç¨?
  python main.py --dry-run   # ç«‹å³?·è?ä½†ä??¨æ’­
"""

import argparse
import asyncio
import io
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ?€?€ Windows çµ‚ç«¯ UTF-8 å¼·åˆ¶ä¿®æ­£ (?€å¼·ç?) ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
# è§?±º PowerShell / CMD ?è¨­ä½¿ç”¨ Big5 (CP950) å°è‡´ä¸­æ?äº‚ç¢¼?„å?é¡?
# ?™æ®µå¿…é??¨ä»»ä½?print / logging ä¹‹å??·è?
if sys.platform == "win32":
    # 1. å¼·åˆ¶è¨­å? Windows Console Code Page ??UTF-8
    os.system("chcp 65001 > nul 2>&1")
    # 2. è¨­å??°å?è®Šæ•¸ï¼Œå½±?¿å?è¡Œç?
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # 3. ?æ–°è¨­å? Python ?„æ?æº–è¼¸???¯èª¤ä¸²æ?
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console
from rich.logging import RichHandler

import config
from scrapers.tavily_searcher import TavilySearcher
from scrapers.apify_scraper import ApifyInstagramScraper
from analyzer.sentiment import SentimentAnalyzer
from reporter.generator import ReportGenerator
from reporter.obsidian_exporter import ObsidianExporter
from notifier.line_bot import LineBotNotifier
from notifier.telegram_bot import TelegramBotNotifier

# 4. å»ºç? Rich Console ?‚ä?å¼·åˆ¶?‡å? UTF-8 è¼¸å‡ºç®¡é?
console = Console(file=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace"))


# ?€?€ Logging è¨­å? ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
def setup_logging():
    """è¨­å??™é€šé??¥è?ï¼šæ?æ¡?+ çµ‚ç«¯ï¼ˆå« rich ç¾å?ï¼‰ã€?""
    log_file = config.LOGS_DIR / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=False,
            ),
        ],
    )

    # ?ä?ç¬¬ä??¹å?ä»¶ç??¥è?ç­‰ç?
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger("aov_monitor")


async def github_backup_job():
    """?ªå??¨æ’­?±å???GitHub ?„æ?ç¨‹ä»»?™ã€?""
    logger.info("============================================================")
    logger.info(" ?? ?‹å??·è?æ¯æ—¥ GitHub ?ªå??™ä»½ä»»å? (?Œæ™¨ 02:00)")
    logger.info("============================================================")
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "add", "data/reports/"], check=True, capture_output=True)
        
        commit_msg = f"chore: æ©Ÿå™¨äººè‡ª?•å?ä»½å ±??{timestamp}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        
        logger.info(f"  ??GitHub ?™ä»½å®Œæ?ï¼Commit: {commit_msg}")
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8', errors='ignore') if e.output else ""
        if "nothing to commit" in output or "?¡æ?æ¡ˆè??äº¤" in output:
            logger.info("  ?¹ï? ä»Šæ—¥æ²’æ??°å ±?Šï??¡é??™ä»½??)
        else:
            logger.error(f"  ??GitHub ?™ä»½å¤±æ?: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")


async def obsidian_backup_job():
    """?ªå??™ä»½?±å???Obsidian ?„æ?ç¨‹ä»»?™ã€?""
    logger.info("============================================================")
    logger.info(" ?? ?‹å??·è?æ¯æ—¥ Obsidian ?™ä»½ä»»å? (?Œæ™¨ 02:00)")
    logger.info("============================================================")
    
    if not config.OBSIDIAN_VAULT_PATH:
        logger.warning("  [SKIP] å°šæœªè¨­å? OBSIDIAN_VAULT_PATHï¼Œç•¥?å?ä»½ã€?)
        return
        
    try:
        # å°‹æ‰¾?€?°ç? analysis JSON
        analysis_files = sorted(config.DATA_DIR.glob("analysis_*.json"))
        if not analysis_files:
            logger.warning("  [SKIP] æ²’æ??¾åˆ°ä»»ä? analysis_*.json ?¯ä??™ä»½??)
            return
            
        latest_file = analysis_files[-1]
        summary_data = json.loads(latest_file.read_text(encoding="utf-8"))
        
        # ä½¿ç”¨ Exporter è½‰æ?å¯«å…¥
        exporter = ObsidianExporter(vault_path=config.OBSIDIAN_VAULT_PATH)
        success = exporter.export(summary_data)
        
        if success:
            logger.info("  ??Obsidian ?™ä»½å®Œæ?ï¼?)
        else:
            logger.error("  ??Obsidian ?™ä»½å¤±æ???)
            
    except Exception as e:
        logger.error(f"  ??Obsidian ?™ä»½?¼ç?ä¾‹å??¯èª¤: {e}")

# ?€?€ ?¸å?æµç? ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
async def run_pipeline(dry_run: bool = False):
    """
    ?·è?å®Œæ•´?„ç›£æ¸¬æ?ç¨‹ï?Tavily ?œé? ??Gemini ?†æ? ???±å? ???¨æ’­??
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(" AoV è¼¿æ???¸¬æµç??Ÿå? (Tavily + Gemini)")
    logger.info(f"   ?‚é?: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   ?œéµå­? {config.SEARCH_KEYWORDS}")
    logger.info(f"   æ¨¡å?: {'ä¹¾è? (ä¸æ¨??' if dry_run else 'å®Œæ•´æµç?'}")
    logger.info("=" * 60)

    # ?€?€ Step 1ï¼šæ??±æ???(Tavily) ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
    logger.info(" Step 1/4: ?‹å?ä½¿ç”¨ Tavily ?œé??…å ±...")

    searcher = TavilySearcher()
    try:
        all_results = await searcher.search(
            keywords=config.SEARCH_KEYWORDS,
            max_results_per_keyword=3,  # ?§åˆ¶?¸é??¿å?è¶…é? LLM ?è²»?åˆ¶ 15 RPM
        )
    except Exception as e:
        logger.error(f"  [FAIL] ?œé?å¤±æ?: {e}")
        all_results = []

    if not all_results:
        logger.warning("[!] æ²’æ??œé??°ä»»ä½•è??™ï?æµç??å?çµæ???)
        return

    # ?²å??Ÿå?è³‡æ?
    raw_data_path = config.DATA_DIR / f"raw_{datetime.now().strftime('%Y%m%d')}.json"
    raw_data_path.write_text(
        json.dumps(
            [r.to_dict() for r in all_results],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info(f"   ?Ÿå??œé?è³‡æ?å·²å„²å­? {raw_data_path}")

    # ?€?€ Step 2ï¼šAI ?†æ? (Gemini) ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
    logger.info(" Step 2/4: Gemini AI ?†æ?ä¸?..")

    analyzer = SentimentAnalyzer()

    try:
        analyzed_posts = await analyzer.analyze_posts(all_results)
        daily_summary = await analyzer.generate_daily_summary(analyzed_posts)
        
        # å°‡å?å±¬ç¶²?é€??æ³¨å…¥??summary ä¸?
        if getattr(config, "GITHUB_PAGES_URL", None):
            base_url = config.GITHUB_PAGES_URL.rstrip("/")
            date_str = daily_summary.get("date", datetime.now().strftime("%Y-%m-%d"))
            daily_summary["report_url"] = f"{base_url}/data/reports/aov_report_{date_str}.html"
            
        logger.info("  [OK] AI ?†æ?å®Œæ?")
    except Exception as e:
        logger.error(f"  [FAIL] AI ?†æ?å¤±æ?: {e}")
        daily_summary = analyzer._empty_summary()
        analyzed_posts = []

    # ?²å??†æ?çµæ?
    analysis_path = config.DATA_DIR / f"analysis_{datetime.now().strftime('%Y%m%d')}.json"
    analysis_path.write_text(
        json.dumps(daily_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"   ?†æ?çµæ?å·²å„²å­? {analysis_path}")

    # ?€?€ Step 3ï¼šç”¢?ºå ±???€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
    logger.info(" Step 3/4: ?¢å‡ºè¦–è¦º?–å ±??..")

    try:
        generator = ReportGenerator()
        report_path = generator.generate(daily_summary, analyzed_posts)
        logger.info(f"  [OK] ?±å?å·²ç??? {report_path}")
    except Exception as e:
        logger.error(f"  [FAIL] ?±å??Ÿæ?å¤±æ?: {e}")

    # ?€?€ Step 4ï¼šæ¨?­é€šçŸ¥ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
    if dry_run:
        logger.info(" Step 4/4: ä¹¾è?æ¨¡å?ï¼Œè·³?æ¨??)
        logger.info("   ?˜è??è¦½:")
        console.print_json(json.dumps(daily_summary, ensure_ascii=False, indent=2))
    else:
        logger.info(" Step 4/4: ?¨æ’­?šçŸ¥...")

        # Line ?¨æ’­
        try:
            line_bot = LineBotNotifier()
            line_ok = await line_bot.send_daily_report(daily_summary)
            logger.info(f"  {'[OK]' if line_ok else '[FAIL]'} Line ?¨æ’­: {'?å?' if line_ok else 'å¤±æ?'}")
        except Exception as e:
            logger.error(f"  [FAIL] Line ?¨æ’­ä¾‹å?: {e}")

        # Telegram ?¨æ’­
        try:
            telegram_bot = TelegramBotNotifier()
            tg_ok = await telegram_bot.send_daily_report(daily_summary)
            logger.info(f"  {'[OK]' if tg_ok else '[FAIL]'} Telegram ?¨æ’­: {'?å?' if tg_ok else 'å¤±æ?'}")
        except Exception as e:
            logger.error(f"  [FAIL] Telegram ?¨æ’­ä¾‹å?: {e}")

    # ?€?€ æµç?çµæ? ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"[*] æµç?å®Œæ?ï¼è€—æ? {elapsed:.1f} ç§?)
    logger.info(f"   ?œé?: {len(all_results)} ç­?| ?†æ?: {len(analyzed_posts)} ç­?)
    logger.info("=" * 60)


# ?€?€ CLI ?‡æ?ç¨??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
def main():
    parser = argparse.ArgumentParser(
        description="AoV ?ªå??–è¼¿?…ç›£æ¸¬ç³»çµ?(Tavily + Gemini)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--run-now", action="store_true", help="ç«‹å³?·è?")
    parser.add_argument("--dry-run", action="store_true", help="ç«‹å³?·è?ä½†ä??¨æ’­")
    args = parser.parse_args()

    setup_logging()

    if args.run_now or args.dry_run:
        console.print(
            "\n[bold cyan] AoV è¼¿æ???¸¬ç³»çµ±[/bold cyan] ??"
            f"{'ä¹¾è?æ¨¡å? (?¡æ¨??' if args.dry_run else '?‹å??·è?'}\n"
        )
        asyncio.run(run_pipeline(dry_run=args.dry_run))
    else:
        console.print("\n[bold cyan] AoV è¼¿æ???¸¬ç³»çµ±[/bold cyan] ???’ç?æ¨¡å?\n")
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            run_pipeline,
            trigger=CronTrigger(
                hour=config.SCHEDULE_HOUR,
                minute=config.SCHEDULE_MINUTE,
                timezone=config.TIMEZONE,
            ),
            id="daily_monitor",
            name="æ¯æ—¥è¼¿æ???¸¬",
            misfire_grace_time=3600,
        )

        scheduler.add_job(
            github_backup_job,
            trigger=CronTrigger(
                hour=2,
                minute=0,
                timezone=config.TIMEZONE,
            ),
            id="github_backup",
            name="æ¯æ—¥ GitHub ?™ä»½",
            misfire_grace_time=3600,
        )

        scheduler.add_job(
            obsidian_backup_job,
            trigger=CronTrigger(
                hour=2,
                minute=0,
                timezone=config.TIMEZONE,
            ),
            id="obsidian_backup",
            name="æ¯æ—¥ Obsidian ?™ä»½",
            misfire_grace_time=3600,
        )

        scheduler.start()
        logger.info(f"?’ç?å·²å??•ï?ä¸‹ä?æ¬¡ç›£æ¸¬æ??? {scheduler.get_job('daily_monitor').next_run_time}")
        logger.info(f"ä¸‹ä?æ¬¡å?ä»½æ??? {scheduler.get_job('github_backup').next_run_time}")

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            logger.info("?’ç?å·²é??‰ã€?)

if __name__ == "__main__":
    main()
