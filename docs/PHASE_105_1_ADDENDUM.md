# 📋 P105.1 補遺 — provider:model 鏈 + per-model 額度調配（B 架構）

> **狀態**：🧊 FROZEN（2026-06-01 阿喜核准凍結｜M1/M2 lint PASS）｜**引用母計畫**：`docs/PHASE_105_PLAN.md`（FROZEN）｜**作者**：Opus 4.8（設計腦）｜**日期**：2026-06-01
> **自包含交接**：下個視窗讀本補遺 + `docs/PHASE_105_PLAN.md` + `docs/HANDOFF_P105_OpenRouter.md` 即可從 S3 動工。

---

## 0. 為何有這份補遺（凍結後變更）

母計畫書 S3 凍結時的設計是「單一 `PRIMARY_PROVIDER` + 解 fail-closed」。**S4 對比實證後，阿喜（2026-06-01）決定**：
1. gemini API 沒額度、OpenRouter 額度多 → **切 OpenRouter 首發**。
2. 要「以後可**詳細調配額度**」→ per-model 額度 + 鏈每級可指定 `provider:model`（架構選 **B**）。

此需求（`PROVIDER_CHAIN` + per-model budget）偏離凍結 S3，按律法（母計畫凍結戳記「凍結後變更新增 P105.X 補遺」）記為本補遺。

## 1. Scope 議定（重要：S3 範圍重切）

**原 S3「解 fail-closed（正式啟用 P93 router 框架）」→ 延後為獨立治理任務（不在本補遺）。**

- **理由**：切 OpenRouter 首發走 `FallbackLLMClient`（`PROVIDER_ROUTER_ENABLED=false`）即可，**不經 router 的 fail-closed guard** → 直接避開 **R-P105-2**（S 級：解 fail-closed 誤放行 groq/cf/github 無 client provider）+ **R-P105-3**（routing 啟用觸發 R-016 升級）。
- P93 router 框架正式啟用可日後 P105.2 或獨立治理任務處理（母計畫「啟用 P93 框架」目標部分延後，需告知阿喜並更新 R-016 狀態）。

**✅ 本補遺（修訂 S3）做**：B 架構（`PROVIDER_CHAIN` + per-model budget）+ diagnostics 動態化 + manifest provider/model + **score 標度校準** + 正式切首發。

## 2. B 架構設計

### 2.1 config（新解析，向後相容 S1）
```python
# .env — 鏈每級 provider:model（逗號分隔級、冒號分 provider:model）
PROVIDER_CHAIN = "openrouter:deepseek/deepseek-chat, openrouter:deepseek/deepseek-r1, gemini"
#   解析 → [("openrouter","deepseek/deepseek-chat"), ("openrouter","deepseek/deepseek-r1"), ("gemini", None)]
#   第一級＝首發，其餘＝多級 fallback。split(":", 1)（model 的 / 不是分隔符）。
OPENROUTER_MODEL_BUDGETS = "deepseek/deepseek-chat:80000, deepseek/deepseek-r1:20000"
#   解析 → {"deepseek/deepseek-chat":80000, "deepseek/deepseek-r1":20000}
```
- **向後相容鐵律**：無 `PROVIDER_CHAIN` 時退回 S1 的 `PRIMARY_PROVIDER`+`PRIMARY_MODEL`+`FALLBACK_PROVIDERS`（不可破 S1 切換測試）。
- 無對應 model budget → 用 `OPENROUTER_DAILY_BUDGET`（總上限 fallback）。

### 2.2 `build_default_llm_client`（改 `provider_router.py:436`）
讀 `PROVIDER_CHAIN`（有則用、無則 S1 路徑）→ 組 primary + fallbacks（各帶 model）→ `FallbackLLMClient(primary, fallbacks)`。仍 `PROVIDER_ROUTER_ENABLED=false` 不包 router。
- registry `build_provider(provider, model=m)` 已支援 model（S2 完成）✅；FallbackLLMClient 多級 fallbacks 已支援（S1 完成）✅。**主要工作在 chain 解析 + 組裝**。

### 2.3 OpenRouterClient per-model budget（改 S2 budget）
- `OpenRouterClient(model=X)` 的 budget：state 檔含 model（sanitize `/`→`_`，如 `data/openrouter_budget_deepseek_deepseek-chat.json`）+ 上限 `OPENROUTER_MODEL_BUDGETS.get(model, OPENROUTER_DAILY_BUDGET)`。
- 每 model 獨立 ledger（避免共用計數）。S2 已有單一 budget manager，改成 model-specific。

