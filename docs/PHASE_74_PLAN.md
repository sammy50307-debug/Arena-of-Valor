# Phase P74 計畫書 — R-015 test_dynamic_focus 事件迴圈隔離修復（凍結版）

> 草案日期：2026-05-15
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：✅ 已收官；R-015 已關閉

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P74 |
| **Phase 名稱** | R-015 test_dynamic_focus 事件迴圈隔離修復 |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準（預估 3-6 檔；測試/模組/文件收官） |
| **預估投入時數** | 1.5 h |
| **Token budget** | 35K tokens |
| **負責模型** | GPT-5.3-Codex（repo 動工 + 測試修復）；若連 3 輪無進展升 GPT-5.5 高 |

## 0.5 狀態轉換清單

N/A。本 Phase 不變更 skill / module / workflow 生命週期狀態，只處理既有測試債與 RISK_REGISTRY 風險關閉。

---

## 1. 目標 (Objective)

讓 `tests/test_dynamic_focus.py` 的 5 個測試在「單檔執行」與「全測試套件執行」兩種情境都通過，關閉 R-015，避免 `test_dynamic_focus` 再被標為 pre-existing 放行。

## 2. 觸發背景 (Why Now)

P72.5 收官登記 R-015：`test_dynamic_focus.py` 有 3 個測試案例呈現事件迴圈隔離問題，單檔跑 OK、全套跑掛，且已連續 5 個 Phase 被標為 pre-existing。依 B-008 通則化規則，連續 >= 3 個 Phase 的 pre-existing failing test 必須升級為獨立 Phase 處理。

## 3. Entry Criteria

開工前必須全部完成：

- [x] 前置 Phase 已收官：P72.5 / P73 已在 handoff 標記完成並推送
- [x] 風險來源已定位：`docs/RISK_REGISTRY.md` R-015
- [x] 測試檔已定位：`tests/test_dynamic_focus.py`
- [x] 相關模組已定位：`analyzer/dynamic_focus.py`
- [x] 主公核准本計畫：2026-05-16「先來搞定 1/2/3」
- [x] 不全讀 `TASK_HISTORY.md`：只查 handoff / RISK_REGISTRY / 局部 grep

## 4. Exit Criteria

達成全部才算收官：

- [x] `py -m pytest tests/test_dynamic_focus.py -q` 通過（5 passed）
- [x] 全套或至少既有 Phase 標準測試命令通過（`py -m pytest -q` → 112 passed）
- [x] 3 個歷史 pre-existing 失敗不再出現
- [x] 若修改 production code，需證明 alert 結構仍為 `{"dynamic_alerts": [...], "overflow_alerts": [...]}`（未修改 production code）
- [x] `docs/RISK_REGISTRY.md` 將 R-015 移至已關閉或標記關閉條件達成
- [x] `TASK_HISTORY.md` 只追加 P74 無損紀錄，不全檔編輯
- [x] `git diff --check` 無 whitespace error

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 1.5 h |
| 預估收益等級 | 高 |
| 收益描述 | 清除連 5 Phase 的測試債，恢復全套測試對 regression 的可信度，避免後續 Phase 繼續用 pre-existing 放行 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 小範圍修改測試或 `analyzer/dynamic_focus.py`，保留現有 async 入口 | 為了測試通過而改壞 runtime 行為 | 先重現失敗，再用最小 diff 修根因 |
| **2. 邏輯層 (Logic)** | 區分事件迴圈隔離問題與業務邏輯錯誤 | 把 pytest event loop 污染誤判為 dynamic alert 邏輯錯 | 單檔 / 全套 / 相鄰測試三種情境交叉驗證 |
| **4. 測試層 (Testing)** | 補足 async test 執行方式或 fixture 隔離 | 只改測試讓它表面變綠 | 保留原 5 cases 的語意斷言，禁止刪斷言逃避 |
| **10. 安全層 (Security)** | 不新增外部 I/O、API key、網路呼叫 | 測試誤觸真實 LLM / 檔案狀態 | 保持 `news_history_indexer.load_index` mock；LLM 用 stub |

### A 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 優先修測試隔離；只有確認 production async 邏輯有缺陷才改模組 | 小測試債擴散成架構重構 | 明確禁止順手重構 dynamic focus 架構 |
| **5. 資料層 (Data)** | N/A，不改業務資料與報告資料 | 測試讀到本機 history index 造成不穩 | mock `load_index`，不依賴磁碟狀態 |
| **6. 可觀察性層 (Observability)** | 保留 logger 行為，收官記錄測試命令與結果 | 後續不知道失敗根因 | TASK_HISTORY 追加根因、修法、驗證命令 |
| **7. 韌性層 (Resilience)** | AI 失敗 fallback case 必須繼續保留 | 修 async 後破壞 fallback | 保留 `test_case5_ai_failure_fallback` 語意 |
| **13. 可維護性層 (Maintainability)** | 若需 helper，命名清楚且只服務測試隔離 | 新增過度抽象 | 優先使用 pytest 現有 async pattern |
| **14. 文件層 (Documentation)** | 計畫書 + RISK_REGISTRY + TASK_HISTORY 收官 | 文件與測試狀態漂移 | 收官時同步關閉 R-015 |
| **15. 流程層 (Process)** | 先計畫、主公核准、再動工；不 stage untracked 報告檔 | 直接修而跳過治理流程 | 本計畫核准後才改程式碼 |

