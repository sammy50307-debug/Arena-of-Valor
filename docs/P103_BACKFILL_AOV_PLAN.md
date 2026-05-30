# 📋 P103 回填 AOV 計畫書 — GOV-PORT 融合引擎裝回母本

> 混合版 v1.2 模板 ｜ 撰於 2026-05-31 ｜ 狀態：**FROZEN（主公 2026-05-31 核准凍結）**
> 施工依據：`Hermes/docs/gov-port/G0_DEEPDIVE_BLUEPRINT.md` + `skills-governance/docs/BACKFILL_AOV_HANDOFF.md`
> 參考實作：`D:/skills-governance/gov/`（6 模組）

---

## 0. Phase 元資料

| 欄位 | 值 |
|---|---|
| Phase 編號 | **P103**（git 最新 P102 → 順延；若與既有編號衝突，收官時對齊） |
| Phase 名稱 | 回填 AOV — GOV-PORT 融合引擎裝回母本 |
| 影響半徑 | **10+ 檔（重大）→ 全層稽核**（META3） |
| 戰線分類 | 治理 / 後端工具鏈（與當前 P101/P102 known-issue-guard 戰線不同） |
| 主導模型 | Opus 4.8（跨多系統融合 + 新架構） |
| 撰寫日期 | 2026-05-31 |
| 主公拍板前提 | ①引擎複製成 AOV 自包含 ②拆兩 Stage（先順手修、後引擎）③趁熱連做 ④新 guard 一律 advisory/shadow 零 strict |

---

## 0.5 狀態轉換清單（B-002）

`DRAFT` → （過 M1+M1.5+M2 + 主公核准）→ `FROZEN` → `IN_PROGRESS` → （Stage A 對拍 307 不退）→ （Stage B 對拍 + shadow 觀察）→ `DONE`
- 回退條件：任一 Stage 對拍測試數 < 307 或既有 checker 退化 → 該 Stage 回退、停工請示。

---

## 1. 目標 (Objective)

把 `D:/skills-governance` 融合改良過的治理引擎，以**快照複製、AOV 自包含**方式裝回 AOV 母本，範圍＝手冊 §3 六項，拆兩 Stage：
- **Stage A 順手修**（修 AOV 既有 3 問題）：X4 9→11 視角 drift、cross_phase_review×m4 去重、metrics 接線根因。
- **Stage B 引擎**（新增 3 基礎設施）：preflight 編排器、斷言引擎+lint_guards、密鑰掃描融合。

---

## 2. 觸發背景 (Why Now)

GOV-PORT G0-G3 已收官（融合引擎 + 防翻車裝甲），但改良只活在實驗 repo `skills-governance`，AOV 母本仍是抽出前的舊版。回填＝把升級裝回每天在用的母本，完成「AOV→抽出融合→回填」閉環。基礎設施已齊、ROI 最高、未知最小（手冊 §2）。

---

## 3. Entry Criteria（入口條件）─ STR4

- [x] AOV 基線 **307 passed in 3.90s**（2026-05-31 實測，pytest 9.0.3 / Python 3.10.8）
- [x] 讀畢 `G0_DEEPDIVE_BLUEPRINT.md`（融合 schema + 12+2 清單）+ 回填手冊
- [x] 環境確認：**必須用 `py` launcher**（`python` 指向 WindowsApps Store stub，非互動空退出 exit 49）
- [x] 三項順手修落點**驗證屬實**（非假設）：X4 ✅、去重 ✅、metrics ⚠️待動工驗接線
- [x] 主公拍板裝法/切分/節奏（見 §0 前提）

---

## 4. Exit Criteria（退出條件）─ STR3

1. 回填後 **`py -m pytest tests/` == 307 passed 不退**（新增測試另計，須全綠）。
2. Stage B 新引擎全部 **advisory/shadow，零 guard 升 strict**。
3. 每段改動 **dry-run 留存 + 可回退**（git 分支 / 備份）；不可逆動作經主公親口確認。
4. 既有 24 支 governance checker（governance_doctor / slo_checker / system_doctor …）**不退化**。
5. 啟發式工具（斷言引擎 / lint_guards）**CLI 末行印召回率免責邊界**（X4-J）。
6. TASK_HISTORY 追加 P103 章節（六塊格式，cat>>heredoc）、影響半徑表更新（STR7）。

---

## 5. ROI 評估（G4-2）

