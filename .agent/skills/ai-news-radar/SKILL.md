---
name: ai-news-radar
type: pipe
status: stale
schema_version: 1
version: 1.0.0
description: 從 9 大科技媒體自動抓取最新 AI 新聞，輸出繁中整合報告

when_to_use:
  - 需要蒐集今日最新 AI 科技新聞時
  - 主公說「幫我看最新 AI 動態」「今天有什麼 AI 新聞」
  - 需要每日情報簡報素材
when_NOT_to_use:
  - AOV 英雄走勢查詢 → 用 history-trend-query
  - 特定網頁爬取 → 用 firecrawl-dynamic-breacher
trigger_keywords: [AI新聞, 科技新聞, 每日情報, news radar, AI動態, 最新AI, AI趨勢, 情報簡報]

example_invocations:
  - input: "幫我看今天的 AI 新聞"
    skill: ai-news-radar
    v1_trigger_block: |
      🪧 [ai-news-radar 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「AI 新聞」
      ├─ 信心分數：0.90
      ├─ 來源層：smart-task-router (L2)
      └─ 動作：執行 ai-news-radar

entry_points:
  cli: "python -m skills.ai_news_radar"
  import: "skills.ai_news_radar"
  prompt_paste: "adapters/prompt_paste/ai-news-radar.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: false

deployed_to: [gemini-global]
requires:
  python: ">=3.10"
  packages: [apify-client, httpx]
  env: [APIFY_TOKEN]
depends_on: []
last_used: 2026-04-17
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[ai-news-radar 已啟動]`。

# 🛰️ AI 情報雷達 Skill

## 📋 Skill 簡介

這個 Skill 讓 AI 助理能夠**一鍵從 9 大來源抓取最新 AI 趨勢新聞**，自動分類、主題偵測，
並輸出繁體中文整合報告，可搭配 Line/Telegram 推播或存成 Markdown 備查。

### 覆蓋來源

| 語系 | 媒體來源 | 特色 |
|------|---------|------|
| 🇹🇼 繁中 | INSIDE 硬塞 | LLM／AI 政策／新創 |
| 🇹🇼 繁中 | 數位時代 BNext | AI 工具教學／半導體 |
| 🇹🇼 繁中 | iThome | 資安／AI Agent／企業 IT |
| 🇹🇼 繁中 | 科技新報 TechNews | 半導體／AI 硬體深度分析 |
| 🇹🇼 繁中 | 科技報橘 TechOrange | Physical AI／機器人 |
| 🌍 英文 | VentureBeat AI | 企業 AI 部署／融資動態 |
| 🌍 英文 | The Rundown AI | 每日 AI 快報／LLM 動態 |
| 🇯🇵 日文 | Ledge.ai | 日本主權 AI／AI 安全 |
| 🇯🇵 日文 | AINOW | 生成 AI 導入實務／DX |

---

## 🚀 快速開始

### 前置需求

```bash
# 確認 Apify Token 已設定（從 .env 讀取）
echo $APIFY_TOKEN   # Windows: $env:APIFY_TOKEN

# 安裝依賴（Arena of Valor 專案已包含）
pip install apify-client httpx
```

### 基本使用

```bash
# 從 Arena of Valor 專案根目錄執行
python .agent/skills/ai-news-radar/scripts/fetch_news.py

# 或從 skill 目錄執行
python scripts/fetch_news.py
```

---

## 📖 使用工作流程

### Step 1：選擇情報語系

```bash
# 只抓台灣繁體中文（5個來源）
python scripts/fetch_news.py --lang zh-TW

# 只抓全球英文（2個來源）
python scripts/fetch_news.py --lang en

# 只抓日本日文（2個來源）
python scripts/fetch_news.py --lang ja

# 抓全部 9 個來源（預設）
python scripts/fetch_news.py --lang all
```

### Step 2：指定主題過濾（可選）

```bash
# 只看 AI Agent 相關
python scripts/fetch_news.py --topic "AI Agent"

# 只看半導體議題
python scripts/fetch_news.py --topic "半導體"

# 只看 Claude / Anthropic 動態
python scripts/fetch_news.py --topic "Claude"
```

### Step 3：控制抓取量

```bash
# 每個來源最多抓 5 筆（預設 3 筆）
python scripts/fetch_news.py --limit 5
```

### Step 4：選擇輸出格式

```bash
# Markdown 整合報告（預設，適合存檔備查）
python scripts/fetch_news.py --format markdown

# JSON 格式（適合後端處理或接 AI 分析）
python scripts/fetch_news.py --format json

# 推播摘要格式（適合 Line / Telegram Bot）
python scripts/fetch_news.py --format summary
```

### Step 5：儲存報告

```bash
# 輸出到指定檔案
python scripts/fetch_news.py --output data/reports/ai_news_today.md

# 完整範例：台灣來源、AI Agent 主題、Markdown、存檔
python scripts/fetch_news.py \
  --lang zh-TW \
  --topic "AI Agent" \
  --limit 5 \
  --format markdown \
  --output data/reports/ai_agent_news.md
```

---

## 🔧 進階使用

### 直接在 Python 程式碼中呼叫

```python
import asyncio
import sys
sys.path.insert(0, r"d:\Coding Project\Arena of Valor")

from .agent.skills.ai_news_radar.scripts.fetch_news import AINewsRadar, ReportFormatter

async def get_ai_news():
    radar = AINewsRadar()
    articles = await radar.run(
        lang="zh-TW",          # 只抓台灣繁中
        topic_filter="AI代理", # 主題過濾
        limit=3                # 每源 3 筆
    )
    report = ReportFormatter.to_markdown(articles)
    return report

# 執行
report = asyncio.run(get_ai_news())
print(report)
```

### 整合進 Arena of Valor 主流程

```python
# 在 main.py 中加入 AI 新聞雷達作為獨立模組
from pathlib import Path
import subprocess

def run_ai_news_radar(output_path: str = "data/reports/ai_news.md"):
    """觸發 AI 情報雷達，輸出 Markdown 報告。"""
    skill_script = Path(".agent/skills/ai-news-radar/scripts/fetch_news.py")
    result = subprocess.run(
        ["python", str(skill_script), "--format", "markdown", "--output", output_path],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode == 0:
        print(f"✅ AI 新聞報告已生成: {output_path}")
    else:
        print(f"❌ 生成失敗: {result.stderr}")
```

---

## 📁 檔案結構

```
.agent/skills/ai-news-radar/
├── SKILL.md                        ← 本文件（主要指令）
├── scripts/
│   └── fetch_news.py               ← 主要爬蟲腳本
├── resources/
│   ├── sources.json                ← 9 大媒體來源定義
│   └── keywords.csv                ← AI 主題關鍵字庫（中/英/日）
└── examples/
    └── sample_output.md            ← 範例輸出報告
```

---

## 🗂️ 主題分類系統

Skill 內建 AI 主題自動偵測，來源為 `resources/keywords.csv`：

| 主題分類 | 覆蓋關鍵詞（摘要） |
|---------|-----------------|
| LLM模型 | Claude / GPT / Gemini / LLaMA |
| AI代理 | AI Agent / Agentic AI / Multi-agent |
| AI安全 | AI Safety / Alignment / Cybersecurity |
| 硬體基礎 | GPU / NPU / CoWoS / 先進封裝 |
| 機器人 | Humanoid Robot / Physical AI |
| 企業應用 | Enterprise AI / ROI / DX |
| 市場動態 | IPO / Funding / 新創 |
| 台灣產業 | TSMC / NVIDIA Taiwan |
| 日本AI | Japan Sovereign AI / SoftBank AI |

---

## 📤 輸出格式說明

### Markdown 格式（`--format markdown`）
完整報告，依地區分組，含來源、主題標籤、摘要、連結。  
→ 適合手動查閱或存入 Obsidian 筆記。

### JSON 格式（`--format json`）
結構化資料，包含 `title / summary / url / source_name / topics / fetched_at`。  
→ 適合串接 LLM 分析或資料庫儲存。

### 摘要格式（`--format summary`）
精簡的推播文字，每區最多 2 則 + 熱點統計。  
→ 適合 Line Bot / Telegram Bot 推播。

---

## ⚠️ 注意事項

1. **APIFY_TOKEN 必填**：請確認 `.env` 中已設定 `APIFY_TOKEN`
2. **限流保護**：每個來源之間有 1 秒延遲，避免被封鎖
3. **備援模式**：若 Apify 不可用，自動切換 httpx 直接爬取（輸出較簡單）
4. **資源消耗**：每次執行約消耗 Apify 平台算力，建議 `--limit 3`（預設值）

---

## 🔄 更新關鍵字庫

如需追蹤新主題，直接編輯 `resources/keywords.csv`：

```csv
category,keyword_en,keyword_zh,keyword_ja,priority
新主題名稱,English keywords,繁中關鍵詞,日文キーワード,HIGH
```

---

## 📋 常見 CLI 範例速查

```bash
# 📰 每日情報日報（全語系 Markdown）
python scripts/fetch_news.py --format markdown

# 🇹🇼 台灣快報（繁中、推播格式）
python scripts/fetch_news.py --lang zh-TW --format summary

# 🤖 AI Agent 深度情報（全語系、每源 5 筆）
python scripts/fetch_news.py --topic "AI Agent" --limit 5

# 💾 儲存今日完整報告
python scripts/fetch_news.py --output data/reports/ai_$(date +%Y%m%d).md

# 🔍 JSON 格式供後端分析
python scripts/fetch_news.py --format json --output data/ai_data.json
```

---

## 🖥️ 終端執行（P71.3）

```bash
cd .agent/skills/ai-news-radar

# 說明（透傳至 fetch_news.py）
python __main__.py --help

# 抓取全語系新聞（預設 markdown）
python __main__.py

# 指定語系 / 主題 / 筆數
python __main__.py --lang zh-TW --limit 5
python __main__.py --topic "LLM" --limit 3

# JSON 輸出（供後端解析）
python __main__.py --format json

# 儲存至檔案
python __main__.py --format markdown --output data/ai_news.md

# NO_COLOR（強制 markdown 格式，無 ANSI）
NO_COLOR=1 python __main__.py
```

依賴：`apify-client`、`httpx`；需設定 `APIFY_TOKEN` 環境變數。
