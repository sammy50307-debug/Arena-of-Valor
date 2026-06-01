# 📋 P105 計畫書 — Provider Abstraction Runtime 啟用 + OpenRouter 首發可切換（飛輪 v2 +ABCDE）

> **狀態**：🧊 FROZEN（2026-06-01 主公核准凍結｜M1/M2 lint PASS）｜**作者**：Opus 4.8（設計腦）｜**執行**：Sonnet（執行手）｜**日期**：2026-06-01

---

## 0. Phase 元資料

| 欄位 | 值 |
|---|---|
| Phase ID | P105 |
| 名稱 | Provider Abstraction Runtime 啟用 + OpenRouter 首發可切換 |
| 影響半徑 | ~10-13 檔（**重大** → 全 17 層）|
| 風險等級 | 中高（動 daily 主鏈路 + P93 治理契約）|
| 可逆性 | 半可逆（`PRIMARY_PROVIDER` 切回 gemini + git 回退）|
| 預估時長 | 2-3 session（S1-S5） |
| 前置 Phase | P104（治理引擎收官）、P93（provider 框架 fail-closed） |

## 0.5 狀態轉換清單（B-002）
- [x] DRAFT → 計畫書撰寫中
- [x] FROZEN → M1/M2 體檢通過、主公核准凍結（2026-06-01）
- [ ] RUNTIME → 開始實作（**動工時主公切 Sonnet**）
- [ ] CLOSED → 收官驗證 + TASK_HISTORY 追加

## 1. 目標 (Objective)
把 P93 的 fail-closed provider 框架**正式 runtime 啟用**，接入 OpenRouter 並設為首發；**核心設計目標：首發 provider＋model 可一行配置切換**（日後換任何 LLM 當首發只改 config 一行）。並提供「provider 對比 CLI」服務「測篩選到完美」與「燒額度」雙目標。

## 2. 觸發背景 (Why Now)
主公老師提供 OpenRouter 100 美金額度（6/5 對賭用光再加碼）；趁機把分析鏈接 OpenRouter 大量真實測試、把文章篩選調到「每次都是想看的」，同時把 provider 層重構成可切換架構（不寫死，日後好換）。費用約束**反轉**：OpenRouter 要用光（非省）。

## 3. Entry Criteria（入口條件，STR4）
- P104 收官且 pushed ✅
- provider 鏈現狀盤查完成（4 子代理 + 親自交叉驗證 3 行）✅
- `base.py` LLMProviderClient Protocol 介面確認 ✅
- OpenRouter API key 已備於 `.env`（待主公填，**不進版控**）

## 4. Exit Criteria（退出條件，STR3）
1. `PRIMARY_PROVIDER`/`PRIMARY_MODEL` 一行切換 work（gemini/openai/openrouter 互換首發，測試證實）
2. OpenRouter client 真實呼叫驗證通過（deepseek-chat/r1/minimax 的 schema 相容性測試有結論）
3. `provider_compare` CLI 可同批雙跑並排比較
4. daily 主鏈路切 OpenRouter 真實跑不壞、manifest 記錄 provider+model
5. 全套測試綠 **≥348+**（P104 後基線 348）+ 新測試
6. R-016 更新為「P105 核准啟用」、P93 DRAFT→FROZEN→TASK_HISTORY 收官

## 5. ROI 評估（G4-2）
- **成本**：OpenRouter＝老師額度（**反向 ROI：要用光**）；Gemini/OpenAI 維持不增費（R-016 行 275）。
- **效益**：① 可切換架構（一次性，長期省切換成本）② 篩選品質可量化比較（對比 CLI）③ 燒額度達成 6/5 對賭。
- **裁決點預估（B-005）**：~3 點 ×5 分鐘（① schema 不相容 model 取捨 ② 切首發時機 ③ R-016 治理更新）；AI 提供格式＝對比 CLI 並排表 + 測試結果。

## 6. 17 層稽核表（META2 強制填表）

### S 級（必填）
| 層 | 本 Phase 處置 |
|---|---|
| 代碼 | provider registry/factory 乾淨；OpenRouter client 仿 `llm_client.py` 複用 `_to_openai_json_schema` |
| 邏輯 | 多級 fallback 順序正確；首發 provider+model 動態組裝；解 fail-closed 只放行有 concrete client 的 provider |
| 測試 | 先寫測試：切換矩陣鎖 + 各 model 輸出契約（真實呼叫）+ fail-closed 契約改寫 + budget guard |
| 安全 | OpenRouter key 只進 `.env`（gitignore）、`os.getenv` 讀、diagnostics raw-free（沿用 P93）、push 前掃描 |

