# Phase 110 v2 — 最新動態文章凍結修復（巴哈板列表撈新文 + 去重 + 凍結偵測器；S3 picker 降最後手段）（草案，待阿喜凍結）

> 狀態：**✅ 已收官 v2（2026-06-13）｜Claude 動工 S1-S6 完成，504 passed，飛輪 Review 裁決可收官；commit 待建（push 待阿喜）**
> 戰線：**爬取層（板列表撈新文）+ 呈現層（去重/分區）+ 可觀察性（凍結偵測器）**
> 鐵律：`py` 不用 `python`；TASK_HISTORY 禁全讀（grep 錨點+Read offset）；改動前計畫書等同意；**芽芽優先於所有過濾規則**（memory，v2 三主力收編全不動 picker、0 風險）；push 前問阿喜。

---

## 📜 v2 緣由（飛輪 Workflow 9-agent 探索 + Claude 親驗，2026-06-13）

阿喜二次追問「更好的做法」+ Ultracode → Workflow 4 角度提案 + 紅隊對抗 + 綜合，Claude 交叉驗證關鍵承重點。結論：**原 P110（S1 PoC 閘門→S2→S3 拆鎖榜→S4）方向對但非最優**，重排如下。

| 飛輪提案 | 裁決 | Claude 親驗 |
|---|---|---|
| **#2 巴哈板最新列表**（B.php 不帶 q、class `b-list__row--sticky` 過濾置頂） | ✅ 採納（最高邊際）| ✅ 親抓 B.php?bsn=30518：32 列/7 sticky/25 feed，時間戳 `31分前/1小時前/昨天17:24` = 每日活 feed |
| **#4 manifest top5 指紋地基** | ✅ 採納 | ✅ source_hash 雜湊輸入非輸出=凍結假陰性盲區；top5 身分未持久化 |
| **#3 去重子集**（top5_news 移除已在芽芽常青區 URL）| 🟡 部分採納 | ✅ 親驗 `generator.py:322-323` top5_news=yaya_cards+other_cards → 同篇芽芽文一頁渲染兩次 |
| **#1 純時間軸雙軌** | ❌ 棄 | dedup 從不剔池→時間軸只把「相關度鎖榜」平移成「時間軸鎖榜」，治標未治本 |
| **原 S3 picker 硬調參** | ⬇️ 降最後手段 | 三參數撞芽芽鐵律 + decay 放寬反抬高觸底值；上游修好後多半不需要 |

**根因（已查證）**：① 爬蟲輸入固定（巴哈搜尋零時間排序回同批舊文）② picker 鎖榜（芽芽豁免+decay觸底2.1天+重複加成）③ dedup 指標誤導 ④ **（飛輪新增）一頁渲染兩次**（top5_news 含 yaya_cards）。

**v2 核心策略**：**先治上游（撈新文）+ 治呈現（去重）+ 補可觀察（偵測器），把會撞芽芽鐵律的 picker 硬調參降為條件性最後手段。** 芽芽優先全程 0 風險。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P110 |
| **Phase 名稱** | 最新動態文章凍結修復 v2（板列表撈新文 + 去重 + 凍結偵測器）|
| **凍結日期** | （待阿喜凍結）|
| **影響半徑** | 重大（~9 檔：bahamut/date_normalizer scraper、generator、report.html、run_manifest、main、check_report_freshness、daily_report.yml、tests）─ META3 |
| **預估投入時數** | 5 h |
| **Token budget** | ~120K tokens |
| **負責模型** | Opus 4.8（Claude 親自動工，飛輪已收斂方向）|

## 0.5 狀態轉換清單 ─ B-002

N/A — 不涉及 skill/module 生命週期狀態轉換。

---

## 1. 目標 (Objective)

讓每日報告「最新動態」**真正每天更新**：(1) 巴哈改抓板最新列表撈新文（治根因①）；(2) top5_news 去重消除「同篇芽芽文一頁渲染兩次」（治根因④）；(3) manifest 持久化 top5 指紋 + 凍結偵測器自動告警未來任何凍結（飛輪護欄）。**全程不動 picker、保芽芽優先**。S3 picker 硬調參降為「僅 S1+S2 後仍凍結才做」的條件性最後手段。量化：連續 3 天 top5 URL 集合不完全相同；同篇芽芽文不再一頁出現兩次；凍結偵測器能抓連續 N 天 top5 相同。

## 2. 觸發背景 (Why Now)

