# Phase P95.1 計畫書 — Enrichment Pending Closure（凍結版）

> 狀態：FROZEN。主公已於 2026-05-24 核准 P95.1 plan freeze。本 Phase 只處理 P95 closeout 後殘留的 `CCG008 current pending` 線頭：2026-05-22 enrichment queue 有 2 筆 eligible pending，而 2026-05-23 / 2026-05-24 已連續 `no_eligible`。P95.1 的目標是用可追溯證據把 pending 關乾淨，不靠時間自然掉出 window 來假裝完美。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P95.1 |
| **Phase 名稱** | Enrichment Pending Closure |
| **凍結日期** | 2026-05-24 |
| **影響半徑** | 標準 Phase：plan-only 5 檔文件；runtime 預估 2-4 檔程式/測試 + 可選本地 raw-free/ignored replay 產物 |
| **預估投入時數** | Plan-only 1-2 小時；runtime 2-4 小時 |
| **Token budget** | Plan-only 20K-35K；runtime 35K-60K |
| **負責模型** | GPT-5.3-Codex 高；若 artifact/replay 判讀連 3 輪矛盾，提醒主公切 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P95.1 plan | NEW | FROZEN | pending closure 流程已固定，但 artifact access / runtime 尚未執行 | 主公回覆「核准 P95.1 plan freeze」 | 主公核准，AI 執行 |
| P95.1 runtime | NOT_STARTED | PENDING_APPROVAL | 需主公另行核准才能下載或讀取 2026-05-22 enrichment artifact / raw queue | plan lint / governance 檢查通過並 commit 後 | 主公 |
| R-016 | Open | Open | plan freeze 不裁決 R-016；runtime 後才可 close / downgrade / keep open | P95.1 evidence matrix 完成且主公核准裁決 | 主公與 AI 共同裁決 |

---

## 1. 目標 (Objective)

把 P95 closeout 後殘留的 `CCG008 current pending` 做到可證明收斂：

- 針對 2026-05-22 enrichment queue 的 `pending eligible=2` 做 dry-run 判讀。
- 若 dry-run 確認可補深讀，在主公核准 runtime 後用既有 budget guard apply replay。
- 若 dry-run 顯示不可 replay 或不應 replay，記錄明確原因，不留下「未知 pending」。
- 修正或補強 cost/cache governance，使「舊 pending 已被後續 no_eligible / resolved evidence 覆蓋」不再被誤標為 blocking closeout 的 current。
- 重跑 SLO / doctor / cost / health / tests，提交 R-016 的 close / downgrade / keep-open 裁決。

## 2. 觸發背景 (Why Now)

P95 第一輪 verification 採保守裁決 `Keep R-016 Open`，原因是缺 post-P94 cloud run 且 `CCG008 current pending` 仍指向 2026-05-22。

之後主公手動 dispatch post-P94 / post-P95 Daily Monitor，已補齊雲端證據：

| 證據 | 結果 |
|---|---|
| 最新成功 run | `26356870400` |
| run conclusion | `success` |
| run head SHA | `8151b2bea8209ff748daa20c4898ef7566726024` |
| auto-sync commit | `65b9f92 docs: 戰略報告自動同步 2026-05-24 08:55:48 [mode:production l1:0 l2:8 hit:62%]` |
| 2026-05-24 SLO | `classification=current`、`issues=[]`、`doctor_blocking_days=0` |
| 2026-05-24 doctor | 無 blocking；DOC007 current advisory；DOC018 / DOC019 residual |
| 2026-05-24 health | production report / landing / quality / core contract 全 PASS |
| 2026-05-24 provider routing | `router_disabled_legacy_default`、`router_enabled=false`、`enabled_slots=0`、`attempts=0` |
| 2026-05-24 cost 3-day | CCG007 residual；CCG008 current for 2026-05-22 pending；CCG008 residual for 2026-05-23/24 no_eligible |
| 2026-05-24 cost 2-day | 只剩 CCG007 residual 與 CCG008 residual |

因此真正問題已從「production 是否恢復」縮小成「5/22 pending 線頭是否已被真實處理或可被治理分類正確關閉」。

### 2.1 方案比較與採用決策

| 方案 | 作法 | 優點 | 缺點 | 決策 |
|---|---|---|---|---|
| A. Artifact dry-run -> necessary apply -> governance classification | 先核准 artifact access，對 5/22 queue dry-run；必要時 apply replay；再補 cost governance 測試/分類 | 最完整；可處理真 pending，也避免靠時間消失 | 需處理 raw artifact privacy 邊界 | 採用 |
| B. 等 5/22 掉出 3-day window | 不改任何東西，等 5/25 cost 3-day 自然不含 5/22 | 最快 | 粉飾風險高；沒有處理 pending 根因 | 不採用 |
| C. 只改 `cost_cache_governance.py` 把舊 pending 標 historical | 小改、低成本 | 若 queue 真的可 replay，會變成治理遮羞布 | 不採用 |
| D. 不 dry-run 直接 apply replay | 可能快速補深讀 | 可能花 LLM budget；可能把 raw artifact 處理邊界跳過 | 不採用 |

採用 A。P95.1 必須先判斷真資料，再改治理分類，不反過來。

---

