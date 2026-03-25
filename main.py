"""
AoV 自動化輿情監測系統 — 主程式入口

功能：
  1. 使用 APScheduler 設定每日 09:00 排程
  2. 串接完整流程：Tavily 搜集 → Gemini 分析 → 報告 → 推播
  3. 支援 --run-now 手動立即執行
  4. 支援 --dry-run 不推播，僅產出報告

用法：
  python main.py             # 啟動排程（每日 09:00 執行）
  python main.py --run-now   # 立即執行一輪完整流程
  python main.py --dry-run   # 立即執行但不推播
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

# ── Windows 終端 UTF-8 強制修正 (最強版) ───────────────
# 解決 PowerShell / CMD 預設使用 Big5 (CP950) 導致中文亂碼的問題
# 這段必須在任何 print / logging 之前執行
if sys.platform == "win32":
    # 1. 強制設定 Windows Console Code Page 為 UTF-8
    os.system("chcp 65001 > nul 2>&1")
    # 2. 設定環境變數，影響子行程
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # 3. 重新設定 Python 的標準輸出/錯誤串流
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

# 4. 建立 Rich Console 時也強制指定 UTF-8 輸出管道
console = Console(file=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace"))


# ── Logging 設定 ─────────────────────────────────────
def setup_logging():
    """設定雙通道日誌：檔案 + 終端（含 rich 美化）。"""
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

    # 降低第三方套件的日誌等級
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger("aov_monitor")


async def github_backup_job():
    """自動推播報告到 GitHub 的排程任務。"""
    logger.info("============================================================")
    logger.info(" 🚀 開始執行每日 GitHub 自動備份任務 (凌晨 02:00)")
    logger.info("============================================================")
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "add", "data/reports/"], check=True, capture_output=True)
        
        commit_msg = f"chore: 機器人自動備份報告 {timestamp}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        
        logger.info(f"  ✅ GitHub 備份完成！Commit: {commit_msg}")
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8', errors='ignore') if e.output else ""
        if "nothing to commit" in output or "無檔案要提交" in output:
            logger.info("  ℹ️ 今日沒有新報告，無需備份。")
        else:
            logger.error(f"  ❌ GitHub 備份失敗: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")


async def obsidian_backup_job():
    """自動備份報告到 Obsidian 的排程任務。"""
    logger.info("============================================================")
    logger.info(" 📓 開始執行每日 Obsidian 備份任務 (凌晨 02:00)")
    logger.info("============================================================")
    
    if not config.OBSIDIAN_VAULT_PATH:
        logger.warning("  [SKIP] 尚未設定 OBSIDIAN_VAULT_PATH，略過備份。")
        return
        
    try:
        # 尋找最新的 analysis JSON
        analysis_files = sorted(config.DATA_DIR.glob("analysis_*.json"))
        if not analysis_files:
            logger.warning("  [SKIP] 沒有找到任何 analysis_*.json 可供備份。")
            return
            
        latest_file = analysis_files[-1]
        summary_data = json.loads(latest_file.read_text(encoding="utf-8"))
        
        # 使用 Exporter 轉檔寫入
        exporter = ObsidianExporter(vault_path=config.OBSIDIAN_VAULT_PATH)
        success = exporter.export(summary_data)
        
        if success:
            logger.info("  ✅ Obsidian 備份完成！")
        else:
            logger.error("  ❌ Obsidian 備份失敗。")
            
    except Exception as e:
        logger.error(f"  ❌ Obsidian 備份發生例外錯誤: {e}")

# ── 核心流程 ─────────────────────────────────────────
async def run_pipeline(dry_run: bool = False):
    """
    執行完整的監測流程：Tavily 搜集 → Gemini 分析 → 報告 → 推播。
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(" AoV 輿情監測流程啟動 (Tavily + Gemini)")
    logger.info(f"   時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   關鍵字: {config.SEARCH_KEYWORDS}")
    logger.info(f"   模式: {'乾跑 (不推播)' if dry_run else '完整流程'}")
    logger.info("=" * 60)

    # ── Step 1：情報搜集 (Tavily) ──────────────────────
    logger.info(" Step 1/4: 開始使用 Tavily 搜集情報...")

    searcher = TavilySearcher()
    try:
        all_results = await searcher.search(
            keywords=config.SEARCH_KEYWORDS,
            max_results_per_keyword=3,  # 控制數量避免超過 LLM 免費限制 15 RPM
        )
    except Exception as e:
        logger.error(f"  [FAIL] 搜集失敗: {e}")
        all_results = []

    if not all_results:
        logger.warning("[!] 沒有搜集到任何資料，流程提前結束。")
        return

    # 儲存原始資料
    raw_data_path = config.DATA_DIR / f"raw_{datetime.now().strftime('%Y%m%d')}.json"
    raw_data_path.write_text(
        json.dumps(
            [r.to_dict() for r in all_results],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info(f"   原始搜集資料已儲存: {raw_data_path}")

    # ── Step 2：AI 分析 (Gemini) ───────────────────────
    logger.info(" Step 2/4: Gemini AI 分析中...")

    analyzer = SentimentAnalyzer()

    try:
        analyzed_posts = await analyzer.analyze_posts(all_results)
        daily_summary = await analyzer.generate_daily_summary(analyzed_posts)
        
        # 將專屬網頁連結注入到 summary 中
        if getattr(config, "GITHUB_PAGES_URL", None):
            base_url = config.GITHUB_PAGES_URL.rstrip("/")
            date_str = daily_summary.get("date", datetime.now().strftime("%Y-%m-%d"))
            daily_summary["report_url"] = f"{base_url}/data/reports/aov_report_{date_str}.html"
            
        logger.info("  [OK] AI 分析完成")
    except Exception as e:
        logger.error(f"  [FAIL] AI 分析失敗: {e}")
        daily_summary = analyzer._empty_summary()
        analyzed_posts = []

    # 儲存分析結果
    analysis_path = config.DATA_DIR / f"analysis_{datetime.now().strftime('%Y%m%d')}.json"
    analysis_path.write_text(
        json.dumps(daily_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"   分析結果已儲存: {analysis_path}")

    # ── Step 3：產出報告 ──────────────────────────────
    logger.info(" Step 3/4: 產出視覺化報告...")

    try:
        generator = ReportGenerator()
        report_path = generator.generate(daily_summary, analyzed_posts)
        logger.info(f"  [OK] 報告已生成: {report_path}")
    except Exception as e:
        logger.error(f"  [FAIL] 報告生成失敗: {e}")

    # ── Step 4：推播通知 ──────────────────────────────
    if dry_run:
        logger.info(" Step 4/4: 乾跑模式，跳過推播")
        logger.info("   摘要預覽:")
        console.print_json(json.dumps(daily_summary, ensure_ascii=False, indent=2))
    else:
        logger.info(" Step 4/4: 推播通知...")

        # Line 推播
        try:
            line_bot = LineBotNotifier()
            line_ok = await line_bot.send_daily_report(daily_summary)
            logger.info(f"  {'[OK]' if line_ok else '[FAIL]'} Line 推播: {'成功' if line_ok else '失敗'}")
        except Exception as e:
            logger.error(f"  [FAIL] Line 推播例外: {e}")

        # Telegram 推播
        try:
            telegram_bot = TelegramBotNotifier()
            tg_ok = await telegram_bot.send_daily_report(daily_summary)
            logger.info(f"  {'[OK]' if tg_ok else '[FAIL]'} Telegram 推播: {'成功' if tg_ok else '失敗'}")
        except Exception as e:
            logger.error(f"  [FAIL] Telegram 推播例外: {e}")

    # ── 流程結束 ──────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"[*] 流程完成！耗時 {elapsed:.1f} 秒")
    logger.info(f"   搜集: {len(all_results)} 筆 | 分析: {len(analyzed_posts)} 筆")
    logger.info("=" * 60)


# ── CLI 與排程 ────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AoV 自動化輿情監測系統 (Tavily + Gemini)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--run-now", action="store_true", help="立即執行")
    parser.add_argument("--dry-run", action="store_true", help="立即執行但不推播")
    args = parser.parse_args()

    setup_logging()

    if args.run_now or args.dry_run:
        console.print(
            "\n[bold cyan] AoV 輿情監測系統[/bold cyan] — "
            f"{'乾跑模式 (無推播)' if args.dry_run else '手動執行'}\n"
        )
        asyncio.run(run_pipeline(dry_run=args.dry_run))
    else:
        console.print("\n[bold cyan] AoV 輿情監測系統[/bold cyan] — 排程模式\n")
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            run_pipeline,
            trigger=CronTrigger(
                hour=config.SCHEDULE_HOUR,
                minute=config.SCHEDULE_MINUTE,
                timezone=config.TIMEZONE,
            ),
            id="daily_monitor",
            name="每日輿情監測",
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
            name="每日 GitHub 備份",
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
            name="每日 Obsidian 備份",
            misfire_grace_time=3600,
        )

        scheduler.start()
        logger.info(f"排程已啟動，下一次監測時間: {scheduler.get_job('daily_monitor').next_run_time}")
        logger.info(f"下一次備份時間: {scheduler.get_job('github_backup').next_run_time}")

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            logger.info("排程已關閉。")

if __name__ == "__main__":
    main()
