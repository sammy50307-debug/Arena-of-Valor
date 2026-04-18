"""
AI 情報雷達爬蟲腳本 (fetch_news.py)
======================================
使用現有的 apify_client 架構，從 9 大來源（繁中/英/日）
抓取最新 AI 新聞，輸出繁體中文整合報告。

使用方式：
    python scripts/fetch_news.py [OPTIONS]

選項：
    --lang <zh-TW|en|ja|all>   指定語系過濾 (預設: all)
    --topic <關鍵字>            關鍵字過濾
    --limit <數字>              每個來源最多抓幾筆 (預設: 3)
    --format <markdown|json|summary>  輸出格式 (預設: markdown)
    --output <檔名>             輸出檔案路徑 (不填則印至終端)
"""

import asyncio
import json
import csv
import logging
import argparse
import sys
import os

# 強制 Windows 終端機輸出 UTF-8，防止亂碼
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field, asdict

# ── 路徑處理：支援從任何目錄執行 ────────────────────────────
_SKILL_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _SKILL_DIR.parent.parent.parent  # 往上找到 Arena of Valor 根目錄

# 嘗試載入專案的 apify_client
try:
    sys.path.insert(0, str(_PROJECT_ROOT))
    from apify_client import ApifyClientAsync  # type: ignore
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False

# 嘗試 httpx (用作備援)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# ── 日誌設定 ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai-news-radar")


# ── 資料模型 ────────────────────────────────────────────────
@dataclass
class NewsArticle:
    """標準化的新聞文章資料模型。"""
    title: str
    summary: str
    url: str
    source_name: str
    source_id: str
    language: str
    region: str
    category: str
    fetched_at: str = ""
    topics: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── 主要爬蟲類別 ────────────────────────────────────────────
