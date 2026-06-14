# Phase 119 — 整站重設計 ②報告視覺重構 + token-lint 上線（草案 v1，待阿喜核准）

> 狀態：**v2 已凍結（2026-06-15，阿喜核准 + §A scope 拍板 + 🌀飛輪升級三項；M1/M2 PASS；交接新視窗執行）**
>
> **🌀 飛輪 v2 升級（阿喜 2026-06-15「直接飛輪優化」核准）**——原 v1 的 S1「tokenize 零視覺變動」全靠肉眼=綠燈假象弱點（B-023/024/025/027 同源），v2 加 machine gate + 補架構盲點：
> 1. **tokens 改 generator 注入 inline（LINE-safe，補盲點/必修）**：mockup 能 link `../tokens.css` 是本機 server；**live report 送進 LINE WebView 若 link 外部 css 抓不到會整份裸奔**。改成 generator render 時讀 `design-system/tokens.css` 注入 report `<style>`（tokens.css 仍唯一真相源、產出 inline）。
> 2. **computed-style 指紋 diff gate（殺綠燈假象）**：S1 tokenize 後 render report 前後 dump 關鍵元素 getComputedStyle→JSON 比對，**必須完全相同**（tokenize 定義＝零視覺變動）；抓漏換/換錯色。
> 3. **結構 smoke test（複用 P120/P121）**：render 後斷言 JS hook（switchRegion/openSidePanel/toggleTranslation 的 onclick）、關鍵 id、Jinja 區塊存活；延伸 P114 smoke 範式，做成可複用 harness。
> 反膨脹：render-diff 是**本機一次性非 CI**（不做重型 Playwright，P118 已定）；token-lint advisory+範圍限定不變；停損＝computed-style diff 太吵則降回截圖人工+結構 smoke。
> 戰線：**前端/UX（套用設計系統到 live）+ 治理/測試（token-lint 防復發）**——整站重設計 4-Phase 第二棒（P118 地基✅ → **P119 報告視覺+token-lint** → P120 響應式/LINE/A11y → P121 Landing）。
> 依據：P118 定案 LOOK = `design-system/variants/variant-bc.html`（B 雜誌封面 × C 霓虹玻璃）；設計決策見 `design-system/MASTER.md`；落地 punch-list 見 MASTER §6。
>
> **⚠️ 本 Phase 與 P118 最大差別：要動 live `report.html`（每天 cron 在跑的生產報告）**。所以核心策略＝**低 blast radius 分段**：先 tokenize（零視覺變動、可逐位元比對）→ 再上視覺（preview 逐步驗）→ token-lint advisory（不阻斷報告）。不碰 `generator.py` 渲染邏輯 / Jinja 資料流 / cron / 後端。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P119（整站重設計 2/4）|
| **Phase 名稱** | 報告視覺重構 + token-lint 上線 |
| **影響半徑** | **重大（report.html 大改 + tokens 接入 + check_design_tokens.py + governance_config.yaml + 測試；10+ 改動點）─ META3** |
| **預估投入** | 5-8 h（分段，preview 驗證佔比高）|
| **負責模型** | Opus 4.8（動 live 生產檔 + 不可逆風險 + 大重構）|
| **後續 Phase** | P120 響應式/LINE/A11y｜P121 Landing |

---

## 1. 目標 (Objective)

把 P118 定案的 `variant-bc` 設計語言**套到 live `report.html`**，並讓硬編碼設計值**機器化防復發**：

