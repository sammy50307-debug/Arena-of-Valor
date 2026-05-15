# Phase P73 計畫書 — 模型選擇指引 v1.2 OpenAI / Codex 分支（凍結版）

> 凍結日期：2026-05-15
> 凍結人：主公（授權）+ Codex（草擬）
> 計畫書版本：v1.0 frozen

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P73 |
| **Phase 名稱** | 模型選擇指引 v1.2 OpenAI / Codex 分支 |
| **凍結日期** | 2026-05-15 |
| **影響半徑** | 標準（預估 5-6 檔） |
| **預估投入時數** | 0.8 h |
| **Token budget** | 25K tokens |
| **負責模型** | GPT-5.3-Codex（文件落地 + repo 修改）；必要查證以 OpenAI 官方來源為準 |

## 0.5 狀態轉換清單

N/A。本 Phase 不變更 skill / module / workflow 生命週期狀態，只更新模型選擇治理文件。

---

## 1. 目標 (Objective)

將既有 Claude / Gemini 為主的模型選擇指引升級為 v1.2，補上主公目前實際使用的 OpenAI / ChatGPT / Codex 雙主力規則：**想清楚用 GPT-5.5，進 repo 動工用 GPT-5.3-Codex，小任務用 GPT-5.4-Mini，卡住升 reasoning effort 或切換視角**。

## 2. 觸發背景 (Why Now)

主公回鍋 ChatGPT 後，實際模型選單已包含 GPT-5.5、GPT-5.4、GPT-5.4-Mini、GPT-5.3-Codex、GPT-5.2。原 `docs/MODEL_SELECTION_GUIDE.md` v1.1 仍以 Sonnet / Opus / Gemini 為主，與 Codex app 當前工作流不一致，會讓 Phase 計畫書的「負責模型」欄繼續漂移。

## 3. Entry Criteria

- [x] 主公確認採用建議方向：OpenAI 雙主力規則
- [x] 已查到現有模型指引主檔：`docs/MODEL_SELECTION_GUIDE.md`
- [x] 已確認 PHASE_TEMPLATE 仍列舊模型欄位
- [x] 官方資訊需以 OpenAI Help / Platform / Pricing / Codex rate card 查證

## 4. Exit Criteria

- [ ] `docs/MODEL_SELECTION_GUIDE.md` 升 v1.2，新增 OpenAI / ChatGPT / Codex 分支
- [ ] `docs/PHASE_TEMPLATE.md` 的「負責模型」欄納入 GPT-5.5 / GPT-5.3-Codex / GPT-5.4-Mini
- [ ] `AGENTS.md` 模型選擇縮版同步 OpenAI 雙主力規則
- [ ] `NEXT_SESSION_HANDOFF.md` 記錄 P73 完成與下一步
- [ ] `TASK_HISTORY.md` 追加 P73 無損紀錄
- [ ] `git diff --check` 無 whitespace error

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 0.8 h |
| 預估收益等級 | 高 |
| 收益描述 | 之後每次 Phase 開工可直接判斷何時用 GPT-5.5、何時用 GPT-5.3-Codex，降低錯用高價模型或低能力模型的成本 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | Markdown 小範圍修改 | 文件表格破格式 | `rg` + `git diff --check` |
| **2. 邏輯層 (Logic)** | OpenAI 分支不取代舊 Claude/Gemini 分支 | 新舊規則衝突 | 寫成「OpenAI / Codex 分支」，保留跨助理通用規則 |
| **4. 測試層 (Testing)** | diff check + 關鍵字 grep | 文件無單測 | 用可檢查的 Exit Criteria 驗收 |
| **10. 安全層 (Security)** | 不新增外部執行邏輯 | 官方價格 / 模型資訊可能過期 | 標註查證日期與回顧觸發 |

