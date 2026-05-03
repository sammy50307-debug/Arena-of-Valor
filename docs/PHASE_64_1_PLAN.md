# 📋 Phase 64.1 — Token 防線回溯補強（7 項追溯優化）

> **基於 PHASE_TEMPLATE.md v1.0 (混合版) 生成 + v3.1 框架稽核**

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P64.1（Phase 64 補遺，遵 STR5 命名規約） |
| **Phase 名稱** | Token 防線回溯補強（7 項追溯優化） |
| **凍結日期** | 2026-05-03 |
| **狀態** | ✅ **收官 2026-05-03**（7 項全於同日直接落地，無需另立動工期） |
| **影響半徑** | **標準 (3-9 檔)** ─ META3，依 v3.1 Patch-1 走 S+A 11 層稽核 |
| **預估投入時數** | 6 小時（7 項分批） |
| **Token budget** | ~15K tokens |
| **負責模型** | Sonnet 4.6（主執行）+ Opus 4.7（架構判斷救援） |

---

## 1. 目標 (Objective)

針對 Phase 64 v0.4 token 優化計畫的四層防線 + 13 元件，依 v3.1 框架回溯診斷結果，補入 7 項缺失優化，使四層防線達到「**抗熵 + 可測 + 可觀察 + 可回滾**」四項硬指標。

## 2. 觸發背景 (Why Now)

2026-05-03 主公採納 v3.0 治理級框架後，要求用框架回頭診斷 Phase 64 — Token 優化計畫 v0.4。診斷報告（`docs/PHASE_64_RETROACTIVE_AUDIT.md`）發現 7 項可立即執行的高 ROI 優化，並識別 1 個致命缺口（**G5-1 規則退化警示缺**：四層防線若 90 天後沒人記得是否還在運作，會默默腐爛）。

主公裁示：先列成草案凍結，動工順序排在 Phase 65 之前。

## 3. Entry Criteria（入口條件）─ STR4

- [x] 前置 Phase 已收官：Phase 64 已收官（commit 2026-05-01）
- [x] 資料/依賴已備：`docs/PHASE_64_RETROACTIVE_AUDIT.md` 已凍結
- [x] 主公已核准：2026-05-03 視窗主公裁示「A 要做 + B 是 + C 是」
- [ ] 風險登記簿無未解高風險：⚠️ 需先動工 #2 G5-1 規則退化警示，才能解鎖未來 Phase 入場條件

## 4. Exit Criteria（退出條件）─ STR3

- [ ] **#1 hook 單元測試**：4 個 hook scripts 各 ≥ 3 cases（檔案不存在/計數溢位/空 stdin），全綠
- [ ] **#2 G5-1 規則退化警示**：90 天偵測機制落地，產出 `scripts/rule-decay-check.sh` + cron 排程或啟動鉤子
- [ ] **#3 R1 fail-loud**：4 個 hooks 加錯誤外推，失敗時 stderr 紅字輸出 + Claude prompt 中可見
- [ ] **#4 G4-1 framework metric**：實測 token 節省（取 5 次對話樣本前後對比，驗 92-96% 是否真實）
- [ ] **#5 DOC2 ADR**：`docs/adr/001-four-layer-defense-rationale.md` 寫成
- [ ] **#6 V2 rollback**：`.claude/settings.json.before-p64.bak` 留檔
- [ ] **#7 G6-1 成功經驗 PM**：`docs/postmortems/2026-05-01-phase-64-success-design.md` 寫成
- [ ] **編年史**：TASK_HISTORY.md 補錄 Phase 64.1 完整章節 + Obsidian 鏡像 + push origin/main