1. **tokens 注入 inline（🌀v2 改）**：generator render 時讀 `design-system/tokens.css` 注入 report `<style>`（**非 link 外部檔，LINE-safe**）；report.html 硬編碼 `#hex`/主間距 px 換 `var(--token)`、`:root` 對映 tokens。
2. **視覺重構**：套 variant-bc 的霓虹玻璃**質感層**（玻璃卡/發光/mesh/發光數字/編輯式標題），**保留現有 report 結構骨架 + 全部功能**（戰力面板/音訊/區域導覽/圖表/警示/側欄…一個不刪，§A1=套質感保骨架）。
3. **熱詞 #1**：**保留藍色**（阿喜 S4 拍板）——只把既有藍 `#1e3a5f→#2563eb` tokenize 成 `var(--hot-tag-bg)` + 加 cursor/hover/focus affordance。**修正 MASTER §6 punch-list #1「重寫成粉」＝過時，以本條為準。**
4. **token-lint 上線**：`scripts/check_design_tokens.py` flag report.html 殘留硬編碼 → 註冊進 `governance_config.yaml` 的 `full` profile（**advisory，不阻斷報告**）。
5. **🌀computed-style 指紋 gate（v2）**：S1 tokenize 後 render report 前後 dump 關鍵元素 getComputedStyle→JSON 比對**必須完全相同**（機器證明零視覺變動、抓漏換/換錯色）。
6. **🌀結構 smoke harness（v2，複用 P120/P121）**：`tests/test_report_structure.py` render 後斷言 JS hook（onclick）/關鍵 id/Jinja 區塊存活。
7. **preview 驗證**：375 / 768 / 1440 + LINE WebView UA 截圖比對（截圖 MCP 故障時用 Edge headless CLI）。

量化：report.html 硬編碼設計值大幅 token 化（token-lint 命中數降到目標門檻）；視覺對齊 variant-bc；**daily cron 報告零功能回歸**。

## 2. 觸發背景 (Why Now)

P118 已產設計系統 + 阿喜定案 LOOK，但**外觀真正改變在 P119 才上線**（P118 純 sandbox）。設計債（#1/#3）的根因是硬編碼無機器守護 → 必須 tokenize + token-lint 才算「不壞」（飛輪脊椎）。趁設計語言剛定案、記憶新，一次落地。

## 3. Entry Criteria

- [x] P118 收官、LOOK 定案（variant-bc）、tokens.css 凍結（commit a521d5c）
- [x] MASTER §6 P119 補帳 punch-list 就緒
- [x] 阿喜核准本計畫書凍結 + §A scope 拍板（2026-06-15：A1=套質感保骨架/A2=report only/A3=advisory）
- [ ] 動工前 snapshot 一份 live report.html（X1 可逆回退點）← **新視窗 S0 第一件事**

### §A scope 決策（✅ 阿喜 2026-06-15 拍板，全採建議）
| # | 決策 | **拍板** |
|---|---|---|
| A1 | 視覺力度 | ✅ **(b) 套質感層保骨架**——保留現有 report 結構/功能不動，只套 variant-bc 質感（色/玻璃/光暈/mesh/熱詞/間距/字級）。中改、低風險、**功能零搬遷**（Exit B 硬條件）|
| A2 | 範圍 | ✅ **report.html only**（index.html=Landing 留 P121）|
| A3 | token-lint 嚴格度 | ✅ **advisory**（warn 不擋報告；穩定後再議升 strict）|

## 4. Exit Criteria

- [ ] **A（🌀v2 inline）**：generator render 時注入 tokens.css 到 report `<style>`（**非 link，LINE-safe**）；硬編碼 `#hex`/主間距 px 換 `var(--token)`，token-lint 命中數 ≤ 目標門檻
- [ ] **B**：視覺對齊 variant-bc 質感（玻璃/光暈/mesh/發光數字/編輯式標題）；**熱詞保留藍色** + 可點 affordance（#1）；**全功能保留零刪**
- [ ] **C**：`scripts/check_design_tokens.py`（flag report.html 硬編碼）+ 註冊 governance_config.yaml `full` profile（advisory）+ 測試
- [ ] **D（preview 驗證）**：375/768/1440 + LINE WebView UA 截圖；對照 P117 截圖確認**功能/版面零破壞**
- [ ] **E（生產零回歸）**：dry-run 或 replay 跑 generate() 產出 report.html 成功、所有 Jinja 區塊正常渲染、既有測試零回歸
- [ ] **G（🌀v2 computed-style gate）**：S1 tokenize 前後 report 關鍵元素 getComputedStyle 指紋**完全相同**（機器證明零視覺變動）；harness 可複用 P120/P121
- [ ] **H（🌀v2 結構 smoke）**：`tests/test_report_structure.py` 斷言 JS hook（switchRegion/openSidePanel/toggleTranslation onclick）/關鍵 id/Jinja 區塊 render 後存活
- [ ] **F**：收官件套（TASK_HISTORY + memory + postmortem 若觸發）+ P120 預告

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 5-8 h |
| 收益 | **高**（設計系統真正上線＝阿喜看到報告變美；token-lint 防 #1/#3 類債復發）|
| 風險 | **中-高**（動每天在跑的生產報告）→ 用分段 tokenize-first + preview 驗 + snapshot 回退壓低 |

