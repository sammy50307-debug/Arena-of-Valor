# 📋 P108 報告數據可信度修復 計畫書（v1.0 DRAFT）

> 對齊 `docs/PHASE_TEMPLATE.md` v1.2｜17 層品質框架 v3.1。
> 凍結前過 `scripts/lint_phase_plan.py docs/P108_REPORT_DATA_CREDIBILITY_PLAN.md`。
> **S0 證據已先行驗證**（見 §2、§9），符合「先驗證資料層再改呈現層」鐵律。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P108 |
| **Phase 名稱** | 報告數據可信度修復（平台統計圖表失真 + 熱詞無連結） |
| **凍結日期** | 2026-06-06 |
| **影響半徑** | 標準 (3-9 檔) ─ META3 |
| **預估投入時數** | 3.5 h |
| **Token budget** | 80K tokens |
| **負責模型** | Opus 4.8（跨資料層/呈現層偵錯，已做 S0 證據鏈）；機械改動段落可降 Sonnet 4.6 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| N/A | | | | | 本 Phase 不涉及 skill / module / workflow 生命週期狀態轉換，僅修報告資料生成與呈現邏輯 |

---

## 1. 目標 (Objective) ─ 必填

修正報告兩處數據失真，達成「報告圖表/熱詞區呈現的數值＝真實爬取資料」：
1. **平台分布長條圖**改採真實 post 平台統計（巴哈 24 篇必須出現在圖上），取代 LLM 幻覺子集（現況圖上只有 ig/threads/facebook，且 facebook=2 根本不存在於原始資料）。
2. **真實熱詞統計區**（jieba 詞頻）非空且可點詞看來源（現況 `real_hot_topics=[]` 整區不渲染）。

## 2. 觸發背景 (Why Now) ─ 必填

P107 收官後阿喜手機看 6/2 報告，發現「資料大多來自巴哈姆特，但圖表上看不到巴哈姆特，全跑到 FB 或其他地方」「熱詞區是空的」。登記 R-028。本視窗 S0 驗證（2026-06-06）已釘死全部根因（見 §9 證據鏈），不再是推測。原交接列 A/B/C 三問題，S0 後 **B 併入 C（同一根因：platform_breakdown 失真）**，收斂為兩個真 bug。

## 3. Entry Criteria（入口條件）─ 必填 ─ STR4

- [x] 前置 Phase 已收官：P107（焦點英雄爬取覆蓋修復）已 push origin/main
- [x] 資料/依賴已備：`data/raw_20260602.json` + `data/analysis_20260602.json` 可供重現；jieba 已在 `requirements.txt:33`
- [x] 主公已核准：2026-06-06 阿喜核准「撰寫計畫書」（動工另需核准凍結後）
- [x] 風險登記簿無未解高風險阻擋：R-028 為本 Phase 標的；R-029（安全）已熱修；無衝突

## 4. Exit Criteria（退出條件）─ 必填 ─ STR3

達成全部才算收官：
- [ ] **C-1 平台圖正確**：以 6/2 真實資料重生報告，平台長條圖含 `bahamut`（24）、`youtube`（2）、`instagram`（1），且無 LLM 幻覺平台（無 facebook=2）
- [ ] **C-2 熱詞非空**：同一報告 `real_hot_topics` 非空、`topic_to_posts` 有對應、側欄點詞可顯示來源；且平台名雜訊（「巴哈姆」等）不在熱詞 top
- [ ] **C-3 防復發 checker**：新增 advisory checker 偵測「platform_breakdown 缺真實平台 / real_hot_topics 空」並印警告，**不阻斷報告生成**（韌性）
- [ ] **C-4 測試不退**：全套測試 ≥ 412 passed（新增測試案例覆蓋 platform_breakdown 真實統計 + checker）
- [ ] **C-5 阿喜人工驗收**：重生 6/2 報告，阿喜親看圖表有巴哈、熱詞非空

