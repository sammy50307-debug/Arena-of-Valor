# Phase P95 計畫書 — R-016 Closeout Verification（凍結版）

> 狀態：FROZEN。主公已於 2026-05-24 核准 P95 plan freeze；本 Phase 是 R-016 Zero-Cost Evidence-first Reliability Program 的 closeout verification gate。P95 plan freeze 只凍結驗證與裁決流程，不改 runtime code、不關閉 R-016、不接 provider。P95 verification 必須另行取得主公明確核准後才能執行。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P95 |
| **Phase 名稱** | R-016 Closeout Verification |
| **草案日期** | 2026-05-24 |
| **凍結日期** | 2026-05-24 |
| **影響半徑** | Plan-only 標準（5 檔文件）；verification 預估標準（治理 probes + 文件裁決，不改 runtime） |
| **預估投入時數** | Plan-only 1-2 小時；verification 2-4 小時 |
| **Token budget** | Plan-only 20K-35K；verification 35K-55K |
| **負責模型** | GPT-5.3-Codex 高；若 closeout 證據互相矛盾或連 3 輪無法裁決，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P95 plan | NEW | FROZEN | closeout 驗證流程已固定，但 verification 尚未執行 | 主公回覆「核准 P95 plan freeze」後，本檔建立並同步 handoff / active / risk / history | 主公核准，AI 執行 |
| P95 verification | NOT_STARTED | PENDING_APPROVAL | 只能等主公另行核准，不得關閉 R-016 或修改風險狀態 | 本計畫 lint / governance 檢查通過並 commit 後，由主公決定是否執行 | 主公 |
| R-016 | Open | Open | P95 plan freeze 不裁決風險；verification 後才可 close / downgrade / keep open | P95 verification evidence matrix 完成，且主公核准裁決 | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

凍結 P95 closeout verification 計畫：以最新 Actions / manifest / report / SLO / doctor / cost governance 證據，判斷 R-016 是否可關閉、降級觀察，或必須保持 Open，並把裁決理由寫入風險登記簿與交接文件。

## 2. 觸發背景 (Why Now)

P85-P94 已完成 R-016 修復主線的所有預定能力建設：

| Phase | 已完成能力 | 與 R-016 的關係 |
|---|---|---|
| P86 | model / schedule modernization | 恢復 production report 產出 |
| P87 | report core contract | 讓 report / analysis / manifest health 可觀測 |
| P88 | deterministic local analyzer | provider 失敗時仍保留真實資料 baseline |
| P89 | quality tier / promotion gate | 允許 publishable `production_local_only` |
| P90 | budget ledger / cooldown | 避免 provider 配額失控 |
| P91 | cache / dedupe / Top-N | 降低 LLM calls 與 duplicate 深讀 |
| P92 | enrichment replay queue | local-only 補深讀可追溯且 no-op 可判讀 |
| P93 | provider abstraction | free provider slots disabled-by-default，不接 daily default |
| P94 | doctor / SLO reclassification | 分清 current / historical / residual，避免舊 spike 誤擋 |

目前最新推送 commit 為 `1b919b3 feat: 完成 P94 doctor SLO 重分類`，`main...origin/main` 已同步。R-016 仍 Open，且風險登記簿明確寫入：「若 P86-P95 完成後仍連續無可發布 production tier >= 3 天，或 landing 指向非最新健康報告造成主公誤判，則不得關閉 R-016」。因此 P95 的真正問題不是再新增功能，而是用 evidence-first closeout gate 做最後裁決。

### 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Evidence-first closeout | 拉最新 origin，讀最新 Actions / manifest / report，重跑 SLO / doctor / cost / health 後裁決 | 最符合 P85-P94 路線；可避免誤關 R-016 | 需要完整證據矩陣與人工裁決 | 採用 |
| B. 看到 P94 `issues=[]` 直接關 R-016 | 快速把風險移到 Closed | 忽略 2026-05-24 之後新 evidence；也忽略 landing / current advisory | 不採用 |
| C. 再開 runtime 修補 | 若發現新 blocking，可直接修 | 會把 closeout gate 變新開發，模糊 P95 邊界 | 僅在 verification 發現 blocking 後另開 Phase |
| D. 接 provider smoke 當 closeout | 用 P93 disabled slots 做 live provider test | 可探索備援 provider | 偏離 R-016 closeout，新增 secrets / privacy / cost 風險 | 不採用 |