### A 級
| 層 | 處置 |
|---|---|
| 架構 | provider registry 解耦；`FallbackLLMClient` 重構吃任意 `LLMProviderClient` |
| 資料 | run_manifest schema 加 provider+model 欄位、同步 manifest 契約測試 |
| 可觀察 | `active_provider` 動態反映真實首發（不再硬寫 gemini_primary）|
| 韌性 | 首發掛→fallback 鏈接手；budget guard 守門；OpenRouter 逾時 retry |
| 可維護 | 換首發＝改 config 一行；model 由 .env 配置不寫死（防 model id 過期）|
| 文件 | docstring 記 provider 切換契約；對比 CLI 用法；TASK_HISTORY 收官 |
| 流程 | P93 DRAFT→FROZEN→核准→runtime；R-016 治理更新 |

### B 級（觸發）
| 層 | 處置 |
|---|---|
| 成本 | 🔄 **反向**：OpenRouter 要用光（對賭）；對比 CLI 真實呼叫正好燒 |
| 部署 | `.env` 跨平台讀取；`py` 不用 `python`；rollback＝config 切回 gemini |

### 層級互鎖（META5）
動 Logic→動 Testing ✅；動 Architecture→動 Documentation ✅

## 7. 跨切面 X1-X4

### X1 可逆性
半可逆：`PRIMARY_PROVIDER=gemini` 一行切回 + git 回退新增檔；OpenRouter client/對比 CLI 為純新增，刪除即還原。

### X2 盲區掃描
「哪個 provider+model 分析了哪篇文章」主公看不到 → manifest `active_provider`+`model` 攤開；對比 CLI 並排顯示。

### X3 時間敏感性
6/5 額度對賭 deadline；OpenRouter model id 會隨時間改版（deepseek-r1 等）→ model 由 `.env` 配置、不寫死過期 id。

### X4 多角度同行審查
- **主公視角**：要燒額度測篩選 → 對比 CLI 直接服務；切 Sonnet 動工降成本。
- **紅隊視角**：OpenRouter key 洩漏面（.env/log/manifest raw）+ DeepSeek r1 經分析鏈的 prompt injection；緩解＝gitignore + raw-free diagnostics + budget guard。
- **接手者視角**：`PRIMARY_PROVIDER` 一行知首發；registry 集中、docstring 記契約。
- **X4-J 自動化邊界**：對比 CLI 是「並排比較」非「自動選最佳」；篩選好壞由主公人工判斷，無啟發式打分；CLI 末行印「比較僅供參考、最佳 model 需人工判斷」。
- **X4-K Patric**：主公可能誤以為「切 PRIMARY_PROVIDER 就自動最佳」→ 文件明講「要自己跑對比 CLI 判斷哪個 model 篩選好」。

## 8. 風險清單

| ID | 風險 | 緩解 | 殘留 |
|---|---|---|---|
| R-P105-1 🔴S | DeepSeek r1（推理模型）可能不支援 `json_schema` structured output → daily 分析拿到非 JSON 崩 | S2 輸出契約測試對每 model 真實呼叫驗 schema，不過的不准當首發；fallback 鏈接手 | 入 RISK_REGISTRY 觀察 |
| R-P105-2 🔴S | 解 fail-closed 誤放行 groq/cf/github（無 concrete client）→ 路由到不存在 client 崩 | 只放行 registry 有 concrete client 的 provider；未實作的仍 fail-closed raise | — |
| R-P105-3 🟡 | provider routing 啟用觸發 R-016 升級回 active blocking | S5 在 RISK_REGISTRY 明文「P105 核准啟用、非異常」，更新 R-016 觸發條件 | — |
| R-P105-4 🟡 | OpenRouter cache 與 OpenAI 用同 key → 快取污染 | cache key 含 provider+model 區分 | — |
| R-P105-5 🟡 | OpenRouter 繞過 P90 budget → 超額 | OpenRouter client 整合 `ensure_budget_for_provider_call` | — |

## 9. 工作階段 (Stages) — Sonnet 照規格執行