## 5. ROI 評估 ─ G4-2

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 6 h（#1=2h, #2=1h, #3=30m, #4=1h, #5=30m, #6=5m, #7=1h） |
| 預估收益等級 | **高** |
| 收益描述 | (1) **抗熵保命**：#2 防止四層防線 90 天後默默腐爛；(2) **可測性**：#1 防止 hook 默默失效；(3) **可觀察**：#3 失敗主動報錯；(4) **可回滾**：#6 應急救命；(5) **跨 Phase 學習**：#5 + #7 留決策歷程 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表（v3.1 Patch-1：標準 Phase → S + A 共 11 層）

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | C1（Pydantic schema 守門用 dataclass 替代）, C2（atomic write）, C6（structured logging） | hook script 用 bash 不適合 Pydantic | 改用 jq + schema 驗證或 `set -euo pipefail` 守門 |
| **2. 邏輯層 (Logic)** | L5（最低門檻：90 天閾值不能設太短誤殺活規則）| 90 天設太長導致死規則持續存在 | 主公可調 `RULE_DECAY_DAYS` 環境變數 |
| **4. 測試層 (Testing)** | T1（每 hook ≥ 3 cases）, T3（E2E：跑完整 prompt 流程驗 hook 觸發） | bash 測試框架選擇困難 | 用 `bats-core` 或純 shell `assert` |
| **10. 安全層 (Security)** | S1（hook 注入字串 escape） | hook 把 history 計數寫入主 prompt 可能含特殊字元 | bash 變數雙引號 + heredoc 守門 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層** | A1（四層防線權重不變，本 Phase 不重構） | 改 hook 機制可能波及四層平衡 | 嚴守「補強不重構」原則 |
| **5. 資料層** | D1（為 phase_map / WIP_PHASES 加 schema_version=1）, D3（rule decay log 留 source_chain） | schema 變更導致現有元件爆 | D1 採增量加入，舊版相容 |
| **6. 可觀察性層** | O1（rule decay 每次掃描寫 log）, O2（記錄哪幾條規則 90 天無觸發 metric）, O3（首次發現死規則時推播警示） | log 寫太密 | 滾動切割 + 月歸檔 |
| **7. 韌性層** | R1（rule-decay-check.sh 失敗 fallback 到「不警示但寫 stderr」）, R2（檔案掃描超時 30s 中止）, R3（主程式不依賴 rule decay，全死也不爆 pipeline） | rule decay 拖慢主流程 | 異步背景跑、絕不阻塞 |
| **13. 可維護性層** | M1（更新 `docs/TECH_DEBT.md`：列 P64 13 元件清單供未來砍/換） | 13 元件積成黑箱 | M1 統一登記 |
| **14. 文件層** | DOC1（4 個 hook scripts 頂部加 docstring）, DOC2（`docs/adr/001-four-layer-defense-rationale.md`） | 未寫 ADR 後人不懂為何選 4 層 | DOC2 為 #5 主軸 |
| **15. 流程層** | PR1（用 PHASE_TEMPLATE.md，已套）, PR2（Exit Criteria 已列）, PR3（commit 走 `chore(P64.1):`） | 流程鬆散 | 嚴守規約 |

### B 級層（v3.1 Patch-2 機械式觸發判斷）

| 層 | 觸發關鍵字檢查 | 結果 |
|---|---|---|
| **8. 效能層** | 「`hook` / `async`」 | ✅ **觸發**（hook 每 turn 執行）→ P1（<10ms latency 目標） |
| **9. UX/A11y 層** | 「`.html` / `templates/`」 | ❌ **未觸發**（純後端 hook 改造） → N/A |
| **11. 部署層** | 「`.github/workflows/` / `settings.json` / `.env`」 | ✅ **觸發**（settings.json 改）→ V1（feature flag `RULE_DECAY_ENABLED`）, V2（settings.json.bak 為 #6） |
| **12. 成本層** | 「`gemini` / `openai` / `token` / `cost`」 | ✅ **觸發**（本 Phase 主題就是 token cost） → B1（rule decay 不增加額外 token） |
| **16. 隱私層** | 「`scraper` / `dcard` / `bahamut`」 | ❌ **未觸發** → N/A |
| **17. i18n 層** | 「`regional` / TW/TH/VN」 | ❌ **未觸發** → N/A |

### 層級互鎖驗證 ─ META5

- [x] 動 Logic 層 → 已動 Testing 層（T1）
- [x] 動 Architecture 層 → 已動 Documentation 層（DOC2 ADR）
- [x] 動 Data 層 → 已動 Maintainability 層（M1 TECH_DEBT）
- [x] 動 Security 層 → 已動 Testing 層（S1 注入測試）
- [x] 動 Performance 層 → 已動 Observability 層（P1 + O2）

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 4 個 test scripts | 可逆 | — |
| 新增 `scripts/rule-decay-check.sh` | 可逆 | — |
| 修改 `.claude/settings.json` | 半可逆（#6 已備份） | — |
| 新增 ADR / Postmortem 文件 | 可逆 | — |
| 修改既有 hook scripts 加 fail-loud | 半可逆（git revert 可救） | — |

**不可逆動作**：無

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [ ] log 副作用：`logs/rule_decay.log` 每月可能長至 ~100KB
- [ ] 中間檔產出：`data/rule_usage_index.json` 記錄每條規則最後觸發時間
- [ ] 系統狀態變更：`.env` 新增 `RULE_DECAY_ENABLED` / `RULE_DECAY_DAYS=90`

### X3 時間敏感性 (Time Decay) — v3.1 Patch-3

