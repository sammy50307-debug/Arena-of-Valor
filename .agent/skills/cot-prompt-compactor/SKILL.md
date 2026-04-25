---
name: cot-prompt-compactor
description: 思維鏈提示詞壓縮機，專門將原有的肥胖 Prompt 轉換為嚴謹的 Pydantic 模型，強制啟用大型語言模型的 Structured Outputs 機制，消滅幻覺並節約 Token。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[cot-prompt-compactor 已啟動]`。

# 思維鏈與結構化萃取器 (CoT Prompt Compactor)

這是「芽芽戰情室」的第二道特種部隊 (Phase 47)。原先我們依賴將龐大的 JSON Schema 寫在 Prompt 裡面，祈禱語言模型依照格式吐回文字，這不僅耗費大量的輸入 Token，有時還會因模型產出多餘括號而導致 `json.loads` 崩潰。

本 Skill 透過導入 `Pydantic` 定義嚴格的資料類別，並將 Prompt 中的「廢話」與「JSON 範例」徹底壓縮剔除，強制模型啟用 **Structured Outputs** 模式。

## 🎯 核心工作流程

1. **結構定義 (Schema Definition)**：在 `prompts_schema.py` 透過 Pydantic 定義所有資料模型（包含單發分析與日報彙整）。
2. **Prompt 瘦身 (Compaction)**：刪除 `prompts.py` 中一切關於「你必須以 JSON 格式回覆」的冗長宣示，只留下純粹的情境與分析目標。
3. **強制綑綁 (Enforced Binding)**：在呼叫 Gemini 或是 OpenAI 時，將 Pydantic 模型直接傳入 `response_schema`，確保 100% 機器的結構化對接。

## 🛠️ 目錄結構

```
cot-prompt-compactor/
├── SKILL.md                 # 您正在閱讀的技能指令核心
├── scripts/
│   ├── compactor.py         # 壓縮後的精簡 Prompt 文本
│   └── prompts_schema.py    # 最核心的 Pydantic 模型定義
└── examples/
    └── schema_output.json   # 經過驗證的輸出結果
```

## 🚀 相依套件要求
- `pydantic`：目前業界公認最強的 Python 資料驗證與設定管理庫。
