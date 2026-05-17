# Phase P82 計畫書 — Idempotency / Timezone（已收官）

> 草案日期：2026-05-17
> 凍結日期：2026-05-17
> 狀態：CLOSED（2026-05-17：run context + run_id/source_hash + timezone contract 已落地）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P82 |
| 名稱 | Idempotency / Timezone |
| 影響半徑 | 標準（預估 5-8 檔） |
| 預估投入時數 | 2.5-4 h |
| Token budget | 35K-55K tokens |
| 負責模型 | GPT-5.3-Codex 高 |

## 0.5 狀態轉換清單

本 Phase 不涉及 skill / module / workflow 的生命週期狀態轉換；僅定義 daily run 的日期與重跑契約。

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P82 計畫 | DRAFT | FROZEN | 已完成計畫書與稽核，尚不可改程式碼 | 本文件建立並通過 lint | AI 建立，主公核准後才進 APPROVED |

## 1. 目標

讓每日監測流程只有一個權威「台北日期」來源，並讓同一日期的重跑具備可預期語義：相同輸入可推導同一 run identity，不同輸入保留版本，不讓 rerun 污染 canonical report、manifest 或 landing。

## 2. 觸發背景

P77-P81 已完成主鏈路止血、manifest、doctor、promotion gate、replay/backfill；下一個長期穩定性缺口是日期與重跑契約。現在 `main.py` 仍有多處 `datetime.now()`，GitHub Actions 以 UTC 排程觸發，但業務報告應以 Asia/Taipei 為準；同日多次重跑也尚未明確定義 source hash、run id、candidate version 與 manifest 覆蓋規則。

## 3. Entry Criteria

開工前必須全部達成：

- [x] P80 已收官：candidate/promote gate 已通過 CI workflow_dispatch 實跑。
- [x] P81 已收官：replay/backfill/debug bundle 已落地。
- [x] run manifest 已存在，可擴充 idempotency 欄位。
- [x] `daily_report.yml` 仍明確使用 UTC 排程，需建立台北日期轉換契約。
- [x] 主公核准 P82 計畫，狀態由 FROZEN 轉 APPROVED。

## 4. Exit Criteria

達成全部才算 P82 收官：

- [x] 建立唯一 run date resolver，所有主鏈路 report/raw/analysis/manifest 日期以 Asia/Taipei 推導。
- [x] `run_id = run_date + mode + source_hash` 契約落地，並寫入 manifest。
- [x] 同日重跑可預期：相同 source hash 不產生矛盾狀態，不同 source hash 保留候選版本且不繞過 P80 promotion gate。
- [x] GitHub Actions UTC 排程與台北日期對映有測試或明確驗證。
- [x] 新增/更新測試覆蓋 timezone、run_id、same-day rerun、manifest contract。
- [x] `py -m pytest -q` 通過，且 Python 3.8 import guard 不回歸。
- [x] handoff / active / TASK_HISTORY / 總戰役計畫同步收官狀態。

## 4.1 已落地（P82）

- `analyzer/run_context.py`
  - 新增 `build_run_context()`：以 Asia/Taipei 推導 daily run business date。
  - 新增 `build_source_hash()`：用 URL/title/platform/region 建立穩定 hash，不把 raw content 寫入 manifest。
  - 新增 `build_run_id()`：落地 `run_date + mode + source_hash prefix` 契約。
- `main.py`
  - raw / analysis / report_url / gate / manifest / promotion fallback date 改用同一份 run context。
  - pipeline log 顯示業務日期與 source hash prefix。
- `analyzer/run_manifest.py`
  - schema version 升至 2。
  - manifest 寫入 `run_date_taipei`、`timezone`、`scheduled_utc`、`run_id`、`source_hash`、`source_hash_version`。
  - `validate_manifest()` 保留 schema v1 相容，避免舊 manifest 直接被 doctor 判壞。
- `scripts/check_daily_report_health.py` / `scripts/system_doctor.py`
  - 預設台北日期改用 `build_run_context()`，避免各自計算。
- 測試
  - 新增 `tests/test_run_context.py`。
  - 更新 `tests/test_run_manifest.py` 覆蓋 schema v2、legacy v1、run_id、same-day rerun identity。
  - 全套 `py -m pytest -q`：`163 passed`。
  - Python 3.8 import smoke：`py -3.8 -c "import main; import analyzer.run_context"` 通過。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 2.5-4 h |
| 預估收益等級 | 高 |
| 收益描述 | 降低每日排程跨時區錯日、同日 rerun 污染 canonical、manifest 難追溯的長期風險 |
| ROI 結論 | 值得做，因為這是 daily pipeline 長期自動運轉的核心契約 |

## 6. 動工範疇（凍結）

