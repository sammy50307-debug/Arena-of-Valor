# Phase P92 計畫書 — Enrichment Replay / Local-only 補深讀（收官版）

> 狀態：CLOSED。主公已於 2026-05-22 核准 P92 runtime 動工；本 Phase 已完成 artifact-backed enrichment queue、budget-aware manual replay、raw-free manifest `enrichment` snapshot、Actions artifact、DOC019 / CCG008。R-016 仍 Open，不得因 P92 收官而關閉。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P92 |
| **Phase 名稱** | Enrichment Replay / Local-only 補深讀 |
| **凍結日期** | 2026-05-22 |
| **收官日期** | 2026-05-22 |
| **影響半徑** | 重大 (10+ 檔) - runtime 新增 enrichment queue helper / replay CLI，並接入 manifest / workflow artifact / governance scripts / docs / tests |
| **預估投入時數** | 5-8 小時 |
| **Token budget** | 55K-85K tokens |
| **負責模型** | GPT-5.3-Codex 高；若同一 replay/merge trace 修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P92 plan | DRAFT | FROZEN | 計畫邊界已固定，但 runtime 尚不可施工 | 本檔建立並通過 plan lint | 主公核准，AI 執行 |
| P92 runtime | PENDING_APPROVAL | CLOSED | 補深讀 runtime 已完成本地驗證 | 主公已核准 runtime；queue / replay / manifest / workflow / governance / tests 已落地 | 主公核准，AI 執行 |
| R-016 | Open | Open | R-016 仍是跨 Phase 風險；P92 只處理 local-only 補深讀子問題 | P92 plan 凍結不得直接關閉 R-016，需等 P95 closeout | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

建立一條 raw-safe、budget-aware 的 enrichment replay 設計：讓 P91 selection 產生的 local-only 貼文，在有剩餘 LLM budget 時可被後補深讀，並以 raw-free manifest snapshot 說明 eligible / skipped / enriched 數量；不得增加 OpenAI API 成本，不得接新 provider，不得取消 P91 節流。

## 2. 觸發背景 (Why Now)

P91 已在 2026-05-22 GitHub Actions 實跑成功：`llm_calls` 從 pre-P91 的 28 降至 6，manifest 已出現 `selection` snapshot，`total_input_posts=19`、`unique_posts=12`、`duplicate_posts=7`、`local_only_posts=7`。這證明節流有效，但也揭露下一個品質問題：報告現在可能是 `analysis_source=mixed` / `llm_coverage=partial`，部分貼文只走 P88 local deterministic baseline。P92 要補的是「何時、如何、用哪些證據補深讀」，而不是把 P91 的節流拿掉。

## 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Artifact-backed enrichment queue + replay CLI | runtime 產生 local-only enrichment queue；raw content 僅保留於本機 / Actions artifact；manifest 只寫 raw-free snapshot；replay CLI 依 budget 後補深讀 | 可追溯、可測、可 no-op；不 commit raw；不新增 provider 成本 | 需新增 queue schema、artifact retention、merge 規則 | 採用 |
| B. 直接把 raw / analysis commit 進 repo | 後續任何日期都能重建與補跑 | 補跑最容易 | 第三方內容擴散、repo 膨脹、隱私與合規風險高 | 不採用 |
| C. 調高 `LLM_ANALYSIS_TOP_N` 或 `LLM_DAILY_BUDGET` | 讓更多貼文在 daily run 當下被 LLM 深讀 | 改動少 | 反向削弱 P91 成果，可能讓 calls 再爆量 | 不採用 |
| D. 接 Groq / Cloudflare / GitHub Models 免費 provider | 用額外 provider 補深讀 | 潛在免費額度增加 | 屬 P93 provider abstraction；安全、品質、secret、fallback 邊界更大 | 延後到 P93 disabled-by-default 候選 |