### S1 可切換地基（先不接 OpenRouter，純驗 gemini↔openai 互換）
1. `config.py` 加：`PRIMARY_PROVIDER`（預設 `"gemini"`）、`PRIMARY_MODEL`（預設 `""`）、`FALLBACK_PROVIDERS`（預設 `["openai"]`）。
2. 新 `analyzer/provider_registry.py`：`REGISTRY = {"gemini": GeminiClient, "openai": LLMClient}`（factory map）。
3. 重構 `analyzer/fallback_llm_client.py:27-44`：`primary` 型別 `Optional[GeminiClient]`→`Optional[LLMProviderClient]`；`fallback`→`fallbacks: List[LLMProviderClient]`（多級）；`_should_fallback`/`chat`/`batch_chat` 改走 fallbacks 鏈。
4. 改 `analyzer/provider_router.py:436-442` `build_default_llm_client()`：讀 config 用 registry 組裝 primary+fallbacks。
5. 測試 `tests/test_provider_switch.py`：切換矩陣（PRIMARY_PROVIDER=gemini/openai 各驗 primary 型別）。
- **verify**：`py -m pytest tests/ -q` ≥348；切 `PRIMARY_PROVIDER=openai` 後 `build_default_llm_client().primary` 是 `LLMClient`。

### S2 OpenRouter client + 輸出契約測試（B，真實呼叫燒額度）
1. `config.py` 加 OpenRouter 區（對照盤查建議）：`AOV_PROVIDER_OPENROUTER_ENABLED` / `OPENROUTER_API_KEY` / `OPENROUTER_BASE_URL`（預設 `https://openrouter.ai/api/v1`）/ `OPENROUTER_MODEL` / `_PRO` / `_FLASH` / `_MINIMAX`。
2. 新 `analyzer/provider_clients/openrouter_client.py`：仿 `llm_client.py`，`AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)`；複用 `_to_openai_json_schema`/`_build_response_format`；cache key 含 `"openrouter:"+model`；整合 `ensure_budget_for_provider_call`；滿足 `LLMProviderClient` Protocol（chat/batch_chat/cache_manager/CONCURRENCY_LIMIT）。
3. registry 加 `"openrouter": OpenRouterClient`。
4. 測試 `tests/test_openrouter_client.py`：**真實呼叫**對 deepseek-chat / deepseek-r1 / minimax-01 各跑一次 json_mode+response_schema，斷言回符合 schema 的 JSON；**r1/minimax 若不支援 structured output 則測試標記為 xfail/skip 並記錄**（這是 R-P105-1 的驗證）。
- **verify**：真實呼叫測試（燒額度）；產出「哪些 model schema 相容」結論表。

### S3 router 解 fail-closed + 動態 diagnostics + 可追溯（D）
1. `provider_router.py:49` `ALLOWED_PROVIDERS` 加 `"openrouter"`。
2. 改 `_guard_candidate_slots`（:360-375）：只對「registry 無 concrete client」的 slot fail-closed raise；有 client 的放行路由。
3. diagnostics（`fallback_llm_client.py:54-72` + router）：`active_provider` 改讀實際 primary 名（不硬寫 gemini_primary）。
4. run_manifest 加 provider+model 欄位（`analyzer/run_manifest.py`）。
5. `.env` 設 `PRIMARY_PROVIDER=openrouter`、`PRIMARY_MODEL=deepseek/deepseek-chat`（主公填）。
- **verify**：daily 主鏈路真實跑用 OpenRouter，manifest 記 `active_provider=openrouter`+model；`--check` 等治理 checker 不誤判。

### S4 provider 對比 CLI（C，飛輪核心·燒額度）
1. 新 `analyzer/provider_compare.py`（CLI）：`py -m analyzer.provider_compare --providers gemini,openrouter --model-a ... --model-b ... --posts <來源>`；同一批文章雙 provider/model 各跑一次、並排輸出篩選/分析結果差異。
2. 末行印 X4-J 邊界免責「比較僅供參考、最佳 model 需人工判斷」。
3. 測試 `tests/test_provider_compare.py`：mock 雙 provider 驗並排結構（不真發）；另留真實呼叫手動指令。
- **verify**：真實跑 `provider_compare` 比較 Gemini vs OpenRouter（燒額度），輸出可讀並排表。

