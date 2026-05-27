# Phase P100 計畫書 — Root Legacy / Debug Debris Quarantine Plan（FROZEN）

> 狀態：FROZEN。主公於 2026-05-27 要求「開 P100 Root Legacy / Debug Debris Quarantine Plan」，並已核准 `P100 plan freeze`。本 Phase 只凍結根目錄 legacy/debug debris 的 quarantine 計畫；不刪檔、不搬檔、不 rename、不改 `.gitignore`、不改 runtime code、不改 GitHub Actions / Pages、不清理既有 tracked root files。進入 runtime 前仍需主公另行核准。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P100 |
| **Phase 名稱** | Root Legacy / Debug Debris Quarantine Plan |
| **建立日期** | 2026-05-27 |
| **所屬 Program** | R-019 Project Self-Optimization Flywheel Program |
| **新風險帳** | R-021 Root legacy / debug debris quarantine false deletion |
| **影響半徑** | 標準（plan 5 檔；future runtime 可能 3-6 檔，仍需另核准） |
| **預估投入時數** | plan 0.8h；runtime 2-3h |
| **Token budget** | plan 16K；runtime 35K |
| **負責模型** | GPT-5.3-Codex（metadata / docs / quarantine plan）；若涉及刪檔、搬檔或 rename，升 GPT-5.5 高並另開 runtime gate |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P99 runtime | CLOSED / pushed | Reference only | P99 checker 作為 P100 的 commit hygiene guard，不再修改 | `b88a846` 已推送 | AI / 主公 |
| P100 plan | DRAFT | FROZEN | quarantine plan 已凍結，尚不可實作 inventory / cleanup | 主公核准 `P100 plan freeze` | 主公 / AI |
| P100 runtime | Not started | Pending approval | 未來可新增 inventory / reference check / quarantine manifest，但不可自動刪移 | 主公核准 P100 plan freeze 後另行核准 runtime | 主公 |
| Cleanup actions | Blocked | Blocked | 任何 delete / move / rename 都不屬 P100 plan draft | 需 future runtime 明列 rollback 並由主公逐項核准 | 主公 |

---

## 1. 目標 (Objective)

把根目錄 tracked debug logs、diff outputs、loose preview scripts、疑似 legacy helper、escaped path hygiene 風險，轉成一套可審核的 quarantine plan。P100 的目標不是把根目錄立刻清空，而是讓 future runtime 能先證明「哪些檔案被引用、哪些只是歷史證據、哪些可以 quarantine、哪些必須保留」。

## 2. 觸發背景 (Why Now)

P98 audit 顯示核心 runtime 很小，但根目錄有一批 legacy/debug debris 會干擾接手判斷。P99 已建立 generated artifact hygiene guard，下一個最高 ROI 候選就是 P100 root legacy/debug debris。

| Evidence | 數值 / 現象 | P100 要處理的問題 |
|---|---|---|
| tracked root files | 目前 root tracked file 約 56 個 | 根目錄混有 product entry、docs、debug outputs、old helper scripts |
| root debug outputs | `run_log.txt` 154.1 KB、`full_diff.txt` 74.9 KB、`diff_result.txt` 53.9 KB、`output.log` 15.8 KB | 容易被 AI 誤讀成最新真相 |
| zero / tiny debug files | `err.log`、`err.txt`、`error.txt`、`out.txt`、`ver.txt`、`debug_output.txt` 等 | 多半是臨時輸出，但不能憑檔名直接刪 |
| loose scripts | `preview_report_script.py`、`generate_final_demo.py`、`force_gen.py`、`quick_demo.py`、`patch.py` 等 | 可能是舊流程，也可能仍被文件引用 |
| P99 policy | root debug outputs 已列為 quarantine candidate | P100 需規劃如何 reference check 與 rollback |

## 2.1 問題定義

P100 解的是「root-level legacy/debug debris boundary」問題，不是 product bug、網站內容、generated reports、skill layer 或 deployment 問題。

