# Phase P79 計畫書 — System Doctor（凍結版）

> 草案日期：2026-05-16
> 凍結日期：2026-05-16
> 狀態：CLOSED（2026-05-17，CI advisory 實跑驗證完成）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P79 |
| 名稱 | System Doctor |
| 影響半徑 | 標準（3-7 檔） |
| 負責模型 | GPT-5.3-Codex 高 |

## 1. 目標

建立統一診斷入口，將 daily run 的關鍵健康信號收斂為 `BLOCKING / DEGRADED / ADVISORY`，供本地與 CI 使用。

## 1.5 Entry Criteria

- [x] P78 已產生可驗證的 run manifest。
- [x] `scripts/check_daily_report_health.py` 可回傳結構化檢查結果。
- [x] P81 debug bundle 已落地，失敗時可追溯。
- [x] 非 production（配額阻塞）屬可預期狀態，doctor 需能誠實標示而不黑箱。
- [x] 不全讀 `TASK_HISTORY.md`，僅用尾端物理真相續工。

## 2. 已落地（P79.0）

- 新增 `scripts/system_doctor.py`：
  - `--profile local|ci`
  - `--require-production`
  - 讀 manifest + contract 驗證 + health checks 匯總
  - 輸出 severity table（`BLOCKING/DEGRADED/ADVISORY`）
- local/ci 行為：
  - local：只要無 BLOCKING 即 exit 0
  - ci：有 DEGRADED 或 BLOCKING 即 exit 1
- 新增測試：
  - `tests/test_system_doctor.py`

## 3. 子階段落地狀態

| 子階段 | 內容 |
|---|---|
| P79.1 | ✅ 導入 debug bundle 聯動（doctor 失敗時自動引用最新 bundle） |
| P79.2 | ✅ 加入 issue code 與 runbook 對應（`docs/OPERATIONS_RUNBOOK.md`） |
| P79.3 | ✅ 接入 CI workflow（advisory 預設 + 手動 strict gate） |

## 4. Exit Criteria

- [x] `system_doctor.py` 可在 local/ci 執行（P79.0）
- [x] 至少覆蓋 manifest missing / production pass / degraded path 測試（P79.0）
- [x] debug bundle 聯動（P79.1）
- [x] runbook issue code（P79.2）
- [x] CI 接入（P79.3，先 advisory）
- [x] 取得至少 1 次 GitHub Actions `System Doctor (Advisory)` 實跑證據

## 4.1 驗證現況（2026-05-17）

- 本地等價驗證：
  - `py -m pytest -q tests/test_system_doctor.py` → 5 passed
  - `py scripts/system_doctor.py --repo-root . --date 2026-05-16 --profile local` → exit 0（advisory）
  - `py scripts/system_doctor.py --repo-root . --date 2026-05-16 --profile ci --require-production` → exit 1（strict gate 生效）
- GitHub Actions 實跑證據（主公手動 `workflow_dispatch`, `strict_doctor=false`）：
  - `Execute AoV Pipeline`：PASS
  - `Daily Report Health Check`：PASS
  - `System Doctor (Advisory)`：PASS
  - `System Doctor (Strict Gate)`：SKIPPED（符合 `strict_doctor=false` 預期）

## 4.2 收官結論

- P79.1/P79.2/P79.3 全部完成，且 CI advisory 已有實跑證據。
- P79 正式收官，主線切換至 P80（Promotion / Atomic Write）動工前凍結。

## 5. 17 層稽核表

