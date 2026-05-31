# 📋 P104 次階段融合計畫書 — 啟用斷言引擎 + health 告警 + shadow 防翻車

> **狀態**：FROZEN ✅（主公 2026-05-31 核准凍結｜lint PASS）｜**作者**：Opus 4.8｜**日期**：2026-05-31｜**前置**：P103 引擎回填完成（已 push）

---

## 0. Phase 元資料

| 欄位 | 值 |
|---|---|
| Phase ID | P104 |
| 名稱 | 次階段融合 — 啟用斷言引擎(G1) + health 告警(G2) + shadow 防翻車(G3) |
| 影響半徑 | 6-9 檔（標準偏重大）|
| 風險等級 | 中 |
| 可逆性 | 半可逆（新增檔為主 + guard 全 advisory 不升 strict，git 可回退）|
| 預估時長 | 1-2 session |
| 前置 Phase | P103（引擎已回填、308 tests 綠）|

> **編號說明**：本 Phase 是 P103「回填引擎」的次階段「啟用 + 補件」，屬新建設方向，故編 P104。若主公偏好 P103.2 可改。

---

## 0.5 狀態轉換清單（B-002）

- [x] DRAFT → 計畫書撰寫中
- [x] FROZEN → M1/M2 體檢通過、主公核准凍結（2026-05-31）
- [ ] RUNTIME → 開始實作
- [ ] CLOSED → 收官驗證 + TASK_HISTORY 追加

---

## 1. 目標 (Objective)

P103 已把 Hermes 融合引擎（preflight/斷言/密鑰/utils）回填進 AOV，但盤點發現引擎「裝了未發揮」。本 Phase 讓引擎真正生效：G1 填斷言 guard（目前 `guards: []` 空轉、0 覆蓋）、G2 回填 health.py（補「壞了會發 Discord 告警」的 runtime 防線）、G3 落地 shadow 觀察機制（兩端目前都只 docstring 提及、無實作）。G4 metrics 緩（掛 R-024，hooks 層、非引擎 scope）。

---

## 2. 觸發背景 (Why Now)

零幻覺盤點（三子代理交叉 + 行號證據）確認：Hermes 引擎優勢已無功能 gap，但 `governance_config.yaml:36` 的 `guards: []` 為空清單，斷言引擎每次必過空轉；AOV 缺 `gov/health.py` 的主動 smoke + 告警；shadow 在 `assertions.py`/`preflight.py` 皆無分支實作。主公裁示一次把「生效 + 告警 + 防翻車」裝齊。

---

## 3. Entry Criteria（入口條件）─ STR4

- [x] P103 引擎回填完成且 push（gov/ 5 檔 + governance_config.yaml）
- [x] 零幻覺盤點完成（G1-G4 證據齊、行號可驗）
- [x] AOV 既有測試綠（基線 308）
- [ ] 主公核准開 P104 並凍結本計畫書

---

## 4. Exit Criteria（退出條件）─ STR3

- [ ] G1：`governance_config.yaml` 填入 ≥3 條實際 guard（全 advisory），`py -m gov.assertions --check` 跑出非 0 覆蓋且不誤擋正常 repo
- [ ] G2：`gov/health.py` 回填、AOV `.agent/skills` 路徑契約驗證通過、`py -m gov.health` 可跑、無 webhook 時 graceful 只印不發
- [ ] G3：`assertions.py` 新增 shadow 分支（失敗只記錄不阻斷）+ shadow ledger（append-only、有 size cap）
- [ ] 既有測試不退（≥308）+ 新增 G1/G2/G3 單測
- [ ] TASK_HISTORY 追加 + 凍結戳記

---

## 5. ROI 評估（G4-2）

| 項目 | 評估 |
|---|---|
| 成本 | 1-2 session 實作 + 測試 |
| 效益 | 斷言引擎從空轉變實際守護；skill「壞了會叫」；guard 可安全升 strict（shadow 護網）|
| 風險 | 中（guard 全 advisory 起步、health graceful、shadow 不阻斷，blast radius 受控）|
| 不做的代價 | 回填的引擎永遠空轉、無 runtime 告警、guard 無安全升級路徑 |

---

## 6. 17 層稽核表（META2 強制填表）

### S 級層（必填）

| 層 | 適用 | 措施 |
|---|---|---|
| 1 代碼 | ✅ | gov/health.py + shadow 分支 PEP8、type hint、docstring |
| 2 邏輯 | ✅ | guard 比對邏輯、shadow「執行但不阻斷」分支邏輯正確 |
| 4 測試 | ✅ | G1 guard / G2 health / G3 shadow 各補單測 |
| 10 安全 | ✅ | webhook 只從 .env 讀不進 git；guard asserts 不執行任意碼 |

