---
name: daily-diff-radar
description: 每日差異雷達。比對今日與前一日的 analysis_*.json，產出「昨日→今日」的關鍵變化摘要：英雄上下榜、情緒分數 Δ、聲量 Δ%、各平台變化，並依閾值標記 alert_level。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[daily-diff-radar 已啟動]`。

# 每日差異雷達 (Daily Diff Radar)

這是「芽芽戰情室」Milestone 4 Phase 58 特種兵。解決使用者每日要從頭讀完整戰報的痛點——雷達只告訴你「和昨天比有什麼不一樣」。

## 🎯 六項差異指標

| 指標 | 計算方式 |
|------|---------|
| `sentiment_delta` | 今日 `overall.sentiment_score` − 昨日 |
| `volume_delta` | 今日 `total_posts` − 昨日 |
| `volume_delta_pct` | `(today − yesterday) / yesterday × 100` |
| `new_heroes` | 今日 hero_stats keys − 昨日 keys |
| `dropped_heroes` | 昨日 keys − 今日 keys |
| `hero_sentiment_shifts` | 同時出現的英雄：今日 avg_sentiment − 昨日 |
| `platform_changes` | 各平台 `post_count` 差值 |
| `trend_change` | 昨日 `trend` → 今日 `trend`（Upward/Stable/Downward）|

## 🚨 Alert 分級

| 等級 | 觸發條件 |
|------|---------|
| HIGH | `|Δsentiment| ≥ 0.3` 或 `|Δvolume_pct| ≥ 50%` |
| MEDIUM | `|Δsentiment| ≥ 0.15` 或 `|Δvolume_pct| ≥ 25%` |
| LOW | 其餘 |

## 🛠️ 目錄結構

```
daily-diff-radar/
├── SKILL.md
├── scripts/
│   └── radar.py              # DailyDiffRadar 主類別
└── test_skill.py             # 6 項自動化測試
```

## ⚙️ 介面

```python
radar = DailyDiffRadar()
report = radar.radar()                  # 自動找最新兩天比對
report = radar.radar(today_date="2026-04-19")  # 指定今日
```

## 📊 輸出範例

```json
{
  "today_date": "2026-04-19",
  "yesterday_date": "2026-04-05",
  "sentiment_delta": -0.15,
  "volume_delta": +3,
  "volume_delta_pct": 25.0,
  "trend_change": "Upward → Stable",
  "new_heroes": ["克里希"],
  "dropped_heroes": ["悟空"],
  "hero_sentiment_shifts": {"芽芽": -0.2},
  "platform_changes": {"dcard": {"today": 5, "yesterday": 3, "delta": 2}},
  "alert_level": "MEDIUM"
}
```

## 🚀 相依套件

純 Python 標準庫（`json`, `pathlib`, `datetime`）。零外部依賴。