## 5. ROI 評估 ─ G4-2 ─ 必填

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 3.5 h |
| 預估收益等級 | 高 |
| 收益描述 | 報告核心價值＝數據可信度；修後使用者看到的圖表/熱詞與真實一致，且 checker 防未來靜默失真復發 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表 ─ 必填 ─ META2

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | 重算邏輯抽成單一純函式、命名清楚、不重複 local_analyzer 既有口徑 | 與 local_analyzer.py:215 口徑漂移（兩處平台統計不一致）| 共用同一 `_canonical_platform` 正規化；測試對齊兩處輸出 |
| **2. 邏輯層 (Logic)** | platform_breakdown 改「真實 post 計數」；熱詞 stopword 補平台名 | 平台正規化遺漏 alias（bahamut/巴哈姆特/forum.gamer）導致同平台被拆兩條 | 重用 `_canonical_platform` alias 表；測試含巴哈別名 |
| **4. 測試層 (Testing)** | T:新增 platform_breakdown 真實統計測試 + checker 測試 + 熱詞 stopword 測試 | 測試只驗 happy path、漏空資料/全單一平台邊界 | 測試含「0 篇」「全巴哈」「混合平台」三案例 |
| **10. 安全層 (Security)** | 純本地資料統計，不引入外部輸入；checker 不外連 | 報告含 URL，無新增注入面 | 沿用既有 `_copy_entry_with_safe_url`；checker 唯讀不寫敏感資料 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層** | 在 sentiment LLM 後處理重算（dynamic_focus 之前），不動 LLM schema/prompts；統計抽共用函式 | 放後處理而非 schema，LLM 仍吐幻覺值但被即時覆寫 | 共用函式 + 註解標明「LLM platform_breakdown 只吐固定子集不可信，以此真實統計為準」 |
| **5. 資料層** | platform_breakdown 來源從 LLM 子集 → analyzed_posts 真實統計 | analyzed_posts 結構變動會破壞重算 | 防禦式取值（entry.get("post")）+ 測試鎖結構 |
| **6. 可觀察性層** | checker 印 advisory 警告；jieba 缺已有 warning log（keyword_stats.py:107）| 警告被淹沒在 log | checker 警告印在報告生成輸出末行，明顯 |
| **7. 韌性層** | checker advisory 不阻斷；jieba 缺時 fallback 空不中斷 | checker 誤判把正常空資料當失敗嚇到使用者 | checker 只 warn 不 raise；訊息註明「可能真無資料」 |
| **13. 可維護性層** | 重算邏輯單一來源、測試鎖口徑 | 半年後不知為何不用 LLM 版 | 計畫書 + 程式註解記錄「LLM 只吐固定子集」根因 |
| **14. 文件層** | 收官補 TASK_HISTORY；R-028 更新狀態；本計畫書留證據鏈 | 文件與實作漂移 | 收官時同步更新三處 |
| **15. 流程層** | 每階段獨立 commit + 跑全套；先驗資料層再改 | N/A | 沿用既有流程 |

> 可觀察性備註（B-009）：checker 為唯讀偵測，不產生 append-only 檔，無 retention 議題。

### B 級層（條件式）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **9. UX/A11y** | 涉及前端（report.html 圖表）| 補 bahamut 平台中文名 + 圖表顏色對照 | 平台名顯示英文 `bahamut` 不夠友善 | 加平台 label 對照表（巴哈姆特）+ 顏色 |
| **12. 成本層** | 報告流程含 LLM | 本 Phase 不增 LLM 呼叫（改用本地統計反而少依賴 LLM 正確性）| 無新增成本 | N/A |

（其餘 B 級層 8/11/16/17 未觸發，刪除）

### 層級互鎖驗證 ─ META5

- [x] 動 Logic 層 → 已動 Testing 層
- [x] 動 Data 層 → 已動 Maintainability 層
- [x] 動 Security 層 → 已動 Testing 層（checker 測試）
- [ ] 動 Architecture 層 → 已動 Documentation 層（收官補註解 + TASK_HISTORY）
- [x] 動 Performance 層 → N/A（未動效能層）

