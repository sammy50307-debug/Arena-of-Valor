# Phase 112 — generate 失敗持久診斷：self-heal 保留 pre_heal_error（R-037 方案B+A）（草案 v2，待阿喜核准）

> 狀態：**v2 已凍結（2026-06-14，阿喜核准 B+A + lint M1/M2 PASS；S1-S4 已動工收官）**
> 戰線：**可觀察性（Observability）+ 資料（manifest）**——R-037 主根因「generate 例外被吞」的最小邊際價值切片：不治本（吞例外是刻意 graceful degradation），只把「被 P111 self-heal 遮蔽且即將被 manifest 覆蓋的失敗原因」**持久保留下來**。
> 鐵律：`py` 不用 `python`（CI yaml 內 python 是 Linux runner 正確）；TASK_HISTORY 禁全讀；改動前計畫書等同意；push 前問阿喜；**完全不碰 main.py、不碰 exit code、不碰 generate 例外處理邏輯**。

> 📎 飛輪三輪收斂註記（2026-06-14）：阿喜三次追問「更好的做法」，飛輪模式定案——(1) 發現 P111 manifest `self_heal=true` 已是持久訊號（L1 已上線）；(2) 唯一真實缺口是 self-heal 覆蓋掉 main.py 寫的失敗 `error`，使「為什麼失敗」遺失；(3) 反膨脹：不建 framework/monitor（0 次發生），改用既有 manifest + 一個欄位 + 數據驅動 PROMOTE 觸發。本 v2 = 穩修 B（pre_heal_error）+ 快修 A（runbook）+ R-037 預埋 promote 觸發。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P112 |
| **Phase 名稱** | self-heal 保留 generate 失敗原因（manifest `pre_heal_error`，持久+可診斷） |
| **影響半徑** | **微 Phase（2 核心檔：run_manifest.py + replay_run.py，皆 additive；+ 擴既有測試 + 文件）─ META3 / Patch-1（S 級為主）** |
| **預估投入** | 1-2 h |
| **負責模型** | Opus 4.8（涉 P111 剛動過的核心檔 + manifest 契約 + 同源邊界） |
| **前置 Phase** | P111（CI self-heal，已收官 72fcc85）；本 Phase 補其「失敗原因被覆蓋遺失」的盲區 |

---

## 1. 目標 (Objective)

self-heal 重產報告前，**先讀既有那份失敗 manifest 的 `error` 欄位**（main.py 已把 generate 例外寫進去，main.py:812），把它帶進 self-heal 自己寫的 manifest 一個新欄位 `pre_heal_error`。使最終（committed 進 git 的）manifest = `self_heal=true` + `pre_heal_error="<generate 真正的錯誤>"`——「今天 generate 為什麼壞、靠 self-heal 救回」**持久保留、可被未來查詢/診斷**，不因 self-heal 覆蓋同路徑 manifest 而遺失。量化：generate 失敗原因從「self-heal 救回即遺失（只剩 ~90 天的 CI log）」→「永久存於 manifest，可 grep、可聚合」。

## 2. 觸發背景 (Why Now)

飛輪三輪收斂（§ 飛輪註記）確認：
- P111 已持久記錄「該日靠 self-heal 救回」（manifest `self_heal=true`）= L1 自我記錄，已上線。
- **唯一真實缺口**：generate 失敗時 main.py 把例外寫進 manifest `error`（status="failed"），但 self-heal 救回時**用自己的 manifest 覆蓋同一路徑** `data/runs/DATE/run_manifest.json`（status="ok"）→ **失敗原因 `error` 被沖掉**。日後（數月）回頭分析「generate 為什麼反覆失敗」時，CI log 早已輪替，無從查起。
- 反膨脹：0 次發生 → 不建 framework/monitor，只補這一個欄位 + 數據驅動 PROMOTE 觸發。

## 3. Entry Criteria

- [x] P111 收官並 push（72fcc85），self-heal 線上線，manifest 已有 `self_heal`/`promoted` 欄位
- [x] R-037 飛輪三輪收斂，阿喜選定方案 B+A（2026-06-14）
- [x] 已親核：main.py:812 `error=report_error` 寫入 manifest；self-heal 經 write_manifest(config.DATA_DIR) 覆蓋同路徑（replay_run 既有 manifest 區塊）
- [ ] 阿喜核准本計畫書凍結

## 4. Exit Criteria

