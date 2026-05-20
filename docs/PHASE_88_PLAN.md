# Phase P88 計畫書 — Deterministic Local Analyzer（凍結版）

> 狀態：FROZEN。此檔只凍結 P88 動工範圍與驗收規則；runtime code 必須等主公另行核准後才能修改。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P88 |
| **Phase 名稱** | Deterministic Local Analyzer |
| **凍結日期** | 2026-05-20 |
| **影響半徑** | 標準 (3-9 檔) — 預計 runtime 實作會碰 `analyzer/`、`main.py` 或 `analyzer/sentiment.py` integration、tests、docs |
| **預估投入時數** | 3-6 小時 |
| **Token budget** | 45K-75K tokens |
| **負責模型** | GPT-5.3-Codex 高；若同一 fallback trace 修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P88 plan | DRAFT_PENDING_PLAN | FROZEN | 計畫可讀、邊界固定、尚不可改 runtime code | `docs/PHASE_88_PLAN.md` 通過 lint 並完成 handoff / risk / history 更新 | AI 建立，主公核准後進 APPROVED |
| Deterministic Local Analyzer runtime | 未建立 | 待 APPROVED | 尚未在 pipeline 產生本地情緒、關鍵字、英雄、平台、事件初判 | 主公明確說「核准 P88 動工」或同義指令 | 主公核准 |

---

## 1. 目標 (Objective)

建立一套不呼叫外部 LLM 的 deterministic local analyzer，能把真實來源貼文轉成 reporter 可用的 baseline analysis：每篇貼文至少產生 sentiment、sentiment_score、keywords、summary、relevance_score、is_hero_focus、detected_heroes、events；每日 summary 至少產生 sentiment_distribution、platform_breakdown、hot_topics、detected_events、hero_stats、wordcloud、top_links，且輸出必須標明 `analysis_source=local_deterministic`。

## 2. 觸發背景 (Why Now)

P86 讓 Gemini model/schedule 降低 429 風險，P87 建立 `quality.core_contract` 判斷真實資料是否足夠，但目前一旦 LLM 失敗，系統仍容易退到 showcase / fallback 文案。P88 要把「有真實資料但 LLM 不可用」這條路補起來，讓後續 P89 可以把它提升成 `production_local_only` 或 `production_llm_partial`，而不是繼續把配額問題當成展示模式。

## 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Rule-based local analyzer + explicit source labels | 新增獨立本地分析模組，透過詞表、英雄 watchlist、平台統計、事件 keyword 產生 baseline；integration 只在 LLM 失敗或主動 local fallback 時啟用 | 可測、零 API 成本、可追溯，壞了容易定位 | 不如 LLM 細膩，需明確標示召回率邊界 | 採用 |
| B. 直接把現有 fallback summary 美化 | 只改 `_generate_fallback_summary()`，讓文案看起來更真 | 改動小 | 仍沒有每篇貼文 analysis，也無法支撐 P89 quality tier | 不採用 |
| C. 接免費 provider 作備援 | Groq / Cloudflare / GitHub Models 補 LLM 分析 | 可能保留 LLM 品質 | 主公已不想增加成本與 provider 依賴；P93 才能 disabled-by-default | 不採用 |

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] 前置 Phase 已收官：P87 CLOSED，manifest / health / doctor 已能顯示 core contract。
- [x] 資料/依賴已備：`SearchResult`、`analyzer.sentiment` schema、`reporter.generator` 期望欄位已可讀。
- [x] 主公已核准計畫凍結：2026-05-20 主公要求「好請繼續」。
- [ ] 主公另行核准 runtime 動工：FROZEN 後仍需主公明確核准才能改 `analyzer/`、`main.py`、`tests/`。
- [x] 風險登記簿無未解新高風險：R-016 仍 Open，但 P88 是既定主線；不新增不可逆操作。

## 4. Exit Criteria（退出條件）