採用 A。P95 是裁決 gate，不是新功能 Phase。

## 3. Entry Criteria（入口條件）

P95 plan-only 開工前必須全部達成：
- [x] P94 runtime 已 CLOSED 並 push：`1b919b3`。
- [x] `main...origin/main` 已同步，無 tracked local diff。
- [x] R-016 仍位於 `docs/RISK_REGISTRY.md` Open section。
- [x] 主公於 2026-05-24 回覆「核准 P95 plan freeze」。
- [x] 本 Phase 不需要新增 provider secret / PAT / Cloudflare token / Groq key / GitHub Models permission。

P95 verification 開工前尚需另行達成：
- [ ] 本檔由 FROZEN 轉 APPROVED。
- [ ] 主公明確說「核准 P95 verification」或等價指令。
- [ ] verification 前重跑 `git fetch origin`，確認是否有新的 Actions auto-sync commit。
- [ ] 若最新 Actions run 已產出 2026-05-24 或更新日期 report，必須以最新 report date 為 closeout 基準。

## 4. Exit Criteria（退出條件）

P95 plan-only 凍結需全部達成：
- [x] `docs/PHASE_95_PLAN.md` 建立完成。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_95_PLAN.md` 通過。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` / `docs/RISK_REGISTRY.md` / `TASK_HISTORY.md` 同步 P95 FROZEN。
- [x] `py scripts\check_handoff_truth.py --repo-root .` 通過。
- [x] `py scripts\governance_doctor.py --repo-root .` 通過。
- [x] `git diff --check` 通過。
- [x] 不修改 runtime code、workflow、provider flags、secrets 或 data reports。