### S5 測試矩陣鎖（E）+ 治理收官
1. 改 `tests/test_provider_router.py:69-97` fail-closed 契約：→「有 concrete client 的 enabled slot 放行路由、無 client 的仍 block」。
2. 同步 `tests/test_run_manifest.py`、`tests/test_system_doctor.py`、`tests/test_cost_cache_governance.py`（slot 清單 + provider 欄位變動）。
3. 切換矩陣鎖測試（E）：每 provider 當首發鏈組裝正確 + 各 model 輸出契約。
4. `docs/RISK_REGISTRY.md`：R-016 更新「P105 核准啟用 provider routing、非異常升級」；新增 R-P105-1（r1 schema）等。
5. 全套 ≥348+；本計畫書 DRAFT→FROZEN；TASK_HISTORY 追加 P105 收官（cat>>heredoc）。
- **verify**：全套綠；`py -m gov.assertions --check` exit 0；治理文件齊。

## 10. 影響檔案清單（STR7，收官更新）
**改**：`config.py`、`analyzer/fallback_llm_client.py`、`analyzer/provider_router.py`、`analyzer/run_manifest.py`、`tests/test_provider_router.py`、`tests/test_run_manifest.py`、`tests/test_system_doctor.py`、`tests/test_cost_cache_governance.py`、`docs/RISK_REGISTRY.md`、`TASK_HISTORY.md`
**新**：`analyzer/provider_registry.py`、`analyzer/provider_clients/openrouter_client.py`、`analyzer/provider_compare.py`、`tests/test_provider_switch.py`、`tests/test_openrouter_client.py`、`tests/test_provider_compare.py`
**.env（不進版控）**：OpenRouter 7 個變數

## 11. Postmortem 預埋點（G6）
若觸發：① DeepSeek r1 schema 不相容導致需改架構（記「我以為 OpenAI-compatible＝schema 相容」）② 解 fail-closed 誤放行 ③ daily 主鏈路換 provider 後篩選品質意外退化。

---

## ✈️ Pre-flight 多視角體檢（STR10）

### M1 強制填表（十一視角，每項 ≥20 字）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | 攻擊面：OpenRouter key 經 .env/log/manifest raw 欄位洩漏，或 DeepSeek 經文章內容做 prompt injection 污染分析；嚴重度高；最小緩解：.gitignore 排除 .env + diagnostics raw-free（沿用 P93 契約）+ budget guard 限流防成本濫用。 |
| **X4-B 接手者** | 半年後接手者看 `config.PRIMARY_PROVIDER` 一行即知首發、看 `provider_registry.py` 知有哪些 provider；docstring 記切換契約與多級 fallback 順序，不需讀完整 router 即可換首發。 |
| **X4-C 災難情境** | 情境：DeepSeek r1 不支援 json_schema，daily 全篇分析拿到推理文字而非 JSON、解析全失敗、當日戰報空白。緩解：S2 輸出契約測試先擋（不過的 model 不准當首發）+ fallback 鏈自動接手 Gemini。 |
| **X4-D 5 年後** | OpenRouter 的 model id（deepseek-r1/minimax-01）會改版或下架，寫死會腐化；故 model 一律由 .env 配置、registry 只管 provider 不管 model 版本，5 年後換 model 只改 .env。 |
| **X4-E 終端 vs IDE** | 對比 CLI 與所有驗證走終端 `py -m`（provider_compare/pytest/gov.assertions），無 IDE 外掛依賴；輸出純文字並排表，終端可讀。 |
| **X4-F 跨平台** | `.env` 讀取（python-dotenv）跨 Win/Mac/Linux 一致；命令一律 `py` 不用 `python`（Windows stub 陷阱）；路徑用 pathlib；無平台專屬 API。 |
| **X4-G 主公個人視角** | 主公要 6/5 前燒光老師額度 + 把篩選調到「每次都想看」；對比 CLI 直接服務（大量真實呼叫 + 並排比較）；動工切 Sonnet 降執行成本。 |
| **X4-H 觀測 / 治理** | manifest 記 active_provider+model 可追溯；R-016 治理更新避免誤觸升級；P93 DRAFT→FROZEN→核准流程合規；解 fail-closed 保留未選 provider 仍 block。 |
| **X4-I 主公可見性** | 自動行為：哪個 provider+model 分析了哪篇文章、何時 fallback 切換——主公看不到；攤開方式：manifest 寫入 + 對比 CLI 並排顯示 + daily log 印 active_provider。 |
| **X4-J 自動化工具邊界** | 對比 CLI 是「並排呈現兩 provider 結果」非「自動評分選最佳」；無啟發式打分；篩選好壞由主公人工判斷；CLI 末行印「比較僅供參考、最佳 model 需人工判斷」免責。 |
| **X4-K Patric 使用者端** | 主公可能誤以為「切 PRIMARY_PROVIDER 就自動變最佳篩選」→ 文件與 CLI 明講「切換只換 provider，篩選好壞要自己跑對比 CLI 判斷」，避免誤期待。 |