### 2.4 diagnostics 動態化（`fallback_llm_client.py:54-72` + `provider_router.py:430`）
- `active_provider` 改讀**實際 primary 名**（不再硬寫 `"gemini_primary"`）；attempts 的 provider 名反映實際（不硬寫 `"openai_fallback"`）。
- `ALLOWED_PROVIDERS`（`provider_router.py:49`）可能要加 openrouter 對應名（diagnostics 驗證/normalize 用）。

### 2.5 run_manifest provider+model（`run_manifest.py` ~:414 provider 區塊）
- manifest 加 `active_provider` + `active_model`（可追溯哪個 provider:model 分析了當日）。**動工時先讀 run_manifest.py provider 區塊現狀 + 同步 test_run_manifest.py**。

### 2.6 🔴 score 標度校準（S4 實證發現，切首發前必做）
- **根因**：`SINGLE_POST_SCHEMA`（`sentiment.py:40`）的 `sentiment_score` 只定 `{"type":"NUMBER"}`，**無語意/範圍說明** → gemini 與 deepseek 各自解讀（gemini negative→低分 / deepseek negative→高分）。
- **下游真實影響**：`analyzer/history.py:111,115` 用 `sentiment_score` 算歷史趨勢 → 切 deepseek 後 score 語意翻轉會讓**趨勢線失真**。
- **校準方向**：在 `SYSTEM_SINGLE_POST` prompt 或 schema description 明確定義 `sentiment_score` 語意（例如「0.0=極負面 … 1.0=極正面」），讓跨 model 一致。S3.2 先驗證（真實呼叫看 deepseek 校準後 score 是否對齊），再 S3.3 切首發。

## 3. 拆解（子階段 + verify）

| 子階段 | 內容 | verify |
|---|---|---|
| **S3.1** | `PROVIDER_CHAIN` + per-model budget（config 解析 + build_default 組鏈 + OpenRouterClient per-model budget）+ 測試 | 鏈組裝矩陣綠；無 CHAIN 退回 S1；per-model budget 各自上限；**全套 ≥370 不退** |
| **S3.2** | diagnostics 動態化 + manifest provider/model + score 標度校準 | diagnostics active_provider 反映實際；manifest 記 provider:model；score 校準後 deepseek 對齊 gemini 語意（真實呼叫驗） |
| **S3.3** | `.env` 正式切首發（`PROVIDER_CHAIN`）+ daily dry-run | daily 真實跑用 openrouter，篩選正常，manifest 正確，history 趨勢不失真 |

## 4. 17 層稽核重點（影響半徑 ~6-8 檔，標準 Phase）

- **代碼/邏輯（S）**：chain/budget 解析乾淨、向後相容、鏈順序正確
- **測試（S）**：鏈組裝矩陣 + per-model budget + **不破 S1 切換測試（基線 370 不退）**
- **安全（S）**：key 仍只進 `.env`；diagnostics raw-free（沿用 P93）
- **架構（A）**：`PROVIDER_CHAIN` **擴充**（非取代）`PRIMARY_PROVIDER`，雙路徑並存
- **資料（A）**：manifest `active_provider`+`active_model` schema + 同步 manifest 契約測試
- **可觀察（A）**：diagnostics 動態 active_provider
- **韌性（A）**：多級鏈接手 + per-model 停損
- **可維護（A）**：換首發/調順序/調額度＝改 `.env` 兩行
- **文件（A）**：docstring 記 `PROVIDER_CHAIN` 格式 + score 語意

## 5. 風險清單

| ID | 風險 | 緩解 |
|---|---|---|
| R-P105.1-1 🔴S | B 架構破壞 S1 向後相容（PRIMARY_PROVIDER 切換測試）| 保留 S1 路徑，PROVIDER_CHAIN 無則退回；測試雙路徑並存 |
| R-P105.1-2 🟡 | per-model budget state 檔爆量 | sanitize model 名；限 .env 配置的已知 model |
| R-P105.1-3 🔴S | score 標度未校準就切，history 趨勢失真 | S3.2 先校準（prompt 定義 score 語意）+ 真實呼叫驗對齊，S3.3 才切 |
| 沿用 | R-P105-1（minimax 不相容，已 xfail）/ R-P105-4（cache 污染，已 prefix）/ R-P105-5（budget 停損，per-model 強化）| 已處理 |

## 6. 現狀地圖（接手必讀）

