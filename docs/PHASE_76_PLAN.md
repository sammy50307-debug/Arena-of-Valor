# Phase P76 計畫書 — RISK_REGISTRY / HANDOFF 狀態清理（凍結版）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：✅ 已收官（2026-05-16）

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P76 |
| **Phase 名稱** | RISK_REGISTRY / HANDOFF 狀態清理 |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 微 Phase（預估 4 檔；純文件狀態對齊） |
| **預估投入時數** | 30 min |
| **Token budget** | 20K tokens |
| **負責模型** | GPT-5.3-Codex（文件 patch + git 驗證） |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 轉換條件 | 執行者 |
|---|---|---|---|---|
| R-007 | Open 區但狀態已修補 | Closed 區 | 已修補且無需進一步觀察 | AI patch |
| R-008 | Open 區但狀態已修補 | Closed 區 | 已修補且無需進一步觀察 | AI patch |
| handoff push 狀態 | 停在 `72cbb25` / 本地 commits 待 push | 最新已推 `614dc13` / tracked clean | 主公已核准並完成 push | AI patch |

---

## 1. 目標 (Objective)

修正狀態帳本漂移：把已修補的 R-007/R-008 移到 Closed，更新 `NEXT_SESSION_HANDOFF.md` 的最新已推 commit 與 push 狀態，讓下一個視窗不再以為 P75/P70.4/P70.6 尚未推送。

## 2. 觸發背景 (Why Now)

主公詢問舊有任務後，WIP 顯示無進行中 / 無凍結待動工；但 handoff 與 RISK_REGISTRY 仍有狀態漂移。這類漂移會讓下一窗誤判「還有本地 commit 要推」或「R-007/R-008 還在 open」。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 不處理 | 保留帳本漂移 | 零改動 | 下窗會誤判狀態 | 不採 |
| B. 只口頭說明 | 不改檔案 | 快 | 權威文件仍錯 | 不採 |
| C. 小 Phase 清理 | 修 registry / handoff / WIP / history | 狀態一致 | 需 commit 一次 | **採用** |

---

## 3. Entry Criteria

- [x] `git status -sb` 顯示 tracked clean，只有既有 untracked 報告/暫存檔
- [x] `main` 已同步 `origin/main`，P75/P70.4/P70.6 已推到 `614dc13`
- [x] WIP 清單顯示無進行中 / 無凍結待動工 Phase
- [x] RISK_REGISTRY 中 R-007/R-008 內容已標示已修補，但仍位於 Open 區
- [x] 不全讀 `TASK_HISTORY.md`

## 4. Exit Criteria

- [x] R-007/R-008 移至 Closed 區
- [x] `NEXT_SESSION_HANDOFF.md` 頂部最新已推 commit 改為 `614dc13`
- [x] handoff 移除「本地 commits 待 push」誤導文字
- [x] WIP 新增 P76 收官記錄
- [x] `TASK_HISTORY.md` 追加 P76 紀錄，不全檔編輯
- [x] `git diff --check` 通過

---

## 5. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | N/A，不改 runtime code | 無 | 純 markdown patch |
| **2. 邏輯層 (Logic)** | 狀態只依 git / registry 物理事實更新 | 誤把觀察中風險關閉 | 只移 R-007/R-008，其他 open 保留 |
| **4. 測試層 (Testing)** | `git diff --check` + status / rg 驗證 | 文件語意錯 | grep stale commit / 待 push 字樣 |
| **10. 安全層 (Security)** | 不讀 secrets、不碰 data/reports | 誤 stage untracked reports | 明確 stage 文件清單 |

### A / B 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | N/A，無模組分工變更 | 無 | — |
| **5. 資料層 (Data)** | 文件狀態資料對齊 | 狀態漂移 | 同步 registry / handoff / WIP |
| **6. 可觀察性層 (Observability)** | handoff 頂部給下一窗正確狀態 | 下窗誤判 | 更新最新已推 commit |
| **7. 韌性層 (Resilience)** | 降低狀態誤判造成的重工 | 文件漏改 | rg 驗證 stale phrases |
| **13. 可維護性層 (Maintainability)** | Closed / Open 區一致 | 已修風險混在 Open | 移動 R-007/R-008 |
| **14. 文件層 (Documentation)** | 本 Phase 主軸 | 無損紀錄不足 | TASK_HISTORY 追加 |
| **15. 流程層 (Process)** | 保持 Phase 收官流程 | 不該 push 自動推 | commit 後等主公確認 push |
| **8/9/11/12/16/17** | N/A，未改效能/UI/部署/成本/隱私/i18n | 無 | — |

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 移動 R-007/R-008 到 Closed | 可逆 | ✅ 2026-05-16 |
| 更新 handoff / WIP / TASK_HISTORY | 半可逆 | ✅ 2026-05-16 |
| `git push` | 半可逆 | 推前必問主公 |

