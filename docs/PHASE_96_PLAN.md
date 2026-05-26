# Phase P96 計畫書 — Website Content Trust（RUNTIME VERIFIED）

> 狀態：RUNTIME VERIFIED，主公已於 2026-05-26 核准 `P96 plan freeze` 與 `P96 runtime 動工`。本 Phase 建立「網站內容可信度」修復計畫，針對主公回報的「芽芽觀察室變成圖倫觀察室」與「很多文章是舊文章」設計根因追查、測試護欄與收官驗證。2026-05-26 cloud commit `0618717` 已通過 content trust checker；R-017 是否降級為 monitoring 仍待主公裁決。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P96 |
| **Phase 名稱** | Website Content Trust Plan |
| **凍結日期** | 2026-05-26（主公核准 P96 plan freeze） |
| **影響半徑** | 標準 (預估 runtime 3-9 檔) |
| **預估投入時數** | plan 0.8h；runtime 2.5-4h |
| **Token budget** | plan 20K；runtime 50K |
| **負責模型** | GPT-5.3-Codex（repo 動工 / 測試）；若根因跨模板與資料流卡住，升 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| R-017 Website Content Trust | New | Open | 前台內容正確性風險已建帳 | 主公回報頁面標題錯置與舊文章問題 | AI 建帳，主公核准 Phase |
| P96 plan | FROZEN | PASSED | 計畫已建立並凍結，但不可動 runtime | 主公下令「開 P96 plan」與「核准 P96 plan freeze」 | AI 執行 |
| P96.0 Evidence Inventory | NOT_STARTED | REQUIRED_BEFORE_RUNTIME | runtime 前必讀完整關聯鏈並留下 evidence matrix | 主公要求最保守品質最高做法 | AI 執行，主公審核 |
| Known Issue Memory / Regression Guard | New | PLANNED | 把復發型錯誤寫成機器可檢查規則與測試 | P96.0 找到根因與最小可測 contract | AI 實作，主公核准 runtime |
| P96 runtime | IN_PROGRESS | VERIFIED | P96.0 Evidence Inventory 已完成；minimal fix / guard 已落地；cloud commit `0618717` 通過 checker | 主公回覆「核准 P96 runtime 動工」後進入；手動 dispatch AoV Daily Monitor 完成 | 主公 / AI |

---

## 1. 目標 (Objective)

建立一套可驗證的內容可信度修復路線，讓最新 production 報告必須同時滿足：焦點英雄標題與 `config.HERO_FOCUS_NAME` 一致、Top-5 / 芽芽觀察室文章不被過期舊文污染、曾復發的錯標問題有自動測試或 checker 擋住。

## 2. 觸發背景 (Why Now)

R-016 後端可靠性已降級為 monitoring，但主公實際看站時仍發現前台內容問題：`芽芽觀察室` 曾多次莫名變成 `圖倫觀察室`，且頁面中有很多舊文章。這屬於 Website Content Trust，不是 Daily Monitor 是否成功、SLO 是否綠燈的問題；若不另開 R-017/P96，會讓後端可靠性收尾與前台內容修復互相打架。

## 2.5 問題切分與方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 只把當前 HTML 改回芽芽 | 快速替換輸出字串 | 立刻看起來正常 | 不知道根因，下次 Daily Monitor 可能又覆蓋 | 不採用 |
| B. 建內容契約 + 根因追查 + 測試護欄 | 先定義 hero/title/freshness contract，再補 checker/tests | 可防復發，能分辨模板、資料、快取、picker 問題 | 比單點 patch 多一個 phase | **採用** |
| C. 重做整個報告生成器 | 大幅整理 reporter/analyzer | 可能順便清掉技債 | 爆 scope，會污染 R-016 monitoring | 不採用 |
| D. 先做 P96.0 Evidence Inventory，再 freeze runtime | runtime 前補讀完整關聯鏈與可重現 evidence | 最保守，降低誤修與漏讀 | 多一道 plan 補強與檢查 | **採用** |

## 2.6 最保守品質門檻（P96.0）

P96 runtime 前必須先完成 Evidence Inventory，不得直接動 code。Inventory 的讀檔範圍不是「全 repo / 全歷史」，而是完整關聯鏈：

