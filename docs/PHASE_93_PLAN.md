# Phase P93 計畫書 — Provider Abstraction / Disabled-by-default Free Provider Slots（收官版）

> 狀態：CLOSED。主公已於 2026-05-22 核准 P93 runtime 動工；本 Phase 已完成 disabled-by-default provider abstraction、raw-free provider diagnostics、doctor / cost governance 訊號、fake-provider / no-call / budget guard 測試。未新增任何 provider secret，未加入 GitHub Actions `models: read`，未把 Groq / Cloudflare / GitHub Models 接進 daily default。R-016 仍 Open。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P93 |
| **Phase 名稱** | Provider Abstraction / Disabled-by-default Free Provider Slots |
| **凍結日期** | 2026-05-22 |
| **草案日期** | 2026-05-22 |
| **收官日期** | 2026-05-22 |
| **影響半徑** | 重大 (10+ 檔) - 新增 provider protocol / router / shared budget guard，接入 manifest diagnostics、doctor、cost governance、tests、runbook 與作戰帳本 |
| **預估投入時數** | Plan-only 1-2 小時；runtime 6-10 小時 |
| **Token budget** | Plan-only 20K-35K；runtime 70K-110K |
| **負責模型** | GPT-5.3-Codex 高；若 provider contract / budget ledger 同題修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P93 plan | NEW | DRAFT | 已建立草案，但不得 runtime 動工 | 本檔建立並通過 plan lint | AI 建立，主公審核 |
| P93 plan | DRAFT | FROZEN | 計畫邊界固定，但 runtime 仍不可施工 | 主公明確核准草案內容；需同步 handoff / active / risk / history | 主公核准，AI 執行 |
| P93 runtime | APPROVED | CLOSED | disabled-by-default provider abstraction 已完成本地驗證 | 主公已核准 runtime；provider protocol / router / diagnostics / governance / tests 已落地 | 主公核准，AI 執行 |
| provider candidates | Candidate | Disabled-by-default slot | 有設定名稱與契約，但預設不可呼叫 | 僅建立 registry/contract；預設 `enabled=false` 且 CI 驗證 fail-closed | AI 實作，主公核准 |
| R-016 | Open | Open | R-016 仍是跨 Phase 風險；P93 只處理 provider abstraction 子問題 | P93 不得直接關閉 R-016，需等 P95 closeout | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

設計一個 fail-closed 的 LLM provider abstraction：讓 Groq、Cloudflare Workers AI / AI Gateway、GitHub Models 只能作為 disabled-by-default 候選插槽存在；預設每日報告仍使用現有 Gemini + local deterministic + P90-P92 budget/replay 鏈路，且未經主公核准不得呼叫任何新 provider。

## 2. 觸發背景 (Why Now)

P91 已把 LLM 呼叫量從 pre-P91 28 次壓到 6 次；P92 已把 local-only 補深讀設計成 artifact-backed、budget-aware replay。下一個自然問題是：「如果 Gemini quota / model availability 再次不穩，是否能用零額外付費或既有平台額度補一層候選供應商？」主公已明確不想增加 OpenAI API 成本，因此 P93 必須先建立抽象層與禁用預設，而不是直接把免費 provider 接進主鏈路。

### 2.1 官方查證基礎