### A 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 主檔 + 縮版 + 模板欄位同步 | 三檔漂移 | 在 guide §8 影響半徑補 OpenAI/Codex |
| **5. 資料層 (Data)** | N/A，不動業務資料 | 無 |
| **6. 可觀察性層 (Observability)** | TASK_HISTORY 記錄決策 | 後續不知道為何改 | 無損紀錄 |
| **7. 韌性層 (Resilience)** | 卡住切換規則 | 模型卡住硬撐 | GPT-5.3-Codex ↔ GPT-5.5 高/超高切換條款 |
| **13. 可維護性層 (Maintainability)** | 保留舊分支並新增 OpenAI 分支 | 文件變長 | TL;DR 與快速決策表先行 |
| **14. 文件層 (Documentation)** | 主軸即文件更新 | 名稱 / 價格過期 | 標日期與官方來源 |
| **15. 流程層 (Process)** | Phase plan frozen 後執行 | 未經核可改治理文件 | 主公已授權「規劃完草案並凍結後繼續」 |

### B 級層

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **12. 成本層 (Cost)** | 模型 token / credit 選擇 | 補 GPT-5.5 vs GPT-5.3-Codex 成本差 | 誤用高價模型 | 寫入「想清楚 / 動工省錢」口訣 |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Documentation 層 → 已動 Process 層
- [x] 動 Cost 層 → 已動 Observability 層

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_73_PLAN.md` | 可逆 | ✅ |
| 修改模型指引 / AGENTS / PHASE_TEMPLATE / handoff / TASK_HISTORY | 半可逆 | ✅ |

### X2 盲區掃描

- [x] log 副作用：無 runtime log
- [x] 中間檔產出：無
- [x] 系統狀態變更：只改 git tracked Markdown

### X3 時間敏感性

- 本計畫凍結日期：2026-05-15
- 本計畫過期日期：2026-08-15
- 風險記錄帶日期：✅

### X4 多角度同行審查

- **主公視角**：主公需要能在 5 秒內決定用 GPT-5.5、GPT-5.3-Codex 或 GPT-5.4-Mini。
- **世界頂尖駭客 / 紅隊攻擊者視角**：本 Phase 不新增執行面攻擊點，但若把模型選錯用於安全審查，可能低估注入 / secrets / CI 風險，因此安全任務不得降 Mini。
- **接手者視角**：未來 AI 必須看得懂這是 OpenAI 分支，不是廢棄 Claude/Gemini 指引。
- **X4-J 自動化建議性工具邊界**：本 Phase 不新增自動化建議工具；N/A。
- **X4-K 使用者端審查官**：若口訣太長，主公仍會回到憑感覺選模型；因此 TL;DR 必須保留一句話。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | OpenAI 模型價格 / rate card 後續更新 | 中 | 中 | 時間敏感 | 標註 2026-05-15 查證，保留回顧觸發 |
| R2 | 舊 Claude/Gemini 分支與 OpenAI 分支混淆 | 中 | 中 | 流程 | 章節標明「OpenAI / ChatGPT / Codex 分支」 |
| R3 | P73 疊在 P72.5 未 commit 變更上 | 中 | 低 | git | 不碰 untracked 檔，final 明列變更範圍 |

**高風險加權檢查**：
- 高風險數量：0
- 加權分數：3
- 是否 ≥ 5 須請示主公：否

---

## 9. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1** | 官方來源查證 + 凍結本計畫 | 避免憑印象寫模型價格 | 官方來源列入 guide |
| **S2** | 更新主檔與模板欄位 | 解決現況漂移 | `rg GPT-5.5 docs/MODEL_SELECTION_GUIDE.md docs/PHASE_TEMPLATE.md` |
| **S3** | 更新 AGENTS / handoff / history | 新視窗可延續 | `git diff --stat` + `git diff --check` |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_73_PLAN.md`

**修改**：
- `docs/MODEL_SELECTION_GUIDE.md`
- `docs/PHASE_TEMPLATE.md`
- `AGENTS.md`
- `NEXT_SESSION_HANDOFF.md`
- `TASK_HISTORY.md`

**刪除**：
- 無

