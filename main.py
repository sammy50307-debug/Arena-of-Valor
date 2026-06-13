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

from __future__ import annotations

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
from scrapers.waterfall_searcher import WaterfallSearcher
from scrapers.dcard_scraper import DcardScraper
from scrapers.bahamut_scraper import BahamutScraper
from scrapers.apify_scraper import ApifyInstagramScraper
from scrapers.hero_stats import HeroStatsScraper
from analyzer.sentiment import SentimentAnalyzer
from analyzer.audio_briefing import AudioBriefingGenerator
from analyzer.heatmap import HeatmapAnalyzer
from analyzer.history import HistoryResolver
from analyzer.local_analyzer import analyze_posts_locally, generate_local_summary
from analyzer.enrichment_queue import build_enrichment_queue, build_enrichment_snapshot, write_enrichment_queue
from analyzer.llm_budget import LLMBudgetManager
from analyzer.run_context import build_run_context, build_source_hash
from analyzer.run_manifest import (
    build_core_contract,
    build_manifest,
    build_quality_tier,
    build_source_quality,
    is_publishable_quality_tier,
    should_promote,
    write_manifest,
)
from analyzer.source_selection import build_source_selection, merge_local_only_entries
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


def evaluate_publish_gate(
    run_date: str,
    mode: str,
    gate_mode: str = "shadow",
    candidate_report_path: Path = None,
    quality_tier: str = "",
) -> tuple[list[str], list]:
    """Evaluate publish gate reasons using report health checks."""
    reasons: list[str] = []
    checks = []
    normalized_gate = str(gate_mode or "shadow").lower()

    if quality_tier:
        if not is_publishable_quality_tier(quality_tier):
            reasons.append("quality_tier is %s (not publishable)" % quality_tier)
            return reasons, checks
    elif mode != "production":
        reasons.append("mode is %s (not production)" % mode)
        return reasons, checks

    try:
        script_dir = Path(__file__).resolve().parent / "scripts"
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from check_daily_report_health import run_checks

        checks = run_checks(
            Path(__file__).resolve().parent,
            run_date,
            expected_mode="production",
            check_git_clean=False,
            check_landing=False,
            expected_report_path=candidate_report_path,
        )
        failed_checks = [c for c in checks if c.failed]
        for c in failed_checks:
            reasons.append("%s: %s" % (c.name, c.detail))
    except Exception as ge:
        reasons.append("gate evaluation error: %s: %s" % (type(ge).__name__, ge))

    if reasons and normalized_gate == "shadow":
        logger.warning("  [GATE][shadow] 發現 %d 項不合格條件（不阻擋本次同步）。", len(reasons))
    elif reasons and normalized_gate == "blocking":
        logger.error("  [GATE][blocking] 發現 %d 項不合格條件（將阻擋本次同步）。", len(reasons))
    else:
        logger.info("  [GATE][%s] publish eligibility 通過。", normalized_gate)

    return reasons, checks


