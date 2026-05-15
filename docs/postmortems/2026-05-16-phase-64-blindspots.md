# P64 Blindspots — M4 追溯

> **M4 協議**：每個 Phase 收官後寫此檔，記錄「計畫書沒寫但實際撞到的問題」>= 3 條，
> 通則化後加入 PHASE_TEMPLATE 體檢清單並升版。

- **Phase**：P64 / P64.1
- **日期**：2026-05-16
- **對應 Postmortem**：
  - [2026-05-01-phase-64-success-design.md](./2026-05-01-phase-64-success-design.md)
  - [2026-05-01-phase-64-token-optimization-success.md](./2026-05-01-phase-64-token-optimization-success.md)
  - [2026-05-03-phase-64-cache-hierarchy.md](./2026-05-03-phase-64-cache-hierarchy.md)

---

## 計畫書沒寫、實際撞到的問題

### B-014：重要規則不能只靠文字記得，必須機械化觸發

**計畫書原寫**：P64 的核心目標是避免新視窗全讀 `TASK_HISTORY.md`，以規則、記憶檔、hook 與警語組成四層防線。

**實際撞到**：Postmortem 將成功原因歸納為「縱深防禦」與「機械化觸發」。這代表原始問題不是單純 token 成本，而是人類和 AI 都會忘記規則；若只把禁令寫在文件中，仍會被新視窗、不同模型或疲勞狀態繞過。

**通則化**：
> 凡是「不能依賴人記住」的規則，計畫書必須至少提供一個機械化觸發點（hook、lint、CLI guard、CI check）與一個人工可見提醒點；文字規則本身不算完成。

**已加入**：AGENTS.md / 專案守則已要求新視窗讀 handoff 與禁止全讀 TASK_HISTORY；後續可補入 PHASE_TEMPLATE 的流程層作為通用 exit criterion。

---

### B-015：規則防線也會腐爛，退化監控與 ADR 不能事後才補

**計畫書原寫**：P64 計畫了四層防線與 token 節省目標，但沒有把「90 天後還是否有效」與「為何選這個架構」作為同 Phase 交付物。

**實際撞到**：Phase 64.1 事後補了 `scripts/rule-decay-check.sh`、hook 測試與 ADR。成功設計復盤明確指出：缺 G5-1 規則退化警示、缺 hook 測試覆蓋、缺 ADR 是 Phase 64 的可改善點。

**通則化**：
> 任何會成為長期治理規則的 Phase，必須在同一 Phase 補齊三件事：退化檢查週期、最小回歸測試、架構決策記錄；不能只交付當下有效的防線。

**待加入**：PHASE_TEMPLATE 的 G5 / Documentation / Testing 互鎖：長期規則 = decay check + tests + ADR。

---

### B-016：cache key 與 no-write policy 必須在計畫書明列

**計畫書原寫**：P64 cache 重構前，cache 被視為「降低重打 LLM」的效能措施，但沒有明列舊 key 為 `MD5(system_prompt + user_prompt)`、`user_prompt` 含每日貼文內容，也沒有列出 showcase / error 何時禁止寫入。

**實際撞到**：每日貼文內容不同導致舊 cache key 每天 100% miss，Gemini free tier 三備援模型全部 429，報告降級為 showcase。Postmortem 另列「showcase 結果不能寫 L1」作為學到的通則，避免壞資料污染快取。

**通則化**：
> 任何 cache Phase 必須在計畫書明列 key dimensions、預期命中率、invalidation / TTL、no-write cases、持久化位置；少任一項就不能把 cache 視為可靠韌性措施。

**待加入**：PHASE_TEMPLATE 的效能層 / 資料層；P70.6 `llm_cache` LRU / TTL 必須直接採用此條。

---

## 體檢清單升版摘要

| 版本 | 升版內容 | 驅動 Phase |
|---|---|---|
| v1.3（待議）| + 長期規則 decay/test/ADR 三件套 + cache key/no-write policy 必填 | **P64 / P75 回填** |

---

## 給下一個 Phase 的提醒

1. **B-014**：重要規則要有機械化入口，否則只是提醒，不是防線。
2. **B-015**：治理規則落地時，同步寫 decay check、測試、ADR。
3. **B-016**：cache 計畫若沒寫 key dimensions 與 no-write cases，等於沒有設計完成。