- 本計畫凍結日期：2026-05-03
- 本計畫過期日期：2026-08-03（3 個月後若未動工需重新審視）
- ⚠️ **特別記**：本 Phase 動工順序排於 Phase 65 之前，若 Phase 65 開工時本 Phase 仍未動工 → 視為 STR4 Entry Criteria 違反

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：7 項追溯優化的優先級主公已點頭 ⭐⭐⭐ 三項先做、其他列管。**通過**。
- **攻擊者視角**：⚠️ #2 rule decay 90 天閾值若被惡意改成 1 天 → 所有規則每天被警示為死，造成 alarm fatigue；⚠️ #3 fail-loud 若把敏感資料 stderr 出來會洩漏。**緩解**：#2 設環境變數下限、#3 escape 守門。
- **接手者視角**：DOC2 ADR + DOC1 hook docstring 已覆蓋；半年後新人讀 P64.1 章節 + ADR 可上手。**通過**。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| RA1 | rule decay 閾值設太短誤殺活規則 | 中 | 中 | 業務 | 預設 90 天，下限 30 天 |
| RA2 | hook fail-loud 把敏感資料 stderr | 低 | 高 | 代碼可控 | escape + 白名單欄位 |
| RA3 | bats-core 測試框架引入新依賴 | 低 | 低 | 環境依賴 | 改用純 shell assert |
| RA4 | settings.json.bak 與真本不同步 | 低 | 中 | 業務 | bak 機制只在 P64.1 動工時建一次，事後改本檔不更新 bak（這是預期行為） |
| RA5 | rule_usage_index.json 損毀 | 低 | 中 | 代碼可控 | C2 atomic write + .bak |
| RA6 | rule decay 拖慢 Claude prompt latency | 低 | 中 | 環境依賴 | 異步背景，絕不阻塞主流程 |

**高風險加權檢查（META4）**：
- 高機率：0 項
- 中機率高影響：0 項
- 中機率中影響：1 項（RA1）
- 加權分數：**1 分**（遠低於 5）→ ✅ **無須請示主公**

---

## 9. 工作階段 (Stages)

> ⚠️ **動工順序**：本 Phase 排在 Phase 65 動工之前

| Stage | 內容 | 對應追溯項 | 投入 | 驗收 |
|---|---|---|---|---|
| **S1 抗熵核心** | #2 G5-1 規則退化警示（最致命缺口優先解） | #2 | 1h | `scripts/rule-decay-check.sh` 跑通、預設 90 天閾值 |
| **S2 韌性補強** | #3 R1 fail-loud + #6 V2 rollback bak | #3, #6 | 35m | hook 失敗 stderr 紅字、bak 已建 |
| **S3 測試守護** | #1 hook 單元測試（4 hooks × 3 cases） | #1 | 2h | T1 全綠 |
| **S4 文件留檔** | #5 DOC2 ADR + #7 G6-1 Postmortem | #5, #7 | 1.5h | 兩份 .md 寫成 |
| **S5 量化驗證** | #4 framework metric 實測 token 節省 | #4 | 1h | 5 樣本對比表進 PM |

---

## 10. 影響檔案清單 ─ STR7

**新增**：
- `scripts/rule-decay-check.sh`（#2）
- `tests/test_hooks/test_check_history_budget.sh`（#1）
- `tests/test_hooks/test_history_tail.sh`（#1）
- `tests/test_hooks/test_finalize_phase.sh`（#1）
- `tests/test_hooks/test_user_prompt_submit.sh`（#1）
- `data/rule_usage_index.json`（#2 副產物）
- `docs/adr/001-four-layer-defense-rationale.md`（#5）
- `docs/postmortems/2026-05-01-phase-64-success-design.md`（#7）
- `.claude/settings.json.before-p64.bak`（#6）

**修改**：
- `.claude/check_history_budget.sh`（#3 fail-loud）
- `scripts/history-tail.sh`（#3 fail-loud）
- `scripts/finalize-phase.sh`（#3 fail-loud）
- `.claude/settings.json`（新增 rule-decay PreToolUse hook，需 V2 bak 守門）
- `.env.example`（新增 `RULE_DECAY_ENABLED`, `RULE_DECAY_DAYS`）
- `docs/TECH_DEBT.md`（M1 登記 13 元件清單，若不存在則新建）

**刪除**：
- 無

**影響但未直接修改**：
- `memory/MEMORY.md`（規則使用率被 #2 統計，但檔案本身不改）
- `memory/feedback_*.md`（同上）

---

## 11. Postmortem 預埋點 ─ G6

收官後若觸發以下情境必寫 Postmortem：
- [ ] #1 hook 測試發現既有 hook 有 silent bug
- [ ] #4 實測 token 節省遠低於 92-96%（揭穿 P64 預期效益虛報）
- [ ] #2 rule decay 機制誤殺活規則
- [ ] 任何「我以為...結果不是」事件 (G2-3)

Postmortem 位置：`docs/postmortems/2026-MM-DD-phase-64-1-<topic>.md`

---

## 12. 凍結戳記

- **凍結人**：主公（核准）+ Opus 4.7（草擬）
- **凍結時間**：2026-05-03
- **動工狀態**：⏳ **凍結，待動工**（順序：Phase 64.1 → Phase 65）
- **凍結後變更**：禁止；如需修改，新增章節「Phase 64.1.X 補遺」並引用本檔

---

*本計畫書受 17 層品質框架 v3.1 + STR1 戰略通則保護，為 v3.0 → v3.1 升級的試金石產物。*
