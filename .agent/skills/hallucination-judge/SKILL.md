---
name: hallucination-judge
type: data
status: in-use
schema_version: 1
version: 1.0.0
description: 校驗 AI 生成戰報中英雄名稱與數值合理性，防止幻覺污染報告

when_to_use:
  - AI 生成英雄戰報後需要驗證英雄名稱合法性
  - 驗證情緒分數、勝率等數值是否在合理範圍
  - 懷疑 AI 回答含有幻覺英雄名稱時
when_NOT_to_use:
  - 查詢英雄走勢/聲量 → 用 history-trend-query
  - 抓取論壇原始資料 → 用 multi-thread-synthesizer
trigger_keywords: [幻覺, 英雄名稱驗證, 白名單, 戰報驗證, hallucination, 驗證英雄, 英雄白名單, 假英雄]

example_invocations:
  - input: "確認這份戰報的英雄名稱是否正確"
    skill: hallucination-judge
    v1_trigger_block: |
      🪧 [hallucination-judge 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「英雄名稱驗證」
      ├─ 信心分數：0.91
      ├─ 來源層：主公口頭
      └─ 動作：執行 hallucination-judge

entry_points:
  cli: "python -m skills.hallucination_judge"
  import: "skills.hallucination_judge"
  prompt_paste: "adapters/prompt_paste/hallucination-judge.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: false
  pure_llm: true

deployed_to: [claude-project]
requires:
  python: ">=3.10"
  packages: []
depends_on: []
last_used: 2026-05-09
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[hallucination-judge 已啟動]`。

# AI 幻覺裁判 (Hallucination Judge)

這是「芽芽戰情室」Milestone 3 的第一支特種兵 (Phase 52)。過去 AI 在生成每日戰情報告時，偶有出現虛構英雄名稱（如「滅世龍帝」、「無盡黑暗者」）或荒謬數值（勝率 150%、情緒分數 2.5）的幻覺問題。本裁判以三層防線確保每份戰報的資料品質。

## 🎯 三層防線

1. **英雄名稱白名單比對**：載入 `hero_whitelist.json` 中的官方英雄清單，擷取文本中所有被標記為英雄的名稱，過濾不在名單中的未知英雄。
2. **數值範圍校驗**：自動掃描 `sentiment_score`（-1~1）、勝率（0~100%）、負面比例（0~100%）等關鍵數值，偵測越界值。
3. **幻覺特徵模式偵測**：透過正規表達式偵測明顯不合理的敘述（如「勝率 XXX%」超過三位數）。

## 🛠️ 目錄結構

```
hallucination-judge/
├── SKILL.md
├── scripts/
│   └── judge.py          # HallucinationJudge 主類別
├── resources/
│   └── hero_whitelist.json   # 官方英雄白名單（含中英文名稱）
└── test_skill.py         # 5 項自動化測試
```

## 📊 輸出格式

```json
{
  "verdict": "PASS | WARN | FAIL",
  "confidence_score": 100,
  "issues": [],
  "details": {
    "hero_check": { "unknown_heroes": [], "passed": true },
    "numeric_check": { "violations": [], "passed": true },
    "pattern_check": { "triggered_patterns": [], "passed": true }
  }
}
```

## 🚀 相依套件
- 純 Python 標準庫（`re`, `json`），無需額外安裝。
