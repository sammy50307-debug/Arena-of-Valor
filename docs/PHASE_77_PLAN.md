# Phase P77 計畫書 — Daily Monitoring 主鏈路止血（凍結待核准）

> 草案日期：2026-05-16
> 草擬人：Codex
> 凍結日期：2026-05-16
> 計畫書版本：v1.0 frozen pending approval
> 狀態：CLOSED（外部配額阻塞；2026-05-16 主公拍板轉交 P78/P81）

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P77 |
| **Phase 名稱** | Daily Monitoring 主鏈路止血 |
| **凍結日期** | 2026-05-16 |
| **影響半徑** | 標準 Phase（預估 5-8 檔；runtime + tests + docs） |
| **預估投入時數** | 2.5-4 h |
| **Token budget** | 50K tokens |
| **負責模型** | GPT-5.3-Codex（repo patch + 測試）；若根因擴散，升 GPT-5.5 高做重審 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 目標狀態 | 轉換條件 | 核准 |
|---|---|---|---|---|
| `HistoryResolver` 非 showcase 路徑 | runtime `NameError`，被 main fallback 掩蓋 | 真實 archives 可用，錯誤 fail loud | regression tests 通過 | P77 動工核准後 |
| fallback 趨勢 | 程式錯誤可能被固定假資料掩護 | expected empty / external failure / programmer error 分級 | tests + report metadata | P77 動工核准後 |
| landing link | 指向舊 report | 指向最新合格 production report | health check 通過 | P77 動工核准後 |
| report health | 測工具但不保證 repo 現況 | repo-state smoke 可抓 stale/missing/preview | tests + dry-run | P77 動工核准後 |

---

## 1. 目標 (Objective)

修掉目前已知會讓每日監測報告「看似正常但實際不可信」的主鏈路問題：歷史趨勢 runtime error、fallback 假資料掩護、首頁連到舊報告、preview/production 混淆，以及測試全綠但發布面壞掉的盲區。

## 2. 觸發背景 (Why Now)

本輪只讀審查已確認：

- `analyzer/history.py` 非 showcase 路徑使用未定義的 `archives`。
- `main.py` catch 後塞固定趨勢，導致錯誤可能被假資料掩護。
- `index.html` 主按鈕仍指 `aov_report_2026-05-06.html`。
- 最新 canonical report 停在 2026-05-10，且 metadata 為 preview。
- 2026-05-16 報告缺失。

P77 只做止血，不引入 manifest/schema/promotion gate；這些交給 P78-P80。

## 2.5 決策取捨

| 方案 | 做法 | 優點 | 代價 / 風險 | 判斷 |
|---|---|---|---|---|
| A. 一口氣導入 P78-P80 架構 | 同時修 bug 與新架構 | 長期完整 | 根因與新架構風險混在一起 | 不採第一步 |
| B. P77 只止血 | 先修確定壞掉的主鏈路 | 風險可控、容易驗證 | 合約化要下一 Phase | **採用** |
| C. 只修 `archives` 一行 | 最快 | landing/fallback/health 盲區仍在 | 不採 |

---

## 3. Entry Criteria

- [x] 主公明確核准 P77 動工
- [ ] P76.1 已完成：handoff active bootstrap 與 L2/L3/L4 文件存在
- [ ] `git status -sb` 已確認 dirty 範圍
- [ ] baseline 已跑：`py -m pytest -q`
- [ ] 已重現或確認 `HistoryResolver(..., showcase=False)` 問題
- [ ] 不全讀 `TASK_HISTORY.md`

## 4. Exit Criteria

- [ ] `HistoryResolver().resolve_trends(..., showcase=False)` 不再噴 `NameError`
- [ ] tests 覆蓋：無 archives、有 archives、壞 archive、showcase mode
- [ ] fallback 分級：程式錯誤不可假裝正常；degraded reason 可觀察
- [ ] `check_daily_report_health` 能抓 stale landing、missing report、preview report
- [ ] `index.html` 指向最新合格 production report，或明確保留 last-known-good 並標示日期
- [ ] `py -m pytest -q` 通過
- [ ] `git diff --check` 通過
- [ ] `NEXT_SESSION_HANDOFF.md` active bootstrap 更新下一步
- [x] `TASK_HISTORY.md` append P77 物理真相

---

## 5. P77 子階段