| 關聯鏈 | 必讀目標 | 要回答的問題 |
|---|---|---|
| Config | `config.py` / env defaults | `HERO_FOCUS_NAME` 與 `HERO_WATCHLIST` 在本地、CI、report 生成時是否一致 |
| Raw-to-analysis | scraper result schema、`analyzer/sentiment.py`、`analyzer/local_analyzer.py` | `hero_focus.name` 與 detected heroes 是誰產生，是否可能被 LLM 寫錯 |
| Selection | `analyzer/top5_picker.py`、`analyzer/news_history_indexer.py` | 舊文、重複文、無日期文如何計分，芽芽 bonus 是否會保留舊文 |
| Report assembly | `reporter/generator.py` | `hero_focus`、`hero_focus_posts`、Top-5、landing history 如何組合 |
| Template output | `reporter/templates/report.html` | 哪些文字硬編碼芽芽，哪些文字吃 `hero_focus.name`，是否互相矛盾 |
| Evidence | latest production report / manifest / optional artifact | 現在最新頁面是否有錯標、舊文、unknown date、重複污染 |
| Existing tests | Top-5 / generator / health tests | 哪些已有測試可延伸，哪些缺口要補 |

P96.0 的輸出必須是 raw-free evidence matrix，不貼原始貼文全文，只記 title/url/date/count/source file/判定理由。

## 2.7 Known Issue Memory / Regression Guard

主公問「是不是要做一個犯錯能夠記得錯在哪並且解決的程式？」答案是：**要做，但不是靠 AI 腦袋記憶，而是靠專案內的機器可檢查記憶。**

P96 runtime 會把復發型問題拆成三層：

| 層 | 形式 | 用途 |
|---|---|---|
| 人類記憶 | `docs/CONTENT_TRUST_KNOWN_ISSUES.md` 或 R-017 條目 | 記錄錯誤現象、根因、修法、復發條件 |
| 機器記憶 | `configs/content_trust_known_issues.yaml` 或等價 JSON/YAML | 保存 known issue pattern、期望 hero、禁用錯名、freshness threshold |
| 執行記憶 | `scripts/check_report_content_trust.py` + tests | 每次檢查 latest report 時，自動抓「以前犯過的錯」 |

這個程式不會神奇地自己理解所有新錯誤；它會做到兩件保守且可靠的事：
- 已知錯誤：下一次能自動擋住或至少明確告警。
- 新錯誤：收官時必須把新錯誤加入 known issue registry 與 regression test，讓它從「人腦記得」變成「repo 記得」。

## 2.7.1 自我優化飛輪落地規格

P96 不承諾「一次消滅所有未知內容錯誤」；P96 要建立的是可重跑、可交接、可升級的內容可信度飛輪。每個已修復的內容錯誤，至少要留下以下四種落點，避免同類問題下一次只靠對話記憶或人眼辨識。

| 落點 | P96 最小落地 | 驗收訊號 |
|---|---|---|
| 人看得懂 | `docs/CONTENT_TRUST_KNOWN_ISSUES.md` 或 P96 closeout section | 有 issue id、症狀、根因層、修法、復發訊號 |
| 機器讀得懂 | `configs/content_trust_known_issues.yaml` 或等價 JSON/YAML | 有 expected focus hero、forbidden title pattern、freshness threshold、severity/action |
| 程式跑得動 | `scripts/check_report_content_trust.py` + focused tests | fixture 可重現 `wrong_focus_hero_title` / `stale_article_pollution` |
| 線上看得到 | report manifest / content trust snapshot / Daily Monitor artifact | latest report 的 content trust status、reason、offenders 可追溯 |

飛輪閉環：