---

## 7. 跨切面檢查 ─ X1-X4 ─ 必填

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 本地 `pip install jieba`（已執行強化 S0） | 可逆（可 uninstall）| 低風險免確認 |
| 修改 generator.py / report.html / keyword_stops.yaml | 可逆（git revert）| 免 |
| 新增 checker + 測試檔 | 可逆 | 免 |
| commit | 可逆 | 免 |
| **push origin/main** | 半可逆 | **需阿喜親口核准** |
| 重生並覆寫 6/2 報告 HTML（驗收用）| 半可逆（git 留舊版）| 提醒阿喜 |

### X2 盲區掃描

- [x] log 副作用：checker 新增 advisory 輸出（阿喜可見，刻意攤開在末行）
- [x] 中間檔產出：重生報告會覆寫 `data/reports/aov_report_2026-06-02.html`（驗收用，git 可回溯）
- [x] 系統狀態變更：本地已裝 jieba（環境變更，已記錄；雲端早有）

### X3 時間敏感性

- 凍結日期：2026-06-06
- 過期日期：2026-09-06（之後若報告架構大改需重新審視本計畫）
- 風險記錄帶日期：✅

### X4 多角度同行審查

- **主公視角**：阿喜要的是「圖表有巴哈、熱詞不空」，C-1/C-2/C-5 直接對應，驗收條件具體可看。
- **紅隊攻擊者視角**：本 Phase 不引入外部輸入或新攻擊面；唯一風險是 checker 邏輯被餵惡意 platform 字串導致誤判，但 checker 唯讀、不執行、不外連，影響僅限警告文字。報告 URL 沿用既有 safe_url 處理。
- **接手者視角**：程式註解 + 計畫書記錄「為何不用 LLM platform_breakdown」，半年後可懂。
- **X4-J 自動化工具邊界**：checker 是啟發式偵測（「平台數 < 真實平台種類」「熱詞為空」），false-negative 模式：若 LLM 剛好幻覺出真實平台名則偵測不到。CLI 末行印免責「此檢查僅供參考，人工覆核仍必要」。
- **X4-K 使用者端審查官**：避免 checker 把「今天真的沒爬到文章」誤報成 bug 嚇到阿喜 → 警告文字註明「也可能當日無資料」。

---

## 8. 風險清單 ─ 必填

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | platform 正規化漏 alias，巴哈被拆成 bahamut/巴哈姆特兩條 | 中 | 中 | 代碼可控 | 重用 `_canonical_platform`；測試含別名 |
| R2 | checker 太嚴，正常空資料誤報 | 中 | 中 | 業務 | advisory 不阻斷 + 文字註明可能真無資料 |
| R3 | 雲端報告其實正常（本地 run-now 才空），改錯方向 | 中 | 中 | 環境依賴 | **S0 第一步先確認 6/2 報告產生來源**再動 A |
| R4 | 在 generator 重算，未來非報告消費者拿不到正確值 | 低 | 低 | 代碼可控 | 函式獨立可複用；目前唯一消費者是報告 |
| R5 | 熱詞 stopword 加太多，誤殺有意義詞 | 低 | 低 | 代碼可控 | 只加平台名雜訊（巴哈姆/論壇等），逐個驗 |

**高風險加權檢查（META4）**：高風險 0 項；加權 = 中×3(1)+低×2(0.5) = 4 分；< 5，不需請示（但 push 仍須核准）。

---

## 9. 工作階段 (Stages) ＋ S0 已驗證證據鏈