| Provider 候選 | 官方文件目前能確認的能力 | P93 採用方式 |
|---|---|---|
| Groq | 官方文件標示 OpenAI-compatible，並示範 `baseURL` 指向 `https://api.groq.com/openai/v1`；Chat Completions / Models API 走 Groq key。參考：[Groq overview](https://console.groq.com/docs/overview)、[Groq API reference](https://console.groq.com/docs/api-reference)。 | 只列為 `groq` disabled slot；不承諾免費額度，不在 plan-only 階段加 key 或呼叫。 |
| Cloudflare Workers AI / AI Gateway | 官方 REST API 提供 `/ai/v1/chat/completions`，並標示 OpenAI chat completions / OpenAI SDK compatible；同頁也描述 Gateway 可套用 logging、caching、rate limiting。參考：[Cloudflare AI Gateway REST API](https://developers.cloudflare.com/ai-gateway/usage/rest-api/)。 | 只列為 `cloudflare_ai` disabled slot；因 Gateway logging/caching 牽涉資料留存，runtime 必須另過 privacy gate。 |
| GitHub Models | 官方 quickstart 說可用 GitHub credentials / Actions 呼叫，REST inference endpoint 為 `https://models.github.ai/inference/chat/completions`，workflow 需 `models: read`。參考：[GitHub Models quickstart](https://docs.github.com/en/github-models/quickstart)、[REST inference API](https://docs.github.com/en/rest/models/inference)。 | 只列為 `github_models` disabled slot；若 runtime 使用 Actions `GITHUB_TOKEN`，需明確 permissions 與 repository/org access 邊界。 |

不確定事項直接入風險：各 provider 免費額度、rate limit、資料留存條款、模型清單與 API 兼容度會隨時間變動；P93 不把「免費」當永久事實，只把它們列為「零新增付費候選」。

### 2.2 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Disabled-by-default provider abstraction | 建 provider interface / registry / factory / budget guard / fake-provider tests；所有新 provider 預設關閉 | 可測、可回滾、主鏈路不偷跑、後續 provider 可逐一核准 | 前期文件與測試較厚，短期不增加可用額度 | 採用 |
| B. 直接用 OpenAI-compatible client 接 Groq / Cloudflare / GitHub Models | 改 `base_url` 與 API key 後先跑看看 | 最快看到能不能通 | 容易繞過 P90 budget、P92 replay、secret/privacy gate；免費額度與條款未核實 | 不採用 |
| C. 繼續只用 Gemini + local deterministic，不做 abstraction | 完全不增加供應商風險 | 最保守、最小改動 | Gemini quota / availability 再波動時沒有工程插槽，只能臨時補洞 | 不採用作為中期策略 |
| D. 使用 LiteLLM 等第三方統一層 | 多 provider 支援現成，少寫 adapter | 省時 | 新依賴、版本風險、資料面與設定面變大，不符合 P93 fail-closed 小步設計 | 暫不採用 |

採用 A。P93 的思路不是「找免費模型來打」，而是「把可呼叫模型的閘門、證據、成本與隱私邊界先做成硬規格」。

## 3. Entry Criteria（入口條件）

P93 plan-only 開工前必須全部達成：
- [x] 前置 Phase 已收官：P92 CLOSED，commit `9dc28d7` 已 push，並已由 Actions run `26282601411` 驗證 enrichment artifact / manifest snapshot。
- [x] 本地與遠端同步：Actions auto-sync commit `4f0e5b7` 已 fast-forward pull，本地 tracked 區乾淨。
- [x] 主公已要求進 P93 plan：2026-05-22 主公回覆「進 P93 plan」。
- [x] 風險登記簿真相：R-016 仍 Open，不得因 P93 plan 直接關閉。
- [x] Provider 官方文件已查證到足夠設計依據，但免費額度與條款仍列不確定。

P93 runtime 開工前尚需另行達成：
- [x] 本檔由 DRAFT 轉 FROZEN，並同步 `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` / `docs/RISK_REGISTRY.md` / `TASK_HISTORY.md`。
- [x] 主公明確核准 P93 runtime 動工：2026-05-22 主公回覆「核准 P93 runtime 動工」。
- [x] 本次 runtime 未建立 live provider adapter；候選 provider 官方能力沿用同日 plan 查證，任何後續 live smoke / per-provider enable 必須重新查 rate limit / data retention / pricing / authentication。
- [x] 明確確認不新增任何 paid OpenAI fallback 成本，不把新 provider 預設接進 daily chain。

## 4. Exit Criteria（退出條件）

P93 plan-only 凍結需全部達成：
- [x] `docs/PHASE_93_PLAN.md` 建立完成。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_93_PLAN.md` 通過。
- [x] `git diff --check` 通過。
- [x] 本檔明確列出 disabled-by-default、kill switch、secret/privacy、budget ledger、fake-provider contract tests。
- [x] P93 runtime 明確維持未核准狀態；不得新增 provider key、不得呼叫 provider、不得修改每日主鏈路。

P93 runtime 收官需全部達成：
- [x] 建立 provider interface，至少支援 `chat` / `batch_chat` / `cache_manager` 相容契約，不把 provider 特例散落到 `main.py`。
- [x] 建立 provider registry / factory，所有非 Gemini provider 預設 `enabled=false`，且沒有 env var 時 fail-closed。
- [x] 建立 kill switches：`PROVIDER_ROUTER_ENABLED=false`、`EXPERIMENTAL_FREE_PROVIDERS_ENABLED=false`、per-provider enabled flag 全預設 false。
- [x] P90 budget ledger 接入 shared guard；OpenAI fallback 切換前也需過 budget / cooldown，不再只守 Gemini primary path。
- [x] Provider diagnostics raw-free：manifest 可寫 provider route / attempt / failure class / budget decision，但不得寫 raw prompt、raw response、secret、author PII。
- [x] Tests 覆蓋 no-env no-call、disabled-provider no-call、fake-provider success/failure、fallback stop condition、budget/cooldown skip、schema normalization、secret masking。
- [x] GitHub Actions / production default 不改每日呼叫 provider 路徑；新 provider 必須由 manual flag 或後續 Phase 才能試跑。
- [x] Focused tests、py_compile、governance doctor 通過；full pytest 與 doctor/cost closeout 驗證見本檔收官證據。R-016 仍 Open。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | Plan-only 1-2 h；runtime 6-10 h |
| 預估收益等級 | 中高 |
| 收益描述 | 把「免費 provider 候選」從臨時手接變成可測、可關、可審計的工程插槽；保護 P90-P92 已建立的成本與證據鏈 |
| ROI 結論 | 值得做，但必須 plan-first；未建立 fail-closed 前，直接接 provider 的風險高於收益 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | Provider interface、registry、factory、shared budget guard 小步拆分；不把新 provider 寫進 `main.py` 分支 | adapter 特例散落，半年後無法確認哪條路會呼叫哪個 provider | runtime 時以 `analyzer/provider_clients/` 或等價小模組集中，並用 contract tests 固定 |
| **2. 邏輯層 (Logic)** | fail-closed routing；disabled provider 必須 no-call；fallback 只處理 provider failure，不處理內容品質 | 把 provider failure、schema failure、content low quality 混成同一種 fallback，造成錯誤重試或成本外溢 | 明確定義 failure taxonomy：rate_limit/server/network 可 fallback；schema/content failure 不自動換 provider |
| **4. 測試層 (Testing)** | fake-provider + monkeypatch HTTP tests；預設環境 no-call tests；budget/cooldown matrix tests | 只在有真 API key 時才測，導致 CI 無法防偷跑 | 所有 provider contract tests 預設不碰外網、不需要 secret；真 provider smoke test 另開 manual-only |
| **10. 安全層 (Security)** | secrets 不落檔、不進 manifest；provider response raw-free；Cloudflare/GitHub token 權限最小化 | secret 被 log、manifest 洩漏 prompt/response、Actions token 權限過大 | secret masking tests、raw-free diagnostics schema、GitHub `models: read` 權限單獨列入 workflow gate |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 新增 provider router / registry 邊界；現有 Gemini path 仍是主路徑 | 架構一改就打破 P88-P92 local baseline / budget / replay | runtime 以 wrapper 層接住既有 `GeminiClient` / `FallbackLLMClient`，每日 default 不切路 |
| **5. 資料層 (Data)** | diagnostics 只寫 provider id、attempt、status、failure class、digest；不寫 raw content | 第三方貼文或 prompt/response 進 repo | raw-free schema + tests 檢查 `content` / `prompt` / `response` 類欄位不得入 manifest |
| **6. 可觀察性層 (Observability)** | manifest / doctor / governance 顯示 provider enabled state、route、skip reason、budget decision | 主公看到 production local-only，卻不知道 provider 是未啟用還是失敗 | diagnostics 明確區分 `disabled_by_default`、`missing_secret`、`budget_blocked`、`provider_failed` |
| **7. 韌性層 (Resilience)** | fallback stop condition、max attempts、cooldown respect；不做 provider cascade loop | 多 provider 連環重試造成 timeout / cost abuse | 每次 run 限制 provider attempts；budget guard 在每次 provider call 前執行 |
| **13. 可維護性層 (Maintainability)** | provider config schema 版本化；provider capability matrix 文件化 | provider 模型、API 版本、免費額度改動後文件腐化 | X3 設 30 天重審；runtime docs 寫「免費額度非永久事實」 |
| **14. 文件層 (Documentation)** | P93 plan、runbook、cost policy、handoff 明確列 forbidden work 與啟用步驟 | 接手者誤把候選 provider 當已啟用 | 文件使用 `disabled slot` 而不是 `provider enabled`，並列出啟用需主公核准 |
| **15. 流程層 (Process)** | DRAFT -> FROZEN -> APPROVED -> runtime；任何 provider live test 需 manual-only | AI 在 plan 後直接接 provider 或 push workflow 權限 | active/handoff 同步 forbidden work；push 前仍需主公確認 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 多 provider fallback / replay 可能增加 latency | daily run timeout 或 report 晚產 | default disabled；runtime 設 max attempts / timeout / manual-only smoke |
| **9. UX/A11y 層** | 報告 metadata / operation docs 會呈現 provider 狀態 | 主公或接手者誤解 disabled 為錯誤 | status 文案用「候選未啟用」而非「失敗」 |
| **11. 部署層 (DevOps)** | GitHub Actions permissions / secrets / workflow_dispatch 可能變更 | workflow token 權限過大或 secrets 被誤加 | `models: read` 僅在 GitHub Models runtime 被核准後才加入；manual-only smoke workflow 另審 |
| **12. 成本層 (Cost)** | LLM provider / free tier / rate limit | 免費額度改條款、超限計費、重試爆量 | 不承諾免費永久；default disabled；budget ledger / cooldown / per-provider cap |
| **16. 隱私/合規層 (Privacy)** | 第三方 provider 會收到玩家貼文內容 | 原始貼文送往新 provider 的資料處理條款不明 | runtime 前逐 provider 查 data retention；只在主公核准後，以最小 payload 試跑 |
| **17. i18n/在地化層** | 不同 provider 對繁中、遊戲術語、JSON schema 支援不一 | provider 回覆品質比 local baseline 更差 | fake contract 只驗 schema；真品質需後續 small sample eval，不自動 promotion |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 Performance 層 -> 已規劃 Observability 層。

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_93_PLAN.md` | 可逆 | 主公要求進 P93 plan；2026-05-22 已核准凍結 |
| P93 plan 轉 FROZEN 並 commit | 可逆 | 主公於 2026-05-22 回覆「核准」 |
| 新增 provider abstraction runtime | 可逆；本次只新增 disabled-by-default router 與 fake-provider tests | 主公於 2026-05-22 核准 runtime 動工 |
| 新增 GitHub Actions `models: read` 或 provider secrets | 半可逆 | 未執行；後續若做 per-provider live smoke 需逐項核准 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：provider router 即使 disabled，也可能在 diagnostics 顯示候選名稱；文案需避免讓人以為已呼叫。
- [x] 中間檔產出：runtime 若做 live smoke，可能產生 local artifact / logs；預設測試必須全部 fake provider。
- [x] 系統狀態變更：一旦 workflow 加 `models: read` 或 secrets，即使 provider disabled，也會改變 Actions 權限面；需單獨審核。

### X3 時間敏感性 (Time Decay)

- 本計畫草案日期：2026-05-22。
- 本計畫凍結日期：2026-05-22。
- 本計畫過期日期：2026-06-22；若任一 provider pricing / free tier / data retention / endpoint 官方文件先變更，runtime 前必須重查。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：P93 要讓主公保有「要不要啟用新 provider」的最後裁決權，而不是 AI 因為看到免費候選就自動接上。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面包含 secret 外洩、prompt/response 進 manifest、Actions token 權限升級、惡意貼文誘導多 provider 重試、Cloudflare/GitHub/Groq data retention 條款被忽略；最小緩解是 default disabled、fake-provider tests、secret masking、runtime 前逐 provider privacy gate。
- **接手者視角**：半年後接手者應能從 provider registry、kill switch、manifest diagnostics、runbook 四處知道哪個 provider 是候選、哪個已啟用、為何被跳過。
- **X4-J 自動化建議性工具邊界**：Provider route diagnostics 是工程狀態，不是品質判斷；`provider_failed` 不代表內容不可用，`provider_disabled` 也不代表系統錯誤，人工審核仍需看 manifest / doctor / run logs。
- **X4-K 使用者端審查官 / Patric 型人格**：主公可能看到 `groq` / `cloudflare_ai` 名稱就以為已開始使用免費 provider；報告與 handoff 必須用「候選插槽，預設關閉」反覆標示。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | Provider 被列名後誤接入 daily chain，繞過主公核准 | 中 | 高 | 流程/架構 | default disabled、global kill switch、CI no-call tests、handoff forbidden work |
| R2 | 新 provider call 繞過 P90 budget / cooldown，造成成本或 rate limit 外溢 | 中 | 高 | 邏輯/成本 | budget guard 上移到 router/shared guard，所有 provider call 前檢查 |
| R3 | Secret 或 raw prompt / response 被 log、manifest、artifact 保存 | 中 | 高 | 安全/隱私 | secret masking tests、raw-free diagnostics schema、禁止 raw provider response 入 repo |
| R4 | Provider OpenAI-compatible 只部分相容，JSON schema / response format 失敗 | 高 | 中 | 邏輯/資料 | fake-provider schema normalization tests；真 provider smoke manual-only |
| R5 | 免費額度或條款改變，導致後續 runtime 成本假設錯誤 | 中 | 高 | 成本/時間敏感 | 不承諾免費永久；runtime 前重查官方 pricing / limits；per-provider cap |
| R6 | GitHub Actions 權限面擴大，例如 `models: read` 或新 secrets | 中 | 中 | DevOps/安全 | 只有 GitHub Models runtime 核准後才加；workflow diff 單獨列審 |
| R7 | 多 provider fallback loop 讓 Actions timeout | 中 | 中 | 韌性/效能 | max attempts、timeout、manual-only live smoke，daily default 不變 |
| R8 | 繁中 AOV 領域品質不如 Gemini/local baseline，卻被誤 promotion | 中 | 中 | 品質/i18n | P93 不做 quality promotion；後續需 small sample eval 才能啟用 |

**高風險加權檢查（META4）**：
- 高風險數量：4 項（R1/R2/R3/R5 影響高）。
- 加權分數：10.5 分（高影響 4*2 + 中影響 4*0.625；保守視為 >= 5）。
- 是否 >= 5 須請示主公：是；P93 runtime 不得自動開工，需主公明確核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P93.0 Plan Freeze** | 建立並凍結本檔，固定 disabled-by-default provider abstraction 邊界 | 防止直接接 provider | plan lint / diff check |
| **P93.1 Contract Design** | 定義 provider interface、failure taxonomy、provider capability matrix | adapter 特例散落、fallback 語意混亂 | doc review + fake-provider contract cases |
| **P93.2 Registry + Kill Switches** | 建立 provider registry / factory；global / experimental / per-provider flags 全預設 false | provider 偷跑 | no-env no-call tests |
| **P93.3 Budget Guard Unification** | 把 budget/cooldown guard 上移到所有 provider call 前 | cost/rate limit 外溢 | budget/cooldown matrix tests |
| **P93.4 Diagnostics + Governance** | manifest / doctor / cost governance raw-free 顯示 provider 狀態 | 主公不可見、raw leak | raw-free schema tests + doctor cases |
| **P93.5 Manual-only Smoke Path** | 若主公核准，建立不進 daily default 的手動 smoke | 真 provider 相容性未知 | manual flag + no secrets in repo + small sample |
| **P93.6 Closeout Verification** | focused tests、full pytest、py_compile、doctor/governance、handoff/history 更新 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

---

## 10. 影響檔案清單 ─ STR7

**新增**：
- `docs/PHASE_93_PLAN.md`：P93 FROZEN 計畫書。

**Plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：ACTIVE_BOOTSTRAP 同步 P93 FROZEN。
- `docs/ACTIVE_OPERATION.md`：L2 作戰狀態同步 P93 FROZEN。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P93 FROZEN，但 R-016 仍 Open。
- `TASK_HISTORY.md`：追加 P93 plan freeze 無損紀錄。

**P93 runtime 已新增 / 修改**：
- `analyzer/provider_clients/base.py`：新增 `LLMProviderClient` protocol，固定 `chat` / `batch_chat` / `cache_manager` 相容契約。
- `analyzer/provider_clients/__init__.py`：新增 provider client package。
- `analyzer/provider_budget.py`：新增 shared `ensure_budget_for_provider_call(...)`，供 Gemini / fallback / future adapters 共用。
- `analyzer/provider_router.py`：新增 `ProviderRouter`、`ProviderSlot`、`ProviderRouteBlocked`、provider diagnostics normalize / validate、default client factory；候選 slot 全部 fail-closed。
- `config.py`：新增 `PROVIDER_ROUTER_ENABLED=false`、`EXPERIMENTAL_FREE_PROVIDERS_ENABLED=false`、`AOV_PROVIDER_*_ENABLED=false`、raw-free secret-present flags。
- `analyzer/fallback_llm_client.py`：OpenAI fallback 切換前先過 shared budget guard，並輸出 raw-free provider diagnostics。
- `analyzer/sentiment.py`：預設透過 `build_default_llm_client()`；router disabled 時仍回傳既有 fallback client，daily default 不變。
- `analyzer/run_manifest.py`：manifest `provider.routing` normalize / validate。
- `main.py`：將 analyzer provider diagnostics 寫入 `_meta`，供 manifest 使用。
- `scripts/system_doctor.py`：新增 DOC020 provider routing advisory。
- `scripts/cost_cache_governance.py`：新增 CCG009 provider routing advisory 與表格欄位。
- `docs/OPERATIONS_RUNBOOK.md` / `docs/COST_CACHE_GOVERNANCE_POLICY.md`：新增 DOC020 / CCG009 說明。
- Tests：新增 `tests/test_provider_router.py`，並更新 OpenAI fallback / manifest / doctor / governance tests。

**P93 runtime 明確未修改**：
- `.github/workflows/daily_report.yml`：未新增 `models: read`，未新增 provider smoke workflow。
- `analyzer/gemini_client.py`：未改 Gemini live path；P90 budget guard 保持原行為。

**刪除**：
- 無。

**影響但未直接修改**：
- P90 budget ledger：P93 runtime 會要求 provider call 前 shared guard。
- P91 selection / P92 enrichment replay：不得被 P93 provider abstraction 反向削弱。
- P95 closeout：P93 只處理 provider abstraction，不得關閉 R-016。

---

## 11. Forbidden Work（P93 邊界）

- 不新增或提交任何 provider API key、PAT、Cloudflare token、Groq key。
- 不把 Groq / Cloudflare / GitHub Models 接進 daily default route。
- 不用 provider 候選名義提高 `LLM_DAILY_BUDGET` 或繞過 P90 cooldown。
- 不把 raw prompt、raw response、raw post content、作者資訊寫進 manifest、repo 或 artifact。
- 不加入 GitHub Actions `models: read` 權限，除非主公核准 GitHub Models runtime smoke。
- 不宣稱任一 provider 永久免費；只能說「目前列為零新增付費候選，runtime 前需重查」。
- 不以 OpenAI-compatible 為由省略 schema / response normalization tests。
- 不讓 provider fallback 修補內容品質問題；fallback 只處理 provider failure。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 11.5 P93 Runtime 收官驗證

| 類別 | 指令 / 觀察 | 結果 |
|---|---|---|
| py_compile | `py -m py_compile analyzer\provider_clients\base.py analyzer\provider_budget.py analyzer\provider_router.py analyzer\fallback_llm_client.py analyzer\sentiment.py analyzer\run_manifest.py scripts\system_doctor.py scripts\cost_cache_governance.py config.py main.py` | PASS，無輸出 |
| Focused tests | `py -m pytest -q tests\test_provider_router.py tests\test_openai_fallback.py tests\test_run_manifest.py tests\test_system_doctor.py tests\test_cost_cache_governance.py` | `70 passed in 1.22s` |
| Adjacent regression | `py -m pytest -q tests\test_sentiment_contract.py tests\test_showcase_modes.py tests\test_llm_budget.py` | `22 passed in 0.76s` |
| Full pytest | `py -m pytest -q` | `286 passed in 4.07s` |
| Phase lint | `py scripts\lint_phase_plan.py docs\PHASE_93_PLAN.md` | PASS |
| Handoff truth | `py scripts\check_handoff_truth.py --repo-root .` | `HND000` |
| Governance doctor | `py scripts\governance_doctor.py --repo-root .` | `GOV000` |
| System doctor | `py scripts\system_doctor.py --repo-root . --date 2026-05-22 --profile local --skip-landing` | exit 0；保留既有 advisories：DOC007 `source_dates empty; missing=7`、DOC018 `selected=9 local_only=10 duplicates=8 cap=9 ... topn_overflow=2`、DOC019 `queue_available=True status=pending eligible=2 skipped=8 enriched=0 skipped_reasons={'duplicate_url': 8}` |
| Cost/cache governance | `py scripts\cost_cache_governance.py --repo-root . --date 2026-05-22 --window-days 1 --max-llm-calls 20` | exit 0；保留既有 advisories：CCG007 selection throttle、CCG008 enrichment replay；provider column 為 `-`，表示 P93 default disabled 未啟用 provider route |
| Diff hygiene | `git diff --check` | PASS；僅 Git for Windows LF -> CRLF 工作樹轉換警告，無 whitespace error |

**收官判定**：
- P93 runtime CLOSED。
- Groq / Cloudflare / GitHub Models 仍只是 disabled-by-default slots，沒有 live adapter、沒有 workflow permission、沒有 secret。
- R-016 仍 Open；P93 不關閉跨 Phase 風險。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 新 provider 在未核准情況下被 daily route 呼叫。
- [ ] secret、prompt、response 或 raw post content 進入 repo / manifest / artifact。
- [ ] provider call 繞過 budget / cooldown。
- [ ] provider compatibility 問題造成 production report 退化或 timeout。
- [ ] 主公或接手者誤以為 disabled slot 已啟用。
- [ ] 「免費 provider」成本或條款假設被官方變更推翻。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-93-provider-abstraction.md`。

> **B-NNN / R-NNN 編號規則（B-010）**：若本 Phase 收官時新增 blindspot 或 risk，必須先查下一個全域編號，禁止 Phase 內局部編號。

---

## Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 主要攻擊面是 secret 外洩、raw prompt/response 進 manifest、Actions token 權限升級、惡意貼文觸發多 provider 重試；最小緩解是 default disabled、fake-provider tests、secret masking 與每次 provider call 前 budget guard。 |
| **X4-B 接手者** | 接手者最怕看到三個 provider 名稱卻不知道誰真的啟用；計畫必須用 registry enabled state、kill switch、diagnostics 與 runbook 四個錨點說明狀態。 |
| **X4-C 災難情境** | 情境：workflow 加上 provider secret 後 daily 自動呼叫新 provider 並保存 raw response；緩解：runtime 前 CI no-call tests、raw-free schema、manual-only smoke 與主公核准閘。 |
| **X4-D 5 年後** | 5 年後 provider endpoint、模型名與免費額度大多會變；真正可保存的是 provider interface、fail-closed 思路、測試矩陣與文件化的啟用流程。 |
| **X4-E 終端 vs IDE** | 終端執行要能在沒有任何 provider secret 時通過完整測試；IDE 看到 env var 也不能讓 disabled provider 自動啟用。 |
| **X4-F 跨平台 Win/Mac/Linux** | P93 runtime 測試不得依賴 shell-specific env 寫法；Windows PowerShell、Linux Actions 都要以 config parser 與 monkeypatch env 固定 no-call 行為。 |
| **X4-G 主公個人視角** | 主公要的是零額外付費與可控風險，而不是 AI 自作主張接免費模型；每個啟用點都要提供清楚的取捨、成本與資料外送邊界。 |
| **X4-H 觀測 / 治理** | Manifest、doctor、cost governance 要能區分 disabled、missing secret、budget blocked、provider failed；不然主公只能看到 local-only 卻不知道原因。 |
| **X4-I 主公可見性** | 主公看不到 provider router 是否真的 no-call，所以 P93 runtime 必須加入 no-env no-call tests、diagnostics enabled state、以及 workflow 權限 diff 說明。 |
| **X4-J 自動化建議性工具邊界** | Provider diagnostics 只能說明工程路由狀態，不保證模型品質；任何 provider ranking 或 fallback 建議都需人工覆核，不得自動 promotion。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 文件若只寫 provider 名稱，使用者會誤解成已經啟用；必須在 handoff、plan、runbook 用「候選插槽，預設關閉」描述。 |

> 主公人工裁決錨點：P93 runtime 至少有 4 個裁決點，每點預估 3-5 分鐘：是否凍結 plan、是否批准 runtime、是否允許某 provider live smoke、是否允許 GitHub Actions 權限 / secret 變更。AI 應提供一頁表格列 provider、成本假設、資料留存、權限、測試狀態與預設開關。

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚；結論是否先行 | 觸發；P93 只做 disabled-by-default abstraction，不做 runtime provider call。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；secret、raw response、Actions permission、fallback loop 是核心攻擊面。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；候選 provider 名稱容易被誤解成已啟用，需文案降誤解。 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；官方來源需列於計畫，不把免費額度寫死。 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；P93 只有官方 capability 查證，尚無品質/成本實測數據。 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | N/A；P93 不改前端 UI，只可能在 metadata 文案呈現 provider state。 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；免費額度不當永久承諾，所有 provider 必須 default off 且有 cap。 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；GitHub Actions permissions / secrets / manual-only smoke 是 runtime 前門檻。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 只要 provider 名稱進 registry，日後某個 env var 被設到就可能偷跑呼叫。 | **S 級** | 0 | registry 與 global kill switch 雙重 default false，並以 no-env/no-call tests 固定。 | 入計畫 |
| 2 | OpenAI-compatible 不代表 JSON schema / structured output 完全相容，可能把分析 JSON 弄壞。 | **S 級** | 0 | fake-provider schema normalization tests 必做；真 provider smoke manual-only，不自動 promotion。 | 入計畫 |
| 3 | Cloudflare AI Gateway 可能有 logging/caching；玩家貼文外送前未審 data retention。 | **S 級** | 0 | runtime 前逐 provider privacy gate；diagnostics raw-free；不把 Cloudflare 直接接 daily。 | 入計畫 |
| 4 | GitHub Models 若用 Actions `GITHUB_TOKEN`，workflow permissions 會改變攻擊面。 | A 級 | 0 | `models: read` 僅在 GitHub Models runtime smoke 被核准後加入，並列 workflow diff 審查。 | 入計畫 |
| 5 | 免費額度今天存在不代表下月存在，成本假設可能悄悄腐化。 | A 級 | 0 | X3 設 30 天重查；文件禁止承諾免費永久，per-provider cap 必做。 | 入計畫 |
| 6 | 多 provider fallback 可能形成 cascade loop，造成 timeout 或成本暴衝。 | A 級 | 0 | max attempts / timeout / budget guard 每次 call 前執行；fallback 只處理 provider failure。 | 入計畫 |
| 7 | Provider diagnostics 寫得太多，可能把 prompt、response、作者資訊帶進 repo。 | **S 級** | 0 | manifest 只允許 raw-free fields；tests 禁 `prompt` / `response` / `content` 類欄位。 | 入計畫 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增、不更新 skill。若 runtime 階段臨時涉及 skill，需另開補遺並補 STR9 表。

---

## 12. 凍結戳記

- **凍結人**：主公核准，AI 執行。
- **凍結時間**：2026-05-22 Asia/Taipei。
- **凍結後變更**：禁止；如需修改，新增章節「Phase P93.x 補遺」並引用本檔。
