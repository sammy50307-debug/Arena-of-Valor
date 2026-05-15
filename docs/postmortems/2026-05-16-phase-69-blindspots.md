# P69 Blindspots — M4 追溯

> **M4 協議**：每個 Phase 收官後寫此檔，記錄「計畫書沒寫但實際撞到的問題」>= 3 條，
> 通則化後加入 PHASE_TEMPLATE 體檢清單並升版。

- **Phase**：P69
- **日期**：2026-05-16
- **對應 Postmortem**：[2026-05-08-p69-showcase-forced-rootcause.md](./2026-05-08-p69-showcase-forced-rootcause.md)

---

## 計畫書沒寫、實際撞到的問題

### B-017：fallback 狀態必須攜帶原因，而不是只標「已 fallback」

**計畫書原寫**：系統已有 showcase / fallback 概念，目標是 API 壞掉時仍能產出報告，不讓主公看到白頁。

**實際撞到**：主動展演（`--showcase`）與被迫展演（Gemini 429 配額耗盡）都顯示 `mode: showcase`，主公無法判斷今天是真實 API 壞掉、有人測試、還是系統主動切到假資料。P69 因此改成 `production / showcase / showcase_forced / error_fallback` 四態。

**通則化**：
> 任何 fallback / degradation 路徑都必須輸出 machine-readable reason 與 user-visible mode；「已 fallback」不是足夠狀態，必須說明為什麼 fallback、誰觸發、是否可恢復。

**待加入**：PHASE_TEMPLATE 的可觀察性層 / UX 層：降級狀態需包含 reason taxonomy 與使用者可見標示。

---

### B-018：配額耗盡後，下游流程不得繼續呼叫同一供應商

**計畫書原寫**：showcase=True 時預期走假資料或本地 fallback，避免再消耗外部 API。

**實際撞到**：`generate_daily_summary` 在 showcase=True 時雖跳過 L2 cache 讀取，卻仍呼叫 `self.llm.chat`，導致配額耗盡後又浪費 1-2 次 LLM 呼叫，甚至引發雪崩式降級。

**通則化**：
> 一旦上游已確認 quota_error / circuit_open / provider_down，同一 request chain 的下游模組必須 short-circuit 到本地 fallback；不得再呼叫同一失效供應商，除非有明確 cooldown 或替代 provider。

**待加入**：PHASE_TEMPLATE 的韌性層 / 成本層；P70.4 OpenAI fallback 必須把 provider failover 與 short-circuit 寫成狀態機。

---

### B-019：catch-all exception 不能寫死成特定業務模式

**計畫書原寫**：外層 `except Exception` 以保護排程不崩潰為主，任何錯誤都能產出可讀 fallback 報告。

**實際撞到**：`main.py` 外層 except 的 `_meta["mode"]` 寫死為 `"showcase"`，即使不是配額問題、也不是主動展演，仍會顯示旗艦展演。這讓 metadata 語意失真，排查時把一般 Exception 誤導成 showcase 問題。

**通則化**：
> catch-all fallback 只能標示「未知錯誤 / error_fallback」，不能宣稱特定業務原因；若要輸出業務模式，必須由已分類的 exception 或顯式 flag 決定。

**待加入**：PHASE_TEMPLATE 的邏輯層 / 可觀察性層：錯誤 taxonomy 與 metadata mapping 要列為設計項。

---

## 體檢清單升版摘要

| 版本 | 升版內容 | 驅動 Phase |
|---|---|---|
| v1.3（待議）| + fallback reason taxonomy / provider short-circuit / catch-all metadata 邊界 | **P69 / P75 回填** |

---

## 給下一個 Phase 的提醒

1. **B-017**：fallback 要能回答「為什麼、誰觸發、是否可恢復」。
2. **B-018**：provider 429 後，同一鏈路不要再打同一 provider。
3. **B-019**：catch-all 只能說未知錯誤，不能假裝知道業務原因。
