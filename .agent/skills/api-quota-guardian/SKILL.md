---
name: api-quota-guardian
description: API 額度守衛。持久化追蹤 Tavily（或其他付費搜尋 API）的月使用量，達 80%/95% 門檻時警示，並提供 should_fallback() 旗標讓瀑布鏈主動切換免費源，避免被動觸發 429。
version: 1.0.0
---

# API 額度守衛 (API Quota Guardian)

這是「芽芽戰情室」Milestone 4 Phase 57 特種兵。解決只能「事後」被動發現 Tavily 額度耗盡的問題，改為「事前」主動預警並切換備援。

## 🎯 三層門檻

| 區間 | verdict | 行為 |
|------|---------|------|
| 0% ~ 79% | OK | 正常使用 |
| 80% ~ 94% | WARN | 發出警告日誌 |
| 95% ~ 100% | CRITICAL | `should_fallback()` 回傳 True，瀑布鏈主動跳過 Tavily |

## 🛠️ 目錄結構

```
api-quota-guardian/
├── SKILL.md
├── scripts/
│   └── guardian.py           # APIQuotaGuardian 主類別
└── test_skill.py             # 6 項自動化測試
```

## 💾 狀態存放

持久化至 `data/quota_state.json`：
```json
{
  "tavily": {
    "month": "2026-04",
    "used": 42,
    "limit": 1000
  }
}
```

每月第一次呼叫時自動 rollover（`month` 不同 → used 歸零）。

## ⚙️ 介面

```python
guardian = APIQuotaGuardian(provider="tavily", monthly_limit=1000)

guardian.record(3)            # 記錄 3 次呼叫
status = guardian.status()    # {used, remaining, percent, verdict, month}
if guardian.should_fallback(): # >= 95% 時 True
    skip_tavily()
```

## 🚀 相依套件

純 Python 標準庫（`json`, `pathlib`, `datetime`）。零外部依賴。