P95 verification 收官需全部達成：
- [ ] 最新 Actions / manifest / report / artifact evidence matrix 已建立。
- [ ] 最新 report date 的 SLO / doctor / cost / health probes 已跑完。
- [ ] landing 指向最新健康 report，或明確列為 closeout blocker。
- [ ] 所有 current / historical / residual issues 已分類，且是否阻擋 closeout 已明列。
- [ ] 裁決結果明確為 `Close R-016` / `Downgrade R-016` / `Keep R-016 Open` 其一。
- [ ] 若裁決為 close 或 downgrade，需主公明確核准並同步 `docs/RISK_REGISTRY.md`。
- [ ] 若裁決為 keep open，需列出下一個 Phase / risk mitigation。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | Plan-only 1-2 h；verification 2-4 h |
| 預估收益等級 | 高 |
| 收益描述 | 避免 R-016 被過早關閉；也避免已修復的 production pipeline 被舊 advisory 長期誤擋 |
| ROI 結論 | 值得做；P95 是 R-016 長修復主線的正式裁決點 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | Plan-only 不改 code；verification 預設只跑既有 probes，不改 runtime | closeout 過程中順手修 bug，導致 scope 從裁決 gate 變成新開發 | 若發現 blocking，先記錄 blocker 與下一 Phase，不在 P95 plan freeze 階段改 code |
| **2. 邏輯層 (Logic)** | 建立 close / downgrade / keep-open 三分裁決，不把 advisory 自動等同 failure | 把 P94 SLO OK 誤判成 R-016 必然可關，或把 residual advisory 誤判成 blocking | Evidence matrix 必列 latest date、severity、classification、是否阻擋 closeout |
| **4. 測試層 (Testing)** | verification 必跑 SLO / doctor / cost / health；必要時跑 focused/full pytest | 只靠人工看 GitHub UI，漏掉 landing 或 manifest gap | Exit Criteria 明列 probes；結果寫入 TASK_HISTORY |
| **10. 安全層 (Security)** | 不讀 raw queue / raw artifact、不新增 secrets、不接 provider、不輸出 token | closeout 查證時不小心下載 raw artifact 或要求 provider key | 只讀 repo-safe manifest / report metadata / Actions log 摘要 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | P95 定義為 closeout gate，不新增 pipeline 模組 | 把裁決與修復混在同一 Phase，導致 R-016 狀態不可信 | 若有新修補需求，另開 P95.x 或 P96，不在本計畫混做 |
| **5. 資料層 (Data)** | 使用 `data/runs/<date>/run_manifest.json`、report metadata、Actions run id、artifact metadata | GitHub UTC 與 Asia/Taipei 日期錯位造成選錯 report date | 以 manifest / report 的 Taipei date 為準，Actions created_at 只作輔助 |
| **6. 可觀察性層 (Observability)** | closeout matrix 列 SLO / doctor / cost / landing / provider routing | 主公只看到「可關」但不知道哪個 probe 支撐 | 表格需列 command、exit code、核心輸出、closeout impact |
| **7. 韌性層 (Resilience)** | 若最新 run 失敗，R-016 不關閉；若新 evidence 缺失，保持 Open | 在資料不完整時硬關，後續又復發 | Entry 要求先 fetch / refresh latest evidence |
| **13. 可維護性層 (Maintainability)** | 裁決理由寫入 RISK_REGISTRY 與 TASK_HISTORY | 半年後無法知道為何關閉或保留 R-016 | R-016 條目需保留 closeout evidence 與日期 |
| **14. 文件層 (Documentation)** | handoff / active / risk / history 同步 P95 FROZEN | 新視窗仍停在 P94 pushed 後，不知道下一步是 closeout gate | L1 bootstrap 指向 P95 plan，Forbidden Work 明寫不得直接 close |
| **15. 流程層 (Process)** | plan freeze 與 verification approval 分離；push 仍需主公確認 | AI 因 plan 已核准就直接關閉 R-016 | 狀態機寫 P95 verification `PENDING_APPROVAL` |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 多日 probes / pytest | closeout 若跑全 pytest 耗時增加 | 預設先跑治理 probes；full pytest 視風險與變更範圍決定 |
| **9. UX/A11y 層** | landing report 驗證 | landing 指到舊 report 會造成主公誤判 | health check / landing link 必列入 closeout matrix |
| **11. 部署層 (DevOps)** | GitHub Actions / auto-sync | verification 期間遠端再產生新 commit 造成分岔 | 開工前與 push 前都 `git fetch origin`；分岔先同步 A |
| **12. 成本層 (Cost)** | cost/cache governance | CCG005 是 pipeline proxy，可能被誤當 provider billing | P95 只判斷是否阻擋 R-016，不作帳單裁決 |
| **16. 隱私/合規層 (Privacy)** | Actions artifact / enrichment queue | raw artifact 可能含 raw post content | 只看 manifest enrichment snapshot 與 artifact metadata，不下載 raw content 除非另核准 |
| **17. i18n/在地化層** | Asia/Taipei report date | 5/23 UTC / 5/24 Taipei 對不上 | 使用 `build_run_context` / manifest date；文檔列絕對日期 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：P95 verification probes 是 exit criteria。
- [x] 動 Architecture 層 -> 已動 Documentation 層：handoff / active / risk / history 必同步。
- [x] 動 Data 層 -> 已動 Maintainability 層：evidence matrix 與 RISK_REGISTRY 記錄裁決理由。
- [x] 動 Security 層 -> 已動 Testing 層：verification 禁止 raw artifact，probes 只讀 repo-safe metadata。
- [x] 動 Performance 層 -> 已動 Observability 層：probe command / output / closeout impact 必列表。

---

## 7. 跨切面檢查

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 建立 `docs/PHASE_95_PLAN.md` | 可逆 | 主公已核准 plan freeze |
| 同步 handoff / active / risk / TASK_HISTORY 到 P95 FROZEN | 可逆 | 主公已核准 plan freeze |
| P95 verification 裁決 R-016 close / downgrade / keep open | 半可逆，治理影響高 | 尚未執行；需主公另行核准 |
| 下載 raw artifact 或讀 raw queue | 半可逆且隱私風險高 | 本計畫禁止；若必要需另行核准 |
| git push | 半可逆 | 仍需主公明確確認 |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：P95 probes 可能產生很長輸出，需只貼核心欄位到 history。
- [x] 中間檔產出：P95 plan-only 不產生資料檔；verification 也不應修改 `data/reports`。
- [x] 系統狀態變更：R-016 若 close / downgrade 會影響後續優先級，必須主公拍板。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-24
- 本計畫過期日期：2026-06-07；若此日前未執行，需重新 fetch latest Actions evidence 後再驗證。
- 風險記錄帶日期：✅

