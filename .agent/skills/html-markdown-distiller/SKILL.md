---
name: html-markdown-distiller
type: exec
status: stale
schema_version: 1
version: 1.0.0
description: 剝離 HTML 廣告/導覽列並輸出精簡 Markdown，大幅降低 Token 量

when_to_use:
  - 有一份 HTML 需要去除廣告、導覽列、頁尾等雜訊
  - 需要將網頁內容轉成乾淨 Markdown 後送入 LLM
  - Token 超量時需要壓縮 HTML 內容
when_NOT_to_use:
  - 需要渲染 JS 動態網頁 → 用 firecrawl-dynamic-breacher
  - 論壇多線程同步抓取 → 用 multi-thread-synthesizer
trigger_keywords: [HTML轉Markdown, 網頁淨化, 去除廣告, distiller, HTML清理, 網頁轉文字, 去雜訊]

example_invocations:
  - input: "把這個 HTML 清一下，去掉廣告"
    skill: html-markdown-distiller
    v1_trigger_block: |
      🪧 [html-markdown-distiller 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「HTML 清理」
      ├─ 信心分數：0.89
      ├─ 來源層：smart-task-router (L2)
      └─ 動作：執行 html-markdown-distiller

entry_points:
  cli: "python -m skills.html_markdown_distiller"
  import: "skills.html_markdown_distiller"
  prompt_paste: "adapters/prompt_paste/html-markdown-distiller.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: false

deployed_to: [gemini-global]
requires:
  python: ">=3.10"
  packages: [beautifulsoup4]
depends_on: []
last_used: 2026-04-18
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[html-markdown-distiller 已啟動]`。

# 網頁淨化蒸餾器 (HTML to Markdown Distiller)

這是一套獨立的 AI Agent Skill，它的終極目標是作為「芽芽戰情室」解析引擎的前置濾波器（Pre-processor）。透過純程式化的資料萃取，取代依賴大型語言模型去除無效 HTML 的暴力做法，每篇網頁文章平均可**節省 30% ~ 60% 的 Token 計算資源**。

## 🎯 核心工作流程

1. **取得來源**：讀入任何包含雜亂 HTML 結構的字串。
2. **DOM 淨化**：利用程式化邏輯移除無語意與非內文區塊（`<nav>`, `<footer>`, `<aside>`, `<script>`, `<style>`, `.ad`, `#comments`）。
3. **萃取轉換**：將剩下的 `<article>`, `<main>` 等主體結構降維打擊，轉換為高密度的 Markdown 格式。
4. **輸出**：返回純淨無染的 Markdown 文本供後續情緒分析模型（Gemini）使用。

## 🛠️ 目錄結構

```
html-markdown-distiller/
├── SKILL.md                 # 您正在閱讀的技能指令核心
├── scripts/
│   └── html_to_md.py        # 淨化與轉換引擎（包含 DOMTrimmer 與 Markdownizer）
├── examples/
│   └── sample_input.html    # 測試用原始包含廣告的網頁
│   └── sample_output.md     # 測試驗證後的純粹輸出
└── resources/
    └── ignore_tags.json     # 自定義要強制剔除的 DOM Selector
```

## 🚀 對話與 CLI 調用方式

### AI 智能觸發
> 「幫我把這段 HTML 淨化成 Markdown，去掉那些沒用的廣告版面：[貼上 HTML]」

### CLI 直接測試
```bash
python .agent/skills/html-markdown-distiller/scripts/html_to_md.py --input ".agent/skills/html-markdown-distiller/examples/sample_input.html" --output "distilled_result.md"
```

## ⚙️ 相依套件要求
- `beautifulsoup4`：DOM 解析與裁剪
- `markdownify`：HTML 轉 Markdown 核心引擎
