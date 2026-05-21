# Phase P91 計畫書 — Cache / Dedupe / Top-N（凍結版）

> 狀態：FROZEN。P91 目前只完成計畫凍結；runtime code 尚未核准，未經主公明確同意前不得修改 `main.py`、`analyzer/`、`scripts/` 或任何 cache/dedupe/top-N runtime。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P91 |
| **Phase 名稱** | Cache / Dedupe / Top-N |
| **凍結日期** | 2026-05-21 |
| **影響半徑** | 標準 (3-9 檔) - runtime 預計新增 source selection helper，並接入 main / sentiment / manifest / governance scripts / tests / docs |
| **預估投入時數** | 5-8 小時 |
| **Token budget** | 50K-80K tokens |
| **負責模型** | GPT-5.3-Codex 高；若同一 selection trace 修 3 次仍失敗，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P91 plan | DRAFT | FROZEN | 計畫邊界已固定，但 runtime 尚不可施工 | 本檔建立，handoff / active / risk / history 同步，plan lint 通過 | 主公要求繼續，AI 執行 |
| P91 runtime | NOT_STARTED | PENDING_APPROVAL | 預計施工範圍已定，但尚未核准改程式碼 | 主公明確說「核准 P91 runtime 動工」後才能轉 APPROVED | 主公核准 |
| R-016 | Open | Open | R-016 仍是跨 Phase 風險；P91 只處理 cache/dedupe/top-N 子問題 | P91 runtime 收官也不得直接關閉 R-016，需等 P95 closeout | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

把每日 LLM 呼叫從「搜到多少篇就盡量全送」改成「先去重，再只把高價值 Top-N 送 LLM，其餘真實資料走 local deterministic baseline」，讓 `llm_calls` 穩定低於 P90 budget，並在 manifest / governance 中看得到 selection 節流效果。

## 2. 觸發背景 (Why Now)

P90 已完成 budget ledger / cooldown，能在 budget 不足時停損；但目前實跑仍可能出現 `llm_calls=28`、超過 governance threshold 20 的情況。這代表 P90 是煞車，P91 要做的是油門控制：在進 provider 前先縮小需要深讀的候選集合，避免每次都等 budget 或 quota 來救火。

## 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Source selection planner | 新增規則式 source planner：URL/content 去重、source/platform 多樣性、hero/source score、budget-aware Top-N | 最直接降低 LLM calls；不依賴新 provider；可測、可觀測 | 需要小心保留所有真實資料，不可把未選貼文丟掉 | 採用 |
| B. 只調高 P90 budget | 把 `LLM_DAILY_BUDGET` 從 20 提高到 30 或更多 | 改動最小 | 只是延後撞 quota，沒有減少成本與噪音 | 不採用 |
| C. 更積極依賴 L2 cache | 期待 prompt cache 命中降低呼叫 | 不改 selection 流程 | 新貼文仍大量 miss；cache hit 低時無法阻止爆量 | 不單獨採用 |
| D. 全部 local-only，完全不打 LLM | 直接跳過深度 LLM | 零 provider 成本 | 報告失去 LLM 深讀價值，偏離 R-016 quality-tiered 目標 | 不採用 |

採用 A，並保留 B/C 作為邊界：P91 runtime 不調高 budget，不新增 provider；L2 cache 仍可加分，但不是唯一防線。

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] 前置 Phase 已收官：P90 Budget Ledger / Cooldown CLOSED，commit `798ed58` 已推上 `origin/main`。
- [x] 資料/依賴已備：manifest 已有 `metrics.llm_calls`、`metrics.total_calls`、`budget` snapshot、quality tier 與 source quality。
- [x] 主公已核准計畫凍結：2026-05-21 主公要求「那繼續P91囉」。
- [ ] 主公尚未核准 runtime 動工：本檔 FROZEN 後需主公明確說「核准 P91 runtime 動工」。
- [x] 風險登記簿無未解新高風險：R-016 仍 Open，但 P91 是既定修復主線；不新增不可逆操作。

## 4. Exit Criteria（退出條件）

