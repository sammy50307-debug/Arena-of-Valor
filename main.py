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
from dataclasses import asdict

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
from scrapers.hero_stats import HeroStatsScraper
from analyzer.sentiment import SentimentAnalyzer
from analyzer.audio_briefing import AudioBriefingGenerator
from analyzer.heatmap import HeatmapAnalyzer
from analyzer.history import HistoryResolver
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


async def github_backup_job(is_manual: bool = False):
    """自動推播報告到 GitHub 的部署任務。"""
    prefix = "🚀 [自動部署]" if not is_manual else "📦 [每日備份]"
    logger.info("=" * 60)
    logger.info(f" {prefix} 啟動 GitHub 雲端同步程序...")
    logger.info("=" * 60)
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 確保 git 在系統環境變數中
        subprocess.run(["git", "add", "data/reports/"], check=True, capture_output=True)
        
        # 專業變動探測：diff --cached --quiet (exit 1 代表有變動)
        has_changes = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
        
        if not has_changes:
            logger.info("  ℹ️ 雲端已是最新同步狀態，無需重複上傳。")
            return

        commit_msg = f"docs: 戰略報告自動同步 {timestamp}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        
        logger.info(f"  ✅ GitHub 同步完成！報表已部署至雲端。")
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8', errors='ignore') if e.output else ""
        if "nothing to commit" in output:
            logger.info("  ℹ️ 今日報告內容無變動，略過同步。")
        else:
            logger.error(f"  ❌ GitHub 同步失敗: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")
    except Exception as e:
        logger.error(f"  ❌ GitHub 同步例外: {e}")


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
async def run_pipeline(dry_run: bool = False, showcase: bool = False):
    """
    執行完整的監測流程：Tavily 搜集 → Gemini 分析 → 報告 → 推播。
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(" AoV 輿情監測流程啟動 (Tavily + Gemini)")
    logger.info(f"   時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   關鍵字: {config.SEARCH_KEYWORDS}")
    logger.info(f"   模式: {'演示模式 (Showcase)' if showcase else ('乾跑 (不推播)' if dry_run else '完整流程')}")
    logger.info("=" * 60)

    # ── Step 1：情報搜集 ────────────────────────────────
    all_results = []
    
    if showcase:
        logger.info(" [!] 偵測到演示模式：啟用高品質數據備援機制 (12 條精選輿情)...")
        from scrapers.tavily_searcher import SearchResult
        all_results = [
            SearchResult(title="【傳說對決】新版芽芽輔助教學：如何成為隊友的最強護盾？", content="這波芽芽的護盾增強真的太有感了！在排位賽中幾乎是非 Ban 即選的存在。本文詳細解析如何利用被動進行極致換血...", url="https://example.com/aov-yaya-guide", region="TW", platform="Website", score=0.98),
            SearchResult(title="2026 傳說職業聯賽：台服戰隊奪冠後，玩家聲量爆棚！", content="台服戰隊在最後一波團戰中展現了驚人的韌性。玩家們紛紛表示這是有史以來最精彩的一場決賽。台服環境明顯回溫。", url="https://example.com/aov-pro-league", region="TW", platform="Facebook", score=0.95),
            SearchResult(title="[討論] 芽芽目前的裝備選擇？坦裝還是全法？", content="自從改版後，全法芽芽的出裝週期太長，推薦大家還是走半坦，不僅能抗裝還能維持護盾厚度。鄉民們討論度極高。", url="https://example.com/ptt-aov-yaya", region="TW", platform="Forum", score=0.92),
            SearchResult(title="官方更新：台服平衡調整公告，多名射手遭削弱", content="針對台服高端局節奏過快的問題，官方今日宣布對勇、凡恩等射手進行削弱。社群情緒目前呈現兩極化反應。", url="https://example.com/aov-patch-notes", region="TW", platform="Website", score=0.90),
            SearchResult(title="【繪畫】萌系芽芽：櫻花下的守護者", content="這是我為芽芽畫的新造型想像圖，背景就是櫻花落下的樣子，希望官方能出這套造型！下方社群好評不斷。", url="https://example.com/art-yaya", region="TW", platform="Instagram", score=0.88),
            SearchResult(title="職業聯賽戰術解析：芽芽與克里希的配合機制", content="在最新的 GCS 比賽中，這種配合展現了強大的地圖控制力。分析師認為這將成為本季台服的主流體系。", url="https://example.com/tactics-yaya", region="TW", platform="Website", score=0.85),
            SearchResult(title="[抱怨] 芽芽掛機怎麼檢舉？這機制有問題吧？", content="真的很討厭隊友選了芽芽結果整場不放技能。希望官方能加強檢舉系統。此帖引發了大量共鳴。", url="https://example.com/rant-yaya", region="TW", platform="Forum", score=0.83),
            SearchResult(title="新角色預告：來自迷霧島的守護靈", content="官方釋出了神秘的剪影，看起來與芽芽的背景故事有關。台服玩家對此充滿期待。", url="https://example.com/new-hero-teased", region="TW", platform="Facebook", score=0.80),
            SearchResult(title="新手入坑指南：如何從零開始自學芽芽？", content="本指南專為那些喜歡輔助位置的新人設計。詳細列出了技能加點與遊走路線。是目前新手圈最熱門的文章。", url="https://example.com/newbie-guide", region="TW", platform="Website", score=0.78),
            SearchResult(title="【實測】芽芽被動觸發頻率對會戰的影響", content="經過數據測試，在 40% 冷卻縮減下，芽芽能提供幾乎不間斷的護盾。這在後期是大優勢。", url="https://example.com/test-yaya", region="TW", platform="YouTube", score=0.75),
            SearchResult(title="台服社群盃報名開始：芽芽禁選令引發熱議", content="為了比賽多樣性，社群盃宣佈暫時禁選芽芽。這引發了輔助玩家的廣泛討論。", url="https://example.com/community-cup", region="TW", platform="Facebook", score=0.72),
            SearchResult(title="[速報] 傳說對決台服下載量突破新高", content="受惠於近期的大型聯名活動，台服重回應用商店榜首。玩家回流速度驚人。", url="https://example.com/download-record", region="TW", platform="Website", score=0.70)
        ]
    else:
        logger.info(" Step 1/4: 開始使用 Tavily 搜集全球區域情報...")
        searcher = TavilySearcher()
        try:
            all_results = await searcher.search(max_results_per_region=3)
        except Exception as e:
            logger.error(f"  [FAIL] 全球情報搜集失敗: {e}")
            return

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
    stats_scraper = HeroStatsScraper()

    try:
        # 同步抓取戰鬥數據
        combat_stats = await stats_scraper.fetch_watchlist_stats()
        
        analyzed_posts = await analyzer.analyze_posts(all_results)
        daily_summary = await analyzer.generate_daily_summary(analyzed_posts)
        
        # ── Step 2.2：計算歷史趨勢 (Phase 29) ──────────
        logger.info(" Step 2.2/4: 啟動情報時光機，計算週趨勢...")
        history_gen = HistoryResolver()
        daily_summary["history_delta"] = history_gen.resolve_trends(daily_summary)
        
        # 將戰鬥數據注入 summary 供 UI 顯示
        daily_summary["combat_stats"] = {name: asdict(s) for name, s in combat_stats.items()}
        
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

    # ── Step 2.5：生成語音導讀 (Phase 27) ──────────────
    logger.info(" Step 2.5/4: 生成語音導讀音檔...")
    audio_gen = AudioBriefingGenerator()
    audio_url = None
    try:
        audio_path = await audio_gen.generate(daily_summary)
        if audio_path and getattr(config, "GITHUB_PAGES_URL", None):
            base_url = config.GITHUB_PAGES_URL.rstrip("/")
            audio_url = f"{base_url}/data/reports/{audio_path.name}"
            daily_summary["audio_url"] = audio_url
    except Exception as e:
        logger.error(f"  [FAIL] 語音生成失敗: {e}")

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
            
            # 額外推送語音戰報 (Phase 27)
            date_str = daily_summary.get("date", datetime.now().strftime("%Y-%m-%d"))
            audio_path = config.DATA_DIR / "reports" / f"aov_briefing_{date_str}.mp3"
            if audio_path.exists():
                await telegram_bot.send_voice_briefing(audio_path)
        except Exception as e:
            logger.error(f"  [FAIL] Telegram 推播例外: {e}")

    # ── 流程結束 ──────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"[*] 流程完成！耗時 {elapsed:.1f} 秒")
    logger.info(f"   搜集: {len(all_results)} 筆 | 分析: {len(analyzed_posts)} 筆")
    logger.info("=" * 60)

    # ────── 雲端即時部署 (New) ──────────────────────────────────
    if not dry_run:
        await github_backup_job(is_manual=False)


# ── CLI 與排程 ────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(
        description="AoV 自動化輿情監測系統 (Tavily + Gemini)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--run-now", action="store_true", help="立即執行")
    parser.add_argument("--dry-run", action="store_true", help="立即執行但不推播")
    parser.add_argument("--showcase", action="store_true", help="演示模式：使用高品質預設數據確保產出完美")
    args = parser.parse_args()

    setup_logging()

    if args.run_now or args.dry_run or args.showcase:
        mode_text = "手動執行"
        if args.dry_run: mode_text = "乾跑模式 (無推播)"
        if args.showcase: mode_text = "演示模式 (高解析度備援)"
        
        console.print(
            f"\n[bold cyan] AoV 輿情監測系統[/bold cyan] — {mode_text}\n"
        )
        # 解除綁定：除非用戶明確下 --dry-run，否則 showcase 也要推播通知以展現全功
        await run_pipeline(dry_run=args.dry_run, showcase=args.showcase)
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
        logger.info(f"排程已啟動，系統正式服役。")
        
        # 保持異步循環在 Python 3.8 穩定運行
        while True:
            await asyncio.sleep(1000)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("系統已手動關閉。")
    except Exception as e:
        logger.exception(f"系統運行發生未知錯誤: {e}")
