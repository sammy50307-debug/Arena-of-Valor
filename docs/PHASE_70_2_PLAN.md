# Phase P70.2 計畫書 — GHA 每日健康巡檢與無報告根因排查（凍結版）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen
> 狀態：✅ 已收官；每日報告健康檢查已接入 workflow

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P70.2 |
| **Phase 名稱** | GHA 每日健康巡檢與無報告根因排查 |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準（預估 5-8 檔；workflow / script / tests / docs） |
| **預估投入時數** | 2.5 h |
| **Token budget** | 45K tokens |
| **負責模型** | GPT-5.3-Codex（repo 動工 + CI 腳本）；若 GHA 外部證據不足，改 GPT-5.5 高做診斷重審 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| `.github/workflows/daily_report.yml` | scheduled but weakly observed | scheduled + health-gated | 每日排程仍負責產報，但新增「是否真的產出今日 canonical 報告 / index 是否更新」的機械化檢查 | 健康檢查腳本與 workflow step 落地，且不洩漏 secrets | Codex 實作；主公核准 |
| 每日報告健康狀態 | 人工事後發現 | 本機/CI 可查 | 用明確 exit code 判定日期報告、metadata、landing 指向與 git diff 是否符合預期 | `scripts/check_daily_report_health.py` 通過單測與 dry-run | Codex 實作；主公驗收 |

---

## 1. 目標 (Objective)

釐清 2026-05-07、2026-05-08 GitHub Actions 連續無報告的根因，並讓每日排程在「沒產出今日 canonical 報告 / landing 沒更新 / metadata 不可信」時用機械化健康檢查失敗或留下明確診斷訊息。

## 2. 觸發背景 (Why Now)

P63.4 修過 daily workflow 的 concurrency、git config、fallback add 與 metadata 問題，但 TASK_HISTORY 仍記錄「workflow_dispatch 驗證 C-B/C-C/C-D 未達成」。後續 P65-hotfix / P63.1.2 期間又留下 2026-05-07、2026-05-08 連兩天無報告的待排查事項。P74 已關閉 R-015 測試債，現在適合回到 production health：確認每日自動產報是否可信。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 只人工排查 | 讀 git log / reports / workflow，不新增工具 | 最快、改動少 | 下次仍靠主公肉眼發現，問題會再潛伏 | 不採為最終方案 |
| B. 診斷 + 最小健康檢查 | 先還原 5/7、5/8 證據，再新增可本機/CI 跑的 health checker | 能同時解根因與未來防呆，影響半徑可控 | 需設計 exit code 與 CI step，避免誤報 | **採用** |
| C. 重做整條 daily pipeline | 大改 workflow、通知、fallback、artifact、cron | 可一次翻新 | 影響半徑大，會混入 P70.4/P70.6 類需求 | 不採 |

---

## 3. Entry Criteria（入口條件）

開工前必須全部完成：

- [x] 前置 Phase 已收官：P74 / R-015 已收官，測試基線恢復 112 passed
- [x] 既有 workflow 已定位：`.github/workflows/daily_report.yml`
- [x] 產報入口已定位：`main.py --run-now` → `ReportGenerator.generate()`
- [x] 既有歷史證據已定位：TASK_HISTORY P63.4 / P65-hotfix / P63.1.2 / handoff P70.2
- [x] 主公核准本計畫：2026-05-16「核准凍結」+「請繼續所有工作」
- [x] 本機工作樹 P74 變更已辨識但尚未 commit；P70.2 動工時嚴格分開 stage 範圍
- [x] 不全讀 `TASK_HISTORY.md`：只查尾段與關鍵錨點

## 4. Exit Criteria（退出條件）

達成全部才算收官：