> 影響半徑：標準 Phase（3-7 檔）。依新規則採全 17 層逐層列示；B 級未觸發者明列 N/A 理由。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | doctor 腳本最小化，聚焦聚合，不重算業務資料 | 腳本過重難維護 | 分層函式 + dataclass |
| 2 | 邏輯層 (Logic) | severity 分級與 exit code 明確化 | 誤判導致誤阻擋 | local/ci 分開策略 |
| 3 | 架構層 (Architecture) | doctor 只讀 manifest/health，不侵入主流程 | 跟 main 流程耦合過深 | 保持 read-only 診斷 |
| 4 | 測試層 (Testing) | doctor 單元測試覆蓋 blocking/degraded/pass | 只測 happy path | 補 missing manifest / ci fail case |
| 5 | 資料層 (Data) | 以 manifest 作單一診斷輸入來源 | 多來源不一致 | manifest contract 驗證先行 |
| 6 | 可觀察性層 (Observability) | 輸出表格化 issue，可直接看 severity | 壞了仍難定位 | issue 名稱含來源（manifest/health） |
| 7 | 韌性層 (Resilience) | 外部配額阻塞時仍回傳可用診斷 | 非 production 被當 fatal | local 預設 advisory/degraded |
| 8 | 效能層 (Performance) | N/A，診斷讀取量小 | 無顯著效能風險 | 單次讀檔即可 |
| 9 | UX/A11y 層 | N/A，CLI 工具非前端 | 無 | 以簡潔表格輸出 |
| 10 | 安全層 (Security) | doctor 不讀 secrets，不輸出敏感值 | 診斷訊息外洩 | 僅輸出狀態與檔案路徑 |
| 11 | 部署層 (DevOps) | P79.3 再接入 CI，先本地驗證 | 太早 blocking CI | 分階段 rollout |
| 12 | 成本層 (Cost) | doctor 不呼叫外部 API | 成本額外增加 | 純本地資料檢查 |
| 13 | 可維護性層 (Maintainability) | severity 常數與結果模型集中 | 規則散落難調整 | `DoctorIssue/DoctorResult` |
| 14 | 文件層 (Documentation) | 計畫書與 handoff 同步 doctor 狀態 | 新視窗不知可用工具 | L1/L2 指向 P79 |
| 15 | 流程層 (Process) | P79.0 基線先落地再擴 CI | 一次做太大難驗證 | 子階段拆分 P79.1~P79.3 |
| 16 | 隱私/合規層 (Privacy) | N/A，不新增資料收集 | 無 | 只讀既有產物 |
| 17 | i18n/在地化層 | N/A，不改在地化輸出規則 | 無 | 日期仍由參數傳入 |

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| X4-A 攻擊者視角 | doctor 若直接暴露敏感值會有風險，因此輸出僅限狀態、類別與路徑。 |
| X4-B 接手者視角 | 接手者要一個指令就看懂系統狀態，不能再散落在多個腳本。 |
| X4-C 災難情境 | 連續多日非 production 時，必須快速判斷是配額阻塞還是程式回歸。 |
| X4-D 5 年後視角 | severity 與 issue 命名需要穩定，否則歷史無法比較。 |
| X4-E 終端 vs IDE | doctor 要能純 CLI 執行，不能依賴 IDE 任務。 |
| X4-F 跨平台 | 只用 pathlib + argparse + 本地檔案，避免 shell 平台差異。 |
| X4-G 主公個人視角 | 主公要一眼看出可不可以收官，不想再手動拼 log。 |
| X4-H 觀測 | doctor 將成為 P80 promotion gate 的前置觀測入口。 |
| X4-I 主公可見性 | doctor 回傳 degraded/blocking 原因必須具體可追。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | doctor 會不會把 showcase 當 hard fail，導致日常全停？ | **S** | 0 | local/ci 分流：local 不因 degraded 失敗。 | 入計畫範圍 |
| 2 | 若 manifest 壞掉，doctor 會不會還回報 OK？ | **S** | 0 | contract 驗證失敗即 BLOCKING。 | 入計畫範圍 |
| 3 | doctor 與 health 指令重複，是否多餘？ | A | 0 | doctor 是聚合層，整合 manifest + health + severity。 | 入計畫範圍 |
| 4 | 診斷結果缺上下文時仍難排錯。 | A | 0 | P79.1 將補 debug bundle 聯動。 | 入計畫範圍 |
| 5 | CI 太早 blocking 會造成噪音。 | A | 0 | P79.3 分階段接入，先 advisory 再收斂。 | 入計畫範圍 |
| 6 | 規則日後變多可能導致 doctor 過重。 | A | 0 | issue code 與 runbook 對應留在 P79.2。 | 入計畫範圍 |
