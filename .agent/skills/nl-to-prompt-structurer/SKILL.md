---
name: nl-to-prompt-structurer
description: 自然語言 → 結構化 Prompt 翻譯器。純 Python 規則式（零 LLM API 成本）、中英雙語自動偵測、五段式 Markdown 輸出（角色/背景/任務/限制/輸出格式）。附加 query router 子模組可將 NL 解析為 P61 history-trend-query 的 Python API 呼叫。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[nl-to-prompt-structurer 已啟動]`。

# 自然語言結構化器 (NL-to-Prompt Structurer) — v1.0 (Phase 62 收官)

「芽芽戰情室」**Milestone 5 Phase 62** 旗艦特種兵。把口語化的 prompt 套上五段式骨架，降低每次跟 AI 溝通要手動套格式的心智負擔；附加 query router 把自然語言查詢翻譯成 P61 的 Python API 呼叫。

---

## 🎯 定位與分工

| 角色 | 職責 |
|---|---|
| **Phase 62 本 skill** | 自然語言 → 五段式 Prompt（純規則） |
| `query_router`（S4） | 自然語言 → P61 `q.hero_trend(...)` 等呼叫規格 |
| Phase 61 `history-trend-query` | 被 query_router 呼叫的時序資料源 |
| `cot-prompt-compactor` | 既有 prompt 精煉（不在本 skill scope） |

**設計原則**：通用型（不限 AOV）、純 Python 規則式（零 LLM）、中英雙語、可手動覆寫 lang。

---

## 📂 檔案結構（v1.0 完整）

```
.agent/skills/nl-to-prompt-structurer/
├── SKILL.md                    ← 本檔
├── scripts/
│   ├── __init__.py
│   ├── lang_detector.py        ← S1 ✅  CJK ratio 偵測
│   ├── templates.py            ← S1 ✅  中英雙語五段式骨架
│   ├── intent_extractor.py     ← S2 ✅  規則式抽 動詞/限制/格式
│   ├── structurer.py           ← S3 ✅  PromptStructurer 主類別
│   ├── query_router.py         ← S4 ✅  NL → P61 API 呼叫規格
│   └── cli.py                  ← S4 ✅  安全 CLI 入口（解 R15）
├── resources/
│   └── keyword_dict.json       ← S2 ✅  v0.2，雙語三類 35~44 詞
└── test_skill.py               ← S4 ✅  43 項全綠

.claude/commands/
└── prompt.md                   ← S4 ✅  /prompt slash（改用 cli.py）
```

---

## 🪜 四階段路線（全部完成）

| Stage | 內容 | 狀態 | 測試 |
|---|---|---|---|
| **S1 地基** | lang_detector + templates + keyword_dict | ✅ | 10 |
| **S2 抽取核心** | intent_extractor 規則式抽三類詞 + 字典擴充 | ✅ | +11 |
| **S3 主類別 + Slash** | PromptStructurer + `/prompt` + escape + dedupe + role_inference | ✅ | +10 |
| **S4 Query Router + CLI** | query_router（NL→P61）+ cli.py（解 R15）| ✅ | +12 |
| | **累計** | | **43** |

---

## 📐 五段式輸出結構

中文：`角色 / 背景 / 任務 / 限制 / 輸出格式`
英文：`Role / Context / Task / Constraints / Output Format`

未填欄位：中文顯示「（未指定）」、英文顯示 `(unspecified)`。

---

## 🔧 介面（v1.0）

### Python API — PromptStructurer

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

### Python API — Query Router

```python
from scripts.query_router import route_query

result = route_query("芽芽最近兩週聲量")
# → {"api": "hero_trend", "kwargs": {"hero_name": "芽芽", "days": 14}, ...}

result = route_query("整體輿情最近一個月")
# → {"api": "overall_trend", "kwargs": {"days": 30}, ...}

result = route_query("各平台聲量 7 天")
# → {"api": "platform_trend", "kwargs": {"days": 7}, ...}

# 手動提供英雄候選（跳過 data/ 動態掃描）
result = route_query("芽芽和蝶舞對比", hero_candidates=["芽芽", "蝶舞"])
# → {"api": "heroes_trend", "kwargs": {"hero_names": ["芽芽", "蝶舞"], ...}, ...}
```

### CLI（解 R15 特殊字元）

```bash
# prompt 子命令
py scripts/cli.py prompt "用 markdown 整理今天戰報"
py scripts/cli.py prompt --stdin              # 從 stdin 讀取
py scripts/cli.py prompt --lang en "translate"
py scripts/cli.py prompt --role 譯者 "翻譯這段"
py scripts/cli.py prompt --mode lite "列重點"

# route 子命令
py scripts/cli.py route "芽芽最近兩週聲量"
py scripts/cli.py route --stdin
```

### Slash command `/prompt`

`/prompt <text> [--lang zh|en] [--role <角色>] [--mode full|lite] [--context <背景>]`

詳見 `.claude/commands/prompt.md`。已改用 `cli.py` 入口，免疫特殊字元。

---

## 🛡️ 內建防護

| 機制 | 解決 | 說明 |
|---|---|---|
| `_escape_slot` | S1 R5 | 行首 `#` heading 跳脫成 `\#`，防止破壞五段式 |
| `_dedupe_overlap` | S2 R7 | constraints 互為 substring 時保長者 |
| `_infer_role` | S1 R3 | 依 task_verb 規則映射角色（翻譯→譯者、analyze→Analyst...） |
| lang fallback 鏈 | S1 R1 | 手動 > 預設 > 自動偵測；無效值回 zh |
| `cli.py` | S3 R15 | 安全 CLI 入口，免疫 shell 特殊字元 |
| 動態英雄掃描 | S4 | 從 data/ 聯集 hero_stats keys，零維護自適應 |
| fallback 路由 | S4 | 無法判定時走 overall_trend，`fallback=true` 標記 |

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

## 🗺️ Query Router 路由規則

| NL 關鍵訊號 | 路由至 | 範例 |
|---|---|---|
| 1 個英雄名 | `hero_trend` | 「芽芽最近兩週」 |
| 2~5 個英雄名 | `heroes_trend` | 「芽芽和蝶舞對比 7 天」 |
| 「整體」/「overall」 | `overall_trend` | 「整體輿情一個月」 |
| 「平台」/「platform」 | `platform_trend` | 「各平台聲量 7 天」 |
| 無法判定 | `overall_trend` (fallback) | 「Hello world」 |

天數解析支援：數字+單位（天/日/週/月/day/week/month）、中文數字（三週→21）。
日期解析支援：`YYYY-MM-DD`、昨天/前天/yesterday。

---

*最後更新：2026-04-26 / Phase 62 S4 收官 → v1.0.0*
