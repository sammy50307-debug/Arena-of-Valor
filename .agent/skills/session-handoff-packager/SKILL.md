---
name: session-handoff-packager
description: >
  跨視窗 / 跨模型對話打包器。在一個對話視窗收工前，自動打包「任務快照」，
  產出 lite（~400 tok）/ full（~1500 tok）兩版 Markdown，
  讓下個視窗（Claude / GPT / Gemini）零摩擦接手。
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[session-handoff-packager 已啟動]`。

# 📦 Session Handoff Packager

## 定位

- **auto-memory** 管「長期事實」（角色、偏好、專案進度）
- **本 Skill** 管「當下任務進行到哪、剛才討論的決策脈絡」

兩者互補，合起來實現完整的跨視窗記憶。

## 觸發時機

當使用者說出以下任一句時觸發：
- 「幫我打包」
- 「打包交接」
- 「handoff」
- 「這個視窗快結束了，幫我整理一下」

## 使用流程

### 方式 A：對話觸發（推薦）

AI 助理收到打包指令後，整理當前對話脈絡，呼叫 `packager.py`：

```python
import sys
sys.path.insert(0, str(project_root / ".agent/skills/session-handoff-packager/scripts"))
from packager import SessionHandoffPackager

p = SessionHandoffPackager(project_root=Path("D:/Coding Project/Arena of Valor"))
result = p.pack(
    doing="Phase 60 Session Handoff Packager 開發中",
    stuck_at="",
    next_step="跑完測試後更新 TASK_HISTORY.md",
    decisions=["全域寫入走 Antigravity 體系", "觸發方式：對話+CLI 雙軌"],
    rejected=["寫入 ~/.claude/handoff/ — 改走 ~/.gemini/antigravity/handoff/"],
    pending=[],
    glossary={"芽芽": "傳說對決角色 Yena", "戰情室": "本專案的暱稱"},
    quotes=["主公：「確認上個階段完全處理完畢的話，我們開始 P60 吧」"],
)
paths = p.save(result)
```

### 方式 B：CLI 指令

```bash
py .agent/skills/session-handoff-packager/scripts/packager.py \
    --doing "Phase 60 開發中" \
    --stuck "測試第 3 項失敗" \
    --next "修正 bootstrap 路徑" \
    --decisions "全域走 Antigravity" "雙軌觸發" \
    --rejected "寫入 ~/.claude/" \
    --dry-run
```

## 輸出結構

### 分層設計（L-1 ~ L3）

| 層級 | 內容 | lite 版 | full 版 |
|---|---|---|---|
| L-1 | Bootstrap 開局讀檔清單 | ✅ 列路徑 | ✅ 內嵌部分全文 |
| L0 | 開場引信（做什麼/卡哪/下一步） | ✅ | ✅ |
| L1 | 核心決策 + 名詞表 + 禁區 | 名詞表+待決議 | ✅ 完整 |
| L2 | 待決議 + Git 環境快照 | — | ✅ |
| L3 | 關鍵原話引用 | — | ✅（有的話） |

### 雙檔輸出

| 檔案 | Token | 適用 |
|---|---|---|
| `handoff_YYYYMMDD_HHMM.md` | ~400 | Claude Code（能讀本地檔） |
| `handoff_YYYYMMDD_HHMM_full.md` | ~1500 | GPT / Gemini 等無法讀檔的模型 |

### 三路寫入（選項 C：最保險策略）

- `<project>/handoff/` — 專案內（版控可追蹤）
- `~/.gemini/antigravity/handoff/` — Antigravity 全域（跨專案存取）
- `~/.claude/handoff/` — Claude Code 全域（Claude 體系存取）

## 注意事項

- 純 Python 規則式，**零 LLM 成本**
- 不綁特定專案邏輯，**全專案通用**
- 請稱呼使用者為「主公」