### A 級層

| 層 | 適用 | 措施 |
|---|---|---|
| 3 架構 | ✅ | gov/health.py 與 scripts/gen_skill_health.py 職責明確分工 |
| 5 資料 | ✅ | guards 宣告式定義 + shadow ledger schema 固定 |
| 6 可觀察 | ✅ | health Discord 告警 + shadow ledger + preflight 分級報告 |
| 7 韌性 | ✅ | health 無 webhook 只印（graceful）；guard advisory 不阻斷 |
| 13 可維護 | ✅ | 快照來源註記 + health 分工文件 |
| 14 文件 | ✅ | 計畫書 + docstring + 兩 health 分工說明 |
| 15 流程 | ✅ | 17 層 + M1/M2 + lint_phase_plan |

### B 級層（條件觸發）

| 層 | 適用 | 措施 |
|---|---|---|
| 8 效能 | ⚠️ | health subprocess 逾時保護 + shadow ledger size cap |
| 11 部署 | ✅ | git 分支 + 可回退 |
| 12 成本 | ⚠️ | guard advisory 不重複跑、shadow 輪轉避免膨脹 |
| 16 隱私 | ✅ | DISCORD_WEBHOOK 機敏值 .env + 佔位符，推送前掃描 |

---

### 層級互鎖驗證（META5）

- 動 Logic（shadow 分支 / guard 比對）→ 必動 Testing（補單測）✅
- 動 Architecture（gov/health.py 新模組）→ 必動 Documentation（docstring + 分工說明）✅

---

## 7. 跨切面檢查（X1-X4）

### X1 可逆性 (Reversibility)

- gov/health.py + shadow ledger 新增 → 刪除即回退
- governance_config.yaml guards 填入、assertions.py shadow 分支 → git 可回退
- guard 全 advisory 不升 strict → 不會誤擋（半可逆、低風險）

---

### X2 盲區掃描 (Blind Spot)

- health.py 路徑契約 skills vs .agent/skills 對不上 → 動工先驗證實際路徑
- shadow 分支可能與既有 strict/advisory 互相干擾 → 新增專屬測試隔離

---

### X3 時間敏感性 (Time Decay)

- guard 定義會隨專案演進腐化 → 登 RISK 定期復盤
- shadow ledger append-only 跑久會膨脹 → 設 size cap / 輪轉

---

### X4 多角度同行審查 (Multi-Role Review)

（詳見 Pre-flight M1 十一視角）

---

## 8. 風險清單

| 風險 | 等級 | 緩解 |
|---|---|---|
| guard 誤擋正常 commit | 中 | 全 advisory 起步 + shadow 觀察零誤判才升 strict + --allow-skip |
| webhook 機敏值外洩進 git | 高 | 只從 .env 讀 + 佔位符 graceful + 推送前掃描 |
| health 路徑契約對不上 | 中 | 動工驗證 .agent/skills 實際路徑 + 測試 |
| shadow 改動破壞既有斷言 | 中 | 每步對拍 pytest 不退 308 + shadow 專屬測試 |
| 既有測試回歸 | 中 | 每 Stage 對拍 pytest |

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 驗證 |
|---|---|---|
| G1 | governance_config.yaml 填 ≥3 條 guard（全 advisory）| py -m gov.assertions --check 非 0 覆蓋、不誤擋 |
| G2 | 回填 gov/health.py + 路徑契約修 + .env webhook + 分工文件 | py -m gov.health 跑通、無 webhook graceful |
| G3 | assertions.py 加 shadow 分支 + shadow ledger + preflight 整合 | shadow guard 失敗只記錄不阻斷、ledger 寫入 |
| C | 補單測 + 文件 + 既有測試對拍 | pytest ≥308 綠 |
| D | 收官（TASK_HISTORY + 主公核准 push）| 主公核准 |

---

## 10. 影響檔案清單（STR7，動工時定稿）

| 檔案 | 動作 |
|---|---|
| governance_config.yaml | 修改（填 guards）|
| gov/health.py | 新增（回填 + 路徑在地化）|
| gov/assertions.py | 修改（加 shadow 分支）|
| gov/preflight.py | 修改（shadow 整合，視需要）|
| gov/shadow_ledger.py | 新增（shadow 持久化）|
| tests/test_*.py | 新增（G1/G2/G3）|
| docs/（health 分工說明）| 新增/修改 |

---

## 11. Postmortem 預埋點（G6）