---

## 6. 17 層稽核表 ─ META2

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | report.html 硬編碼→token；新增 check_design_tokens.py | 2100 行大檔改錯/漏改 | 分段 tokenize（先色後間距）、每段 preview 比對、git diff 逐塊審 |
| **2. 邏輯** | 不碰 generator.py 渲染邏輯/Jinja 資料流，只動 CSS/標記 | 改 HTML 結構誤傷 Jinja 變數/JS 選擇器 | 保留所有 class 名/id/data-* 與 Jinja `{% %}`；改樣式不改資料綁定 |
| **4. 測試** | token-lint 機械驗硬編碼；既有測試零回歸；preview 截圖 | 視覺無法單元測 | token-lint + generate() 端到端產出驗 + 既有 pytest 全套 + preview 三寬 |
| **10. 安全** | 純前端樣式 + advisory checker；零後端/機敏 | 引入外部 CDN？ | 字體沿用既有 Google Fonts；不引未知第三方；token-lint 純本地讀檔 |

### A 級（提示填）
| 層 | 採用/N-A | 風險 | 緩解 |
|---|---|---|---|
| **3. 架構** | tokens.css 單一真相源接入 live（消除雙軌漂移）| report 自帶 :root 與 tokens 衝突 | report :root 改為引用/對映 tokens；保留必要 report 專屬變數 |
| **6. 可觀察性** | token-lint 進 gov.preflight full（advisory）| 太吵/誤報 | 範圍限色值+主間距，微尺寸豁免（MASTER §4 明文）；advisory 先觀察 |
| **9. UX（核心）** | 套 variant-bc 質感、#1 affordance、#3 間距 | 真實資料撐爆/功能擠壓 | preview 用真實 generate() 產出驗（非 mockup 假資料）|
| **13. 可維護性** | 全站 token 化、token-lint 守護 | — | MASTER 文件化；lint 防 re-creep |
| **14. 文件** | 計畫書+MASTER 更新+TASK_HISTORY | — | 收官件套 |
| **15. 流程** | 4-Phase 第二棒；preview gate + dry-run gate | — | 每段驗證、snapshot 回退 |

### B 級（條件式）
| 層 | 觸發 | 採用 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能** | mesh/glow/blur 多層 | 行動版降規（既有 mobile 關 backdrop-filter）| 低階機卡頓 | 沿用 report 既有 mobile 降規策略；glow 用 box-shadow 非昂貴濾鏡 |
| **11. 部署** | 改 daily_report.yml? | 否（token-lint 走 gov.preflight 既有 step）| — | 不新增 CI step，復用 P117 總指揮 |
| **17. i18n** | 中文報告 | 行高/字體 token 對中文友善 | — | --leading-normal 1.6 + Noto Sans TC |

### 層級互鎖 ─ META5
- [x] UX→Documentation｜[x] Architecture→Documentation｜[x] Logic→Testing（動 report 結構→generate() 端到端驗 + 既有測試）

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| 改 report.html | **半可逆**（生產檔；動工前 snapshot + git）| 動工前存 `backups/report_before_p119.html` + git diff 可還原 |
| 新增 check_design_tokens.py / 註冊 config | 可逆（advisory，git rm/還原 yaml）| — |
| token-lint 進 gov.preflight | 可逆（advisory 不擋）| — |

### X2 盲區掃描
- [ ] tokenize 改錯色值 → 每段 preview 逐位元比對 + dry-run 產出驗
- [ ] 改 HTML 誤傷 JS 選擇器（switchRegion/openSidePanel/toggleTranslation 等）→ 保留所有 id/class/onclick；改後 preview 點測互動
- [ ] mockup 質感套到真實資料密度撐爆 → preview 用真 generate() 產出（非假資料）
- [ ] 改動破壞 cron 報告 → dry-run/replay 端到端 gate；snapshot 回退

### X3 時間敏感性
- 草案 2026-06-15；依 variant-bc（2026-06-15 快照）落地；token-lint 門檻隨落地進度調整