採用 A。P92 runtime 不新增 OpenAI key，不接免費 provider，不調高 P91 Top-N，不把 duplicate local-only 當成必補深讀。若某日 local-only 全部來自 `duplicate_url` / `duplicate_signature`，P92 replay 應正確 no-op。

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] 前置 Phase 已收官：P91 Cache / Dedupe / Top-N CLOSED，commit `a1949d6` 已推上 `origin/main`。
- [x] P91 實跑證據已備：2026-05-22 Actions run 成功，遠端 commit `a020f32` 新增 `data/runs/2026-05-22/run_manifest.json`，`llm_calls=6` 且有 selection snapshot。
- [x] 本地/遠端分岔已處理：handoff commit 已 rebase 至 Actions 產物後並 push，`origin/main` 為 `c1dae0d`。
- [x] 主公已核准計畫凍結：2026-05-22 主公回覆「核准」。
- [x] 風險登記簿無未解新高風險：R-016 仍 Open，但 P92 是既定修復主線；不新增不可逆操作。

P92 runtime 開工前尚需另行達成：
- [x] 主公明確核准 P92 runtime 動工。
- [x] P92 plan lint 通過，且若同步 handoff / active / risk / history，需保持 R-016 Open。
- [x] 明確確認 queue / artifact retention 不會把 raw content commit 進 repo。

## 4. Exit Criteria（退出條件）

