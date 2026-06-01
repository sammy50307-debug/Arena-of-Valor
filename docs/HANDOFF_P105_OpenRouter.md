# 🤝 P105 交接筆記 — OpenRouter Provider 整合（新視窗開局必讀）

> **給下一個視窗 + Sonnet 的自包含交接**。看完這份 + `docs/PHASE_105_PLAN.md`（FROZEN 計畫書）即可直接動工，不需回看上個對話。
> **作者**：Opus 4.8（設計腦）｜**日期**：2026-06-01｜**狀態**：計畫書已凍結、**尚未動工**

---

## 0. 一句話起手式（貼到新視窗）
> 接手 P105（OpenRouter provider 整合 + 首發可切換）。讀 `docs/PHASE_105_PLAN.md`（FROZEN 完整規格）+ 本交接。從 **S1** 開工。鐵律：`py` 不用 `python`、push 前問主公、寫檔後 git diff/pytest 交叉驗證、基線 **348 不退**、OpenRouter key 只進 `.env` 不進版控。

## 1. 要做什麼（目標）
把 AOV 的 **LLM provider 鏈**正式接入 **OpenRouter** 並設為首發，且做成**首發 provider+model 可一行配置切換**的架構（日後換任何 LLM 都只改 config 一行）。附一個 **provider 對比 CLI**（同批文章雙跑比較篩選結果）。

## 2. 為什麼（觸發背景）
- 主公老師給 **OpenRouter 100 美金額度**，跟學生對賭「**6/5（週五）前用光再加碼 100**」→ 要**大量真實呼叫、儘量燒、不用省**。
- 主公目標：趁機把文章篩選/分析調到「**每次找出來都是想看的東西**」。
- 順便把 provider 層重構成可切換架構（好維護、好換）。
- ⚠️ **費用約束反轉**：OpenRouter 要用光（非省）；但 Gemini/OpenAI 維持不增費（R-016 行 275）。

## 3. 必讀檔（開局順序）
1. **`docs/PHASE_105_PLAN.md`** — FROZEN 計畫書，**主執行規格**（S1-S5 含確切檔案/行號、17 層、M1/M2 體檢、風險清單）。**這是動工的聖經。**
2. 本交接（脈絡 + 鐵律 + 現狀地圖）。
3. 需要時：`docs/RISK_REGISTRY.md`（R-016 provider 約束）、`TASK_HISTORY.md` P93 段（grep 錨點精讀，**禁全讀**）。

## 4. 現狀地圖（4 子代理盤查 + Opus 親自交叉驗證過，可信）

### 4a. 釐清一個誤解：有「兩條不相干的瀑布鏈」
| 鏈 | 決定 | 首發 | 檔案 |
|---|---|---|---|
| 搜尋來源瀑布 | 文章**從哪爬** | Tavily→DDG | `scrapers/waterfall_searcher.py` |
| **LLM provider 瀑布**（本 Phase 要動的）| 文章**用哪個 LLM 分析** | **Gemini**→OpenAI | `analyzer/fallback_llm_client.py:33` |

→ OpenRouter 是 LLM provider，接的是**下面那條**，跟爬蟲/搜尋瀑布無關。

### 4b. LLM provider 鏈現狀
```
Gemini (gemini-3.1-flash-lite →429→ gemini-3.5-flash)   ← 首發 fallback_llm_client.py:33
   ↓ 僅 429/5xx/逾時 fallback
OpenAI (gpt-4o-mini)                                      ← 副發 llm_client.py:78（無 base_url）
```
- **OpenRouter 全 repo 零實作**（唯一命中是 `governance_config.yaml:70` 的密鑰掃描 regex）。要新寫 client。
- **OpenRouter 是 OpenAI-compatible** → client 幾乎可整碗端 `analyzer/llm_client.py`（只差 `base_url` + key + model）。

### 4c. P93 治理現狀（重要約束）
- `provider_router.py` 是 **fail-closed**：任何非 Gemini slot 一 `enabled` → `_guard_candidate_slots()`（:360-375）直接 `raise ProviderRouteBlocked`，**不呼叫**。
- 首發硬寫 `gemini_primary`（diagnostics `fallback_llm_client.py:70`）。
- `provider_clients/` 只有 `base.py`（Protocol 抽象），**無 concrete client**。
- **R-016 行 294**：「provider routing 非預期啟用」會觸發風險升級 → S5 必須在 RISK_REGISTRY 明文「P105 核准啟用、非異常」。

