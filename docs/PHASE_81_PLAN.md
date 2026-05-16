# Phase P81 計畫書 — Replay / Backfill 治理（凍結版）

> 草案日期：2026-05-16
> 凍結日期：2026-05-16
> 狀態：CLOSED（已完成 P81.0 + P81.1 + P81.2 + P81.3）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P81 |
| 名稱 | Replay / Backfill 治理 |
| 影響半徑 | 標準（3-7 檔） |
| 負責模型 | GPT-5.3-Codex 高 |

## 1. 目標

建立可重放機制：當日常流程受外部配額阻塞時，可用既有 `analysis_YYYYMMDD.json` 重建報告、補 run manifest、並做健康檢查。

## 1.5 Entry Criteria

- [x] P77 已以外部配額阻塞收官，production 產出不可強求偽造。
- [x] P78.0 已提供 `run_manifest.json` 基礎能力，可供 replay/backfill 寫入同一狀態來源。
- [x] `scripts/check_daily_report_health.py` 已能回傳結構化 health checks。
- [x] replay 只使用既有 `analysis_YYYYMMDD.json` / `raw_YYYYMMDD.json`，不重新呼叫外部 LLM。
- [x] 不全讀 `TASK_HISTORY.md`；本 Phase 只追加尾端紀錄。

## 2. 已落地（P81.0）

- 新增 `scripts/replay_run.py`
  - `--date YYYY-MM-DD`
  - 讀取 `analysis_YYYYMMDD.json` 重建報告
  - 寫入 run manifest（標記 `replay_source=analysis_json`）
  - 可選 `--check-health --expected-mode any|production`
- 新增測試：
  - `tests/test_replay_run.py`
  - `tests/test_run_manifest.py`

## 2.1 已落地（P81.1）

- `scripts/replay_run.py` 新增 quarantine 流程：
  - invalid JSON → `data/quarantine/invalid_json/`
  - analysis schema violation → `data/quarantine/analysis_schema_violation/`
- 每次 quarantine 會輸出 sidecar `.meta.json`（reason/detail/time/original_path）。
- 測試：
  - `tests/test_replay_run.py::test_replay_run_quarantines_invalid_json`
  - `tests/test_replay_run.py::test_replay_run_quarantines_schema_violation`

## 2.2 已落地（P81.2）

- replay 產物加入 backfill 標記：
  - report metadata comment：`backfill: true | replay_source: analysis_json`
  - run manifest：`is_backfill=true`、`replay_source=analysis_json`
- 實跑驗證：
  - `py scripts/replay_run.py --date 2026-05-16 --check-health --expected-mode any`
  - 成功重建報告與 manifest，mode 仍忠實呈現 `showcase_forced`（受外部配額阻塞）

## 3. 後續子階段

| 子階段 | 內容 |
|---|---|
| P81.1 | replay 加入 quarantine（壞 analysis 隔離） |
| P81.2 | backfill 報告標記與來源說明 |
| P81.3 | debug bundle（health + manifest + 失敗原因）輸出 |

## 3.1 已落地（P81.3）

- 新增 `scripts/debug_bundle.py`：
  - 輸出 `data/debug_bundles/YYYY-MM-DD/debug_bundle_<timestamp>.json`
  - 內含：health checks、manifest snapshot、paths、error reason、extra context。
- `scripts/replay_run.py` 新增 `--debug-bundle`：
  - 成功可主動輸出 debug bundle。
  - 失敗（missing analysis / quarantine / health fail）自動輸出 debug bundle。
- 測試：
  - `tests/test_replay_run.py::test_replay_run_emits_debug_bundle_when_requested`

## 4. Exit Criteria

- [x] `replay_run.py` 可用指定日期重建報告（P81.0）
- [x] replay 後自動寫 run manifest（P81.0）
- [x] quarantine 流程（P81.1）
- [x] backfill 標記（P81.2）
- [x] debug bundle（P81.3）

## 5. 17 層稽核表