P92 plan-only 凍結需全部達成：
- [x] 新增本檔 `docs/PHASE_92_PLAN.md`。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_92_PLAN.md` 通過。
- [x] `git diff --check` 通過。
- [x] P92 runtime 在 plan freeze 當下明確維持未核准狀態；後續已由主公另行核准 runtime。

P92 runtime 收官需全部達成：
- [x] 建立 enrichment queue schema，至少包含 `schema_version`、`run_date`、`source_hash`、`source_count`、`eligible_count`、`skipped_count`、`records`、`retention_truth`。
- [x] Queue 可保存 replay 所需原始欄位，但只能位於 git-ignored 本機路徑或 GitHub Actions artifact；不得 commit raw content、prompt 或作者個資到 repo。
- [x] Manifest 寫入 raw-free `enrichment` snapshot，至少包含 `queue_available`、`eligible_posts`、`skipped_posts`、`enriched_posts`、`skipped_reason_counts`、`artifact_retention_days`、`replay_status`。
- [x] Replay CLI 尊重 P90 budget / cooldown；budget 不足時 no-op 或 partial，不得繞過 cooldown。
- [x] P92 只補可補價值高的 local-only：`topn_overflow` / budget-limited 類候選；`duplicate_url` / `duplicate_signature` 預設 skipped。
- [x] Enriched 結果可與既有 `analysis_YYYYMMDD.json` / report / manifest 合併，但 raw source retained 與 P91 selection truth 不被改寫。
- [x] 2026-05-22 這類 local-only 全為 `duplicate_url` 的日子，replay 應顯示 `eligible_posts=0` 並成功 no-op，不消耗 LLM。
- [x] Tests 覆蓋 queue raw-free manifest、duplicate no-op、topn_overflow eligible、budget cap、cooldown skip、partial replay、merge 不丟貼文、artifact path 不被 git add。
- [x] Focused tests、full `py -m pytest -q`、py_compile、governance doctor、cost/cache governance 通過；R-016 仍不得關閉。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 5-8 h |
| 預估收益等級 | 高 |
| 收益描述 | 把 P91 的「少打 LLM」補上一條受控後補深讀路徑，讓 partial coverage 不等於永久洞察變淺 |
| ROI 結論 | 值得做；這是 R-016 零額外付費主線中承接 P91 節流後的品質補償層 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增小型 enrichment queue helper 與 replay CLI，保持 queue / replay / merge 分工清楚 | 把 replay 邏輯塞回 `main.py` 造成 daily pipeline 難測 | helper 純函式 + CLI integration tests；`main.py` 只產 queue / snapshot |
| **2. 邏輯層 (Logic)** | reason-aware enrichment：只補值得深讀的 local-only，duplicate 預設跳過 | 把 duplicate 又送回 LLM，抵銷 P91 節流 | eligibility enum 與 tests 固定 `duplicate_url` / `duplicate_signature` no-op |
| **4. 測試層 (Testing)** | 建立 queue / replay / merge / budget matrix tests | 補深讀依賴 Actions artifact，本地難復現 | 用 fixture queue + fake analyzer + fake budget snapshot 測 deterministic path |
| **10. 安全層 (Security)** | manifest raw-free；raw queue 只進 git-ignored path 或 short-retention artifact | 第三方貼文內容被 commit 或長期保存 | `.gitignore` 路徑檢查、no raw leakage tests、artifact retention 明文化 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | Queue producer 與 replay consumer 解耦；provider abstraction 留給 P93 | P92 偷渡新 provider 或改 Gemini client 大邊界 | Forbidden Work 明列不接 provider；replay 只使用現有 analyzer interface |
| **5. 資料層 (Data)** | raw content 在 queue artifact；repo manifest 只留 counts / hashes / reason codes | manifest 無 per-post IDs 時難追蹤 local-only | P92 runtime 新增 stable raw-safe source id / queue digest，不寫 raw content |
| **6. 可觀察性層 (Observability)** | manifest / CLI 顯示 eligible、skipped、enriched、budget skip 與 no-op reason | 主公只看到 partial，不知道為何沒補 | `enrichment` snapshot 與 runbook 說明 duplicate no-op 是正常結果 |
| **7. 韌性層 (Resilience)** | budget/cooldown active 時 replay no-op，不影響 daily production report | replay 失敗拖垮每日報告或覆蓋健康產物 | P92 replay 預設手動 / local-only，不作 daily blocking gate |
| **13. 可維護性層 (Maintainability)** | queue schema 版本化、reason enum 固定、merge 規則集中 | 半年後不知道哪些 local-only 能補 | docs + tests 固定 eligibility table |
| **14. 文件層 (Documentation)** | 更新 runbook / cost policy / handoff，說明 artifact-backed queue 與 no-op | 接手者誤以為 local-only 全都要補深讀 | 文件明列 duplicate skipped、topn/budget eligible |
| **15. 流程層 (Process)** | FROZEN -> APPROVED -> IN_PROGRESS；runtime 需主公另行核准 | plan 凍結後 AI 直接改 runtime | handoff / active 明確列 P92 runtime forbidden until approved |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | replay 可能處理多日 queue 或大量 local-only | 一次補太多造成 Actions timeout 或 provider 壓力 | CLI cap / per-run max enrichment，預設小批次 |
| **9. UX/A11y 層** | 報告 metadata 可能顯示 enrichment 狀態 | 使用者誤解 no-op 為失敗 | 文案使用「無需補深讀：本批 local-only 為 duplicate」而非錯誤語氣 |
| **11. 部署層 (DevOps)** | GitHub Actions artifact / workflow_dispatch 參與 replay | artifact retention 過短或路徑錯誤導致無法補跑 | retention days 明列；artifact missing 時 manifest 顯示 queue unavailable |
| **12. 成本層 (Cost)** | replay 會消耗 LLM budget | 補深讀把每日 budget 吃光，影響正常 daily | P90 budget check 優先，replay cap 低於 remaining budget |
| **16. 隱私/合規層 (Privacy)** | queue 保存第三方貼文 raw content | raw 內容長期保存或被提交 | git-ignored / artifact retention / raw-free manifest 三層隔離 |
| **17. i18n/在地化層** | 多平台多語內容補深讀 | 跨語內容被 eligibility heuristic 誤判 | P92 不做語意同義判斷，只依 P91 reason / score / budget 補跑 |

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
| 新增 `docs/PHASE_92_PLAN.md` | 可逆 | 主公於 2026-05-22 核准 plan freeze |
| P92 runtime 實作 commit | 可逆 | 尚未核准，需主公另行確認 |
| GitHub Actions artifact retention 設定 | 可逆 | runtime 前需主公核准 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：duplicate local-only 可能讓 replay 顯示 no-op，這是節流成功，不是沒做事。
- [x] 中間檔產出：queue 可能含 raw post content，必須只在 git-ignored path 或 Actions artifact。
- [x] 系統狀態變更：P92 後 partial coverage 可能被後補為 richer report，但不保證每篇 local-only 都會被 LLM 深讀。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-22。
- 本計畫過期日期：2026-06-22；若 P93 provider abstraction、Gemini quota、或 Actions artifact policy 先改，P92 runtime 需重審。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：P92 的價值是讓 P91 省下來的 LLM calls 不變成永久洞察缺口；主公應能看到哪些貼文值得補、哪些因 duplicate 正常跳過。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面是 raw queue 被 commit、artifact 被長期保存、惡意貼文誘導 replay 消耗 budget、或 replay 覆蓋健康報告；最小緩解是 raw-free manifest、artifact retention、budget cap、no-op 安全路徑。
- **接手者視角**：接手者要能從 queue schema、manifest enrichment snapshot、runbook 三處理解 replay 為何補或不補。
- **X4-J 自動化建議性工具邊界**：Eligibility 是啟發式，不是內容價值真相；false negative 包含 duplicate 其實有新留言脈絡、短文卻有高價值爆料、跨平台轉貼但討論區回覆不同。
- **X4-K 使用者端審查官 / Patric 型人格**：使用者可能把 enrichment no-op 解讀成失敗；報告與 CLI 必須明講「本批 local-only 因 duplicate 跳過，raw source 仍已納入 baseline」。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | Queue 保存 raw content 後被誤 commit 或長期留存 | 中 | 高 | 安全/隱私 | git-ignored path、Actions artifact retention、no raw leakage tests |
| R2 | Duplicate local-only 被錯誤補深讀，抵銷 P91 節流 | 中 | 高 | 邏輯/成本 | eligibility enum：duplicate 預設 skipped，tests 固定 2026-05-22 型 no-op |
| R3 | Replay 消耗正常 daily run budget，導致隔日 production 變 local-only | 中 | 高 | 成本/流程 | P90 budget check 優先，replay cap 低於 remaining budget，runbook 建議非 daily 高峰執行 |
| R4 | Manifest 只有 aggregate counts，缺 stable source id 導致無法追蹤補深讀對象 | 中 | 中 | 資料/可觀察性 | P92 runtime 新增 raw-safe source id / queue digest，但不寫 raw content |
| R5 | Replay merge 覆蓋既有 analysis/report，造成資料回退 | 低 | 高 | 資料/韌性 | merge 前保留 source_hash / run_id；dry-run 與 explicit write 模式分離 |
| R6 | P92 混入 P93 provider abstraction | 中 | 高 | 流程/架構 | Forbidden Work 明列不新增 provider；免費 provider 只保留 P93 disabled-by-default 候選 |

**高風險加權檢查（META4）**：
- 高風險數量：5 項（R1/R2/R3/R5/R6 影響高）。
- 加權分數：8 分。
- 是否 >= 5 須請示主公：是；本檔僅凍結計畫，runtime 需主公另行核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P92.0 Plan Freeze** | 建立本檔，固定 artifact-backed queue / replay 邊界 | 防止直接改 runtime 或混 P93 | lint plan / diff check |
| **P92.1 Queue Contract** | 定義 queue schema、eligible/skipped reason、raw-free manifest snapshot | raw 泄漏、追蹤不清 | schema tests + no raw leakage tests |
| **P92.2 Producer Integration** | daily runtime 產生 git-ignored queue / optional Actions artifact | manifest 只有 counts 無法補跑 | queue fixture + artifact path tests |
| **P92.3 Replay CLI** | 手動 replay local-only eligible posts，尊重 P90 budget/cooldown | 補深讀超 budget | fake budget / fake analyzer tests |
| **P92.4 Merge + Manifest** | enriched 結果合併回 analysis/report/manifest，保留 P91 selection truth | 覆蓋既有健康報告 | dry-run / explicit write tests |
| **P92.5 Closeout Verification** | focused tests、full pytest、doctor/governance、docs/handoff 更新 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

目前狀態：P92.0-P92.5 已完成並通過本地驗證；後續 provider abstraction 必須另開 P93 plan，不得在 P92 追加。

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_92_PLAN.md`：本 Phase 凍結計畫。

