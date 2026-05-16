# Phase P76.1 計畫書 — Handoff Rule Unification（凍結版）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：CLOSED（2026-05-16；4 層入口與防偏航規則已凍結；純文件，不修程式）

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P76.1 |
| **Phase 名稱** | Handoff Rule Unification |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準 Phase（文件入口 5 檔；不改 runtime） |
| **預估投入時數** | 45 min |
| **Token budget** | 25K tokens |
| **負責模型** | GPT-5.3-Codex（文件 patch + repo 驗證） |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 轉換條件 | 執行者 |
|---|---|---|---|---|
| `NEXT_SESSION_HANDOFF.md` | 頂部與尾端可能同時含下一步 | 頂部 `ACTIVE_BOOTSTRAP` 為唯一下一步來源 | 主公核准統一規則 | Codex |
| 舊 handoff 內容 | 舊段落仍可能被誤讀為當前指令 | `ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION` 以下僅作歷史參考 | active bootstrap 已建立 | Codex |
| P77-P84 reliability program | 對話中草案 | 文件化總計畫 | 主公採方案 B | Codex |
| P77 止血 | 對話中草案 | 當前 Phase 計畫草案；不可未核准動工 | P76.1 完成後等待主公核准 P77 | Codex |

---

## 1. 目標 (Objective)