- [ ] **A（run_manifest 欄位）**：`build_manifest` 加 `pre_heal_error: str = ""` 參數 + 輸出 `"pre_heal_error"` 欄位（緊鄰 `self_heal`/`promoted`）；main.py 既有呼叫不傳→預設 ""（零影響）
- [ ] **B（replay 讀舊 manifest）**：`replay_run.py` heal 路徑在寫 manifest 前，讀既有 `manifest_path(config.DATA_DIR, date)`，若 `status=="failed"` 取其 `error`（截斷上限 ~500 字防爆）為 `pre_heal_error` 傳入 build_manifest；讀檔以 try/except 包覆（讀失敗→空字串，不阻斷 heal）
- [ ] **C（不碰 main.py / exit code）**：本 Phase **零** main.py 改動、零 exit code 改動、零 generate 例外邏輯改動（RP1 物理歸零）
- [ ] **D（測試）**：擴 `tests/test_self_heal_replay.py`——①pre-existing failed manifest（status=failed,error=X）存在 → heal 後 manifest `pre_heal_error==X`；②無 pre-existing manifest → `pre_heal_error==""`；③pre-existing manifest status=ok（非失敗）→ 不帶 pre_heal_error；④build_manifest 純函數層：傳 pre_heal_error 出現在輸出、不傳為 ""
- [ ] **E（快修 A + 數據驅動觸發）**：runbook 註記「查 manifest `self_heal=true` + `pre_heal_error` 診斷 generate 失敗」；RISK R-037 補記「方案B 已持久保留失敗原因；**PROMOTE 觸發：若 `self_heal=true` recurring（≥3 次/30 天，可從 manifest history grep）才升級加 health checker（C′），否則維持**」
- [ ] **F**：全套零回歸（基線 514）；本地 run-now 不受影響（不碰 main.py）
- [ ] **G**：收官件套（TASK_HISTORY + RISK R-037 補記不關閉 + memory + 飛輪元教訓存 memory feedback）

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 1-2 h |
| 收益等級 | **低-中**（窄但真實：補唯一 downstream 補不到、且會被覆蓋遺失的「失敗原因」持久化） |
| ROI | ✅ 正（additive 欄位、零 main.py、零 exit-code 風險、P111 測試框架內可測；數據驅動觸發防過度工程） |

---

## 6. 17 層稽核表（Patch-1 微 Phase：S 級為主）

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | build_manifest +`pre_heal_error` 參數/欄位；replay 讀舊 manifest 取 error | additive 改 P111 剛動的核心檔 | 純 additive（預設 ""）；main.py 呼叫不變；讀檔 try/except 包覆 |
| **2. 邏輯** | 僅 `status=="failed"` 才取 error；截斷防爆 | 誤取成功態 error / 巨大 error 爆 manifest | 判據復用既有 status；error 截斷 ~500 字 |
| **4. 測試** | 擴 test_self_heal_replay 4 case + 純函數層 | session 污染/假綠 | 復用 P111 三隔離框架；pre-existing manifest 由測試精確構造 |
| **10. 安全** | 只多存一段 error 文字、零外呼、零 exit code、零新授權 | error 含機敏？ | error=generate 渲染例外訊息（非機敏）；截斷；不存 secret |

### A/B 級（微 Phase 提示填）
- **5. 資料（核心，本 Phase 主旨）**：manifest 加 `pre_heal_error` 保留 self-heal 覆蓋前的失敗原因。✅ validate_manifest 允許額外欄位（已查證 P111）。
- **6. 可觀察性（核心）**：失敗原因從短暫（CI log ~90 天）升級為持久（committed manifest）。✅
- **13. 可維護性**：runbook + 註解寫明「為何讀舊 manifest（self-heal 覆蓋會沖掉失敗原因）」。✅
- 其餘層 N/A（微 Phase）。

### 層級互鎖 ─ META5
- [x] Logic→Testing｜[x] Data→Maintainability｜[x] Security→Testing

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| build_manifest +pre_heal_error 欄位 | 可逆（git revert，additive） | main.py 既有測試零回歸 |
| replay 讀舊 manifest | 可逆（try/except，讀失敗不阻斷） | self-heal 既有測試零回歸 |

### X2 盲區掃描
- [x] 本 Phase 即補 X2 盲區（被覆蓋遺失的失敗原因）
- [x] 新盲區：pre_heal_error 只在「main.py 先寫失敗 manifest」時有值；若 generate 在 manifest 寫入前就崩（main.py 更早期例外）→無 pre-existing manifest→pre_heal_error 空（誠實標示於 runbook）