| 維度 | 評估 |
|---|---|
| 收益 | 母本升級；24 checker 獲統一閘門；消 2 處重複邏輯；修 metrics 永不執行根因；X4 視角對齊模板 v1.2 |
| 成本 | 開發時間（8 小 + 4 中規模）；AOV 新增 `gov/` 模組與 `.governance/` 設定的長期維護 |
| 邊際效益 | Stage A 高（低成本修真 bug）；Stage B 中（基礎設施，價值高但需 shadow 觀察期） |
| 停損點 | 對拍測試退化且 30 分內無法定位 → 回退該段、登記 RISK_REGISTRY、停工請示 |

---

## 6. 17 層稽核表（META2 強制填表）

### S 級層（必填）

| 層 | 本 Phase 動作 | 風險 |
|---|---|---|
| **代碼** | 複製 gov/ 6 模組進 AOV、改 3 腳本去重/補視角、新增 .governance/ 設定 | 複製版與源分叉（見 M2-1） |
| **邏輯** | 去重合併需確認兩函式邏輯等價；metrics 接線根因需驗 AOV 實況 | 細微差異致回歸（M2-4） |
| **測試** | 每段對拍 307 基線；A2 去重補等價測試；A3 補「import 觸發 record」反向測試；B 引擎各補單元測試 | 測試數退化即 FAIL |
| **安全** | 密鑰掃描融合：聯集 regex + .env 比對；**絕不回傳/落 log 真實值**（聖旨：資安>紀錄） | regex 過寬誤報 / 真值外洩（M2-5，S 級） |

### A 級層

| 層 | 本 Phase 動作 | 風險 |
|---|---|---|
| **架構** | 三層融合：governance_config.yaml + governance_utils.py + 兩地基；複製非引用（主公拍板） | 分叉維護成本 |
| **資料** | 新增 `.governance/preflight.yaml`、`guards.yaml`；密鑰 baseline 取聯集不退化 | baseline 退化漏掃 |
| **可觀測性** | metrics 根因修後 metrics 檔才會生成；preflight 結果分級輸出 | 修法無效靜默失敗 |
| **韌性** | preflight 防遞迴 env（GOV_PREFLIGHT_RUNNING）；某 checker 掛不可拖垮全局 | 防遞迴設錯致迴圈（M2-2，S 級） |
| **可維護性** | gov/ 模組自包含、config 外化；docstring 標明源 commit 便於日後同步 | 6 個月後同步遺忘 |
| **文件** | 計畫書 + TASK_HISTORY + 影響半徑表 + （收官）同步點記錄 | 文件漂移 |
| **流程** | 走 Evidence→Contract→Guard→Fix→Verify→Record；每段 dry-run→對拍 | 趁熱連做略過檢查點 |

### B 級層（條件觸發）

| 層 | 是否觸發 | 說明 |
|---|---|---|
| **效能** | 觸發 | preflight `fast` profile 須 commit 前快跑（秒級）；`full` 才全跑。避免拖慢日常 |
| **部署** | 觸發 | 新增 `.governance/` 設定屬部署面；需 rollback 路徑（檔案級可逆） |
| **成本** | N/A | 不涉付費 API / 雲端成本 |
| **UX/A11y** | N/A | 無 UI / 報告視覺改動 |
| **隱私** | 觸發 | 密鑰掃描涉讀 `.env`；確保只比對不外傳（同安全層） |
| **i18n** | N/A | 純後端工具鏈，無多語 |

### 層級互鎖驗證（META5）

- 動 **Logic（去重/根因）→ 必動 Testing**：A2/A3 補等價測試 + 反向測試 ✅
- 動 **Architecture（三層融合）→ 必動 Documentation**：計畫書 + 收官同步點記錄 ✅
- 動 **Security（密鑰）→ 必動 Testing**：補密鑰掃描不外傳真值的測試 ✅

---