> **S0 證據（2026-06-06 本視窗已完成驗證，非推測）**：
> - 原始 `raw_20260602.json` 27 篇：bahamut=24 / youtube=2 / instagram=1，source/platform 兩欄皆正確。
> - `analysis_20260602.json` 的 `platform_breakdown = {ig:0, threads:0, facebook:2}` ← LLM 幻覺（facebook=2 不存在於原始）。根因 `sentiment.py:101` schema 只吐 ig/threads/fb + `generator.py:122-131` 寫死白名單無 bahamut。
> - `real_hot_topics=[]`。本地裝 jieba 後對同一 raw 跑 `compute_hot_topics` → 正常回 10 熱詞 → **A 是純環境問題（缺 jieba），非邏輯 bug**；但 top1「巴哈姆」是平台名切殘雜訊。
> - **報告來源已釘死**：6/2 22:38 報告 commit `931b71a` author＝`sammy50307-debug`（阿喜本人）、非 cron 時間（cron＝`30 8 * * *`）、`analysis_20260602.json` 無 commit 記錄 → **阿喜手機那份＝本地 run-now**（非雲端）。GitHub Actions cron 的 commit author＝`github-actions[bot]`（workflow:49-50），雲端有 jieba（requirements:33）。
> - **消費者掃描**：`platform_breakdown` 僅 2 消費者 — `dynamic_focus.py:93`（今日焦點平台熱度，在 sentiment 階段跑）+ `generator.py:122`（圖表）。`real_hot_topics` 僅 generator + report.html。
>
> **A/C 兩端對照結論**：
> | | 本地 run-now | 雲端 cron（有 jieba）|
> |---|---|---|
> | A 熱詞空 | ❌ 空（缺 jieba）| ✅ 應正常（非 production bug）|
> | C 平台圖失真 | ❌ 壞 | ❌ 也壞（LLM schema 幻覺，與 jieba 無關）|
> → **A 簡化為「本地裝 jieba（已裝）+ checker 防復發」，不碰邏輯**；**C 是真 bug、兩端都壞、為本 Phase 核心**。

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0** | ✅ **已完成**（見上方證據塊）：報告來源已釘死＝本地 run-now；A 為環境問題、C 為真 bug | R3 | 已判定，無懸念 |
| **S1（C＝B，高 ROI，核心）** | (a) 抽真實 platform 統計函式（複用 local_analyzer `_canonical_platform` 口徑）；(b) **sentiment.py:509 後**（`sentiment_distribution` 覆寫旁、dynamic_focus 之前）加 platform_breakdown 真實重算覆寫 LLM 版；(c) 拔 generator.py:122-131 寫死白名單讓真實 key 全通過；(d) report.html 圖表補 bahamut label/顏色 | 平台圖 + 今日焦點失真 | 6/2 重生圖表含 bahamut 24、無幻覺 facebook；今日焦點平台熱度正確 |
| **S2（A，已解大半）** | 本地 jieba（已裝）；keyword_stopwords.yaml 補平台名雜訊（巴哈姆/論壇等）；確認熱詞區渲染 | 熱詞空 + 雜訊 | 6/2 重生熱詞非空且無平台雜訊 top |
| **S3（防復發）** | 新增 advisory checker（scripts/check_report_credibility.py）守 platform_breakdown 含真實平台數 + real_hot_topics 非空；報告生成末行印警告（不阻斷）| 未來靜默復發 | checker 對失真資料印警告、對正常資料靜默 |
| **S4（測試+收官）** | 補測試（platform 真實統計 / checker / stopword）；跑全套 ≥412；補 TASK_HISTORY + 更新 R-028 狀態 | 回歸 | 全套綠 + 文件同步 |

> **修法決策（架構選擇，已修正）**：platform_breakdown 重算放 **sentiment.py:509 後**（LLM 後處理、dynamic_focus 之前），**非 generator**。理由：S0 掃描發現 `dynamic_focus.py:93` 是第二消費者且在 sentiment 階段跑——放 generator 會漏修今日焦點。放 sentiment 後處理一處修、兩消費者（圖表＋今日焦點）都正確，且有現成 pattern（`sentiment_distribution` 同樣「LLM 不可靠→code 覆寫」，sentiment.py:504-509）。generator 仍需拔白名單讓真實 key 通過。統計口徑複用 local_analyzer `_canonical_platform`，避免兩處漂移。

---

## 10. 影響檔案清單 ─ STR7

