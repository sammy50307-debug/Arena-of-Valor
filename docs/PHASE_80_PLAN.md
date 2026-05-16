# Phase P80 計畫書 — Promotion / Atomic Write（執行中）

> 草案日期：2026-05-17
> 凍結日期：2026-05-17
> 狀態：IN_PROGRESS（P80.1 已落地，待 CI 實跑驗證）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P80 |
| 名稱 | Promotion / Atomic Write |
| 影響半徑 | 標準（3-9 檔，預估） |
| 負責模型 | GPT-5.3-Codex 高 |

## 1. 目標

把「報告生成」與「正式發布」分離，建立 candidate -> validate -> promote 的安全鏈路，避免錯誤報告覆蓋對外入口。

## 1.5 Entry Criteria

- [x] P79 收官（doctor + runbook + CI advisory 實跑證據齊備）
- [x] 現有 health check 可機械化驗證 report/link/mode
- [x] run manifest 可提供 mode/status/eligibility 訊號
- [x] 已明確禁止一次混修 P82+ 內容

## 2. 動工範疇（凍結）

1. candidate 與 production 檔案路徑分流（不直接覆蓋）
2. promotion gate：僅健康且 eligible 才 promote
3. atomic write：`.tmp` -> rename，避免半寫入
4. index 更新只在 promote 成功後執行

## 3. 非範疇（避免偏航）

- 不在 P80 做 replay/quarantine/backfill（屬 P81）
- 不在 P80 做 timezone/idempotency（屬 P82）
- 不在 P80 擴 data quality/security gate（屬 P83）

## 4. Exit Criteria（預先凍結）

- [x] candidate 生成不會直接覆蓋 production canonical report
- [x] promotion 前需通過 doctor/health gate（以既有訊號為準）
- [x] promotion 寫入路徑採原子化
- [x] landing/index 只指向 promote 後目標
- [ ] 至少 1 組成功 promote + 1 組被 gate 擋下的測試證據

## 4.1 已落地（P80.1）

- `reporter/generator.py`
  - `generate(..., promote=False)` 支援僅產 candidate，不觸發 canonical/landing 更新
  - 新增 `promote_candidate(...)`，以 `.tmp -> os.replace()` 原子覆蓋 canonical，並在 promote 後更新 landing
- `scripts/check_daily_report_health.py`
  - `run_checks()` 新增 `check_landing` 與 `expected_report_path`
  - 支援 pre-promotion gate 只驗 candidate 本身，不把 landing 當前置條件
- `main.py`
  - 主鏈路改為：先 `generate(promote=False)` 產 candidate
  - `evaluate_publish_gate(..., candidate_report_path=...)` 做 pre-promotion gate
  - 僅在 `mode=production` 且 gate 無理由時 promote
  - 僅在 promote 成功後才進入 `github_backup_job`
- 測試
  - `tests/test_daily_report_health.py` 新增 pre-promotion gate 測試
  - `tests/test_report_generator_landing.py` 新增 `promote_candidate` 測試
  - 全套 `pytest`：`154 passed`

## 5. 17 層稽核表