| 不解的事 | 原因 | 轉交 |
|---|---|---|
| 直接刪除 root debug files | 可能仍是歷史證據或被 docs 引用 | P100 runtime 需 reference check 後逐項裁決 |
| 搬移 scripts 到 archive | move / rename 會改 git history 與引用路徑 | future runtime 另核准 |
| 改 `.gitignore` | 可能影響 production commit 行為 | P100 plan 禁止 |
| 清理 `data/reports` / `ui_previews` | 已由 P99 policy 管 commit hygiene，cleanup 另開 | P101+ |
| 整理 `.agents` / skills | skill-layer hygiene | P102 |
| 修芽芽 / 舊文章內容 | content trust / freshness | R-017 / P104 |

## 2.2 方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 直接刪 root debug logs | 立刻降噪 | 快 | 可能刪掉仍有價值的 evidence；不可逆風險高 | 不採用 |
| B. 直接搬到 `archive/` | 保留但降低 root 噪音 | 可回溯 | move/rename 仍會破壞引用，且新增 archive policy | P100 plan 不採用 |
| C. Reference-first quarantine plan | 先列 inventory、引用檢查、分類、rollback，再 future runtime | 最保守，能降低誤刪 | 需要多一步 | 採用 |
| D. Strict root allowlist gate | 只允許少數 root 檔 | root 最乾淨 | false positive 高，會卡住正常治理檔 | P100 不採用 |

---

## 3. Entry Criteria（入口條件）

- [x] P99 runtime 已完成並推送：`b88a846` 已在 origin/main。
- [x] P99 policy 已將 root debug outputs 標為 `quarantine candidate`，但明確不 cleanup。
- [x] P98 audit 排序指出 P100 是 P99 後的第二高 ROI 候選。
- [x] 主公已要求：`開 P100 Root Legacy / Debug Debris Quarantine Plan`。
- [x] P100 plan 明確限制為 plan，不執行刪檔 / 搬檔 / rename / `.gitignore` / runtime code 改動。
- [x] P100 plan draft 已推送：`e92ad76` 已在 origin/main。
- [x] 主公核准 `P100 plan freeze`。

## 4. Exit Criteria（退出條件）

P100 plan draft 退出條件：
- [x] `docs/PHASE_100_PLAN.md` 建立並通過 `scripts/lint_phase_plan.py`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 R-019 / R-021 / P100 DRAFT。
- [x] `docs/RISK_REGISTRY.md` 建立 R-021 Open 風險。
- [x] `TASK_HISTORY.md` 追加 P100 plan draft 物理真相。
- [x] `git diff --check`、handoff truth、governance doctor、P99 artifact hygiene staged check 通過。

P100 plan freeze 退出條件：
- [x] 主公核准 `P100 plan freeze`。
- [x] `docs/PHASE_100_PLAN.md` 狀態改為 FROZEN。
- [x] handoff / active / risk / history 同步 P100 FROZEN。
- [x] 仍未執行任何 delete / move / rename / cleanup。