### X4 多角度同行審查

- **主公視角**：P95 必須回答「這條大 bug 主線能不能正式收官」，而不是再堆一堆新工具或技術名詞。
- **世界頂尖駭客 / 紅隊攻擊者視角**：最大濫用面是把 classification 當遮羞布，將真 failure 包成 historical / residual；緩解是 closeout matrix 必列 raw-free evidence 與 latest date。
- **接手者視角**：接手者要能從 P95 plan 看懂 R-016 的來源、每個 Phase 修了什麼、何種證據允許 close 或 keep open。
- **X4-J 自動化建議性工具邊界**：SLO / doctor / cost governance 都是輔助建議，不是自動裁決；false-negative 可能來自缺 manifest、舊 report metadata、Actions auto-sync 延遲、日期錯位。
- **X4-K 使用者端審查官 / Patric 型人格**：如果文件只寫「pass」，主公會不知道是否真的安全；P95 輸出需用 closeout impact 欄明說阻擋或不阻擋。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 最新 Actions 在 plan freeze 後又產生新 commit，P95 用舊 evidence 裁決 | 中 | 高 | DevOps / 時間敏感 | verification 前必 `git fetch origin`，若分岔先同步 A |
| R2 | 2026-05-23 SLO OK 被誤解成 R-016 可自動關閉 | 中 | 高 | 流程 / 邏輯 | 本計畫明寫 closeout 需最新 evidence matrix 與主公核准 |
| R3 | CCG008 current pending 被忽略，導致 enrichment backlog 沒被裁決 | 中 | 中 | 觀測 | closeout matrix 必列 current / residual issue 與是否阻擋 |
| R4 | landing 指向舊 report，但 doctor/SLO 仍看起來綠 | 低 | 高 | UX / DevOps | 必跑 health / landing check；若 stale，R-016 keep open |
| R5 | closeout 過程中下載 raw artifact 導致 raw post 進 log | 低 | 高 | Security / Privacy | P95 只讀 manifest snapshot / artifact metadata，不讀 raw content |
| R6 | R-016 被關閉後又出現連續無 production | 中 | 高 | 韌性 | 若 close，需保留 reopen trigger；若證據不足就 downgrade 或 keep open |

**高風險加權檢查（META4）**：
- 高風險數量：4 項（R1、R2、R4、R6）
- 加權分數：9 分（高=2，中=1，低=0.5）
- 是否 >= 5 須請示主公：是；P95 verification 與 R-016 裁決都需主公另行核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P95.0 Plan Freeze** | 建立本檔，同步 handoff / active / risk / history | 避免直接關閉 R-016 | phase lint / handoff truth / governance doctor / diff check |
| **P95.1 Evidence Refresh** | `git fetch origin`，確認最新 Actions auto-sync / report date / manifest | 舊 evidence 裁決 | evidence matrix 有 latest commit / latest report date |
| **P95.2 Local Verification** | 跑 SLO / doctor / cost / health / landing probes | 漏掉 current blocker | commands + exit codes + core outputs |
| **P95.3 Closeout Decision** | 判斷 close / downgrade / keep open | 誤關或誤擋 R-016 | 主公可讀裁決表 |
| **P95.4 Documentation Closeout** | 更新 RISK_REGISTRY / TASK_HISTORY / handoff | 裁決理由消失 | governance doctor |
| **P95.5 Commit / Push** | commit closeout；push 前主公確認 | 交接漂移 | git status clean / push success |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_95_PLAN.md`：P95 closeout verification 凍結計畫。

**修改**：
- `NEXT_SESSION_HANDOFF.md`：ACTIVE_BOOTSTRAP 同步 P95 FROZEN。
- `docs/ACTIVE_OPERATION.md`：L2 作戰狀態同步 P95 FROZEN。
- `docs/RISK_REGISTRY.md`：R-016 mitigation 補 P95 FROZEN，但 R-016 仍 Open。
- `TASK_HISTORY.md`：追加 P95 plan freeze 無損紀錄。

**刪除**：
- 無。

**影響但未直接修改**：
- `scripts/slo_checker.py`
- `scripts/system_doctor.py`
- `scripts/cost_cache_governance.py`
- `scripts/check_daily_report_health.py`
- GitHub Actions AoV Daily Monitor run evidence

---

## 11. Forbidden Work（P95 邊界）

- 不修改 `.github/workflows/daily_report.yml`。
- 不修改 `main.py`。
- 不修改 provider router / Gemini client / config / provider env flags。
- 不新增 provider key / PAT / Cloudflare token / Groq key。
- 不加入 GitHub Actions `models: read`。
- 不把 Groq / Cloudflare / GitHub Models 接進 daily default。
- 不讀 raw enrichment queue / raw artifact content，除非主公另行核准。
- 不降低 `SLO001` / `SLO002` / `SLO003` blocking 門檻。
- 不因 P95 plan freeze 關閉 R-016；verification 後仍需主公裁決。
- 不 stage unrelated untracked reports / scratch / backup。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P95 關閉 R-016 後 7 天內又連續無 production。
- [ ] P95 把 current blocker 誤判成 residual / historical。
- [ ] P95 讀 raw artifact 導致 raw content 進 log。
- [ ] P95 因日期錯位看錯 report date。
- [ ] 主公發現 closeout 文件無法支持裁決。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-95-r016-closeout.md`。

