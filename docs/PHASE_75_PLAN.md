# Phase P75 計畫書 — R-014 歷史 Phase Blindspot 回填（凍結版）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：✅ 已收官（2026-05-16）

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P75 |
| **Phase 名稱** | R-014 歷史 Phase Blindspot 回填 |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準（預估 6-8 檔；postmortems / risk / handoff / history） |
| **預估投入時數** | 2 h |
| **Token budget** | 45K tokens |
| **負責模型** | GPT-5.3-Codex（文件回填 + 驗證）；若 postmortem 脈絡不足，切 GPT-5.5 高做治理推理 |

## 0.5 狀態轉換清單

N/A。本 Phase 不變更 skill / module / workflow 生命週期，只補齊 M4 blindspot 文件與關閉 R-014。

---

## 1. 目標 (Objective)

為 P63、P64、P69、P70.3 四個歷史 Phase 補齊 M4 blindspot 檔，讓 `py scripts/m4_track_blindspots.py --status` 從「缺 4 個 blindspot」變成「全數已配對」，並關閉 R-014。

## 2. 觸發背景 (Why Now)

P72.3 的 M4 `--status` 偵測出 P63/P64/P69/P70.3 已有 postmortem 但缺 blindspots。P72.5 將此登記為 R-014。P74 與 P70.2 已收官，現在適合補治理資料，提升 `cross_phase_review.py` 對歷史教訓的召回。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 不回填 | 保留 R-014 開放 | 省時間 | M3/M4 只看 P71/P72，歷史坑重複踩 | 不採 |
| B. 一次回填 4 份 | 讀既有 postmortem，補 B-011 起連續 blindspots | 一次關閉 R-014，治理完整 | 文件量較多，需避免編號衝突 | **採用** |
| C. 每次回填 1 份 | 分 4 個小 Phase | 低風險 | 管理成本太高，R-014 拖太久 | 不採 |

---

## 3. Entry Criteria

- [x] 前置 Phase 已收官：P74 / P70.2 已 commit/push
- [x] R-014 來源已定位：`docs/RISK_REGISTRY.md`
- [x] 缺失清單已由 `py scripts/m4_track_blindspots.py --status` 確認：P63/P64/P69/P70.3
- [x] 既有 postmortem 檔已定位：`docs/postmortems/`
- [x] B-NNN 下一號已查：現有最高 B-010，P75 從 B-011 起
- [x] 主公授權：2026-05-16「好啊把剩下的東西做一做吧」
- [x] 不全讀 `TASK_HISTORY.md`：本 Phase 以 postmortem 檔為主，必要時才 grep 歷史錨點

## 4. Exit Criteria

- [x] 新增 4 份 blindspot 檔：P63 / P64 / P69 / P70.3
- [x] 每份 blindspot 至少 3 條 B-NNN，且全域編號不重複
- [x] 每條 blindspot 含「計畫書原寫 / 實際撞到 / 通則化 / 已加入或待加入」
- [x] `py scripts/m4_track_blindspots.py --status` 顯示 P63/P64/P69/P70.3 全部已配對
- [x] `py scripts/cross_phase_review.py` 可讀到新增 B-NNN 規則
- [x] `docs/RISK_REGISTRY.md` 將 R-014 移至 Closed 或標記已關閉
- [x] `TASK_HISTORY.md` 追加 P75 無損紀錄；不全檔編輯
- [x] `git diff --check` 無 whitespace error

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 2 h |
| 預估收益等級 | 中高 |
| 收益描述 | 補齊 M4 歷史資料，讓後續 Phase 能自動看見 P63/P64/P69/P70.3 的坑，不靠主公口頭提醒 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 不改 runtime code，只跑既有 M4 scripts | scaffold 工具輸出格式不符預期 | 生成後人工檢查並跑 `--status` |
| **2. 邏輯層 (Logic)** | 從 postmortem 事實抽盲點，不憑空編故事 | 把後見之明寫成當時真因 | 每條標明來源與不確定性 |
| **4. 測試層 (Testing)** | M4 status + cross_phase_review 驗證 | 文件寫了但工具讀不到 | Exit Criteria 要求兩個 script 都跑 |
| **10. 安全層 (Security)** | 不讀 secrets、不呼叫外部 API、不碰 data/reports | 文件可能暴露敏感路徑 | 只寫 repo 相對路徑與已公開 commit/hash |

