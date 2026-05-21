# Phase P89 計畫書 — Quality Tier / Promotion Gate（收官版）

> 狀態：CLOSED。P89 runtime 已依本計畫完成 quality tier contract、promotion gate、metadata、health/doctor 與 focused tests；R-016 仍 Open，後續續行 P90-P95。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P89 |
| **Phase 名稱** | Quality Tier / Promotion Gate |
| **凍結日期** | 2026-05-20 |
| **影響半徑** | 標準 (3-9 檔) — runtime 預計會碰 `main.py`、`analyzer/run_manifest.py`、health/doctor scripts、tests、docs |
| **預估投入時數** | 3-6 小時 |
| **Token budget** | 40K-70K tokens |
| **負責模型** | GPT-5.3-Codex 高；若同一 gate/tier trace 修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P89 plan | FROZEN | CLOSED | 計畫邊界已固定並完成 runtime 收官 | runtime code / tests / health / doctor / docs 已驗證 | 主公核准，AI 執行 |
| Promotion gate runtime | 待 APPROVED | CLOSED | gate 已從單純 `mode == production` 升級為 publishable quality tier + health checks | `production_local_only` 可在 core/local baseline pass 時 promotion；manual/error 不可 promotion | AI 執行 |
| Quality tier contract | 待 APPROVED | CLOSED | manifest/report metadata 已產生 `quality.tier` / `analysis_source` / `llm_coverage` | focused tests + full pytest 通過 | AI 執行 |

---

## 1. 目標 (Objective)

建立品質分級與 promotion gate 規則，讓每日報告從單一 `mode` 判斷升級成 `quality_tier + publish_eligible` 判斷：LLM 滿配時是 `production_full`，LLM 部分失敗但有真實資料與本地 baseline 時是 `production_llm_partial` 或 `production_local_only`，手動展示與真正錯誤則不允許上首頁。

## 2. 觸發背景 (Why Now)

P87 已讓 manifest 能判斷 report core contract，P88 已讓 LLM 429 / provider exception 時仍可從真實貼文產生 `analysis_source=local_deterministic` baseline。現在最大的錯誤仍在 promotion 判斷：`main.py` 目前把 `_quota_error` 直接轉成 `mode=showcase_forced`，`evaluate_publish_gate()` 與 `should_promote` 只接受 `mode == production`。P89 要把「資料真實且本地 baseline 足夠」從 showcase/錯誤語意中分離出來，避免 429 把整份真實報告降成不可發布狀態。

## 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. 新增 `quality_tier`，保留 `mode` 作相容欄位 | `mode` 仍可為 `production/showcase/...`，新增 `quality_tier` 決定 publish gate；manifest/metadata/doctor 同步讀 tier | 相容舊報告；可逐步導入；P89 不必大改所有舊 code | 需要短期維持兩個欄位，文件要清楚 | 採用 |
| B. 直接把 `showcase_forced` 改成 `production_local_only` mode | `ALLOWED_MODES` 擴充 tier 字串，promotion 直接看 mode | 改動直覺 | 舊 `mode` 語意混亂，health check / report metadata / tests 牽動較大 | 不採用 |
| C. 只放寬 `should_promote` 讓 quota report 可上首頁 | 最小改動 | 會把品質原因藏在 gate 裡，doctor/manifest 難定位 | 不採用 |

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] 前置 Phase 已收官：P87 Report Core Contract CLOSED、P88 Deterministic Local Analyzer CLOSED。
- [x] 資料/依賴已備：`quality.core_contract`、P88 `analysis_source=local_deterministic`、`provider.quota_error` 已可被 runtime 取得。
- [x] 主公已核准計畫凍結：2026-05-20 主公要求「開始下一步」。
- [x] 主公另行核准 runtime 動工：主公已明確要求「推 20b9a78 核准 P89 runtime 動工」與「現在我們做到哪？請接著繼續做」。
- [x] 風險登記簿無未解新高風險：R-016 仍 Open，但 P89 是既定主線；不新增不可逆操作。

## 4. Exit Criteria（退出條件）