**新增**：
- `scripts/check_report_credibility.py`（advisory checker，~60 行）
- `tests/test_report_credibility.py`（platform 真實統計 + checker + stopword，~80 行）

**修改**：
- `analyzer/sentiment.py`（LLM 後處理加 platform_breakdown 真實重算覆寫，~+8 行；位置 :509 後）
- `analyzer/local_analyzer.py`（抽 `compute_platform_breakdown(analyzed_posts)` 共用函式供兩處複用，~+5/-3 行）
- `reporter/generator.py`（拔 :122-131 寫死白名單，改原樣傳遞所有平台，~+5/-12 行）
- `reporter/templates/report.html`（圖表 bahamut label/顏色，~+10 行）
- `configs/keyword_stopwords.yaml`（補平台名雜訊，~+5 行）
- `requirements.txt`（jieba 已在，無需改）

**刪除**：無

**影響但未直接修改**：
- `analyzer/dynamic_focus.py`（第二消費者；因重算放 sentiment 後處理，它自動拿到真實版，無需改）

---

## 11. Postmortem 預埋點 ─ G6

- [ ] 主公中途否決重來
- [ ] 階段測試發現重大設計缺陷
- [x] **S0 已揭露「我以為」事件（G2-3）**：原以為熱詞是邏輯 bug + 重算放 generator 即可；實為「本地缺 jieba」+「dynamic_focus 是第二消費者需放 sentiment 後處理」。已於動工前修正計畫，無需事後 Postmortem（記錄於此）
- [ ] 上線後發現預期外副作用

Postmortem 位置：`docs/postmortems/2026-06-06-phase-108-report-credibility.md`

> 新風險如需登記用 R-030；新通則化盲點用 B-023（全域連續）。

---

## ✈️ Pre-flight 多視角體檢 ─ M1 + M1.5 + M2

### M1 強制填表（十一視角）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | 無新外部輸入面；checker 唯讀不執行不外連，惡意 platform 字串至多影響警告文字，嚴重度低，最小緩解＝checker 不 eval/不寫檔 |
| **X4-B 接手者** | 程式註解標明「LLM platform_breakdown 只吐固定子集不可信，以 generator 真實重算為準」，半年後可循計畫書理解 |
| **X4-C 災難情境** | 情境：generator 重算誤吃到空 analyzed_posts 導致圖全空 / 緩解：空時 fallback 沿用原 daily_summary 值且 checker 警告 |
| **X4-D 5 年後** | 若報告改用真正多平台爬蟲，真實統計邏輯自然涵蓋新平台，不需改架構 |
| **X4-E 終端 vs IDE** | 改動為純後端 Python + 模板，終端 `py` 執行；無 IDE 專屬行為差異 |
| **X4-F 跨平台 Win/Mac/Linux** | jieba 純 Python 跨平台；路徑用 pathlib；checker 不依賴 OS 指令 |
| **X4-G 主公個人視角** | 阿喜手機看報告要圖表有巴哈、熱詞不空——C-1/C-2/C-5 直接對應，可一眼驗收 |
| **X4-H 觀測 / 治理** | checker advisory 警告攤在報告生成輸出，治理上可見；R-028 狀態收官更新 |
| **X4-I 主公可見性** | 看不到的：本地已裝 jieba（已記 X2）、重算覆寫 LLM 值（程式註解攤開）、重生報告覆寫 6/2 HTML（git 可回溯）|
| **X4-J 自動化工具邊界** | checker 啟發式 false-negative：LLM 幻覺剛好命中真實平台名則偵測不到；CLI 末行印「僅供參考、人工覆核仍必要」|
| **X4-K 使用者端審查官** | 風險：checker 把「當日真無資料」誤報成失真嚇到阿喜 → 警告文字明寫「也可能當日無資料，請人工確認」|

> 主公裁決錨點（B-005）：本 Phase 裁決點 2 個 ─ (1) 凍結核准（~2 分鐘讀計畫書）、(2) push 前核准（~1 分鐘看 diff 摘要）。AI 提供格式：計畫書全文 + 收官 diff 摘要。

