---
name: trend-anomaly-detector
type: exec
status: stale
schema_version: 1
version: 1.0.0
description: Z-Score 即時偵測論壇聲量/情緒異常暴增，輸出紅黃警報

when_to_use:
  - 需要主動偵測輿情是否有異常暴增
  - 主公說「有沒有什麼聲量突然爆炸的」「輿情有沒有異常」
  - 需要 Z-Score 或移動平均分析玩家怨氣是否超標
when_NOT_to_use:
  - 查看過去走勢（被動 pull）→ 用 history-trend-query
  - 抓取論壇原始資料 → 用 multi-thread-synthesizer
trigger_keywords: [異常, Z-Score, 警報, 輿情爆炸, anomaly, 暴增, 聲量異常, 輿情警報, 玩家怨氣]

example_invocations:
  - input: "最近有沒有哪個英雄聲量突然暴增？"
    skill: trend-anomaly-detector
    v1_trigger_block: |
      🪧 [trend-anomaly-detector 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「聲量暴增」
      ├─ 信心分數：0.87
      ├─ 來源層：smart-task-router (L2)
      └─ 動作：執行 trend-anomaly-detector

entry_points:
  cli: "python -m skills.trend_anomaly_detector"
  import: "skills.trend_anomaly_detector"
  prompt_paste: "adapters/prompt_paste/trend-anomaly-detector.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: false

deployed_to: [gemini-global]
requires:
  python: ">=3.10"
  packages: []
depends_on: [history-trend-query]
last_used: 2026-04-19
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[trend-anomaly-detector 已啟動]`。

# 輿情核爆異常觀測儀 (Trend Anomaly Detector)

這支特種兵 (Phase 50) 是「芽芽戰情室」防雷達體系的最高守護者。在沒有這隻兵種以前，營運團隊往往是在「日報總結出爐後」才驚覺論壇已經炸鍋了 12 小時。

本特種兵改變了這個被動局面。它不依賴 LLM 的慢速語意分析，而是直接以純數學角度切入：把過去 N 天的聲量視為基準波型，當今日的新進波形在短時間內突破「3 倍標準差 (3-Sigma)」閾值時，它會武斷地判定發生了「輿情核爆 (Anomaly)」，並直接送出緊急告警。

## 🎯 核心工作流程

1. **基準建立 (Baseline Profiling)**：吃入過去 7~14 天的歷史聲量或情緒均值，計算出穩定的平均數 ($\mu$) 與標準差 ($\sigma$)。
2. **即時離群運算 (Z-Score Calculation)**：每當有批量新數據進入時，直接算出差異值。公式為：`Z = (最新數值 - 平均值) / 標準差`。
3. **核爆裁決 (Threshold Breach)**：
   - Z > 2.0：黃色警戒 (熱門話題浮現)
   - Z > 3.0：紅色警戒 (輿情核爆 / 炎上警告)
4. **輸出情報**：產出夾帶嚴重等級與確切發生時間戳的異常回報供告警系統使用。

## 🛠️ 目錄結構

```
trend-anomaly-detector/
├── SKILL.md                 # 異常觀測儀守則
├── scripts/
│   └── anomaly_detector.py  # 搭載 Z-Score 分野核心演算法
└── test_skill.py            # 自動化驗證：突發脈衝壓力測試
```

## 🚀 相依套件
- 此演算法為了保證極致的執行速度，使用純 Python 原生庫 (`math`) 撰寫，無須掛載笨重的 numpy 或 pandas。