### A 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | M4 blindspot 檔維持 postmortems 目錄結構 | 文件散落難找 | 命名用 `phase-XX-blindspots.md` |
| **5. 資料層 (Data)** | 不改業務資料，只新增治理文件 | B-NNN 編號衝突 | 先查最高 B-010，P75 從 B-011 起 |
| **6. 可觀察性層 (Observability)** | 讓 cross_phase_review 能讀到新增規則 | 自動化召回仍可能漏 | 跑 `cross_phase_review.py` 並記錄限制 |
| **7. 韌性層 (Resilience)** | 補歷史坑到新 Phase 計畫前置審查 | 歷史教訓只留在人腦 | blindspot 通則化 |
| **13. 可維護性層 (Maintainability)** | 每份檔同一格式 | 四份檔品質不一致 | 參照 P71/P72 blindspots 格式 |
| **14. 文件層 (Documentation)** | 本 Phase 主軸即文件回填 | 過度摘要違反無損精神 | 寫具體物理真相、命令、檔名 |
| **15. 流程層 (Process)** | 關閉 R-014 並更新 handoff/WIP | RISK_REGISTRY 漂移 | 收官同步修改 |

### B 級層

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **12. 成本層 (Cost)** | 文件回填耗 token | 限定讀 4 個 postmortem + 必要 grep | token 過量 | 不全讀 TASK_HISTORY |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Architecture 層 → 已動 Documentation層
- [x] 動 Data 層 → 已動 Maintainability 層
- [x] 動 Security 層 → 已動 Testing 層

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_75_PLAN.md` | 可逆 | ✅ 2026-05-16 |
| 新增 4 份 blindspot 文件 | 可逆 | ✅ 2026-05-16 |
| 修改 `docs/RISK_REGISTRY.md` | 半可逆 | ✅ 2026-05-16 |
| 追加 `TASK_HISTORY.md` / 更新 handoff | 半可逆 | ✅ 2026-05-16 |
| `git push` | 半可逆 | 推前必問主公 |

### X2 盲區掃描

- [x] log 副作用：M4 / cross_phase_review 只輸出終端文字
- [x] 中間檔產出：scaffold 直接產生 blindspot markdown
- [x] 系統狀態變更：不改 runtime、不改 reports、不改 secrets

### X3 時間敏感性

- 本計畫凍結日期：2026-05-16
- 本計畫過期日期：2026-06-16
- 風險記錄帶日期：✅ R-014 來源為 2026-05-14

### X4 多角度同行審查

- **主公視角**：主公要的是歷史坑能被未來 Phase 自動看見，不必每次口頭提醒。
- **世界頂尖駭客 / 紅隊攻擊者視角**：本 Phase 不新增攻擊面；主要風險是把敏感路徑或 token 寫進文件，需避免。
- **接手者視角**：新人應能從每份 blindspot 檔看懂該 Phase 的計畫盲點與通則化規則。
- **X4-J 自動化建議性工具邊界**：cross_phase_review 仍是字面抽取工具，新增 blindspots 提升來源資料，但不保證召回 100%。
- **X4-K 使用者端審查官**：若只補檔不關 RISK_REGISTRY，主公會以為 R-014 還沒做；收官必須同步關閉。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | postmortem 脈絡不足，導致 blindspot 寫得像後見之明 | 中 | 中 | 文件 | 寫明「推論」與「物理證據」分界 |
| R2 | B-NNN 全域編號重複 | 低 | 高 | 流程 | 先查最高 B-010，依序 B-011 起 |
| R3 | scaffold 工具產出 B-XXX 占位符未自動編號 | 中 | 低 | 工具限制 | 人工替換成連續 B-NNN |
| R4 | 四份文件太長但無重點 | 中 | 中 | 文件 | 每份至少 3 條，聚焦可通則化盲點 |
| R5 | R-014 關閉但 cross_phase_review 仍讀不到新增規則 | 低 | 中 | 工具 | 收官前跑 cross_phase_review 驗證 |

**高風險加權檢查（META4）**：
- 高風險數量：1
- 加權分數：5
- 是否 >= 5 須請示主公：是；主公已授權「把剩下的東西做一做」

---

## 9. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1** | 生成 4 份 scaffold | R3 | 檔案存在 |
| **S2** | 精讀 4 個 postmortem 並回填 B-011 起規則 | R1/R2/R4 | 每份 >= 3 條 |
| **S3** | 跑 M4 status + cross_phase_review | R5 | 全配對 + 能抽規則 |
| **S4** | 關閉 R-014，更新 TASK_HISTORY / handoff / WIP | 流程漂移 | git diff 明確 |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_75_PLAN.md`
- `docs/postmortems/2026-05-16-phase-63-blindspots.md`
- `docs/postmortems/2026-05-16-phase-64-blindspots.md`
- `docs/postmortems/2026-05-16-phase-69-blindspots.md`
- `docs/postmortems/2026-05-16-phase-70.3-blindspots.md`