阿喜 2026-06-13 回報「文章沒在更新，特別芽芽版」。調查證實每天每篇一樣。飛輪深探翻案了原 S1 悲觀假設（巴哈板列表可撈新文）+ 揭露原 S4 因果斷點 + 找到第 4 個觀感根因（一頁渲染兩次）。

## 3. Entry Criteria

- [x] 前置：P107（爬取）、P106.1/P108.4（picker）已收官
- [x] 根因 + 飛輪方案已交叉驗證（Workflow 9-agent + Claude 親驗 4 承重點）
- [x] 主公核准凍結（2026-06-13；同意 S3 降條件性最後手段、本期不動 picker；接受 META4 7.5）
- [x] 風險登記簿無未解高風險阻擋

## 4. Exit Criteria

- [ ] A：巴哈板列表接入——`B.php?bsn=30518` 不帶 q、`b-list__row--sticky` class 過濾置頂（**不寫死跳 N 列**）、保留關鍵字搜尋雙軌補芽芽精準命中、graceful 降級回搜尋
- [ ] B：`date_normalizer.py` 支援裸「MM-DD」（無 HH:MM）變體 + fixture（否則板列表新文被當無日期文壓低 decay）
- [ ] C：`generator.py:323` top5_news 移除已在 top5_yaya 的芽芽 URL（根除一頁渲染兩次）+ 處理槽位/編號/enforce_diversity 耦合
- [ ] D：`run_manifest.py` 加 `quality.freshness`（top5_hash〔成員集合排序去名次〕+ 最老文齡 + decay 觸底篇數）；top5 卡片從 generator 穿線進 manifest
- [ ] E：`scripts/check_report_freshness.py`（連續 N 天 top5_hash 相同→advisory 告警，末行印邊界，文案標「凍結可能是芽芽預期副作用由阿喜判讀」）+ daily_report.yml advisory step
- [ ] F：契約測試（top5 連續日輪動 + 芽芽佔比不降 + 同篇芽芽文不一頁兩次 + 偵測器自測）+ 既有 picker 測試零回歸
- [ ] G：全套零回歸（基線動工實跑）
- [ ] H：收官文件 + 風險/盲點登記 + postmortem「優先豁免反噬鎖榜 + 名實不符雙軌」通則
- [ ] **S3 picker 硬調參 = 條件性**：S1+S2 落地後若驗證仍凍結才做；否則登記觀察、本期不動 picker

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 5 h |
| 收益等級 | **高** |
| 收益 | 治根因①（撈新文）+ 根因④（去重）；裝凍結偵測器（未來凍結自動抓不靠肉眼）；避開撞芽芽鐵律的 picker 硬調參 |
| ROI | ✅ 高（每日戰報凍結=產品死亡；v2 比原版更可靠〔已驗證撈新文〕、更安全〔不動 picker 保芽芽〕）|

---

## 6. 17 層稽核表 ─ META2

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | bahamut 板列表 method + sticky class 過濾;date_normalizer 裸MM-DD;generator top5_news 去重;run_manifest freshness;check_report_freshness | 板列表解析與既有搜尋骨架耦合;跨模組穿 top5 進 manifest | 沿用 _parse_row 骨架加條件分支;graceful 降級;小批次每改一處測 |
| **2. 邏輯** | 板列表跳 sticky;去重排除已在常青區芽芽;top5_hash 成員集合算法;decay 觸底計數 | sticky 寫死/裸MM-DD解析失敗/去重破壞槽位編號 | sticky 用 class 非寫死;date_normalizer fixture;去重處理 enforce_diversity 耦合 |
| **4. 測試** | 契約(輪動+芽芽佔比+不渲染兩次)+偵測器自測+板列表fixture+normalizer fixture | 只驗單元不驗端到端輪動 | 多日模擬端到端契約測試 |
| **10. 安全** | 板列表單頁 GET(請求量不增)、遵守 ToS/robots | 加爬取觸反爬/IP ban | 單頁、最多 page=2、不暴力、失敗 graceful（Ken 紅隊覆核）|