> 影響半徑：標準 Phase（預估 3-9 檔）。依規則列 S+A，B 級未觸發者明列 N/A 理由。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | 最小化改動，只抽 promotion/atomic write 必需函式 | 混入 unrelated refactor | 僅動 candidate/promote 路徑 |
| 2 | 邏輯層 (Logic) | 生成與發布分離，promote 前必 gate | 健康檢查漏判導致壞報告發布 | 使用既有 doctor/health/manifest 訊號 |
| 3 | 架構層 (Architecture) | promotion 作為 report 產出後的獨立階段 | main/generator 耦合過深 | 保持小型 helper，避免新框架 |
| 4 | 測試層 (Testing) | 補成功 promote 與 gate 擋下測試 | 只測 happy path | 至少一正一反 |
| 5 | 資料層 (Data) | candidate 與 production 路徑分流 | candidate 污染 canonical | 檔名/目錄明確分離 |
| 6 | 可觀察性層 (Observability) | promotion 結果寫入 manifest/log | promotion 失敗難追 | doctor 可讀到狀態 |
| 7 | 韌性層 (Resilience) | atomic write 避免半檔 | 中斷時留下壞檔 | `.tmp` 後 rename |
| 8 | 效能層 (Performance) | N/A，報告檔小且單次寫入 | 無顯著效能風險 | 不新增大量 IO |
| 9 | UX/A11y 層 | N/A，不改前端版面 | 無 | 僅控制發布入口 |
| 10 | 安全層 (Security) | 不把 raw/secret 寫入 promotion metadata | debug 資訊外洩 | 僅記路徑與狀態 |
| 11 | 部署層 (DevOps) | CI 先沿用 advisory doctor，不立刻升 blocking | 過早阻斷排程 | P80 僅本地 gate，CI 升級另議 |
| 12 | 成本層 (Cost) | 不呼叫外部 API | 成本增加 | 純本地驗證 |
| 13 | 可維護性層 (Maintainability) | promote 規則集中 | 發布規則散落 | helper + 測試鎖定 |
| 14 | 文件層 (Documentation) | handoff/active/TASK_HISTORY 同步 | 新視窗不知道 P80 邊界 | L1 指向本計畫 |
| 15 | 流程層 (Process) | FROZEN 後待核准才動工 | 未核准先改碼 | handoff 明確禁止 |
| 16 | 隱私/合規層 (Privacy) | N/A，不新增資料收集 | 無 | 只處理既有 report |
| 17 | i18n/在地化層 | N/A，不改文案/日期規則 | 無 | 日期/時區留待 P82 |

## 6. Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| X4-A 攻擊者視角 | 若未分離 candidate/production，外部或內部錯誤都可能把 showcase/backfill 推成正式入口。 |
| X4-B 接手者視角 | 接手者需要一眼知道「生成成功」不等於「發布成功」。 |
| X4-C 災難情境 | 報告寫到一半中斷時，首頁不得指向半檔或壞檔。 |
| X4-D 5 年後視角 | promotion gate 要可測、可讀、可逐步升級，不能散在多個 if。 |
| X4-E 終端 vs IDE | 必須能用 CLI/pytest 驗證，不依賴 GitHub UI。 |
| X4-F 跨平台 | atomic write 使用 pathlib/os 原生能力，避免 shell 專屬語法。 |
| X4-G 主公個人視角 | 主公要能安心看到首頁只指向通過 gate 的報告。 |
| X4-H 觀測 | promotion 結果需能被 doctor 或 manifest 追蹤。 |
| X4-I 主公可見性 | 被 gate 擋下時要說明原因，不可靜默不更新。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | candidate 生成成功就被誤當 production，是否仍會污染首頁？ | **S** | 0 | P80 明確分離 generate/promote，index 只在 promote 後更新。 | 入計畫範圍 |
| 2 | atomic write 若只保護 report，不保護 index，首頁仍可能半更新。 | **S** | 0 | report 與 index 更新都需納入原子寫入或明確順序。 | 入計畫範圍 |
| 3 | gate 用太嚴會讓 daily 永遠不發布。 | A | 0 | P80 先用既有 health/manifest 訊號，CI blocking 另議。 | 入計畫範圍 |
| 4 | gate 用太鬆會把 showcase/backfill 放上首頁。 | **S** | 0 | eligible/mode/health 必須共同通過。 | 入計畫範圍 |
| 5 | P80 會不會偷做 P82 timezone/idempotency？ | A | 0 | 明列非範疇，日期問題留待 P82。 | 入計畫範圍 |

## 7. 狀態機

`FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED`

目前狀態：`IN_PROGRESS`（已完成 P80.1 程式落地，待 CI 實跑驗證）。
