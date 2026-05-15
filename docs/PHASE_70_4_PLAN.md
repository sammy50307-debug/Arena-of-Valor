# Phase P70.4 計畫書 — OpenAI Fallback（凍結版）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：✅ 已收官（2026-05-16）

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P70.4 |
| **Phase 名稱** | Gemini primary / OpenAI fallback |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準（預估 8-9 檔；LLM client / analyzer wiring / tests / docs） |
| **預估投入時數** | 3 h |
| **Token budget** | 70K tokens |
| **負責模型** | GPT-5.3-Codex（repo 動工）；OpenAI API surface 以官方文件查證 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 轉換條件 | 執行者 |
|---|---|---|---|---|
| `SentimentAnalyzer` 預設 LLM client | 直接使用 `GeminiClient()` | 使用 fallback wrapper：Gemini primary，OpenAI secondary | Gemini 429 / provider down 且 `OPENAI_API_KEY` 存在 | AI 實作，主公驗收 |
| `analyzer/llm_client.py` | 舊 OpenAI client，未接 cache / response_schema | 補齊與 `GeminiClient` 相容的 `chat` / `batch_chat` / `cache_manager` 介面 | 單測驗證 | AI 實作 |

---

## 1. 目標 (Objective)

在 Gemini 429 或 provider down 時，自動改用 OpenAI 產出同型 JSON 結果，避免每日報告直接被迫 showcase。若 OpenAI key 未設定或 OpenAI 也失敗，維持既有 P69 行為：拋回上層，讓 `showcase_forced` / `error_fallback` 明確標記。

## 2. 觸發背景 (Why Now)

P63 / P69 多次證明 Gemini 免費配額 429 會造成每日報告降級。P70.2 已補上健康巡檢，P75 已補齊 blindspot；下一個高 ROI 是降低單一 LLM 供應商風險。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 直接把 primary 換 OpenAI | `SentimentAnalyzer` 全改 OpenAI | Gemini 429 不再是主問題 | 改變成本/品質/快取行為太大 | 不採 |
| B. fallback wrapper | Gemini 優先，特定錯誤才切 OpenAI | 行為保守，最小化 blast radius | 需維護 provider 狀態與測試 | **採用** |
| C. 升級到 Responses API | 用最新 OpenAI Responses / Structured Outputs | 長期方向更現代 | repo 鎖 Python 3.8 + `openai<1.56`，升 SDK 會牽動環境 | 不採 |

**官方文件查證**：
- OpenAI Chat Completions API 仍支援 Python SDK 與 `response_format`；官方同時建議新專案可考慮 Responses API。
- OpenAI Structured Outputs 官方建議能用時優先於 JSON mode，且 `gpt-4o-mini` 支援 `json_schema` response format。

---

## 3. Entry Criteria

- [x] P75 / R-014 已本地 commit：`66392f4`
- [x] `requirements.txt` 已含 `openai>=1.12.0,<1.56.0`，本機版本 `1.55.3`
- [x] `.github/workflows/daily_report.yml` 已傳入 `OPENAI_API_KEY`
- [x] 已讀本地 `analyzer/gemini_client.py` / `analyzer/llm_client.py` / `analyzer/sentiment.py`
- [x] 已查官方 OpenAI Chat Completions / Structured Outputs docs
- [x] 不實打 OpenAI/Gemini API；驗收以 mock 單測為主，避免消耗 quota

## 4. Exit Criteria

- [x] `SentimentAnalyzer()` 預設使用 fallback wrapper，而不是直接 `GeminiClient()`
- [x] Gemini 429 時，若 OpenAI fallback 存在，`analyze_posts()` 回傳 production 結果，不進 showcase
- [x] OpenAI key 不存在時，Gemini 429 維持既有 `quota_error=True` / showcase_forced 路徑
- [x] `generate_daily_summary()` / dynamic focus 的單次 `chat()` 也能走 OpenAI fallback
- [x] OpenAI client 支援 `response_schema` 參數，至少把 Gemini uppercase schema 轉成 OpenAI lowercase JSON Schema
- [x] 新增 mock tests 覆蓋 fallback success / no-key re-raise / response_format schema / SentimentAnalyzer integration
- [x] 全套 `py -m pytest -q` 通過
- [x] `TASK_HISTORY.md` / handoff / WIP 同步收官，不 stage 既有 untracked 報告檔

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 3 h |
| 預估收益等級 | 高 |
| 收益描述 | Gemini 配額耗盡時可嘗試 OpenAI 續跑，減少假資料報告與 daily health failure |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增 wrapper，少改 `SentimentAnalyzer` | 介面不相容導致 runtime crash | 對齊 `chat` / `batch_chat` / `cache_manager` |
| **2. 邏輯層 (Logic)** | 只在 provider failure 時 fallback，不改正常 Gemini 路徑 | fallback 吞掉真 bug | 僅 fallback 可辨識 provider 錯誤；非 provider bug 保留 raise |
| **4. 測試層 (Testing)** | mock OpenAI/Gemini，不打真 API | 假測試沒有覆蓋 wiring | 加 SentimentAnalyzer integration test |
| **10. 安全層 (Security)** | 不輸出 API key，不 dump env | log 洩漏 secret | 只 log provider 名與錯誤類型，不 log request URL key |