### A 級（提示填）
| 層 | 採用/N-A | 風險 | 緩解 |
|---|---|---|---|
| **3. 架構** | 巴哈雙軌（板列表撈新文 + 關鍵字搜尋補芽芽）;呈現層去重;manifest 可觀察 | 雙軌複雜化 | 沿用既有骨架、非新架構 |
| **5. 資料** | 板列表相對時間戳正規化;top5 指紋持久化 | 裸MM-DD/相對格式解析 | date_normalizer 補變體 + 複用 |
| **6. 可觀察性（飛輪核心）** | 🌟 manifest `quality.freshness`(top5_hash/最老文齡/decay觸底) + check_report_freshness 偵測器 | 偵測器誤報;source_hash 假陰性盲區 | advisory 不阻斷 + top5_hash 才是真信號(非 source_hash) + 末行印邊界 |
| **7. 韌性** | 板列表失敗 graceful 降級回搜尋 | 板列表 DOM 漂移崩潰 | class 漂移 fixture + try/except 降級 |
| **13. 可維護性** | sticky 用 class 過濾(抗漂移);偵測器版控友善資料源 | 巴哈改版 | fixture 擋漂移 + 降級 |
| **14. 文件** | 計畫書 + TASK_HISTORY + postmortem + 風險登記 | — | 收官件套 |
| **15. 流程** | 標準 Phase（S1-S6）| — | — |

### B 級（條件式）
| 層 | 觸發 | 採用 | 風險 | 緩解 |
|---|---|---|---|---|
| **9. UX/A11y** | report.html | 去重消除重複渲染 + 常青區語意化 badge + 最新動態真輪動 | 去重後槽位/編號斷裂 | 處理 enforce_diversity/need_general 耦合 |
| **11. 部署** | daily_report.yml | 凍結偵測器掛 advisory step | CI step 失敗中斷 | continue-on-error（既有模式）|
| **8 效能/12 成本/16 隱私/17 i18n** | 未觸發 | — | — | N/A（板列表請求量不增、無付費 API 增量）|

### 層級互鎖 ─ META5
- [x] Logic→Testing｜[x] Architecture→Documentation｜[x] Data→Maintainability｜[x] Security→Testing｜[ ] Performance→N/A

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| 改 scraper/normalizer/generator/manifest/main/template/yaml | 可逆（git revert）| — |
| 新增 check_report_freshness.py / tests | 可逆 | — |
| push origin/main | 半可逆 | **push 前問阿喜** |

### X2 盲區掃描
- [x] log：板列表撈取 log；偵測器告警
- [x] 中間檔：dry-run 產 index.html/llm_cache → 收官 git checkout
- [x] 系統狀態：未來報告 top5 輪動 + manifest 多 freshness 欄位 + CI 多 advisory step

### X3 時間敏感性
- 凍結日期：（待）／過期日期：2026-09-13／風險帶日期：✅
- 巴哈板列表 DOM/sticky class 可能隨巴哈改版變動 → fixture 擋 + 降級 + 登記觀察

### X4 多角度審查
- **主公**：阿喜要文章每天更新。v2 用「已驗證的板列表撈新文 + 去重」直擊，且**不動 picker 保芽芽優先**（比原 S3 硬調參更安全）。
- **紅隊**：板列表加爬取要防反爬/IP ban——單頁 GET、不暴力分頁、class 過濾非寫死、graceful 降級（延續 R-027/P107 教訓）。
- **接手者**：sticky 用 class 過濾 + fixture + postmortem「名實不符雙軌」通則，接手者懂為何板列表取代搜尋、為何 picker 不動。
- **X4-J 自動化建議性工具邊界**：凍結偵測器是**字面比對啟發式**（top5_hash 連續相同），會誤報（真的沒新文時也告警），故 advisory 不阻斷、CLI 末行印「召回率僅供參考、人工覆核必要 + 凍結可能是芽芽預期副作用」免責。
- **X4-K 使用者端審查官**：誤解風險①去重後最新動態槽位變少看起來空 ②偵測器誤報讓阿喜誤砍芽芽。緩解：處理槽位耦合補滿、偵測器文案標「芽芽預期副作用由阿喜判讀」。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 巴哈板列表 DOM/sticky class 改版漂移 | 中 | 中 | 環境 | class 過濾非寫死 + fixture 擋漂移 + graceful 降級回搜尋 |
| R2 | 裸 MM-DD（無 HH:MM）正規化失敗→新文被當無日期壓低 decay | 中 | 中 | 代碼 | date_normalizer 補變體 + fixture（飛輪紅隊指出的 _MMDD_RE:32 缺口）|
| R3 | 去重破壞 top5_news 槽位/編號/enforce_diversity 契約 | 中 | 中 | 代碼 | 先查既有契約(B-024) + 補滿槽位 + 測試 |
| R4 | 板列表全板主題稀釋芽芽專文 | 中 | 中 | 業務 | 保留關鍵字搜尋雙軌補芽芽精準命中（不純列表單軌）|
| R5 | top5 卡片跨模組穿線進 manifest（generator→main→run_manifest）出錯 | 中 | 低 | 代碼 | 小批次 + 處理 generator 降級路徑 + 測試 |
| R6 | 偵測器誤報（真沒新文時告警）| 中 | 低 | 代碼 | advisory 不阻斷 + 文案標芽芽副作用 + 閾值調校 |
| R7 | 加爬取觸巴哈反爬/IP ban | 低 | 高 | 環境 | 單頁 GET、不暴力、graceful（Ken 覆核）|
| R8 | 基線測試數漂移 | 中 | 低 | 環境 | S5 第一步實跑 pytest |