P91 runtime 收官需全部達成：
- [ ] 新增 deterministic source selection contract，至少輸出 `total_input_posts`、`unique_posts`、`duplicate_posts`、`llm_selected_posts`、`local_only_posts`、`selection_reasons`。
- [ ] LLM 深讀候選數由 `LLM_ANALYSIS_TOP_N` 或 P90 budget remaining 限制；預設不得高於 20。
- [ ] 去重只影響 LLM 分析候選，不可刪除 raw source；報告仍能使用真實資料 local baseline 補齊未送 LLM 的貼文。
- [ ] 同 URL、明顯同標題同平台、空內容或極短低訊號貼文不得重複消耗 LLM provider call。
- [ ] Top-N selection 保留平台/來源多樣性，避免單一平台洗掉其他來源。
- [ ] Manifest 寫入 `selection` snapshot；doctor / cost governance 顯示 dedupe 與 top-N 節流狀態。
- [ ] `production_local_only` / `production_llm_partial` 仍可由 P89 gate 判定，不回退成 showcase。
- [ ] Tests 覆蓋 exact URL dedupe、title/content near dedupe、platform diversity、budget-aware cap、local-only merge、manifest selection validation、cost governance CCG for excessive LLM calls。
- [ ] Focused tests、full `py -m pytest -q`、health、doctor、cost/cache governance、handoff truth、governance doctor、diff check 全部通過。
- [ ] `TASK_HISTORY.md`、`NEXT_SESSION_HANDOFF.md`、`docs/ACTIVE_OPERATION.md`、`docs/RISK_REGISTRY.md` 更新；R-016 仍不得關閉。

