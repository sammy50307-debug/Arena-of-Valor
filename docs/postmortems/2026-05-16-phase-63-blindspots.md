# P63 Blindspots — M4 追溯

> **M4 協議**：每個 Phase 收官後寫此檔，記錄「計畫書沒寫但實際撞到的問題」>= 3 條，
> 通則化後加入 PHASE_TEMPLATE 體檢清單並升版。

- **Phase**：P63 / P63.4
- **日期**：2026-05-16
- **對應 Postmortem**：[2026-05-03-phase-63-4-showcase-rootcause.md](./2026-05-03-phase-63-4-showcase-rootcause.md)

---

## 計畫書沒寫、實際撞到的問題

### B-011：本機 API 成功不等於 GHA 目標環境安全

**計畫書原寫**：P63.4 前的 production 路徑以本機測試與既有 retry / circuit breaker 為主要安全感來源，沒有把 GitHub Actions 瞬時並發與供應商 rate limit 當成獨立驗收條件。

**實際撞到**：`concurrency=3` 在 GHA 環境瞬間送出 3 個 LLM 請求，全部觸發 HTTP 429，斷路器熔斷後每日報告持續降級為 showcase。Postmortem 明列 G2-3「我以為本機沒問題，GHA 也沒問題」。

**通則化**：
> 任何在 CI 內呼叫外部 API 的 Phase，Exit Criteria 必須包含「目標 CI 環境實跑」或「明確降載設計」；本機成功只能證明程式可跑，不能證明排程環境不會撞 rate limit。

**待加入**：PHASE_TEMPLATE 的 DevOps / 韌性層 Exit Criteria：API 型 workflow 要列 target-environment smoke test 或 concurrency budget。

---

### B-012：workflow step 順序不能只按語意分組審查

**計畫書原寫**：P63.4 前的 workflow 修補把 GitHub Actions 步驟視為「準備 / 執行 / 收尾」的語意群組，未要求逐步確認 runtime 前置條件是否真的排在使用點之前。

**實際撞到**：`git config` 寫在 `python main.py` 之後，導致 `main.py` 內部 `git commit` 拋出 `Author identity unknown`，後續 push 從未執行。視覺上像準備工作，但實際執行時序已經太晚。

**通則化**：
> 任何修改 CI/CD workflow 的 Phase，計畫書必須列「前置條件 -> 使用點」時序表；每個會被 runtime command 使用的設定，必須在該 command 之前完成。

**待加入**：PHASE_TEMPLATE 的部署層 / 流程層：workflow diff 審查必含 prerequisite ordering table。

---

### B-013：persistent state 必須同時檢查 commit 範圍與 ignore 規則

**計畫書原寫**：cache 被視為可持久化的改善，但計畫沒有把「誰負責把 cache 帶到下一次 job」拆成 `git add` 範圍、`.gitignore` 例外、fallback push 三個獨立檢查點。

**實際撞到**：Fallback `git add data/reports/` 沒包含 `data/llm_cache.json`，而 `.gitignore` 又有 `data/*` 規則擋住 cache。每日 cache 生成後未被 commit，下一次排程仍然 100% 重打 LLM。

**通則化**：
> 任何跨 job / 跨日保存的 state（cache、artifact、index、metadata）都必須在同一 Phase 明列：產生位置、持久化載體、commit / upload 範圍、ignore 例外、失敗時 fallback 是否也保存。

**待加入**：PHASE_TEMPLATE 的資料層 / DevOps 層；也作為 P70.6 `llm_cache` LRU / TTL 計畫的 entry criterion。

---

## 體檢清單升版摘要

| 版本 | 升版內容 | 驅動 Phase |
|---|---|---|
| v1.3（待議）| + CI API target-environment smoke test / workflow prerequisite ordering / persistent state commit-scope 檢查 | **P63 / P75 回填** |

---

## 給下一個 Phase 的提醒

1. **B-011**：API 型 CI 不要只信本機；GHA 實跑或降載預算要寫進 Exit Criteria。
2. **B-012**：workflow 審查看的是執行時序，不是 YAML 區塊看起來像哪一類。
3. **B-013**：cache 不是「寫到檔案」就持久化，還要確認 commit / artifact / ignore 規則。
