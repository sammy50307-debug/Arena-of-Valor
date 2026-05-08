---
name: firecrawl-dynamic-breacher
type: exec
status: stale
schema_version: 1
version: 1.0.0
description: 透過 Firecrawl API 渲染 JS 動態網頁並提取 Markdown，破解反爬蟲

when_to_use:
  - 需要抓取重度依賴 JavaScript 動態載入的網頁
  - 一般爬蟲拿到空白或亂碼頁面時
  - SPA 網站或需要滾動載入的無限捲動頁面
when_NOT_to_use:
  - 靜態 HTML 網頁清理 → 用 html-markdown-distiller（更輕量）
  - 多論壇同步抓取 → 用 multi-thread-synthesizer
trigger_keywords: [Firecrawl, 動態網頁, JS渲染, 爬蟲, SPA, 網頁抓取, 動態載入, 無限捲動, 反爬蟲]

example_invocations:
  - input: "這個網頁是 SPA，幫我抓下來"
    skill: firecrawl-dynamic-breacher
    v1_trigger_block: |
      🪧 [firecrawl-dynamic-breacher 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「SPA 網頁抓取」
      ├─ 信心分數：0.88
      ├─ 來源層：smart-task-router (L2)
      └─ 動作：執行 firecrawl-dynamic-breacher

entry_points:
  cli: "python -m skills.firecrawl_dynamic_breacher"
  import: "skills.firecrawl_dynamic_breacher"
  prompt_paste: "adapters/prompt_paste/firecrawl-dynamic-breacher.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: false

deployed_to: [gemini-global]
requires:
  python: ">=3.10"
  packages: [firecrawl-py]
  env: [FIRECRAWL_API_KEY]
depends_on: []
last_used: 2026-04-19
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[firecrawl-dynamic-breacher 已啟動]`。

# 動態網頁渲染刺客 (Firecrawl Dynamic Breacher)

這是「芽芽戰情室」Milestone 2 的首發特種兵 (Phase 49)。在收集網路輿情時，我們遇到最大的防禦體系就是「純前端動態渲染 (SPA)」。許多遊戲論壇或外媒網站，第一次讀取只會回傳空蕩蕩的 `<div>`，真實的 HTML 與文本必須等數百毫秒的 JS 執行後才會出現。

為保持主機的極致輕量化，我們不選擇在本地佈署沈重、容易爆 Memory 的 Playwright / Puppeteer 內核。相反地，我們直接派遣擁有強大穿透力的 `Firecrawl API` 替我們完成所有的「等待渲染、網頁翻頁、繞過 Cloudflare 盾牌、以及降噪蒸餾 Markdown」。

## 🎯 核心工作流程

1. **雲端空降 (Cloud Initiation)**：將要攻堅的網頁目標透過我們自製的外殼 `breacher.py` 傳送給 Firecrawl 行動指揮中心。
2. **火力壓制 (JS Rendering & Evasion)**：在遠端執行無頭瀏覽器，進行 3~5 秒的深度模擬捲動，讓所有被隱藏的留言板或圖文資源「被迫顯形」。
3. **無損抽離 (Markdown Extraction)**：不需要 BeautifulSoup，不再跟爛 HTML 糾纏。Firecrawl 會直接用 AI 從骨架把內文抽成格式完美的 Markdown 並且回傳。
4. **回傳戰情 (Data Yield)**：將解析出來的文字送回戰情室，做成高密度的單發或總結分析。

## 🛠️ 目錄結構

```
firecrawl-dynamic-breacher/
├── SKILL.md                 # 刺客行動準則
├── scripts/
│   └── breacher.py         # 對接 Firecrawl API 的遠端狙擊槍
└── test_skill.py            # 自動化驗證：挑戰動態渲染挑戰網頁
```

## 🚀 相依套件與需求
- `requests`
- 註冊並在環境變數中寫入 `FIRECRAWL_API_KEY` (如無設定，系統可降級備援模式，但會失去深層渲染穿透力)。