| 步驟 | 動作 | 停損點 |
|---|---|---|
| Detect | checker / evidence matrix 抓出症狀，不輸出 raw 全文 | 能指出錯在哪個 report / block / field 即停 |
| Diagnose | 判斷根因層：資料、分析、選文、生成、模板、部署或治理 | 不跨層猜修，沒有 evidence 不動 runtime |
| Record | 把錯誤寫成 known issue 條目 | 至少有 issue id、復發條件與預期行為 |
| Codify | 把條目轉成機器規則或 regression test | 至少一個可重跑驗證落地 |
| Verify | 先證明錯誤會被抓到，再證明修法後通過 | 不能只改測試讓它綠 |
| Observe | 檢 latest local / production report 與 artifact | 若雲端與本地不同步，先列為 deployment evidence gap |
| Promote | shadow advisory 穩定後，才評估 strict gate | 未經穩定窗口，不阻斷 Daily Monitor |

P96 的「自我修復」定義是：系統能自動偵測、記錄、驗證並阻止已知錯誤復發；不是讓程式自行改 production code，也不是新增泛用 AI 自動修 code 代理。若 runtime 發現需要更大規模的自動修復系統，必須另開 P97+，不能塞進 P96。

## 2.8 跨層級歸屬與邊際效益優化

本問題不歸類為單純前端或單純後端；它是 **Content Trust / Report Contract** 橫切面問題。

| 層級 | 這裡負責什麼 | 最小高效修法 | 不採用的低效修法 |
|---|---|---|---|
| 資料層 | 文章 title / url / published_date / timestamp 的真實性 | 日期缺失與過舊文章先標記，再決定降權或排除 | 看到舊文就手動刪 HTML |
| 分析層 | `hero_focus.name`、detected heroes、summary 是否可信 | 以 `config.HERO_FOCUS_NAME` 作焦點英雄權威，LLM 只能補摘要不能改焦點身份 | 讓 LLM 自由決定觀察室名稱 |
| 選文層 | Top-5 / hero focus posts 是否新鮮且不重複污染 | freshness / duplicate / unknown-date guard | 只調高或調低單一分數常數 |
| 報告生成層 | 把資料轉成 template variables | 在 generator 邊界做 contract assert / diagnostics | 把所有判斷塞進 HTML template |
| 前端模板層 | 正確呈現標題、日期、連結與提示 | template 只呈現已驗證內容，必要時顯示 unknown/stale badge | 在 template 裡猜資料真相 |
| 治理層 | 曾犯錯誤如何被記住 | known issue registry + checker + regression tests | 只寫在對話記憶裡 |

邊際效益最高的順序：

1. **先加 checker / evidence matrix**：成本低，不改 runtime，馬上知道問題在哪層。
2. **再加 known issue memory**：把「圖倫觀察室」「舊文章污染」變成可重跑規則。
3. **只在根因層小修**：若錯在 generator，就不動 scraper；若錯在 picker，就不動 template。
4. **最後才接 CI / Daily Monitor gate**：等本地 checker 穩定後，再決定是否升成雲端 gate，避免誤擋每日報告。

P96 runtime 的最佳化目標不是「每層都改」，而是「每層只放最便宜、最能防復發的 guard」。這樣能最大化品質收益，同時降低誤修與維護成本。

## 2.9 邊際效益前緣（Layer × Viewpoint Frontier）

主公要求「直接把各層級各視角優化至邊際效益」。P96 runtime 採用以下前緣規則：每個候選改動都必須說清楚 **收益、成本、風險、停損點**；沒有跨過邊際效益門檻，不准進 runtime。

邊際效益門檻：
- **必做**：低成本、低 blast radius、可防高影響復發，例如 checker / tests / manifest advisory。
- **延後**：高成本但收益尚未被 evidence 證明，例如重寫 picker 或改 CI strict gate。
- **拒絕**：只改善表面、不能防復發，例如手修單份 HTML、硬塞 hero 名稱到 template 卻不修資料契約。