| 子階段 | 範圍 | Allowed Files | 不做 |
|---|---|---|---|
| **P77.0** | 修 `HistoryResolver` NameError + regression tests | `analyzer/history.py`, `tests/...` | 不改 landing、不改 workflow |
| **P77.1** | fallback 分級與可觀察性 | `main.py`, `tests/...` | 不導入 manifest |
| **P77.2** | report health / landing link 修復 | `reporter/generator.py`, `scripts/check_daily_report_health.py`, `index.html`, `tests/...` | 不重做前端 |
| **P77.3** | repo-state smoke test | `tests/...`, `scripts/...` | 不改 CI promotion gate |

---

## 6. 17 層稽核表

### S 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 精修 history/fallback/health，不做 unrelated refactor | 小修擴散 | 子階段 Allowed Files 限制 |
| **2. 邏輯層 (Logic)** | 區分 empty / external failure / programmer error | fallback 繼續誤導 | fail loud + degraded reason |
| **4. 測試層 (Testing)** | regression + repo-state smoke | 測試仍只綠單元不抓發布 | 增加實際 repo health 檢查 |
| **10. 安全層 (Security)** | 不新增外部執行；HTML 內容不在本 Phase 大改 | XSS 另屬 P83 | P77 不引入新 raw injection |

### A 級層

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層** | 不重做架構，只修主鏈路 | 架構債留到 P78 | 總計畫已列 P78-P80 |
| **5. 資料層** | history archives 來源正確化 | analysis/raw 持久化仍缺 | P78/P83 處理 |
| **6. 可觀察性層** | fallback reason / health output | 錯誤被吞 | 分級輸出 |
| **7. 韌性層** | 壞 archive 跳過，程式錯誤不假正常 | 報告生成更容易 fail | 只讓 programmer error fail loud |
| **13. 可維護性層** | 小步測試命名清楚 | 分散規則難懂 | P79 doctor / P84 runbook 後續 |
| **14. 文件層** | P77 收官回寫 handoff / history | 文檔漂移 | active bootstrap 更新 |
| **15. 流程層** | 先 P77 止血，再 P78 合約 | 跳 Phase | P76.1 handoff 仲裁 |

### B 級層

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **8. 效能層** | report/history 掃描限 canonical pattern | reports 多時慢 | 只掃必要日期 |
| **9. UX/A11y 層** | 首頁連到正確 report | 使用者看舊資料 | health gate |
| **11. 部署層** | P77 只做本地 health，CI gate 後續 | GHA 仍可能壞 | P79/P80 接手 |
| **12. 成本層** | 不增加 LLM call | 無 | 無 |
| **16. 隱私/合規層** | 不 commit raw 原文 | analysis policy 後續 | P78/P83 |
| **17. i18n/在地化層** | 保持 UTF-8 / 繁中輸出 | Windows cp950 | 跑 Python 前設 UTF-8 |

---

## 7. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 |
|---|---|
| 修 history runtime | 可逆 |
| 修改 fallback 分級 | 半可逆 |
| 更新 index/report health | 可逆 |
| 更新 TASK_HISTORY / handoff | 半可逆 |

### X2 盲區掃描

- P77 不會解決 GHA fresh checkout 缺 analysis/raw 的完整資料持久化問題；P78/P83 處理。
- P77 不會建立 manifest/schema；避免第一波混入新架構。
- P77 不保證今日外部 API 一定成功，只保證錯誤不被假正常掩護。

### X3 時間敏感性

- 本計畫日期：2026-05-16。
- daily report date 預設以 Asia/Taipei 理解；正式 timezone contract 到 P82。

### X4 多角度同行審查

- **主公視角**：最重要是報告可信，不要漂亮但假的趨勢。
- **世界頂尖駭客 / 紅隊攻擊者視角**：P77 不新增外部 attack surface；需注意 HTML 顯示資料後續 P83 補。
- **接手者視角**：子階段與 Allowed Files 要清楚，避免一口氣大改。
- **維運者視角**：health output 要能指出 stale / missing / preview，而非只給 fail。
- **X4-K 使用者端審查官**：首頁指到舊報告是使用者可見 bug，P77 必須處理。

---

## 8. 風險清單

| 風險 | 機率 | 影響 | 緩解 |
|---|---:|---:|---|
| 修 history 後發現 archives 本來就缺 | 高 | 中 | P77 標 degraded，P78 解資料保存 |
| fallback 變嚴導致報告生成失敗 | 中 | 高 | 區分 programmer error 與 external failure |
| 更新 index 可能選到 preview | 中 | 高 | latest qualified production report 規則 |
| repo-state smoke 在本地與 CI 結果不同 | 中 | 中 | P79/P80 統一 doctor/CI |