統一跨視窗交接規則：讓新視窗在不全讀 `TASK_HISTORY.md`、不讀完整 P77-P84 總計畫的情況下，只靠 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP` 與當前 Phase 計畫，就能知道下一步、可動檔案、禁止事項與驗收條件。

## 2. 觸發背景 (Why Now)

主公指出過去 Claude 流程似乎常把筆記寫在最下面；實查後確認：`TASK_HISTORY.md` 確實採 append-only，但 `NEXT_SESSION_HANDOFF.md` 同時存在頂部新指令與尾端舊指令，會讓下一視窗有機會讀到舊的「下個視窗直接動工」而偏航。P76.1 先統一 handoff 仲裁規則，再進 P77 止血。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 維持舊 handoff | 頂部更新、尾端保留舊下一步 | 零改動 | 新視窗可能讀到舊指令 | 不採 |
| B. 清空舊 handoff | 只保留最新 80 行 | 最乾淨 | 可能遺失歷史交接上下文 | 不採 |
| C. Active bootstrap + archive marker | 頂部唯一當前指令，舊內容標 archive | 不丟歷史，又能防偏航 | 需新增規則文件 | **採用** |

---

## 3. Entry Criteria

- [x] 主公核准 P76.1：只改文件規則與入口，不修程式碼
- [x] 現況已確認：`NEXT_SESSION_HANDOFF.md` 頂部與尾端存在不同時期的下一步文字
- [x] 實際最新 commit 已確認：`c0de129 docs: 清理風險與交接狀態`
- [x] 不全讀 `TASK_HISTORY.md`
- [x] 不 stage 既有 untracked reports / scratch / backups

## 4. Exit Criteria

- [x] `NEXT_SESSION_HANDOFF.md` 頂部存在 `ACTIVE_BOOTSTRAP_START` / `ACTIVE_BOOTSTRAP_END`
- [x] 舊 handoff 內容前存在 `ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION`
- [x] 新增 `docs/ACTIVE_OPERATION.md`，明列 Current Phase / Current Step / Allowed Files / Forbidden Work / Exit Criteria / Resume Rule
- [x] 新增 `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`，凍結 P77-P84 總戰役與跨 Phase 驗收規則
- [x] 新增 `docs/PHASE_77_PLAN.md`，作為 P77 動工前必讀計畫；狀態為 FROZEN_PENDING_APPROVAL，不可直接動工
- [x] `git diff --check` 通過（僅 Windows LF/CRLF warning，無 whitespace error）
- [x] `rg` 驗證 active/archive markers 存在

---

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 45 min |
| 預估收益等級 | 高 |
| 收益描述 | 大幅降低新視窗讀到舊下一步、跳 Phase、或誤改非目標檔案的風險 |
| ROI 結論 | 值得做；這是 P77-P84 長期修復前的入口防偏航基礎 |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | N/A，不改 runtime code | 誤碰程式檔 | 限定只改 markdown |
| **2. 邏輯層 (Logic)** | 建立 handoff 仲裁順序：ACTIVE_BOOTSTRAP → ACTIVE_OPERATION → Phase plan → Program → TASK_HISTORY 證據 | 多檔案互相矛盾 | 權威順序明文化 |
| **4. 測試層 (Testing)** | `git diff --check` + `rg ACTIVE_BOOTSTRAP` / `rg ARCHIVE_BELOW` | markdown marker 打錯導致新窗無法辨識 | 機械化 grep 驗證 |
| **10. 安全層 (Security)** | 不讀 secrets、不修改 `.env`、不碰 data raw | 誤公開敏感資料 | 文件只描述規則，不輸出 secret |

### A 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 建立 L1-L4 交接架構 | 文件分層反而增加複雜度 | L1 只保留短封包，其他層按需讀 |
| **5. 資料層 (Data)** | handoff 狀態資料與 git truth 對齊 | commit 狀態再次漂移 | ACTIVE_OPERATION 寫入 git truth check |
| **6. 可觀察性層 (Observability)** | 新視窗可從一段 bootstrap 看到狀態、下一步、禁止事項 | 舊段落仍干擾 | archive marker 明確降權 |
| **7. 韌性層 (Resilience)** | 新視窗讀少檔仍可接手 | 若 L1 過期會誤導 | Resume Rule 要求先跑 `git status -sb` |
| **13. 可維護性層 (Maintainability)** | 固定欄位 Current Phase / Step / Allowed / Forbidden / Exit / Resume | 欄位未來被漏填 | P84 納入 long-term governance |
| **14. 文件層 (Documentation)** | 本 Phase 主軸：文件規則凍結 | 文字太長讓新窗仍讀太多 | handoff L1 限制在頂部短段 |
| **15. 流程層 (Process)** | 狀態機 DRAFT → FROZEN → APPROVED → IN_PROGRESS → VERIFYING → CLOSED | AI 未依狀態行事 | bootstrap 明列 Mode 與可做事項 |

### B 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **8. 效能層** | 降低新視窗讀檔 token 成本 | 仍可能讀太多舊 archive | active 區明令不讀 archive 作下一步 |
| **9. UX/A11y 層** | N/A，無前端 UI | 無 | 無 |
| **11. 部署層** | N/A，不改 workflow | 無 | P77 後續才碰 |
| **12. 成本層** | 降低 token 成本 | 大計畫文件太長 | 新窗只讀 L1 + 當前 Phase |
| **16. 隱私/合規層** | 不納入 raw / secret 內容 | 文件誤貼敏感資訊 | 僅寫路徑與規則 |
| **17. i18n/在地化層** | 繁中為主，關鍵 marker 用 ASCII | marker 被翻譯後失效 | `ACTIVE_BOOTSTRAP_*` 保持 ASCII |

### 層級互鎖驗證

| 觸發 | 已同步 |
|---|---|
| 動 Architecture | 同步 Documentation / Process |
| 動 Process | 同步 Handoff / ACTIVE_OPERATION |
| 動 Documentation | 同步 Exit Criteria / Resume Rule |

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 P76.1/P77/P77-P84/ACTIVE_OPERATION 文件 | 可逆 | 主公核准 P76.1 |
| 在 handoff 頂部插入 active bootstrap | 可逆 | 主公核准 P76.1 |
| 將舊 handoff 標 archive | 可逆 | 主公核准 P76.1 |
| git push | 半可逆 | 推前必問主公 |

### X2 盲區掃描

- 新視窗若略過 handoff 頂部，仍可能偏航；靠 AGENTS 開局規則與 active marker 降低風險。
- 舊 handoff 內容仍保留，不可刪除歷史，但必須降權。
- P77 計畫此階段只是凍結入口，不代表可直接改程式。

### X3 時間敏感性

- 本計畫日期：2026-05-16
- Bootstrap 中的最新 commit 需以開局 `git status -sb` / `git log -1 --oneline` 校驗。

### X4 多角度同行審查

- **主公視角**：希望新視窗少讀檔也不做偏；L1 必須短、硬、可執行。
- **世界頂尖駭客 / 紅隊攻擊者視角**：此 Phase 不新增攻擊面；主要風險是文件誤導造成錯誤操作。
- **接手者視角**：只看 `ACTIVE_BOOTSTRAP` 就能知道下一步與禁止事項。
- **維運者視角**：handoff 不再用尾端舊句子決定下一步，降低事故風險。
- **X4-J 自動化邊界**：marker grep 只能證明格式存在，不能替代人工確認語意。
- **X4-K 使用者端審查官**：使用者不應被要求每次全讀大檔；入口應壓到可快速掃讀。

---

## 8. 風險清單

| 風險 | 機率 | 影響 | 緩解 |
|---|---:|---:|---|
| 舊 handoff 內容仍被誤讀 | 中 | 高 | archive marker + bootstrap 寫明唯一來源 |
| P77 計畫被誤認為已核准動工 | 中 | 高 | P77 狀態設為 FROZEN_PENDING_APPROVAL |
| 文件數增加造成負擔 | 中 | 中 | 新窗只讀 L1 + 當前 Phase |
| commit truth 再次漂移 | 中 | 中 | ACTIVE_OPERATION 明列 git truth check |

---

## 9. 工作階段

| Stage | 工作 | 驗收 |
|---|---|---|
| S1 | 新增 P76.1 計畫書 | 本檔存在且 Exit Criteria 明確 |
| S2 | 新增 P77-P84 總計畫與 ACTIVE_OPERATION | L2/L3 建立 |
| S3 | 新增 P77 當前 Phase 計畫 | L4 建立且狀態不可直接動工 |
| S4 | 更新 NEXT_SESSION_HANDOFF 頂部 | active/archive markers 存在 |
| S5 | 驗證 | `git diff --check` + rg markers |

---

## 10. 影響檔案清單

| 檔案 | 動作 | 理由 |
|---|---|---|
| `docs/PHASE_76_1_PLAN.md` | 新增 | 本 Phase 凍結計畫 |
| `docs/ACTIVE_OPERATION.md` | 新增 | L2 當前作戰狀態 |
| `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md` | 新增 | L3 P77-P84 總計畫 |
| `docs/PHASE_77_PLAN.md` | 新增 | L4 當前 Phase 計畫 |
| `NEXT_SESSION_HANDOFF.md` | 更新 | L1 唯一開局入口 |

---

## 11. Postmortem 預埋點

- 若後續新視窗仍讀到 archive 舊指令，代表 active marker 不夠醒目，P84 需補 doctor 檢查 handoff。
- 若 P77 被未核准動工，代表狀態機欄位不夠硬，需在 `ACTIVE_OPERATION.md` 增加更明確禁止事項。

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 攻擊者視角** | 本 Phase 不新增攻擊面，真正風險是文件誤導 AI 去改錯檔或跳過主公核准。 |
| **X4-B 接手者視角** | 接手者只讀頂部 active bootstrap 就要能判斷目前不可動 P77 runtime。 |
| **X4-C 災難情境** | 若 archive 舊段落仍被當成下一步，AI 可能重做 P70.5 或跳過 P77 核准。 |
| **X4-D 5 年後視角** | 未來維護者需要知道 handoff 是「頂部指令、下方歷史」，否則仍會讀錯來源。 |
| **X4-E 終端 vs IDE** | 終端環境能用 `rg` 驗證 marker，IDE 讀檔也能直接看到頂部封包。 |
| **X4-F 跨平台** | Markdown marker 與 PowerShell/rg 驗證在 Windows 本機可跑，日後 Linux CI 也可用同樣字串。 |
| **X4-G 主公個人視角** | 主公希望新視窗少讀檔也不做偏，因此 L1 必須短而硬。 |
| **X4-H 觀測** | P76.1 的可觀測成果是 marker、L2/L3/L4 文件與狀態機欄位可被 grep。 |
| **X4-I 主公可見性** | 主公看不到 AI 內部是否讀到舊段落，所以文件必須明示 archive 不可作下一步。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | active bootstrap 如果過期，反而會成為新的單點誤導。 | **S** | 0 | Resume Rule 強制新窗先跑 git truth check，不只信文字。 | 入計畫範圍 |
| 2 | P77 計畫已建立，AI 可能誤以為已可直接改程式。 | **S** | 0 | P77 狀態明列 `FROZEN_PENDING_APPROVAL`，Allowed Files 禁止 runtime。 | 入計畫範圍 |
| 3 | 舊 handoff 沒刪，仍可能被搜尋命中。 | A | 0 | 加 `ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION`，並在 L1 明令 archive 不作下一步。 | 入計畫範圍 |
| 4 | 文件分成 4 層可能增加讀取負擔。 | A | 0 | 新視窗只必讀 L1，L2/L3/L4 由 bootstrap 指名時才讀。 | 入計畫範圍 |
| 5 | marker grep 只能證明格式存在，不能保證 AI 遵守。 | A | 0 | AGENTS 開局規則與 ACTIVE_OPERATION 仲裁順序共同約束。 | 入計畫範圍 |
| 6 | TASK_HISTORY 仍追加新章，可能讓人誤以為歷史也是下一步來源。 | B | 0 | 明確規定 TASK_HISTORY 只作物理證據，不決定下一步。 | 入計畫範圍 |

---

## 12. 凍結戳記

- **主公核准**：2026-05-16
- **凍結版本**：v1.0
- **狀態**：CLOSED
- **凍結後變更**：若需修改本 Phase 範圍，新增 P76.1 補遺，不改寫本節。