- **分支**：`P105-openrouter`（已有 S1/S2/S4）。已 commit：S1 `7b37472`、S2 `5a6c814`、S4 `d6bed50`。
- **基線**：**370 passed, 4 skipped**（真實呼叫測試預設 skip）。
- **🚑 救急路徑**：阿喜可**現在**就在 `.env` 設 `PRIMARY_PROVIDER=openrouter` + `PRIMARY_MODEL=deepseek/deepseek-chat`，daily 立即改用 OpenRouter（S1 已支援，不必等 S3）。差別只在 diagnostics/manifest 可觀察性還不準 + 還沒 per-model 額度。
- **關鍵檔/行**：
  - `build_default_llm_client`：`analyzer/provider_router.py:436`
  - `FallbackLLMClient`（多級鏈）：`analyzer/fallback_llm_client.py`
  - `OpenRouterClient`（per-model budget 改這）：`analyzer/provider_clients/openrouter_client.py`
  - diagnostics 硬寫點：`fallback_llm_client.py:70`、`provider_router.py:430`
  - `sentiment_score` schema：`analyzer/sentiment.py:40`；下游趨勢：`analyzer/history.py:111,115`
  - registry：`analyzer/provider_registry.py`（已支援 model）

## 7. 下個 session 開工指引

1. 讀本補遺 + `docs/PHASE_105_PLAN.md`（母計畫）+ `docs/HANDOFF_P105_OpenRouter.md`。
2. 確認分支 `P105-openrouter`、基線 `py -m pytest tests/ -q` = 370 passed 4 skipped。
3. 從 **S3.1** 開工（TDD：先寫鏈組裝 + per-model budget 測試）。
4. **鐵律**：`py` 不用 `python`（`$env:PYTHONUTF8=1`）；push 前問阿喜；寫檔後 git diff/pytest 交叉驗證；**基線 370 不退**；OpenRouter key 只進 `.env`；TASK_HISTORY 禁全讀。
5. 每子階段 dry-run → 阿喜拍板 → commit（本地，push 前問）。
6. **執行用 Sonnet**（規劃已 Opus 完成）。

---

## ✈️ Pre-flight 多視角體檢（M1/M2，針對 B 架構）

### M1 強制填表（十一視角，每項 ≥20 字）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | 攻擊面：`PROVIDER_CHAIN` 解析若不驗證可注入無效 provider:model 讓 build_provider 爆；per-model budget state 檔以 model 名拼路徑恐 path traversal；緩解：provider 走 registry 白名單驗證 + model 名 sanitize（限 `[\w/.\-]`）+ key 仍只 `os.getenv` 讀 .env。 |
| **X4-B 接手者** | 半年後接手者看 `PROVIDER_CHAIN` 一行即知整條鏈（首發+多級 fallback+各 model）、看 `OPENROUTER_MODEL_BUDGETS` 知各 model 額度；docstring 記格式 + 向後相容 S1 路徑，不需讀完 build_default 即可調鏈。 |
| **X4-C 災難情境** | `PROVIDER_CHAIN` 配置 typo（錯 model 名）→ daily 啟動 build_provider raise → 整日無戰報。緩解：解析時驗證 + 無效退回 S1 預設 + 啟動前 dry-run 驗證鏈可組裝。 |
| **X4-D 5 年後** | OpenRouter model id（deepseek-r1/minimax）會改版下架，寫死會腐化；故 chain 由 .env 配置、registry 只管 provider 不管 model 版本，5 年後換 model 改 .env 一行不動 code。 |
| **X4-E 終端 vs IDE** | 所有驗證走終端 `py -m pytest` + daily dry-run，無 IDE 外掛依賴；`PROVIDER_CHAIN`/`OPENROUTER_MODEL_BUDGETS` 在 .env 純文字配置，終端可讀。 |
| **X4-F 跨平台** | .env 字串解析（split）跨 Win/Mac/Linux 一致；per-model budget state 檔路徑用 pathlib + model 名 sanitize；命令 `py` 不用 `python`（Windows stub 陷阱）。 |
| **X4-G 阿喜個人視角** | 阿喜要 gemini 沒額度時切 openrouter + 詳細調配額度（per-model）；B 架構直接服務——`PROVIDER_CHAIN` 切首發 + `OPENROUTER_MODEL_BUDGETS` 調各 model 額度，且救急可先改 .env。 |
| **X4-H 觀測 / 治理** | diagnostics 動態 active_provider + manifest active_provider/model 可追溯；解 fail-closed **延後**（不動 P93 治理契約、避 R-016 誤升級）；補遺引用母計畫 FROZEN 流程合規。 |
| **X4-I 阿喜可見性** | 哪個 provider:model 分析了當日、各 model 燒多少額度——阿喜看不到；攤開：manifest 寫 active_provider+model + per-model budget ledger 可查 + diagnostics 印實際 provider。 |
| **X4-J 自動化工具邊界** | B 架構是「按 .env 配置組鏈」非「自動選最佳 model」；無啟發式打分；篩選好壞仍由阿喜跑對比 CLI 人工判斷（沿用 S4 X4-J）。 |
| **X4-K Patric 使用者端** | 阿喜可能誤以為「配了 per-model budget 就自動分配最佳」→ 文件明講「budget 是停損上限非自動分配；鏈順序與各 model 額度由你 .env 配」。 |