## 7. 跨切面檢查（X1-X4）

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 複製 gov/ 進 AOV/gov/ | 可逆（刪目錄即還原） | — |
| 新增 .governance/*.yaml | 可逆（刪檔還原） | — |
| 改 lint_phase_plan.py（補視角） | 可逆（git revert） | — |
| 改 cross_phase_review.py + m4（去重 import） | 半可逆（需驗等價） | — |
| 改 metrics 接線 | 半可逆（git revert） | — |
| git commit / push | 半可逆 | push 前問主公（守則） |
| 升任何 guard 到 strict | **本 Phase 不做** | 一律 shadow，零 strict |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [ ] log 副作用：metrics 修好後 `~/.claude/skill_metrics.jsonl` 開始寫入（之前從未生成）
- [ ] 中間檔產出：`.governance/` 新目錄、preflight 執行的暫存
- [ ] 系統狀態變更：preflight 設 `GOV_PREFLIGHT_RUNNING` 環境變數於子行程

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-31（待主公核准）
- 本計畫過期日期：**2026-07-31**（逾期未動工需重審 skills-governance 是否已再演進）
- 風險記錄帶日期：✅
- ⚠️ AG skill 路徑會 drift（手冊 §5.1，已三代）；若回填涉部署勿寫死。

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：拆兩 Stage、先低風險見效，邊做邊教，每段可懂可驗。
- **世界頂尖駭客 / 紅隊視角**：密鑰掃描是最大攻擊面——聯集 regex 須防真值落 log；preflight 防遞迴 env 須防被惡意/誤設觸發無限迴圈或繞過。詳見 M1 X4-A。
- **接手者視角**：gov/ 每模組 docstring 標源 commit + 計畫書留同步 SOP，半年後可循。
- **X4-J 自動化建議性工具邊界**：斷言引擎（contains/exists 字面比對）+ lint_guards（弱護欄啟發式偵測）屬建議性工具，**召回率僅供參考**，須在 CLI 末行印免責、design 階段列 false-negative 模式（見 §8 R6）。
- **X4-K 使用者端審查官**：preflight 一鍵全跑若某 checker 報錯，須讓主公一眼看出「哪個 checker、blocking 還是 warning」，不可一團紅讓人卡死。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 複製版 gov/ 與 skills-governance 源**長期分叉** | 高 | 中 | 代碼可控 | docstring 標源 commit；收官寫同步 SOP；登 RISK_REGISTRY |
| R2 | preflight 串 24 checker，某個掛掉 **block 日常 commit/push** | 中 | 高 | 代碼可控 | blocking/warning 分級；fast/full profile；--allow-skip 逃生艙 |
| R3 | metrics 根因修法**對 AOV 接線無效**（藍圖描述的是 skills-governance） | 中 | 中 | 代碼可控 | 動工 step 0 先驗 AOV 實際接線；補 import 觸發反向測試 |
| R4 | 去重合併兩函式**非完全等價致回歸** | 中 | 中 | 代碼可控 | 先 diff 兩函式；合併後對拍 test_m4 + test_cross_phase |
| R5 | 密鑰掃描**真實值外洩進 log/報告** | 低 | **高** | 安全 | 絕不回傳值（Hermes 設計）；補不外傳測試；推送前掃描 |
| R6 | 啟發式斷言**漏判（false negative）**被當成「保證」 | 中 | 中 | 業務 | CLI 末行免責邊界；文件標「人工覆核仍必要」 |
| R7 | 補 X4 視角致**既有已凍結計畫書 lint FAIL**（向後相容） | 中 | 低 | 代碼可控 | 確認 lint 只驗「新計畫書」或對舊檔寬鬆；不回溯改舊計畫書 |

**高風險加權檢查（META4）**：
- 高風險（影響=高）：R2、R5 → 2 項
- 加權分數：R2(中機×高影=1+) + R5(低機×高影) ≈ 2.5 分 → **< 5，不需暫停**（但 R5 屬安全，全程資安最高原則）

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **A0** | 建 P103 分支；跑基線存證（307 + governance checker 綠燈快照） | 回退基準 | 基線數記錄 |
| **A1** | `lint_phase_plan.py` PREFLIGHT_ANCHORS 9→11（補 X4-J/K）+ 修 docstring「九個」→「十一個」+ 同源 CLAUDE.md 漂移 | R7 | 對拍 307；test_lint_phase_plan 綠 |
| **A2** | 抽 `_extract_blindspots`≈`extract_blindspot_rules` 進 `governance_utils.py`，兩腳本改 import | R4 | diff 等價；test_m4 + test_cross_phase 綠 |
| **A3** | 驗 AOV metrics 接線 → 修 record() 至 import 可觸發位置 + 補反向測試 | R3 | 「import→metrics 非空」測試綠 |
| **B1** | 複製 `gov/utils.py`+建 `governance_config.yaml`（共享層；A2 的 utils 併入） | R1 | import 正常；config 載入 graceful |
| **B2** | 複製 `gov/preflight.py` + `.governance/preflight.yaml`，註冊 AOV doctor/checker；防遞迴 env | R2 | fast/full profile dry-run；某 checker 掛不拖垮 |
| **B3** | 複製 `gov/assertions.py` + `.governance/guards.yaml`，全 guard advisory/shadow + --allow-skip；CLI 免責行 | R6 | 斷言 4 型測試；shadow 零誤判；末行免責 |
| **B4** | 複製 `gov/scan_secrets.py`，regex 聯集 `.secrets.baseline`；不回傳真值 | R5 | 掃描測試；不外傳真值測試；對拍 baseline 不退 |

> 趁熱連做：A0→A3 連續，Stage A 末做一次完整對拍（307）後接 B1→B4；每 Stage dry-run 留存。遇不可逆動作（push / 刪檔）才停問主公。

---

## 10. 影響檔案清單（STR7，動工時定稿）

**新增**：
- `gov/__init__.py` `gov/utils.py` `gov/preflight.py` `gov/assertions.py` `gov/scan_secrets.py`（複製自 skills-governance；metrics/health 視需要）
- `.governance/preflight.yaml` `.governance/guards.yaml`
- `governance_config.yaml`（AOV 根，宣告 anchors/keywords/paths）
- `tests/test_governance_utils.py` `tests/test_preflight.py` `tests/test_assertions.py` `tests/test_scan_secrets.py`（新增測試）

**修改**：
- `scripts/lint_phase_plan.py`（+2 視角 anchor，~10 行）
- `scripts/cross_phase_review.py` `scripts/m4_track_blindspots.py`（改 import 共用，各 ~-15 行）
- `scripts/skill_metrics_logger.py` 或其呼叫端（接線根因，動工驗後定）
- `C:/Users/sammy/.claude/CLAUDE.md`（X4 九→十一視角同源漂移，僅該段）

**刪除**：無（複製/新增為主，可逆）

**影響但未直接修改**：11 個 AOV skill（metrics 接線生效後開始寫 metrics）、24 支 checker（被 preflight 註冊編排）

---

## 11. Postmortem 預埋點（G6）

收官後若觸發必寫 Postmortem（`docs/postmortems/2026-MM-DD-phase-103-<topic>.md`）：
- [ ] 主公中途否決重來
- [ ] 對拍發現重大設計缺陷（如去重非等價、metrics 修法無效）
- [ ] 回填後既有測試退化
- [ ] 任何「我以為…結果不是」事件（G2-3）——特別是 metrics 接線假設

> B-NNN/R-NNN 全域連續編號，新增前 `grep -h '^### [BR]-' docs/**.md | sort -u | tail` 查下一個。

---

## ✈️ Pre-flight 多視角體檢（STR10，凍結前必過）

### M1 強制填表（十一視角）

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面①密鑰掃描 regex 聯集若把比對到的真值寫進輸出/log = 自釀外洩，嚴重度高；最小緩解＝沿用 Hermes「絕不回傳值」+ 補不外傳測試。攻擊面②preflight 防遞迴 env 若可被外部設定繞過，guard 形同虛設；緩解＝env 名固定 + 文件化。 |
| **X4-B 接手者** | 半年後接手者靠 gov/ docstring 標的源 commit + 本計畫書 §9 同步 SOP 即可理解「為何 AOV 有一份 gov/ 複製、何時該與 skills-governance 再同步」。 |
| **X4-C 災難情境** | 情境：B2 preflight 把某 blocking checker 串進 push 閘門，該 checker 因環境問題恆掛，導致主公完全無法 push。緩解：先全 warning 級觀察 + --allow-skip 逃生艙 + 分級輸出。 |
| **X4-D 5 年後** | 5 年後 skills-governance 可能大改或廢棄；AOV 自包含複製確保不被外部 repo 拖累，但需收官明載「這是 2026-05-31 快照」避免誤以為是 live 連結。 |
| **X4-E 終端 vs IDE** | 回填純後端腳本，終端（py -m pytest）與 IDE 皆走同一 py launcher；無 IDE 專屬行為。 |
| **X4-F 跨平台 Win/Mac/Linux** | 路徑用 pathlib、env 用 os.environ；但 `py` launcher 為 Windows 專屬，gov/ 模組勿寫死 `py`，subprocess 呼叫須跨平台（sys.executable）。 |
| **X4-G 主公個人視角** | 主公要邊做邊教 + 趁熱連做；每 Stage 我說「做什麼/為什麼/下一步」並 dry-run 給看，連做但不靜默。 |
| **X4-H 觀測 / 治理** | metrics 根因修後首次產出 skill_metrics.jsonl，可觀測性提升；preflight 結果需分級可讀，納入治理閘門。 |
| **X4-I 主公可見性** | 自動行為：metrics 開始寫檔、preflight 設 env、.governance/ 產出——已在 X2 盲區攤開，收官 TASK_HISTORY 載明。 |
| **X4-J 自動化建議性工具邊界** | 斷言引擎（contains/exists 字面比對）+ lint_guards（弱/幽靈護欄啟發式）召回率僅供參考：已知 false-negative＝語意等價但字面不符的 guard 會漏判。CLI 末行須印「召回率僅供參考、人工覆核必要」，design 階段列 FN 模式。 |
| **X4-K 使用者端審查官 / Patric** | 主公最可能卡在：preflight 一鍵全跑後一團紅、分不清哪個 checker 是 blocking。緩解＝分級彩色輸出 + 摘要列出 blocking 數 vs warning 數，避免走死路。 |

> **主公人工裁決錨點（B-005）**：本 Phase 裁決點預估 ──（a）計畫書核准 1 點（~5 分，讀本書）；（b）Stage A→B 之間對拍結果確認 1 點（~2 分，看 307 是否不退）；（c）push 前確認 1 點（~1 分）。AI 提供格式：每點附 dry-run diff / 測試數對比 / 一句話結論。共 ~3 裁決點。

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發 | 發現 |
|---|---|---|
| **Jarvis 型總控** | 固定 | 目標明確（裝回 6 項拆兩 Stage）、邊界清楚（零 strict、複製非引用）、下一步＝核准後 A0 起手；結論先行 ✅ |
| **Ken 型紅隊** | 固定 | 安全邊界＝密鑰不外傳（R5/S 級）；不可逆＝push 前問；無新 secrets 進 git ✅ |
| **Patric 型使用者端** | 固定 | preflight 輸出不可一團紅讓主公卡死（X4-K）；斷言免責邊界須白話（X4-J） |
| **Jimmy 型文件主筆** | 觸發（改 CLAUDE.md/計畫書/TASK_HISTORY） | gov/ docstring 標源 commit、可追溯；計畫書有施工依據引用，非空泛 |
| **Marcus 型數據** | 觸發（基線 metrics） | 基線 307 為定量錨點；metrics 根因修有「import→非空」可量測判據 |
| **Oliver 型設計** | N/A | 無 UI / 報告視覺改動 |
| **Penny 型 CFO** | N/A | 不涉付費 API / 雲端成本 |
| **Jason 型 DevOps** | 觸發（腳本/git/環境） | `py` launcher 環境差異已記；subprocess 跨平台用 sys.executable；rollback＝分支+檔案級可逆 |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing 計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | **(S)** 複製 gov/ 進 AOV 後與源分叉，skills-governance 修了 bug AOV 不知道，長期淪為兩份漂移的死碼 | **S** | — | docstring 標源 commit + 收官寫同步 SOP + 登 R1；主公已拍板「複製非引用」接受此代價換自包含 | 接受，緩解入 RISK_REGISTRY |
| 2 | **(S)** preflight 把 24 checker 串進 push 閘門，防遞迴 env 設錯或某 checker 恆掛 → 主公完全無法 commit/push | **S** | — | 全程 warning 級 + fast/full profile + --allow-skip 逃生艙；B2 先 dry-run 驗「某 checker 掛不拖垮全局」 | 緩解，R2 |
| 3 | metrics 根因修法照搬 skills-governance，但 AOV skill 接線結構不同 → 改了無效還誤動 | 中 | — | A3 動工 step 0 **先驗 AOV 實際接線**再決定修法，不照搬；補 import 觸發反向測試證明有效 | 緩解，R3 |
| 4 | 去重合併假設兩函式「一字不差」，實際有細微差異 → 合併引入回歸 | 中 | — | A2 先 `diff` 兩函式確認等價再合併；合併後對拍 test_m4 + test_cross_phase | 緩解，R4 |
| 5 | **(S)** 密鑰掃描融合後 regex 太寬，把比對到的真實金鑰片段寫進 log/報告 → 自釀資安事故 | **S** | — | 沿用 Hermes「絕不回傳值」設計；補「掃描輸出不含真值」測試；推送前自掃 | 緩解，R5，資安最高 |
| 6 | 補 X4 9→11 後，既有已凍結（只填 9 視角）的計畫書突然 lint FAIL，污染歷史 | 中 | — | A1 確認 lint 僅驗當前受測計畫書、不回溯；不改任何舊計畫書檔 | 緩解，R7 |

> 無 pre-existing failing test（基線 307 全綠），M2 無需處理跳過計次。未解質疑：無（皆有緩解或入 RISK_REGISTRY）。

---

## ✈️ STR9 — Skill 收官 entry_points 檢查

本 Phase **不新增/不更新 skill**（回填的是引擎與腳本，非 skill）→ STR9 N/A。

---

## 12. 凍結戳記

- **凍結人**：主公核准（2026-05-31）+ AI 自驗（M1 十一視角 + M2 六條含 3 條 S 級）
- **凍結日期**：2026-05-31
- **lint 自驗**：✅ PASS（M1 + M2 體檢通過，2026-05-31）