### X4 多角度審查
- **主公**：阿喜要報告變美但功能不能壞、熱詞保留藍。建議 scope (b)：套質感保骨架。
- **紅隊**：見 M2。
- **接手者**：tokens.css 單一真相源 + token-lint 守護；report :root 對映 tokens 有文件。
- **X4-J 自動化邊界**：token-lint advisory（啟發式、僅 warn）；視覺最終人工 preview 簽核。
- **X4-K 使用者端審查官**：明告 P119 上線後報告外觀才真改變；功能零變動。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| RP1 | tokenize/視覺改動誤傷 Jinja 變數或 JS 選擇器→cron 報告壞 | 中 | **高** | 邏輯/部署 | 保留所有 class/id/onclick/`{% %}`；分段改；每段 preview 互動點測 + dry-run 端到端 gate |
| RP2 | 漏改/改錯硬編碼，視覺花掉 | 中 | 中 | UX | token-lint 機械抓殘留；preview 三寬比對 |
| RP3 | variant-bc 雜誌版型硬搬，功能擠不進/被刪 | 中 | 高 | UX/流程 | scope (b) 套質感保骨架（建議）；功能零刪為 Exit B 硬條件 |
| RP4 | mesh/glow 多層在低階機/LINE WebView 卡頓 | 低 | 中 | 效能 | 沿用 report 既有 mobile 降規；P120 正式做 LINE |
| RP5 | token-lint 太吵→淪為噪音被忽略 | 中 | 低 | 治理 | 範圍限色+主間距，微尺寸豁免；advisory 先觀察，穩定再議 strict |
| RP6 | report 自帶 :root 與 tokens.css 雙軌衝突 | 中 | 中 | 架構 | report :root 改為對映/引用 tokens；保留必要專屬變數，文件化 |
| RP7 | **（🌀v2 揭露盲點）** tokens 用 link 外部檔，report 送進 LINE WebView 抓不到 css→整份裸奔無樣式 | 中 | **高** | 架構 | generator render 時**注入 tokens inline** 到 `<style>`（非 link）；S4 LINE UA preview 實測樣式正常 |
| RP8 | computed-style 指紋 diff 因 antialiasing/font 渲染太吵→誤報 | 低 | 低 | 測試 | 取 getComputedStyle（解析後值，非像素）較確定性；停損＝太吵降回截圖人工+結構 smoke |

**META4 加權**：RP1/RP3/RP7 高影響（動生產報告 + LINE 裸奔）→ **加權 ≥5，動工前須阿喜確認 §A scope（已拍板）+ snapshot 回退點 + 🌀computed-style gate 守 tokenize**。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 驗收 |
|---|---|---|
| **S0 前置 + harness（🌀v2）** | snapshot report.html→backups/；建 `scripts/report_visual_diff.py`（render report dry-run→dump 關鍵元素 computed-style JSON）+ `tests/test_report_structure.py`（JS hook/id/Jinja 區塊存活）；token-lint PoC 量基線硬編碼數；**先存改前 computed-style 指紋 + 結構基線** | snapshot + harness 可跑 + 改前指紋/結構基線存檔 |
| **S1 tokenize（零視覺變動，🌀machine gate）** | generator 注入 tokens.css inline 到 `<style>`（非 link）；`:root` 對映 tokens；硬編碼 `#hex`/主間距→`var()` | **computed-style 指紋與 S0 改前完全相同**（機器證零變動，抓漏換/換錯）+ token-lint 命中降 |
| **S2 視覺質感層** | 套 variant-bc 質感（玻璃/光暈/mesh/發光數字/編輯式標題）；**熱詞 tokenize 藍+affordance（#1）**；間距走 scale（#3）。功能零刪 | preview 三寬對齊 variant-bc；**結構 smoke 全綠**（改動沒誤傷功能）；互動點測 OK |
| **S3 token-lint** | check_design_tokens.py + 註冊 governance_config.yaml full（advisory）+ 測試 | lint 命中數 ≤ 門檻；gov.preflight full 含此 check |
| **S4 端到端驗證** | generate()/replay 產 report 成功；既有 pytest + 新 test_report_structure 全套；preview 375/768/1440+LINE UA（驗 inline tokens 在 LINE 不裸奔）| 零功能回歸 + LINE 樣式正常 + 截圖存證 |
| **S5 收官** | TASK_HISTORY + memory + postmortem（若觸發）+ P120 預告（含 harness 複用） | 件套齊 |