**P92 plan-only 修改**：
- 無。若主公要求同步 handoff / active / risk / history，另以文件變更處理，不動 runtime。

**P92 runtime 核准後預計新增 / 修改**：
- `analyzer/enrichment_queue.py`：新增 queue schema、eligibility、raw-free snapshot helper。
- `analyzer/source_selection.py`：必要時補 per-post reason / stable source id，供 queue producer 追蹤 local-only。
- `scripts/enrichment_replay.py`：新增手動 replay CLI，尊重 P90 budget / cooldown。
- `main.py`：在 P91 selection 後產生 git-ignored enrichment queue / manifest enrichment snapshot。
- `analyzer/run_manifest.py`：新增 manifest `enrichment` snapshot normalize / validate。
- `.github/workflows/daily_report.yml`：必要時上傳 short-retention enrichment queue artifact。
- `scripts/cost_cache_governance.py`、`scripts/system_doctor.py`：顯示 enrichment / replay advisory。
- `docs/OPERATIONS_RUNBOOK.md`、`docs/COST_CACHE_GOVERNANCE_POLICY.md`：補 enrichment replay runbook。
- `tests/test_enrichment_queue.py`、`tests/test_enrichment_replay.py`、既有 manifest / doctor / governance tests。

**刪除**：
- 無。