**META4 加權**：影響高=2(R7)；中=1(R1,R2,R3,R4)；低=0.5(R5,R6,R8) → 2+4+1.5 = **7.5 分 ≥5 須請示**。已攤開：R1/R2/R3 為落地細節（fixture + 查契約緩解），R7 安全（速率限制），請阿喜凍結時確認。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解風險 | 驗收 |
|---|---|---|---|
| **S1 巴哈板列表撈新文（主力）** | bahamut_scraper 加板列表 method(B.php 不帶q)+`b-list__row--sticky` class 過濾(非寫死跳N列);date_normalizer 補裸MM-DD+fixture;main 改板列表+關鍵字搜尋雙軌;graceful 降級 | R1,R2,R4,R7 | 端到端:候選池含近期新文+連續日輪動;fixture 過 |
| **S2 去重 + 分區語意化** | generator.py:323 top5_news 移除已在 top5_yaya 的芽芽URL(根除一頁渲染兩次);處理槽位/編號/enforce_diversity 耦合;report.html 常青區語意化 badge | R3 | 同篇芽芽文不一頁兩次+槽位補滿 |
| **S3 凍結偵測器 + manifest 地基（飛輪護欄）** | run_manifest 加 quality.freshness(top5_hash/最老文齡/decay觸底);top5 卡片穿線 generator→main→manifest;check_report_freshness.py(連續N天告警,advisory,芽芽副作用文案)+daily_report.yml advisory step | R5,R6 | 偵測器自測+manifest 有 freshness |
| **S4 picker 拆鎖榜【條件性最後手段】** | **S1+S2 落地後驗證**：若仍凍結才動 picker（最不傷芽芽方式）;否則登記觀察、**本期不動 picker** | — | 預設不做;若做須芽芽佔比不降 |
| **S5 防復發測試** | 契約(輪動+芽芽佔比+不渲染兩次)+偵測器自測+板列表/normalizer fixture;**第一步實跑基線** | R3,R8 | 契約綠+零回歸 |
| **S6 收官** | TASK_HISTORY+RISK+postmortem(優先豁免反噬+名實不符通則)+memory | — | 件套齊 |

> 動工順序：S1→S2→S3→（驗證）→S4 條件判斷→S5→S6。我這邊動工，從 **S1 巴哈板列表**起（已驗證可撈新文，不需 PoC 閘門）。

---

## 10. 影響檔案清單 ─ STR7

**新增**：`scripts/check_report_freshness.py`（凍結偵測器）；`tests/test_article_freshness.py`（輪動+佔比+不渲染兩次+偵測器自測）；板列表/normalizer fixtures；`docs/postmortems/2026-06-13-phase-110-article-freeze.md`

**修改**：`scrapers/bahamut_scraper.py`（板列表 method+sticky 過濾）；`scrapers/date_normalizer.py`（裸MM-DD）；`reporter/generator.py`（top5_news 去重 + top5 卡片穿線）；`reporter/templates/report.html`（常青區語意化）；`analyzer/run_manifest.py`（quality.freshness）；`main.py`（雙軌呼叫 + top5 穿線）；`.github/workflows/daily_report.yml`（advisory step）

**影響但未直接改（本期）**：`analyzer/top5_picker.py`（S4 條件性，預設不動→**保芽芽優先 0 風險**）

---

## 11. Postmortem 預埋點 ─ G6

位置：`docs/postmortems/2026-06-13-phase-110-article-freeze.md`