---

## 10. 影響檔案清單 ─ STR7

**改**：`reporter/templates/report.html`（tokenize + 視覺質感）、`reporter/generator.py`（**🌀v2 唯一允許改動＝render 時讀 tokens.css 注入 `<style>` 的純 additive，不碰資料流/渲染邏輯/exit code**）
**新增**：`scripts/check_design_tokens.py`（token-lint）、`scripts/report_visual_diff.py`（🌀computed-style 指紋 diff harness）、`tests/test_design_tokens.py`、`tests/test_report_structure.py`（🌀結構 smoke）、`backups/report_before_p119.html`
**改（治理）**：`governance_config.yaml`（註冊 token-lint 進 full profile，advisory）
**不碰**：`reporter/generator.py` **資料流/渲染邏輯/exit code**（僅允許上述 tokens 注入 additive）、Jinja 資料綁定、`daily_report.yml`、cron、後端、`index.html`（P121）
**已存在依賴**：`design-system/tokens.css`（P118，唯一真相源）

---

## 11. Postmortem 預埋點 ─ G6

位置：`docs/postmortems/2026-XX-XX-phase-119-report-restyle.md`（若觸發，尤其 RP1 cron 報告破壞）

> **通則1（生產檔改動先 tokenize 再視覺）**：動每天在跑的生產報告，先做「零視覺變動的 tokenize」逐位元驗證，再疊視覺層 preview 驗——把「改錯」與「改醜」兩類風險拆開、各自有獨立 gate。
> **通則2（設計系統落地必配 lint）**：tokens 接入 live 同時上 token-lint（advisory），否則硬編碼會再 creep（#1/#3 即此下場）。
> **通則3（保功能優先於搬版型）**：把 sandbox mockup 套進功能豐富的真模板時，優先套「質感層」保骨架，不為了版型一致而刪/擠功能。
> **通則4（🌀零視覺變動要機器證明，不靠肉眼）**：「tokenize 不改外觀」這種宣稱是綠燈假象高發區——用 render 前後 computed-style 指紋 machine-diff 證明「完全相同」，比 git diff/肉眼強；harness 做成可複用，攤提到後續同類 Phase。
> **通則5（🌀產出物的執行環境決定接入方式）**：設計系統 link vs inline 不是品味問題——report 的真實環境是 LINE WebView（抓不到外部 css 會裸奔），故 tokens 必須 render 時 inline 注入；mockup 能 link 是因為本機 server，別把 sandbox 的接入方式直接搬上 live。

---

## ✈️ Pre-flight 多視角體檢 ─ STR10

### M1 強制填表（十一視角）
| 視角 | 發現 |
|---|---|
| **X4-A 紅隊** | 見 M2。核心：改生產報告壞 cron（snapshot+dry-run gate）、硬搬版型刪功能（scope b 保骨架）、JS 選擇器誤傷（保 id/class/onclick）、token-lint 太吵（範圍限定+advisory）。 |
| **X4-B 接手者** | tokens.css 單一真相源 + token-lint 守護 + report :root 對映文件化；後續 P120/P121 同依據。 |
| **X4-C 災難** | 最壞＝cron 報告渲染壞 → snapshot 回退 `backups/report_before_p119.html` + git revert，分段改使 blast radius 小。 |
| **X4-D 5 年後** | 全站 token 化 + lint＝未來改版有依據、債不復發。 |
| **X4-E 終端 vs IDE** | 本地 Edit + Edge headless 出圖；無終端互動。 |
| **X4-F 跨平台** | preview 375/768/1440 + LINE WebView UA（B-020）；mesh/glow 行動版降規。 |
| **X4-G 主公視角** | 報告變美但功能零壞、熱詞保藍。scope (b) 套質感保骨架最穩。 |
| **X4-H 觀測/治理** | token-lint 進 gov.preflight full（advisory）可追溯硬編碼 re-creep。 |
| **X4-I 主公可見性** | P119 上線後報告外觀才真變；明告功能不動。 |
| **X4-J 自動化邊界** | token-lint advisory 僅 warn；視覺人工 preview 簽核。 |
| **X4-K 使用者端審查官** | 誤解「會不會把功能改不見」→ Exit B 硬釘功能零刪 + dry-run 端到端驗。 |