| 層級 | 最高邊際效益動作 | 何時停止 | 主視角 | 驗收訊號 |
|---|---|---|---|---|
| 資料層 | 統一 article freshness 欄位與 unknown-date 診斷 | 能列出 stale/unknown offenders 即停，不重建資料模型 | Marcus / Patric | checker 能輸出日期來源與 stale count |
| 分析層 | `hero_focus.name` 以 config 為權威，LLM 只補摘要 | 能擋錯英雄名即停，不重寫 prompt 大系統 | Ken / Jarvis | 非焦點英雄觀察室會 fail |
| 選文層 | stale/duplicate/unknown-date guard 先 shadow | 能解釋入選理由即停，不先改 scoring 常數 | Marcus / Penny | Top-5 每張卡有 freshness reason |
| 生成層 | render 前做 content contract snapshot | manifest/report metadata 有 `content_trust` 即停 | Jason / Jimmy | `content_trust.status` 可追溯 |
| 模板層 | 只顯示已驗證欄位與 stale/unknown badge | 不在 template 內做資料推理 | Oliver / Patric | 人眼看到的標題與日期不誤導 |
| 治理層 | known issue registry + regression tests | 能把新錯轉成規則即停，不做泛用 AI 記憶系統 | Jimmy / Jarvis | 新錯誤有 issue id、fixture、test |
| 部署層 | 先 advisory，連續穩定後才 strict gate | shadow 期未滿不阻斷 Daily Monitor | Jason / Penny | 連續 N 次 pass 再提 gate |

各視角最優解不是加更多功能，而是各自把最小閉環補齊：

| 視角 | 最有價值的問題 | P96 對應最佳化 |
|---|---|---|
| 主公 / 使用者 | 我看到的頁面能不能信？ | latest report 必有 content trust 狀態與可讀原因 |
| 接手者 | 下次換窗會不會忘記？ | known issue 文件 + 機器規則 + tests |
| 紅隊 / 技術長 | 會不會外洩 raw 或被 URL/HTML 注入？ | raw-free evidence、safe URL、HTML checker |
| 數據分析師 | 舊文判定有沒有證據？ | freshness reason、unknown date 不默認 fresh |
| 設計審查 | 修內容會不會破壞畫面？ | template 只加必要 badge，不重排整頁 |
| DevOps | 會不會誤擋每日報告？ | advisory shadow 先行，strict gate 後置 |
| CFO / 成本 | 會不會多燒 LLM/API？ | 優先本地 deterministic checker，不靠重跑 LLM |

P96 freeze 前的品質線：先把「最便宜但可防復發」的設計凍住；runtime 再依 P96.0 evidence 決定哪些層真的需要改。這能把邊際收益推到高點，同時避免把 P96 膨脹成重構案。

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] R-016 已降級為 monitoring，可靠性主線不再阻擋 P96 plan。
- [x] 主公已明確下令「開 P96 plan」。
- [x] 已讀 handoff / active / phase template / R-016 risk registry。
- [x] 主公已核准 `P96 plan freeze`；runtime 仍需另行核准。
- [x] 主公已核准 `P96 runtime 動工`。
- [x] runtime 前完成 P96.0 Evidence Inventory，並把 evidence matrix 寫入 `docs/PHASE_96_EVIDENCE_INVENTORY.md`。
- [x] runtime 前先確認最新 production report、manifest、`config.HERO_FOCUS_NAME` 與可重現樣本。

## 4. Exit Criteria（退出條件）

P96 plan freeze 退出條件：
- [x] `docs/PHASE_96_PLAN.md` 通過 `scripts/lint_phase_plan.py`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 P96 plan。
- [x] `docs/RISK_REGISTRY.md` 建立 R-017 Open 風險。
- [x] `TASK_HISTORY.md` 追加 P96 plan 物理真相。