> 雙通則：(a) **「優先級豁免」設計會反噬成「鎖榜」**（芽芽豁免+重複加成+decay觸底→老芽芽文數學霸榜）；(b) **「展示層雙軌但機制層共用單一公式」會名實不符**（最新動態名為更新實為相關度榜 + top5_news 含芽芽致一頁渲染兩次）。通則：任何「優先豁免」必須配「新鮮度區分」；任何「雙軌展示」必須確認機制層真正分流、不重複。

---

## ✈️ Pre-flight 多視角體檢 ─ STR10（凍結前必過）

### M1 強制填表（十一視角）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | 攻擊面：板列表加爬取若暴力分頁/高頻會觸巴哈反爬導致 IP 永 ban（不可逆）或違 ToS。緩解：單頁 GET（請求量不增反減）、最多 page=2、不暴力重試、只爬公開頁、class 過濾、graceful 降級回搜尋，Ken 紅隊覆核爬取頻率。 |
| **X4-B 接手者** | sticky 用 class `b-list__row--sticky` 過濾（非寫死跳N列）+ fixture + postmortem 雙通則，接手者懂為何板列表取代搜尋、為何 picker 刻意不動、為何 top5_news 要去重。 |
| **X4-C 災難情境** | 情境：巴哈改版 DOM/class 漂移致板列表解析全失敗 → 報告無新文。緩解：class 過濾 + fixture 擋漂移 + try/except graceful 降級回既有關鍵字搜尋，不中斷 pipeline。 |
| **X4-D 5 年後** | 5 年後巴哈介面可能大改，板列表 method 需維護；但雙軌設計（板列表+搜尋）任一條失效另一條兜底，且 picker 不動長期穩定。 |
| **X4-E 終端 vs IDE** | 純 Python（scraper/generator/manifest）+ httpx 抓網頁，pytest 兩端一致，無終端/IDE 互動差異。 |
| **X4-F 跨平台 Win/Mac/Linux** | scraper httpx + 純運算邏輯，無平台相依路徑/shell；雲端 cron(Linux) 與本地(Win) 行為一致，時間正規化複用 date_normalizer。 |
| **X4-G 主公個人視角** | 阿喜手機看報告：最新動態開始每天輪動、同篇芽芽文不再一頁出現兩次、芽芽仍優先。收官明告「文章會更新了、芽芽仍優先、且裝了凍結偵測器未來自動抓」。 |
| **X4-H 觀測/治理** | manifest quality.freshness（top5_hash/最老文齡/decay觸底）持久化輸出可觀察；凍結偵測器掛 CI advisory；postmortem 雙通則進治理；爬取頻率納安全觀察。 |
| **X4-I 主公可見性** | 自動行為：cron 報告 top5 每天變、manifest 多 freshness 欄位、CI 多 advisory step、爬取量持平。攤開：收官文件 + manifest 指標 + 下次 cron 阿喜親見輪動。 |
| **X4-J 自動化建議性工具邊界** | 凍結偵測器是字面比對啟發式（top5_hash 連續相同→告警），會誤報（真沒新文時也報），召回率僅供參考、人工覆核必要，故 advisory 不阻斷 + CLI 末行印邊界 + 文案標「凍結可能是芽芽預期副作用由阿喜判讀」防誤砍芽芽。 |
| **X4-K 使用者端審查官 / Patric** | 誤解風險：①去重後最新動態槽位變少顯得空→補滿槽位處理 enforce_diversity 耦合；②偵測器誤報讓阿喜或他人為求 hash 變動誤砍芽芽→文案明標芽芽副作用由阿喜判讀。 |

> **主公裁決錨點(B-005)**：2 裁決點 =（1）S1+S2 落地後是否仍需 S4 動 picker（~3 分鐘，AI 給驗證後輪動數據）；（2）凍結偵測器連續 N 天閾值取值（凍結時或 S3，AI 給建議值）。

### M1.5 八人格顧問團