### X3 時間敏感性
- 草案 2026-06-14；與 P111 self-heal + manifest 契約強綁，任一改動需重審
- **PROMOTE 觸發為數據驅動**（self_heal recurring ≥3/30天），非日期驅動——避免 dead rule

### X4 多角度審查
- **主公**：阿喜三輪追問後選 B（持久+可診斷），要「失敗原因不因 self-heal 救回而遺失」。
- **紅隊**：見 M2。
- **接手者**：runbook + 註解 + 測試釘 pre_heal_error 行為 + R-037 promote 觸發明文。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| ~~RP1~~ | ~~改 exit code 破 P111~~ | — | — | — | **N/A（v2 完全不碰 main.py/exit code，物理歸零）** |
| **RP2** | **【S】** 讀既有 manifest 失敗（壞 JSON/權限）例外冒泡**中止 self-heal → 打斷剛上線 production L5 恢復** | 低 | **高** | 韌性 | **try/except 全包覆**，讀失敗→pre_heal_error="" 繼續 heal（恢復優先於診斷）；新增無-manifest case + 既有 5 case 驗恢復不受影響 |
| **RP6** | **【S】** additive 改 build_manifest 破 manifest 契約 → write_manifest validate 拋 → **cron + self-heal manifest 寫入全失敗** | 低 | **高** | 代碼/資料 | pre_heal_error 純 additive optional（預設 ""）；validate_manifest 不檢查未知欄位（P111 查證）；main.py 呼叫不變；純函數層 + 514 全套回歸驗 manifest 仍 valid |
| RP3 | 巨大 error 文字爆 manifest | 低 | 低 | 資料 | 截斷 ~500 字 |
| RP4 | error 含機敏 | 低 | 中 | 安全 | error=渲染例外訊息（非機敏）；截斷；如未來可能帶值再評估 redact |
| RP5 | 過度工程（為 0 次失敗加欄位） | 中 | 低 | 流程 | 最小 additive 欄位；數據驅動 PROMOTE 觸發擋住後續膨脹；飛輪元教訓存 memory 防復發 |

**META4 加權**：RP2+RP6 兩 S 級（皆「打斷剛上線 production L5/manifest 契約」高 blast radius），但**均為設計緩解**（純 additive optional 欄位 + try/except 全包覆 + 514 全套回歸）→ 發現時高、緩解後低。阿喜 2026-06-14 已核准動工，S 級已設計歸零，無須二次請示。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 驗收 |
|---|---|---|
| **S1 manifest 欄位** | `run_manifest.build_manifest` 加 `pre_heal_error: str=""` 參數 + 輸出欄位 | 純函數層測試 + main.py 既有呼叫零影響 |
| **S2 replay 讀舊 manifest** | `replay_run.py` heal 寫 manifest 前讀既有 `manifest_path(config.DATA_DIR,date)`，status=failed 取 error（截斷）為 pre_heal_error；try/except 包覆 | self-heal 既有測試零回歸 |
| **S3 測試** | 擴 `tests/test_self_heal_replay.py` 4 case（D） | 514→+4 passed 零回歸 |
| **S4 收官** | runbook A 註記 + RISK R-037 補記（含 PROMOTE 觸發，不關閉）+ TASK_HISTORY + memory（含飛輪元教訓 feedback：勿為 0 次失敗 speculative observability，改數據驅動觸發） | 件套齊 |

---

## 10. 影響檔案清單 ─ STR7

**修改（核心，皆 additive）**：`analyzer/run_manifest.py`（+pre_heal_error 參數/欄位 ~2 行）、`scripts/replay_run.py`（heal 讀舊 manifest ~8 行）
**修改（測試）**：`tests/test_self_heal_replay.py`（+4 case）
**新增/修改（文件）**：runbook（查 self_heal/pre_heal_error；找既有 ops 文件或新建小節）、`docs/RISK_REGISTRY.md`（R-037 補記 + PROMOTE 觸發）、`TASK_HISTORY.md`
**memory**：飛輪元教訓（feedback 類，跨專案）
**不碰**：`main.py`（含 exit code / generate 例外邏輯）、`.github/workflows/daily_report.yml`、P111 self-heal 閘門邏輯

---

## ✈️ Pre-flight 多視角體檢 ─ STR10

### M1 強制填表（十一視角，微 Phase 精簡）