---

## Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 最大攻擊面是 closeout 被用來粉飾 production failure；必須保留 latest evidence、exit code、landing target 與 provider disabled truth。 |
| **X4-B 接手者** | 接手者需要從本計畫看懂 R-016 為何仍 Open、P86-P94 解了哪些子問題、P95 如何裁決。 |
| **X4-C 災難情境** | 情境：P95 關閉後隔天 Actions 又失敗；緩解：closeout 必須列 reopen trigger 與最新 evidence date。 |
| **X4-D 5 年後** | 五年後模型與 provider 都會換，但 closeout gate 的價值是留下「何時、用哪些證據、誰核准」的治理脈絡。 |
| **X4-E 終端 vs IDE** | 終端輸出可能只看到 exit code，IDE 可能只看 docs；計畫需讓 JSON / 表格 / history 三端都能追裁決。 |
| **X4-F 跨平台 Win/Mac/Linux** | P95 probes 必須是 Python / git 可跨平台命令，不依賴 PowerShell-only parsing 才能在 Actions 或其他機器重跑。 |
| **X4-G 主公個人視角** | 主公真正要的是知道「修 bug 大計畫能不能結束」；輸出要先給可關、降級或保持 Open 的結論。 |
| **X4-H 觀測 / 治理** | SLO / doctor / cost 都是建議性觀測；P95 必須把 current / historical / residual 與 closeout impact 合在一張表。 |
| **X4-I 主公可見性** | 主公看不到 auto-sync commit 與 Taipei date 對齊細節；P95 要攤開 latest commit、report date、manifest path。 |
| **X4-J 自動化建議性工具邊界** | 自動分類可能漏掉舊 schema 或缺欄位；P95 必須明文說明人工審核仍必要，不能讓工具自動關風險。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 若報告入口仍指舊檔，使用者會以為系統沒更新；landing health 必須和 SLO 一起看。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P95 只做 closeout verification，不做新 runtime。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、secrets、CI/CD | 觸發；禁止 raw artifact、provider secret 與 workflow 改動。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公與接手者是否會誤解裁決 | 觸發；closeout matrix 要明說是否阻擋。 |
| **Jimmy 型文件主筆** | 改 docs / history / handoff 時觸發 | 文字是否可追溯、有來源 | 觸發；RISK_REGISTRY 與 TASK_HISTORY 必須保留 evidence。 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據時觸發 | 定量與定性是否分清楚 | 觸發；SLO / doctor / cost / landing probes 必須分列。 |
| **Oliver 型設計審查** | 涉及 UI / report / landing 時觸發 | 入口是否指最新健康報告 | 觸發；不改 UI，但驗 landing target。 |
| **Penny 型 CFO** | 涉及成本與 LLM calls 時觸發 | proxy 與帳單真相是否混淆 | 觸發；CCG005 不代表 provider billing truth。 |
| **Jason 型執行 / DevOps** | 涉及 Git / Actions / CI 時觸發 | fetch、分岔、rollback、push 邊界 | 觸發；verification 前後都需檢查 origin。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | P95 最容易把「連續幾天看起來 OK」誤當永久修好，關閉 R-016 後復發。 | **S 級** | 0 | closeout matrix 必列 latest evidence date 與 reopen trigger。 | 入計畫 |
| 2 | classification 可能被濫用，把 current failure 標成 historical / residual。 | **S 級** | 0 | P95 必須列 raw-free detail、latest date、exit code，不允許只看 classification。 | 入計畫 |
| 3 | GitHub Actions 在 verification 期間又 auto-sync，導致本地證據落後。 | A 級 | 0 | verification 前與 push 前都 `git fetch origin`；分岔先同步 A。 | 入計畫 |
| 4 | landing 指向舊 report 時，SLO 可能仍看似 OK，但主公看到的是舊畫面。 | A 級 | 0 | landing health check 是 closeout 必備，不可只跑 SLO。 | 入計畫 |
| 5 | raw artifact 可能含 raw post，closeout 查證時若下載會污染 log。 | **S 級** | 0 | plan 禁止讀 raw artifact content，只看 manifest snapshot / artifact metadata。 | 入計畫 |
| 6 | CCG005 是 pipeline proxy，不是 provider 帳單；若混淆會做錯成本決策。 | A 級 | 0 | P95 只判斷是否阻擋 R-016，不裁決 provider billing。 | 入計畫 |
| 7 | 若 P95 發現 blocker 又直接修，Phase 邊界會混亂。 | A 級 | 0 | 發現 blocker 時 keep open，另開下一 Phase 處理。 | 入計畫 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增、不更新 skill。若 verification 階段臨時涉及 skill，需另開補遺並補 STR9 表。