**影響但未直接修改**：
- P93 provider abstraction：不得混入 P92；P92 只使用既有 provider path。
- P95 closeout：P92 只是 R-016 子問題之一，不得直接關閉 R-016。

---

## 11. Forbidden Work（P92 邊界）

- 不新增 `OPENAI_API_KEY`，不要求主公多花 OpenAI API 錢。
- 不接 Groq / Cloudflare / GitHub Models 等免費 provider；P93 才能 disabled-by-default 設計。
- 不調高 `LLM_DAILY_BUDGET` 或 `LLM_ANALYSIS_TOP_N` 來假裝補深讀。
- 不把 raw queue、raw prompt、raw provider response、作者資訊 commit 進 repo。
- 不讓 replay 繞過 P90 budget / cooldown。
- 不把 `duplicate_url` / `duplicate_signature` 預設送 LLM。
- 不把 enrichment no-op 當成失敗；若 no-op 由 duplicate 主導，應明確標示為 expected.
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] Queue raw content 被 commit、推送或長期留存超過 retention。
- [ ] Replay 消耗過多 budget，導致正常 daily run 變成 local-only。
- [ ] Duplicate local-only 被大量補深讀，抵銷 P91 call reduction。
- [ ] Replay merge 覆蓋健康報告或造成 landing 指向退回舊報告。
- [ ] 主公或接手者誤以為 local-only no-op 是系統失敗。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-92-enrichment-replay.md`。

> **B-NNN / R-NNN 編號規則（B-010）**：若本 Phase 收官時新增 blindspot 或 risk，必須先查下一個全域編號，禁止 Phase 內局部編號。

---

## 13. Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是 raw queue 外洩、artifact 長期保存、惡意貼文誘導 replay 消耗 budget、或 replay merge 覆蓋健康產物；最小緩解是 raw-free manifest、short retention、budget cap、explicit write。 |
| **X4-B 接手者** | 接手者需要從 queue schema、manifest enrichment snapshot、runbook 三處定位某篇 local-only 為何 eligible、skipped 或已 enriched。 |
| **X4-C 災難情境** | 情境：replay 把 duplicate local-only 全送 LLM，隔日 budget 被吃光；緩解：duplicate 預設 skipped，replay cap 低於 P90 remaining budget。 |
| **X4-D 5 年後** | 五年後 provider 與平台可能全換，但 artifact-backed queue、raw-free manifest、budget-aware replay 三段資料流仍應可理解與替換。 |
| **X4-E 終端 vs IDE** | 終端 CLI 必須直接顯示 eligible/skipped/enriched/no-op，不要求接手者打開 HTML 或 GitHub UI 才知道 replay 結果。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows 本機與 Linux Actions 都會處理 queue path；runtime 需使用 `pathlib` 與 JSON schema，不寫 shell-specific 路徑假設。 |
| **X4-G 主公個人視角** | 主公要的是零額外付費又不失去深讀品質；P92 必須讓補深讀有證據、有上限，且清楚說明何時不需要補。 |
| **X4-H 觀測 / 治理** | 若 enrichment 只存在 artifact 而 manifest 無 snapshot，下一視窗無法判斷補跑狀態；manifest 必須寫 raw-free enrichment counts。 |
| **X4-I 主公可見性** | 主公看不到的是 queue 是否含 raw、artifact 留多久、replay 為何 no-op；計畫要求 retention、manifest snapshot、CLI output 一起攤開。 |
| **X4-J 自動化建議性工具邊界** | Eligibility 是啟發式，召回率僅供參考；duplicate 可能有新討論脈絡、短文可能是爆料，仍需人工抽查與後續 risk review。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者可能把 no-op 誤會成沒做事；報告與 CLI 需用「本批 local-only 為 duplicate，已納入 baseline，不消耗 LLM」的語意。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P92 只處理 enrichment replay，不混 P93 provider，不關閉 R-016。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；raw queue 不進 repo，artifact retention 與 budget cap 是主要安全邊界。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；no-op 必須講成 expected duplicate skip，不讓人以為 replay 壞掉。 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase plan 需引用 P91 實跑證據與 R-016 邊界。 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；P91 實跑數據是 `llm_calls=6`、`local_only_posts=7`、`duplicate_url=7`。 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 條件觸發；若 runtime 顯示 report metadata，需避免把 no-op 文案做成錯誤警報。 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P92 不加 paid fallback，replay 必須低於 P90 remaining budget。 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；Actions artifact、workflow_dispatch、git-ignored queue path 都需可驗證。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | Queue 若含 raw content，被 `git add data/` 或 workflow fallback 誤納入，會擴散第三方貼文內容。 | **S** | 0 | Queue 放 git-ignored path / artifact；manifest raw-free；tests 檢查 raw leakage 與 tracked path。 | 入計畫範圍：P92.1/P92.2 |
| 2 | Replay 若把 duplicate_url 全部補深讀，P91 省下的 calls 會被 P92 花回去。 | **S** | 0 | eligibility 明確讓 duplicate 預設 skipped；2026-05-22 型 fixture 應 no-op。 | 入計畫範圍：P92.1/P92.3 |
| 3 | Replay 消耗 budget 可能讓正常 daily run 沒額度，反而使 production 變 local-only。 | **S** | 0 | P90 budget / cooldown 檢查優先；replay cap 低於 remaining budget，且預設手動執行。 | 入計畫範圍：P92.3 |
| 4 | Manifest 現在只有 aggregate selection counts，沒有 per-post reason，可能無法重建 local-only queue。 | A | 0 | P92 runtime 需新增 stable source id / per-post queue record，但只在 artifact 保存 raw。 | 入計畫範圍：P92.1/P92.2 |
| 5 | Replay merge 可能覆蓋健康 report 或讓 landing 指回舊產物。 | A | 0 | dry-run 與 explicit write 分離；merge 前檢查 run_date/source_hash；report promotion 仍走 existing gate。 | 入計畫範圍：P92.4 |
| 6 | P92 很容易順手接免費 provider，讓 provider abstraction 邊界失控。 | A | 0 | Forbidden Work 明列 P93 才能處理 disabled-by-default provider；P92 只用現有 analyzer path。 | 入計畫範圍：P92.0 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增或修改 skill，STR9 不觸發；若後續臨時新增 skill，必須另開 Phase 或修訂計畫並重新凍結。

---

## 15. Plan Freeze 實跑證據（2026-05-22）

| 指令 | 結果 |
|---|---|
| `py scripts\lint_phase_plan.py docs\PHASE_92_PLAN.md` | PASS：通過 Pre-flight 體檢（M1 + M2） |
| `git diff --check` | PASS；無輸出 |

### 凍結後下一步

P92 plan 已於同日取得主公 runtime 核准，並完成 P92.1-P92.5 runtime。後續供應商抽象化、免費 provider 插槽、SLO 重分類不得追加到 P92，需另開 P93 或後續 Phase。

---

## 16. 凍結戳記

- **凍結人**：主公核准，AI 執行
- **凍結時間**：2026-05-22 03:05 Asia/Taipei
- **凍結後變更**：主公已核准 P92 runtime 動工；runtime 收官證據見下節。

---

## 17. Runtime 收官證據（2026-05-22）

### 17.1 物理真相

- `analyzer/enrichment_queue.py`
  - 新增 `ENRICHMENT_SCHEMA_VERSION=1`。
  - Queue raw truth：`raw replay queue; do not commit to repo`。
  - Snapshot raw-free truth：`raw-free enrichment snapshot only`。
  - `duplicate_url` / `duplicate_signature` / `low_signal_local_only` 只進 skipped；`topn_overflow` 在 replay cap 內才 eligible。
  - `build_enrichment_snapshot(...)` 只輸出 counts、digest、reason counts、budget decision，不輸出 raw title/content/url。
- `analyzer/source_selection.py`
  - `SourceSelection` 新增 `local_only_reasons` 與 `local_only_records`。
  - 新增 `build_source_id(...)`：用 platform / normalized url / title signature / content signature 建立 16 字元 raw-safe digest。
- `main.py`
  - P91 selection 後產生 `data/enrichment_queue/<date>/enrichment_queue.json`。
  - `daily_summary["_meta"]["enrichment"]` 進入 manifest。
  - 無 local-only 時產生 `not_available` snapshot；duplicate-only local-only 會是 `queue_available=true` / `eligible_posts=0` / `replay_status=no_eligible`。
- `scripts/enrichment_replay.py`
  - 預設 dry-run。
  - `--apply` 才寫入 `enriched_posts.json` 與更新既有 manifest `enrichment`。
  - `--write-report` 才生成候選報告，且 `promote=False`。
  - 使用 `FallbackLLMClient(enable_openai=False)`，不新增 OpenAI 成本。
  - 依 P90 budget snapshot 判斷 `call_llm` / `skip_llm`，不得繞過 cooldown / exhausted。
- `.github/workflows/daily_report.yml`
  - 新增 `actions/upload-artifact@v4` 上傳 `data/enrichment_queue/`。
  - `retention-days: 3`，`if-no-files-found: ignore`。
- `analyzer/run_manifest.py`
  - 新增 manifest `enrichment` snapshot normalize / validate。
- `scripts/system_doctor.py`
  - 新增 `DOC019 enrichment:replay`。
- `scripts/cost_cache_governance.py`
  - 新增 `CCG008 enrichment replay` 與日級 enrichment 欄位。
- `docs/OPERATIONS_RUNBOOK.md` / `docs/COST_CACHE_GOVERNANCE_POLICY.md`
  - 補 P92 replay no-op / pending / budget skip / failed 處置。

### 17.2 驗證

| 指令 | 結果 |
|---|---|
| `py -m pytest -q tests\test_enrichment_queue.py tests\test_enrichment_replay.py tests\test_source_selection.py tests\test_run_manifest.py tests\test_system_doctor.py tests\test_cost_cache_governance.py` | PASS：66 passed |
| `py -m py_compile analyzer\enrichment_queue.py analyzer\source_selection.py analyzer\run_manifest.py scripts\enrichment_replay.py scripts\system_doctor.py scripts\cost_cache_governance.py main.py` | PASS |
| `py -m pytest -q` | PASS：274 passed |
| `py scripts\system_doctor.py --repo-root . --date 2026-05-22 --profile local --skip-landing` | PASS exit 0；僅既有 DOC007 / DOC018 advisory |
| `py scripts\cost_cache_governance.py --repo-root . --date 2026-05-22 --window-days 1 --max-llm-calls 20` | PASS exit 0；僅既有 CCG007 advisory |
| `git diff --check` | PASS；僅 CRLF warning，無 whitespace error |

### 17.3 收官狀態

- ✅ P92 runtime CLOSED。
- ✅ R-016 仍 Open。
- ✅ Raw queue 不納入 repo；只在 git-ignored `data/enrichment_queue/` 或 short-retention Actions artifact。
- ✅ P93 provider abstraction 尚未動工，需另開計畫。
