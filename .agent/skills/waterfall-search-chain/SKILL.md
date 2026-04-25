---
name: waterfall-search-chain
description: 瀑布式輪用搜尋鏈。依優先順序嘗試多個搜尋源（Tavily → DDG），前一個額度耗盡或失敗時自動切換下一個，確保日報在 Tavily 超額時仍能正常產出。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[waterfall-search-chain 已啟動]`。

# 瀑布式輪用搜尋鏈 (Waterfall Search Chain)

這是「芽芽戰情室」Milestone 4 的 Phase 56 特種兵。解決 Tavily API 月配額耗盡後系統無法搜集資料的問題。

## 🎯 輪用邏輯

```
① Tavily（付費 API，最高品質）
    ↓ 失敗 / 額度耗盡 / 空結果
② DDGSearcher（DuckDuckGo HTML，免費無限額）
    ↓ 失敗
③ 回傳空列表（觸發 pipeline 提前結束警報）
```

## 🛠️ 目錄結構

```
waterfall-search-chain/
├── SKILL.md
├── scripts/
│   └── waterfall.py      # WaterfallSearcher 包裝
└── test_skill.py         # 5 項自動化測試
```

## ⚙️ 額度耗盡偵測

| HTTP 狀態碼 | 判定 |
|-------------|------|
| 429 Too Many Requests | ✅ 額度耗盡 |
| 402 Payment Required  | ✅ 額度耗盡 |
| 403 Forbidden         | ✅ 額度耗盡 |
| 回應含 quota/exceeded | ✅ 額度耗盡 |

## 📊 輸出

```python
List[SearchResult]  # 與 TavilySearcher.search() 完全相容
```

## 🚀 相依套件

- `httpx`（已安裝）
- `beautifulsoup4`（已安裝）
- 純 Python 標準庫