---

## 13. 凍結戳記

- **凍結人**：主公核准，AI 執行。
- **凍結時間**：2026-05-24 Asia/Taipei。
- **凍結後變更**：禁止；如需修改，新增章節「Phase P95.x 補遺」並引用本檔。

---

## 14. Phase P95.1 Verification Closeout 補遺（2026-05-24）

> 本節為凍結後補遺，不改動上方 frozen plan。主公於 2026-05-24 回覆「完成後直接P95 verification 動工」，視為 P95 verification 開工核准。AI 依本計畫執行 evidence refresh / local verification / closeout decision / documentation closeout，未修改 runtime code、workflow、provider flags、secrets 或 data reports。

### 14.1 Evidence Refresh Matrix

| 證據 | 結果 | Closeout 影響 |
|---|---|---|
| `git fetch origin` | 2026-05-24 16:40 Asia/Taipei 執行；`main...origin/main` 同步在 `8c1fa99` | 無分岔，可驗證 P95 plan freeze 後狀態 |
| 最新 pushed commit | `8c1fa99 docs: 凍結 P95 closeout verification 計畫` | P95 plan 已在雲端；verification 文檔尚待 commit / push |
| 最新 AoV Daily Monitor run | GitHub API 顯示最新 run `26330077260`，event=`schedule`，status=`completed`，conclusion=`success`，created_at=`2026-05-23T10:12:57Z`，updated_at=`2026-05-23T10:15:35Z` | 雲端每日監控最新成功，但不是 2026-05-24 run |
| 最新 run head SHA | `b649dc4ddf3870352c72d0224e5135975d9af97b` | 此 run 早於 P94 runtime commit `1b919b3` 與 P95 plan commit `8c1fa99`，不能作為 post-P94 runtime closeout 的最終雲端證據 |
| Artifact metadata | run `26330077260` 有 artifact `enrichment-queue-26330077260`，id=`7176197190`，size=`1406` bytes，expired=`false`，expires_at=`2026-05-26T10:15:31Z` | 只讀 metadata，未下載 raw artifact，符合 security / privacy 邊界 |
| 最新 repo run manifest | `data/runs/2026-05-23/run_manifest.json` | 目前最新可驗證 report date 是 2026-05-23 |
| 2026-05-24 run | GitHub API latest 5 runs 中沒有 2026-05-24 run | 不視為 pipeline failure，但阻擋 `Close R-016` 的最終裁決 |

### 14.2 Local Verification Matrix

