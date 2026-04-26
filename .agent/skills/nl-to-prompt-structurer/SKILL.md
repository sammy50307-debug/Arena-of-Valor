---
name: nl-to-prompt-structurer
description: 自然語言 → 結構化 Prompt 翻譯器。純 Python 規則式（零 LLM API 成本）、中英雙語自動偵測、五段式 Markdown 輸出（角色/背景/任務/限制/輸出格式）。附加 query router 子模組可將 NL 解析為 P61 history-trend-query 的 Python API 呼叫。
version: 0.3.0-S3
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[nl-to-prompt-structurer 已啟動]`。

# 自然語言結構化器 (NL-to-Prompt Structurer) — v0.3 (Stage 3 主類別 + Slash)

「芽芽戰情室」**Milestone 5 Phase 62** 旗艦特種兵。把口語化的 prompt 套上五段式骨架，降低每次跟 AI 溝通要手動套格式的心智負擔；附加 query router 在 S4 接上 P61 的自然語言查詢介面。

---

## 🎯 定位與分工

| 角色 | 職責 |
|---|---|
| **Phase 62 本 skill** | 自然語言 → 五段式 Prompt（純規則） |
| `query_router`（S4） | 自然語言 → P61 `q.hero_trend(...)` 等 Python 呼叫 |
| Phase 61 `history-trend-query` | 被 query_router 呼叫的時序資料源 |
| `cot-prompt-compactor` | 既有 prompt 精煉（不在本 skill scope） |

**設計原則**：通用型（不限 AOV）、純 Python 規則式（零 LLM）、中英雙語、可手動覆寫 lang。

---

## 📂 檔案結構（v0.3 S3 進度）

```
.agent/skills/nl-to-prompt-structurer/
├── SKILL.md                    ← 本檔
├── scripts/
│   ├── __init__.py
│   ├── lang_detector.py        ← S1 ✅  CJK ratio 偵測
│   ├── templates.py            ← S1 ✅  中英雙語五段式骨架
│   ├── intent_extractor.py     ← S2 ✅  規則式抽 動詞/限制/格式
│   ├── structurer.py           ← S3 ✅  PromptStructurer 主類別
│   └── query_router.py         ← S4 ⏳  NL → P61 API 呼叫
├── resources/
│   └── keyword_dict.json       ← S2 ✅  v0.2，雙語三類 35~44 詞
└── test_skill.py               ← S3 ✅  31 項

.claude/commands/
└── prompt.md                   ← S3 ✅  /prompt slash 上架
```

---

## 🪜 五階段路線

| Stage | 內容 | 狀態 |
|---|---|---|
| **S1 地基** | lang_detector + templates + keyword_dict | ✅ |
| **S2 抽取核心** | intent_extractor 規則式抽三類詞 | ✅ |
| **S3 主類別 + Slash** | PromptStructurer + `/prompt` + escape + dedupe + role_inference | ✅ |
| S4 Query Router | NL → P61 `hero_trend` 等呼叫 | ⏳ |

---

## 📐 五段式輸出結構

中文：`角色 / 背景 / 任務 / 限制 / 輸出格式`
英文：`Role / Context / Task / Constraints / Output Format`

未填欄位：中文顯示「（未指定）」、英文顯示 `(unspecified)`。

---

## 🔧 介面（v0.3）

### Python API

```python
from scripts.structurer import PromptStructurer

s = PromptStructurer()
md = s.structure("用 markdown 整理今天戰報，300 字以內")
# → 五段式 Markdown，role 自動推為「資料整理員」

# 強制英文
s.structure("整理戰報", lang="en")

# 覆寫角色（不走推斷）
s.structure("翻譯這段", role="法律譯者")

# 精簡模式（只 task + output_format 兩段）
s.structure("列重點", mode="lite")

# 補背景
s.structure("寫一篇文", context="目標讀者：高中生")
```

### Slash command `/prompt`

`/prompt <text> [--lang zh|en] [--role <角色>] [--mode full|lite] [--context <背景>]`

詳見 `.claude/commands/prompt.md`。

## 🛡️ 內建防護

| 機制 | 解決 | 說明 |
|---|---|---|
| `_escape_slot` | S1 R5 | 行首 `#` heading 跳脫成 `\#`，防止破壞五段式 |
| `_dedupe_overlap` | S2 R7 | constraints 互為 substring 時保長者 |
| `_infer_role` | S1 R3 | 依 task_verb 規則映射角色（翻譯→譯者、analyze→Analyst...） |
| lang fallback 鏈 | S1 R1 | 手動 > 預設 > 自動偵測；無效值回 zh |

## 🎭 role_inference 規則對照（部分）

| zh 動詞 | 推為角色 | en verb | inferred role |
|---|---|---|---|
| 翻譯 | 譯者 | translate | Translator |
| 撰寫 / 寫 / 改寫 / 潤飾 | 寫手 | write / rewrite / polish | Writer |
| 分析 / 評估 / 比較 | 分析師 | analyze / evaluate / compare | Analyst |
| 整理 / 歸納 / 排序 | 資料整理員 | summarize / outline | Summarizer |
| 查詢 / 找 / 搜尋 | 情報員 | query / find / search | Researcher |
| 規劃 / 設計 / 預測 | 策略顧問 | plan / design / predict | Strategist |
| 解釋 / 說明 / 回答 | 說明員 | explain / describe / answer | Explainer |
| 推薦 / 建議 | 推薦顧問 | recommend / suggest | Advisor |

未命中對照表 → fallback「通用助理」/ `Generalist Assistant`。

---

*最後更新：2026-04-26 / Phase 62 S3 收官*