P88 runtime 收官需全部達成：
- [ ] 新增本地分析模組，單篇貼文輸出與 `SINGLE_POST_SCHEMA` / reporter 需要欄位相容。
- [ ] 本地 daily summary 輸出與 `DAILY_SUMMARY_SCHEMA` / reporter 需要欄位相容。
- [ ] LLM 單篇分析失敗時可回退到 local deterministic analyzed posts，不再使用高擬真 showcase mock posts 取代真實貼文。
- [ ] LLM daily summary 失敗時可回退到 local deterministic summary，保留真實 source links / platform / hero 統計。
- [ ] 輸出必須標明 `analysis_source=local_deterministic` 或同等 `_meta` 欄位，且不改 P89 才負責的 quality tier / promotion gate。
- [ ] Focused tests 覆蓋正負中情緒、英雄偵測、關鍵字、事件偵測、平台 breakdown、LLM 429 fallback、非 429 fallback、空資料。
- [ ] `py -m pytest -q` 通過；若有 pre-existing failure，需依 B-008 記錄，不可靜默放行。
- [ ] `py scripts\check_daily_report_health.py --date 2026-05-20 --expected-mode production` 與 `py scripts\system_doctor.py --repo-root . --date 2026-05-20 --profile ci --require-production` 不新增 blocking。
- [ ] `TASK_HISTORY.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md` 更新；R-016 仍不得關閉。