async def github_backup_job(is_manual: bool = False, meta: dict = None):
    """自動推播報告到 GitHub 的部署任務。"""
    prefix = "🚀 [自動部署]" if not is_manual else "📦 [每日備份]"
    logger.info("=" * 60)
    logger.info(f" {prefix} 啟動 GitHub 雲端同步程序...")
    logger.info("=" * 60)

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_paths = ["data/reports/", "data/runs/", "data/llm_cache.json", "index.html"]
        if config.LLM_BUDGET_STATE_FILE.exists():
            add_paths.append("data/llm_budget_state.json")
        subprocess.run(["git", "add", *add_paths], check=True, capture_output=True)

        has_changes = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0

        if not has_changes:
            logger.info("  ℹ️ 雲端已是最新同步狀態，無需重複上傳。")
            return

        # O2：commit msg 帶 mode + cache hit rate
        if meta:
            mode = meta.get("mode", "unknown")
            l1 = meta.get("l1_hits", 0)
            l2 = meta.get("l2_hits", 0)
            total = meta.get("total_calls", 0)
            hit_rate = f"{(l1+l2)/total*100:.0f}%" if total else "N/A"
            commit_msg = (
                f"docs: 戰略報告自動同步 {timestamp} "
                f"[mode:{mode} l1:{l1} l2:{l2} hit:{hit_rate}]"
            )
        else:
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
async def run_pipeline(dry_run: bool = False, showcase: bool = False, force: bool = False):
    """
    執行完整的監測流程：Tavily 搜集 → Gemini 分析 → 報告 → 推播。
    """
    # Lockfile：30 分鐘內成功跑過就跳過，--force 可強制重跑
    if not force and not dry_run and not showcase:
        lf = config.LOCKFILE_PATH
        if lf.exists():
            try:
                from datetime import timezone as _tz
                last_run = datetime.fromisoformat(lf.read_text().strip())
                age_min = (datetime.now(_tz.utc) - last_run).total_seconds() / 60
                if age_min < config.LOCKFILE_COOLDOWN_MINUTES:
                    logger.info(
                        f"[SKIP] 距上次成功跑 {age_min:.1f} 分鐘（< {config.LOCKFILE_COOLDOWN_MINUTES} 分），"
                        "跳過本次執行。使用 --force 強制重跑。"
                    )
                    return
            except Exception:
                pass  # lockfile 格式異常就忽略，繼續跑

    run_context = build_run_context(timezone_name=config.TIMEZONE)
    run_date = run_context.run_date
    compact_run_date = run_context.compact_date
    source_hash = "unknown"
    budget_manager = LLMBudgetManager(
        config.LLM_BUDGET_STATE_FILE,
        max_daily_llm_calls=config.LLM_DAILY_BUDGET,
        cooldown_minutes=config.LLM_BUDGET_COOLDOWN_MINUTES,
        retention_days=config.LLM_BUDGET_RETENTION_DAYS,
    )

    start_time = datetime.now()
    logger.info("=" * 60)
    _llm_label = config.PROVIDER_CHAIN[0][0] if config.PROVIDER_CHAIN else config.PRIMARY_PROVIDER
    logger.info(f" AoV 輿情監測流程啟動 (Tavily + {_llm_label})")
    logger.info(f"   時間: {run_context.started_at_local}")
    logger.info(f"   業務日期: {run_date} ({run_context.timezone_name})")
    logger.info(f"   關鍵字: {config.SEARCH_KEYWORDS}")
    logger.info(f"   模式: {'演示模式 (Showcase)' if showcase else ('乾跑 (不推播)' if dry_run else '完整流程')}")
    logger.info("=" * 60)

    raw_data_path = None
    analysis_path = None
    report_path = None
    report_candidate_path = None
    report_promoted_path = None
    report_error = ""

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
        logger.info(" Step 1/4: 開始搜集全球區域情報（瀑布鏈：Tavily → DDG，補充 Dcard + 巴哈）...")
        searcher = WaterfallSearcher()
        try:
            all_results = await searcher.search(max_results_per_region=5)
        except Exception as e:
            logger.error(f"  [FAIL] 瀑布搜尋鏈全部失敗: {e}")
            return

        # ── 補充 Dcard + 巴哈姆特 爬蟲 ────────────────────
        tw_keywords = config.REGIONAL_KEYWORDS.get("TW", ["傳說對決"])
        # P107 S2: 焦點英雄單詞接入 aov 板搜集（巴哈 PoC 搜「芽芽」8/8 命中真遊戲文）
        # 根因 A 修復：焦點覆蓋不再靠泛詞碰運氣。Dcard 走 DDG 對焦點暫無效（PoC 0 篇），留 S3 Apify 治本
        focus_keywords = list(tw_keywords) + list(getattr(config, "HERO_WATCHLIST", []))
        seen_urls = {r.url for r in all_results}

        try:
            dcard = DcardScraper()
            dcard_results = await dcard.search(focus_keywords, max_results=8)
            added = 0
            for r in dcard_results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append(r)
                    added += 1
            logger.info(f"   [Dcard] 新增 {added} 篇不重複文章")
        except Exception as e:
            logger.warning(f"  [!] Dcard 爬蟲失敗（跳過）: {e}")

        try:
            bahamut = BahamutScraper()
            # P110 v2: 雙軌 — 板最新列表撈每日新文（治根因①凍結）+ 關鍵字搜尋補芽芽精準命中（防全板稀釋 R4）
            baha_results = await bahamut.fetch_board_latest(max_results=15)
            baha_results += await bahamut.search(focus_keywords, max_results=8)
            added = 0
            for r in baha_results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append(r)
                    added += 1
            logger.info(f"   [巴哈] 雙軌新增 {added} 篇不重複（板列表新文 + 關鍵字補芽芽）")
        except Exception as e:
            logger.warning(f"  [!] 巴哈姆特爬蟲失敗（跳過）: {e}")

    if not all_results:
        logger.warning("[!] 沒有搜集到任何資料，流程提前結束。")
        source_quality = build_source_quality(all_results)
        try:
            manifest = build_manifest(
                run_date=run_date,
                mode="unknown",
                raw_path=None,
                analysis_path=None,
                report_path=None,
                meta={"history_status": "not_run", "budget": budget_manager.snapshot(run_date)},
                history_delta={},
                status="failed",
                error="no source results",
                dry_run=dry_run,
                showcase_flag=showcase,
                gate_mode=getattr(config, "PUBLISH_GATE_MODE", "shadow"),
                eligibility_reasons=source_quality["reasons"],
                source_hash=source_hash,
                timezone_name=run_context.timezone_name,
                scheduled_utc=run_context.started_at_utc,
                source_quality=source_quality,
            )
            manifest_out = write_manifest(config.DATA_DIR, manifest)
            logger.info(f"   run manifest 已儲存: {manifest_out}")
        except Exception as me:
            logger.warning(f"  [!] 0 posts run manifest 寫入失敗: {me}")
        return

    source_quality = build_source_quality(all_results)
    source_hash = build_source_hash([r.to_dict() for r in all_results])
    logger.info(f"   source_hash: {source_hash[:12]}")

    # 儲存原始資料
    raw_data_path = config.DATA_DIR / f"raw_{compact_run_date}.json"
    raw_data_path.write_text(
        json.dumps(
            [r.to_dict() for r in all_results],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info(f"   原始搜集資料已儲存: {raw_data_path}")

    # ── Step 2：數據分析 ────────────────────────────────
    logger.info(" Step 2/4: 啟動 AI 大腦進行語意與情緒拆解...")
    analyzer = SentimentAnalyzer()
    stats_scraper = HeroStatsScraper()
    pre_cache_stats = analyzer.llm.cache_manager.get_stats()
    selection_snapshot = {}
    enrichment_snapshot = {}

    def _stat_delta(current: dict, previous: dict, key: str) -> int:
        return max(0, int(current.get(key, 0) or 0) - int(previous.get(key, 0) or 0))

    try:
        budget_snapshot = budget_manager.snapshot(run_date)
        selection = build_source_selection(
            all_results,
            max_llm_posts=getattr(config, "LLM_ANALYSIS_TOP_N", 18),
            budget_remaining=budget_snapshot.get("remaining_llm_calls", getattr(config, "LLM_DAILY_BUDGET", 20)),
            hero_focus=getattr(config, "HERO_FOCUS_NAME", "芽芽"),
        )
        selection_snapshot = selection.snapshot
        logger.info(
            "   [P91] source selection: total=%s selected=%s local_only=%s duplicate=%s cap=%s",
            selection_snapshot.get("total_input_posts", 0),
            selection_snapshot.get("llm_selected_posts", 0),
            selection_snapshot.get("local_only_posts", 0),
            selection_snapshot.get("duplicate_posts", 0),
            selection_snapshot.get("max_llm_items", 0),
        )
        if selection.local_only_posts:
            enrichment_queue = build_enrichment_queue(
                run_date=run_date,
                source_hash=source_hash,
                local_only_posts=selection.local_only_posts,
                local_only_reasons=selection.local_only_reasons,
                max_replay_posts=getattr(config, "ENRICHMENT_REPLAY_MAX_POSTS", 4),
                retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
            )
            enrichment_queue_path = write_enrichment_queue(
                getattr(config, "ENRICHMENT_QUEUE_DIR", config.DATA_DIR / "enrichment_queue"),
                enrichment_queue,
            )
            enrichment_snapshot = build_enrichment_snapshot(
                enrichment_queue,
                queue_path=enrichment_queue_path,
                budget_snapshot=budget_snapshot,
                artifact_retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
            )
        else:
            enrichment_snapshot = build_enrichment_snapshot(
                None,
                artifact_retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
            )
        logger.info(
            "   [P92] enrichment queue: available=%s eligible=%s skipped=%s status=%s",
            enrichment_snapshot.get("queue_available", False),
            enrichment_snapshot.get("eligible_posts", 0),
            enrichment_snapshot.get("skipped_posts", 0),
            enrichment_snapshot.get("replay_status", "not_available"),
        )

        if selection.llm_posts:
            cache_hero = "combined" if not selection.local_only_posts and len(selection.llm_posts) == len(all_results) else None
            cache_date = run_date if cache_hero else None
            analysis_res = await analyzer.analyze_posts(
                selection.llm_posts,
                showcase=showcase,
                hero_name=cache_hero,
                date_str=cache_date,
            )
            if selection.local_only_posts:
                local_entries = analyze_posts_locally(selection.local_only_posts, config.HERO_WATCHLIST)
                analysis_res = merge_local_only_entries(analysis_res, local_entries)
        else:
            local_entries = analyze_posts_locally(selection.local_only_posts, config.HERO_WATCHLIST)
            analysis_res = {
                "posts": local_entries,
                "is_showcase": False,
                "quota_error": False,
                "contract_status": "ok",
                "contract_errors": [],
                "local_analysis_status": "ok",
                "fallback_reason": "selection_no_llm_posts",
                "analysis_source": "local_deterministic",
                "provider_diagnostics": analyzer._provider_diagnostics(),
            }
        analysis_res = dict(analysis_res)
        analysis_res["selection"] = selection_snapshot
        analyzed_posts = analysis_res["posts"]
        active_showcase = analysis_res["is_showcase"] or showcase
        # P69 F2：區分 showcase 四態（production / showcase / showcase_forced / error_fallback）
        _quota_error = analysis_res.get("quota_error", False)
        if analysis_res.get("analysis_source") == "local_deterministic":
            daily_summary = generate_local_summary(
                analyzed_posts,
                run_date,
                hero_focus=getattr(config, "HERO_FOCUS_NAME", "芽芽"),
            )
        else:
            daily_summary = await analyzer.generate_daily_summary(analyzed_posts, date=run_date, showcase=active_showcase)
        daily_summary["date"] = run_date
        _provider_diag = dict(analysis_res.get("provider_diagnostics", {}))
        _provider_diag["openai_fallback_used"] = bool(
            _provider_diag.get("openai_fallback_used", False)
            or getattr(analyzer.llm, "last_fallback_used", False)
        )

        # 注入 LLM cache 統計 meta，供報告檔頂 metadata comment 使用
        _stats = analyzer.llm.cache_manager.get_stats()
        _l1 = _stats.get("total_l1_hits", 0)
        _l2 = _stats.get("total_l2_hits", 0)
        _ap = _stats.get("total_apify_hits", 0)
        _miss = _stats.get("total_misses", 0)
        _l1_delta = _stat_delta(_stats, pre_cache_stats, "total_l1_hits")
        _l2_delta = _stat_delta(_stats, pre_cache_stats, "total_l2_hits")
        _ap_delta = _stat_delta(_stats, pre_cache_stats, "total_apify_hits")
        _miss_delta = _stat_delta(_stats, pre_cache_stats, "total_misses")

        _analysis_source = str(
            analysis_res.get("analysis_source")
            or daily_summary.get("analysis_source")
            or ""
        )
        _summary_contract = daily_summary.get("llm_contract", {})
        _contract_status = str(analysis_res.get("contract_status", "ok"))
        _summary_contract_status = (
            str(_summary_contract.get("status", "ok"))
            if isinstance(_summary_contract, dict)
            else "ok"
        )
        if _analysis_source == "local_deterministic":
            _llm_coverage = "none"
        elif _analysis_source == "mixed":
            _llm_coverage = "partial"
        elif _contract_status == "degraded" or _summary_contract_status == "degraded":
            _analysis_source = "mixed"
            _llm_coverage = "partial"
        elif showcase:
            _analysis_source = "showcase"
            _llm_coverage = "none"
        else:
            _analysis_source = "llm"
            _llm_coverage = "full"

        _legacy_mode = "showcase_forced" if _quota_error else ("showcase" if active_showcase else "production")
        if showcase:
            _mode = "showcase"
        elif _analysis_source == "local_deterministic":
            _mode = "production"
        elif _quota_error:
            _mode = "showcase_forced"
        elif active_showcase:
            _mode = "showcase"
        else:
            _mode = "production"
        _active_provider, _active_model = analyzer.active_provider_model()
        daily_summary["_meta"] = {
            "mode": _mode,
            "legacy_mode": _legacy_mode,
            "analysis_source": _analysis_source,
            "llm_coverage": _llm_coverage,
            "local_analysis_status": analysis_res.get("local_analysis_status", ""),
            "cache_hit": _l1_delta + _l2_delta,
            "l1_hits": _l1_delta,
            "l2_hits": _l2_delta,
            "apify_hits": _ap_delta,
            "llm_calls": _miss_delta,
            "total_calls": _l1_delta + _l2_delta + _ap_delta + _miss_delta,
            "quota_error": bool(_quota_error),
            "openai_fallback_configured": bool(_provider_diag.get("openai_fallback_configured", False)),
            "openai_fallback_used": bool(_provider_diag.get("openai_fallback_used", False)),
            "active_provider": _active_provider,
            "active_model": _active_model,
            "provider_diagnostics": _provider_diag,
            "budget": budget_manager.snapshot(run_date),
            "selection": selection_snapshot,
            "enrichment": enrichment_snapshot,
        }

        # 同步抓取戰鬥數據 - 異常隔離處理 (Phase 35.5)
        # 必須在 daily_summary 產出之後才能注入
        try:
            combat_stats = await stats_scraper.fetch_watchlist_stats()
            daily_summary["combat_stats"] = {name: asdict(s) for name, s in combat_stats.items()}
            
            # P106.2 注入 combat_stats_source / combat_stats_age_days
            focus_hero = getattr(config, "HERO_FOCUS_NAME", "芽芽")
            hero_stats = combat_stats.get(focus_hero)
            if hero_stats:
                daily_summary["_meta"]["combat_stats_source"] = hero_stats.data_source
                age_days = 0
                if hero_stats.update_time:
                    try:
                        dt_up = datetime.strptime(hero_stats.update_time[:10], "%Y-%m-%d")
                        dt_rep = datetime.strptime(run_date, "%Y-%m-%d")
                        age_days = (dt_rep - dt_up).days
                    except Exception:
                        pass
                daily_summary["_meta"]["combat_stats_age_days"] = age_days
            else:
                daily_summary["_meta"]["combat_stats_source"] = "none"
                daily_summary["_meta"]["combat_stats_age_days"] = 0
        except Exception as se:
            logger.warning(f"  [!] 戰鬥數據同步延遲或失敗: {se} (流程繼續)")
            daily_summary["combat_stats"] = {}
            daily_summary["_meta"]["combat_stats_source"] = "none"
            daily_summary["_meta"]["combat_stats_age_days"] = 0
        
        # ── Step 2.2：計算歷史趨勢 (Phase 29) ──────────
        logger.info(" Step 2.2/4: 啟動情報時光機，計算週趨勢...")
        try:
            history_gen = HistoryResolver()
            daily_summary["history_delta"] = history_gen.resolve_trends(daily_summary, showcase=showcase)
            daily_summary["_meta"]["history_status"] = "ok"
        except (OSError, ValueError) as he:
            # 可預期的資料讀取問題：保留流程但標記 degraded，避免注入假趨勢數據。
            logger.warning(f"  [!] 歷史趨勢讀取異常: {he} (使用今日基線降級結果)")
            today_vol = daily_summary.get("total_posts", 0)
            daily_summary["history_delta"] = {
                "overall": {"volume_pct": 0.0, "avg_baseline": today_vol, "is_red_alert": False},
                "heroes": {},
                "weekly_vol_pulse": {
                    "volumes": [today_vol],
                    "labels": [run_context.display_date],
                    "average": today_vol,
                },
                "alerts": [],
                "diagnostics": {
                    "status": "degraded",
                    "reason": f"{type(he).__name__}: {he}",
                },
            }
            daily_summary["_meta"]["history_status"] = "degraded"
        except Exception:
            # 不可預期的程式錯誤必須 fail loud，交給外層錯誤處理，不可靜默掩蓋。
            logger.exception("  [FAIL] 歷史趨勢計算發生程式錯誤，終止本輪分析流程。")
            raise
        
        # 將專屬網頁連結注入到 summary 中
        if getattr(config, "GITHUB_PAGES_URL", None):
            base_url = config.GITHUB_PAGES_URL.rstrip("/")
            date_str = daily_summary.get("date", run_date)
            daily_summary["report_url"] = f"{base_url}/data/reports/aov_report_{date_str}.html"
            
        logger.info("  [OK] AI 分析完成")
    except Exception as e:
        logger.error(f"  [FAIL] AI 分析發生嚴重錯誤: {e} (啟動旗艦演示備援)")
        daily_summary = analyzer._empty_summary(date=run_date, showcase=showcase)
        _fb_stats = analyzer.llm.cache_manager.get_stats()
        _fb_l1_delta = _stat_delta(_fb_stats, pre_cache_stats, "total_l1_hits")
        _fb_l2_delta = _stat_delta(_fb_stats, pre_cache_stats, "total_l2_hits")
        _fb_ap_delta = _stat_delta(_fb_stats, pre_cache_stats, "total_apify_hits")
        _fb_miss_delta = _stat_delta(_fb_stats, pre_cache_stats, "total_misses")
        daily_summary["_meta"] = {
            "mode": "showcase" if showcase else "error_fallback",
            "legacy_mode": "showcase" if showcase else "error_fallback",
            "analysis_source": "showcase" if showcase else "unknown",
            "llm_coverage": "none",
            "local_analysis_status": "",
            "cache_hit": _fb_l1_delta + _fb_l2_delta,
            "l1_hits": _fb_l1_delta,
            "l2_hits": _fb_l2_delta,
            "apify_hits": _fb_ap_delta,
            "llm_calls": _fb_miss_delta,
            "total_calls": _fb_l1_delta + _fb_l2_delta + _fb_ap_delta + _fb_miss_delta,
            "provider_diagnostics": analyzer._provider_diagnostics(),
            "budget": budget_manager.snapshot(run_date),
            "selection": selection_snapshot,
            "enrichment": enrichment_snapshot,
        }
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

    # 儲存分析結果（Phase 56.5：契約守門 + atomic write 治本 R7/R21）
    from analyzer.data_writer import atomic_write_json, validate_summary, coerce_to_schema
    analysis_path = config.DATA_DIR / f"analysis_{compact_run_date}.json"
    preview_report_path = config.REPORTS_DIR / f"aov_report_{daily_summary.get('date', run_date)}.html"
    _meta = daily_summary.setdefault("_meta", {})
    # P105.1 趨勢補完：兜底所有 summary 路徑（fallback/empty）都有 total_posts（history volume 來源）
    daily_summary.setdefault("total_posts", len(analyzed_posts))
    _preview_core_contract = build_core_contract(
        source_quality=source_quality,
        analysis_path=analysis_path,
        report_path=preview_report_path,
    )
    _preview_tier = build_quality_tier(
        mode=_meta.get("mode", "unknown"),
        status="ok",
        core_contract=_preview_core_contract,
        meta=_meta,
        showcase_flag=showcase,
    )
    _meta["quality_tier"] = _preview_tier["tier"]
    _meta["analysis_source"] = _preview_tier["analysis_source"]
    _meta["llm_coverage"] = _preview_tier["llm_coverage"]
    _meta["quality_tier_reasons"] = _preview_tier["reasons"]
    ok, missing = validate_summary(daily_summary)
    if not ok:
        logger.warning(f"  [!] daily_summary 缺契約欄位 {missing}，已用安全預設值補齊")
        daily_summary, _ = coerce_to_schema(daily_summary)
    try:
        atomic_write_json(analysis_path, daily_summary)
        logger.info(f"   分析結果已儲存（atomic）: {analysis_path}")
    except Exception as e:
        logger.error(f"  [FAIL] 寫檔失敗: {e}")

    # ── Step 3：產出報告 ──────────────────────────────
    logger.info(" Step 3/4: 產出視覺化報告...")

    generator = ReportGenerator()
    try:
        report_candidate_path = generator.generate(daily_summary, analyzed_posts, promote=False)
        report_path = report_candidate_path
        logger.info(f"  [OK] 候選報告已生成: {report_candidate_path}")
        # P108：報告數據可信度 advisory（不阻斷報告生成）
        try:
            from scripts.check_report_credibility import check_report_credibility, format_warnings
            for _cred_line in format_warnings(
                check_report_credibility(daily_summary, analyzed_posts)
            ).split("\n"):
                logger.info(_cred_line)
        except Exception as _cred_e:
            logger.warning(f"  報告可信度檢查跳過：{_cred_e}")
    except Exception as e:
        report_error = str(e)
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
            date_str = daily_summary.get("date", run_date)
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

    # ── Step 4.5：寫入 Run Manifest (P78) ──────────────
    gate_mode = getattr(config, "PUBLISH_GATE_MODE", "shadow")
    mode = daily_summary.get("_meta", {}).get("mode", "unknown")
    quality_tier = daily_summary.get("_meta", {}).get("quality_tier", "")
    gate_reasons, gate_checks = evaluate_publish_gate(
        daily_summary.get("date", run_date),
        mode,
        gate_mode=gate_mode,
        candidate_report_path=report_candidate_path,
        quality_tier=quality_tier,
    )
    do_promote = should_promote(bool(report_candidate_path), quality_tier, len(gate_reasons))
    if do_promote:
        try:
            report_promoted_path = generator.promote_candidate(
                report_candidate_path,
                daily_summary.get("date", run_date),
                output_dir=config.REPORTS_DIR,
            )
            report_path = report_promoted_path
            logger.info(f"   [PROMOTE] 已發布 canonical 報告: {report_promoted_path}")
        except Exception as pe:
            gate_reasons.append("promotion error: %s: %s" % (type(pe).__name__, pe))
            logger.error("  [FAIL] promote 失敗：%s", pe)
    else:
        logger.info(
            "   [PROMOTE] 跳過：mode=%s, quality_tier=%s, gate_reasons=%d",
            mode,
            quality_tier or "unknown",
            len(gate_reasons),
        )
    try:
        _meta = daily_summary.get("_meta", {})
        manifest = build_manifest(
            run_date=daily_summary.get("date", run_date),
            mode=_meta.get("mode", "unknown"),
            raw_path=raw_data_path,
            analysis_path=analysis_path,
            report_path=report_path,
            meta=_meta,
            history_delta=daily_summary.get("history_delta"),
            status="ok" if report_path else "failed",
            error=report_error,
            dry_run=dry_run,
            showcase_flag=showcase,
            gate_mode=gate_mode,
            eligibility_reasons=gate_reasons,
            source_hash=source_hash,
            timezone_name=run_context.timezone_name,
            scheduled_utc=run_context.started_at_utc,
            source_quality=source_quality,
        )
        manifest_out = write_manifest(config.DATA_DIR, manifest)
        logger.info(f"   run manifest 已儲存: {manifest_out}")
        if gate_checks:
            failed = [c for c in gate_checks if c.failed]
            logger.info(
                "   gate checks: %d total / %d failed",
                len(gate_checks),
                len(failed),
            )
    except Exception as me:
        logger.warning(f"  [!] run manifest 寫入失敗: {me}")

    # Lockfile 寫入：production 模式成功才記錄
    _meta = daily_summary.get("_meta", {})
    if not dry_run and not showcase and _meta.get("mode") == "production":
        try:
            from datetime import timezone as _tz2
            config.LOCKFILE_PATH.write_text(
                datetime.now(_tz2.utc).isoformat(), encoding="utf-8"
            )
        except Exception as _le:
            logger.warning(f"Lockfile 寫入失敗: {_le}")

    # ────── 雲端即時部署 ──────────────────────────────────────
    should_publish = bool(report_promoted_path)
    if gate_reasons and str(gate_mode).lower() == "blocking":
        should_publish = False
    if not dry_run and should_publish:
        await github_backup_job(is_manual=False, meta=_meta)
    elif not dry_run and not should_publish:
        logger.error("  [BLOCKED] 未 promote 成功，略過 GitHub 同步。")


# ── CLI 與排程 ────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(
        description="AoV 自動化輿情監測系統 (Tavily + LLM)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--run-now", action="store_true", help="立即執行")
    parser.add_argument("--dry-run", action="store_true", help="立即執行但不推播")
    parser.add_argument("--showcase", action="store_true", help="演示模式：使用高品質預設數據確保產出完美")
    parser.add_argument("--force", action="store_true", help="強制執行，忽略 Lockfile 30 分鐘冷卻")
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
        await run_pipeline(dry_run=args.dry_run, showcase=args.showcase, force=args.force)
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