1. 建立集中式台北日期 resolver。
2. 移除主鏈路中與報告日期相關的散落 `datetime.now()` 決策點。
3. 定義並寫入 `run_id`、`source_hash`、`timezone`、`scheduled_utc` / `run_date_taipei` 相關 manifest 欄位。
4. 定義同日重跑規則：candidate 可多版本，canonical 仍只由 P80 promote 更新。
5. 補測試：timezone resolver、manifest contract、same-day rerun 行為。
6. 文件同步：P82 plan / handoff / active / TASK_HISTORY。

## 7. 非範疇（避免偏航）

- 不做 P83 data quality/security gate。
- 不做 P84 retention/SLO/long-term governance。
- 不改報告 UI 視覺設計。
- 不新增外部 API 呼叫。
- 不改 P80 promotion gate 的核心通過條件，除非是為了接入 run date / run_id 欄位。

## 8. 17 層稽核表

> 影響半徑：標準 Phase（預估 5-8 檔）。依規則列全 17 層，B 級未觸發者明列理由。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | 集中 resolver，小步替換日期決策點 | 一次改太多散落呼叫造成回歸 | 先 inventory，再逐處替換並測試 |
| 2 | 邏輯層 (Logic) | Asia/Taipei 為唯一 daily report 日期來源 | UTC 排程日與台北業務日不一致 | resolver 明確接受 now / timezone 注入 |
| 3 | 架構層 (Architecture) | 日期與 run identity 成為 manifest 契約 | main.py 繼續承擔太多決策 | 把推導邏輯放在小型 helper |
| 4 | 測試層 (Testing) | timezone 邊界、source_hash、rerun、manifest contract | 只在本機當天測試而漏掉跨日 | 測固定時間樣本與 UTC/Taipei 邊界 |
| 5 | 資料層 (Data) | manifest 新增 run_id/source_hash/timezone 欄位 | 新舊 manifest 不相容 | schema version 或向後相容驗證 |
| 6 | 可觀察性層 (Observability) | manifest 可看出 run date、source hash、rerun identity | rerun 後不知道是哪次資料 | manifest/debug bundle 暴露非敏感識別欄位 |
| 7 | 韌性層 (Resilience) | 同日 rerun 不覆蓋未 promote 的狀態 | rerun 把健康 canonical 變壞 | P80 promote gate 仍是唯一發布入口 |
| 8 | 效能層 (Performance) | 只計算小型 hash 與日期，不掃大檔 | source_hash 若吃完整大型輸出可能慢 | hash 以穩定小型來源摘要為主 |
| 9 | UX/A11y 層 | N/A，不改 UI layout | 無 | 報告日期文案若需改留在小範圍 |
| 10 | 安全層 (Security) | source_hash 不寫 raw content，不寫 secret | manifest 泄漏原文或 token | 僅寫 hash、模式、日期、路徑 |
| 11 | 部署層 (DevOps) | 明確 GHA UTC schedule 對映台北日期 | CI 與本地日期不同 | 測試固定 UTC time，文件註明對映 |
| 12 | 成本層 (Cost) | 不新增 LLM/API 呼叫 | 成本不應增加 | 純本地計算 |
| 13 | 可維護性層 (Maintainability) | 單一 date/run identity helper | 半年後又出現散落 now | 測試與 grep 檢查防回歸 |
| 14 | 文件層 (Documentation) | 計畫、handoff、TASK_HISTORY 同步 | 新視窗誤以為可直接動工 | L1 標 FROZEN pending approval |
| 15 | 流程層 (Process) | FROZEN 後等主公核准 | 計畫未核准先改碼 | active bootstrap 禁止改程式 |
| 16 | 隱私/合規層 (Privacy) | 不新增資料收集，不保存原文 hash input | hash 前資料來源不清 | 明定 hash payload 不含 raw content |
| 17 | i18n/在地化層 | Asia/Taipei contract 是本 Phase 核心 | 未來多區域擴展受限 | 先把 timezone 做成參數，預設台北 |

## 9. 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 DevOps 層 -> 已規劃 Observability / Documentation。

## 10. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 P82 計畫文件 | 可逆 | 不需不可逆確認 |
| 後續新增 helper / tests | 可逆 | P82 核准後才可做 |
| 後續修改 manifest schema | 半可逆 | 需保留向後相容 |
| 後續 push | 半可逆 | 依專案規則 push 前詢問主公 |

### X2 盲區掃描

- log 副作用：resolver 可能讓 log 顯示台北日期，但 GitHub run metadata 仍是 UTC。
- 中間檔產出：同日 rerun 可能新增 candidate version 與 manifest attempt 欄位。
- 系統狀態變更：canonical report 仍由 P80 控制，P82 不應繞過 promote。

### X3 時間敏感性