P100 runtime 未來退出條件：
- [ ] 產出 root legacy inventory：root file / type / size / last-touch evidence / category。
- [ ] 產出 reference check：`rg` 搜尋每個 candidate 是否被 docs/scripts/workflows/imports 引用。
- [ ] 產出 quarantine decision table：keep / document-only / archive-candidate / delete-candidate / requires主公裁決。
- [ ] 若有 move/delete proposal，必須列 rollback command、affected references、主公逐項核准。
- [ ] 若新增 checker，先 advisory-only，不升 strict gate。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 2-3h |
| 預估收益等級 | 高 |
| 收益描述 | 降低根目錄噪音，避免 AI 把舊 debug logs / diff outputs / loose scripts 誤當最新真相 |
| ROI 結論 | 值得做；先 reference-first quarantine plan，再決定是否 runtime cleanup |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | plan 不改 runtime code；future runtime 可新增 metadata/checker script | loose scripts 可能仍被使用 | runtime 前先 reference check，不憑檔名裁決 |
| **2. 邏輯層 (Logic)** | 建 root classification：keep / evidence / debug output / loose script / quarantine candidate / decision required | 分類錯造成誤刪 | plan only；cleanup 需 future approval |
| **4. 測試層 (Testing)** | future runtime 若新增 checker，必補 fixture tests | checker 太吵或漏報 | advisory-first，positive/negative case 都要有 |
| **10. 安全層 (Security)** | 不讀 raw log 內容，只先用 metadata / path / references | debug log 可能含敏感內容 | P100 plan 不輸出 raw content；runtime 如需讀內容另行裁決 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 根目錄用途分層：entry/docs/config/assets/debug/legacy | 把 root cleanup 混進 product architecture | P100 只做 quarantine planning |
| **5. 資料層 (Data)** | debug outputs 視為 evidence candidate，不直接刪 | 誤刪歷史排錯證據 | 先記錄物理真相與 reference |
| **6. 可觀察性層 (Observability)** | future inventory 要列 path、size、category、reason、reference result | 接手者不知道為何保留/移除 | decision table |
| **7. 韌性層 (Resilience)** | move/delete 必須 rollback-first | cleanup 破壞流程 | future runtime 逐項核准 |
| **13. 可維護性層 (Maintainability)** | 降低 root 噪音，保留真正入口 | 過度整理造成陌生路徑 | keep list 先明確 |
| **14. 文件層 (Documentation)** | P100 plan / risk / history 同步 | future AI 又忘了 P100 不可 cleanup | handoff anti-drift 明列 forbidden work |
| **15. 流程層 (Process)** | Plan -> freeze -> runtime inventory -> decision -> optional cleanup | plan 偷渡 cleanup | State machine 與 forbidden work |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | runtime reference scan 可能掃大量檔 | 使用 `rg` path/reference scan，不讀大檔內容 | 慢或 token 高 | metadata-first，必要時限制 candidate set |
| **9. UX/A11y 層** | N/A | 不改前台 UI | 誤以為修網站 | 明列非網站 phase |
| **11. 部署層 (DevOps)** | root files 可能含 `index.html` / config / Actions references | 不改 deploy files | Pages / GHA 破壞 | P100 plan 禁止 runtime deploy change |
| **12. 成本層 (Cost)** | 降低 AI 誤讀與 token 噪音 | future windows 少讀 debug debris | 規則太重 | 只處理 root high-signal candidates |
| **16. 隱私/合規層 (Privacy)** | logs 可能含 raw output | plan 不讀 raw content | 敏感資訊暴露 | metadata-only；內容讀取另開裁決 |
| **17. i18n/在地化層** | escaped / quoted path 風險 | future inventory normalize path | 跨平台路徑誤判 | 使用 `git ls-files -z` 或 escaped-safe parsing |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：future runtime 若新增 checker，必補 tests。
- [x] 動 Data 層 -> 已動 Documentation 層：debug outputs 先視為 evidence candidate。
- [x] 動 DevOps 層 -> 已動 Process 層：不改 Actions / Pages / `.gitignore`。
- [x] 動 Security 層 -> 已動 Observability 層：metadata-only output。

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_100_PLAN.md` | 可逆 | 主公已要求開 plan |
| 更新 handoff / active / risk / history | 可逆 | 本次只同步 FROZEN |
| future 新增 inventory / checker / manifest | 可逆 | runtime 需另核准 |
| 移動 root files | 半可逆 | P100 plan 禁止 |
| 刪除 root files | 不可逆到半可逆 | P100 plan 禁止；future 需逐項核准 |

### X2 盲區掃描

- [x] `main.py`、`config.py`、`index.html`、`requirements.txt` 等 root files 可能是真入口，不是 debris。
- [x] `run_log.txt` / diff outputs 可能含歷史排錯證據，不可憑檔名刪。
- [x] loose scripts 可能被 docs、TASK_HISTORY、舊 workflow 或人工流程引用。
- [x] root 大圖 `yaya_bg.png` 是 static asset 戰線，不混入 P100 cleanup。
- [x] P99 checker 只提醒 staged risky paths，不等於 P100 cleanup 已核准。

### X3 時間敏感性

- 本計畫建立日期：2026-05-27。
- 本計畫過期日期：2026-06-03；若一週內未 freeze，需重新確認 root tracked file inventory。
- R-016 monitoring 至 2026-06-01；R-017 monitoring 至 2026-06-02。

### X4 多角度同行審查

- **主公視角**：P100 要讓根目錄變得可理解，但不能用「清乾淨」冒充安全。
- **紅隊 / 技術長視角**：最大風險是刪掉仍可證明 production/debug history 的檔案；必須 reference-first。
- **接手者視角**：需要一張表知道哪些 root files 是入口、哪些是 legacy、哪些待 quarantine。
- **X4-J 自動化工具邊界**：任何 checker 只能 advisory；不得 auto move/delete。
- **X4-K 使用者端審查官**：P100 不會直接改善網站畫面或內容，它改善的是 repo 接手與 AI 判斷品質。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 誤刪仍被引用的 root script / log / config | 中 | 高 | 資料 / 流程 | P100 plan 禁止刪；runtime reference-first |
| R2 | 把 product entry 誤列 debris | 低 | 高 | 架構 / 部署 | keep list 明列，任何 entry 需主公裁決 |
| R3 | 讀 raw debug log 導致敏感內容外洩 | 低 | 高 | 安全 / 隱私 | plan metadata-only；內容讀取另行核准 |
| R4 | scope 漂移成 generated report cleanup 或 skill cleanup | 中 | 中 | Scope | reports 留 P99/P101+；skills 留 P102 |
| R5 | quarantine plan 太複雜，成本高於收益 | 中 | 中 | 流程 | 先只處理 root high-signal candidates |

**高風險加權檢查（META4）**：
- 高風險數量：3 項。
- 加權分數：7 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；P100 plan 可建立，但 runtime / cleanup 需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 Plan / Boundary Lock** | 建立 P100 plan、R-021、handoff、active、history | 避免 plan 變 cleanup | plan lint / governance checks PASS |
| **S1 Root Inventory Design** | 定義 root file classes 與 candidate set | 根目錄靠印象判斷 | inventory spec |
| **S2 Reference Check Design** | 設計 `rg`/import/workflow/doc reference scan | 誤刪仍被引用檔案 | reference result table |
| **S3 Quarantine Decision Table（future）** | keep / document-only / archive-candidate / delete-candidate / decision-required | cleanup 無裁決依據 | decision table |
| **S4 Optional Advisory Guard（future）** | 若需要，擴充 P99 checker 或新增 root checker | root debris 復發 | tests + advisory output |

---

## 10. 影響檔案清單

**P100 plan draft 新增**：
- `docs/PHASE_100_PLAN.md`

**P100 plan draft 修改**：
- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`