P88 plan-only 凍結需全部達成：
- [x] 新增本檔 `docs/PHASE_88_PLAN.md`。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_88_PLAN.md` 通過。
- [x] handoff / active / risk / history 更新成 P88 FROZEN。
- [x] `git diff --check` 通過。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 3-6 h |
| 預估收益等級 | 高 |
| 收益描述 | 讓有真實資料但 LLM 失敗的日報仍有可用 baseline，降低 429 對每日營運的破壞 |
| ROI 結論 | 值得做；這是 P89 `production_local_only` 的必要前置 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增小型 local analyzer 模組，輸出既有 schema 欄位；integration 只接 LLM fallback 路徑 | 直接塞進 `sentiment.py` 造成巨型函式更難維護 | 優先獨立 `analyzer/local_analyzer.py`，`sentiment.py` 只薄薄接入 |
| **2. 邏輯層 (Logic)** | 情緒詞表、英雄 watchlist、事件 keyword、平台統計分開處理 | 規則誤判被當成 LLM 級結論 | 每筆輸出標 `analysis_source=local_deterministic` 與 reason，不冒充 LLM |
| **4. 測試層 (Testing)** | 單元測試鎖住正/負/中、英雄、事件、平台、fallback path | 規則看似簡單但欄位漂移會破壞 reporter | 先寫 focused tests，再接 integration，再跑 full pytest |
| **10. 安全層 (Security)** | 不新增外部 API、不新增 secret、不 eval 使用者內容 | 原文內容若被當成格式字串或指令執行會有 injection 風險 | 只做純字串比對與聚合，不執行貼文內容 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / 不適用理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | local analyzer 作獨立模組；`SentimentAnalyzer` 負責選擇 LLM 或 local fallback | 把 P88 與 P89 tier gate 混在一起 | P88 只標 source 與 coverage，不新增 tier enum |
| **5. 資料層 (Data)** | 保留原始 post url/platform/source，analysis 只加本地推論欄位 | fallback 產生假連結或假貼文污染資料 | 禁止 showcase mock 替代真實來源；top_links 必來自真實 post |
| **6. 可觀察性層 (Observability)** | `_meta.local_analysis_status`、coverage counts、fallback reason 可被 manifest/doctor 後續讀取 | LLM 失敗後看不出是 local fallback 還是假資料 | 明確寫入 analysis source 與 fallback reason |
| **7. 韌性層 (Resilience)** | LLM 429 / schema failure / non-HTTP exception 都可產 baseline | local fallback 也因欄位缺失崩潰 | 對 title/content/platform/source 都做空值防護 |
| **13. 可維護性層 (Maintainability)** | 詞表常數集中，輸出欄位穩定 | 規則逐步變成無測試的黑盒 | 每新增規則先補 case；不做大型 NLP 引擎 |
| **14. 文件層 (Documentation)** | plan、handoff、history 明確寫 P88 不等於 P89 promotion | 新視窗誤以為 local analyzer 完成後可直接關 R-016 | R-016 保持 Open，下一步仍是 P89-P95 |
| **15. 流程層 (Process)** | FROZEN -> APPROVED -> IN_PROGRESS；runtime 前需主公核准 | plan 凍結後 AI 直接改程式碼 | handoff/active 寫明 FROZEN 與 Allowed Files |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 每日可有數十篇貼文 | 規則分析慢或重複掃描過多 | 單篇 O(n) 字串掃描，避免 heavy NLP dependency |
| **9. UX/A11y 層** | 報告內容會被使用者讀到 | local summary 文案被誤讀成 LLM 深度分析 | summary/recommendation 明確標示本地 deterministic baseline |
| **11. 部署層 (DevOps)** | GitHub Actions daily pipeline | fallback path 在 CI Linux 與本機 Windows 行為不同 | tests 不依賴平台路徑，避免 locale-sensitive parsing |
| **12. 成本層 (Cost)** | LLM 429 / quota 主線 | fallback 又呼叫外部 API 造成成本回流 | P88 嚴禁外部 API，零額外付費 |
| **16. 隱私/合規層 (Privacy)** | 第三方貼文內容進本地分析 | 將原文過度複製到 summary 或 logs | 摘要截斷、top_links 保留 url/title，不新增 raw dump |
| **17. i18n/在地化層** | AOV 台灣語境與可能中英混合貼文 | 只支援中文詞表導致英文貼文全 neutral | 先標明中文/台灣語境 baseline；英文只做保守 neutral |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已規劃 Testing 層。
- [x] 動 Architecture 層 → 已規劃 Documentation 層。
- [x] 動 Data 層 → 已規劃 Maintainability 層。
- [x] 動 Security 層 → 已規劃 Testing 層。
- [x] 動 Performance 層 → 已規劃 Observability 層。

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_88_PLAN.md` | 可逆 | 已核准繼續 P88 plan |
| 更新 handoff / active / risk / history | 可逆 | 已核准繼續 P88 plan |
| P88 runtime 實作 commit | 可逆 | 尚未核准，需主公下一步確認 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：local fallback 會多出 status / reason，這是定位訊號。
- [x] 中間檔產出：analysis json 可能新增 `analysis_source` 與 local coverage 欄位。
- [x] 系統狀態變更：P88 不改首頁 promotion；P89 才決定 local-only 是否可上首頁。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-20。
- 本計畫過期日期：2026-06-20；若 P89 已先改 tier / promotion，P88 需重審 integration path。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：這份計畫要讓主公看到「LLM 掛了也還有真實 baseline」，但不假裝 baseline 等於深度 LLM 分析。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面主要是內容注入、假資料污染與 reason spoofing；最小緩解是純字串分析、不執行內容、不讓貼文決定 mode/tier。
- **接手者視角**：半年後接手者需要從單一 local analyzer 模組找到規則、詞表、輸出欄位與測試，不必在 `sentiment.py` 追一堆 fallback 分支。
- **X4-J 自動化建議性工具邊界**：本地 analyzer 是啟發式規則工具，召回率僅供 baseline，人工與後續 LLM enrichment 仍必要。
- **X4-K 使用者端審查官 / Patric 型人格**：報告文案不能說「深度 AI 洞察」卻只靠詞表；UI/metadata 要避免承諾 X 但交付 Y。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | local analyzer 誤判情緒，被主公當成 LLM 級分析 | 中 | 高 | 業務 | 明確標 `analysis_source=local_deterministic`，summary 文案保守 |
| R2 | fallback integration 改壞現有 production LLM 成功路徑 | 中 | 高 | 代碼 | focused tests 覆蓋 LLM success path 與 fallback path |
| R3 | P88 越界改 quality tier / promotion gate | 中 | 高 | 流程 | Forbidden Work 明列 P89 才改 tier/gate |
| R4 | 英雄/事件詞表太窄，漏掉大量真實討論 | 高 | 中 | 業務 | 先列已知 false-negative；P92 replay/LLM enrichment 補深度 |
| R5 | local summary 產生過度複製原文造成報告冗長 | 中 | 中 | 隱私/UX | summary 截斷，top_links 只帶必要 title/url/platform |

