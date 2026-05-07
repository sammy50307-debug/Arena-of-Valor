# Postmortem：旗艦展演模式被迫觸發（P69）

**日期**：2026-05-08
**Phase**：P69 — 旗艦展演模式根治
**嚴重度**：中（使用者看到假資料，但系統不崩潰）
**相關 Phase**：P63.4（2026-05-03 同主題上一次修復）

---

## 症狀

主公在每日報告中持續看到「旗艦展演模式」假資料（mock 文章、mock 分析），而非真實輿情分析結果。報告頂部 metadata comment 顯示 `mode: showcase`。

---

## 根因

### 主因（A 假設確認）

Gemini 免費 API 每日配額耗盡（HTTP 429）。

觸發鏈：

```
GHA 排程執行
  → pre-flight check 偵測 429（gemini_client.py:231-235）
  → batch_chat 拋出 httpx.HTTPStatusError
  → analyze_posts 捕捉 → showcase=True（sentiment.py:203-207）
  → 回傳 mock 假資料（is_showcase=True）
  → main.py 傳播 → active_showcase=True → mode="showcase"
```

### 次要 Bug 1（B9）

`generate_daily_summary` 在 showcase=True 時跳過 L2 快取讀取（正確），但**仍然呼叫 `self.llm.chat`**（錯誤）。這導致：
- 配額耗盡後又浪費 1-2 次 LLM 呼叫
- 若 `generate_daily_summary` 也遇 429，引發雪崩式降級

### 次要 Bug 2（F3）

`main.py` 外層 `except Exception` 的 `_meta["mode"]` 寫死為 `"showcase"`，即使 showcase=False（非配額問題的一般 Exception），也顯示旗艦展演，語意誤導主公。

---

## 三假設排除說明

| 假設 | 結論 | 證據 |
|---|---|---|
| A：API 配額耗盡（429） | **✅ 確認主因** | gemini_client.py 斷路器 + sentiment.py catch |
| B：main.py 呼叫端 bug | ❌ 排除 | main.py:280 傳 showcase=showcase，GHA 不傳 --showcase，預設 False |
| C：L2 快取污染 | ❌ 排除 | sentiment.py:296-297 已防 showcase 寫 L1；`cache_hit: 0/2` 顯示無快取命中 |

---

## 修法（P69）

| 項 | 檔案 | 修法 |
|---|---|---|
| F1 | `analyzer/sentiment.py` | analyze_posts 429 except 加 `quota_error_triggered=True`，回傳 dict 帶 `quota_error` flag |
| A7（治本） | `analyzer/sentiment.py` | `generate_daily_summary` showcase=True 時直接走 `_generate_fallback_summary`，0 LLM 呼叫 |
| F2 | `main.py` | mode 四態化：`production / showcase / showcase_forced / error_fallback` |
| F3 | `main.py` | 外層 except 的 `"mode"` 改條件式 |
| B9 | `reporter/generator.py` | metadata comment 加四態中文標示（✅/🎭/⚠️/❌） |

---

## 教訓

**「Graceful degradation 必須讓上層能區分主動 vs 被迫」**

設計初衷是好的（API 掛掉時給主公看假資料比白頁好），但主動展演（`--showcase`）和被迫展演（429 配額耗盡）顯示一樣的 `mode: showcase`，導致主公無法判斷今天是真的 API 壞了，還是有人跑了測試指令。

**通則**：任何 fallback 路徑都應攜帶「為什麼 fallback」的 reason，而非只帶「已 fallback」的狀態。

---

## 預防措施

1. `mode: showcase_forced` 在 metadata comment 顯示 `⚠️ 配額耗盡被迫展演`，主公一眼可辨
2. `generate_daily_summary` 的 showcase 路徑不再浪費配額
3. 建議：觀察 GHA 每日 429 頻率，若連 3 日 quota_error → 考慮升級 Gemini API 方案或調整抓取量

---

## 關聯文件

- 上一次同主題：`2026-05-03-phase-63-4-showcase-rootcause.md`
- TASK_HISTORY：P63.4 / P69 段
