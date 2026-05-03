# Postmortem — P64 Cache 高層化重構

- **日期**：2026-05-03
- **嚴重度**：中（功能降級，非資料損毀）
- **Phase**：P64

---

## 事件摘要

P63.4 C-B 驗收時，Gemini free tier 三備援模型全部 429，報告降級為 showcase 模式。根因為 cache key 設計讓每日例行跑 100% miss，每次都打滿 LLM 呼叫。

## 根本原因

```
舊 cache key = MD5(system_prompt + user_prompt)
user_prompt 包含每篇貼文實際內容（每天不同）
→ 每日 100% cache miss → LLM 呼叫滿載 → 429
```

## 修復措施

| 層級 | 修復 |
|---|---|
| L1 hero-level cache | `hero:{hero_name}:{date}` — 當天同英雄整批結果快取，零 LLM 呼叫 |
| L2 prompt-level cache | 保留舊 MD5 機制，加 `prompt:` prefix，v1→v2 migration |
| pre-flight check | batch_chat 入口探活，429 直接熔斷省 retry 等待 |
| wait 加長 | `[60,120]` → `[60,300,900]` |
| Lockfile | 30 分鐘冷卻，防重複觸發 |
| B2 concurrency group | workflow 防連點兩次 dispatch |

## 附帶發現（不歸 P64 責任）

`analyze_posts` showcase 路徑回傳 `list`，main.py 預期 `dict`，TypeError 被 outer except 吃掉，降級 `_empty_summary`。已登記 P65 B1。

## 學到的通則

1. **cache key 設計必須在 Phase 計畫書明列**：key 包含什麼欄位直接決定命中率。
2. **pre-flight 探活比長 retry 更有效率**：2.5 秒偵測 vs 3 分鐘空等。
3. **showcase 結果不能寫 L1**：防止壞資料污染快取，今後所有 cache 寫入都需標注「什麼情況不寫」。