| 視角 | 發現 |
|---|---|
| **X4-A 紅隊** | 見 M2。核心：讀舊 manifest 阻斷 heal（try/except）；機敏（error 非機敏+截斷）；過度工程（數據驅動觸發擋）。 |
| **X4-B 接手者** | additive 欄位 + 註解「為何讀舊 manifest」+ runbook + 測試釘行為 + R-037 promote 觸發明文。 |
| **X4-C 災難** | 讀舊 manifest 失敗→try/except→pre_heal_error 空、heal 照跑（不阻斷恢復）；最壞=少一段診斷字串。 |
| **X4-D 5 年後** | 與 P111 self-heal + manifest 契約強綁（X3）；PROMOTE 觸發數據驅動防 dead rule；接手者讀 manifest + runbook 即懂。 |
| **X4-E 終端 vs IDE** | 純 python additive，本地 py 驗；不涉終端互動。 |
| **X4-F 跨平台** | 純 python（json 讀 + 字串截斷），3.8 相容；不涉 yaml/shell。 |
| **X4-G 主公視角** | 阿喜三輪收斂選 B；明告「不治本、只持久保留失敗原因；主根因仍 known issue」。 |
| **X4-H 觀測/治理** | manifest 持久診斷 + 數據驅動 PROMOTE 觸發（飛輪自升級）。 |
| **X4-I 主公可見性** | 無自動對外行為；只多一個 manifest 欄位（隨既有 Fallback Push 進版控）。 |
| **X4-J 自動化邊界** | 純被動記錄一段失敗原因文字進 manifest，不觸發任何自動動作、不對外、不可逆；自動化邊界僅止於「多存一欄位」，無啟發式判斷、無自動執行。 |
| **X4-K 使用者端審查官** | 誤解「加欄位=修好了」→明界定「只持久化失敗原因供未來診斷，generate 仍可能失敗、仍靠 self-heal 救」。 |

### M2 紅藍對抗（≥5 條）

| # | 紅隊質疑 | 攻擊力 | 藍隊回應 | 處置 |
|---|---|---|---|---|
| 1 | **【S 級】** replay heal 讀既有 manifest 若未確實 guard → 例外冒泡**中止 self-heal → 打斷剛上線的 production L5 恢復線**？ | S | try/except **全包覆**讀檔+解析，讀失敗→pre_heal_error="" 繼續 heal；恢復永遠優先於診斷記錄；新增 case ②（無 pre-existing manifest）+ self-heal 既有 5 case 驗恢復不受影響。 | 入計畫範圍（RP2/S3） |
| 6 | **【S 級】** additive 改 P111 剛上線核心檔 `build_manifest`，若破 manifest 契約 → `write_manifest` validate 拋 ValueError → **cron + self-heal manifest 寫入全失敗**（連帶破 P111 + 正常 pipeline）？ | S | pre_heal_error 純 additive optional 欄位（預設 ""）；validate_manifest 不檢查未知欄位（P111 已查證額外欄位不擋）；main.py 呼叫不傳→零影響；全套 514 回歸 + 純函數層 case 驗 manifest 仍 valid。 | 入計畫範圍（RP6/S3） |
| 2 | 與 P111 既有 `self_heal=true` 冗餘？ | A | self_heal=true 只說「發生了」，pre_heal_error 補「為什麼」（可定位）；且失敗原因本會被覆蓋遺失，這是唯一持久保留處。 | 入計畫範圍（目標聚焦） |
| 3 | 過度工程（0 次發生加欄位）？ | B | 最小 additive 欄位（非 framework/monitor）；數據驅動 PROMOTE 觸發擋後續膨脹；飛輪元教訓存 memory 防同類復發。 | 入計畫範圍（接受為微 Phase 設計 + 觸發） |
| 4 | error 印出機敏？ | B | error=渲染例外訊息（非機敏）+ 截斷 ~500 字；未來若可能帶值再評估 redact（RP4）。 | 入計畫範圍（RP4） |
| 5 | 巨大 error 爆 manifest？ | B | 截斷 ~500 字（RP3）。 | 入計畫範圍（RP3） |

> 未解質疑：無。

---

## 11. 凍結戳記（待填）

- **凍結人**：阿喜核准（2026-06-14）+ Claude（Opus 4.8 1M）
- **凍結時間**：2026-06-14
- **凍結依據**：飛輪三輪收斂（v1 main.py print → v2 manifest pre_heal_error）+ lint M1/M2 PASS + 阿喜核准 B+A 方向

---

*狀態：草案 v2，待阿喜核准。受 17 層框架 v3.1 + STR10 保護（Patch-1 微 Phase）。建立 2026-06-14（v1 main.py print → v2 飛輪三輪收斂改 manifest pre_heal_error，更持久/可測/零 main.py 風險）。*