- [x] S0 證據表完成：列出 2026-05-07 / 2026-05-08 各自「報告檔是否存在、index 是否指向、git commit 是否含報告、workflow run 證據是否可得」
- [x] `scripts/check_daily_report_health.py` 可用 `--date YYYY-MM-DD` 檢查 canonical report、metadata comment、landing link、可選 git dirty/staged 狀態
- [x] 健康檢查至少 5 個單元測試通過，涵蓋「報告存在 / 報告缺失 / metadata 非 production / landing 未指向 / 日期格式錯誤」（7 cases）
- [x] `.github/workflows/daily_report.yml` 在 pipeline 後加入 health check step；若前序 pipeline 失敗，health step 仍能輸出診斷，但不洩漏 secrets
- [x] 本機 `py -m pytest -q` 或明確子集測試通過（119 passed）
- [x] `git diff --check` 無 whitespace error
- [x] `TASK_HISTORY.md` 追加 P70.2 無損紀錄；不全檔編輯
- [x] `NEXT_SESSION_HANDOFF.md` 更新下一步：R-014 或主公指定項目

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 2.5 h |
| 預估收益等級 | 高 |
| 收益描述 | 讓每日自動產報從「跑了但不知道有沒有成功」變成「有明確健康狀態與失敗診斷」，降低主公隔天才發現無報告的風險 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 新增小型 health checker，workflow 只加最小 step | 腳本寫太大變成另一套 pipeline | 單一責任：只檢查報告健康，不負責產報 |
| **2. 邏輯層 (Logic)** | 先還原 5/7、5/8 因果鏈，再落地檢查 | 把「沒有報告」誤判為 GHA 問題，忽略 lockfile/API/commit 無變更 | S0 證據表拆四格：run、report、index、commit |
| **4. 測試層 (Testing)** | `tests/test_daily_report_health.py` 覆蓋 5 種狀態 | 健康檢查腳本本身誤報 | 測試用 tmp_path 建假 reports/index，不讀真 data |
| **10. 安全層 (Security)** | 不印 secrets，不讀 API key 值，只檢查環境變數是否存在可選 | workflow log 洩漏 token / API key | 禁止 echo secret；只輸出 env name 是否 set 的布林摘要 |

### A 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 產報 pipeline 與 health check 分離 | health checker 反過來耦合 ReportGenerator internals | 只讀生成後的檔案與 metadata comment |
| **5. 資料層 (Data)** | 只讀 `data/reports/*.html` / `index.html`，不改 raw/analysis | 誤把 untracked 預覽報告納入判斷 | 僅檢查 canonical `aov_report_YYYY-MM-DD.html` |
| **6. 可觀察性層 (Observability)** | health step 輸出日期、檔案存在、metadata mode、landing link、git diff 摘要 | log 太長或資訊不夠 | 固定短表輸出；不 dump HTML 內文 |
| **7. 韌性層 (Resilience)** | workflow 前序失敗時仍跑 health check 診斷 | `if: always()` 造成失敗被吞 | health step 可輸出診斷，最終 exit code 仍反映健康失敗 |
| **13. 可維護性層 (Maintainability)** | checker CLI 參數明確，測試用 tmp fixtures | 下次改報告命名規則會忘記改 checker | constants 集中，計畫書記錄 contract |
| **14. 文件層 (Documentation)** | P70.2 計畫、TASK_HISTORY、handoff 同步 | 舊 WIP / handoff 又漂移 | 收官時同步 WIP_PHASES 與 handoff |
| **15. 流程層 (Process)** | P70.2 不混入 P70.4 OpenAI fallback / P70.6 LRU TTL | 範圍膨脹 | 本 Phase 僅排查與健康巡檢，不新增 LLM provider 或 cache eviction |

### B 級層

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | CI 執行時間 | health checker 只讀少量檔案 | CI 多跑太久 | 目標 < 3 秒 |
| **11. 部署層 (DevOps)** | `.github/workflows/` | health check step 加在 daily workflow 後段 | CI YAML 語法錯 / exit code 誤傷 | 本機 grep + 若可行跑 actionlint fallback；最少改動 |
| **12. 成本層 (Cost)** | GHA minutes / API | health check 不呼叫 LLM/API | 驗證 workflow_dispatch 可能燒 API | 動工期先用本機與腳本測試；真 GHA 驗收需主公同意 |
| **16. 隱私/合規層 (Privacy)** | 第三方 API secrets | 不輸出 secret 值，不上傳 artifact 內含 secrets | log 洩漏 | 只列 secret name set/unset 或完全不查 secret |
| **17. i18n/在地化層** | 台北日期 vs UTC cron | health check 明確支援 `--timezone Asia/Taipei` 或 `--date` | UTC 00:00 與台北日期混淆 | workflow 直接傳台北日期或用 Python timezone 算 |

### 層級互鎖驗證

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Architecture 層 → 已動 Documentation 層
- [x] 動 Data 層 → 已動 Maintainability 層
- [x] 動 Security 層 → 已動 Testing 層
- [x] 動 Performance 層 → 已動 Observability 層
- [x] 動 DevOps 層 → 已動 Testing 層

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `docs/PHASE_70_2_PLAN.md` | 可逆 | ✅ 2026-05-16 |
| 新增 `scripts/check_daily_report_health.py` | 可逆 | ✅ 2026-05-16 |
| 新增 `tests/test_daily_report_health.py` | 可逆 | ✅ 2026-05-16 |
| 修改 `.github/workflows/daily_report.yml` | 可逆 | ✅ 2026-05-16 |
| 追加 `TASK_HISTORY.md` / 更新 handoff | 半可逆 | 收官時需主公知情 |
| 手動 `workflow_dispatch` 真跑 | 半可逆 | 需主公核准，因可能消耗 API / 產生 commit |
| `git push` | 半可逆 | 推前必問主公 |

