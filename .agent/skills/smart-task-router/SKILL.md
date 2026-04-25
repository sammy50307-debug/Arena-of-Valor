---
name: smart-task-router
description: 智能任務路由器。根據輸入的自然語言描述，自動比對關鍵字並判斷最適合的特種兵技能，回傳路由決策與信心等級，讓戰情室大腦能精準指派任務。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[smart-task-router 已啟動]`。

# 智能任務路由器 (Smart Task Router)

這是「芽芽戰情室」Milestone 3 的第二支特種兵 (Phase 53)。在擁有 10 支特種兵後，若每次都要人工決定「該用哪隻特種兵」，效率極低且容易出錯。本路由器透過關鍵字比對演算法，自動分析任務描述並推薦最適合的特種兵。

## 🎯 核心工作流程

1. **載入技能冊 (Skill Registry)**：從 `skill_registry.json` 讀取所有已登記的 10 支特種兵及其關鍵字。
2. **關鍵字評分 (Keyword Scoring)**：對每支特種兵計算與輸入 query 的關鍵字匹配分數。
3. **路由決策 (Routing Decision)**：選出分數最高者作為主要推薦，並附上 TOP-3 候選清單。
4. **信心評估 (Confidence)**：匹配分數 ≥ 2 = HIGH，否則 = LOW。

## 🛠️ 目錄結構

```
smart-task-router/
├── SKILL.md
├── scripts/
│   └── router.py             # SmartTaskRouter 主類別
├── resources/
│   └── skill_registry.json   # 10 支特種兵登記冊（含關鍵字與描述）
└── test_skill.py             # 6 項自動化測試
```

## 📊 輸出格式

```json
{
  "query": "輸入的任務描述",
  "routing_decision": "firecrawl-dynamic-breacher",
  "task_type": "scrape",
  "task_type_desc": "情報收集類 — 從網路抓取原始資料",
  "confidence": "HIGH",
  "recommendations": [
    { "skill_id": "...", "skill_name": "...", "match_score": 3 }
  ],
  "total_candidates": 2
}
```

## 🚀 相依套件
- 純 Python 標準庫（`json`, `pathlib`），無需額外安裝。