> 影響半徑：標準 Phase（3-7 檔）。依新規則採全 17 層逐層列示；B 級未觸發者明列 N/A 理由。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | `scripts/replay_run.py` 小步加入 replay/quarantine/debug bundle | CLI 功能膨脹 | 保持單一入口、輔助函式拆分 |
| 2 | 邏輯層 (Logic) | 壞 JSON / schema violation 先 quarantine，再 fail | 壞資料反覆污染補跑 | 移至 `data/quarantine/` 並寫 sidecar |
| 3 | 架構層 (Architecture) | replay 只重建報告與 manifest，不碰 promotion | P81 與 P80 混修 | landing/promotion 仍由 P77/P80 gate 處理 |
| 4 | 測試層 (Testing) | `tests/test_replay_run.py` 覆蓋缺檔、成功、quarantine、debug bundle | 只測成功路徑 | 失敗路徑也列為必測 |
| 5 | 資料層 (Data) | backfill/replay_source 寫入 report metadata 與 manifest | 歷史報告真假混雜 | `is_backfill=true` 與 `replay_source=analysis_json` |
| 6 | 可觀察性層 (Observability) | debug bundle 收 health checks / manifest / paths / error | 失敗時只能翻 log | `--debug-bundle` 與 fail auto bundle |
| 7 | 韌性層 (Resilience) | 外部配額阻塞時仍可由既有 analysis 補跑 | 無 analysis 時無法 replay | 明確 FAIL + debug bundle |
| 8 | 效能層 (Performance) | N/A，小型 JSON/HTML 讀寫 | 無顯著效能風險 | 不重跑 LLM |
| 9 | UX/A11y 層 | N/A，不改 UI / template layout | 無 | 只加 metadata comment |
| 10 | 安全層 (Security) | quarantine/debug bundle 不寫 secrets | 診斷包外洩敏感內容 | 只寫路徑、狀態、manifest snapshot |
| 11 | 部署層 (DevOps) | N/A，不改 workflow/deploy | 無 | P79/P80 再接 CI |
| 12 | 成本層 (Cost) | replay 不呼叫外部 LLM | 補跑燒 API 額度 | 使用既有 analysis JSON |
| 13 | 可維護性層 (Maintainability) | debug bundle 抽到 `scripts/debug_bundle.py` | replay 腳本過長難測 | bundle writer 獨立測試入口 |
| 14 | 文件層 (Documentation) | P81 計畫、handoff、TASK_HISTORY 同步 | 新視窗不知道 P81 已 CLOSED | L1/L2/L4 明確標狀態 |
| 15 | 流程層 (Process) | P81.0→P81.3 逐步收斂，完成後 CLOSED | 未完成子階段被誤認收官 | Exit Criteria 全部打勾 |
| 16 | 隱私/合規層 (Privacy) | N/A，不新增資料蒐集 | 無 | 只處理本地既有檔案 |
| 17 | i18n/在地化層 | N/A，不改語系/時區規則 | 無 | P82 處理 timezone/idempotency |

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| X4-A 攻擊者視角 | replay 若直接吃壞 JSON 會炸流程，需加 quarantine 與錯誤分類。 |
| X4-B 接手者視角 | 接手者需一個命令就能補跑，不應要求手改多檔。 |
| X4-C 災難情境 | 外部 API 長時間 429 時，replay 是唯一可持續輸出的補救路。 |
| X4-D 5 年後視角 | replay 產出是否為 backfill 必須可追溯，否則歷史真假混雜。 |
| X4-E 終端 vs IDE | replay 必須 CLI 可用，不能依賴 IDE 任務。 |
| X4-F 跨平台 | script import path 需穩定，避免 Windows 跑得動 Linux 壞掉。 |
| X4-G 主公個人視角 | 主公要的是「能補跑、能看清狀態」，不接受黑箱補檔。 |
| X4-H 觀測 | replay 產生 manifest，供 P79 doctor 收斂觀測。 |
| X4-I 主公可見性 | replay 後是否通過 health check 必須明確印出。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | replay 可能重建出 showcase，不是真 production。 | **S** | 0 | 這是事實揭露，不偽裝；health 會明示 mode。 | 入計畫範圍 |
| 2 | script import 在不同執行路徑可能失敗。 | **S** | 0 | 已加 repo-root `sys.path` 注入並有測試。 | 入計畫範圍 |
| 3 | 沒有 analysis 檔就無法 replay。 | A | 0 | 明確 FAIL 訊息，後續 P81.1 加引導與 quarantine。 | 入計畫範圍 |
| 4 | replay 生成報告可能污染 landing。 | A | 0 | 目前 landing 有 production gate，不會被 showcase 誤覆蓋。 | 入計畫範圍 |
| 5 | replay 結果若沒 manifest，觀測仍斷。 | A | 0 | 已在 P81.0 寫入 manifest。 | 入計畫範圍 |
| 6 | backfill 沒標記會混入日常報告。 | A | 0 | P81.2 明確補 backfill 標記。 | 入計畫範圍 |