### X2 盲區掃描

主公看不到但會發生的：

- [x] log 副作用：GHA console 會多 health check 表格，但不含 secrets
- [x] 中間檔產出：測試可能產生 `.pytest_cache/`，不 stage
- [x] 系統狀態變更：若 workflow_dispatch 真跑，可能產生報告 commit；需主公核准

### X3 時間敏感性

- 本計畫草案日期：2026-05-16
- 本計畫過期日期：2026-06-16
- 風險記錄帶日期：✅ 5/7、5/8 無報告為 2026-05-08 前後遺留

### X4 多角度同行審查

- **主公視角**：主公要知道每天 08:00 自動化到底有沒有成功，而不是隔天打開才發現報告沒更新。
- **世界頂尖駭客 / 紅隊攻擊者視角**：CI log 是主要攻擊面；不得 echo secrets、不得把 env dump 到 log、不得把 token 透過 artifact 或 error message 洩漏。
- **接手者視角**：半年後新人要能只看 checker CLI help 與測試，就知道每日報告健康的 contract 是什麼。
- **X4-J 自動化建議性工具邊界**：health checker 是規則式檢查，不代表輿情內容品質正確；它只能保證「產出物存在且 metadata / landing 基本一致」，不能保證 LLM 分析品質。
- **X4-K 使用者端審查官 / Patric 型人格**：若報告存在但 landing 沒指到它，主公感受到的仍是「沒報告」；因此檢查必須包含 `index.html` 指向。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | GitHub Actions run log 需要 GitHub 權限或網頁資訊，本機不一定拿得到 | 中 | 中 | 環境依賴 | S0 分成「可得證據」與「待主公提供 run URL」兩欄 |
| R2 | 5/7、5/8 無報告根因可能已被後續 P63.1.2/P69.1/P70 修掉 | 中 | 中 | 時間敏感 | 本 Phase 不強行重修舊 bug，改建立健康檢查防復發 |
| R3 | health check 太嚴，遇 API 配額耗盡 fallback 仍產報卻被判失敗 | 中 | 中 | 邏輯 | mode policy 明定：production 期望；showcase_forced 視為 warning 或 failure 由計畫書決定 |
| R4 | workflow `if: always()` 與 exit code 設計錯誤，導致真正失敗被吞 | 中 | 高 | DevOps | health step 最後明確 `exit 1`；fallback push 不吞 health 結果 |
| R5 | 真跑 workflow_dispatch 會消耗 API quota 並可能產生 commit | 中 | 中 | 成本 / 流程 | 真 GHA 驗收需主公另行確認；草案與本機階段不真跑 |
| R6 | 本機 untracked reports 很多，容易誤判健康或誤 stage | 中 | 中 | Git 流程 | checker 只看 canonical date；stage 前固定 `git status -sb` |

**高風險加權檢查（META4）**：

- 高風險數量：1
- 加權分數：7
- 是否 >= 5 須請示主公：是，本計畫需主公核准後才動工；workflow_dispatch 真跑需二次確認

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 證據盤點** | 查 reports、index、git log、workflow yaml、可得 run 線索；建立 5/7、5/8 證據表 | R1/R2 | 表格列出每日期 report/index/commit/run 狀態 |
| **S1 Contract 設計** | 定義健康檢查項：canonical report、metadata mode、landing link、git diff、timezone | R3/R4 | 計畫補遺或實作註解寫明 pass/warn/fail |
| **S2 Checker 實作** | 新增 `scripts/check_daily_report_health.py` + CLI exit code | R6 | 手動跑缺報告 / 正常報告兩種案例 |
| **S3 測試** | 新增 `tests/test_daily_report_health.py`，用 tmp_path 假資料 | R3/R6 | 至少 5 cases 通過 |
| **S4 Workflow 接線** | daily_report.yml 加 health check step；保護 secrets | R4/R5 | YAML diff 小範圍；本機可檢查命令 |
| **S5 收官** | TASK_HISTORY / handoff / WIP 更新；列出是否仍需主公提供 GHA run URL | 流程漂移 | Exit Criteria 全勾 |

---

## 10. 影響檔案清單

**新增**：

- `docs/PHASE_70_2_PLAN.md`
- `scripts/check_daily_report_health.py`
- `tests/test_daily_report_health.py`

**可能修改**：

- `.github/workflows/daily_report.yml`：新增 health check step
- `TASK_HISTORY.md`：追加 P70.2 無損紀錄
- `NEXT_SESSION_HANDOFF.md`：更新下一步
- `memory/history_lookup/WIP_PHASES.md`：同步待辦狀態

**刪除**：

- 無

