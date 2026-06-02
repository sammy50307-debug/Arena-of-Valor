# Phase 107 — 焦點英雄爬取覆蓋修復（Dcard 治本 + HERO_FOCUS_KEYWORDS 接線 + 防復發飛輪）

> **狀態**：DRAFT（草案，凍結前須過 M1 + M1.5 + M2 體檢，建議 `lint-phase-plan` 驗）
> **日期**：2026-06-02
> **提案**：阿喜（P106.1 run-now 後質疑「0 篇芽芽、尤其 Dcard」）
> **模型**：規劃 Opus 4.8；機械改動 Sonnet 4.6；Dcard 繞 Cloudflare PoC 用 Opus
> **影響半徑**：🔴 重大（scrapers 多檔 + main.py + config + tests + checker + manifest + docs ≥ 10 檔）→ **全 17 層稽核**
> **命名**：P107（主）/ P107.1、P107.2…（子階段）

---

## 0. 觸發與證據（Evidence）

P106.1 正式跑流程（2026-06-02 run-now，commit 15dfd2a 後）阿喜質疑芽芽 0 篇不合理。Opus 端到端調查（讀 raw_20260602.json + 三主力爬蟲原始碼）證實**不是判定 bug，是爬取層四根因**：

| # | 根因 | 證據（檔案:行號 / 資料）|
|---|---|---|
| **A** | `HERO_FOCUS_KEYWORDS` 是 dead config，未接入任何爬蟲 | grep 全專案僅 config.py:123 定義；main.py:315 搜集用 `REGIONAL_KEYWORDS`；Tavily:86 自讀 `REGIONAL_KEYWORDS` |
| **B** | 三平台都不抓全文內文，content 只有標題 | Dcard:122 `content=title+後綴`；巴哈:162 `title+回覆數`；Tavily:140 `include_raw_content=False`（僅 snippet）。raw 實測 Dcard content 39–76 字 |
| **C** | `detected_heroes` 只有 Tavily 做，Dcard/巴哈沒設 | Tavily:156-159 掃 title+content；Dcard:120 / 巴哈:160 的 SearchResult 未傳 detected_heroes → raw 19 篇全空 |
| **D** | `keyword not in title` 過濾扼殺多詞 keyword | Dcard:116 / 巴哈:129,187 要求標題含完整關鍵字 → 「芽芽 配裝」幾乎不可能完整現於標題 |

**關鍵洞察**：Tavily:123-125 已寫好焦點英雄「意圖注入」（keyword 含芽芽 → 自動加 `(評價 OR 攻略 OR 配裝…)`），但因根因 A **從未觸發**。基礎建設已存在，只差接線。

**既有可複用資產（飛輪善用）**：
- `waterfall-search-chain`（P56）：Tavily→DDG 瀑布鏈，main.py 在用
- `auto-proxy-evader`（P48）：UA 輪替+指數退避+重試，防 **403/429**（⚠️ 非 Cloudflare JS challenge，見 M2-Q3）
- `api-quota-guardian`（P57）：Tavily 額度守衛，已整合
- `apify_scraper.py`：Apify IG 爬蟲（抓 caption 真內文），證明 **Apify 平台能抓深度內文** → Dcard 可能有對應 Actor

---

## 0.5 戰線分類（飛輪 #1）

| 戰線 | 本 Phase 涉及 | 說明 |
|---|---|---|
| 爬取層（資料源）| ✅ 主戰場 | HERO_FOCUS_KEYWORDS 接線、Dcard Cloudflare 繞過、各平台內文抓取、keyword 過濾放寬 |
| 資料層 | ✅ | content 完整度、detected_heroes 偵測有效性 |
| 治理層 | ✅ | 防復發 guard（checker/test/monitor）+ 記憶落點 |
| 報告呈現層 | ❌ N/A | P106.1 已處理（placeholder）；本 Phase 不動報告模板 |
| 部署層 | ⚠️ 部分 | Dcard 若用 Apify 需 APIFY_TOKEN secret（雲端），列 X1 不可逆確認 |