**P100 future runtime 候選，不在 plan draft 實作**：
- `docs/ROOT_LEGACY_QUARANTINE.md`
- `scripts/check_root_legacy_hygiene.py`（只有需要 advisory checker 時）
- `tests/test_root_legacy_hygiene.py`（只有新增 checker 時）

**明確不修改**：
- `.gitignore`
- `.github/workflows/*`
- root tracked files such as `run_log.txt`, `full_diff.txt`, `diff_result.txt`, `output.log`
- runtime code under `analyzer/`, `reporter/`, `scrapers/`
- `data/reports/*`
- `ui_previews/*`
- `scratch/*`

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] P100 plan 或 runtime 未經逐項核准刪除 / 移動 / rename root files。
- [ ] P100 改了 `.gitignore` 或 GitHub Actions。
- [ ] P100 checker 讀出 raw log / debug content。
- [ ] P100 把 production entry / deployment artifact 誤標為可刪。
- [ ] 有任何「我以為這只是 debug，結果是 production truth」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-100-root-legacy-quarantine.md`

---

## 12. Forbidden Work（P100 邊界）

- 不刪檔。
- 不搬檔。
- 不 rename。
- 不改 `.gitignore`。
- 不改 runtime code。
- 不改 GitHub Actions / Pages deployment。
- 不 stage unrelated untracked reports、scratch、raw artifact、舊 untracked skill 暫存。
- 不導入 RTK 或新工具。
- 不把 advisory guard 升 strict gate。
- 不把 root static asset / generated reports / skill layer cleanup 混進 P100。

---

## Pre-flight 多視角體檢（M1+M1.5+M2）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | debug logs 可能含敏感內容；P100 plan 不讀 raw content。 |
| **X4-B 接手者** | 接手者需要知道 root 哪些是入口，哪些只是舊 debris。 |
| **X4-C 災難情境** | 災難是刪掉仍被 docs/workflow/scripts 引用的檔案；runtime 必須 reference-first。 |
| **X4-D 5 年後** | 五年後需要 quarantine decision table，而不是對話裡一句「看起來可刪」。 |
| **X4-E 終端 vs IDE** | 終端適合 metadata inventory / `rg` reference scan；IDE 適合看 decision table。 |
| **X4-F 跨平台 Win/Mac/Linux** | root path 與 escaped path 需 normalize，避免 Windows-only 判斷。 |
| **X4-G 主公個人視角** | 主公不需要知道每個 root 檔歷史；AI 要把可留/可隔離/需裁決講清楚。 |
| **X4-H 觀測 / 治理** | P100 成功訊號是 root candidates 有分類與引用證據，不是刪多少檔。 |
| **X4-I 主公可見性** | 主公看不到 AI 是否讀錯 root debug logs；P100 要把 root debris 降噪。 |
| **X4-J 自動化建議性工具邊界** | guard 只能 advisory；不能 auto move/delete。 |
| **X4-K 使用者端審查官** | P100 不修網站內容；它修 repo 接手與 AI 判斷品質。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步 | 觸發；P100 只開 quarantine plan。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | raw log / irreversible cleanup | 觸發；metadata-only，不刪檔。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公是否誤解效果 | 觸發；P100 不修前台內容。 |
| **Jimmy 型文件主筆** | 改 docs / handoff 時觸發 | 文件可追溯 | 觸發；handoff / active / risk / history 同步 FROZEN。 |
| **Marcus 型數據分析師** | 涉及 inventory 時觸發 | root file metadata | 觸發；使用 metadata，不讀 raw content。 |
| **Oliver 型設計審查** | 涉及 root static asset 時觸發 | `yaya_bg.png` 是否混線 | 條件觸發；P100 不處理 static asset cleanup。 |
| **Penny 型 CFO** | 涉及成本時觸發 | 降低返工成本 | 觸發；root 降噪可減少 AI 誤讀。 |
| **Jason 型執行 / DevOps** | 涉及 root/deploy 時觸發 | Pages / Actions / entry files | 觸發；P100 不改 deploy。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | P100 可能變成「順手刪一堆 root 檔」。 | **S 級** | 0 | plan 明列不刪、不移、不 rename；runtime 另核准。 | 入計畫範圍 |
| 2 | `main.py`、`config.py`、`index.html` 被誤判成 legacy debris。 | **S 級** | 0 | keep list 與 decision-required 類別，entry files 不進 cleanup。 | 入 RISK_REGISTRY |
| 3 | debug logs 可能含敏感資訊，讀內容會外洩。 | **S 級** | 0 | plan metadata-only；內容讀取另行裁決。 | 入 RISK_REGISTRY |
| 4 | loose scripts 名稱像舊檔，但可能仍被 docs 或人工流程引用。 | A 級 | 0 | runtime 必須 reference scan。 | 入計畫範圍 |
| 5 | root 大圖也很大，為什麼不一起處理？ | B 級 | 0 | static asset canonical source 是另一戰線，P100 不混線。 | 入計畫範圍 |
| 6 | 不刪檔是不是沒效果？ | B 級 | 0 | P100 plan 先讓 future cleanup 有證據與 rollback，降低誤刪。 | 入計畫範圍 |
| 7 | P100 會不會跟 P99 checker 重複？ | A 級 | 0 | P99 是 commit hygiene；P100 是 root quarantine decision。 | 入計畫範圍 |