**影響但未直接修改**：

- `data/reports/`：被 health checker 讀取，不應在本 Phase 直接新增/刪除報告
- `index.html`：被 health checker 讀取；除非 S0 發現健康 contract 需要補最小修法，否則不改
- GitHub Actions run / API quota：若主公核准 workflow_dispatch 才會觸發

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] S0 證據證明 5/7、5/8 無報告是多因素疊加，而非單一 bug
- [ ] health checker 第一次設計造成 false positive / false negative
- [ ] workflow_dispatch 真跑消耗 API quota 但沒有產出可用診斷
- [ ] 有任何「我以為...結果不是」事件

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-70-2-daily-health.md`

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | CI log 與 workflow env 是主要攻擊面；最小緩解是禁止輸出 secret 值、禁止 dump env、health checker 只讀檔案與 metadata。 |
| **X4-B 接手者** | 接手者需要知道健康檢查不是產報器，而是產報後的 contract verifier；CLI help 與測試案例必須清楚。 |
| **X4-C 災難情境** | 情境：cron 每天跑但無報告，主公一週後才發現；緩解：health step 讓 run 直接紅燈並留下缺哪一項。 |
| **X4-D 5 年後** | GitHub Actions、Python 版本與報告命名可能變動；checker 應集中常數並用測試保護命名 contract。 |
| **X4-E 終端 vs IDE** | 本機 PowerShell 用 `py`，GHA 用 `python`；命令需跨平台，且避免 PowerShell 專屬語法進 workflow。 |
| **X4-F 跨平台 Win/Mac/Linux** | checker 應使用 pathlib 與標準庫，不依賴 Windows path；workflow 在 Ubuntu 執行，測試在 Windows 也要通過。 |
| **X4-G 主公個人視角** | 主公需要一眼知道今天報告是否真的更新；health output 必須是短表，不要逼主公翻千行 log。 |
| **X4-H 觀測 / 治理** | P63.4 的 C-B/C-C/C-D 驗收未完全達成，P70.2 應把缺口轉成機械化檢查與明確 runbook。 |
| **X4-I 主公可見性** | 主公看不到 cron 是否跳過、fallback 是否吞錯、landing 是否沒更新；health checker 必須攤開 report/index/metadata/commit 四件事。 |
| **X4-J 自動化建議性工具邊界** | checker 只能判定產物健康，不能判定輿情內容真偽、LLM 品質或社群資料完整性；收官文件要明說。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 如果報告檔存在但首頁仍指舊日期，使用者體感仍是失敗；因此 landing link 是必檢項。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P70.2 只做 daily health，不混入 OpenAI fallback / cache TTL |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；workflow log 不得洩漏 secrets，workflow_dispatch 需主公二次確認 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；報告存在但首頁沒更新也算體感失敗 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；S0 證據表必須留在 TASK_HISTORY |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；5/7、5/8 證據要分可得/不可得，不亂補故事 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | N/A；本 Phase 不改報告 UI |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；workflow_dispatch 可能消耗 LLM/API quota，需主公核准 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；workflow 改動要保持 Ubuntu shell 可執行，rollback 為 revert YAML step |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 沒有 GitHub run log 就很難證明 5/7、5/8 真根因 | **S** | N/A | S0 證據表分「已證實」與「需主公提供 run URL」 | 入計畫範圍 |
| 2 | health checker 可能只檢查檔案存在，卻漏掉 landing page 指舊報告 | **S** | N/A | Exit Criteria 強制檢查 `index.html` 指向 | 入計畫範圍 |
| 3 | workflow 加 `if: always()` 可能讓前面失敗被 fallback push 掩蓋 | **S** | N/A | health step 最終 exit code 不吞；fallback 不等於健康 | 入計畫範圍 |
| 4 | mode 非 production 時到底算失敗還是警告，若不定義會吵架 | A | N/A | S1 明定 mode policy，至少 `error_fallback` 必 fail | 入計畫範圍 |
| 5 | 真跑 workflow_dispatch 可能燒 API quota，還可能產生雜訊 commit | A | N/A | workflow_dispatch 真跑需主公二次確認；本地階段不真跑 | 入計畫範圍 |
| 6 | 現在工作樹有 P74 變更與 untracked reports，P70.2 很容易混 commit | A | N/A | stage 前固定列檔，只 stage P70.2/P74 明確範圍 | 入計畫範圍 |

---

## STR9 — Skill 收官 entry_points 機械化檢查

N/A。本 Phase 不新增或更新 skill。

---

## 12. 凍結戳記

- **凍結人**：主公核准 + Codex
- **凍結時間**：2026-05-16 00:23 +08:00
- **凍結後變更**：禁止；如需修改，新增 P70.2 補遺並引用本檔