P91 plan-only 凍結需全部達成：
- [x] 新增本檔 `docs/PHASE_91_PLAN.md`。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_91_PLAN.md` 通過。
- [x] handoff / active / risk / history 更新成 P91 FROZEN。
- [x] `py scripts\check_handoff_truth.py --repo-root .` 通過。
- [x] `py scripts\governance_doctor.py --repo-root .` 通過。
- [x] `git diff --check` 通過。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 5-8 h |
| 預估收益等級 | 高 |
| 收益描述 | 把 provider 壓力從事後 cooldown 改成事前節流；預期每日 LLM calls 從 20+ 壓到設定 Top-N 範圍內 |
| ROI 結論 | 值得做；這是 R-016 零額外付費主線中降低 429 與 CCG005 的關鍵環節 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增小型 source selection helper，集中 dedupe / scoring / Top-N 決策 | selection 判斷散落在 `main.py` 與 `sentiment.py` 後難以測試 | 單一 helper + focused tests；main 只接收 plan 結果 |
| **2. 邏輯層 (Logic)** | 先 dedupe，再 selection，再 LLM partial analysis，最後 local baseline merge | 少送 LLM 後可能漏掉關鍵高價值貼文 | scoring 明列 hero focus、source score、platform diversity、recency / search score |
| **4. 測試層 (Testing)** | 建立 selection matrix tests，覆蓋去重、Top-N、多樣性、budget cap、merge 完整性 | 只在 Actions 才看出 calls 爆量，本地測不到 | 用 deterministic fake SearchResult 與 fake budget snapshot 測 selection output |
| **10. 安全層 (Security)** | selection state / manifest 只寫計數、normalized id、reason code，不寫 raw content | manifest 或 debug output 洩漏 raw post / URL 之外的敏感內容 | raw source 照既有 raw 檔處理；selection snapshot 禁 raw content / prompt |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | Selection planner 獨立於 provider client，輸出純資料 plan | 後續 P92 replay 或 P93 provider 需要重寫 selection | 對外只暴露 `build_selection_plan(...)` 與 manifest-safe snapshot |
| **5. 資料層 (Data)** | raw results 保留完整；selection snapshot 只描述選取結果 | 去重若直接刪 raw，會破壞追溯與 source_hash | raw data 不變；selection 只控制 LLM 深讀候選 |
| **6. 可觀察性層 (Observability)** | manifest / doctor / cost governance 顯示 duplicate count、selected count、local-only count | 主公只看到 LLM calls 降低，不知道少分析了哪些類型 | CLI 與 manifest 明確列 reason counts |
| **7. 韌性層 (Resilience)** | 未選入 LLM 的貼文走 P88 local deterministic baseline | local-only 過多可能使報告洞察變淺 | quality tier 顯示 `production_llm_partial` 或 `production_local_only`，不假裝 full LLM |
| **13. 可維護性層 (Maintainability)** | reason code 固定 enum，selection scoring 不接外部 API | scoring 變成魔法數，半年後看不懂 | docs 與 tests 固定每個 reason code 的語意 |
| **14. 文件層 (Documentation)** | 更新 handoff / active / runbook / cost policy，說明 selection 是節流不是刪資料 | 接手者誤以為 duplicate posts 被永久丟棄 | 文件強調 raw source retained、LLM selected subset |
| **15. 流程層 (Process)** | FROZEN -> APPROVED -> IN_PROGRESS；runtime 前需主公核准 | plan 凍結後 AI 直接改 cache / selection runtime | handoff / active 寫明 P91 FROZEN 與 Forbidden Work |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 每日 pipeline 會處理多平台貼文 | near-dedupe 若用昂貴相似度比對，可能拖慢 Actions | 初版只用 normalized URL/title/content signature，O(n) 或 O(n log n) |
| **9. UX/A11y 層** | report metadata 可能顯示 selection/tier | 使用者誤解為資料被砍掉 | 文案只說「LLM 深讀 Top-N，其餘以本地 baseline 納入」 |
| **11. 部署層 (DevOps)** | GitHub Actions daily run 會依 selection 節流 | CI 與本機 timezone / env cap 不一致 | config defaults 固定，manifest 記錄實際 cap |
| **12. 成本層 (Cost)** | LLM calls 與 quota 直接相關 | Top-N 太高仍超 budget，太低則洞察不足 | default Top-N 先對齊 P90 budget，後續由 CCG005 / CCG006 調整 |
| **16. 隱私/合規層 (Privacy)** | 第三方貼文進入 raw / analysis | selection snapshot 不該複製 raw content | snapshot 只存 counts、reason codes、可選 normalized hash |
| **17. i18n/在地化層** | 多語平台標題 / 內容參與 near-dedupe | 簡繁、泰文、越文 normalization 可能誤判 | 初版只做保守 exact / normalized title，比 aggressive semantic dedupe 更安全 |

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
| 新增 `docs/PHASE_91_PLAN.md` | 可逆 | 主公要求繼續，本階段只凍結計畫 |
| 更新 handoff / active / risk / history | 可逆 | 主公要求繼續，本階段只凍結計畫 |
| P91 runtime 實作 commit | 可逆 | 尚未核准，需主公另行確認 |
| Git push | 半可逆 | 每次 push 前需主公明確說 push |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：同一輪可能搜到 30 篇，但只有 Top-N 送 LLM；需在 manifest 說明其餘仍被 local baseline 納入。
- [x] 中間檔產出：可能新增 selection snapshot 或 selection diagnostics；必須 raw-free。
- [x] 系統狀態變更：P91 後 `llm_calls` 降低不等於資料變少，而是 LLM 深讀範圍被節流。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-21。
- 本計畫過期日期：2026-06-21；若 P92 replay 或 Gemini quota 行為先改，P91 runtime 需重審。
- 風險記錄帶日期：是。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：P91 的價值是讓系統少打 API 但不丟真實資料；主公應能從 manifest 看出 LLM 深讀幾篇、local baseline 補幾篇。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面是惡意大量近似貼文誘導 Top-N 被洗掉，或用標題相似度讓重要負面被 dedupe；最小緩解是保守 dedupe、多樣性 quota、reason codes 可稽核。
- **接手者視角**：接手者要能從 source planner tests、manifest selection snapshot、cost governance row 三處理解為何 calls 降低。
- **X4-J 自動化建議性工具邊界**：Selection scoring 是啟發式，不是內容品質真相；false negative 包含跨語言同義改寫、截圖型貼文、短標題但高價值爆料。
- **X4-K 使用者端審查官 / Patric 型人格**：使用者可能誤解 Top-N 為只看 Top-N 資料；報告/metadata 必須說清楚未深讀貼文仍納入 local baseline。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | Dedupe 誤判，把重要但相似的貼文排除在 LLM 深讀之外 | 中 | 高 | 邏輯 | 初版只做保守 exact / normalized signature；near-dedupe 只降分不硬刪 |
| R2 | Top-N 被單一平台或同一來源洗版 | 中 | 高 | 資料 | platform/source diversity quota；tests 固定多平台保留 |
| R3 | LLM calls 降低後，報告被誤認為資料減少或偷工 | 中 | 中 | UX/文件 | manifest / metadata / docs 寫明 full raw retained、LLM selected subset |
| R4 | Selection snapshot 寫入 raw content 或 prompt，造成資料洩漏 | 低 | 高 | 安全 | snapshot schema 禁 raw content，新增 no raw leakage tests |
| R5 | Top-N cap 太低，連續多日 `production_local_only` 比例過高 | 中 | 中 | 成本/品質 | governance 顯示 selected/local-only ratio，後續 P92 replay 補深讀 |
| R6 | P91 混入 P92 replay/backfill 或 P93 provider abstraction | 中 | 高 | 流程 | Forbidden Work 明列，不得越界；handoff 只允許 P91 scope |

**高風險加權檢查（META4）**：
- 高風險數量：3 項（R1/R2/R4/R6 影響高）。
- 加權分數：6 分。
- 是否 >= 5 須請示主公：是；本檔僅凍結計畫，runtime 需主公另行核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P91.0 Plan Freeze** | 建立本檔，更新 handoff / active / risk / history | 防止直接改 runtime | lint plan / handoff truth / governance doctor |
| **P91.1 Source Selection Contract** | 定義 selection schema、reason enum、raw-free snapshot | raw 泄漏、追溯不清 | schema tests + no raw leakage tests |
| **P91.2 Dedupe Rules** | URL exact、normalized title/content signature、低訊號過濾 | 重複貼文耗 quota | dedupe matrix tests |
| **P91.3 Budget-aware Top-N** | 依 `LLM_ANALYSIS_TOP_N` 與 P90 remaining budget 決定 LLM selected subset | LLM calls 爆量 | fake budget tests + CCG005 改善 |
| **P91.4 Local Merge + Manifest** | 未選貼文走 local baseline，合併 LLM/local 結果，manifest 寫 selection | 資料被誤刪或不可見 | integration tests + manifest validation |
| **P91.5 Closeout Verification** | focused tests、full pytest、health/doctor/governance、history/handoff 更新 | Phase 狀態漂移 | 全驗證通過後 commit；R-016 仍 Open |

目前狀態：僅 P91.0 plan freeze 可執行；P91.1-P91.5 需主公核准 runtime 後才能開始。

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_91_PLAN.md`：本 Phase 凍結計畫。