**與 P106.1 關係**：P106.1 芽芽空態 placeholder 是**治標**（空了好看）；P107 是**治本**（讓芽芽不再無謂地空）。placeholder 保留（真的某日無芽芽文時仍需要）。

---

## 1. 目標：最終不壞 / 可修復（飛輪 #2）

1. **芽芽（焦點英雄）每日穩定覆蓋**——不再靠泛搜碰運氣，HERO_FOCUS_KEYWORDS 確實驅動搜尋。
2. **Dcard 修到順利爬取**（阿喜核心要求）——抓到**內文**（非只標題），芽芽內文討論判得出。
3. **detected_heroes 偵測有效**——各平台貼文的英雄偵測不再全空。
4. **防復發**——未來若爬取覆蓋退化（HERO_FOCUS_KEYWORDS 斷線 / content 退回只標題 / detected_heroes 全空 / 焦點英雄覆蓋率歸零），有 machine guard **自動告警**，不靠人肉發現。

**成功條件（可觀察）**：見 §5 Exit Criteria。

---

## 2. 三方案：快修 / 穩修 / 飛輪修（飛輪 #3）

| 方案 | 範圍 | ROI | 風險 |
|---|---|---|---|
| **快修** | Tavily 搜集加掛 `HERO_FOCUS_KEYWORDS`（啟動既有意圖注入）；main.py / Tavily.search 各加一處 | 🟢 高/低 | 額度小增；不解 Dcard 內文 |
| **穩修** | 快修 +（a）Tavily `include_raw_content=True` 拿全文（b）Dcard/巴哈補 detected_heroes 標題層偵測（c）放寬 keyword 過濾（多詞 OR/部分匹配，焦點英雄豁免）| 🟡 中/中 | 額度↑token↑；過濾放寬可能引雜訊 |
| **飛輪修**（本 Phase 採用）| 穩修 +（d）**Dcard 治本**：Apify Dcard Actor PoC / 強化繞 Cloudflare（e）**防復發 guard**：checker+test+manifest+monitor（f）**記憶落點**：docs+postmortem+RISK+blindspot | 🔴 高/高 | Dcard 繞 Cloudflare 不保證成功（見停損 §7）|

**阿喜裁定**：採飛輪修，Dcard 為核心目標。

**子階段切分（建議）**：
- **S0 前置確認**：查 analyzer 是否有二次英雄偵測（影響 C 修法範圍）；查 Apify 是否有 Dcard Actor（決定 D-Dcard 路徑）
- **S1 快修**：HERO_FOCUS_KEYWORDS 接線（Tavily）+ 驗證芽芽撈回
- **S2 穩修**：内文抓取（Tavily raw）+ detected_heroes 補做 + keyword 過濾放寬
- **S3 Dcard 治本**：Apify Dcard Actor 或繞 Cloudflare PoC（停損條款）
- **S4 防復發飛輪**：checker + test + manifest 欄位 + monitor + 記憶落點
- **S5 治理收官**：TASK_HISTORY + postmortem + R-027 + blindspot

---

## 3. 17 層稽核表（全層；S/A/B）