- 本計畫凍結日期：2026-05-17
- 本計畫過期日期：2026-05-24，超過需重看 main.py 與 workflow 是否已變。
- 風險記錄帶日期：已在本文件與 TASK_HISTORY 補錄。

### X4 多角度同行審查

- 主公視角：主公要的是同一天重跑時不要產生互相打架的報告，這份計畫把「日期」與「發布」拆清楚。
- 世界頂尖駭客 / 紅隊攻擊者視角：攻擊面主要是 manifest 泄漏資料、hash input 含 raw content、CI 時區誤導；緩解是只寫 hash 與非敏感 metadata。
- 接手者視角：半年後接手者只要看 resolver 與 manifest 欄位，就能知道某份報告屬於哪個台北業務日與哪次輸入。
- X4-J 自動化建議性工具邊界：本 Phase 不新增啟發式推薦工具；若加 grep/lint 只作防回歸輔助，不宣稱完整召回。
- X4-K 使用者端審查官 / Patric 型人格：最容易誤解的是「GitHub 顯示 5/16，報告卻是台北 5/17」；文件與 manifest 必須同時攤開 UTC/Taipei。

## 11. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 日期 resolver 改錯，導致 raw/analysis/report 不同日 | 中 | 高 | 代碼可控 | 集中 helper + 固定時間測試 |
| R2 | manifest schema 新欄位破壞既有 doctor/replay | 中 | 高 | 代碼可控 | 向後相容驗證，更新相關測試 |
| R3 | source_hash 選錯輸入，重跑判斷不穩 | 中 | 中 | 業務 | 明定 hash payload，排除 volatile timestamp |
| R4 | 同日 rerun 規則太複雜，主公難判讀 | 中 | 中 | 流程 | manifest 欄位與 log 語句要直白 |
| R5 | GHA UTC schedule 與台北日期測試不足 | 低 | 高 | DevOps | 固定 UTC 16:00/00:00 邊界測試 |

**高風險加權檢查（META4）**：
- 高風險數量：3 項。
- 加權分數：R1 2 + R2 2 + R3 1 + R4 1 + R5 2 = 8。
- 是否 >= 5 須請示主公：是；本計畫保持 FROZEN，待主公核准後才動工。

## 12. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| P82.0 | Inventory 日期使用點與 manifest 欄位影響 | R1/R2 | grep 清單與測試目標明確 |
| P82.1 | 建立 Asia/Taipei run date resolver | R1/R5 | 固定 UTC/Taipei 邊界測試通過 |
| P82.2 | 建立 source_hash / run_id 契約並寫入 manifest | R2/R3 | manifest validate + run_id 測試通過 |
| P82.3 | 定義 same-day rerun 行為，不繞過 P80 promote | R3/R4 | rerun 測試證明 canonical 不被污染 |
| P82.4 | 對齊 GHA schedule / docs / handoff | R5 | 文件與 active bootstrap 同步 |
| P82.5 | 收官驗證與 TASK_HISTORY 無損紀錄 | 全部 | pytest / diff check / 收官紀錄 |

## 13. 影響檔案清單

**新增**：
- `docs/PHASE_82_PLAN.md`
- 後續可能新增：`tests/test_run_context.py` 或同等 timezone/idempotency 測試檔

**修改（計畫核准後才可動）**：
- `main.py`：改用集中 run date / run context。
- `analyzer/run_manifest.py`：加入 run_id/source_hash/timezone 欄位與驗證。
- `scripts/check_daily_report_health.py` 或 `scripts/system_doctor.py`：視 manifest contract 變更補診斷。
- `.github/workflows/daily_report.yml`：若需明示台北日期 env 或 log，才小改。
- `tests/*`：補 timezone / manifest / rerun 覆蓋。
- `NEXT_SESSION_HANDOFF.md`, `docs/ACTIVE_OPERATION.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`：狀態同步。

**刪除**：
- 無預期刪除。

**影響但未直接修改**：
- P80 promotion gate：P82 不改其核心決策，但會提供更穩定的 run date / run_id。
- P81 replay/backfill：後續需能讀新 manifest 欄位，並保留向後相容。