## 5. 架構設計（這是「好切換」的核心）
```python
# config.py — 換首發＝改這一行
PRIMARY_PROVIDER   = "openrouter"          # gemini│openai│openrouter
PRIMARY_MODEL      = "deepseek/deepseek-chat"
FALLBACK_PROVIDERS = ["gemini", "openai"]

# analyzer/provider_registry.py（新）
REGISTRY = {"gemini": GeminiClient, "openai": LLMClient, "openrouter": OpenRouterClient}

# FallbackLLMClient 重構：primary 吃任意 LLMProviderClient + 多級 fallback
```
`LLMProviderClient` Protocol（`analyzer/provider_clients/base.py`）只要 4 項：`CONCURRENCY_LIMIT`、`cache_manager` property、`chat()`、`batch_chat()`。

## 6. 五階段（詳細步驟見計畫書 §9）
| 階段 | 一句話 | 關鍵 verify |
|---|---|---|
| **S1** | config 切換變數 + registry + 重構 FallbackLLMClient（先驗 gemini↔openai 互換）| 切 `PRIMARY_PROVIDER=openai` 後 primary 是 LLMClient；全套 ≥348 |
| **S2** | 寫 OpenRouter client（仿 llm_client）+ **真實呼叫輸出契約測試** | deepseek-chat/r1/minimax 各驗 schema 相容（燒額度）|
| **S3** | router 解 fail-closed + diagnostics 動態 + manifest 記 provider+model | daily 真實跑用 OpenRouter、manifest 正確 |
| **S4** | **provider 對比 CLI**（同批雙跑比較，燒額度測篩選）| `py -m analyzer.provider_compare` 並排輸出 |
| **S5** | 矩陣鎖測試 + 治理收官（R-016 更新 + TASK_HISTORY）| 全套 ≥348+、`gov.assertions --check` exit 0 |

## 7. 鐵律（務必遵守，違反會出事）
1. **`py` 不用 `python`**（Windows stub 會空退出）；跑測試前 `$env:PYTHONUTF8=1`。
2. **基線 348 passed 不退**（P104 後）；每階段 verify。
3. **OpenRouter key 只進 `.env`**（已 `.gitignore`）、**絕不進版控/不貼進任何同步檔**；`os.getenv` 讀、push 前掃描。
4. **push 前問主公**。
5. **寫檔後不信工具回傳**，用獨立命令（git diff/pytest/`--check`）交叉驗證。
6. **TASK_HISTORY.md 禁全讀**：grep 錨點 + Read offset≤200。
7. 🔴 **DeepSeek r1 風險**：r1 是推理模型，**可能不支援 json_schema structured output** → S2 必須真實呼叫驗證，不過的 model **不准當首發**（否則 daily 分析全崩）。
8. 🔴 **解 fail-closed 只放行「registry 有 concrete client」的 provider**，groq/cf/github（無 client）仍要 fail-closed block。

## 8. 關鍵檔案 / 行號速查
| 檔案:行 | 是什麼 |
|---|---|
| `analyzer/fallback_llm_client.py:33` | 首發 = `GeminiClient()`（S1 要重構成可配置）|
| `analyzer/fallback_llm_client.py:70` | diagnostics 硬寫 `gemini_primary`（S3 動態化）|
| `analyzer/provider_router.py:436-442` | `build_default_llm_client()` 入口（S1 讀 config 組裝）|
| `analyzer/provider_router.py:49` | `ALLOWED_PROVIDERS`（S3 加 openrouter）|
| `analyzer/provider_router.py:360-375` | fail-closed guard（S3 改成只擋無 client 的）|
| `analyzer/llm_client.py` | OpenAI client（S2 仿它寫 OpenRouter，已 OpenAI-compatible）|
| `analyzer/provider_clients/base.py:9-36` | LLMProviderClient Protocol（新 client 要滿足）|
| `analyzer/provider_budget.py:8-18` | budget guard（OpenRouter 要整合）|
| `analyzer/sentiment.py:265/473` | LLM 唯二呼叫出口（batch/chat）|
| `tests/test_provider_router.py:69-97` | fail-closed 契約（S5 要改寫）|

## 9. 動工流程（主公回來後）
1. **切 Sonnet**（規劃用 Opus 已完成、執行用 Sonnet）。同對話切 context 保留；新視窗讀 `docs/` 即可。
2. **先填 `.env`**：OpenRouter 7 變數（`OPENROUTER_API_KEY` 等），**不進版控**。
3. **從 S1 開工**（TDD：先寫測試）。每階段 dry-run→主公拍板→commit。
4. **若撞計畫外的模糊判斷**（r1/minimax 行為超乎預期、daily 跑出非預期）→ **升級回 Opus 或問主公**，別硬猜。

## 10. 目前狀態
- ✅ 計畫書 `docs/PHASE_105_PLAN.md` **已 FROZEN**（M1/M2 lint PASS）。
- ✅ 盤查完成（本交接 §4）。
- ⬜ **尚未動工**（S1-S5 全待做）。
- 📌 基線：全套 **348 passed**（P104 收官後）。
- 📌 P104 已全收官 + pushed（治理引擎，與本 Phase 無關但同 repo）。