class AINewsRadar:
    """
    AI 情報雷達 — 使用 Apify RAG Browser 從多語系媒體抓取 AI 新聞
    """

    RESOURCES_DIR = _SKILL_DIR / "resources"

    def __init__(self, apify_token: Optional[str] = None):
        # 從環境變數或參數取得 token
        self.apify_token = apify_token or os.getenv("APIFY_TOKEN", "")
        self.sources = self._load_sources()
        self.keywords = self._load_keywords()

        if not self.apify_token:
            logger.warning("⚠️  APIFY_TOKEN 未設定，將嘗試使用 httpx 直接爬取（功能受限）")

    def _load_sources(self) -> List[dict]:
        """載入 sources.json。"""
        sources_path = self.RESOURCES_DIR / "sources.json"
        if not sources_path.exists():
            logger.error(f"找不到 sources.json: {sources_path}")
            return []
        with open(sources_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("sources", [])

    def _load_keywords(self) -> List[dict]:
        """載入 keywords.csv。"""
        keywords_path = self.RESOURCES_DIR / "keywords.csv"
        if not keywords_path.exists():
            logger.warning(f"找不到 keywords.csv，跳過關鍵字分類。")
            return []
        keywords = []
        with open(keywords_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keywords.append(row)
        return keywords

    def filter_sources(self, lang: str = "all") -> List[dict]:
        """依語系過濾新聞來源。"""
        if lang == "all":
            return self.sources
        return [s for s in self.sources if s["language"] == lang]

    def detect_topics(self, text: str) -> List[str]:
        """從文字中偵測 AI 主題關鍵字。"""
        text_lower = text.lower()
        matched = []
        for kw_row in self.keywords:
            category = kw_row.get("category", "")
            # 檢查繁中和英文關鍵字
            for field_name in ["keyword_zh", "keyword_en", "keyword_ja"]:
                terms = kw_row.get(field_name, "").split("/")
                for term in terms:
                    term = term.strip().lower()
                    if term and term in text_lower:
                        if category not in matched:
                            matched.append(category)
                        break
        return matched[:5]  # 最多回傳 5 個主題

    async def fetch_with_apify(
        self,
        url: str,
        source: dict,
        max_results: int = 3
    ) -> List[NewsArticle]:
        """使用 Apify RAG Browser 抓取單一來源。"""
        if not APIFY_AVAILABLE or not self.apify_token:
            return await self.fetch_with_httpx(url, source)

        articles = []
        try:
            client = ApifyClientAsync(self.apify_token)
            run_input = {
                "startUrls": [{"url": url}],
                "maxCrawlPages": max_results,
                "outputFormats": ["markdown"],
            }

            logger.info(f"  📡 [Apify] 正在抓取: {source['name']} ({url})")
            run = await client.actor("apify/rag-web-browser").call(run_input=run_input)

            dataset_client = client.dataset(run["defaultDatasetId"])
            items = await dataset_client.list_items()

            for item in (items.items or []):
                markdown_text = item.get("markdown", "")
                metadata = item.get("metadata", {})
                title = metadata.get("title", "（無標題）")
                item_url = metadata.get("url", url)

                if not markdown_text:
                    continue

                # 擷取前 500 字作為摘要
                summary_raw = markdown_text[:500].strip().replace("\n", " ")

                article = NewsArticle(
                    title=title,
                    summary=summary_raw,
                    url=item_url,
                    source_name=source["name"],
                    source_id=source["id"],
                    language=source["language"],
                    region=source["region"],
                    category=source["category"],
                    fetched_at=datetime.now().isoformat(),
                    topics=self.detect_topics(title + " " + summary_raw),
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"  ❌ Apify 抓取失敗 ({source['name']}): {e}")

        logger.info(f"  ✅ {source['name']}: 取得 {len(articles)} 筆")
        return articles

    async def fetch_with_httpx(
        self,
        url: str,
        source: dict,
    ) -> List[NewsArticle]:
        """備援：使用 httpx 直接抓取（輸出格式較簡單）。"""
        if not HTTPX_AVAILABLE:
            logger.error("httpx 未安裝，無法備援爬取。請執行 pip install httpx")
            return []

        articles = []
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with httpx.AsyncClient(timeout=30, headers=headers) as client:
                logger.info(f"  📡 [httpx] 正在抓取: {source['name']}")
                resp = await client.get(url)
                resp.raise_for_status()

                # 簡單截取文本（無 HTML 解析）
                text = resp.text[:2000]
                article = NewsArticle(
                    title=f"{source['name']} 首頁摘要",
                    summary=f"（備援模式）RAW 內容前段: {text[:300]}...",
                    url=url,
                    source_name=source["name"],
                    source_id=source["id"],
                    language=source["language"],
                    region=source["region"],
                    category=source["category"],
                    fetched_at=datetime.now().isoformat(),
                    topics=[],
                )
                articles.append(article)
        except Exception as e:
            logger.error(f"  ❌ httpx 備援抓取失敗 ({source['name']}): {e}")

        return articles

    async def run(
        self,
        lang: str = "all",
        topic_filter: Optional[str] = None,
        limit: int = 3,
    ) -> List[NewsArticle]:
        """主要執行入口：抓取所有符合條件的來源。"""
        sources = self.filter_sources(lang)
        logger.info(f"🛰️  AI 情報雷達啟動 | 來源數: {len(sources)} | 語系: {lang}")

        all_articles: List[NewsArticle] = []

        for source in sources:
            articles = await self.fetch_with_apify(
                url=source["url"],
                source=source,
                max_results=limit,
            )
            all_articles.extend(articles)

            # 短暫延遲，避免請求過快
            await asyncio.sleep(1)

        # 主題過濾
        if topic_filter:
            topic_lower = topic_filter.lower()
            all_articles = [
                a for a in all_articles
                if topic_lower in a.title.lower()
                or topic_lower in a.summary.lower()
                or any(topic_lower in t.lower() for t in a.topics)
            ]
            logger.info(f"🔍 主題過濾 '{topic_filter}' 後剩餘: {len(all_articles)} 筆")

        logger.info(f"🎯 抓取完成！共 {len(all_articles)} 筆文章")
        return all_articles


# ── 輸出格式化 ───────────────────────────────────────────────
class ReportFormatter:
    """將文章列表輸出成不同格式。"""

    @staticmethod
    def to_markdown(articles: List[NewsArticle], title: str = "AI 情報雷達日報") -> str:
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        lines = [
            f"# 🛰️ {title}",
            f"",
            f"> 生成時間：{now} ｜ 共 {len(articles)} 篇文章",
            f"",
            "---",
            "",
        ]

        # 依語系/地區分組
        regions = {
            "taiwan": ("🇹🇼 台灣科技媒體", []),
            "global": ("🌍 全球英文來源", []),
            "japan": ("🇯🇵 日本亞洲前瞻", []),
        }
        for article in articles:
            region_key = article.region.lower()
            if region_key in regions:
                regions[region_key][1].append(article)
            else:
                regions["global"][1].append(article)

        for region_key, (region_title, region_articles) in regions.items():
            if not region_articles:
                continue
            lines.append(f"## {region_title}")
            lines.append("")
            for a in region_articles:
                topic_tags = " ".join([f"`{t}`" for t in a.topics]) if a.topics else ""
                lines.append(f"### [{a.source_name}] {a.title}")
                if topic_tags:
                    lines.append(f"**主題**: {topic_tags}")
                lines.append(f"")
                lines.append(f"{a.summary[:400]}...")
                lines.append(f"")
                lines.append(f"🔗 [{a.url}]({a.url})")
                lines.append("")
                lines.append("---")
                lines.append("")

        # 熱點摘要
        all_topics = []
        for a in articles:
            all_topics.extend(a.topics)
        if all_topics:
            topic_count = {}
            for t in all_topics:
                topic_count[t] = topic_count.get(t, 0) + 1
            sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
            lines.append("## 📊 本次熱點主題排行")
            lines.append("")
            for i, (topic, count) in enumerate(sorted_topics[:8], 1):
                lines.append(f"{i}. **{topic}** — 出現 {count} 次")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_json(articles: List[NewsArticle]) -> str:
        return json.dumps(
            [a.to_dict() for a in articles],
            ensure_ascii=False,
            indent=2
        )

    @staticmethod
    def to_summary(articles: List[NewsArticle]) -> str:
        """Line/Telegram 推播格式（精簡）。"""
        now = datetime.now().strftime("%Y/%m/%d")
        lines = [
            f"🛰️ AI 情報雷達 — {now}",
            f"━━━━━━━━━━━━━━━",
            f"共 {len(articles)} 篇文章",
            "",
        ]

        regions = {"taiwan": "🇹🇼 台灣", "global": "🌍 全球", "japan": "🇯🇵 日本"}
        grouped: dict = {k: [] for k in regions}
        for a in articles:
            key = a.region.lower()
            if key in grouped:
                grouped[key].append(a)

        for key, label in regions.items():
            region_articles = grouped.get(key, [])
            if not region_articles:
                continue
            lines.append(f"{label}焦點")
            for a in region_articles[:2]:  # 每區最多 2 則
                short_title = a.title[:30] + ("..." if len(a.title) > 30 else "")
                lines.append(f"• {short_title}")
            lines.append("")

        # 統計熱點
        all_topics = []
        for a in articles:
            all_topics.extend(a.topics)
        if all_topics:
            topic_count = {}
            for t in all_topics:
                topic_count[t] = topic_count.get(t, 0) + 1
            top3 = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:3]
            lines.append("🔥 今日熱點：" + " | ".join([f"{t}×{c}" for t, c in top3]))

        return "\n".join(lines)


# ── CLI 入口 ────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="🛰️ AI 情報雷達 — 多語系 AI 新聞爬蟲"
    )
    parser.add_argument(
        "--lang",
        choices=["zh-TW", "en", "ja", "all"],
        default="all",
        help="指定語系 (預設: all)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="關鍵字主題過濾"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="每個來源最多抓幾筆 (預設: 3)"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "summary"],
        default="markdown",
        help="輸出格式 (預設: markdown)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="輸出檔案路徑 (不填則印至終端)"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Apify API Token (可覆蓋環境變數)"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # 初始化雷達
    radar = AINewsRadar(apify_token=args.token)

    # 抓取
    articles = await radar.run(
        lang=args.lang,
        topic_filter=args.topic,
        limit=args.limit,
    )

    if not articles:
        logger.warning("⚠️  未取得任何文章，請確認 APIFY_TOKEN 是否正確設定。")
        sys.exit(1)

    # 格式化輸出
    formatter = ReportFormatter()
    if args.format == "markdown":
        output_text = formatter.to_markdown(articles)
    elif args.format == "json":
        output_text = formatter.to_json(articles)
    elif args.format == "summary":
        output_text = formatter.to_summary(articles)
    else:
        output_text = formatter.to_markdown(articles)

    # 輸出
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        logger.info(f"📄 報告已儲存至: {output_path}")
    else:
        print("\n" + output_text)


if __name__ == "__main__":
    asyncio.run(main())