## 3. Entry Criteria（入口條件）

P95.1 plan-only 凍結需全部達成：

- [x] P95 verification docs 已 push：`8151b2b`。
- [x] post-P95 AoV Daily Monitor 已成功：run `26356870400`。
- [x] auto-sync production commit 已同步：`65b9f92`。
- [x] 2026-05-24 SLO / doctor / health 顯示 production pipeline 健康。
- [x] `CCG008 current` 仍由 2026-05-22 pending 造成，且 2026-05-23 / 2026-05-24 皆為 `no_eligible`。
- [x] 主公於 2026-05-24 回覆「核准 P95.1 plan freeze」。

P95.1 runtime 開工前尚需另行達成：

- [ ] 主公明確說「核准 P95.1 runtime」或等價指令。
- [ ] 主公另行核准讀取 / 下載 2026-05-22 enrichment artifact 或 raw queue，因 artifact 可能含 raw post content。
- [ ] `git fetch origin` 後確認是否有新的 Actions auto-sync commit。
- [ ] 若 artifact 已過期，改走「artifact unavailable」證據路徑，不硬造 replay 結果。
- [ ] 先 dry-run，不直接 apply。

## 4. Exit Criteria（退出條件）

P95.1 plan-only 凍結需全部達成：

- [x] `docs/PHASE_95_1_PLAN.md` 建立完成。
- [x] `py scripts\lint_phase_plan.py docs\PHASE_95_1_PLAN.md` 通過。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` / `docs/RISK_REGISTRY.md` / `TASK_HISTORY.md` 同步 P95.1 FROZEN。
- [x] `py scripts\check_handoff_truth.py --repo-root .` 通過。
- [x] `py scripts\governance_doctor.py --repo-root .` 通過。
- [x] `git diff --check` 通過。
- [x] 不下載 artifact、不讀 raw queue、不改 runtime、不改 workflow、不改 provider。

P95.1 runtime 收官需全部達成：

- [ ] 2026-05-22 pending queue 已被 dry-run 判讀。
- [ ] 若可 replay，已在主公核准後 apply，且 manifest snapshot 變成 `completed` / `partial` / `no_eligible` / `skipped_budget` 之一。
- [ ] 若不可 replay，有明確原因：artifact expired / queue unavailable / budget skip / invalid queue / duplicate-only 等。
- [ ] `CCG008 current pending` 不再阻擋最新日 closeout；若仍 current，明確列為 R-016 keep-open blocker。
- [ ] SLO / doctor / cost / health / focused tests / full pytest 已重跑。
- [ ] R-016 裁決明確為 `Close R-016` / `Downgrade R-016` / `Keep R-016 Open` 其一。
- [ ] 文件與 history 更新，commit；push 仍需主公確認。

---

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | Plan-only 1-2 h；runtime 2-4 h |
| 預估收益等級 | 高 |
| 收益描述 | 避免 R-016 closeout 靠時間衰減掩蓋 pending；讓「修 bug 大計畫」用真正完整證據收官 |
| ROI 結論 | 值得做；P95.1 是 R-016 完美 closeout 前的最後治理補牙 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | plan-only 不改 code；runtime 僅允許小範圍修 `cost_cache_governance.py` 與 tests | 借 P95.1 順手重構 cost governance 或 replay flow | 每一行改動都必須追到 CCG008 pending closure |
| **2. 邏輯層 (Logic)** | 先判讀 5/22 queue，再決定分類；不讓後續 no_eligible 自動粉飾 pending | 把治理分類改成「看起來綠」但 pending 未處理 | runtime exit criteria 要求 dry-run 證據 |
| **4. 測試層 (Testing)** | 補 CCG008 pending -> resolved/historical/residual case；跑 focused/full pytest | 分類修正破壞現有 current pending warning | 保留單日 pending 仍 current 的測試 |
| **10. 安全層 (Security)** | artifact / raw queue access 需主公另核准；raw 不進 log、不進 repo | raw post content 被貼入 history 或 commit | 只記 metadata / counts / status；raw path 保持 git-ignored |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / 不適用理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 不改 pipeline 架構；只在 existing replay / governance 邊界內處理 | 把 P95.1 擴成新 provider 或新 workflow | Forbidden Work 明列不接 provider、不改 workflow |
| **5. 資料層 (Data)** | 使用 2026-05-22 queue / 2026-05-24 manifest / Actions artifact metadata | artifact expired 或 local queue 不存在導致無法判讀 | 記錄 artifact unavailable，不能偽造 replay 結果 |
| **6. 可觀察性層 (Observability)** | runtime matrix 列 dry-run/apply/probes 的 command、exit、核心輸出 | 主公只看到「已修」但不知道哪兩筆 pending 如何處理 | history 必列 counts / status / no raw content |
| **7. 韌性層 (Resilience)** | replay 失敗或 artifact 不可得時 R-016 保持 Open | 為了收官硬改狀態 | failure path 明列 keep-open blocker |
| **13. 可維護性層 (Maintainability)** | 補測試與 runbook 判讀，讓未來 pending 不靠人工猜 | CCG008 分類規則半年後看不懂 | detail 裡保留 dates / latest day / covered day |
| **14. 文件層 (Documentation)** | P95.1 plan / handoff / active / risk / history 同步 | 新視窗仍以為 P95 可以 close | L1 bootstrap 指向 P95.1 |
| **15. 流程層 (Process)** | plan freeze 與 runtime / artifact approval 分離 | plan freeze 後直接下載 raw artifact | Entry criteria 明列 runtime 另需核准 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | replay / pytest | dry-run/apply 耗時或 LLM call 過多 | 使用 existing `--max-items` / budget guard |
| **9. UX/A11y 層** | landing health | pending closure 後首頁仍 stale | 收官必跑 `check_daily_report_health.py` |
| **11. 部署層 (DevOps)** | Actions / auto-sync | runtime 期間遠端又產生 auto-sync commit | 開工與 push 前都 fetch；必要時 fast-forward |
| **12. 成本層 (Cost)** | LLM replay / CCG | apply replay 消耗 LLM budget | dry-run 不花；apply 受 LLMBudgetManager 控制 |
| **16. 隱私/合規層 (Privacy)** | raw artifact / raw queue | raw post content 進 history / PR / commit | 不貼 raw；只寫統計與狀態 |
| **17. i18n/在地化層** | report date | UTC run date 與 Taipei report date 錯位 | 以 manifest `run_date_taipei` 判讀 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：必補 CCG008 分類測試。
- [x] 動 Data 層 -> 已動 Security / Privacy 層：artifact access 另需核准。
- [x] 動 Architecture 層 -> 已動 Documentation 層：handoff / active / risk / history 同步 P95.1。
- [x] 動 Cost 層 -> 已動 Observability 層：replay budget / CCG detail 必列。

---

## 7. 跨切面檢查

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 建立 P95.1 plan | 可逆 | 主公已核准 plan freeze |
| 同步 handoff / active / risk / TASK_HISTORY | 可逆 | 主公已核准 plan freeze |
| 下載 / 讀 artifact | 半可逆，隱私風險 | 尚未核准；runtime 前另問 |
| dry-run replay | 可逆；但會讀 raw queue | 尚未核准 |
| apply replay / 更新 manifest | 半可逆 | 尚未核准；需先 dry-run |
| 修改 CCG008 分類邏輯 | 可逆 | runtime 才可執行 |
| R-016 close / downgrade | 半可逆，治理影響高 | runtime 後另需主公裁決 |

### X2 盲區掃描 (Blind Spot)

- [x] 主公看不到 artifact 內文；因此不得把 raw 片段貼進回覆。
- [x] GitHub artifact retention 到期後可能無法重現 5/22 queue；需記錄 expires_at / unavailable。
- [x] replay apply 可能修改 git-ignored queue / enriched_posts，不能誤 stage。
- [x] CCG008 current 可能只是 window semantic，不代表最新日失敗；但必須用 evidence 關閉。

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-24
- 5/22 artifact retention 可能於 2026-05-25 左右到期；runtime 若晚於到期日，需改採 artifact unavailable path。
- 本計畫過期日期：2026-06-07；逾期需重新跑 latest Actions / SLO / cost。

### X4 多角度同行審查

- **主公視角**：主公要的是「完美處理」，所以不能用時間窗口把 5/22 pending 蓋掉；必須處理或明確證明不可處理。
- **世界頂尖駭客 / 紅隊攻擊者視角**：最大攻擊面是用 classification 粉飾未處理 queue；計畫要求先 dry-run / evidence，再改分類。
- **接手者視角**：接手者要能從 P95.1 看懂為何 P95 沒 close、5/22 pending 怎麼被判讀、R-016 為何可或不可關。
- **X4-J 自動化建議性工具邊界**：CCG 是治理建議，不是唯一真相；若工具分類與 artifact evidence 衝突，artifact evidence 優先。
- **X4-K 使用者端審查官 / Patric 型人格**：production report 已健康，但風險帳若留 pending，主公會感覺沒收乾淨；P95.1 必須把帳本與實際狀態對齊。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | artifact 讀取含 raw post，污染 log / history | 中 | 高 | Security / Privacy | runtime 前另核准；只記 counts / status |
| R2 | artifact 已過期，無法 dry-run | 中 | 中 | Data / Time Decay | 記 artifact unavailable，不偽造 replay |
| R3 | 只改分類，未處理真 queue | 中 | 高 | Logic / Governance | runtime 順序固定：artifact/dry-run 先於分類修正 |
| R4 | apply replay 消耗 LLM budget 或碰 provider | 低 | 中 | Cost | 先 dry-run；apply 受 budget guard；不接 OpenAI paid fallback |
| R5 | auto-sync 在 runtime 期間造成分岔 | 中 | 中 | DevOps | fetch / status / diff before commit and push |
| R6 | R-016 被過早 close 後又復發 | 低 | 高 | Resilience | close/downgrade 需最新 probes 與主公裁決 |

**高風險加權檢查（META4）**：
- 高風險項：R1 / R3 / R6。
- 結論：runtime / artifact access / R-016 裁決都需主公另行核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **P95.1.0 Plan Freeze** | 建立本檔，同步 handoff / active / risk / history | 防止直接下載 artifact 或靠時間 close | phase lint / handoff truth / governance doctor / diff check |
| **P95.1.1 Evidence Refresh** | fetch origin，確認 latest run / artifact metadata / report date | 避免使用舊 evidence | matrix 有 run id / commit / expires_at |
| **P95.1.2 Artifact Dry-run** | 在核准後讀 5/22 queue，跑 `enrichment_replay.py --date 2026-05-22` dry-run | 真 pending 未判讀 | command + exit + counts |
| **P95.1.3 Apply Or Explain** | 若可 replay 且主公核准，apply；否則記不可 replay 原因 | 未知 pending 殘留 | manifest / evidence 狀態明確 |
| **P95.1.4 Governance Classification** | 補 CCG008 resolved/historical/residual 判讀與 tests | 5/22 pending 永遠 current | focused tests |
| **P95.1.5 Closeout Probes** | SLO / doctor / cost / health / pytest | closeout 漏洞 | all commands / exit codes |
| **P95.1.6 R-016 Decision** | Close / Downgrade / Keep Open | 誤關風險 | 主公可讀裁決表 |
| **P95.1.7 Commit / Push** | commit；push 前主公確認 | 交接漂移 | git status clean / push success |

---

## 10. 影響檔案清單

**Plan-only 新增**：
- `docs/PHASE_95_1_PLAN.md`

**Plan-only 修改**：
- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`

