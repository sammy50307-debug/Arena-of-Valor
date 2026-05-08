---
name: api-quota-guardian
type: exec
status: in-use
schema_version: 1
version: 1.0.0
description: 追蹤 Tavily API 月額度，80%/95% 門檻警示，自動提供備援旗標

when_to_use:
  - 爬蟲任務前確認 Tavily API 額度是否充足
  - 出現 Tavily 429 錯誤、需要切換備援時
  - 需要查詢本月 API 使用量或設定用量上限
when_NOT_to_use:
  - 網頁爬取本身 → 用 firecrawl-dynamic-breacher 或 waterfall-search-chain
  - 管理非 Tavily 的 API 配額 → 視需求擴充
trigger_keywords: [API額度, 配額, Tavily, 429, quota, 額度不夠, should_fallback, 搜尋API, API用量]

example_invocations:
  - input: "Tavily 額度還夠嗎？"
    skill: api-quota-guardian
    v1_trigger_block: |
      🪧 [api-quota-guardian 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「Tavily 額度」
      ├─ 信心分數：0.95
      ├─ 來源層：主公口頭
      └─ 動作：執行 api-quota-guardian

entry_points:
  cli: "python -m skills.api_quota_guardian"
  import: "skills.api_quota_guardian"
  prompt_paste: "adapters/prompt_paste/api-quota-guardian.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: false
  pure_llm: false

deployed_to: [claude-project]
requires:
  python: ">=3.10"
  packages: []
depends_on: []
last_used: 2026-05-09
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[api-quota-guardian 已啟動]`。

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