P89 runtime 收官需全部達成：
- [x] 新增 machine-readable `quality_tier`，支援 `production_full`、`production_llm_partial`、`production_local_only`、`showcase_manual`、`error_fallback`。
- [x] `quality_tier` 判定規則同時參考 P87 `quality.core_contract`、P88 local baseline source、LLM coverage/quota diagnostics、manual showcase flag。
- [x] `production_local_only` 在 source/core contract PASS 且 local baseline 完整時可被 promotion gate 接受；`showcase_manual` 與 `error_fallback` 不可 promotion。
- [x] Manifest 寫入 `quality.tier`、`quality.analysis_source`、`quality.llm_coverage`，並維持舊 `mode` 相容。
- [x] Report metadata comment 可顯示 quality tier / analysis source / LLM coverage，不誤導為 full LLM report。
- [x] Health check / system doctor 可辨識 tier，不再把 quota-limited local-only 誤判成普通程式壞；blocking 與 advisory 分級明確。
- [x] Focused tests 覆蓋 full LLM、partial LLM、local-only quota、manual showcase、error fallback、core contract fail、shadow/blocking gate。
- [x] `py -m pytest -q` 通過：240 passed。
- [x] `py scripts\check_daily_report_health.py --date 2026-05-20 --expected-mode production` 與 `py scripts\system_doctor.py --repo-root . --date 2026-05-20 --profile ci --require-production` 不新增 blocking。
- [x] `TASK_HISTORY.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md` 更新；R-016 仍不得關閉。

