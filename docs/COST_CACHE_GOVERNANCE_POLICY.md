# Cost / Cache Hit Governance Policy（P84.5）

> 狀態：ACTIVE（2026-05-18）
> 原則：本政策只提供 pipeline 成本代理訊號，不代表 OpenAI / Gemini / Tavily / Apify 供應商帳單。

## 1. 指標來源

| Source | 位置 | 可讀指標 |
|---|---|---|
| Run manifest | `data/runs/<date>/run_manifest.json` -> `metrics` | `cache_hit` / `l1_hits` / `l2_hits` / `apify_hits` / `llm_calls` / `total_calls` |
| Report metadata | `data/reports/aov_report_<date>.html` 首行註解 | `cache_hit` / `total_calls` / `llm_calls` / `mode` |
| Cache store stats | `data/llm_cache.json` -> `stats` | `total_l1_hits` / `total_l2_hits` / `total_apify_hits` / `total_misses` / entry count |

## 2. 機械檢查項

| Check | 規則 | Issue |
|---|---|---|
| Metrics source | window 內至少要能從 manifest 或 report metadata 讀到一筆日級指標 | `CCG001` |
| Metrics invariant | `cache_hit <= total_calls` 且 `llm_calls <= total_calls`，所有指標必須是非負整數 | `CCG002` |
| Cache hit advisory | aggregate cache hit rate 低於門檻時輸出 advisory，不阻擋 daily | `CCG003` |
| Cache store stats | `data/llm_cache.json` 只能讀 schema / entry count / stats，不輸出 entry content | `CCG004` |
| LLM call budget | window 內 LLM call proxy 超過門檻時輸出 degraded | `CCG005` |

## 3. 指令

```powershell
py scripts\cost_cache_governance.py --repo-root . --date 2026-05-18 --window-days 3
py scripts\cost_cache_governance.py --repo-root . --date 2026-05-18 --window-days 3 --json
```

## 4. 邊界

- `total_llm_calls` 是 pipeline proxy，不是供應商帳單。
- cache hit rate 低是 advisory；它可能只是冷啟動或資料源變動，不一定是 bug。
- checker 不讀、不輸出 cache entry 的 LLM 結果內容。
- 若要判斷真實花費，必須另查供應商帳單或 API usage dashboard。
