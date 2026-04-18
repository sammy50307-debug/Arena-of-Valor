---
name: multi-thread-synthesizer
description: 跨維度多線程聚合兵，透過 asyncio.gather 將多個論壇（Dcard、PTT、巴哈、FB）的抓取任務同步發出，大幅縮短等待時間，並自動融合各來源結果，產出標記時間戳與平台來源的高密度情報戰報。
version: 1.0.0
---

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