**Runtime 可能修改**：
- `scripts/cost_cache_governance.py`
- `tests/test_cost_cache_governance.py`
- `docs/OPERATIONS_RUNBOOK.md`（若新增或釐清 CCG008 runbook）
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`
- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`

**Runtime 可能讀取但不可 stage**：
- GitHub Actions artifact `enrichment-queue-26299079187`
- `data/enrichment_queue/2026-05-22/enrichment_queue.json`
- `data/enrichment_queue/**/enriched_posts.json`

---

## 11. Forbidden Work（P95.1 邊界）

- 不修改 `.github/workflows/daily_report.yml`。
- 不修改 `main.py`。
- 不新增 provider key / PAT / Cloudflare token / Groq key。
- 不加入 GitHub Actions `models: read`。
- 不把 Groq / Cloudflare / GitHub Models 接進 daily default。
- 不啟用 OpenAI paid fallback 作為 replay 主線。
- 不在 plan freeze 階段下載 artifact、讀 raw queue、跑 replay。
- 不貼 raw post / raw prompt / raw LLM payload 到回覆或文件。
- 不 stage raw artifact、raw queue、enriched_posts、debug bundle、scratch。
- 不把 R-016 標記 Closed；runtime 後仍需主公裁決。
- 不 git push，除非主公明確確認。

