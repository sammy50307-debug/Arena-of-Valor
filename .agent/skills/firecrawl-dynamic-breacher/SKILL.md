---
name: firecrawl-dynamic-breacher
description: 動態網頁渲染刺客，專攻重度依賴 JavaScript 動態載入（如 SPA 或無限捲動）的敵軍陣地。透過對接 Firecrawl API，無視反爬蟲機制，強行渲染整張網頁並直接提取為最純粹的 Markdown 格式，為大腦省下 90% 除噪功夫。
version: 1.0.0
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