### A 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | provider fallback wrapper 分離於 Gemini/OpenAI client | wrapper 變成雜訊層 | 僅負責 provider selection，不處理 prompt/schema 業務 |
| **5. 資料層 (Data)** | 共用 CacheManager，fallback 產物仍是 production 結果 | provider 產物混入同一 prompt cache | 只 cache 成功 JSON；provider metadata 暫不寫入 cache |
| **6. 可觀察性層 (Observability)** | wrapper 記錄 fallback 發生 | metadata 不顯示 provider | 本 Phase 先 log；若主公需要報告頂部 provider，再開 P70.4.1 |
| **7. 韌性層 (Resilience)** | Gemini 429 / provider down → OpenAI | OpenAI 也失敗 | re-raise，保留 P69 showcase_forced/error_fallback |
| **13. 可維護性層 (Maintainability)** | OpenAI client 補同介面而非改 prompt 層 | 兩 provider schema 差異 | schema converter 集中在 `llm_client.py` |
| **14. 文件層 (Documentation)** | 計畫書 + TASK_HISTORY + handoff | OpenAI docs 過期 | 記錄查證日期 2026-05-16 與官方連結 |
| **15. 流程層 (Process)** | 不混入 P70.6 cache LRU/TTL | scope creep | P70.6 保留下一段 |

### B 級層

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | LLM 呼叫 / batch | fallback concurrency 保守使用 1 | OpenAI 成本/延遲增加 | 只在 Gemini 失敗時啟動 |
| **11. 部署層 (DevOps)** | GHA 有 `OPENAI_API_KEY` secret | 不改 workflow secret 名稱 | secret 未設時 fallback 不啟動 | no-key path 單測驗證 |
| **12. 成本層 (Cost)** | OpenAI API 付費 | fallback-only，不做 preflight 打 API | 成本突然增加 | 不在本地/測試打真 API；可另加 cost cap |
| **16. 隱私/合規層 (Privacy)** | LLM provider 切換 | 送往 OpenAI 的內容與 Gemini 相同 | 資料出境/供應商政策需主公知情 | 只在既有 `OPENAI_API_KEY` 已設定時啟用；文件明示 |

### N/A 層

| 層 | N/A 理由 |
|---|---|
| **9. UX/A11y 層** | 不改 UI / template |
| **17. i18n/在地化層** | 不改多語輸出規則；prompt 既有繁中要求沿用 |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Architecture 層 → 已動 Documentation 層
- [x] 動 DevOps 層 → 已動 Security / Testing 層

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_70_4_PLAN.md` | 可逆 | ✅ 2026-05-16 |
| 新增 fallback wrapper / tests | 可逆 | ✅ 2026-05-16 |
| 修改 `SentimentAnalyzer` default client | 半可逆 | ✅ 2026-05-16 |
| `git push` | 半可逆 | 推前必問主公 |

### X2 盲區掃描

- [x] API key 不輸出
- [x] 不呼叫真 API
- [x] 不修改 reports / raw data
- [x] 不升級 SDK / Python

### X3 時間敏感性

- 本計畫凍結日期：2026-05-16
- 本計畫過期日期：2026-06-16
- OpenAI docs 查證日期：2026-05-16；若 OpenAI SDK / API guide 更新，需重查

### X4 多角度同行審查

- **主公視角**：主公要少看到假資料；fallback 成功時應保持 production，而非 showcase。
- **世界頂尖駭客 / 紅隊攻擊者視角**：最危險的是把 API key 打到 log；本 Phase 禁止輸出 secrets。
- **接手者視角**：接手者要能看到 provider selection 在 wrapper，不散落在 sentiment 業務邏輯。
- **X4-J 自動化建議性工具邊界**：mock tests 只能驗證 wiring 與 request shape，不證明真 OpenAI quota/帳號可用。
- **X4-K 使用者端審查官**：如果 OpenAI secret 沒設，使用者仍會看到 showcase_forced；這是明確降級，不是假裝已修。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | OpenAI SDK 1.55.3 不支援某些新 Responses API 功能 | 高 | 中 | API | 不採 Responses API，沿用 Chat Completions |
| R2 | Gemini schema uppercase 與 OpenAI JSON Schema lowercase 不相容 | 中 | 高 | Logic | 寫集中轉換器 + 單測 |
| R3 | fallback 吞掉非 provider bug | 中 | 高 | Logic | `_is_provider_failure()` 限定錯誤類型 |
| R4 | OpenAI secret 未設，主公以為 fallback 已可用 | 中 | 中 | DevOps | no-key path 明文維持 showcase，handoff 說明 |
| R5 | OpenAI fallback 成本不可見 | 中 | 中 | Cost | 本 Phase fallback-only；provider meta/cost cap 留後續候選 |

**高風險加權檢查（META4）**：
- 高風險數量：2
- 加權分數：10
- 是否 >= 5 須請示主公：是；主公已授權「把剩下的東西做一做」，且本 Phase 不打真 API / 不 push。

---

## 9. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1** | 補 OpenAI client 介面與 schema converter | R1/R2 | OpenAI request shape 單測 |
| **S2** | 新增 Gemini→OpenAI fallback wrapper | R3/R4 | fallback success / no-key tests |
| **S3** | `SentimentAnalyzer` default 改走 wrapper | wiring | integration test |
| **S4** | 全套測試 + 收官文件 | 流程漂移 | 119+ tests passed |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_70_4_PLAN.md`
- `analyzer/fallback_llm_client.py`
- `tests/test_openai_fallback.py`

