# Postmortem：每日 CI 報告持續 Showcase 模式根因

**日期**：2026-05-03
**Phase**：P63.4
**嚴重度**：中（功能降級，非系統崩潰）
**撰寫人**：Claude Sonnet 4.6 + 主公

---

## 事件摘要

每日 CI 排程連續多日產出 showcase 預演假資料而非真實 LLM 分析報告。
診斷發現三個獨立 Bug 共同作用，導致整條 production 路徑完全失效。

---

## 時間軸

| 時間 | 事件 |
|---|---|
| P63.3 收官後 | 每日 CI 報告開始固定輸出 showcase 資料 |
| 2026-05-03 | P63.4 診斷完成，鎖定 3 Bug |
| 2026-05-03 | S0 排查 → S1a/b/c/S2/S3 動工 → 5 commit 完成 |

---

## 根因分析

### Bug 1：GHA 環境 burst 觸發 429 全滅

**症狀**：`concurrency=3` 在 GHA 環境瞬間發出 3 個並行請求，全部 429 → 斷路器熔斷 → showcase。

**根因**：本機測試從未出現 429（配額充足 + 時間分散），開發者假設 concurrency=3 是安全值。

> **G2-3「我以為」**：「我以為本機沒問題，GHA 也沒問題」── 跨環境效能假設未驗證。

**修法**：
- 併發數 3→1（S1a）
- 429 後 wait 60s→120s 再重試，wait 預算耗盡才熔斷（S1b）
- 並且：`chat()` 的 while 迴圈讓 429 重試不消耗 MAX_RETRIES 計數（否則 5 次上限不夠跑完三輪模型 × 兩次 wait）

### Bug 2：git config 在 python main.py 之後才設定

**症狀**：`main.py` 內 `git commit` 拋出 `Author identity unknown` → `CalledProcessError` → push 從未執行。

**根因**：workflow 的 git config step 寫在 Execute AoV Pipeline 之後，視覺上看起來是「準備工作」卻放在最後。

**修法**：新增獨立 `🔧 Git Config` step，置於 `🚀 Execute AoV Pipeline` 之前（S2）。

### Bug 3：Fallback git add 漏 data/llm_cache.json + .gitignore 擋住

**症狀**：每日 cache 生成後未被 commit，下次跑全部 19 篇重打 LLM。

**根因**：
1. Fallback `git add data/reports/` 未包含 `data/llm_cache.json`
2. `.gitignore` 有 `data/*` 規則，即使手動 add 也會被擋

> **隱藏層**：S0 排查時沒注意到 .gitignore 的問題，是 S3 動工時才發現的額外 bug。

**修法**：
- Fallback `git add` 補納 `data/llm_cache.json`
- `.gitignore` 補 `!data/llm_cache.json` + `!data/.cache_policy.md` 例外（S3）

---

## 通則化（G6 失誤學）

| # | 通則 | 適用範圍 |
|---|---|---|
| 1 | **跨環境效能假設必須在目標環境驗證**：本機不 429 不代表 GHA 不 429 | 任何 API 呼叫型 CI |
| 2 | **斷路器熔斷條件必須有重試緩衝**：一觸即發的熔斷等於放棄，應先 wait 再熔斷 | 有速率限制的 LLM 呼叫 |
| 3 | **persistent state 必須與 commit 範圍對齊**：cache / artifact 若不入版控等於每次重來 | 任何跨 job 的中間產物 |
| 4 | **workflow step 順序要從「執行時序」角度審查**，不是「邏輯分組」角度 | 所有 CI/CD workflow |
| 5 | **.gitignore 的 `dir/*` 萬用規則要配 `!` 例外**，否則 force add 的檔案下次仍被忽略 | 有版控例外需求時 |

---

## 預防措施

- **C-B Exit Criteria**：每次類似修復必須在 GHA 真環境跑 `workflow_dispatch` 2 次驗證
- **報告頂部 metadata**：`<!-- mode: production | cache_hit: X/Y -->` 讓主公一眼判真假，無需打開 DevTools
- **G3 觀察期**：修復後 7 天每日 09:00 親檢，連 2 日任一失敗立刻 disable cron

---

## 後續待辦

- [ ] `workflow_dispatch` 手動觸發 2 次（C-B）
- [ ] 第一次正規排程後確認 commit 訊息無 `(Fallback)`（C-C）
- [ ] 主公親點一次驗收（C-D）
- [ ] 5 commit hash + 3 GHA run URL 記入 TASK_HISTORY（C-E，push 後補）
