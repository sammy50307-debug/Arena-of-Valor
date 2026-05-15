# Phase P70.6 計畫書 — llm_cache LRU / TTL 機制（凍結版）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：✅ 已收官（2026-05-16）

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P70.6 |
| **Phase 名稱** | `llm_cache.json` LRU / TTL retention |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準（預估 7 檔；cache manager / config / tests / docs） |
| **預估投入時數** | 2 h |
| **Token budget** | 45K tokens |
| **負責模型** | GPT-5.3-Codex（repo 動工） |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 轉換條件 | 執行者 |
|---|---|---|---|---|
| `data/llm_cache.json` schema | v2：`stored_at` + `ttl_days` | v3：補 `last_accessed`，支援 LRU | `CacheManager` 載入 v2 檔時自動 migration | 程式自動 |

---

## 1. 目標 (Objective)

補上 `llm_cache.json` 的 retention 上限：保留既有 TTL 清理，再新增 max entries + LRU eviction，避免 prompt / hero / daily_summary cache 長期無界增長。

## 2. 觸發背景 (Why Now)

P64 cache 架構已讓 daily pipeline 降低 LLM 呼叫，但 P75 / B-016 重新提醒 cache key、TTL、no-write policy 必須明列。P70.4 又讓 OpenAI fallback 也共用 CacheManager，因此現在補上 LRU / size cap 的 ROI 最高。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 只靠現有 TTL | 不改 code | 零風險 | 熱 cache 若 TTL 長仍無 max size；B-016 未解 | 不採 |
| B. JSON schema v3 + max entries LRU | 加 `last_accessed`、`CACHE_MAX_ENTRIES` | 小改、可測、保留 JSON 格式 | v2 migration 要寫對 | **採用** |
| C. 改 SQLite | 原生 query / retention | 長期漂亮 | 對目前 40KB cache 過度重構 | 不採 |

---

## 3. Entry Criteria

- [x] P70.4 已本地 commit：`089119f`
- [x] 現有 `CacheManager` 已有 TTL eviction，但無 max entries / LRU
- [x] `data/llm_cache.json` 目前 schema_version=2，約 40KB，屬可無痛 migration 規模
- [x] 不直接編輯 `data/llm_cache.json`；只改程式，讓 runtime 自動 migration
- [x] 不處理 P72 metrics JSONL retention（那是 R-012，非 `llm_cache`）

## 4. Exit Criteria

- [x] `config.py` 新增 `CACHE_MAX_ENTRIES`
- [x] `CacheManager` schema 升 v3，v2 load 自動補 `last_accessed`
- [x] `get()` 命中時更新 in-memory `last_accessed`
- [x] `set()` / `save()` / `_load()` 會執行 max entries LRU eviction
- [x] 新增測試覆蓋 v2 migration、LRU eviction、get 更新 last_accessed
- [x] `py -m pytest tests/test_cache_manager.py -q` 通過
- [x] 全套 `py -m pytest -q` 通過
- [x] TASK_HISTORY / handoff / WIP 同步，不 stage `data/llm_cache.json` 或既有 reports

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 2 h |
| 預估收益等級 | 中 |
| 收益描述 | 防止 cache 長期無界增長，讓 Gemini/OpenAI 共用 cache 更可控 |
| ROI 結論 | ✅ 值得做，但不升 SQLite |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 小改 `CacheManager`，不改 LLM 呼叫 | eviction 邏輯誤刪新資料 | LRU 單測驗證 |
| **2. 邏輯層 (Logic)** | TTL 先清，再 LRU cap | timestamp 缺失排序錯 | 缺 `last_accessed` 時 fallback `stored_at` |
| **4. 測試層 (Testing)** | 擴充 `tests/test_cache_manager.py` | 只測 v3 不測 v2 migration | 必加 v2 fixture |
| **10. 安全層 (Security)** | 不讀 secrets、不輸出 cache 內容 | cache 可能含 LLM 結果 | 測試用 tmp cache，不 dump 真 cache |

### A 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 保留 JSON CacheManager，不引 SQLite | JSON 寫入仍整檔 | cache 目前小，max entries 降低長期風險 |
| **5. 資料層 (Data)** | schema v3 migration | 舊 v2 entry 無 `last_accessed` | migration 補 `last_accessed=stored_at` |
| **6. 可觀察性層 (Observability)** | log eviction count | eviction 不可見 | logger.info 記錄 TTL/LRU 清除數 |
| **7. 韌性層 (Resilience)** | 壞 schema 仍重建空 cache | migration 失敗 | 既有 load exception fallback 保留 |
| **13. 可維護性層 (Maintainability)** | retention 邏輯集中在 CacheManager | 多處手動清 cache | key factory / retention 同檔 |
| **14. 文件層 (Documentation)** | 計畫書 + TASK_HISTORY | schema v3 未記 | history 記物理真相 |
| **15. 流程層 (Process)** | 不混入 R-012 metrics JSONL | scope creep | 明列 N/A |

### B 級層

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | cache entries 可能增長 | max entries LRU | 每次 set/save sort entries | 預設 500 筆，成本可接受 |
| **12. 成本層 (Cost)** | cache eviction 影響 LLM call | LRU 保留最近使用 | 過小 max_entries 會增加 API cost | 預設 500，不激進 |
| **11. 部署層 (DevOps)** | GHA 會載入 cache | 不改 workflow | 首次 v3 migration 只在 save 時落盤 | 單測驗證 |

### N/A 層

