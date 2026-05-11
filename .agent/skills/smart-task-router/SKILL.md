---
name: smart-task-router
type: exec
status: in-use
schema_version: 1
version: 2.0.0
description: L2 路由引擎：純規則關鍵字比對，自動路由至最適 skill 並輸出 V1 觸發塊

when_to_use:
  - 收到模糊任務描述，需要判斷該用哪個 skill 時
  - 主公說「幫我…」但沒點名 skill 時，LLM 自動呼叫此路由器
  - 多 skill 可能匹配，需要信心分數排序

when_NOT_to_use:
  - 主公已明確點名 skill（直接執行即可，不需路由）
  - 查詢 AOV 英雄走勢 → 用 history-trend-query
  - 驗證英雄名稱 → 用 hallucination-judge

trigger_keywords:
  - 路由
  - 分派任務
  - 該用哪個skill
  - 哪個特種兵
  - 任務分配
  - smart-task-router
  - 自動路由
  - 判斷技能

entry_points:
  cli: "python __main__.py \"<query>\""
  import: "from scripts.router import SmartTaskRouter"
  prompt_paste: "adapters/prompt_paste/smart-task-router.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: true

deployed_to: []
requires:
  python: ">=3.10"
  packages: []
depends_on: []
last_used: "2026-05-11"
---

> ⚡ **啟動標記**：執行此 skill 時，回覆首段必須標示 V1 觸發塊（見下方格式）。

# Smart Task Router — L2 路由引擎（P71.6）

對輸入的自然語言描述，使用 `skills/registry.json`（S1 schema）中的 `trigger_keywords` + `when_to_use` 計算數值信心分數，依閾值決定動作。

**不呼叫 LLM、不燒 token，純 Python 規則匹配。**

## 🎯 信心分數 × 動作閾值（D3 決定）

| 信心分數 | 動作 | 說明 |
|---|---|---|
| ≥ 0.9 | **AUTO** | 直接執行，印 V1 觸發塊 |
| 0.7 ~ 0.89 | **CONFIRM** | 印 V1 觸發塊 + 詢問主公「[Y/n]」|
| < 0.7 | **NO_MATCH** | 不觸發，可口頭建議 |

## 📊 信心算法

```
trigger_keywords 命中：每個 +0.2（強匹配）
when_to_use 命中：每條描述 ≥2 詞命中 +0.05（弱匹配）
when_NOT_to_use 命中：每條描述 ≥2 詞命中 −0.2（負向）
最終：min(max(score, 0.0), 1.0)
```

## 🪧 V1 觸發塊格式（任何 skill 啟動必印）

```
🪧 [<skill-name> 已觸發]
├─ 觸發理由：匹配 trigger_keyword 「芽芽聲量」
├─ 信心分數：0.92
├─ 來源層：smart-task-router (L2)
└─ 動作：執行 history-trend-query
```

終端 plain 模式（`NO_COLOR=1` 或非 TTY）：
```
[<skill-name> 已觸發] 觸發理由: ... 信心: 0.92 來源: smart-task-router (L2) 動作: 執行 <skill-name>
```

## 🛠️ 目錄結構

```
.agent/skills/smart-task-router/
├── SKILL.md                  # 本文件（S1 schema）
├── __main__.py               # CLI 入口
├── scripts/
│   └── router.py             # SmartTaskRouter 核心邏輯
├── resources/
│   └── skill_registry.json   # 舊版（P53 時代，僅備份）
└── test_skill.py             # 自動化測試
```

## 🚀 終端執行

```bash
# 路由查詢（rich 輸出，自動偵測 TTY）
python __main__.py "我要查詢芽芽最近一週的聲量走勢"

# JSON 輸出（CI / pipeline 用）
python __main__.py "幫我驗證這份戰報的英雄名稱" --output json

# Plain 輸出（NO_COLOR 模式）
NO_COLOR=1 python __main__.py "AI 新聞今天有什麼"

# 列出所有已登記 skill
python __main__.py list
python __main__.py list --output json

# 說明
python __main__.py --help
```

**範例輸出（AUTO 模式）：**
```
🪧 [history-trend-query 已觸發]
├─ 觸發理由：匹配 trigger_keyword 「聲量走勢」
├─ 信心分數：0.40
├─ 來源層：smart-task-router (L2)
└─ 動作：直接執行 history-trend-query
```

## 📥 輸入 / 輸出 Schema

### 輸入

| 參數 | 說明 |
|---|---|
| `query` | 自然語言任務描述（任意長度）|

### 輸出（JSON 模式）

```json
{
  "query": "我要查詢芽芽最近聲量走勢",
  "action": "AUTO",
  "best_match": {
    "name": "history-trend-query",
    "confidence": 0.40,
    "description": "...",
    "type": "pipe",
    "status": "in-use",
    "entry_points": {}
  },
  "confidence": 0.40,
  "candidates": [
    { "name": "history-trend-query", "confidence": 0.40, ... },
    { "name": "trend-anomaly-detector", "confidence": 0.20, ... }
  ],
  "registry_path": "D:/Coding Project/Arena of Valor/skills/registry.json"
}
```

## 🔗 相依

- 純 Python 標準庫（`json`, `pathlib`, `argparse`, `os`, `sys`），無額外套件
- 讀取 `skills/registry.json`（S1 schema，P71.2 建立）
