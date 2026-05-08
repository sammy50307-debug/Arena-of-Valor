---
name: semantic-cache-shield
type: exec
status: stale
schema_version: 1
version: 1.0.0
description: 特徵+雜湊值攔截高同質洗版文章，零 Token 消耗從快取直接回傳

when_to_use:
  - 需要過濾論壇中大量重複/洗版文章
  - 抓取的文章有高度同質性，想避免重複 LLM 分析
  - 需要加速大量文章處理時（快取命中率高時有效）
when_NOT_to_use:
  - 首次抓取文章（快取為空時效果有限）
  - 需要分析全部文章（不希望過濾任何內容）
trigger_keywords: [快取, 洗版, 語意快取, 重複文章過濾, cache, semantic, 洗版文章, 去重]

example_invocations:
  - input: "這堆文章很多洗版的，幫我過濾掉"
    skill: semantic-cache-shield
    v1_trigger_block: |
      🪧 [semantic-cache-shield 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「洗版文章過濾」
      ├─ 信心分數：0.85
      ├─ 來源層：smart-task-router (L2)
      └─ 動作：執行 semantic-cache-shield

entry_points:
  cli: "python -m skills.semantic_cache_shield"
  import: "skills.semantic_cache_shield"
  prompt_paste: "adapters/prompt_paste/semantic-cache-shield.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: true
  pure_llm: false

deployed_to: [gemini-global]
requires:
  python: ">=3.10"
  packages: []
depends_on: []
last_used: 2026-04-19
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[semantic-cache-shield 已啟動]`。

# 語意快取神盾 (Semantic Cache Shield)

這是一套為「芽芽戰情室」量身打造的防禦型 AI Agent Skill。在大型遊戲賽事或改版期間，論壇（如巴哈姆特、Dcard）往往會出現大量複製貼上或內容極度相似的「洗版文」。若讓每個相似文本都經過大語言模型（LLM）運算，將產生可怕的 Token 帳單與冗長的 API 等待時間。

透過建立輕量級的本地 SQLite 快取資料庫，本特種兵將在文本送達 LLM 之前進行攔截並快速比對，如果此篇戰情之前已經被解析過，將直接「無損回傳」上次的心得總結。

## 🎯 核心工作流程

1. **攔截與計算**：讀入經過 Markdown 蒸餾後的純淨文本，透過演算法（例如 SHA-256 Hash 或 Jaccard 相似度）抽出文章的本質特徵。
2. **快取池守望**：去本地 `resources/yaya_cache.db` 中比對。
3. **無傷撤退 (Cache Hit)**：如果發現高度重疊，立刻中止呼叫 LLM，直接回傳快取中的 JSON 情感分析與報告。
4. **深入敵陣 (Cache Miss)**：如果這是一篇史無前例的新觀點文章，就放行交給 LLM 解析，並將 LLM 算出的全新結果「存入快取池中」，做為下次防守的基石。

## 🛠️ 目錄結構

```
semantic-cache-shield/
├── SKILL.md                 # 您正在閱讀的技能指令核心
├── scripts/
│   └── cache_engine.py      # 快取神盾的核心驅動引擎 (封裝 SQLite)
├── examples/
│   └── text_a.md            # 測試用原始文章
│   └── text_b_spam.md       # 測試用洗版文章 (高度相似)
└── resources/
    └── yaya_cache.db        # 自動生成的本地輕量型記憶迴路
```

## 🚀 對話與 CLI 調用方式

### AI 智能觸發
> 「使用快取神盾幫我判斷這篇文章之前有沒有看過，如果沒有請交給 LLM 分析後存起來。」

### CLI 查詢管理
```bash
# 測試快取寫入與命中效果
python .agent/skills/semantic-cache-shield/scripts/test_skill.py
```

---

## 🖥️ 終端執行（P71.3）

```bash
cd .agent/skills/semantic-cache-shield

# 說明
python __main__.py --help

# 查詢快取統計
python __main__.py stats
python __main__.py stats --output json

# 查詢快取命中
python __main__.py lookup "芽芽最近走勢"
python __main__.py lookup "芽芽最近走勢" --output json

# 儲存查詢結果至快取
python __main__.py store "芽芽最近走勢" "回答內容..."

# NO_COLOR（CI 日誌）
NO_COLOR=1 python __main__.py stats
```

依賴：Python 原生 `sqlite3`，無需額外安裝。