| # | 層 | 級 | 本 Phase 動作 / 風險 |
|---|---|---|---|
| 1 | 代碼 | S | 爬蟲改動小批次、surgical；新增 helper 不重寫架構 |
| 2 | 邏輯 | S | keyword 過濾放寬不能誤殺（焦點英雄豁免）；意圖注入觸發條件正確 |
| 3 | 架構 | A | 爬蟲 SearchResult 契約一致；新增 detected_heroes 不破既有欄位 |
| 4 | 測試 | S | 每根因配 anti-regression test（A 接線/B 內文長度/C 偵測/D 過濾）|
| 5 | 資料 | A | content 完整度提升；manifest 加覆蓋率欄位；raw 向後相容 |
| 6 | 可觀察 | A | manifest focus_hero_post_count / detected_heroes_total / content_avg_len；monitor 告警 |
| 7 | 韌性 | A | Dcard 繞 Cloudflare 失敗要 graceful（不崩 pipeline）；waterfall/proxy-evader 複用 |
| 8 | 效能 | B | include_raw_content + Apify 增加耗時/額度，需評估（X4-C）|
| 9 | UX/A11y | B | N/A（不動報告呈現）|
| 10 | 安全 | S | APIFY_TOKEN 只進 .env/secret；爬蟲 UA 偽裝合規；不爬非公開內容；尊重 robots/ToS |
| 11 | 部署 | B | Apify 需雲端 APIFY_TOKEN secret（X1 不可逆，阿喜確認）|
| 12 | 成本 | B | Tavily raw content + Apify 燒額度，列預算上限 + guardian |
| 13 | 可維護 | A | 各子階段獨立 commit；爬蟲改動有註解溯源 |
| 14 | 文件 | A | 本計畫書 + postmortem + RISK + 爬蟲 README 更新 |
| 15 | 流程 | A | Entry/Exit 明文；飛輪六件事；M1/M2 體檢 |
| 16 | 隱私 | B | 只爬公開貼文；不存個資；遵守平台 ToS（X4-A 紅隊覆核）|
| 17 | i18n | B | N/A（焦點台服繁中）|

---

## 4. Pre-flight 多視角體檢（STR10：M1 + M1.5 + M2）

### M1 強制填表（十一視角，每項 ≥ 20 字元）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | 爬蟲偽裝 UA 規避 WAF 屬灰色；須確認只爬公開頁、遵守 ToS/robots，避免 IP 被永 ban 或法務風險；APIFY_TOKEN 外洩可被盜刷額度；繞 Cloudflare 勿觸法 |
| **X4-B 接手者** | 半年後接手者須能從 manifest 覆蓋率欄位 + checker 一眼看出爬取是否健康；爬蟲改動需註解溯源根因 A-D |
| **X4-C 災難情境** | 情境：Apify/Tavily raw 燒爆額度或 Cloudflare 永封 IP / 緩解：budget guardian 上限 + 失敗 graceful 降級 + 不無限重試 |
| **X4-D 5 年後** | Dcard/巴哈頁面結構會改版使 selector 失效；checker 須偵測「content 長度驟降/detected_heroes 歸零」及早告警，不靠人肉 |
| **X4-E 終端 vs IDE** | 爬蟲 PoC 在終端 `py` 跑（非 IDE）；Apify 需網路，IDE 內建終端可能 proxy 干擾 |
| **X4-F 跨平台** | UA 池/退避純 Python 跨平台；Apify SDK 與 httpx 在 Win/Mac/Linux 一致；注意 Windows 編碼（scraper 已有 reconfigure utf-8）|
| **X4-G 主公個人視角** | 阿喜要的是「芽芽真的被抓到、Dcard 順利爬」，不是表面數字；驗收須看真實芽芽文出現於報告，非只測試綠 |
| **X4-H 觀測/治理** | 新增 checker + manifest 覆蓋率欄位 + monitor 為治理核心；advisory 起步、穩定後評估 strict gate |
| **X4-I 主公可見性** | 爬蟲 UA 偽裝、Apify 雲端爬蟲、額度消耗 阿喜看不到 → 須在 manifest/log 攤開實際 provider、Apify 命中、額度餘量 |
| **X4-J 自動化工具邊界** | checker 用「字面比對」判覆蓋（content 長度/detected_heroes 計數/焦點英雄出現）為啟發式，有 false-negative（標題剛好含芽芽但無內文）；CLI 末行須印免責邊界 |
| **X4-K 使用者端審查官** | 風險：報告顯示「芽芽動態」但其實是泛搜剛好撈到、非真芽芽深度討論 → 須確保 detected_heroes 真實反映內文，不製造虛假焦點覆蓋 |

### M1.5 八人格顧問團（至少 Ken 紅隊必看）