- guard 填入後 shadow 觀察期是否出現誤判？
- health.py 路徑契約在 AOV `.agent/skills` 是否真的對上？
- shadow ledger 設計是否過重（YAGNI 檢查）？

---

## ✈️ Pre-flight 多視角體檢（STR10，凍結前必過）

### M1 強制填表（十一視角）

| 視角 | 內容 |
|---|---|
| **X4-A 攻擊者視角** | 惡意 guard 定義或 webhook 注入？guard 的 asserts 只做檔案存在與內容比對、不執行任意碼；webhook 從 .env 讀不寫死，推送前掃描防外洩 |
| **X4-B 接手者視角** | 半年後接手者懂 G1/G2/G3 分工？health.py 與 gen_skill_health 文件明確分工，guard config 加註解，shadow ledger 格式文件化 |
| **X4-C 災難情境** | guard 誤判把正常 commit 全擋住？guard 全 advisory 起步，shadow 觀察零誤判才升 strict，保留 --allow-skip 逃生艙 |
| **X4-D 5 年後視角** | shadow ledger 無限長大、guard 定義腐化？ledger 設 size cap 與輪轉，guard 隨專案演進登 RISK 定期復盤 |
| **X4-E 終端 vs IDE** | health/shadow CLI 在終端與 IDE 都能跑？用 py launcher + sys.executable，純 CLI 無 IDE 依賴 |
| **X4-F 跨平台** | .agent/skills 路徑與 webhook 在 Windows/Mac 一致？用 pathlib 處理路徑，webhook 用 urllib 跨平台 |
| **X4-G 主公個人視角** | 主公能一鍵看 health、跑 guard？py -m gov.health --notify 與 py -m gov.assertions --check 一鍵執行 |
| **X4-H 觀測** | guard/health 壞了看得到？health 失敗發 Discord 告警，shadow ledger 記錄判定，preflight 分級報告與 exit code |
| **X4-I 主公可見性** | 主公知道填了哪些 guard、改了什麼？計畫書影響清單 + guard config 可讀 + 動工 dry-run 預覽 |
| **X4-J 自動化建議性工具邊界** | guard/shadow 召回率限制？末行免責標示工具是輔助非萬能，人工覆核仍必要 |
| **X4-K 使用者端審查官** | 主公能否決 guard 升 strict？guard 升 strict 需主公核准（兩道關 + 人工），dry-run→拍板→可回退 |

---

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發 | 意見 |
|---|---|---|
| 架構師 | ✅ | gov/health.py 自包含、與 scripts 分工 |
| 安全官 | ✅ | webhook 不外洩、guard 不執行任意碼 |
| 測試官 | ✅ | G1/G2/G3 各補單測、對拍 308 |
| 維運官 | ✅ | health 告警 + shadow ledger 可觀察 |

---

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 🔴 紅隊質疑 | 🔵 藍隊回應 | 攻擊力 | 處置 |
|---|---|---|---|---|
| 1 | 填的 guard 誤擋正常 commit／開發流程 | 全 advisory 起步 + shadow 觀察零誤判才升 strict + --allow-skip 逃生 | **S** | 入計畫 Stage G1/G3 |
| 2 | health.py 的 webhook 機敏值外洩進 git | webhook 只從 .env 讀、佔位符 graceful、推送前掃描 | **S** | 入計畫 Stage G2 |
| 3 | health 路徑契約對不上導致誤報全部 fail | 動工先驗證 AOV .agent/skills 實際路徑 + 測試覆蓋 | A | 入計畫 Stage G2 |
| 4 | shadow ledger 無限長大或設計過重 | 最小 append-only jsonl + size cap，YAGNI 檢查 | A | 入計畫 Stage G3 |
| 5 | 改 assertions.py 加 shadow 破壞既有 strict/advisory | 每步對拍 pytest 不退 308 + 新增 shadow 專屬測試 | **S** | 入計畫 Stage G3/C |
| 6 | health.py 與 gen_skill_health 職責混淆漂移 | 文件明確分工：跑 smoke+告警 vs 出靜態看板 | B | 入 RISK_REGISTRY |

---

## ✈️ STR9 — Skill 收官 entry_points 檢查

（本 Phase 不涉及 skill 收官，N/A — 動的是 gov/ 引擎與 config，非 .agent/skills 的 SKILL.md）

---

## 12. 凍結戳記

```
FROZEN by Opus 4.8 @ 2026-05-31（主公核准凍結）
M1: 11/11 視角填表完成
M2: 6 條質疑（3 S 級）
lint_phase_plan: ✅ PASS
主公核准: ✅ 2026-05-31
```