P96 runtime 收官退出條件：
- [x] 新增或更新內容可信度 checker / tests，可檢出焦點英雄錯標。
- [x] 新增或更新 stale article guard，可檢出 Top-5 / hero focus article 過舊或重複污染。
- [x] 新增 known issue memory：可讀文件 + 機器可讀規則 + regression test 三者至少兩者落地；若暫緩，需主公明文豁免。
- [x] 自我優化飛輪至少對 `wrong_focus_hero_title` 與 `stale_article_pollution` 建立 issue id、可讀紀錄、機器規則或測試、驗證輸出。
- [x] 最新 production report 檢查：標題為芽芽觀察室，且未出現圖倫觀察室。
- [x] report 文章清單可解釋其日期來源；無日期時不可默默當新文。
- [x] focused tests 通過；若動到 report generator / picker，至少跑相關 tests。
- [x] 若需要雲端確認，手動 dispatch AoV Daily Monitor 後讀 artifact/report。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 2.5-4h |
| 預估收益等級 | 高 |
| 收益描述 | 修掉主公肉眼可見的錯標與舊文問題，並把復發型錯誤變成可測、可查、可交接 |
| ROI 結論 | ✅ 值得做；這是使用者信任層，不處理會讓 production 綠燈失去意義 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | runtime 僅允許小範圍改 checker / reporter / picker / tests | 借 P96 大重構報告生成器 | 每一行需追到錯標、舊文、known issue guard |
| **2. 邏輯層 (Logic)** | 建立 hero/title/freshness contract | 只看 HTML 字串，漏掉資料流根因 | 同時檢查 config、summary.hero_focus、template、Top-5 picker |
| **4. 測試層 (Testing)** | 新增 focused regression tests 與 known issue guard | 修到目前樣本但下次復發 | 測「圖倫錯標不得出現」「舊文章需被標記/降權/排除」；新錯誤必入 registry/test |
| **10. 安全層 (Security)** | 不新增 secrets、不接 provider、不抓 raw 私密資料進 repo | 為查內容把 raw artifact 或 token commit | raw / artifact 只放 git-ignored scratch；輸出只記 raw-free evidence |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | 不重建架構；在現有 reporter/analyzer 邊界加 contract | checker 散落成一次性腳本 | 若新增 checker，放 `scripts/` 並配 tests |
| **5. 資料層 (Data)** | 明確區分 `published_date`、`timestamp`、report date、first_seen | 無日期文章被當成新文 | 無日期進 degraded/unknown，不默默視為 fresh |
| **6. 可觀察性層 (Observability)** | report / manifest / checker 輸出內容健康狀態 | 使用者只看到錯，不知道哪層壞 | checker 印 hero、date、stale counts、offender titles |
| **7. 韌性層 (Resilience)** | checker fail 時阻止錯誤結論，不硬說修完 | Daily report 成功但內容錯 | P96 收官需本地與必要雲端雙證據 |
| **13. 可維護性層 (Maintainability)** | known issue guard 條文化 + 機器可讀記憶 | 下次 AI 忘記舊解法 | regression test 名稱與 R-017 風險對齊；known issue registry 保存錯誤/根因/修法 |
| **14. 文件層 (Documentation)** | plan / active / handoff / risk / history 同步 | 下一窗誤把 P96 當 runtime 已核准 | Mode 保持 FROZEN，runtime 需另行核准 |
| **15. 流程層 (Process)** | Plan -> freeze -> runtime -> verify -> closeout | 前端內容修復插隊 R-016 monitoring | R-016 只監控；P96 只處理內容可信度 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | 可能掃 HTML / reports / manifest | checker 掃描限制 latest 與小窗口 | 掃全 `data/reports` 太慢且混入舊 preview | 預設 latest canonical；歷史掃描需明確 window |
| **9. UX/A11y 層** | 涉及前台文字 | 不改視覺前先保內容正確 | 為修內容破壞排版 | runtime 若動 template，需 browser/HTML sniff |
| **11. 部署層 (DevOps)** | Daily Monitor 會覆蓋 report | 必要時雲端 dispatch 驗證 | 本地修好但雲端又覆蓋 | 收官可要求 latest Actions evidence |
| **12. 成本層 (Cost)** | 可能重跑 Daily Monitor / LLM | 不新增 LLM calls 作為預設修復手段 | 為查內容燒 provider budget | 優先 local checker / existing artifact |
| **16. 隱私/合規層 (Privacy)** | 第三方社群資料 | 文件只記 raw-free offender metadata | 把原始貼文全文寫進 history | 只記 title/url/date/count，必要 raw 留 scratch |
| **17. i18n/在地化層** | 中文英雄名與台服語境 | 以 `HERO_FOCUS_NAME` 作權威 | 圖倫/芽芽等英雄名被 LLM 自由改寫 | hero title contract 禁止非 configured focus |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：P96 runtime 必含 regression tests。
- [x] 動 Architecture 層 -> 已動 Documentation 層：本 plan 同步 governance docs。
- [x] 動 Data 層 -> 已動 Maintainability 層：freshness contract 寫成可維護 guard。
- [x] 動 Security 層 -> 已動 Testing 層：raw-free / URL safety 沿用既有 tests。
- [x] 動 Performance 層 -> 已動 Observability 層：checker output 限 window 並輸出 offenders。