| 人格 | 觸發 | 關注 |
|---|---|---|
| **Ken 型紅隊/技術長** | 固定必看 | 爬蟲 ToS/法務邊界、APIFY_TOKEN secrets、繞 Cloudflare 合規性、額度濫用、不可逆（IP ban）|
| 資料/數據顧問 | 觸發 | content 完整度、detected_heroes 召回率、覆蓋率指標可信度 |
| 維運顧問 | 觸發 | selector 易碎、頁面改版偵測、failure graceful |

### M2 紅藍對抗（≥5 質疑，≥2 S 級；未解入 RISK_REGISTRY）

| # | 紅隊質疑 | 攻擊力 | 藍隊回應 | 處置 |
|---|---|---|---|---|
| 1 | **接了 HERO_FOCUS_KEYWORDS 但 Dcard/巴哈 content 只標題，搜到芽芽文仍判不出** | **S** | 快修只解 Tavily（有 snippet）；Dcard/巴哈須穩修補內文或標題層偵測；S1 驗收須分平台看 | 入計畫 S2/S3；列 Exit |
| 2 | **Dcard 繞 Cloudflare PoC 可能失敗（proxy-evader 只防 403/429 非 JS challenge）** | **S** | 不保證成功；§7 停損條款明定失敗則降級 Dcard 標題層 + 強化 Tavily/巴哈內文，不無限投入 | 入 RISK R-027 + 停損 §7 |
| 3 | keyword 過濾放寬可能引入雜訊（非芽芽文混入焦點）| A | 焦點英雄走 detected_heroes 精準判定 + 黑名單仍生效；放寬僅對 HERO_FOCUS_KEYWORDS 子集 | 入計畫 S2 測試 |
| 4 | Tavily include_raw_content + Apify 燒爆額度（6/5 對賭額度有限）| A | budget guardian 上限 + Apify 快取（同英雄同日不重爬）+ 列預算停損 | 入計畫 S2/S3 預算停損 |
| 5 | 爬蟲 UA 偽裝/繞 Cloudflare 觸犯平台 ToS、法務或 IP 永 ban | **S** | 只爬公開頁、遵守 robots、合理速率；Ken 紅隊覆核；不可逆 IP ban 列 X1 | 入 RISK R-027（Ken 覆核）|
| 6 | detected_heroes 補做後召回仍受限於資料（只標題）→ 製造虛假覆蓋率 | A | checker 區分「標題層偵測」vs「內文層偵測」；覆蓋率指標標註信賴邊界（X4-J/K）| 入計畫 S4 checker |

**S 級攻擊 3 條（#1/#2/#5）達標（≥2）。未解質疑 #2/#5 → 凍結時入 RISK_REGISTRY R-027。**

---

## 5. Entry / Exit Criteria

### Entry（入口，動工前須滿足）
- [ ] 本計畫書過 M1+M1.5+M2 體檢（`lint-phase-plan` 綠）
- [ ] 阿喜核准凍結；S3 Dcard 繞 Cloudflare 路徑（Apify vs proxy）阿喜選定
- [ ] APIFY_TOKEN 可用性確認（若走 Apify 路）

### Exit（退出，收官須滿足）
- [ ] **S1**：HERO_FOCUS_KEYWORDS 接入搜集，真實跑驗證芽芽文撈回（report 出現真芽芽內容）
- [ ] **S2**：Tavily 內文抓取生效（content 不再只標題）；Dcard/巴哈 detected_heroes 非全空
- [ ] **S3**：Dcard 抓到內文（順利爬取達標）**或** 停損降級已明文記錄並阿喜確認
- [ ] **S4**：checker `check_crawl_coverage.py` 上線（detected_heroes 全空 / content 只標題 / 焦點覆蓋率 0 → 告警）；anti-regression test 全綠
- [ ] 全套測試不退（現 406 baseline）；零回歸
- [ ] manifest 新增覆蓋率欄位；daily monitor 接入
- [ ] TASK_HISTORY + postmortem + R-027 + blindspot 落地

---

## 6. 飛輪記憶落點：防復發（飛輪 #5；阿喜「以後不要再犯」）