---

## 12. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] P95.1 只改分類卻未能證明 queue 狀態。
- [ ] raw artifact content 進入 git diff / TASK_HISTORY / 回覆。
- [ ] apply replay 消耗超出預期 budget。
- [ ] R-016 close 後 7 天內 CCG008 或 production SLO 復發。
- [ ] artifact expired 導致無法重建 5/22 pending，但文件未記錄不可得原因。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-95-1-enrichment-pending.md`。

---

## Pre-flight 多視角體檢 ─ STR10

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊者會質疑我們把 5/22 pending 用分類洗掉；本計畫強制 artifact dry-run 先行，分類修正只能跟在 evidence 後面。 |
| **X4-B 接手者視角** | 接手者需要知道 5/22 pending 不是最新日 production failure，而是 P95 closeout 前留下的 queue 帳；P95.1 會留下 run id、date、status、裁決。 |
| **X4-C 災難情境** | 若 artifact 過期又直接 close，未來無法重現 pending 真相；計畫要求過期時走 unavailable path，R-016 保持 Open 或降級觀察。 |
| **X4-D 5 年後視角** | 五年後 provider 與 artifact retention 早已不同，但「不能靠 window 過期收官」這條治理原則會保留在 risk/history 中。 |
| **X4-E 終端 vs IDE** | 終端會看到 replay exit code，IDE 會看 docs；P95.1 要同時記 command、exit、counts、classification，讓兩種閱讀方式都能追溯。 |
| **X4-F 跨平台 Win/Mac/Linux** | runtime 命令以 Python 腳本為主，PowerShell 只用於本地觀察；必要的修法與測試需能在 Windows 本地與 GitHub Actions Linux 重跑。 |
| **X4-G 主公個人視角** | 主公要的是完美處理，不是看起來 pass；因此本 Phase 明確拒絕等 5/22 自然掉出視窗。 |
| **X4-H 觀測 / 治理** | CCG008 是治理訊號，不是自動真相；P95.1 要把 artifact evidence、manifest snapshot、cost classification 三者對齊。 |
| **X4-I 主公可見性** | 主公看不到 artifact retention 與 raw queue 細節；計畫要把哪些能讀、哪些不能貼、何時需要核准明列。 |
| **X4-J 自動化建議性工具邊界** | 自動分類若只看 window 會把舊 pending 留成 current；P95.1 會補測試避免工具誤導裁決。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 報告頁已健康不代表治理帳本乾淨；P95.1 要讓使用者看到的最新報告與風險登記簿同時收斂。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步是否清楚 | 觸發；P95.1 只關 CCG008 pending，不開新主線。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | raw artifact、安全邊界、CI/CD | 觸發；artifact access 必須另核准。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公是否會覺得「還沒完」 | 觸發；拒絕等時間過期。 |
| **Jimmy 型文件主筆** | 改 docs / history / handoff 時觸發 | 是否可追溯 | 觸發；run id、commit、dates 必列。 |
| **Marcus 型數據分析師** | 涉及趨勢與判斷依據 | 三日窗與兩日窗差異 | 觸發；2-day 只作輔助，3-day 仍要處理。 |
| **Oliver 型設計審查** | 涉及 landing / report | report 是否最新 | 觸發；收官仍要跑 health。 |
| **Penny 型 CFO** | 涉及 LLM calls / budget | replay 成本 | 觸發；apply 受 budget guard 控制。 |
| **Jason 型執行 / DevOps** | 涉及 git / Actions | artifact expiry、auto-sync 分岔 | 觸發；fetch / status / push checks 必做。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | P95.1 可能只改 CCG008 classification，把 pending 粉飾成 resolved。 | **S 級** | 0 | artifact dry-run 是 runtime entry；無 evidence 不允許 close。 | 入計畫 |
| 2 | 讀 artifact 可能讓 raw post content 進入 history 或 commit。 | **S 級** | 0 | artifact access 另核准；只記 metadata/counts/status。 | 入計畫 |
| 3 | 直接 apply replay 可能消耗 LLM budget 或觸發 provider 成本。 | A 級 | 0 | 先 dry-run；apply 受 existing budget guard；不啟用 OpenAI paid fallback。 | 入計畫 |
| 4 | artifact 已過期時，AI 可能硬說已處理。 | **S 級** | 0 | artifact unavailable 是正式 outcome；R-016 不因此 close。 | 入計畫 |
| 5 | 三日窗 current 與兩日窗 residual 可能被混用，造成裁決漂移。 | A 級 | 0 | 三日窗仍是 gate；兩日窗只作輔助 evidence。 | 入計畫 |
| 6 | auto-sync commit 可能在 runtime 期間讓本地落後。 | A 級 | 0 | fetch / status / diff before commit and push。 | 入計畫 |
| 7 | replay 產物可能被誤 stage。 | A 級 | 0 | Forbidden Work 明列 raw / enriched temp 不 stage。 | 入計畫 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

本 Phase 不新增、不更新 skill。若 runtime 臨時涉及 skill，需另開補遺並補 STR9 表。

---

## 13. 凍結戳記

- **凍結人**：主公核准，AI 執行。
- **凍結時間**：2026-05-24 Asia/Taipei。
- **凍結後變更**：禁止；如需修改，新增章節「Phase P95.1.x 補遺」並引用本檔。

---

## 14. Phase P95.1A Artifact Dry-run 補遺（2026-05-24）

> 本節為凍結後補遺，不改動上方 frozen plan。主公於 2026-05-24 回覆「核准」，視為核准 P95.1A artifact dry-run access。AI 只下載 / 解壓 2026-05-22 enrichment artifact 到 git-ignored `scratch/`，只做 schema/count 驗證與 dry-run，不 apply、不寫 report、不 stage raw、不輸出 raw post content。

### 14.1 Artifact Evidence

| 欄位 | 值 |
|---|---|
| 正確 GitHub run | `26285001843` |
| run conclusion | `success` |
| run created_at | `2026-05-22T11:25:11Z` |
| run updated_at | `2026-05-22T11:26:35Z` |
| run head_sha | `4f0e5b78ff96d47521eebe11e7c75885f978c5df` |
| artifact id | `7159368993` |
| artifact name | `enrichment-queue-26285001843` |
| artifact size | `4935` bytes |
| artifact expires_at | `2026-05-25T11:26:27Z` |
| zip entry | `2026-05-22/enrichment_queue.json` |
| extracted path | `scratch/p95_1a_artifact_26285001843/extracted/2026-05-22/enrichment_queue.json` |

錯誤排除：run `26299079187` 的 artifact 雖然也存在，但 zip entry 是 `2026-05-23/enrichment_queue.json`，不能用來判讀 2026-05-22 pending。P95.1A 已改用 manifest `generated_at=2026-05-22T11:26:25Z` 對應的 run `26285001843`。

### 14.2 Queue Schema / Count Evidence

| Probe | Result |
|---|---|
| `validate_enrichment_queue(queue)` | valid |
| `run_date` | `2026-05-22` |
| `source_count` | `10` |
| `eligible_count` | `2` |
| `skipped_count` | `8` |
| `eligible_records(queue, max_items=100)` | `2` |

未輸出 raw 欄位：title / content / url / prompt / LLM payload 皆未寫入文件或回覆。

### 14.3 Dry-run Evidence

Command:

```powershell
py scripts\enrichment_replay.py --date 2026-05-22 --queue-path scratch\p95_1a_artifact_26285001843\extracted\2026-05-22\enrichment_queue.json
```

Output:

```text
DRY-RUN: eligible=2 will_replay=2 remaining_budget=15 status=dry_run
```

Interpretation:

- 2026-05-22 pending 不是 phantom；artifact 內確實有 2 筆 eligible records。
- dry-run 顯示這 2 筆可 replay。
- 下一步不應先修 CCG008 classification；應進 P95.1B apply replay，讓 pending 真正收斂。
- apply 可能消耗 LLM budget，且會產生 ignored `enriched_posts.json` / manifest snapshot mutation，因此需要主公另行核准。

### 14.4 P95.1A Decision

| 選項 | 裁決 | 理由 |
|---|---|---|
| 直接 Close / Downgrade R-016 | 不採用 | pending 已證實可 replay，尚未 apply |
| 只改 CCG008 classification | 不採用 | 會把真 pending 粉飾成 residual/historical |
| 進 P95.1B apply replay | **採用** | dry-run 顯示 `will_replay=2` 且 budget 尚可 |

**P95.1A 結論**：Artifact dry-run 已完成；P95.1B 需主公另行核准後 apply replay。R-016 仍 Open。

---

## 15. Phase P95.1B Apply Replay 補遺（2026-05-24）

> 主公於 2026-05-24 同時下令 push 並核准 P95.1B apply replay。AI 先將 P95.1A commit rebased onto latest origin 並 push，再執行 `enrichment_replay.py --apply`。本節只記錄 raw-free manifest / command / probe 結果，不輸出 raw post content，不 stage scratch artifact / raw queue。

### 15.1 Push / Rebase Context

| 欄位 | 結果 |
|---|---|
| push 前 fetch | 遠端新增 auto-sync `eb9c11f docs: 戰略報告自動同步 2026-05-24 10:20:28 [mode:production l1:0 l2:0 hit:N/A]` |
| 同步方式 | `git rebase origin/main` |
| rebased P95.1A commit | `b836bc0 docs: 記錄 P95.1A artifact dry-run` |
| push result | `eb9c11f..b836bc0 main -> main` |

### 15.2 Apply Replay Evidence

Command:

```powershell
py scripts\enrichment_replay.py --date 2026-05-22 --queue-path scratch\p95_1a_artifact_26285001843\extracted\2026-05-22\enrichment_queue.json --apply
```

Output:

```text
OK: budget skip; decision=skip_llm reason=cooldown_active
```

Manifest delta (`data/runs/2026-05-22/run_manifest.json`):

| 欄位 | Apply 前 | Apply 後 |
|---|---|---|
| enrichment.queue_ref | `data/enrichment_queue/2026-05-22/enrichment_queue.json` | `enrichment_queue.json` |
| enrichment.replay_status | `pending` | `skipped_budget` |
| enrichment.budget_decision | `call_llm` | `skip_llm` |
| enrichment.budget_reason | `budget_available` | `cooldown_active` |
| enrichment.budget_remaining | `9` | `15` |
| enrichment.cooldown_active | `false` | `true` |
| enrichment.enriched_posts | `0` | `0` |

### 15.3 Probe Evidence After Apply

| Probe | Result | Closeout impact |
|---|---|---|
| 2026-05-22 manifest snapshot | `replay_status=skipped_budget`、`eligible_posts=2`、`enriched_posts=0`、`budget_decision=skip_llm`、`budget_reason=cooldown_active` | Unknown pending 已轉成明確 budget-skip state；仍未補深讀 |
| 2026-05-24 cost 3-day | CCG006 current cooldown；CCG008 current `2026-05-22:status=skipped_budget eligible=2`；CCG008 residual 2026-05-23/24 no_eligible | R-016 仍不可 close；需 cooldown 後 retry |
| 2026-05-24 doctor | DOC017 current cooldown；DOC018/DOC019 residual；無 blocking | production 不壞，但 budget/cooldown 仍需處理 |
| 2026-05-24 SLO | `issues=[]`、`doctor_blocking_days=0`、`doctor_degraded_days=0` | production SLO 不阻擋 |
| 2026-05-24 health | canonical report / landing / core contract PASS | landing 不阻擋 |

Budget state:

| 欄位 | 值 |
|---|---|
| current local time | `2026-05-24 20:35 +08:00` |
| cooldown_until_utc | `2026-05-24T16:20:27Z` |
| cooldown_until_taipei | `2026-05-25 00:20:27 +08:00` |
| cooldown_reason | `quota_error` |

### 15.4 P95.1B Decision

| 選項 | 裁決 | 理由 |
|---|---|---|
| Bypass budget / force LLM | 不採用 | 會違反 P90 budget guard 與 P95.1 cost/security 邊界 |
| 直接修 CCG008 classification | 不採用 | 目前 state 是真 `skipped_budget`，不是 resolved |
| 等 cooldown 結束後 retry apply replay | **採用** | 符合 P90 budget guard，也能真正補掉 eligible=2 |

**P95.1B 結論**：P95.1B 已把 2026-05-22 unknown pending 轉成明確 `skipped_budget/cooldown_active`；尚未 replay 成功。下一步是 P95.1C cooldown retry，需在 2026-05-25 00:20:27 +08 後重新 apply replay。R-016 仍 Open。

### 15.5 Commit-time Validation

| Check | Result |
|---|---|
| `py scripts\lint_phase_plan.py docs\PHASE_95_1_PLAN.md` | PASS：Pre-flight 體檢 M1 + M2 通過 |
| `py scripts\check_handoff_truth.py --repo-root .` | PASS：`HND000 active bootstrap truth verified` |
| `py scripts\governance_doctor.py --repo-root .` | PASS：`GOV000 runbook and risk registry governance verified` |
| `git diff --check` | PASS：無 whitespace error；僅 Git for Windows LF -> CRLF 工作樹轉換警告 |
| `py scripts\cost_cache_governance.py --repo-root . --date 2026-05-24 --window-days 3 --json` | PASS exit 0；`CCG008 current` 仍正確指出 2026-05-22 `skipped_budget eligible=2` |
| `py scripts\system_doctor.py --repo-root . --date 2026-05-24 --profile ci --require-production` | PASS exit 0；無 blocking，DOC017 current cooldown |
| `py scripts\slo_checker.py --repo-root . --date 2026-05-24 --window-days 5 --json` | PASS exit 0；`issues=[]`、`doctor_blocking_days=0` |
| `py scripts\check_daily_report_health.py --repo-root . --date 2026-05-24 --expected-mode production` | PASS exit 0；canonical / landing / core contract PASS |

---

## 16. Phase P95.1C Cooldown Retry 補遺（2026-05-25）

> 主公於 2026-05-25 核准 P95.1C cooldown retry。AI 先確認已過 `2026-05-25 00:20:27 +08` cooldown 截止時間、遠端無分岔、queue 檔仍在，再依 P95.1A artifact queue 執行 dry-run 與 apply。本節只記錄 raw-free manifest / command / probe 結果，不輸出 raw post content，不 stage scratch artifact / raw queue / git-ignored enriched output。

### 16.1 Entry Evidence

| 欄位 | 結果 |
|---|---|
| local time | `2026-05-25 09:33:22 +08:00` |
| cooldown_until_taipei | `2026-05-25 00:20:27 +08:00` |
| git status | `main...origin/main`，無 tracked dirty；既有 untracked reports / scratch 仍未納入 |
| latest commit | `05be57a docs: 記錄 P95.1B apply replay cooldown` |
| queue path | `scratch/p95_1a_artifact_26285001843/extracted/2026-05-22/enrichment_queue.json` |
| queue exists | `true` |

Dry-run:

```powershell
py scripts\enrichment_replay.py --date 2026-05-22 --queue-path scratch\p95_1a_artifact_26285001843\extracted\2026-05-22\enrichment_queue.json
```

Output:

```text
DRY-RUN: eligible=2 will_replay=2 remaining_budget=20 status=dry_run
```

### 16.2 Apply Replay Evidence

Command:

```powershell
py scripts\enrichment_replay.py --date 2026-05-22 --queue-path scratch\p95_1a_artifact_26285001843\extracted\2026-05-22\enrichment_queue.json --apply
```

Output:

```text
OK: enrichment replay completed; enriched=2/2; manifest=D:\Coding Project\Arena of Valor\data\runs\2026-05-22\run_manifest.json
```

Manifest delta from P95.1B to P95.1C (`data/runs/2026-05-22/run_manifest.json`):

| 欄位 | P95.1B | P95.1C |
|---|---|---|
| enrichment.enriched_posts | `0` | `2` |
| enrichment.replay_status | `skipped_budget` | `completed` |
| enrichment.budget_decision | `skip_llm` | `call_llm` |
| enrichment.budget_reason | `cooldown_active` | `budget_available` |
| enrichment.budget_remaining | `15` | `20` |
| enrichment.cooldown_active | `true` | `false` |

Generated output:

| Path | Status |
|---|---|
| `data/enrichment_queue/2026-05-22/enriched_posts.json` | Created locally, git-ignored by `.gitignore:25 data/*`, not staged |

### 16.3 Probe Evidence After Retry

| Probe | Result | Closeout impact |
|---|---|---|
| 2026-05-22 manifest snapshot | `replay_status=completed`、`eligible_posts=2`、`enriched_posts=2`、`budget_decision=call_llm`、`budget_reason=budget_available` | P95.1 target pending 已真正補跑完成 |
| 2026-05-24 cost 3-day | CCG008 current removed；CCG008 residual only `2026-05-23/24 no_eligible`；CCG006 current remains for 2026-05-24 cooldown | 2026-05-22 blocker cleared；latest-day cooldown advisory remains separate |
| 2026-05-24 doctor | DOC007 current、DOC017 current cooldown、DOC018 residual、DOC019 residual；無 blocking | production SLO 不阻擋，但 R-016 裁決仍需主公 |
| 2026-05-24 SLO | `issues=[]`、`doctor_blocking_days=0`、`doctor_degraded_days=0` | SLO gate clean |
| 2026-05-24 health | canonical report / landing / core contract PASS；tier=`production_local_only` | report health clean；LLM coverage remains local-only for latest report |
| Focused tests | `32 passed in 0.99s` | SLO / doctor / cost governance tests pass |
| Full pytest | `288 passed in 9.30s` | full regression pass |

### 16.4 P95.1C Decision

| 選項 | 裁決 | 理由 |
|---|---|---|
| Keep treating 2026-05-22 as pending | 不採用 | manifest 已 `completed` 且 `enriched_posts=2` |
| Close R-016 automatically | 不採用 | R-016 close / downgrade / keep-open 是治理裁決，需主公明確同意 |
| Commit P95.1C completed evidence, then ask for R-016 decision | **採用** | CCG008 blocker 已清除，但 latest 2026-05-24 cooldown advisory 與後續雲端證據仍需裁決 |

**P95.1C 結論**：P95.1C 已成功補跑 2026-05-22 的 2 筆 eligible enrichment，`CCG008 current` 已清除；R-016 仍 Open，下一步是 P95.1D 由主公裁決 `Close R-016` / `Downgrade R-016` / `Keep R-016 Open`。若追求最保守完美收尾，建議 P95.1C push 後手動 dispatch post-2026-05-25 Daily Monitor，補最新雲端證據後再裁決。

---

## 17. Phase P95.1D Post-P95.1C Cloud Verification 補遺（2026-05-25）

> 主公要求「最保守完美收尾」，因此 P95.1C local success 後沒有直接裁決 R-016，而是先 push `9188a92`，再手動 dispatch AoV Daily Monitor，讀雲端 workflow / artifact / auto-sync commit / post-cloud probes。本節只記錄 raw-free cloud evidence，不把前台內容可信度問題混入 R-016。

### 17.1 Workflow Evidence

| 欄位 | 結果 |
|---|---|
| workflow | `AoV Daily Monitor` |
| event | `workflow_dispatch` |
| run id | `26379118247` |
| head sha | `9188a92f3302c54f996c25989c6d6517f4e0cbe4` |
| created_at | `2026-05-25T01:51:10Z` |
| updated_at | `2026-05-25T01:53:19Z` |
| status / conclusion | `completed` / `success` |
| job id | `77644855026` |
| strict doctor step | `System Doctor (Strict Gate)` success |
| artifact | `enrichment-queue-26379118247` |
| artifact id | `7190334548` |
| artifact expires_at | `2026-05-28T01:53:14Z` |

Auto-sync:

```text
d89c3b9 docs: 戰略報告自動同步 2026-05-25 01:53:13 [mode:production l1:0 l2:9 hit:75%]
```

Files from auto-sync commit:

| Path | Change |
|---|---|
| `data/reports/aov_report_2026-05-25.html` | new production report |
| `data/runs/2026-05-25/run_manifest.json` | new cloud manifest |
| `data/llm_budget_state.json` | budget state updated |
| `data/llm_cache.json` | cache updated |
| `index.html` | landing now points to 2026-05-25 report |

### 17.2 Post-cloud Probe Evidence

| Probe | Result |
|---|---|
| `check_daily_report_health.py --date 2026-05-25 --expected-mode production` | PASS：canonical / mode / tier / core contract / landing all PASS |
| `system_doctor.py --date 2026-05-25 --profile ci --require-production` | PASS exit 0；DOC007 current only；DOC018/DOC019 residual；無 blocking |
| `slo_checker.py --date 2026-05-25 --window-days 5 --json` | PASS exit 0；`issues=[]`、`doctor_blocking_days=0`、`doctor_degraded_days=0` |
| `cost_cache_governance.py --date 2026-05-25 --window-days 3 --json` | PASS exit 0；CCG006 current still records 2026-05-24 cooldown；CCG008 residual only no_eligible |

2026-05-25 manifest highlights:

| 欄位 | 值 |
|---|---|
| mode | `production` |
| publish_eligible | `true` |
| quality.tier | `production_local_only` |
| quality.analysis_source | `mixed` |
| quality.llm_coverage | `partial` |
| core_contract.status | `pass` |
| total_posts / platform_count / source_count | `19` / `4` / `3` |
| budget.decision | `call_llm` |
| budget.cooldown_active | `false` |
| budget.llm_calls_used | `3` |
| budget.remaining_llm_calls | `17` |
| selection.cache_hit_rate | `75%` via `l2=9` / total calls `12` |
| enrichment.replay_status | `no_eligible` |
| enrichment.eligible_posts | `0` |
| enrichment.skipped_posts | `8` |
| provider.routing.route_status | `router_disabled_legacy_default` |
| provider.routing.enabled_slots | `0` |

Content-trust quick sniff:

| Check | Result |
|---|---|
| report title search | `芽芽觀察室` present |
| unwanted title search | `圖倫觀察室` not found |

**Boundary**：This quick sniff does not close the separate frontend/content-trust problem. 主公先前回報的「芽芽觀察室變圖倫」與「舊文章」仍應另開 R-017 / P96+，不能混入 R-016 closeout。

### 17.3 R-016 Decision Options

| 選項 | AI 保守建議 | 理由 |
|---|---|---|
| Close R-016 | 可行但較激進 | R-016 planned blockers are cleared, cloud strict gate passed, SLO clean |
| Downgrade R-016 to monitoring | **建議採用** | 最保守：承認主線修復完成，但保留 7-day monitoring 與 latest advisory observation |
| Keep R-016 Open | 不建議 | 目前已無 R-016 blocking evidence；繼續 Open 容易把 R-017 前台內容問題混入後端可靠性主線 |

**P95.1D 結論**：Post-P95.1C cloud verification 已完成且成功。AI 建議主公裁決 `Downgrade R-016 to monitoring`，並另開 R-017 / P96+ 處理網站內容可信度（芽芽觀察室、舊文章、known issue guard）。