| 人格 | 觸發 | 發現 |
|---|---|---|
| **Jarvis 總控** | 固定 | ✅ 目標清楚（撈新文+去重+偵測器,picker不動）、S4 條件性、6 stage、芽芽 0 風險 |
| **Ken 紅隊** | 固定 | ⚠️ 板列表爬取頻率→單頁/不暴力/graceful（R7）；零 secret；push 前問 |
| **Patric 使用者審查** | 固定 | ⚠️ 去重槽位變少 + 偵測器誤砍芽芽→補滿槽位+文案標芽芽副作用（X4-K）|
| **Jimmy 文件主筆** | 觸發（postmortem/TASK_HISTORY/template） | ✅ 雙通則 postmortem + sticky class 註解 |
| **Marcus 數據分析** | 觸發（輪動率/top5_hash） | ✅ manifest freshness 量化（輪動率/最老文齡/decay觸底），偵測器資料驅動 |
| **Oliver 設計審查** | 觸發（報告呈現） | ✅ 去重消除重複渲染 + 常青區語意化 badge + 最新動態真輪動 |
| **Penny CFO** | 觸發（爬取量） | ✅ 板列表單頁 GET 請求量不增反減，零付費 API 增量 |
| **Jason DevOps** | 觸發（scraper/CI/manifest） | ✅ graceful 降級、跨平台、偵測器掛 CI advisory continue-on-error、push 前問 |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | **【S 級】** v2 不動 picker 真能解凍結嗎？根因②picker鎖榜不是核心嗎？ | S | 0 | 飛輪交叉驗證：鎖榜的「燃料」是根因①爬蟲每天回同批舊文。一旦 S1 板列表撈到新文進池，picker 即使不改也會選到新文（decay 對新文不觸底）。S4 保留為條件性最後手段：S1+S2 後若仍凍結才動 picker。先治上游避免撞芽芽鐵律。 | 入計畫範圍（S1+S4條件性）|
| 2 | **【S 級】** 板列表 sticky「只佔前 7 列」是脆弱假設，巴哈可任意增減置頂！ | S | 0 | 故**嚴禁寫死跳 N 列**，必用 class `b-list__row--sticky` 過濾（Claude 親驗該 class 存在、7 sticky/25 feed）；補 fixture 擋 DOM/class 漂移 + graceful 降級回搜尋。 | 入計畫範圍（S1+R1）|
| 3 | 裸 MM-DD 正規化缺口（_MMDD_RE:32 要 HH:MM）會讓板列表新文被當無日期壓低 decay | B | 0 | 飛輪紅隊指出的真缺口。S1 先補 date_normalizer 裸 MM-DD 變體 + fixture，否則「時間戳可靠」賣點對這類列失效。 | 入計畫範圍（S1+R2）|
| 4 | 去重「只改一行」嚴重低估——撞 enforce_diversity + need_general 槽位契約 | B | 0 | 承認非一行。S2 先查既有契約(B-024) + 處理槽位/編號/多樣性耦合 + 補滿槽位 + 測試。 | 入計畫範圍（S2+R3）|
| 5 | manifest top5_hash「順手回填」低估成本——top5 卡片只在 generator、generate() 只回 path | B | 0 | 飛輪紅隊指出跨模組穿線（generator→main→run_manifest）+ generator 降級路徑。S3 接受此成本（小到中上緣），效益（picker-agnostic 凍結信號抓任何復發）值得。 | 入計畫範圍（S3+R5）|
| 6 | 板列表全板主題會稀釋芽芽專文、且加爬取觸反爬？ | B | 0 | 保留關鍵字搜尋雙軌補芽芽精準命中（不純列表單軌，R4）；單頁 GET 請求量不增反減、不暴力、graceful（R7）。 | 入計畫範圍（S1+R4+R7）|

> 未解質疑：無（6 條皆納入；S4 picker 由 S1+S2 後驗證閘門條件處置）。

---

## 12. 凍結戳記

- **凍結人**：阿喜 + Claude（雙方確認）
- **凍結時間**：2026-06-13
- **動工者**：Claude（從 S1 巴哈板列表撈新文起）
- **收官結果（2026-06-13）**：✅ S1-S6 完成，504 passed 零回歸（496→+8）。飛輪雙 Workflow（探索 9-agent 翻案 S1 板列表 + Review 24-agent 4 維度對抗審，裁決可收官 0 must_fix）。nice_to_fix 高 ROI guard 已納入（params 斷言鎖根因①契約 + 降級路徑測試）。芽芽優先 0 風險（picker 未動）。**已 push origin/main（b49f9a8，rebase 疊 6/13 cron 960da5d，main↔origin 同步）**。
- **凍結後變更**：禁止；如需改，新增「Phase 110.X 補遺」章節

---

*受 17 層品質框架 v3.1 + STR1/STR10 保護。狀態：草案 v2，待阿喜凍結。*
*建立 2026-06-13｜v1 飛輪版 → Workflow 9-agent 深探 + Claude 交叉驗證 4 承重點後重排為 v2（收編 #2/#4/#3、棄 #1、S3 降最後手段），未動工。*