| 落點 | 內容 | 防的復發 |
|---|---|---|
| **docs** | 本計畫書 + `docs/postmortems/P107_*.md`（根因：dead config + 只標題的連鎖失效）| 根因被遺忘、未來重蹈 |
| **RISK_REGISTRY** | R-027（爬取覆蓋退化 / 焦點英雄覆蓋率歸零 / Dcard Cloudflare 反爬）| 已知風險失憶 |
| **tests** | `test_hero_focus_keywords_wired`（焦點詞確實接入搜集）/ `test_scraper_content_has_body`（content 非只標題）/ `test_detected_heroes_not_all_empty`（偵測有效）| 接線斷掉、content 退化、偵測失效無人知 |
| **checker** | `scripts/check_crawl_coverage.py`：掃當日 raw/analysis → detected_heroes 全空告警 / content 平均長度過短告警 / 焦點英雄覆蓋率為 0 告警（advisory 起步）| 靜默退化（如今天 0 芽芽無人察覺）|
| **config** | HERO_FOCUS_KEYWORDS 已存在；加註解「必須接入搜集，見 test_hero_focus_keywords_wired」防再變 dead config | dead config 復活 |
| **manifest** | run_manifest 加 `focus_hero_post_count` / `detected_heroes_total` / `content_avg_len` | 無歷史可追溯覆蓋率趨勢 |
| **monitor** | daily monitor 讀 manifest 覆蓋率欄位，異常 advisory 告警 | 線上退化無告警 |
| **blindspot** | B-NNN：「定義了卻沒接的 dead config」「靠泛搜碰運氣的焦點覆蓋」通則化，納入 cross-phase-review | 同類盲點跨 Phase 復發 |

---

## 7. 停損點與不做項（飛輪 #6）

**停損（Dcard 繞 Cloudflare）**：
- 若 S3 PoC 證明 Apify 無 Dcard Actor **且** proxy-evader/cloudscraper 擋不住 JS challenge → **停損**：Dcard 降級為「標題層偵測 + 加強 Tavily/巴哈內文補足焦點覆蓋」，不無限投入繞 Cloudflare。降級須明文 + 阿喜確認 + 入 R-027。
- 額度停損：Tavily raw + Apify 累計達預算上限 → 自動降級，不燒爆 6/5 對賭額度。

**明確不做（反飛輪膨脹）**：
- ❌ 不重寫整個爬蟲架構（surgical，只接線 + 補偵測 + 治本 Dcard）
- ❌ 不引入 headless browser（playwright/selenium）除非 S3 PoC 證明唯一可行 **且** 阿喜核准（重量級依賴 + CI 成本）
- ❌ 不動報告呈現層（P106.1 已處理）
- ❌ 不為非焦點平台（IG/Threads/FB）過度投入（本 Phase 聚焦芽芽覆蓋 + Dcard）

---

## 8. 風險登記（凍結時寫入 RISK_REGISTRY）

**R-027：焦點英雄爬取覆蓋退化 / Dcard Cloudflare 反爬 / 靜默資料淺化（P107 開案）**
- 風險級：🟡 中（修復中）
- 未解質疑：M2-#2（Dcard 繞 Cloudflare 不保證成功）、M2-#5（爬蟲 ToS/法務/IP ban 不可逆）
- 緩解：見 §6 記憶落點 + §7 停損；checker advisory 監控覆蓋率

---

## 9. 影響半徑表（收官時更新）
預估動檔：`scrapers/tavily_searcher.py` / `dcard_scraper.py` / `bahamut_scraper.py` / `main.py` / `config.py`（註解）/ `scripts/check_crawl_coverage.py`（新）/ `tests/test_*`（新 3-4 支）/ `reporter`（manifest 欄位）/ `docs/`（本檔+postmortem）→ **≥ 10 檔，重大 Phase**。

---

*草案版本：v0.1（2026-06-02 Opus 4.8 起草）。對齊 PHASE_TEMPLATE v1.2。凍結前須過 lint-phase-plan + 阿喜裁決。*