**修改**：
- `docs/RISK_REGISTRY.md`
- `TASK_HISTORY.md`
- `NEXT_SESSION_HANDOFF.md`
- `memory/history_lookup/WIP_PHASES.md`

**刪除**：
- 無

**影響但未直接修改**：
- `scripts/m4_track_blindspots.py`
- `scripts/cross_phase_review.py`

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 發現既有 postmortem 無法支持任何 blindspot，只能臆測
- [ ] B-NNN 編號再次衝突
- [ ] cross_phase_review 無法讀到新檔，需改工具
- [ ] 有任何「我以為...結果不是」事件

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-75-r014-backfill.md`

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 本 Phase 不新增 runtime 攻擊面；文件不得包含 secrets、私有 token、完整本機敏感路徑或未公開憑證。 |
| **X4-B 接手者** | 接手者需要從 blindspot 檔直接看懂當時計畫漏寫什麼、實際撞到什麼、未來如何避免。 |
| **X4-C 災難情境** | 情境：回填文件憑空編造歷史，未來 Phase 用錯教訓；緩解：每條只從 postmortem 或明確 git/檔案事實抽取。 |
| **X4-D 5 年後** | 五年後模型與工具都變了，但 B-NNN 通則仍應可讀；規則需寫成工具無關原則。 |
| **X4-E 終端 vs IDE** | 本 Phase 以 PowerShell 執行 `py scripts/...`，文件不寫 bash-only 命令作為唯一做法。 |
| **X4-F 跨平台 Win/Mac/Linux** | 新增 markdown 檔跨平台無差異；驗收命令使用 Python 腳本，不依賴 shell 特性。 |
| **X4-G 主公個人視角** | 主公需要知道 R-014 是否真的關閉；收官會列 M4 status 全配對結果，不只說已補。 |
| **X4-H 觀測 / 治理** | P75 補的是治理觀測資料；若不跑 cross_phase_review，就不知道新增規則是否進入未來計畫前置審查。 |
| **X4-I 主公可見性** | 主公看不到 scaffold 產生的 B-XXX 是否被修正；收官需列 B-011 起編號區間。 |
| **X4-J 自動化建議性工具邊界** | M4 / cross_phase_review 只做字面抽取，回填可增加資料源，但人工審查仍必要。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 如果文件只補在 postmortems 但 handoff/WIP 不同步，下一窗仍會以為 R-014 未完成。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P75 僅處理 R-014，不混入 P70.4/P70.6 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；文件回填不應暴露 secrets |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；需同步 RISK_REGISTRY 與 WIP，避免狀態矛盾 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；本 Phase 主軸是文件 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；需列缺失 Phase 數與補齊後 status |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | N/A；不改 UI |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | N/A；不呼叫付費 API |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；驗收命令需在 Windows PowerShell 可跑 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 回填歷史 blindspot 容易把今天的理解投射回過去 | **S** | N/A | 每條標明物理事實與推論邊界 | 入計畫範圍 |
| 2 | B-NNN 編號若再重複，會讓 M4 工具輸出失真 | **S** | N/A | 從 B-011 起連續編號，收官 grep 驗證 | 入計畫範圍 |
| 3 | scaffold 產出檔案但 cross_phase_review 讀不到，R-014 表面關閉實際沒效 | **S** | N/A | Exit Criteria 要求跑 cross_phase_review | 入計畫範圍 |
| 4 | 四份文件一次做可能品質不均 | A | N/A | 每份至少 3 條，同一模板格式 | 入計畫範圍 |
| 5 | 只補 postmortems 不更新 RISK_REGISTRY/WIP，下一窗仍誤判 | A | N/A | 收官同步 RISK_REGISTRY / handoff / WIP | 入計畫範圍 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

N/A。本 Phase 不新增或更新 skill。

---

## 12. 凍結戳記

- **凍結人**：主公授權 + Codex
- **凍結時間**：2026-05-16
- **凍結後變更**：禁止；如需修改，新增 P75 補遺並引用本檔