**高風險加權檢查（META4）**：
- 高風險數量：3 項（R1/R2/R3 影響高）。
- 加權分數：5.0 分。
- 是否 ≥ 5 須請示主公：是；因此 P88 runtime 前需主公明確核准，本檔只凍結計畫。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P88.0 Plan Freeze** | 建立本檔，更新 handoff / active / risk / history | 防止 P88 直接混入 P89/P90 | lint plan / handoff truth / governance doctor |
| **P88.1 Local Post Analyzer** | 新增單篇 deterministic analysis：sentiment、keywords、heroes、events、summary | 無 LLM 時每篇貼文沒有 baseline | focused unit tests |
| **P88.2 Local Daily Summary** | 聚合 analyzed posts 成 reporter-compatible summary | LLM summary 掛掉後報告沒有真實統計 | schema compatibility tests |
| **P88.3 SentimentAnalyzer Fallback Integration** | LLM 失敗時走 local baseline，LLM 成功時不影響既有路徑 | integration 改壞 production path | async tests 覆蓋 success / 429 / exception |
| **P88.4 Closeout** | full pytest、health、doctor、handoff truth、governance doctor，更新歷史 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_88_PLAN.md`：本 Phase 凍結計畫。

**P88 plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：Current Phase 改 P88 FROZEN。
- `docs/ACTIVE_OPERATION.md`：短版狀態同步。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P88 plan frozen。
- `TASK_HISTORY.md`：追加 P88 plan freeze 物理紀錄。

**P88 runtime 核准後預計修改**：
- `analyzer/local_analyzer.py`：新增 deterministic local analyzer。
- `analyzer/sentiment.py`：接入 LLM failure fallback，不改 success path。
- `tests/test_local_analyzer.py`：本地分析 focused tests。
- `tests/test_sentiment_contract.py` 或新增 integration tests：LLM success / fallback path。
- 可能修改 `main.py`：只在需要傳遞 `_meta.local_analysis_status` 時做最小接線。
- 可能修改 `docs/OPERATIONS_RUNBOOK.md` 或 doctor：若新增 issue code 才補 runbook。

**刪除**：
- 無。

**影響但未直接修改**：
- `reporter/generator.py`：P88 應維持既有欄位相容，除非 runtime 發現 metadata 必須標示 local source，才另行明列。
- P89 / P90：依賴 P88 baseline，但不得混入 P88。

---

## 11. Forbidden Work（P88 邊界）

- 不加 `OPENAI_API_KEY`，不要求主公花 OpenAI API 錢。
- 不接 Groq / Cloudflare / GitHub Models 等免費 provider；P93 才能 disabled-by-default 設計。
- 不改 Gemini model list 或 schedule；P86 已 CLOSED。
- 不改 `production_full` / `production_local_only` 等 quality tier enum；P89 才處理。
- 不改 landing promotion gate；P89 才處理。
- 不做 LLM budget ledger / cooldown；P90 才處理。
- 不做 cache/dedupe/top-N 策略；P91 才處理。
- 不做 enrichment queue / replay；P92 才處理。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 主公中途否決 local analyzer 欄位設計並要求重來。
- [ ] focused tests 顯示 reporter 既有欄位與 local summary 不相容。
- [ ] LLM success path 被 P88 fallback integration 意外改壞。
- [ ] 發生「我以為 local baseline 可以當 LLM 深度分析，結果不是」的判斷錯誤。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-88-deterministic-local-analyzer.md`。

