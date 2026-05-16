# 進行中 / 待動工 Phase 清單

> 更新日期：2026-05-16
> 來源：TASK_HISTORY.md 尾段 + NEXT_SESSION_HANDOFF.md + docs/RISK_REGISTRY.md
> 備註：本檔是索引，不是權威歷史；若與 TASK_HISTORY.md 衝突，以 TASK_HISTORY.md 為準。

## ⏳ 進行中

| Phase | 卡點 | 下一步 | 阻塞於 |
|---|---|---|---|
| — | 目前無進行中 Phase | 從待動工清單擇一 | 主公拍板 |

## 📋 凍結待動工

| Phase | 草案位置 | 阻塞於 |
|---|---|---|
| — | 目前無凍結待動工 Phase | 主公拍板下一個 open risk / enhancement |

## ✅ 已收官

| Phase | 收官日 | 備註 |
|---|---|---|
| P76 | 2026-05-16 | RISK_REGISTRY / HANDOFF 狀態清理；R-007/R-008 移至 Closed；handoff 最新已推 commit 對齊 `614dc13` |
| P70.6 | 2026-05-16 | `llm_cache.json` schema v3；新增 `last_accessed`、`CACHE_MAX_ENTRIES`、max entries LRU eviction；cache 單測 12 passed，全套 126 passed |
| P70.4 | 2026-05-16 | Gemini primary / OpenAI fallback；新增 fallback wrapper、OpenAI schema/cache 介面與 5 個 mock tests；全套 124 passed |
| P75 / R-014 | 2026-05-16 | 回填 P63/P64/P69/P70.3 blindspots；新增 B-011~B-022；M4 status 缺漏數 0；R-014 關閉 |
| P70.2 | 2026-05-16 | 新增 daily report health checker；workflow fallback push 後檢查 canonical report / metadata / landing / git clean；全套 119 passed |
| P74 / R-015 | 2026-05-16 | `test_dynamic_focus.py` 三處改 `asyncio.run`；單檔 5 passed，全套 112 passed；R-015 關閉 |
| P73 | 2026-05-15 | 模型選擇指引 v1.2 OpenAI / Codex 分支 |
| P72.0~P72.5 | 2026-05-14 | Skill metrics / backup / M3 / M4 / postmortem + RISK_REGISTRY |
| P71.2~P71.9 | 2026-05-09~2026-05-11 | Skill 永續化主線分段落地 |
| P70.3 | 2026-05-08 | LINE 滑動失靈修補；R-004 仍以人工 SOP 觀察 |
| P65 | 2026-05-07 | Top-5 News Cards 收官 |
| **61.1**（R20/R23/R24 根治）| 2026-05-03 | commit f697853，已 push |
| **63.1.0/1.1/1.2**（Landing Page 自動更新）| 2026-05-03 | commits 220f6ae / 714750b，已 push |
| **63.3 / 63.3.1**（Landing UI/UX 統一 + 補遺）| 2026-05-03 | TASK_HISTORY 已記錄收官 |
| 64（Cache 架構）| 2026-05-03 | E-C/E-D 明日驗收 |
| 64.1（Token 防線補強）| 2026-05-03 | 7 項直接落地，無動工期 |
| 64（Token 優化 v0.4）| 2026-05-01 | 四層防線 + 13 元件 |
| 63.4 | 2026-05-03 | C-B 豁免，代碼已落地 |