### M1.5 八人格顧問團

| 人格 | 是否觸發 / 發現 |
|---|---|
| **Jarvis 總控** | ✅ 目標（可切換+OpenRouter+對比 CLI）、邊界（不做自動選最佳）、S1-S5 派工、下一步（切 Sonnet 動工）皆清楚，結論先行。 |
| **Ken 紅隊/技術長** | ✅ key 安全（.env/raw-free）、fail-closed 保留未選 provider、budget guard、r1 schema 風險已列 R-P105-1/2。 |
| **Patric 使用者端** | ✅ 主公「切了就最佳」誤解 → X4-K + 文件明講要自跑對比 CLI。 |
| **Jimmy 文件主筆** | ✅ 觸發（改 TASK_HISTORY/RISK_REGISTRY）：收官紀錄附 commit/測試數，R-016 更新可追溯。 |
| **Marcus 數據分析** | ✅ 觸發（篩選品質比較）：對比 CLI 提供並排結果，定性（人工看）為主、不假裝定量打分。 |
| **Oliver 設計審查** | ✅ 觸發（對比 CLI 輸出）：並排表需欄位對齊、可讀；篩選差異標示清楚。 |
| **Penny CFO** | ✅ 觸發（API 成本）：OpenRouter＝老師額度要用光（反向）；Gemini/OpenAI 不增費；budget guard 為停損。 |
| **Jason 執行/DevOps** | ✅ 觸發（.env/git/跨平台）：`py` 不用 `python`、.env 跨平台、rollback＝config 切回、push 前掃 key。 |

### M2 紅藍對抗（≥5 質疑，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing 計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | DeepSeek r1 是推理模型，很可能不回 structured JSON，直接設首發會讓 daily 分析全崩 | **S** | 0（新） | S2 輸出契約測試對每 model 真實呼叫驗 schema，不過者不准當首發 + fallback 接手 | 入計畫範圍（S2）+ 入 RISK_REGISTRY（R-P105-1） |
| 2 | 解 fail-closed 可能誤放行 groq/cf/github 等無實作 client 的 slot，路由到不存在的 client 崩潰 | **S** | 0 | 只放行 registry 有 concrete client 的 provider；其餘仍 fail-closed raise | 入計畫範圍（S3）+ 入 RISK_REGISTRY（R-P105-2） |
| 3 | OpenRouter key 不慎進 git 或寫進 manifest/log 造成洩漏 | A | 0 | .env gitignore（已驗 data/* 機制）+ os.getenv 讀 + diagnostics raw-free + push 前掃描 | 入計畫範圍（S2/安全）+ 入 RISK_REGISTRY（R-P105-4） |
| 4 | 換首發後 daily 篩選品質比 Gemini 差，主公跑壞一天才發現 | A | 0 | C 對比 CLI 先離線比較滿意才切首發；manifest 記 provider 可追溯回滾 | 入計畫範圍（S4） |
| 5 | OpenRouter 與 OpenAI 共用 cache key 造成快取污染、拿到錯結果 | A | 0 | cache key 含 provider+model 前綴區分 | 入計畫範圍（S2） |
| 6 | provider routing 啟用觸發 R-016 升級回 active blocking 造成誤判 | A | 0 | S5 在 RISK_REGISTRY 明文「P105 核准啟用、非異常」，更新觸發條件 | 入 RISK_REGISTRY（R-P105-3） |

> M2 達標：6 質疑（≥5）✅，S 級 2 條（#1/#2）✅，無 pre-existing failing test 放行。

---

## 12. 凍結戳記
- **凍結人**：主公（2026-06-01 口頭核准「凍結」）+ AI（Opus 4.8 設計腦）
- **凍結時間**：2026-06-01（主公午餐前）
- **凍結後變更**：禁止；如需修改，新增「P105.X 補遺」引用本檔。