## 14. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] 主公中途否決 run_id / source_hash 定義。
- [ ] 測試發現 manifest schema 與 P79/P81 doctor/replay 不相容。
- [ ] CI 實跑發現台北日期與預期業務日不同。
- [ ] 有任何「我以為 UTC/台北轉換沒影響，結果污染報告日期」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-82-idempotency-timezone.md`

## 15. Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是 manifest 與 debug bundle 洩漏 raw content、hash input 包含敏感原文、CI 日期錯置被利用製造錯誤報告；最小緩解是只寫非敏感 hash 與明確 timezone 欄位。 |
| **X4-B 接手者** | 接手者最怕看到 raw、analysis、report、manifest 各用不同日期；本 Phase 要讓日期推導集中，並讓 run_id 可從 manifest 讀懂。 |
| **X4-C 災難情境** | 情境：UTC 5/16 晚上觸發但台北已 5/17，報告寫錯日並覆蓋首頁；緩解：resolver 固定以 Asia/Taipei 推導業務日。 |
| **X4-D 5 年後** | 五年後若要支援其他區域，硬編台北會卡住；所以 resolver 應參數化 timezone，專案預設仍鎖 Asia/Taipei。 |
| **X4-E 終端 vs IDE** | 終端、CI、IDE 都可能有不同本機 timezone；測試不能依賴當下時間，需用固定 datetime 注入驗證。 |
| **X4-F 跨平台 Win/Mac/Linux** | Windows 本機與 Ubuntu Actions 對 timezone library 支援不同；優先用標準庫 zoneinfo 或明確 fallback，不用 shell date 當核心邏輯。 |
| **X4-G 主公個人視角** | 主公需要知道「今天重跑會不會把昨天或壞報告蓋掉」；計畫必須把 same-day rerun 與 promotion gate 關係寫死。 |
| **X4-H 觀測 / 治理** | 若 manifest 沒有 run_id/source_hash/timezone，doctor 只能看結果檔名；P82 要讓觀測工具可直接判斷是哪個業務日與哪次輸入。 |
| **X4-I 主公可見性** | 自動推導台北日期與 source hash 是主公看不到的行為；manifest、log、handoff 必須把推導結果與決策原因攤開。 |
| **X4-J 自動化建議性工具邊界** | 若增加 grep/lint 防止散落 datetime.now，只能視為防回歸提示，不保證抓到所有語義日期錯誤，仍需人工審核。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者會卡在 GitHub run 日期、報告日期、資料日期三者不一致；P82 必須讓這三者各自命名，不再混稱「今天」。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| Jarvis 型總控 | 固定必看 | 目標、邊界、下一步 | 已觸發；P82 僅處理 timezone/idempotency，不跨 P83/P84。 |
| Ken 型紅隊 / 技術長 | 固定必看 | 技術假設、安全邊界 | 已觸發；hash 不可包含 raw content 或 secrets。 |
| Patric 型使用者端審查官 | 固定必看 | 是否誤解或死路 | 已觸發；需避免 GitHub UTC 日期被誤讀成報告日。 |
| Jimmy 型文件主筆 | 改 docs / handoff | 可追溯與來源 | 已觸發；收官需補 TASK_HISTORY 物理真相。 |
| Marcus 型數據分析師 | 涉及判斷依據 | 定量/定性分清 | 已觸發；source_hash 與 run_id 是判斷依據。 |
| Oliver 型設計審查 | 涉及 UI | 視覺與 A11y | 未觸發；不改報告 UI layout。 |
| Penny 型 CFO | 涉及成本 | API 成本與停損 | 已觸發；本 Phase 不新增外部 API 呼叫。 |
| Jason 型執行 / DevOps | 涉及 CI/Git | 可執行性與 rollback | 已觸發；GHA UTC 排程需明確對映台北日。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 如果只改 report date，raw/analysis/manifest 仍用本機 now，三者會分裂。 | **S** | 0 | P82 明確要求唯一 resolver，所有主鏈路日期都從同一 run context 取得。 | 入計畫範圍 |
| 2 | source_hash 若包含 timestamp，每次 rerun 都不同，idempotency 形同失效。 | **S** | 0 | hash payload 排除 volatile timestamp，只含穩定輸入摘要與模式。 | 入計畫範圍 |
| 3 | GitHub Actions UTC 排程跨日，台北日期可能比 run metadata 多一天。 | **S** | 0 | manifest 同時記錄 scheduled UTC 與 run_date_taipei，測試固定邊界時間。 | 入計畫範圍 |
| 4 | 新 manifest 欄位可能讓 P79 doctor 或 P81 replay 讀取失敗。 | A | 0 | schema 更新需保持向後相容，相關 doctor/replay 測試納入驗收。 | 入計畫範圍 |
| 5 | 同日 rerun 若 production 失敗，可能把上一份健康 canonical 移走。 | **S** | 0 | P82 不繞過 P80；canonical 只在 promote 成功時更新，失敗只留 candidate/manifest。 | 入計畫範圍 |
| 6 | 若 timezone 參數化過度，會引入不需要的多區域複雜度。 | A | 0 | 只做 helper 參數化，專案預設與文件仍鎖 Asia/Taipei。 | 入計畫範圍 |

## 16. 狀態機

`DRAFT -> FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED`

目前狀態：`CLOSED`。P82 已完成本地驗證；下一步進入 P83 Data Quality / Security 草案期。