### B 級層

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 全套測試執行時間 | 不新增慢速 sleep / 真實 I/O | 測試變慢 | 使用 stub/mock，不等待真實事件 |
| **11. 部署層 (DevOps)** | 測試套件影響 CI | 保持 pytest 命令可在 CI 執行 | Windows pass / CI fail | 避免平台限定 event loop 寫法 |
| **12. 成本層 (Cost)** | LLM stub | 不呼叫真實 Gemini/OpenAI | 測試燒 API quota | 保持 fake llm client |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Architecture 層 → 已動 Documentation 層
- [x] 動 Security 層 → 已動 Testing 層
- [x] 動 Performance 層 → 已動 Observability 層
- [x] 動 DevOps 層 → 已動 Testing 層

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_74_PLAN.md` | 可逆 | ✅ 2026-05-16 |
| 修改 `tests/test_dynamic_focus.py` | 可逆 | ✅ 2026-05-16 |
| 視根因修改 `analyzer/dynamic_focus.py` | 可逆 | ✅ 2026-05-16 |
| 追加 `TASK_HISTORY.md` | 半可逆 | 收官時需主公知情 |
| `git push` | 半可逆 | 必須推前再問主公 |

### X2 盲區掃描

主公看不到但會發生的：

- [x] log 副作用：pytest 可能產生 warning / cache，不納入 commit
- [x] 中間檔產出：可能有 `.pytest_cache/`，不 stage
- [x] 系統狀態變更：不改 API key、不改 reports、不改 data 原始資料

### X3 時間敏感性

- 本計畫草案日期：2026-05-15
- 本計畫過期日期：2026-06-15
- 風險記錄帶日期：✅ R-015 來源為 2026-05-14 P72.5

### X4 多角度同行審查

- **主公視角**：主公需要看到這次不是又把失敗標 pre-existing，而是明確以測試全綠作為 Phase 目標。
- **世界頂尖駭客 / 紅隊攻擊者視角**：本 Phase 不新增外部攻擊面，但必須防止測試誤觸真實 LLM、讀本機隱私資料或把 API key 暴露在 log。
- **接手者視角**：半年後接手者要能從 P74 紀錄看懂「單檔 OK / 全套掛」的根因與修法，而不是只看到測試被改掉。
- **X4-J 自動化建議性工具邊界**：N/A。本 Phase 不新增啟發式推薦工具。
- **X4-K 使用者端審查官 / Patric 型人格**：若只報「全綠」但不說全套命令，主公無法判斷測試債是否真的關閉；收官必須列命令與結果。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 全套測試失敗根因不在 `test_dynamic_focus.py`，而是其他測試污染 event loop | 中 | 高 | 測試環境 | 用測試排序 / 相鄰子集定位污染源 |
| R2 | 修測試 fixture 後單檔通過，但 CI 使用不同 pytest async policy | 中 | 中 | DevOps | 避免平台限定寫法，優先用 `asyncio.run` 或 pytest 支援 pattern |
| R3 | production code async 行為真的有缺陷 | 低 | 高 | 代碼可控 | 若確認為 production 根因，補上對應測試再改 |
| R4 | 收官時誤 stage 既有 untracked reports | 低 | 中 | Git 流程 | 每次 stage 前 `git status -sb` + 明列 staged files |

**高風險加權檢查（META4）**：

- 高風險數量：2
- 加權分數：5
- 是否 >= 5 須請示主公：是，本計畫本身即送主公核准後才動工

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1 重現** | 跑單檔、相關子集、全套測試，確認 3 個失敗的實際 trace | 避免憑 handoff 印象修錯 | 貼出失敗 case 名稱與 root-cause 假設 |
| **S2 定位** | 檢查 event loop 使用、mock 邊界、其他測試是否污染 loop | 區分相關性與因果性 | 找到最小可重現命令 |
| **S3 修復** | 依根因最小修改測試或 production code | 清掉 R-015 | 單檔與子集通過 |
| **S4 驗證與收官** | 跑驗收命令、更新 RISK_REGISTRY / TASK_HISTORY / handoff | 防止治理漂移 | Exit Criteria 全部打勾 |

---

## 10. 影響檔案清單

**新增**：

- `docs/PHASE_74_PLAN.md`

**可能修改**：

- `tests/test_dynamic_focus.py`：修正 async test 執行或隔離方式
- `analyzer/dynamic_focus.py`：只有確認 production code 根因時才改
- `docs/RISK_REGISTRY.md`：收官關閉 R-015
- `TASK_HISTORY.md`：追加 P74 無損紀錄
- `NEXT_SESSION_HANDOFF.md`：更新下一窗狀態

**刪除**：

- 無

**影響但未直接修改**：

- pytest 全套測試可信度
- 後續 Phase pre-existing failing test 判定流程

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] 連 3 輪修復仍出現相同 error trace
- [ ] 發現 P72.0-P72.5 的「pre-existing 不阻擋」判定有系統性漏洞
- [ ] 為了通過測試需要修改 production async contract
- [ ] 有任何「我以為...結果不是」事件

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-74-dynamic-focus-tests.md`

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 測試修復本身攻擊面低，但若測試誤觸真實 LLM 或讀本機 history data，可能外洩 prompt、API key 使用狀態與本機資料路徑；最小緩解是全程 mock 外部 I/O。 |
| **X4-B 接手者** | 接手者需要知道失敗是 event loop 隔離、mock 邊界還是 production async contract；P74 必須留下 root cause，不只留下測試綠燈。 |
| **X4-C 災難情境** | 情境：為了快速全綠刪掉 3 個 failing assertions；緩解：禁止刪除原 5 case 語意，必要時只改執行方式。 |
| **X4-D 5 年後** | pytest / asyncio policy 可能更新，計畫要避免綁死舊版 event loop API；修法需使用清楚、可維護的 async 測試模式。 |
| **X4-E 終端 vs IDE** | Codex PowerShell 與 IDE pytest runner 可能使用不同 loop policy；驗收至少保留命令列結果，避免只看 IDE 綠燈。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows event loop 行為可能和 Linux CI 不同；修法不可依賴 Windows 專屬 event loop policy，必要時用平台中立寫法。 |
| **X4-G 主公個人視角** | 主公要的是測試債真關閉，不是又看到 pre-existing；收官必須清楚寫「哪些命令已通過」。 |
| **X4-H 觀測 / 治理** | R-015 已是治理風險，不關閉會削弱未來 Phase 的測試可信度；本 Phase 必須同步 RISK_REGISTRY 狀態。 |
| **X4-I 主公可見性** | 主公看不到 pytest cache、warning、部分測試跳過；收官需攤開是否有 skipped / xfailed / warning。 |
| **X4-J 自動化建議性工具邊界** | N/A。本 Phase 不新增字面比對、啟發式分類、推薦工具或風險打分工具。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 若計畫書未明講「不碰 GHA / reports」，主公可能擔心範圍擴散；本 Phase 明確限縮在 dynamic_focus 測試債。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；目標是關閉 R-015，不順手處理 P70.2 GHA |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；最大安全要求是不觸發真實 LLM、不讀未 mock 的本機資料 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；收官要明列單檔與全套命令結果 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；R-015 來源與關閉條件必須引用 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；測試結果必須列 passed/failed/skipped 數字 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | N/A；不改 UI / 報告視覺 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；LLM 必須 stub，測試不得消耗 API quota |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；PowerShell 設 UTF-8，驗收命令要可複跑 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 這 3 個失敗已被 5 個 Phase 放行，若 P74 再延期就是治理破口 | **S** | 5 | 本 Phase 專責處理，Exit Criteria 要求不再失敗 | 入計畫範圍 |
| 2 | 單檔 OK / 全套掛不一定是 `dynamic_focus.py` 錯，可能是其他測試污染 event loop | **S** | 5 | S1/S2 要找最小重現命令，再決定改哪裡 | 入計畫範圍 |
| 3 | 直接把 `asyncio.get_event_loop().run_until_complete` 換掉可能掩蓋 production async 問題 | A | 5 | 需判定失敗是否來自測試執行方式或 production contract | 入計畫範圍 |
| 4 | 若只跑單檔通過就收官，R-015 的「全套掛」沒有被解 | **S** | 5 | Exit Criteria 明列全套或 Phase 標準測試命令 | 入計畫範圍 |
| 5 | 修改 RISK_REGISTRY / TASK_HISTORY 可能誤 stage 既有 untracked reports | A | N/A | 每次 stage 前檢查 `git status -sb`，只 stage 本 Phase 檔案 | 入計畫範圍 |
| 6 | 全套測試可能因外部 API key 缺失或其他 pre-existing 問題失敗 | A | N/A | 若發生，需列出非 P74 失敗並提供最小替代驗證範圍 | 入計畫範圍 |

---

## 12. 凍結戳記

- **凍結人**：主公核准 + Codex
- **凍結時間**：2026-05-16 00:11 +08:00
- **凍結後變更**：禁止；如需修改，新增 P74 補遺並引用本檔