P89 plan-only 凍結需全部達成：
- [x] 新增本檔 `docs/PHASE_89_PLAN.md`。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_89_PLAN.md` 通過。
- [x] handoff / active / risk / history 更新成 P89 FROZEN。
- [x] `git diff --check` 通過。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 3-6 h |
| 預估收益等級 | 高 |
| 收益描述 | 把 429 / quota limit 從「整份報告不可發布」改成「品質分級降級但真實資料仍可發布」，直接降低 R-016 反覆出現機率 |
| ROI 結論 | 值得做；這是 P85 zero-cost 路線的核心 gate 轉折點 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增小型 quality tier 判定函式，避免把條件散落在 `main.py` 多處 | gate 條件散亂後難以定位 why not promoted | 將 tier decision 集中成可測函式，`main.py` 只接結果 |
| **2. 邏輯層 (Logic)** | `publish_eligible` 從 `mode == production` 改為 tier + core contract + gate reasons | local-only 被過度放寬，上首頁但缺真實資料 | 必須要求 core contract pass，manual showcase / error fallback 永不 promotion |
| **4. 測試層 (Testing)** | focused tests 鎖住 tier matrix、manifest validation、health/doctor gate | 改 gate 很容易把舊 production 或 showcase 行為改壞 | 先補 matrix tests，再動 integration，最後 full pytest |
| **10. 安全層 (Security)** | 不新增 secrets/provider，不讓貼文內容決定 tier；tier 只讀系統 metadata | prompt/content injection 偽造 `quality_tier` | tier 由 runtime/manifest code 計算，不信任貼文原文欄位 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | quality tier 作為 mode 之外的獨立 contract，避免混淆舊 mode 語意 | `mode` 與 `quality_tier` 雙軌短期造成誤讀 | 文件與 tests 明確：mode 相容、tier 決策 |
| **5. 資料層 (Data)** | manifest 記錄 tier、analysis source、LLM coverage、core contract | 舊 manifest 缺 tier 導致 doctor 誤判 | 舊 manifest 顯示 unknown/advisory，不回填除非另開 Phase |
| **6. 可觀察性層 (Observability)** | doctor / health 顯示 tier decision 與 gate reasons | 主公只看到 Actions 綠勾卻不知道 local-only | health table 與 manifest 都印 tier / reason |
| **7. 韌性層 (Resilience)** | 429 只降成 `production_local_only`，不把整份報告降成 showcase | local analyzer 失敗時仍錯誤 promotion | local baseline 缺失或 core fail 時進 `error_fallback` |
| **13. 可維護性層 (Maintainability)** | tier enum / allowed values 集中，測試 matrix 對齊 | 後續 P90-P95 需要再接 budget/replay，若 enum 散亂會變難 | P89 runtime 必須留下單一 helper 與文件錨點 |
| **14. 文件層 (Documentation)** | handoff / active / history 明確寫 P89 不等於 R-016 closeout | 新視窗以為可關 R-016 | R-016 保持 Open，P90-P95 仍待做 |
| **15. 流程層 (Process)** | FROZEN -> APPROVED -> IN_PROGRESS；runtime 前需主公核准 | plan 凍結後 AI 直接改 promotion gate | handoff/active 寫明 FROZEN 與 Allowed Files |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 每日 pipeline 必跑 gate | tier decision 必須 O(1) / O(n small)，不可掃大報告 HTML | gate 只讀 metadata/manifest/check 結果，不 parse 大量 raw |
| **9. UX/A11y 層** | 報告 metadata / 可能 UI 顯示 tier | `production_local_only` 被使用者看成壞掉 | 用「真實資料 + 本地 baseline，LLM 深讀待補」而非恐嚇字眼 |
| **11. 部署層 (DevOps)** | GitHub Actions daily promotion | 改 gate 後首頁 promotion 行為改變 | shadow/blocking gate tests；runtime 後需 Actions 實跑證據 |
| **12. 成本層 (Cost)** | LLM quota / zero-cost 主線 | gate 放寬後可能掩蓋 LLM coverage 下降 | tier 必須顯示 coverage，P90 再做 budget ledger |
| **16. 隱私/合規層 (Privacy)** | quality metadata 可能包含 source info | 把 raw prompt/raw post 放進 manifest 或 metadata | manifest 只記 count/status/source hash，不寫 raw content |
| **17. i18n/在地化層** | 報告語境為台灣，時區 Asia/Taipei | tier date 與 Actions UTC 日期錯位 | 沿用 run_context / run_date_taipei，不新增手寫日期邏輯 |

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
| 新增 `docs/PHASE_89_PLAN.md` | 可逆 | 已核准開始下一步 plan |
| 更新 handoff / active / risk / history | 可逆 | 已核准開始下一步 plan |
| P89 runtime 實作 commit | 可逆 | 已核准並完成本地驗證 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：promotion skip reason 會因 tier 改寫，需讓 log 更白話。
- [x] 中間檔產出：manifest 會新增 `quality.tier` / coverage 欄位。
- [x] 系統狀態變更：P89 後首頁可能接受 `production_local_only`，但必須標示不是 full LLM。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-20。
- 本計畫過期日期：2026-06-20；若 P90 先改 budget/cooldown 或 reporter metadata 先改版，P89 runtime 需重審 gate 接線。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：這份計畫要解的不是「讓所有報告都說 production」，而是讓主公一眼知道 full/partial/local-only 的品質差異。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面是貼文內容或 provider error message 試圖污染 tier；最小緩解是 tier 只由內部 contract 與 metadata 計算，不信任原文。
- **接手者視角**：半年後接手者需要看到 tier enum、promotion rule、doctor code 在同一套測試矩陣裡，不必猜 `showcase_forced` 為何不可發布。
- **X4-J 自動化建議性工具邊界**：tier 是規則判定，不是人類品質審稿；local-only 代表可用 baseline，不代表語意洞察完整。
- **X4-K 使用者端審查官 / Patric 型人格**：最容易誤解的是 `production_local_only` 看起來像偷工減料；報告/metadata 需說明它是真實資料、LLM 深讀覆蓋較低。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | local-only 被過度 promotion，讓低品質或缺資料報告上首頁 | 中 | 高 | 邏輯 | `production_local_only` 必須同時通過 core contract 與 local baseline 完整性 |
| R2 | `mode` 與 `quality_tier` 雙欄位造成接手者混淆 | 中 | 中 | 文件/維護 | 文件寫明 mode 是相容欄位，tier 是 P89 後決策欄位 |
| R3 | health check / doctor 舊測試因 tier 欄位變更破掉 | 中 | 中 | 測試 | 先補兼容測試，舊 manifest 缺 tier 僅 advisory |
| R4 | UI/metadata 把 local-only 說得太像 full LLM | 中 | 高 | UX/業務 | 文案禁用「深度 AI 完整分析」；顯示 analysis source / coverage |
| R5 | blocking gate 一改就讓每日 report 不 promotion | 低 | 高 | DevOps | 先保留 `PUBLISH_GATE_MODE=shadow`，runtime 後用 workflow_dispatch 實跑 |
| R6 | R-016 被誤關 | 中 | 高 | 流程 | P89 只關 quality gate 子問題；R-016 要 P95 才能 closeout |

**高風險加權檢查（META4）**：
- 高風險數量：4 項（R1/R4/R5/R6 影響高）。
- 加權分數：6.5 分。
- 是否 >= 5 須請示主公：是；主公已核准 runtime 動工，收官時以 focused tests + full pytest + health/doctor 驗證。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P89.0 Plan Freeze** | 建立本檔，更新 handoff / active / risk / history | 防止直接改 promotion gate | lint plan / handoff truth / governance doctor |
| **P89.1 Tier Contract Helper** | 新增 quality tier enum 與判定 helper | gate 條件散落 | focused unit tests |
| **P89.2 Manifest + Metadata Integration** | manifest/report metadata 寫入 tier/source/coverage | 主公看不到品質差異 | manifest validation + metadata tests |
| **P89.3 Promotion Gate Integration** | promotion 從 `mode == production` 改成 tier eligibility | 429 -> showcase_forced | gate matrix tests |
| **P89.4 Doctor / Health Classification** | health/doctor 顯示 tier，不誤判 quota local-only | 定位不清 | script tests |
| **P89.5 Closeout** | full pytest、health、doctor、handoff truth、governance doctor，更新歷史 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

狀態：P89.0-P89.5 均已完成；R-016 仍 Open，下一步續行 P90 budget ledger / cooldown plan。

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_89_PLAN.md`：本 Phase 凍結計畫。