---

## 13. Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 主要攻擊面是貼文內容注入、假平台資料污染與 fallback reason spoofing；緩解是不執行內容、不信任內容決定 tier，只做本地聚合。 |
| **X4-B 接手者** | 接手者需要看到 local analyzer 是獨立模組，輸出欄位與測試都集中，不必在主流程裡追散落規則。 |
| **X4-C 災難情境** | 情境：LLM 掛掉後 local baseline 被當作完整 production 深度分析；緩解：P88 只標 source，P89 才決定 quality tier。 |
| **X4-D 5 年後** | 五年後 LLM provider 可能全換，但本地 baseline 仍能保留基本報告能力，所以規則不應綁死 Gemini 或 OpenAI。 |
| **X4-E 終端 vs IDE** | 終端測試必須能看出 fallback path 與 source label，不應只靠 IDE 打開報告人工判斷。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows 與 Linux 都會跑同一批字串規則，需避免依賴平台路徑、locale 或 shell-specific 行為。 |
| **X4-G 主公個人視角** | 主公要的是 API 不夠時仍有真實 baseline，而不是再看到高級展示假資料；P88 文案必須白話標示來源。 |
| **X4-H 觀測 / 治理** | P88 若只產生分析不標示 local status，doctor/manifest 後續仍難定位；需留下 `_meta` 或 contract 訊號。 |
| **X4-I 主公可見性** | 主公看不到的是 P88 不會直接讓 local-only 上首頁；handoff 必須明寫 promotion 要等 P89。 |
| **X4-J 自動化建議性工具邊界** | 本地 analyzer 是規則式啟發工具，召回率與語意深度有限，人工覆核與後續 LLM enrichment 仍必要。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 最容易誤解的是報告看起來很完整但其實只靠 deterministic baseline；需避免「深度 AI」類誇大字眼。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P88 只做 local baseline，P89/P90 不混入 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；不新增 secrets，不執行貼文內容 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；必須標明 local deterministic 不是 LLM 深度洞察 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase 需更新 handoff、active、history |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；本地分析必須分清 counts、score、rule reason |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 條件觸發；P88 若改 metadata 文案，需避免誤導使用者 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P88 零外部 API，降低 429 導致的營運成本 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；P88 fallback 需在 GitHub Actions Linux 與本機 Windows 都通過 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 規則情緒分析很粗糙，若直接當 production 深度洞察會誤導主公。 | **S** | 0 | P88 只標 source 與 baseline，不改 quality tier；P89 才決定 local-only 呈現。 | 入計畫範圍：P88.1 / Forbidden Work |
| 2 | fallback integration 可能改壞 LLM 成功路徑，讓正常 production 反而退化。 | **S** | 0 | 必測 LLM success path；fallback 只在 exception / quota / invalid contract 下啟動。 | 入計畫範圍：P88.3 tests |
| 3 | local analyzer 可能用假 mock summary，繼續污染真實報告。 | A | 0 | P88 禁止 showcase mock 替代真實貼文；top_links 必來自原始 source。 | 入計畫範圍：P88.2 |
| 4 | 英雄詞表漏掉別名、簡繁、英文名時，hero_stats 可能低估熱度。 | A | 0 | 明文列 false-negative 邊界；先鎖 watchlist，後續再擴詞表。 | 入計畫範圍：P88.1 tests |
| 5 | P88 若順手改 promotion gate，會和 P89 職責重疊。 | A | 0 | Forbidden Work 明列 P89 才改 tier / gate，handoff 也要防偏航。 | 入計畫範圍：流程層 |
| 6 | 本地 summary 若過度複製原文，會讓報告冗長且增加隱私風險。 | A | 0 | 摘要需截斷，top_links 只保留必要 title/url/platform。 | 入計畫範圍：資料/隱私層 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增或修改 skill，STR9 不觸發；若後續臨時新增 skill，必須另開 Phase 或修訂計畫並重新凍結。
