"""
AI 情報雷達 Skill 自我測試腳本
================================
用於驗證 skill 所有元件都能正常運作。
執行方式：
    python .agent/skills/ai-news-radar/scripts/test_skill.py
"""

import json
import csv
import sys
import os
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("skill-test")

# ── 路徑定義 ────────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SKILL_DIR.parent.parent.parent
RESOURCES_DIR = SKILL_DIR / "resources"

print("=" * 60)
print("🛰️  AI 情報雷達 Skill — 自我測試")
print("=" * 60)

PASS = 0
FAIL = 0

def test_pass(name):
    global PASS
    PASS += 1
    print(f"  ✅ PASS: {name}")

def test_fail(name, reason):
    global FAIL
    FAIL += 1
    print(f"  ❌ FAIL: {name}")
    print(f"       原因: {reason}")

# ──────────────────────────────────────────────────────────
# TEST 1: sources.json 結構驗證
# ──────────────────────────────────────────────────────────
print("\n📁 [TEST 1] sources.json 結構驗證")
try:
    sources_path = RESOURCES_DIR / "sources.json"
    assert sources_path.exists(), f"找不到 {sources_path}"
    with open(sources_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sources = data.get("sources", [])
    assert len(sources) == 9, f"預期 9 個來源，實際 {len(sources)}"
    
    # 驗證必要欄位
    required_fields = ["id", "name", "url", "language", "category", "region"]
    for s in sources:
        for field in required_fields:
            assert field in s, f"來源 {s.get('id', '?')} 缺少欄位: {field}"
    
    # 語系統計
    langs = {"zh-TW": 0, "en": 0, "ja": 0}
    for s in sources:
        lang = s["language"]
        langs[lang] = langs.get(lang, 0) + 1
    
    test_pass(f"sources.json 載入完成 - 共 {len(sources)} 個來源 (zh-TW:{langs.get('zh-TW',0)} en:{langs.get('en',0)} ja:{langs.get('ja',0)})")
    
    for s in sources:
        print(f"       [{s['language']}] {s['name']} → {s['url']}")
except Exception as e:
    test_fail("sources.json", str(e))

# ──────────────────────────────────────────────────────────
# TEST 2: keywords.csv 結構驗證
# ──────────────────────────────────────────────────────────
print("\n📊 [TEST 2] keywords.csv 結構驗證")
try:
    kw_path = RESOURCES_DIR / "keywords.csv"
    assert kw_path.exists(), f"找不到 {kw_path}"
    
    keywords = []
    with open(kw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        assert header is not None and "category" in header, "缺少 category 欄位"
        for row in reader:
            keywords.append(row)
    
    assert len(keywords) > 0, "關鍵字庫為空"
    
    # 統計類別
    categories = set(k["category"] for k in keywords)
    priorities = [k.get("priority", "") for k in keywords]
    high_count = priorities.count("HIGH")
    
    test_pass(f"keywords.csv 載入完成 - {len(keywords)} 條目，{len(categories)} 個類別，{high_count} 個高優先")
    print(f"       類別: {', '.join(sorted(categories))}")
except Exception as e:
    test_fail("keywords.csv", str(e))

# ──────────────────────────────────────────────────────────
# TEST 3: Python 依賴套件驗證
# ──────────────────────────────────────────────────────────
print("\n📦 [TEST 3] Python 依賴套件驗證")

# apify_client
try:
    from apify_client import ApifyClientAsync
    test_pass("apify_client 匯入成功")
except ImportError as e:
    test_fail("apify_client", str(e))

# httpx
try:
    import httpx
    test_pass(f"httpx 匯入成功 (版本: {httpx.__version__})")
except ImportError as e:
    test_fail("httpx", str(e))

# dotenv
try:
    from dotenv import load_dotenv
    test_pass("python-dotenv 匯入成功")
except ImportError as e:
    test_fail("python-dotenv", str(e))

# ──────────────────────────────────────────────────────────
# TEST 4: .env 環境變數驗證
# ──────────────────────────────────────────────────────────
print("\n🔑 [TEST 4] 環境變數驗證")
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    assert env_path.exists(), f"找不到 .env: {env_path}"
    load_dotenv(env_path)
    
    apify_token = os.getenv("APIFY_TOKEN", "")
    if apify_token:
        masked = apify_token[:8] + "..." + apify_token[-4:] if len(apify_token) > 12 else "***"
        test_pass(f"APIFY_TOKEN 已設定 ({masked})")
    else:
        test_fail("APIFY_TOKEN", "未設定或為空值")
    
    # 可選的其他 token
    for var in ["TAVILY_API_KEY", "GEMINI_API_KEY"]:
        val = os.getenv(var, "")
        status = "已設定" if val else "未設定（可選）"
        print(f"       {var}: {status}")
        
except Exception as e:
    test_fail(".env 載入", str(e))

# ──────────────────────────────────────────────────────────
# TEST 5: fetch_news.py 模組語法驗證
# ──────────────────────────────────────────────────────────
print("\n📄 [TEST 5] fetch_news.py 語法驗證")
try:
    fetch_script = SKILL_DIR / "scripts" / "fetch_news.py"
    assert fetch_script.exists(), f"找不到 {fetch_script}"
    
    # 語法檢查
    import ast
    with open(fetch_script, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    
    # 確認關鍵類別存在
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    assert "AINewsRadar" in class_names, "找不到 AINewsRadar 類別"
    assert "ReportFormatter" in class_names, "找不到 ReportFormatter 類別"
    assert "NewsArticle" in class_names, "找不到 NewsArticle 資料模型"
    
    test_pass(f"fetch_news.py 語法正確 - 類別: {', '.join(class_names)}")
except SyntaxError as e:
    test_fail("fetch_news.py 語法", f"語法錯誤 line {e.lineno}: {e.msg}")
except AssertionError as e:
    test_fail("fetch_news.py 結構", str(e))
except Exception as e:
    test_fail("fetch_news.py", str(e))

# ──────────────────────────────────────────────────────────
# TEST 6: AINewsRadar 類別初始化測試
# ──────────────────────────────────────────────────────────
print("\n🤖 [TEST 6] AINewsRadar 核心類別初始化")
try:
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    sys.path.insert(0, str(PROJECT_ROOT))
    
    # 動態載入模組
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fetch_news",
        SKILL_DIR / "scripts" / "fetch_news.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 初始化
    radar = module.AINewsRadar()
    assert hasattr(radar, 'sources'), "缺少 sources 屬性"
    assert hasattr(radar, 'keywords'), "缺少 keywords 屬性"
    assert hasattr(radar, 'run'), "缺少 run 方法"
    assert len(radar.sources) == 9, f"預期 9 個來源，實際 {len(radar.sources)}"
    
    test_pass(f"AINewsRadar 初始化成功 - {len(radar.sources)} 個來源，{len(radar.keywords)} 個關鍵字")
    
    # 測試語系過濾
    tw_sources = radar.filter_sources("zh-TW")
    en_sources = radar.filter_sources("en")
    ja_sources = radar.filter_sources("ja")
    test_pass(f"語系過濾正常 - zh-TW:{len(tw_sources)}, en:{len(en_sources)}, ja:{len(ja_sources)}")
    
    # 測試主題偵測
    test_text = "Claude Opus 4.7 AI Agent 發布，AI安全機制大幅提升"
    topics = radar.detect_topics(test_text)
    test_pass(f"主題偵測正常 - 測試文本偵測到: {topics}")

except Exception as e:
    test_fail("AINewsRadar 類別", str(e))
    import traceback
    traceback.print_exc()

# ──────────────────────────────────────────────────────────
# TEST 7: ReportFormatter 輸出格式測試
# ──────────────────────────────────────────────────────────
print("\n📝 [TEST 7] 報告格式化測試")
try:
    from datetime import datetime
    
    # 建立假資料
    NewsArticle = module.NewsArticle
    ReportFormatter = module.ReportFormatter
    
    sample_articles = [
        NewsArticle(
            title="Claude Opus 4.7 發布，AI安全機制全面升級",
            summary="Anthropic 正式發布旗艦模型，benchmark 排名登頂...",
            url="https://www.inside.com.tw/sample",
            source_name="INSIDE 硬塞",
            source_id="inside",
            language="zh-TW",
            region="taiwan",
            category="tech-trend",
            fetched_at=datetime.now().isoformat(),
            topics=["LLM模型", "AI安全"]
        ),
        NewsArticle(
            title="Meta Launches Superintelligence Model",
            summary="Meta's new model challenges OpenAI and Anthropic...",
            url="https://venturebeat.com/sample",
            source_name="VentureBeat AI",
            source_id="venturebeat",
            language="en",
            region="global",
            category="enterprise-ai",
            fetched_at=datetime.now().isoformat(),
            topics=["LLM模型", "AI代理"]
        ),
    ]
    
    # 測試 Markdown 格式
    md = ReportFormatter.to_markdown(sample_articles, "測試報告")
    assert "🛰️" in md, "Markdown 格式缺少標題圖示"
    assert "台灣科技媒體" in md, "Markdown 格式缺少台灣分區"
    assert "全球英文來源" in md, "Markdown 格式缺少全球分區"
    test_pass(f"Markdown 格式正常 - 輸出 {len(md)} 字元")
    
    # 測試 JSON 格式
    import json
    json_out = ReportFormatter.to_json(sample_articles)
    parsed = json.loads(json_out)
    assert len(parsed) == 2, "JSON 格式文章數量不符"
    assert "title" in parsed[0], "JSON 格式缺少 title 欄位"
    test_pass(f"JSON 格式正常 - {len(parsed)} 筆文章，欄位: {list(parsed[0].keys())[:5]}")
    
    # 測試摘要格式
    summary = ReportFormatter.to_summary(sample_articles)
    assert "🛰️" in summary, "摘要格式缺少標題"
    test_pass(f"推播摘要格式正常 - 輸出 {len(summary)} 字元")

except Exception as e:
    test_fail("ReportFormatter", str(e))
    import traceback
    traceback.print_exc()

# ──────────────────────────────────────────────────────────
# TEST 8: sample_output.md 存在性驗證
# ──────────────────────────────────────────────────────────
print("\n📑 [TEST 8] 範例檔案驗證")
examples_dir = SKILL_DIR / "examples"
sample_path = examples_dir / "sample_output.md"
if sample_path.exists():
    test_pass(f"sample_output.md 存在 ({sample_path.stat().st_size} bytes)")
else:
    test_fail("sample_output.md", f"找不到 {sample_path}")

skill_md = SKILL_DIR / "SKILL.md"
if skill_md.exists():
    test_pass(f"SKILL.md 存在 ({skill_md.stat().st_size} bytes)")
else:
    test_fail("SKILL.md", f"找不到 {skill_md}")

# ──────────────────────────────────────────────────────────
# 測試結果總結
# ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"📊 測試結果：PASS {PASS} / FAIL {FAIL} / TOTAL {PASS + FAIL}")
if FAIL == 0:
    print("🎉 所有測試通過！Skill 可以正常部署。")
else:
    print(f"⚠️  有 {FAIL} 個測試失敗，請檢查上方錯誤訊息。")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