**P89 plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：Current Phase 改 P89 FROZEN。
- `docs/ACTIVE_OPERATION.md`：短版狀態同步。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P89 plan frozen。
- `TASK_HISTORY.md`：追加 P89 plan freeze 物理紀錄。

**P89 runtime 核准後預計修改**：
- `main.py`：接入 quality tier decision 與 promotion gate，不改 LLM budget ledger。
- `analyzer/run_manifest.py`：新增 tier contract / validation / manifest 欄位。
- `scripts/check_daily_report_health.py`：health check 顯示 tier / local-only eligibility。
- `scripts/system_doctor.py`：doctor issue reclassification，不把 quota local-only 當 blocking。
- `reporter/generator.py` 或 metadata 相關位置：報告 metadata comment 補 tier/source/coverage。
- `tests/test_run_manifest.py`、`tests/test_daily_report_health.py`、`tests/test_system_doctor.py`、新增或更新 gate matrix tests。

**刪除**：
- 無。

**影響但未直接修改**：
- `.github/workflows/daily_report.yml`：P89 runtime 後需 Actions 實跑，但本 Phase 不改 workflow。
- P90/P91/P92：依賴 P89 tier，但不得混入 P89。

---

## 11. Forbidden Work（P89 邊界）

- 不加 `OPENAI_API_KEY`，不要求主公花 OpenAI API 錢。
- 不接 Groq / Cloudflare / GitHub Models 等免費 provider；P93 才能 disabled-by-default 設計。
- 不改 Gemini model list 或 schedule；P86 已 CLOSED。
- 不做 LLM budget ledger / cooldown；P90 才處理。
- 不做 cache/dedupe/top-N 策略；P91 才處理。
- 不做 enrichment queue / replay；P92 才處理。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] `production_local_only` 被 promotion 但缺 core contract 或 local baseline。
- [ ] P89 runtime 讓原本 `production_full` 的 Actions report 變成不 promotion。
- [ ] 主公或接手者誤解 `quality_tier` 與 `mode` 的差異。
- [ ] doctor/health 對同一份 manifest 給出互相矛盾的判定。
- [ ] 有任何「我以為 429 可發布，結果其實是資料缺失」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-89-quality-tier-promotion-gate.md`。

---

## 13. Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 主要攻擊面是貼文內容、provider error 或 malformed manifest 試圖污染 tier；最小緩解是 tier 僅由內部 contract/helper 計算並驗證 allowed enum。 |
| **X4-B 接手者** | 接手者需要從 `quality_tier` helper、manifest schema、doctor/health tests 三處快速定位 promotion 原因，不該回去猜 `showcase_forced` 語意。 |
| **X4-C 災難情境** | 情境：local-only 報告缺資料卻上首頁；緩解：production_local_only 必須同時通過 core contract 與 local baseline 完整性。 |
| **X4-D 5 年後** | 五年後 provider 可能全換，但 tier contract 仍應保留：真實資料、分析覆蓋率、發布資格三件事分開判定。 |
| **X4-E 終端 vs IDE** | 終端測試必須印出 tier matrix 與 gate reasons，不能只靠打開 HTML 人工判斷 promotion 是否合理。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows 本機與 Linux Actions 都會跑相同 manifest / health / doctor tests，需避免路徑分隔符或 timezone 手寫差異。 |
| **X4-G 主公個人視角** | 主公要的是 API 不夠時仍有真實報告，而不是再看到假展示；tier 文案必須白話說明 full/partial/local-only。 |
| **X4-H 觀測 / 治理** | 若 manifest 只寫 mode 不寫 tier，R-016 仍難定位；P89 必須讓 doctor/health 都能看到 tier 與 reason。 |
| **X4-I 主公可見性** | 主公看不到的是 promotion gate 可能接受 local-only；handoff 和 report metadata 必須攤開「為何可發布」。 |
| **X4-J 自動化建議性工具邊界** | tier 是啟發式/規則式 gate，不是人類品質審稿；false negative 包含新平台欄位缺失、local analyzer 漏英雄別名、舊 manifest 無 tier。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者可能以為 local-only 是壞掉或偷工；報告需避免承諾 full LLM insight，改說真實資料 baseline 與 LLM 覆蓋率。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P89 只做 quality tier / gate，不混 P90 budget |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；不新增 secrets，不信任 raw post 決定 tier |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；tier 文案需避免 local-only 被誤認為 full LLM |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase 需更新 handoff、active、history |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；tier 必須清楚區分 source count、LLM coverage、publish eligibility |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 條件觸發；若 runtime 改報告 metadata/UI，要避免干擾主要內容 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P89 零新增 API 成本，避免把 429 修法導回付費 fallback |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；promotion gate 改動需在 shadow 模式與 Actions 實跑驗證 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | local-only 一旦可 promotion，可能把來源不足的報告推到首頁。 | **S** | 0 | 必須要求 P87 core contract pass，且 local baseline 欄位完整。 | 入計畫範圍：P89.1/P89.3 tests |
| 2 | `mode` 與 `quality_tier` 雙軌會讓 doctor/health 給出互相矛盾判定。 | **S** | 0 | P89 runtime 要把 tier 作決策 source，mode 僅相容；doctor/health 同讀 tier。 | 入計畫範圍：P89.2/P89.4 |
| 3 | 429 仍可能被舊 code 設成 `showcase_forced`，導致 tier 沒機會生效。 | A | 0 | P89 需調整 `_mode` 與 tier mapping，但不碰 P90 budget。 | 入計畫範圍：P89.3 |
| 4 | 報告文案若把 local-only 說成 AI 深度分析，主公會被誤導。 | A | 0 | metadata / recommendation 必須顯示 analysis source 與 LLM coverage。 | 入計畫範圍：P89.2 |
| 5 | 舊 manifest 沒 tier，system doctor 可能突然多很多 warning。 | B | 0 | 舊 manifest 缺 tier 只 advisory，不回填舊資料，避免 scope 爆炸。 | 入計畫範圍：P89.4 |
| 6 | gate 改動若直接 blocking，可能讓 Actions 產出報告但首頁不更新。 | A | 0 | 保留 `PUBLISH_GATE_MODE=shadow`，runtime 收官要用 workflow_dispatch 實跑證據。 | 入計畫範圍：P89.5 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增或修改 skill，STR9 不觸發；若後續臨時新增 skill，必須另開 Phase 或修訂計畫並重新凍結。

---

## 15. Plan Freeze 實跑證據（2026-05-20）

| 指令 | 結果 |
|---|---|
| `py scripts\lint_phase_plan.py docs\PHASE_89_PLAN.md` | PASS：通過 Pre-flight 體檢（M1 + M2） |
| `py scripts\check_handoff_truth.py --repo-root .` | PASS：HND000 active bootstrap truth verified |
| `py scripts\governance_doctor.py --repo-root .` | PASS：GOV000 runbook and risk registry governance verified |
| `git diff --check` | PASS；僅 CRLF warning |

## 16. Runtime 收官證據（2026-05-21）

| 指令 | 結果 |
|---|---|
| `py -m pytest -q tests/test_run_manifest.py tests/test_daily_report_health.py tests/test_system_doctor.py tests/test_slo_checker.py tests/test_publish_gate.py` | PASS：57 passed |
| `py -m pytest -q` | PASS：240 passed |
| `py scripts\check_daily_report_health.py --date 2026-05-20 --expected-mode production` | PASS：無 FAIL；舊產物缺 `quality_tier` 僅 WARN |
| `py scripts\system_doctor.py --repo-root . --date 2026-05-20 --profile ci --require-production` | PASS：無 blocking / degraded；僅 DOC007、DOC016 advisory |
| `py scripts\governance_doctor.py --repo-root .` | PASS：GOV000 |
| `py scripts\lint_phase_plan.py docs\PHASE_89_PLAN.md` | PASS：通過 Pre-flight 體檢（M1 + M2） |
| `git diff --check` | PASS；僅 CRLF warning |

### 收官後下一步

P89 runtime 已收官。下一步是建立 / 凍結 P90 budget ledger / cooldown plan；P90 未核准前不得改 budget runtime。R-016 仍 Open，不得在 P89 收官時關閉。