---

## 9. 工作階段

| Stage | 工作 | 驗收 |
|---|---|---|
| S0 | Baseline 重現與測試 | 記錄 pytest / health 現況 |
| S1 | P77.0 history runtime 修復 | regression tests |
| S2 | P77.1 fallback 分級 | degraded reason 可觀察 |
| S3 | P77.2 landing/report health | health check 通過 |
| S4 | P77.3 repo-state smoke | 測試能抓實際發布壞狀態 |
| S5 | 收官 | docs / handoff / history 更新 |

---

## 10. 影響檔案清單

| 檔案 / 目錄 | 預計動作 |
|---|---|
| `analyzer/history.py` | 修 `archives` 初始化與錯誤處理 |
| `main.py` | fallback 分級 |
| `reporter/generator.py` | latest qualified report / landing update |
| `scripts/check_daily_report_health.py` | health 分類增強 |
| `tests/` | regression + repo-state smoke |
| `index.html` | 指向合格 production report |
| `NEXT_SESSION_HANDOFF.md` | 更新 active bootstrap |
| `TASK_HISTORY.md` | append 收官紀錄 |

---

## 11. Postmortem 預埋點

- 為什麼原本 126 tests passed 沒抓到 `HistoryResolver` NameError？
- 為什麼 P70.2 health checker 已存在，但 index 仍 stale？
- fallback 哪些情況應允許 degraded，哪些應阻擋？
- P78 是否需要優先處理 analysis/raw 持久化？

---

## Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 攻擊者視角** | P77 會觸及資料到 HTML 的主鏈路，必須避免假資料與未 escape 內容造成安全或信任問題。 |
| **X4-B 接手者視角** | 接手者需要按 P77.0 到 P77.3 順序小步修，不可把 P78 manifest 混進止血。 |
| **X4-C 災難情境** | 若只修一行 `archives` 卻保留靜默 fallback，報告仍可能漂亮但不可信。 |
| **X4-D 5 年後視角** | 未來維護者應能從 tests 與 health checker 看到為何 programmer error 不可 fallback。 |
| **X4-E 終端 vs IDE** | Windows 終端需先設 UTF-8 再跑 Python；IDE 修改也要用同一套 pytest/health 驗證。 |
| **X4-F 跨平台** | P77 主要 Python 與 Markdown 變更需在本機與 GitHub Actions 都能用相同命令驗證。 |
| **X4-G 主公個人視角** | 主公最在意長期可信，P77 必須先讓錯誤會叫，不再用假趨勢掩護。 |
| **X4-H 觀測** | report health 要能指出 stale landing、missing report、preview report，而不是只回傳失敗。 |
| **X4-I 主公可見性** | 主公看不到 fallback 內部原因，所以 degraded reason 必須進 log 或 metadata。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 修 `HistoryResolver` 後可能發現根本沒有可用 archives，報告仍缺歷史。 | **S** | 0 | P77 先明示 degraded，P78 再處理 manifest/history source persistence。 | 入計畫範圍 |
| 2 | fallback 變嚴後 daily report 可能更常失敗。 | **S** | 0 | 只讓 programmer error fail loud，external failure 可 degraded 並標 reason。 | 入計畫範圍 |
| 3 | 更新 landing 規則可能誤選 preview report。 | **S** | 0 | latest qualified production report 需檢查 metadata，不只看檔名日期。 | 入計畫範圍 |
| 4 | repo-state smoke test 可能在開發機與 CI 看到不同結果。 | A | 0 | P77 先補本地可見盲區，P79/P80 再統一本地與 CI doctor。 | 入計畫範圍 |
| 5 | 只做 P77 不會根治資料保存與 replay。 | A | 0 | P77 明確只止血，P78-P84 總計畫承接長期治理。 | 入計畫範圍 |
| 6 | P77 同時碰 history、fallback、landing，仍可能範圍太大。 | A | 0 | 拆 P77.0-P77.3，每次只處理一類根因並跑對應驗證。 | 入計畫範圍 |

---

## 12. 凍結戳記

- **狀態**：CLOSED（external dependency blocked）
- **主公核准動工前不可修改 runtime**：已解除（2026-05-16 已核准）
- **下一步**：已轉交 P78（manifest）與 P81（replay/backfill）持續治理。