---

## 7. 跨切面檢查

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 建立 P96 plan 文件 | 可逆 | 本次主公已要求開 plan |
| 更新 handoff / active / risk / history | 可逆 | 本次同步 plan 狀態 |
| P96 runtime 改 checker/tests | 可逆 | 需 freeze 後另核准 |
| P96 runtime 改 report generator / template | 半可逆 | 需主公核准 runtime |
| 手動 dispatch Daily Monitor | 半可逆 | 若需要雲端驗證再請示 |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] `news_history_index.json` 會影響舊文判定，且可能不進 git。
- [x] `published_date` / `timestamp` 格式不一致會讓舊文被當成新文。
- [x] template 有硬編碼芽芽文字，也有 `hero_focus.name` 動態文字，兩者可能互相矛盾。
- [x] LLM summary 可能把焦點英雄名稱寫錯，但 template 仍照渲染。
- [x] AI 換視窗後不會自帶完整個人記憶；必須把錯誤寫進 repo 文件、規則與測試。

### X3 時間敏感性 (Time Decay)

- 本計畫建立日期：2026-05-26。
- 本計畫過期日期：2026-06-02；若一週內未進 runtime，需重新讀 latest report。
- R-016 monitoring window：2026-05-25～2026-06-01；P96 不改 R-016 狀態。
- 風險記錄帶日期：✅。

### X4 多角度同行審查

- **主公視角**：主公要的是網站不要再胡說；P96 會用白話把錯標、舊文、復發防線拆開，不要求主公分辨前後端。
- **世界頂尖駭客 / 紅隊攻擊者視角**：本 Phase 主要攻擊面是 HTML 注入、URL scheme、raw artifact 外洩與 CI 產物污染；沿用 safe URL，新增 checker 不輸出 raw 全文。
- **接手者視角**：接手者要能從 R-017/P96 看懂「為何 R-016 綠燈但網站還錯」，以及哪些 tests 專門防復發。
- **X4-J 自動化建議性工具邊界**：freshness / hero contract checker 若採字串比對，只能作 deterministic guard；召回率非 100%，仍需主公抽看 latest report。
- **X4-K 使用者端審查官 / Patric 型人格**：頁面標題錯一次就會讓使用者懷疑整站，P96 收官需把「看起來正常」提升為「有證據正常」。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 只修 HTML 現象，Daily Monitor 下一跑又覆蓋 | 中 | 高 | 流程 | 不採單點替換，先建 contract/test |
| R2 | LLM summary 把焦點英雄名寫錯，template 照單全收 | 中 | 高 | 邏輯 | hero/title contract 以 config 為權威 |
| R3 | 舊文因 `published_date` 缺失而拿到高分 | 高 | 高 | 資料 | 無日期不得默認 fresh，需 unknown/degraded |
| R4 | news history index 本地/雲端狀態不同，造成重複或舊文判定飄 | 中 | 中 | 環境 | 收官記錄 index 狀態與可重現 fixture |
| R5 | P96 修前台時誤動 R-016 monitoring / provider / workflow | 低 | 高 | 流程 | Forbidden Work 明列，不改 workflow/provider |
| R6 | RTK 評估插隊造成 terminal 行為變因 | 低 | 中 | 工具 | RTK 保持排程，不進 P96 runtime |
| R7 | known issue memory 只寫文件、沒有可執行檢查 | 中 | 高 | 可維護性 | runtime exit criteria 要求文件/機器規則/checker/tests 至少兩層落地 |