**P91 plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`：Current Phase 改 P91 FROZEN。
- `docs/ACTIVE_OPERATION.md`：短版狀態同步。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P91 plan frozen。
- `TASK_HISTORY.md`：追加 P91 plan freeze 物理紀錄。

**P91 runtime 核准後預計修改**：
- `analyzer/source_selection.py`：新增 source dedupe / scoring / Top-N planner。
- `main.py`：在 raw save 與 analysis 前建立 selection plan，並把 snapshot 寫入 meta。
- `analyzer/sentiment.py`：支援 LLM selected subset + local-only merge，避免未選貼文變成丟失。
- `analyzer/run_manifest.py`：新增 manifest `selection` snapshot normalize / validate。
- `scripts/cost_cache_governance.py`：延伸 selection/call ratio 檢查，降低 CCG005 噪音。
- `scripts/system_doctor.py`：必要時顯示 selection advisory。
- `docs/COST_CACHE_GOVERNANCE_POLICY.md`、`docs/OPERATIONS_RUNBOOK.md`：補 selection / Top-N runbook。
- `tests/test_source_selection.py`、既有 sentiment / manifest / governance tests：新增矩陣測試。

**刪除**：
- 無。

**影響但未直接修改**：
- P92 enrichment replay：將使用 P91 的 local-only / LLM-selected 訊號決定後補深讀。
- P93 provider abstraction：將受益於 P91 reduced call volume，但不得混入 P91。

---

## 11. Forbidden Work（P91 邊界）

- 不加 `OPENAI_API_KEY`，不要求主公花 OpenAI API 錢。
- 不接 Groq / Cloudflare / GitHub Models 等免費 provider；P93 才能 disabled-by-default 設計。
- 不改 Gemini model list 或 schedule；P86 已 CLOSED。
- 不做 P92 enrichment queue / replay / backfill。
- 不做 P93 provider abstraction 或任何新 provider runtime。
- 不刪 raw source posts；P91 只限制 LLM 深讀候選。
- 不把 Top-N 說成內容品質真相；它只是成本與 quota 節流策略。
- 不關閉 R-016；P95 才能 closeout。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點 ─ G6

收官後若觸發以下情境，必寫 Postmortem：
- [ ] Dedupe 導致重要貼文未被 LLM 深讀，且造成報告判讀錯誤。
- [ ] Top-N 被單一平台洗版，其他平台訊號被排除。
- [ ] Selection snapshot 寫入 raw post、prompt、作者或任何不該 commit 的內容。
- [ ] 主公或接手者誤以為 P91 刪除了原始資料。
- [ ] 有任何「我以為 calls 降低就是品質不變，結果洞察變淺」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-91-cache-dedupe-topn.md`。

---