### M1.5 八人格顧問團

| 人格 | 觸發 | 檢查重點 | 發現 |
|---|---|---|---|
| **Jarvis 總控** | 固定 | 目標/邊界/下一步 | 目標明確兩 bug、結論先行（B＝C）、階段清楚 S0-S4 ✅ |
| **Ken 紅隊** | 固定 | 安全/權限/不可逆 | 無新攻擊面；push 半可逆需核准 ✅ |
| **Patric 使用者審查** | 固定 | 誤解/死路 | checker 誤報防護（註明可能真無資料）✅ |
| **Jimmy 文件主筆** | 觸發（改 TASK_HISTORY/計畫書）| 可追溯/有來源 | S0 證據鏈帶 file:line + 重現數據 ✅ |
| **Marcus 數據分析** | 觸發（涉數據/統計）| 定量定性分清 | platform 統計用真實計數；熱詞用 jieba 詞頻覆蓋率口徑 ✅ |
| **Oliver 設計審查** | 觸發（涉圖表）| 可讀性/顏色 | 圖表補 bahamut 中文 label + 顏色對照 ✅ |
| **Penny CFO** | 觸發（LLM 成本）| ROI/停損 | 不增 LLM 呼叫（反而少依賴 LLM）；成本中性 ✅ |
| **Jason DevOps** | 觸發（git/環境）| rollback/環境 | jieba 跨平台；改動 git revert 可逆；雲端 requirements 已有 jieba ✅ |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing 計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | **（S 級）** 你怎麼確定雲端報告也壞？改 A 可能改錯方向（重蹈 P107 沒驗證就改）| S | 0 | **S0 已完成**：6/2 報告 commit author＝阿喜本人＝本地 run-now；A 是本地缺 jieba（雲端有）、C 兩端都壞。A 不碰邏輯 | 已解（S0 完成）+ 入 RISK_REGISTRY（R3 降級）|
| 2 | **（S 級）** 重算 platform_breakdown 會不會破壞其他 `daily_summary[platform_breakdown]` 消費者？ | S | 0 | **已 grep 確認** 僅 2 消費者：dynamic_focus（sentiment 階段）+ generator。原「放 generator」會漏 dynamic_focus → **改放 sentiment:509 後**涵蓋兩者；複用 local_analyzer 口徑防漂移 | 入計畫範圍（S1 修法決策已修正）|
| 3 | platform 正規化漏 alias 導致巴哈被拆兩條 | A | 0 | 重用 local_analyzer 既有 `_canonical_platform` alias 表，不自造 | 入計畫範圍（S1）+ 入 RISK_REGISTRY（R1）|
| 4 | checker 太嚴把正常空資料誤報，嚇到阿喜 | A | 0 | advisory 不阻斷 + 文字註明「可能真無資料」 | 入計畫範圍（S3）+ 入 RISK_REGISTRY（R2）|
| 5 | 熱詞 stopword 加平台名，會不會誤殺英雄名或有意義詞 | B | 0 | 只加確認的平台/論壇雜訊，逐詞驗證；英雄名在自訂詞庫保護 | 入計畫範圍（S2）+ 入 RISK_REGISTRY（R5）|
| 6 | 重生 6/2 報告覆寫舊 HTML，阿喜看不到變更 | B | 0 | git 留舊版可 diff；X2 已記錄 | 入計畫範圍（已緩解）|

> 未解質疑：質疑 1（雲端來源）以 S0 解；質疑 2（消費者）收官前 grep 確認。兩者均有明確驗證步驟，不留未解高風險。無 pre-existing failing test 涉入。

---

## 12. 凍結戳記

- **凍結人**：阿喜 + AI 雙方確認（2026-06-06 核准凍結並開工）
- **凍結時間**：2026-06-06
- **凍結後變更**：禁止；如需修改新增「P108.X 補遺」章節

---

*本計畫書受 17 層品質框架 v3.1 + STR10 Pre-flight 保護。*