**高風險加權檢查（META4）**：
- 高風險數量：4 項。
- 加權分數：8 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；本 plan 只凍結方案，runtime 需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 P96.0 Evidence Inventory** | 補讀完整關聯鏈，建立 raw-free evidence matrix | 避免漏讀與誤修 | matrix 有 config/report/manifest/template/picker/test evidence |
| **S1 Content Contract Design** | 定義 hero title、focus block、Top-5 freshness、date unknown 規則 | 讓錯誤可測 | contract 條文進 plan/runtime docs |
| **S2 Known Issue Memory Design** | 建 known issue 文件/機器規則/checker schema | 讓錯誤可被 repo 記住 | 至少列 `wrong_focus_hero_title`、`stale_article_pollution`，並有 issue id / recurrence signal |
| **S3 Regression Tests / Checker** | 新增 focused tests 或 `scripts/check_report_content_trust.py` | 防復發 | 測錯標與舊文 fixture，並能留下 fail-before / pass-after evidence |
| **S4 Minimal Runtime Fix** | 依根因小改 reporter/top5/template/local analyzer | 修真根因 | focused tests pass |
| **S5 Latest Report Verification** | 本地生成或檢查 latest production；必要時手動 dispatch | 防雲端覆蓋 | latest report 無圖倫錯標、stale offenders 合理 |
| **S6 Closeout Docs** | 更新 handoff/active/risk/history | 防下一窗漂移 | governance checks pass |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_96_PLAN.md`
- runtime 可能新增 `scripts/check_report_content_trust.py`
- runtime 可能新增 `tests/test_report_content_trust.py`
- runtime 可能新增 `docs/CONTENT_TRUST_KNOWN_ISSUES.md`
- runtime 可能新增 `configs/content_trust_known_issues.yaml`

**修改**：
- `NEXT_SESSION_HANDOFF.md`：指向 P96 plan。
- `docs/ACTIVE_OPERATION.md`：指向 P96 plan。
- `docs/RISK_REGISTRY.md`：新增 R-017 Open。
- `TASK_HISTORY.md`：追加 P96 plan 紀錄。
- runtime 可能修改 `reporter/generator.py`、`reporter/templates/report.html`、`analyzer/top5_picker.py`、`analyzer/news_history_indexer.py`。

**刪除**：
- 無。

**影響但未直接修改**：
- `data/reports/aov_report_*.html`
- `data/runs/*/run_manifest.json`
- `data/news_history_index.json`
- GitHub Actions AoV Daily Monitor。

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 主公再度看到 `芽芽觀察室` 變其他英雄。
- [ ] runtime 後 Daily Monitor 覆蓋出錯報告。
- [ ] checker 通過但人工看到舊文章污染。
- [ ] 發生「我以為 HTML 正常就代表資料正常」事件。
- [ ] 已知錯誤復發但 known issue guard 沒擋住。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-96-content-trust.md`

---

## 12. Forbidden Work（P96 邊界）

- 不把 R-016 monitoring 改成 Closed 或 active，除非 monitoring 觸發條件命中。
- 不新增 provider key / PAT / Cloudflare token / Groq key。
- 不加 GitHub Actions `models: read`。
- 不接 Groq / Cloudflare / GitHub Models 到 daily default。
- 不安裝或全域部署 RTK；RTK 另開 Program。
- 不全讀 `TASK_HISTORY.md`。
- 不 stage unrelated untracked reports / scratch / skills 暫存目錄。
- 不用手改 production HTML 當作唯一修復。

---

## 13. Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 攻擊面是內容來源與 HTML 輸出：惡意 URL、錯誤 hero name、raw artifact 外洩、CI 產物覆蓋。最小緩解是 safe URL、raw-free logs、deterministic checker。 |
| **X4-B 接手者** | 接手者需要知道 R-016 已是 reliability monitoring，P96 是 content trust，不能拿 SLO 綠燈證明頁面內容正確。 |
| **X4-C 災難情境** | 情境：Daily Monitor 成功但再次發布圖倫觀察室。緩解：checker 在收官前檢 latest report，必要時接入 CI gate。 |
| **X4-D 5 年後** | 五年後英雄焦點可能不是芽芽，因此規則必須讀 `HERO_FOCUS_NAME`，不要把芽芽硬編成唯一真理。 |
| **X4-E 終端 vs IDE** | 終端要看到 PASS/FAIL/offender titles；IDE 讀 plan 要知道會動哪些檔案與何時需主公核准。 |
| **X4-F 跨平台 Win/Mac/Linux** | checker 應使用 Python pathlib 與 UTF-8，避免 Windows cp950 中文輸出崩潰；測試需設 UTF-8。 |
| **X4-G 主公個人視角** | 主公不需要判斷前端/後端/治理打架；P96 會明白說這是網站內容可信度，RTK 與 R-016 都不插隊。 |
| **X4-H 觀測 / 治理** | 目前 health/SLO 看 pipeline，不看 hero title/freshness；P96 要補內容觀測，不再讓綠燈掩蓋錯文。 |
| **X4-I 主公可見性** | 主公看不到 news_history_index、published_date 缺失與 LLM summary hero name；收官需把這些用表格攤開。 |
| **X4-J 自動化建議性工具邊界** | 若 checker 用字串比對圖倫/芽芽，只能抓已知錯誤；未知錯名仍需抽看與後續規則擴充。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者看到錯英雄或舊文章會直接失去信任；修復不能只追求程式綠燈，要追求頁面語意可信。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P96 只做 content trust，runtime 需另核准。 |
| **Ken 型紅隊 / 技術長** | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD、不可逆操作 | 觸發；不新增 secrets、不改 workflow、不輸出 raw 全文。 |
| **Patric 型使用者端審查官** | 固定必看 | 主公 / 使用者 / 接手者是否會誤解、卡住、走到死路 | 觸發；頁面內容錯比後端告警更傷信任。 |
| **Jimmy 型文件主筆** | 改 docs / TASK_HISTORY / handoff / 對外文字 / template 時觸發 | 文字是否可追溯、有來源、避免空泛敘事 | 觸發；history 要記物理真相，不寫空泛「優化內容」。 |
| **Marcus 型數據分析師** | 涉及數據、趨勢、判斷依據、實驗結果時觸發 | 沒數據時是否明說；定量 / 定性是否分清楚 | 觸發；舊文判定需列日期來源與 unknown count。 |
| **Oliver 型設計審查** | 涉及 UI、報告、圖表、視覺呈現時觸發 | 視覺層級、可讀性、A11y、資訊密度是否合適 | 觸發；若動 template，需確認文字不重疊且不破壞觀察室區塊。 |
| **Penny 型 CFO** | 涉及 API 成本、雲端成本、排程成本、付費工具時觸發 | ROI、預算上限、成本爆量與停損條件 | 觸發；P96 預設 local checker，不用額外 LLM 成本。 |
| **Jason 型執行 / DevOps** | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell / 跨平台細節 | 觸發；若接 CI gate 需小心不阻斷既有 Daily Monitor。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 只檢查 `圖倫觀察室` 字串，其他錯英雄仍漏掉。 | S 級 | 0 | checker 應檢 `hero_focus.name == HERO_FOCUS_NAME`，不是只列黑名單。 | 入計畫範圍 |
| 2 | 舊文可能沒有日期，測不到 age，仍會混入。 | S 級 | 0 | 無日期不得默認 fresh；需列 unknown date offenders。 | 入計畫範圍 |
| 3 | 本地 report 正常，GitHub Actions 又用不同 env 覆蓋。 | A 級 | 0 | 收官時視情況手動 dispatch，讀 latest production artifact/report。 | 入計畫範圍 |
| 4 | news_history_index 是本地狀態，測試 fixture 與真實 index 不一致。 | A 級 | 0 | focused tests 注入 fixture；真實驗證讀現有 index snapshot。 | 入計畫範圍 |
| 5 | 修 Top-5 舊文會降低芽芽文章數，主公以為變少是壞了。 | B 級 | 0 | 收官報告需說明新鮮度規則與 unknown/stale 被排除原因。 | 入計畫範圍 |
| 6 | RTK 若插隊安裝，terminal 行為變因會污染 P96 debug。 | B 級 | 0 | RTK 明列 Forbidden Work，P96 收到穩定點後另開 Program。 | 入 RISK_REGISTRY |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

| Skill 名稱 | SKILL.md 啟動標記 | registry.json 登記 | `claude_path` 目錄存在 | slash_command 設定 |
|---|---|---|---|---|
| N/A | 本 Phase 不新增或收官 skill | N/A | N/A | N/A |
