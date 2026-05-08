---
name: multi-thread-synthesizer
type: exec
status: stale
schema_version: 1
version: 1.0.0
description: asyncio 多線程同步抓取 Dcard/PTT/巴哈/FB，融合輸出高密度情報

when_to_use:
  - 需要同時從多個論壇抓取資料時
  - 主公說「幫我看各平台今天的討論」「多平台情報蒐集」
  - 需要比較跨平台聲量和情緒時
when_NOT_to_use:
  - 單一特定網頁抓取 → 用 firecrawl-dynamic-breacher
  - 僅查詢歷史走勢（不需實時抓取）→ 用 history-trend-query
trigger_keywords: [多論壇, 同步抓取, Dcard, PTT, 巴哈, FB, 多平台情報, 論壇聚合, 多線程]

example_invocations:
  - input: "幫我同步抓 Dcard、PTT、巴哈今天的討論"
    skill: multi-thread-synthesizer
    v1_trigger_block: |
      🪧 [multi-thread-synthesizer 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「多論壇同步抓取」
      ├─ 信心分數：0.91
      ├─ 來源層：smart-task-router (L2)
      └─ 動作：執行 multi-thread-synthesizer

entry_points:
  cli: "python -m skills.multi_thread_synthesizer"
  import: "skills.multi_thread_synthesizer"
  prompt_paste: "adapters/prompt_paste/multi-thread-synthesizer.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: false

deployed_to: [gemini-global]
requires:
  python: ">=3.10"
  packages: [httpx, asyncio]
depends_on: [api-quota-guardian]
last_used: 2026-04-19
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[multi-thread-synthesizer 已啟動]`。

# 跨維度多線程聚合兵 (Multi-Thread Synthesizer)

這是「芽芽戰情室」Milestone 2 的壓軸特種兵 (Phase 51)。在過去，當我們需要同時巡視 Dcard、PTT 巴哈姆特、Facebook 粉絲專頁時，因為每一次請求都必須「乖乖排隊等候」，整個監測流程可能得花上數分鐘。

本特種兵打通了任督二脈，將所有的情報採集任務「同時發出」，就像一個指揮官在同一時刻派出十個偵察兵奔赴各自的陣地，而不是一個接一個輪流上場。透過 Python 的 `asyncio.gather` 非同步並發技術，所有任務將在同一個時間視窗內完成，大幅壓縮等待時間。

## 🎯 核心工作流程

1. **任務拆分 (Task Decomposition)**：接收一批多元化的目標任務清單 (各論壇URL)，拆散成獨立的非同步協程。
2. **並行轟炸 (Concurrent Dispatch)**：透過 `asyncio.gather()` 同時並行執行所有任務，不互相阻塞。
3. **資料融合 (Data Synthesis)**：自動為每一批打撈回來的結果打上「時間戳」與「來源平台標記」，並統一整合進單一的高密度輸出結果字典。

## 🛠️ 目錄結構

```
multi-thread-synthesizer/
├── SKILL.md                 # 多線程聚合兵作戰準則
├── scripts/
│   └── synthesizer.py       # `AsyncSynthesizer` 核心並行引擎
└── test_skill.py            # 並行效能壓力測試
```

## 🚀 相依套件
- Python 原生 `asyncio` (無需額外安裝)

---

## 🖥️ 終端執行（P71.3）

```bash
cd .agent/skills/multi-thread-synthesizer

# 說明
python __main__.py --help

# 示範模式（5 個 fake 並行任務）
python __main__.py --demo

# 指定並發數
python __main__.py --demo --concurrency 10

# JSON 輸出（供解析結果）
python __main__.py --demo --output json

# NO_COLOR（plain 格式）
NO_COLOR=1 python __main__.py --demo
```

> 注意：本 skill 為函式庫元件。實際使用需在 Python 程式碼中 `from scripts.synthesizer import AsyncSynthesizer`。
> 依賴：Python 原生 `asyncio`，無需額外安裝。