**影響但未直接修改**：
- 未來 Phase 計畫書的「負責模型」欄

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 主公中途否決重來
- [ ] 官方資訊與現有模型選單明顯衝突
- [ ] P73 後 3 次仍錯用模型

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 安全審查、secrets、CI/CD、不可逆操作不得用 Mini；必須指定 GPT-5.5 高或 GPT-5.3-Codex 高。 |
| **X4-B 接手者** | 新人會疑惑 Claude/Gemini 舊規則是否廢棄，因此 OpenAI 分支必須明示「新增分支，不取代跨助理規則」。 |
| **X4-C 災難情境** | 情境：主公用 Mini 做重大 Phase 架構判斷；緩解：TL;DR 寫明重大決策用 GPT-5.5 高。 |
| **X4-D 5 年後** | 模型名必然過時，文件需保留版本日期與強制回顧條件。 |
| **X4-E 終端 vs IDE** | ChatGPT 對話適合 GPT-5.5，Codex repo 動工適合 GPT-5.3-Codex；不能只寫單一預設。 |
| **X4-F 跨平台 Win/Mac/Linux** | 本 Phase 只改 Markdown，不涉及 shell 差異；驗收命令使用 PowerShell 可執行的 `rg` / `git`。 |
| **X4-G 主公個人視角** | 主公需要一句口訣，不想每次翻長表；文件必須保留「想清楚 / 動工 / 小事 / 卡住」四格。 |
| **X4-H 觀測 / 治理** | 模型指引已在 RISK_REGISTRY 有漂移風險，P73 應降低三檔同步不一致。 |
| **X4-I 主公可見性** | 本次會在 handoff 與 TASK_HISTORY 明列改了哪些模型規則，避免新視窗看不出原因。 |
| **X4-J 自動化建議性工具邊界** | 不新增自動化工具；本視角 N/A，但仍記錄理由。 |
| **X4-K 使用者端審查官** | 若表格太複雜，主公會放棄使用；必須讓最短口訣出現在 TL;DR。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、下一步是否清楚 | 觸發；P73 範圍限定為模型指引，不順手重構其他治理文件 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界 | 觸發；安全 / 不可逆任務不得降 Mini |
| **Patric 型使用者端審查官** | 固定必看 | 主公是否好用 | 觸發；保留一句口訣 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff | 來源、可追溯、避免空泛 | 觸發；官方來源與日期寫入 |
| **Marcus 型數據分析師** | 涉及價格 / token | 沒數據時明說 | 觸發；價格以官方 rate card / pricing 為準 |
| **Oliver 型設計審查** | UI / 視覺 | N/A | N/A；純文件 |
| **Penny 型 CFO** | 成本 / token | 成本爆量 | 觸發；補 GPT-5.5 vs GPT-5.3-Codex 成本差 |
| **Jason 型執行 / DevOps** | Git / 腳本 / 環境 | 可執行性 | 觸發；驗收用 `rg` / `git diff --check` |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 模型資訊很快過期，今天寫明天就錯 | A | N/A | 標查證日期與回顧條件 | 接受 |
| 2 | 把 OpenAI 分支加進跨助理指引會混亂 | B | N/A | 分章，不取代原規則 | 接受 |
| 3 | GPT-5.5 / GPT-5.3-Codex 價格差若寫錯會誤導主公 | S | N/A | 只寫官方查證值與相對倍率 | 接受 |
| 4 | P73 疊在 P72.5 未 commit 上，git 範圍可能混雜 | A | N/A | final 明列 P72.5 + P73 tracked files，不碰 untracked | 接受 |
| 5 | Mini 用途寫得太多會被拿去做重要任務 | S | N/A | 明確列「不得用於安全 / 架構 / 不可逆」 | 接受 |

---

## 12. 凍結戳記

- **凍結人**：主公授權 + Codex
- **凍結時間**：2026-05-15
- **凍結後變更**：若後續發現官方 pricing 與文件不同，新增 P73 補遺，不直接重寫本計畫。