### M2 紅藍對抗（≥5 條，≥2 S 級）
| # | 紅隊質疑 | 攻擊力 | 藍隊回應 | 處置 |
|---|---|---|---|---|
| 1 | **【S】** 改 2100 行 live report.html 誤傷 Jinja 變數/JS 選擇器，cron 隔天報告壞掉、使用者看到破版？ | S | 保留所有 class/id/data-*/onclick/`{% %}`，只改樣式不改資料綁定；分段改；每段 preview 互動點測 + **dry-run/replay 端到端 gate**（產出成功才算過）；snapshot 回退。 | 入計畫（RP1+S1/S4/Exit E）|
| 2 | **【S】** 為了套 variant-bc 雜誌版型，把戰力面板/音訊/圖表等功能擠掉或刪掉？ | S | **scope (b)：套質感層保骨架**，功能零刪為 **Exit B 硬條件**；variant-bc 只借色/玻璃/光暈/熱詞/間距/字級語言，不硬搬 5-post 版型。 | 入計畫（RP3+§A1）|
| 3 | tokenize 改錯色值，報告變花但測試抓不到（視覺無單元測）？ | A | S1「零視覺變動」逐位元/視覺比對 + token-lint 機械抓殘留 + preview 三寬。 | 入計畫（RP2/S1）|
| 4 | token-lint 太吵（每個 px 都報）→ 被忽略成噪音？ | A | 範圍限色值+主間距，微尺寸豁免（MASTER §4 明文）；advisory 先觀察，穩定才議升 strict。 | 入計畫（RP5/A2）|
| 5 | report 自帶 :root 與 tokens.css 雙軌，改一邊另一邊沒同步→漂移？ | A | report :root 改為**對映/引用** tokens（消除雙軌），保留必要專屬變數並文件化。 | 入計畫（RP6）|
| 6 | mesh/glow 多層在 LINE WebView/低階機卡頓？ | B | 沿用 report 既有 mobile 降規（關 backdrop-filter）；glow 用 box-shadow；P120 正式做 LINE WebView 驗。 | 入計畫（RP4）|
| 7 | **【S，🌀v2 揪出】**「tokenize 零視覺變動」全靠肉眼=綠燈假象（B-023/024/025/027 同源），漏換/換錯色測試抓不到、cron 報告悄悄花掉？ | S | **computed-style 指紋 machine-gate**：render 前後 dump getComputedStyle JSON 必須完全相同，機器證明零變動、抓換錯。harness 複用 P120/P121。 | 入計畫（RP2/Exit G/S1）|
| 8 | **【S，🌀v2 揪出】** tokens 用 link 外部 css，report 送進 LINE WebView 抓不到→整份裸奔，使用者看到無樣式報告？ | S | generator render 時**注入 tokens inline** 到 `<style>`（非 link）；S4 LINE UA preview 實測。 | 入計畫（RP7/Exit A）|

> 未解質疑：無（§A scope 阿喜已拍板；飛輪三項已折入 v2）。

---

## 12. 凍結戳記（待填）

- **凍結人**：阿喜核准（2026-06-15，§A scope 拍板 + 🌀飛輪 v2 三項）+ Claude（Opus 4.8 1M）
- **凍結時間**：2026-06-15（v1 凍結 → 同日飛輪升級 v2 凍結）
- **凍結依據**：lint M1/M2 PASS + 阿喜核准 §A scope（A1=套質感保骨架 / A2=report.html only / A3=advisory）+ 🌀飛輪三項（tokens inline 注入 / computed-style gate / 結構 smoke harness）+ P118 LOOK 已定案（variant-bc）
- **執行**：交接新視窗（本對話極長，context 衛生）；下個視窗讀 `docs/PHASE_119_HANDOFF.md` + 本計畫書 + `design-system/MASTER.md` + `design-system/variants/variant-bc.html` 即可動工 S0-S5

---

*狀態：草案 v1，待阿喜核准 + §A scope 拍板。受 17 層框架 v3.1 + STR10 保護。整站重設計 2/4。建立 2026-06-15（P118 收官後）。*
