---
name: rich-push-formatter
description: 戰報推播格式化儀。把 daily-diff-radar / analysis JSON 轉成人類可讀的 Markdown 日報，含 emoji 警戒燈號、Δ 方向箭頭、英雄變動清單、平台變化表格。可直接貼進 Discord / Obsidian / Line。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[rich-push-formatter 已啟動]`。

# 戰報推播格式化儀 (Rich Push Formatter)

「芽芽戰情室」Milestone 4 Phase 59 特種兵。解決使用者需求：JSON 太冷，
人類要的是一眼就能看懂的推播訊息。

## 🎯 核心職責

| 輸入 | 輸出 |
|------|------|
| daily-diff-radar 的 diff dict | Markdown 日報（含 emoji、箭頭、表格） |
| analysis_YYYYMMDD.json | 單日 briefing Markdown |

## 🚨 警戒燈號對照

| alert_level | Emoji | 視覺提示 |
|-------------|-------|---------|
| HIGH | 🔴 | 紅燈警報 |
| MEDIUM | 🟡 | 黃燈注意 |
| LOW | 🟢 | 綠燈穩定 |

## 📈 Δ 方向圖示

- 正向變化：`⬆️ +0.15`
- 負向變化：`⬇️ -0.12`
- 持平：`➡️ 0.00`

## 🛠️ 目錄結構

```
rich-push-formatter/
├── SKILL.md
├── scripts/
│   └── formatter.py       # RichPushFormatter 主類別
└── test_skill.py          # 自動化測試
```

## ⚙️ 介面

```python
formatter = RichPushFormatter()
md = formatter.format_diff(diff_dict)        # 昨→今差異報告
md = formatter.format_analysis(analysis)     # 單日情報摘要
```

## 🚀 相依套件

純 Python 標準庫。零外部依賴。