## 13. Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是大量近似貼文洗 Top-N、惡意標題誘導 dedupe、或用短文低訊號藏重要爆料；緩解是保守 dedupe、多樣性 quota、reason code 稽核。 |
| **X4-B 接手者** | 接手者需要從 `source_selection` helper、manifest selection snapshot、cost governance row 三處定位為何某些貼文沒有送 LLM。 |
| **X4-C 災難情境** | 情境：Top-N 全被同平台洗掉，其他平台負面消失；緩解：platform/source diversity tests 與 manifest reason counts。 |
| **X4-D 5 年後** | 五年後 provider 或平台可能全換，但 selection contract 仍應描述 raw retained、LLM subset、local-only subset 三種資料流。 |
| **X4-E 終端 vs IDE** | 終端輸出必須能看到 input/unique/selected/local-only counts，不能要求接手者打開 HTML 才知道省了多少 calls。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows 本機與 Linux Actions 都會跑 selection；需用 Python 標準字串/URL normalization，不寫 shell-specific 指令。 |
| **X4-G 主公個人視角** | 主公要的是不要再一直 429，又不要犧牲真實資料；P91 必須說清楚少打 LLM 不是少看資料。 |
| **X4-H 觀測 / 治理** | 若 selection 只存在 memory，下一視窗無法判斷 calls 為何下降；manifest / doctor / governance 必須寫出 selection snapshot。 |
| **X4-I 主公可見性** | 主公看不到的是哪些貼文只走 local baseline；handoff、manifest、governance 要攤開 selected/local-only 比例與理由。 |
| **X4-J 自動化建議性工具邊界** | Top-N scoring 是啟發式，召回率僅供參考；跨語言同義、截圖型貼文、短標題爆料仍需後續 P92 replay 補洞。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者可能把 Top-N 誤解成只處理少量資料；報告和文件要避免承諾 full LLM coverage，改標示 partial/local coverage。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P91 只處理 cache/dedupe/top-N，不混 P92 replay 或 P93 provider |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；selection snapshot 禁 raw content，dedupe 不能刪 raw |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；Top-N 文案必須說明未入選貼文仍被 local baseline 納入 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase 需更新 handoff、active、history、risk |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；selection metrics 必須清楚分 input/unique/selected/local-only |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 條件觸發；若 runtime 改 report metadata，需避免干擾核心報告閱讀 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P91 目標是降低 calls，不是提高 budget 或導回 paid fallback |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；Actions 需要看到 selection metrics，runtime 不得依賴本機狀態 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | Dedupe 若太 aggressive，可能把相似但立場不同的貼文排除在 LLM 深讀外。 | **S** | 0 | 初版 exact / normalized signature 才硬去重，near-dedupe 只降分不刪 raw。 | 入計畫範圍：P91.2 |
| 2 | Top-N 可能被單一平台洗版，讓跨平台輿情失真。 | **S** | 0 | 加 platform/source diversity quota，tests 固定多平台至少保留。 | 入計畫範圍：P91.3 |
| 3 | calls 降低後可能掩蓋 LLM coverage 變低，主公以為品質完全不變。 | A | 0 | manifest / quality tier / report metadata 顯示 selected/local-only ratio。 | 入計畫範圍：P91.4 |
| 4 | Selection snapshot 若寫 raw content，會把第三方貼文擴散到更多 metadata 檔。 | **S** | 0 | schema 禁 raw content、prompt、author；新增 no raw leakage tests。 | 入計畫範圍：P91.1 |
| 5 | P91 若順手做 P92 replay，就會把節流與補深讀混在一起，難定位。 | A | 0 | Forbidden Work 明列 P92 不得混入，P91 只輸出 local-only signals。 | 入計畫範圍：P91.0 |
| 6 | Cache-aware selection 若偷看 provider prompt key，可能和 prompt 格式強耦合。 | B | 0 | 初版 selection 以 SearchResult 層判斷；prompt cache 只作輔助，不作 schema 基礎。 | 入計畫範圍：P91.1 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增或修改 skill，STR9 不觸發；若後續臨時新增 skill，必須另開 Phase 或修訂計畫並重新凍結。

---

## 15. Plan Freeze 實跑證據（2026-05-21）

| 指令 | 結果 |
|---|---|
| `py scripts\lint_phase_plan.py docs\PHASE_91_PLAN.md` | PASS：通過 Pre-flight 體檢（M1 + M2） |
| `py scripts\check_handoff_truth.py --repo-root .` | PASS：HND000 active bootstrap truth verified |
| `py scripts\governance_doctor.py --repo-root .` | PASS：GOV000 runbook and risk registry governance verified |
| `git diff --check` | PASS；僅 CRLF warning |

### 凍結後下一步

P91 plan 凍結後，下一步是等待主公核准 P91 runtime 動工。核准前不得修改 cache/dedupe/top-N runtime；R-016 仍 Open。
