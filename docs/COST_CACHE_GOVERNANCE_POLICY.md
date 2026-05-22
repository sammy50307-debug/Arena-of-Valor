# Cost / Cache Hit Governance Policy（P84.5 / P94）

> 狀態：ACTIVE（2026-05-23）
> 原則：本政策只提供 pipeline 成本代理訊號，不代表 OpenAI / Gemini / Tavily / Apify 供應商帳單。

## 1. 指標來源

| Source | 位置 | 可讀指標 |
|---|---|---|
| Run manifest | `data/runs/<date>/run_manifest.json` -> `metrics` | `cache_hit` / `l1_hits` / `l2_hits` / `apify_hits` / `llm_calls` / `total_calls` |
| Run manifest selection | `data/runs/<date>/run_manifest.json` -> `selection` | `total_input_posts` / `llm_selected_posts` / `local_only_posts` / `duplicate_posts` / `max_llm_items` |
| Run manifest enrichment | `data/runs/<date>/run_manifest.json` -> `enrichment` | `queue_available` / `eligible_posts` / `skipped_posts` / `enriched_posts` / `replay_status` |
| Run manifest provider routing | `data/runs/<date>/run_manifest.json` -> `provider.routing` | `route_status` / `router_enabled` / `experimental_free_providers_enabled` / `slots[*].enabled` |
| Report metadata | `data/reports/aov_report_<date>.html` 首行註解 | `cache_hit` / `total_calls` / `llm_calls` / `mode` |
| Cache store stats | `data/llm_cache.json` -> `stats` | `total_l1_hits` / `total_l2_hits` / `total_apify_hits` / `total_misses` / entry count |

## 2. 機械檢查項

| Check | 規則 | Issue |
|---|---|---|
| Metrics source | window 內至少要能從 manifest 或 report metadata 讀到一筆日級指標 | `CCG001` |
| Metrics invariant | `cache_hit <= total_calls` 且 `llm_calls <= total_calls`，所有指標必須是非負整數 | `CCG002` |
| Cache hit advisory | aggregate cache hit rate 低於門檻時輸出 advisory，不阻擋 daily | `CCG003` |
| Cache store stats | `data/llm_cache.json` 只能讀 schema / entry count / stats，不輸出 entry content | `CCG004` |
| LLM call budget | 最新日超過門檻時輸出 current degraded；若總量只因舊日 spike 超標，輸出 historical advisory | `CCG005` |
| Budget cooldown | window 內 manifest `budget` 顯示 skip / cooldown / budget exhausted / malformed state 時輸出 advisory | `CCG006` |
| Selection throttle | window 內 manifest `selection` 顯示 local-only / duplicate 節流，或 selected 超過 cap | `CCG007` |
| Enrichment replay | window 內 manifest `enrichment` 顯示 pending / no-op / budget skip / partial / failed replay 狀態 | `CCG008` |
| Provider routing | window 內 manifest `provider.routing` 顯示 provider router 或候選 slot 被啟用 | `CCG009` |

## 3. 指令

```powershell
py scripts\cost_cache_governance.py --repo-root . --date 2026-05-18 --window-days 3
py scripts\cost_cache_governance.py --repo-root . --date 2026-05-18 --window-days 3 --json
```

## 4. P94 Classification Taxonomy

| Classification | 意義 | 典型來源 | 操作解讀 |
|---|---|---|---|
| `current` | 最新日或目前 window 仍有需要處置的風險 | `CCG005` 最新日超標、`CCG007` selected over cap、`CCG008 failed/pending`、`CCG009` provider enabled | 依 runbook 處理；若 severity 是 degraded/blocking，不能拿來支撐 closeout |
| `historical` | window aggregate 被舊日 pre-remediation spike 拉高，但最新日未超過同一門檻 | P94 的 2026-05-21 pre-P91 `llm_calls=28` 對 2026-05-23 三日窗造成 `total_llm_calls=35` | 保留成本脈絡，但不讓最新健康 run 因舊尖峰 exit 1 |
| `residual` | post-remediation 預期殘留，不代表 production failure | P91 duplicate/local-only 節流、P92 `no_eligible` replay no-op | 觀察品質與趨勢，不直接補 provider 或重送 LLM |

## 5. 邊界

- `total_llm_calls` 是 pipeline proxy，不是供應商帳單。
- `budget.llm_calls_used` 與 `budget.decision` 也是 pipeline proxy，不是供應商帳單。
- `selection.llm_selected_posts` 只代表送入 LLM 深讀的真實來源數；`local_only_posts` 仍會走本地 deterministic baseline，不代表資料被丟棄。
- `enrichment.eligible_posts` 只代表 P92 replay 候選；`no_eligible` 常見於 duplicate-only local-only，不代表報告失敗。
- `data/enrichment_queue/` 可含 raw post content，必須保持 git-ignored 或短 retention artifact；manifest `enrichment` 才是 repo-safe 訊號。
- `provider.routing` 是 raw-free 工程路由狀態；預設應為 disabled / legacy default，不代表供應商帳單真相。
- cache hit rate 低是 advisory；它可能只是冷啟動或資料源變動，不一定是 bug。
- checker 不讀、不輸出 cache entry 的 LLM 結果內容。
- 若要判斷真實花費，必須另查供應商帳單或 API usage dashboard。