| Probe | Command | Exit | 核心輸出 | Closeout 影響 |
|---|---|---|---|---|
| SLO | `py scripts\slo_checker.py --repo-root . --date 2026-05-23 --window-days 5 --json` | 0 | `classification=current`、`issues=[]`、`consecutive_no_production=0`、`missing_manifest_count=0`、`doctor_blocking_days=0` | 不阻擋；production SLO 五日窗已恢復 |
| System doctor | `py scripts\system_doctor.py --repo-root . --date 2026-05-23 --profile ci --require-production` | 0 | DOC007 current advisory；DOC018 residual；DOC019 residual；無 blocking | 不阻擋；仍保留 source coverage 與 local-only/enrichment 觀察 |
| Cost/cache governance | `py scripts\cost_cache_governance.py --repo-root . --date 2026-05-23 --window-days 3 --json` | 0 | CCG005 historical；CCG007 residual；CCG008 current for 2026-05-22 pending eligible=2；CCG008 residual no_eligible for 2026-05-23 | 阻擋直接 Close；需要 post-P94 cloud run 或 replay/next run 證明 pending 已消化或可接受 |
| Health by date | `py scripts\check_daily_report_health.py --repo-root . --date 2026-05-23 --expected-mode production` | 0 | canonical report PASS；metadata mode production；quality_tier production_local_only；core contract PASS；landing main link PASS | 不阻擋；landing 指向最新健康 report |
| Latest production landing | `py scripts\check_daily_report_health.py --repo-root . --use-latest-production --expected-mode production` | 0 | 2026-05-24 執行時解析到 `data/reports/aov_report_2026-05-23.html`，mode=production | 不阻擋；首頁未 stale |
| Focused tests | `py -m pytest -q tests\test_slo_checker.py tests\test_system_doctor.py tests\test_cost_cache_governance.py tests\test_daily_report_health.py` | 0 | `46 passed` | probe test surface 未退化 |
| Full pytest | `py -m pytest -q` | 0 | `288 passed` | repo baseline 未退化 |

### 14.3 Raw-free Manifest Snapshot

| 欄位 | 2026-05-23 manifest 值 |
|---|---|
| mode / status | `production` / `ok` |
| publish_eligible | `true` |
| quality | tier=`production_local_only`、analysis_source=`mixed`、llm_coverage=`partial`、core_contract=`pass` |
| budget | decision=`call_llm`、decision_reason=`budget_available`、llm_calls_used=`14` |
| selection | total_input_posts=`19`、llm_selected_posts=`12`、local_only_posts=`7`、duplicate_posts=`7`、max_llm_items=`15` |
| enrichment | queue_available=`true`、replay_status=`no_eligible`、eligible_posts=`0`、skipped_posts=`7`、enriched_posts=`0` |
| provider.routing | route_status=`router_disabled_legacy_default`、router_enabled=`false`、enabled_slots=`0`、attempts=`0`、raw_payload_logging=`false`、secrets_logged=`false` |

### 14.4 Closeout Decision

| 選項 | 裁決 | 理由 |
|---|---|---|
| Close R-016 | 不採用 | 缺 post-P94 runtime 的雲端 Daily Monitor run；最新 run head SHA 是 pre-P94 `b649dc4`；且 CCG008 仍有 2026-05-22 current pending evidence |
| Downgrade R-016 | 暫不採用 | production SLO / landing 已健康，但 current advisory 尚未完成 post-P94 cloud evidence 驗證；降級仍需主公另行核准 |
| Keep R-016 Open | **採用** | 最保守且符合 P95 風險門檻；避免把舊雲端 run 與 current advisory 誤判成可收官 |

**P95 verification 結論**：`Keep R-016 Open`。P95 沒有發現 production/landing current blocking；真正阻擋 closeout 的是「缺 post-P94 cloud run」與「CCG008 current pending 尚未由後續 run / replay 證明消化」。

### 14.5 下一步 / Reopen Trigger

- 下一步：手動 dispatch 一次 AoV Daily Monitor，確認新的 run head SHA 至少包含 `1b919b3`（P94 runtime）與最好包含 `8c1fa99`（P95 plan），待 run 完成後讀 manifest / artifact metadata / SLO / doctor / cost / health。
- 若 post-P94 run success，且 SLO current clear、landing PASS、provider routing 仍 disabled、CCG008 不再 current blocking，才可重新提交 `Downgrade R-016` 或 `Close R-016` 給主公裁決。
- 若 post-P94 run failed、無 production、landing stale，或 CCG008 current pending 持續，R-016 維持 Open 並另開 P96 / P95.x mitigation。
