---
name: nl-to-prompt-structurer
description: 自然語言 → 結構化 Prompt 翻譯器。純 Python 規則式（零 LLM API 成本）、中英雙語自動偵測、五段式 Markdown 輸出（角色/背景/任務/限制/輸出格式）。附加 query router 子模組可將 NL 解析為 P61 history-trend-query 的 Python API 呼叫。
version: 0.1.0-S1
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[nl-to-prompt-structurer 已啟動]`。

# 自然語言結構化器 (NL-to-Prompt Structurer) — v0.1 (Stage 1 地基)

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

## 📂 檔案結構（v0.1 S1 進度）

```
.agent/skills/nl-to-prompt-structurer/
├── SKILL.md                    ← 本檔
├── scripts/
│   ├── __init__.py
│   ├── lang_detector.py        ← S1 ✅  CJK ratio 偵測
│   ├── templates.py            ← S1 ✅  中英雙語五段式骨架
│   ├── intent_extractor.py     ← S2 ⏳  規則式抽 動詞/限制/格式
│   ├── structurer.py           ← S3 ⏳  PromptStructurer 主類別
│   └── query_router.py         ← S4 ⏳  NL → P61 API 呼叫
├── resources/
│   └── keyword_dict.json       ← S1 ✅  動詞/限制/格式關鍵字
└── test_skill.py               ← S1 ✅  10 項
```

---

## 🪜 五階段路線

| Stage | 內容 | 狀態 |
|---|---|---|
| **S1 地基** | lang_detector + templates + keyword_dict | ✅ |
| S2 抽取核心 | intent_extractor 規則式抽三類詞 | ⏳ |
| S3 主類別 + Slash | PromptStructurer + `/prompt` | ⏳ |
| S4 Query Router | NL → P61 `hero_trend` 等呼叫 | ⏳ |

---

## 📐 五段式輸出結構

中文：`角色 / 背景 / 任務 / 限制 / 輸出格式`
英文：`Role / Context / Task / Constraints / Output Format`

未填欄位：中文顯示「（未指定）」、英文顯示 `(unspecified)`。

---

## 🔧 S1 介面預覽

```python
from scripts.lang_detector import detect_lang
from scripts.templates import render_skeleton

detect_lang("最近兩週悟空怎樣")        # → "zh"
detect_lang("How is Wukong recently") # → "en"

render_skeleton(lang="zh", slots={"task": "整理今天戰報"})
# → 五段式 Markdown，未填欄位顯示「（未指定）」
```

---

*最後更新：2026-04-26 / Phase 62 S1 收官*