| 層 | N/A 理由 |
|---|---|
| **9. UX/A11y 層** | 不改 UI |
| **16. 隱私/合規層** | 不新增資料外送，只管理本地 cache |
| **17. i18n/在地化層** | 不改文本輸出 |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Data 層 → 已動 Documentation / Maintainability 層
- [x] 動 Performance / Cost 層 → 已動 Testing 層

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 修改 `CacheManager` retention | 可逆 | ✅ 2026-05-16 |
| schema v3 runtime migration | 半可逆 | ✅ 2026-05-16（不直接改真 cache 檔） |
| `git push` | 半可逆 | 推前必問主公 |

### X2 盲區掃描

- [x] 不 stage `data/llm_cache.json`
- [x] 不 stage reports
- [x] 不處理 metrics JSONL R-012
- [x] 不做 SQLite migration

### X3 時間敏感性

- 本計畫凍結日期：2026-05-16
- 本計畫過期日期：2026-06-16
- 預設 `CACHE_MAX_ENTRIES=500` 可在 90 天後依 cache 實際大小回顧

### X4 多角度同行審查

- **主公視角**：主公要的是 cache 不默默長大，不想被 SQLite 大工程拖住。
- **世界頂尖駭客 / 紅隊攻擊者視角**：不輸出真 cache 內容，不把 LLM 回傳 dump 到 log。
- **接手者視角**：v2/v3 migration 要一眼看懂，不能藏在 set/get 旁支。
- **X4-J 自動化建議性工具邊界**：單測能驗 LRU 邏輯，不證明 production cache 永遠最優大小。
- **X4-K 使用者端審查官**：若 max_entries 太小，使用者可能看到 API cost 回升；預設要保守。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | v2 cache migration 漏補欄位 | 中 | 中 | Data | v2 fixture test |
| R2 | LRU 以 stored_at 排序而非 last_accessed，誤刪熱資料 | 中 | 中 | Logic | get 更新 last_accessed + test |
| R3 | max_entries 太小增加 API cost | 低 | 中 | Cost | 預設 500，env 可調 |
| R4 | save 時清除 entries 但沒 log | 中 | 低 | Observability | log LRU 清除數 |

**高風險加權檢查（META4）**：
- 高風險數量：0
- 加權分數：0
- 是否 >= 5 須請示主公：否；主公已授權本輪剩餘工作

---

## 9. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1** | config + CacheManager v3 / LRU | R1/R2/R4 | cache tests |
| **S2** | 擴充 tests | R1/R2/R3 | `tests/test_cache_manager.py` |
| **S3** | 全套 pytest + 收官文件 | 流程漂移 | 124+ passed |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_70_6_PLAN.md`

**修改**：
- `analyzer/cache_manager.py`
- `config.py`
- `tests/test_cache_manager.py`
- `TASK_HISTORY.md`
- `NEXT_SESSION_HANDOFF.md`
- `memory/history_lookup/WIP_PHASES.md`

**刪除**：
- 無

**明確不納入**：
- `data/llm_cache.json`
- `data/reports/*.html`
- `~/.claude/skill_metrics.jsonl`（R-012）

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] v2 production cache migration 後資料遺失
- [ ] LRU eviction 導致 API cost 明顯回升
- [ ] `data/llm_cache.json` 被誤 stage

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 不 dump cache 內容、不輸出 prompt/result；只測 tmp cache。 |
| **X4-B 接手者** | 接手者要看得懂 schema v2→v3 與 `last_accessed` 的目的。 |
| **X4-C 災難情境** | 真 cache 被 migration 寫壞；緩解是不直接改真檔，runtime save 才落盤。 |
| **X4-D 5 年後** | 若 JSON cache 不夠用，v3 仍可作為遷 SQLite 的來源 schema。 |
| **X4-E 終端 vs IDE** | 測試以 PowerShell `py -m pytest` 執行。 |
| **X4-F 跨平台 Win/Mac/Linux** | 只用 pathlib/json/datetime，跨平台。 |
| **X4-G 主公個人視角** | 主公要知道 P70.6 不處理 metrics JSONL R-012，那是另一個風險。 |
| **X4-H 觀測 / 治理** | log eviction count，但不新增 dashboard。 |
| **X4-I 主公可見性** | 收官明列未 stage `data/llm_cache.json` 與既有報告檔。 |
| **X4-J 自動化建議性工具邊界** | 單測只驗 retention 邏輯；實際 max_entries 是否足夠需觀察 90 天。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 過度 aggressive eviction 會讓使用者看到更多 fallback/API delay；預設保守。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | P70.6 只處理 `llm_cache` | 觸發 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 不輸出 cache 內容，不誤 stage data | 觸發 |
| **Patric 型使用者端審查官** | 固定必看 | eviction 不可太 aggressive | 觸發 |
| **Jimmy 型文件主筆** | 改 docs/history | schema v3 要記清楚 | 觸發 |
| **Marcus 型數據分析師** | 涉及 cache size | 預設 500 是保守假設 | 觸發 |
| **Oliver 型設計審查** | UI | N/A |
| **Penny 型 CFO** | API 成本 | cache 過度清會增加成本 | 觸發 |
| **Jason 型執行 / DevOps** | GHA / data | 不改 workflow；不 stage cache data | 觸發 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 為什麼不直接改 SQLite？ | A | N/A | 目前 cache 40KB，SQLite 屬過度重構 | 不採 |
| 2 | v3 migration 可能寫壞真 cache | **S** | N/A | 不直接 stage/寫真 cache；只改程式與 tmp tests | 入限制 |
| 3 | LRU 可能刪掉最近常用但 stored_at 舊的熱資料 | **S** | N/A | 新增 `last_accessed`，get 命中更新 | 入實作 |
| 4 | max_entries 可能讓 API cost 回升 | A | N/A | 預設 500，env 可調 | 入 config |
| 5 | R-012 metrics JSONL 仍沒解 | A | N/A | 這是另一個風險，不混入 P70.6 | 明列不處理 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

N/A。本 Phase 不新增或更新 skill。