**修改**：
- `analyzer/llm_client.py`
- `analyzer/sentiment.py`
- `config.py`
- `TASK_HISTORY.md`
- `NEXT_SESSION_HANDOFF.md`
- `memory/history_lookup/WIP_PHASES.md`

**刪除**：
- 無

**影響但未直接修改**：
- `.github/workflows/daily_report.yml`（已存在 `OPENAI_API_KEY` env，P70.4 不改）

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] OpenAI fallback mock 綠但實際 workflow 因 SDK/API request shape 掛掉
- [ ] fallback 吞掉非 provider bug，導致 production 結果錯誤
- [ ] OpenAI 產物污染 cache，造成後續 Gemini 命中不可信

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 主要攻擊面是 secret 洩漏與 prompt/data 外送；不 log key、不 dump env、不在測試打真 API。 |
| **X4-B 接手者** | 接手者應從 `fallback_llm_client.py` 看懂 provider 選擇，不必讀完整 sentiment 流程。 |
| **X4-C 災難情境** | Gemini 失敗、OpenAI 也失敗、wrapper 吞錯 → 報告假 production；緩解是失敗時 re-raise，保留 P69 降級語意。 |
| **X4-D 5 年後** | Provider 名稱會變，但 wrapper 模式仍可替換成任意 secondary provider。 |
| **X4-E 終端 vs IDE** | 測試以 PowerShell `py -m pytest` 執行，不依賴 bash-only 語法。 |
| **X4-F 跨平台 Win/Mac/Linux** | 不新增平台依賴；使用現有 `openai` / `httpx` 套件。 |
| **X4-G 主公個人視角** | 主公需要知道：若 secret 沒設，fallback 不會魔法啟動。 |
| **X4-H 觀測 / 治理** | 初版只 log provider fallback；報告 metadata provider/cost 可列後續候選。 |
| **X4-I 主公可見性** | 收官時必須清楚列出：P75/P70.4 是否已 commit、哪些 commit 尚未 push、push 前仍需主公明確確認。 |
| **X4-J 自動化建議性工具邊界** | Mock tests 不等於真 OpenAI 帳號健康；真 workflow_dispatch 需主公另行核准。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者只在報告品質上感知差異；fallback 成功不應變成 showcase 標示。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | P70.4 只處理 OpenAI fallback，不混入 P70.6 | 觸發；scope 固定 |
| **Ken 型紅隊 / 技術長** | 固定必看 | API key / provider failure / exception taxonomy | 觸發；不 log secret |
| **Patric 型使用者端審查官** | 固定必看 | fallback 成功時不能顯示假資料模式 | 觸發；production mode 保持 |
| **Jimmy 型文件主筆** | 改 docs / handoff | 文件需說清楚 no-key 行為 | 觸發 |
| **Marcus 型數據分析師** | 涉及判斷依據 | mock vs real API 證據要分清楚 | 觸發 |
| **Oliver 型設計審查** | UI | N/A；不改 UI |
| **Penny 型 CFO** | API 成本 | fallback-only，避免常態成本轉移 | 觸發 |
| **Jason 型執行 / DevOps** | GHA / secrets / tests | workflow 已傳 `OPENAI_API_KEY`，不改 secret 名 | 觸發 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | Responses API 才是官方推薦方向，為何還用 Chat Completions？ | A | N/A | repo 鎖 Python 3.8 / `openai<1.56`；本 Phase 不做 SDK migration | 採保守方案 |
| 2 | mock tests 綠不代表真 OpenAI 可用 | **S** | N/A | 收官明說真 API 未跑；workflow_dispatch 需主公核准 | 入限制 |
| 3 | fallback 可能掩蓋 Gemini client bug | **S** | N/A | 只 fallback provider failure；非 provider exception 不吞 | 入實作 |
| 4 | OpenAI 產物與 Gemini 產物有差異，cache 混用可能怪 | A | N/A | 只 cache schema 成功結果；provider-aware cache 留後續候選 | 登記限制 |
| 5 | OpenAI 成本可能失控 | A | N/A | fallback-only + concurrency=1；不做 preflight 打 API | 入實作 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

N/A。本 Phase 不新增或更新 skill。