### X2 盲區掃描

- [x] 不 stage untracked reports
- [x] 不改 runtime code
- [x] 不關閉仍在觀察中的 R-001/R-002/R-003/R-004/R-005/R-006/R-011/R-012/R-013

### X3 時間敏感性

- 本計畫日期：2026-05-16
- 最新已推 commit 物理事實：`614dc13`

### X4 多角度同行審查

- **主公視角**：主公要知道現在還剩哪些舊債，文件不應暗示剛推完的 commits 仍未推。
- **世界頂尖駭客 / 紅隊攻擊者視角**：本 Phase 不新增攻擊面；主要風險是誤 stage 本地未追蹤報告。
- **接手者視角**：下一窗看 handoff 頂部即可知道主線已清空、最新已推到 `614dc13`。
- **X4-J 自動化建議性工具邊界**：rg/status 只能抓字面漂移，仍需人工判斷哪些 open risk 不該關閉。
- **X4-K 使用者端審查官**：若 R-007/R-008 留在 Open，主公會以為已修問題仍待辦。

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 本 Phase 只改文件，攻擊面低；最大風險是誤 stage `data/reports/*.html`。 |
| **X4-B 接手者** | 接手者需要 handoff 頂部和 WIP 同步，避免重推或重做已收官項。 |
| **X4-C 災難情境** | 誤關閉仍需觀察的 R-004/R-006/R-012/R-013；本 Phase 僅移 R-007/R-008。 |
| **X4-D 5 年後** | 風險登記簿需要 Open / Closed 區可信，否則歷史查詢會失真。 |
| **X4-E 終端 vs IDE** | 用 PowerShell / git / rg 可驗證，不依賴 IDE。 |
| **X4-F 跨平台 Win/Mac/Linux** | 純 markdown 文件修改，Windows / macOS / Linux 只需 git 與文字 diff，沒有 shell 相容性風險。 |
| **X4-G 主公個人視角** | 主公問的是舊有任務，此 Phase 讓「主線清空、剩 open risk」更清楚。 |
| **X4-H 觀測 / 治理** | 清理 registry 是治理觀測品質，不是功能變更。 |
| **X4-I 主公可見性** | 收官需列明仍 open 的風險，以及 P76 是否只本地 commit、是否尚待 push。 |
| **X4-J 自動化建議性工具邊界** | `rg` 只能找 stale 字樣，不能替主公判斷是否該關閉觀察期風險。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 下個使用者體感是「帳本可信」；不要讓已修項留在 Open 製造焦慮。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 範圍只做狀態帳本 | 觸發 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 不 stage untracked reports | 觸發 |
| **Patric 型使用者端審查官** | 固定必看 | 主公能否一眼看懂剩餘舊債 | 觸發 |
| **Jimmy 型文件主筆** | 改 docs/history | 文字狀態一致 | 觸發 |
| **Marcus 型數據分析師** | 判斷依據 | 依 git status/log 與 registry 物理狀態 | 觸發 |
| **Oliver 型設計審查** | UI | N/A |
| **Penny 型 CFO** | 成本 | N/A |
| **Jason 型執行 / DevOps** | Git / handoff | 最新已推 commit 要正確 | 觸發 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | R-007 還有「觀察下次 LINE 實機驗收」字樣，移到 Closed 會不會太早？ | **S** | N/A | 狀態已寫已修補；R-004 已承接 LINE WebView 長期觀察 | 可移 |
| 2 | handoff 可能還有其他舊段落提到待 push | **S** | N/A | 用 rg 掃 `72cbb25` / `待 push` / `本地 commits` | 入驗證 |
| 3 | 只改文件但不 commit，下一窗仍漂移 | A | N/A | 本 Phase 收官 commit | 入流程 |
| 4 | 誤 stage data/reports | A | N/A | `git add --` 指定文件清單 | 入流程 |
| 5 | TASK_HISTORY 若不記，未來不知道為何移動 R-007/R-008 | A | N/A | 追加 P76 紀錄 | 入流程 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

N/A。本 Phase 不新增或更新 skill。