### M1.5 八人格顧問團

| 人格 | 是否觸發 / 發現 |
|---|---|
| **Jarvis 總控** | ✅ 目標（切首發+per-model 調配）、邊界（不解 fail-closed、不自動選最佳）、拆解（S3.1/3.2/3.3）、下一步（fresh session 動工）清楚。 |
| **Ken 紅隊/技術長** | ✅ PROVIDER_CHAIN 注入 / path traversal / 向後相容破壞 / score 失真已列 X4-A + R-P105.1-1/3。 |
| **Patric 使用者端** | ✅ 阿喜「配了就最佳」誤解 → X4-K + 文件明講。 |
| **Jimmy 文件主筆** | ✅ 觸發：補遺 + 收官 TASK_HISTORY + docstring 記 chain 格式 + score 語意。 |
| **Marcus 數據分析** | ✅ 觸發：score 標度校準（history.py 趨勢失真）已列 R-P105.1-3 + S3.2 校準。 |
| **Oliver 設計審查** | ✅ 觸發：`PROVIDER_CHAIN` config 形式一行可讀整條鏈，可維護性高。 |
| **Penny CFO** | ✅ 觸發：per-model budget 停損＝燒額度但有天花板；OpenRouter＝老師額度要用光。 |
| **Jason 執行/DevOps** | ✅ 觸發：.env 跨平台、`py` 不用 `python`、rollback＝改回 `PRIMARY_PROVIDER`/移除 PROVIDER_CHAIN。 |

### M2 紅藍對抗（≥5 質疑，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing 計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | B 架構改 build_default 組鏈，恐破壞 S1 的 `PRIMARY_PROVIDER` 切換測試（370 基線退）| **S** | 0（新） | 保留 S1 路徑（無 `PROVIDER_CHAIN` 則退回），雙路徑測試並存、基線不退 | 入計畫範圍（S3.1）+ 入 RISK_REGISTRY（R-P105.1-1）|
| 2 | `sentiment_score` 標度未校準就切 deepseek 首發，`history.py` 趨勢線失真、報表誤導 | **S** | 0 | S3.2 先在 prompt/schema 定義 score 語意 + 真實呼叫驗對齊，S3.3 才切首發 | 入計畫範圍（S3.2）+ 入 RISK_REGISTRY（R-P105.1-3）|
| 3 | `PROVIDER_CHAIN` typo（錯 model 名）→ daily 啟動 build_provider raise、整日崩 | A | 0 | 解析時驗證 + 無效退回 S1 預設 + 啟動 dry-run 驗鏈可組裝 | 入計畫範圍（S3.1）|
| 4 | per-model budget state 檔以 model 名拼路徑，恐 path traversal | A | 0 | model 名 sanitize（白名單字元）+ pathlib 組路徑 | 入計畫範圍（S3.1）|
| 5 | OpenRouter key 經 `PROVIDER_CHAIN`/budget state 洩漏 | A | 0 | chain/budget 只存 provider:model + 計數，key 仍 `os.getenv` 讀 .env、不進版控 | 入計畫範圍（S3.1 安全層）|
| 6 | 解 fail-closed 延後 → 母計畫「啟用 P93 框架」目標未達、R-016 狀態不一致 | A | 0 | 補遺 §1 明文延後為獨立任務 + S5 更新 R-016 標註「P105 切首發走 FallbackLLMClient、router 啟用另議」 | 入 RISK_REGISTRY（R-016）+ Scope 議定 §1 |

> M2 達標：6 質疑（≥5）✅，S 級 2 條（#1/#2）✅，無 pre-existing failing test 放行。

## 8. 凍結戳記
- **凍結人**：阿喜（2026-06-01 選「凍結+commit+過 lint」）+ AI（Opus 4.8 設計腦）｜`lint_phase_plan` PASS（M1+M2）。
- **凍結後變更**：禁止；如需再修，新增 P105.2 補遺引用本檔。
