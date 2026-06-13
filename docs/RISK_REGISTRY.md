# 跨 Phase 風險登記簿（STR6）

> **用途**：登記跨 Phase 不滅的風險、待解隱患、需長期觀察的議題。每個 Phase 收官時主動掃一次，新風險入帳、已解風險標記關閉。
> **建立日期**：2026-05-07（隨 P69 模型選擇指引啟用）
> **格式**：每筆 = 編號 + 標題 + 來源 Phase + 風險級 + 狀態 + 描述 + 緩解策略

---

## 更新 SOP（P84.4）

1. 新增風險時使用下一個未占用 `R-###`，不得重複編號。
2. 仍需觀察或未完成緩解的風險放在 `開放風險（Open）`，且 `狀態` 欄位必須包含 `Open`。
3. 已修補、已豁免關閉或已由其他風險承接的條目移到 `已關閉風險（Closed）`，且 `狀態` 欄位必須包含 `已` 或 `Closed`。
4. Phase 收官前執行：`py scripts\governance_doctor.py --repo-root .`。
5. 若 governance doctor 回報 `GOV###`，先依 `docs/OPERATIONS_RUNBOOK.md` 對應 anchor 修正後再提交。

---

## 開放風險（Open）

### R-037：self-heal 自動修復邊界 + 主根因（main.py generate 例外被吞）未治本（P111 衍生）

- **來源**：P111 CI 報告自癒收官（2026-06-14）
- **風險級**：🟢 低（自癒線守同源閘門 + 失敗 graceful 降級 L4，已對抗審查；殘留為未治本 + 退化版保真）
- **狀態**：Open（self-heal 已上線且 514 passed + 4 視角審查；殘留為主根因待治本 + 自動化邊界長期監測）
- **描述**：(a) **主根因未治本**：報告意外缺漏的源頭是 [main.py:728](../main.py) `generate` 例外被 `try/except` 吞掉（analysis 已寫、report 沒寫）。P111 是「偵測→自動補產」的下游補救（症狀面），未動上游吞例外（刻意不碰，scope 對齊）。(b) **self-heal top5 退化保真（原 R8）**：replay 用既有 analysis 重渲染，若 analysis 缺 `analyzed_posts` 細節，top5 排序與正式版可能略異（fallback post.score）；屬退化版補救，非逐位元還原正式報告。(c) **自動化邊界**：L5 自動修復限「重渲染窄面、零額度、不可逆不碰」；未來若有人擴大 self-heal 到不可逆動作，會破 L5 前提。
- **緩解策略**：(a) 主根因登記 future（下一輪可加 `main.py:728` 例外時的結構化告警或重試，非本期）；(b) 退化保真：manifest 標 `self_heal/is_backfill` 可辨識自癒產出 vs 正式產出；(c) 自動化邊界：`replay_run.py` docstring 契約 + postmortem 通則1/2 + G-ii sys.modules guard + 「不可逆仍問阿喜」鐵律；改 `should_promote`/`run_checks` 參數/heal 流程任一處須重審 L5 同源性（X3 過期日 2026-09-14）。
- **關聯**：B-027（凍結計畫字面修法可能與真實架構矛盾且測試抓不到）；R-038（no-op candidate 進版控）；postmortem 4 通則。

---

### R-038：self-heal no-op 的 candidate 檔仍被 Fallback Push 撈進版控（cron 既有行為，非 P111 惡化）（P111 衍生）

- **來源**：P111 第二輪對抗審查 X4-K / X2 揭露（2026-06-14）
- **風險級**：🟢 低（cron 既有行為，P111 不惡化；no-op candidate 未 promote、不被 index 連結、僅檔案存在）
- **狀態**：Open（known issue，明告阿喜；非本期 must_fix）
- **描述**：self-heal 不通過閘門時 no-op（不 promote、不寫 sidecar、index 不指向），但 `generate(promote=False)` 已落地的 candidate 檔（`aov_report_<date>.html`）仍會被既有 Fallback Push（`git add data/reports/`）撈進版控，且 GitHub Pages 可被直連 URL 存取。**這是 cron 本來就有的行為**（main.py 的 candidate 同樣會被 Fallback Push 撈），P111 self-heal 沿用同一條 push 路徑、不新增授權、不惡化。
- **緩解策略**：(a) 明告阿喜「自動補產僅限通過 cron 同款閘門的報告才會被 index 指向發布；no-op 的 candidate 雖進版控但不在首頁、不被連結」；(b) 若未來要根治「未發布 candidate 不進版控」，需改 Fallback Push 的 `git add` 範圍（cron + self-heal 一併，登記 future，非本期）；(c) no-op candidate 不寫 sidecar（修法A）→ 不污染凍結偵測器。
- **關聯**：與既有 Fallback Push（`daily_report.yml`）同部署戰線；R-037（self-heal 邊界）。

---

### R-036：P110 文章凍結修復殘留 — 連續日輪動待 cron 終驗 + 板列表無時間文被擋出池（P110 衍生）

- **來源**：P110 v2 收官（2026-06-13）+ Review Workflow 容錯維度 finding
- **風險級**：🟢 低（核心已修、502→504 passed；殘留為待驗 + 邊界隱性風險）
- **狀態**：Open（機制已端到端驗證，待 cron 真實連續日終驗）
- **描述**：(a) **連續日輪動待 cron**：S1+S2 端到端驗證（板列表撈 15 新文 decay 0.83-0.99 排前、top5_news 去重）+ decay 純函式證新文排前，但「使用者連續多天看到報告真的每天不同」待 cron 自然驗（同 P108.3/3.1/108.4 待 cron 驗鏈）。(b) **板列表無時間文隱性風險**：`fetch_board_latest` 經 `_parse_row` 若某列無時間元素 → `published_date=''` → 被 `generator.py:284` other_pool 的 `dated_posts`（`_has_known_post_date`）擋出最新動態候選池；若巴哈板列表時間欄 DOM 與搜尋頁不同，P110 撈新文目標可能靜默打折（凍結偵測器 advisory 不硬擋）。
- **緩解策略**：(a) 凍結偵測器 `check_report_freshness.py`（連續 N 筆 top5_hash 相同→advisory 告警）持續監測，cron 跑幾天後看告警是否消失即驗證輪動；(b) 板列表無時間風險——可在 `fetch_board_latest` 對空 published 補爬取當下時間 + warning 計數（登記為下一輪韌性增強，非本期 must_fix）；(c) **nice_to_fix 技術債**：`generator._focus_text_evidence` 與 `top5_picker._is_yaya_related` 芽芽判定範圍不一致（LLM 模式窄角可達，本地路徑不可達），長期收斂為單一 helper。
- **關聯**：B-026（優先豁免反噬 + 名實不符雙軌）；與 R-031（報告 UX）同呈現戰線、與 R-027（爬取覆蓋）同爬取戰線。

---

### R-034：combat_stats 無自動真實數據源 — 官方勝率頁已下線，採半自動手動 yaml；B′ 巴哈真爬 PoC 已驗不可行（圖片源需 OCR）（P106.2 衍生）

- **來源**：P106.2 PoC 實測（2026-06-07）
- **風險級**：🟡 中（半自動依賴阿喜手動更新；過時數據已由 stale 警示誠實標示緩解）
- **狀態**：Open（半自動已上線；**B′ 真爬 PoC 2026-06-07 已做 → 不可行 → 維持半自動**）
- **描述**：PoC 證 Garena 官方勝率子域 `herowinrate.moba.garena.tw` 已下線（tw/vn/th 全 NXDOMAIN）、無公開 API、第三方 AOVRanking 只導流到死連結、遊戲內 API 逆向違 ToS+封號。現採半自動（阿喜遊戲內看真值 → 填 `configs/hero_combat_stats.yaml`）。殘留：(a) 阿喜可能忘更新→數據過時（stale 警示緩解）；(b) 唯一潛在自動源「巴哈官方勝率帖」（我們有 bahamut_scraper）尚未驗證投報比。
- **緩解策略**：(a) stale 警示（>30天標「可能過時」）+ yaml 更新 SOP；(b) ~~B′ 巴哈官方帖真爬~~ **【2026-06-07 PoC 已做，結論：不採用】**：官方「羊咩調查室」帖反爬可過(HTTP 200)，但**勝率數據是圖片**(內文 0 個 %數字 vs 80-97 張圖)、需 OCR 中文英雄名+數字(準確度堪憂)、賽季級低頻、帖 ID 每期變 → 投報比遠差於手動填 yaml(1 分鐘 100% 準確)，**維持半自動**；(c) `scripts/check_no_fake_stats.py` 防假數據潛入。
- **關聯**：與 R-027（焦點英雄爬取覆蓋）同爬取戰線；P107 教訓「不先 PoC 不接線」適用 B′。

---

### R-035：歷史 archive combat_stats 污染 — P106.2 前報告含假戰績，不回溯改（P106.2 衍生，低）

- **來源**：P106.2 收官（2026-06-07）
- **風險級**：🟢 低（不影響未來；僅歷史查詢可能誤信）
- **狀態**：Open（known issue，刻意不回溯，X3）
- **描述**：P106.2 之前所有報告/archive 的 `combat_stats` 是寫死假數據（芽芽 52.8/45.2 等），且無 `data_source` 標記。依「不竄改歷史」原則（X3）不回溯修改。`data_source` 標記僅 P106.2 起生效，故歷史 archive 的 combat_stats 無法用 data_source 辨識真假。
- **緩解策略**：(a) 不回溯改（保持歷史誠實，竄改更糟）；(b) history-trend-query 等消費 archive 的 skill 若用到歷史 combat_stats 需注意 P106.2 前不可信；(c) 未來若需歷史勝率趨勢，以 P106.2 後（含 data_source=manual_yaml）為準。
- **關聯**：B-025（假數據壓制 guard）；data_source 貫穿設計。

---

### R-033：picker 仍對未正規化來源脆弱 — 治本採爬蟲端正規化、picker 未加防禦（P108.3 衍生，advisory）

- **來源**：P108.3 治本 vs 治標決策（2026-06-06 阿喜拍板純治本）
- **風險級**：🟢 低（advisory 觀察；現有來源已由爬蟲端正規化覆蓋）
- **狀態**：Open（advisory，不立即修）
- **描述**：P108.3 採爬蟲端正規化（bahamut_scraper → ISO），picker `_compute_decay`/`_is_too_old` 的 `_FMTS` 維持只認 ISO 系列**未動**（阿喜拍板治本不治標）。殘留：若未來新增爬蟲也存非標準/相對格式且未接 `date_normalizer`，picker 會重蹈 decay 觸底 0.300 覆轍（單點補丁風險）。
- **緩解策略**：(a) `date_normalizer` 設計為平台無關純函式，新爬蟲可直接複用；(b) 新增爬蟲時於計畫書檢查 published_date 是否需正規化；(c) 若復發頻繁，再評估 picker 加相對格式容錯當第二道防線（治本+防禦）。
- **關聯**：與 R-030（已 Closed，本 Phase 治本）同 picker 戰線；與 R-026（age filter fallback 倒灌）同 picker 家族。

---

### R-031：報告 UX — 24H 聲量圖無圖例看不懂 / 最新動態無法獨立滾輪（P108 衍生，UX Phase 待開）

- **來源**：P108 阿喜驗收（2026-06-06）
- **風險級**：🟢 低（不影響數據正確性，影響閱讀體驗）
- **狀態**：Open（部分收斂；#4a CSS 已解，#3 暫擱待 P106-5 PNG 化）
- **描述**：#3 heatmap 無 visualMap 顏色圖例 + 無說明文字（只 hover tooltip）→ 靜態看不知顏色代表什麼；#4a `.feed-container` 無 `max-height`+`overflow-y` → 最新動態無法獨立滾輪（已於 P109 解決）。
- **緩解策略**：
  - #4a 已由 P109 CSS 屬性注入（max-height: 70vh + overflow-y: auto）解決，並新增防復發單元測試。
  - #3 在 LINE webview 因無法加載 ECharts CDN 暫時無效，故此項暫擱，待 P106-5 PNG 化解決方案一併處理。
- **關聯**：純呈現層 UX，與 R-028 數據可信度不同戰線。

---

### R-025：子代理派遣準則 v1.0 dead rule 風險 / 到期實效復盤（P104.2 衍生）

- **來源**：阿喜 2026-05-31 要求把全域 `~/.claude/CLAUDE.md`「🤖 子代理派遣準則 v1.0」的到期復盤義務錨定到 repo（remote scheduled agent 拿不到本地全域守則與對話歷史，ROI 低，改用本地 RISK_REGISTRY 錨定）。
- **風險級**：🟢 低
- **狀態**：Open（觀察至 2026-08-31；到期人工復盤）
- **描述**：v3 子代理派遣準則寫在本地全域 CLAUDE.md（不在本 repo）。若三個月內無人回顧其實效，可能淪為 dead rule——一直掛著卻從未真正擋下任何「亂派／回頭難驗證／幻覺」，造成規則膨脹與虛假信心（G5 抗熵 / G1 dead rule 政策）。
- **緩解策略**：
  - 短期：本條目以 X3 到期日 `2026-08-31` 錨定，靠既有「每 5-10 phase 復盤」掃到。
  - 中期：2026-08-31 前的跨-phase 復盤，人工回顧守則三個月內是否真正擋下亂派／幻覺（可對照守則「自稽收斂判準句」出現頻率與當下判斷）。
  - 長期：有效 → 保留或考慮升級為 checker；無效或過吵 → 降級為「建議」或移除，避免規則膨脹。
- **觸發升級／到期動作**：2026-08-31 到期未復盤 → 由 G5-1 dead rule 偵測標記；復盤判定無效卻保留 → 升為規則腐化 active issue，需明文降級或移除並記錄理由。

---

### R-026：top5 age filter 與 template fallback 倒灌不一致（P106.1 衍生）

- **來源**：P106.1 問題 8（top5 加時間上限過濾 `TOP5_MAX_AGE_DAYS=14`）收官品質審查，2026-06-02 Opus 端到端驗證發現（commit `b5d1337`）。
- **風險級**：🟢 低（極端邊界；fallback 倒灌為 pre-existing 設計，非 P106.1 引入）
- **狀態**：Open（已知設計邊界，不立即修；實務日報每天有新文鮮少觸發）
- **描述**：age filter（`analyzer/top5_picker.py::_is_too_old`）只作用於 `pick_top5` 內部，影響 `top5_news`。但 `reporter/templates/report.html`「最新動態詳情」區有 fallback：`{% if top5_news %}…{% else %}` 改用**未經 age filter** 的 `posts`（=`dated_posts`）。因此當 `top5_news` 被 age filter 清空（極端：當日所有候選文章皆 >14 天），fallback 會把未過濾的舊文倒灌回頁面，age filter 在該情況形同虛設。**此為 R-017「Top-5 / hero focus / general feed 出現不可解釋舊文污染」的一個已知機制根因（cross-ref R-017）**。
- **緩解策略**：
  - 短期：本條目錨定。端到端驗證確認正常情況無虞——`max_age=14` 砍個別舊文後 `top5_news` 仍有內容、新文遞補；實務日報每天有新文，`top5_news` 鮮少全空，fallback 極少觸發。
  - 中期：若 R-017 monitoring 再現舊文污染，優先排查此 fallback 路徑——讓 fallback 的 `posts` 也套用同一 age filter，或 fallback 改顯示友善空態而非倒灌。
  - 長期：評估把 age filter 上移到 `dated_posts` 生成處（單一過濾點），消除 top5 / fallback 雙路徑不一致。
- **觸發升級**：若生產報告出現「`top5_news` 空 + fallback 倒灌 >14 天舊文」實例，或 R-017 content trust checker 因舊文 FAIL 且根因指向此 fallback → 升為 active，開 follow-up 修 fallback 過濾。
- **附帶記錄（同次審查，極低風險不修）**：
  - (a) `reporter/generator.py` 呼叫 `pick_top5` 未傳 `now`（:269-272、:283-287），age 基準為真實 `datetime.now()` 而非 `report_date`；日報即時跑無影響，補跑歷史報告時基準偏移。
  - (b) `report.html` 芽芽觀察室空態判斷用 `hero_focus_posts`，但迴圈跑 `hero_focus.top_comments`，兩者不同源；理論上「前者空後者非空」會吃掉 comments，實務不發生（comments 由芽芽貼文萃取）。

---

### R-027：焦點英雄爬取覆蓋退化 / Dcard Cloudflare 反爬 / 靜默資料淺化（P107 開案）

- **來源**：P106.1 run-now 正式跑流程（2026-06-02）阿喜質疑「0 篇芽芽、尤其 Dcard」，Opus 端到端調查（讀 raw + 三主力爬蟲原始碼）證實爬取層四根因，非報告 bug。
- **風險級**：🟡 中（修復中；`docs/PHASE_107_PLAN.md` DRAFT 已過 M1/M2 lint）
- **狀態**：Open（P107 已凍結 2026-06-02、**S1-S2 已收官 push**〔HERO_FOCUS_KEYWORDS 接線 + 巴哈治本〕；**剩 S3 Dcard 治本被阿喜主動延後**——Cloudflare 鎖死〔cloudscraper/playwright headless 全 403〕+ 投報比差〔巴哈已撈 28 篇芽芽文〕+ 不可逆風險〔M2#5 觸 ToS/IP ban〕，需 playwright-stealth/Apify 才能過，改天評估）
- **描述**：焦點英雄芽芽長期靠泛搜「傳說對決」碰運氣覆蓋，四根因連鎖：(A) `HERO_FOCUS_KEYWORDS` 是 dead config（config.py:123 定義但無爬蟲使用，連 Tavily:123 寫好的焦點意圖注入都因此永不觸發）(B) 三平台 content 只有標題無內文（Dcard:122/巴哈:162 寫死標題+後綴、Tavily:140 `include_raw_content=False`）(C) `detected_heroes` 僅 Tavily 做、Dcard/巴哈未設（raw 2026-06-02 共 19 篇全空）(D) `keyword not in title` 過濾扼殺多詞 keyword。連鎖效應：英雄聲量追蹤（專案核心定位）建立在淺資料上，焦點覆蓋率可無預警歸零且無人察覺。
- **緩解策略**（詳見 `docs/PHASE_107_PLAN.md`）：
  - 短期（快修）：`HERO_FOCUS_KEYWORDS` 接入 Tavily 搜集，啟動既有意圖注入。
  - 中期（穩修）：Tavily `include_raw_content` 拿全文 + Dcard/巴哈補 `detected_heroes` + 放寬 keyword 過濾（焦點豁免）。
  - 長期（飛輪）：Dcard 治本（Apify Dcard Actor / 繞 Cloudflare PoC，含停損）+ 防復發 guard（`check_crawl_coverage` checker / anti-regression test / manifest 覆蓋率欄位 / daily monitor）+ blindspot 通則化「dead config」與「靠泛搜碰運氣的焦點覆蓋」。
- **未解質疑（M2）**：#2 Dcard 繞 Cloudflare 不保證成功（proxy-evader 只防 403/429 非 JS challenge）；#5 爬蟲 UA 偽裝/繞 Cloudflare 觸 ToS/法務/IP 永 ban（不可逆，Ken 紅隊覆核）。
- **觸發升級**：P107 動工後若 Dcard PoC 失敗 → 依停損降級標題層並明文記錄；若 checker 上線後焦點覆蓋率持續 0 或 content 退回只標題 → 升 active，排查接線斷裂 / selector 失效。
- **防復發落點**：`docs/PHASE_107_PLAN.md` §6（docs / test / checker / config / manifest / monitor / blindspot 七落點）。

---

### R-029：API key 外洩防線不足 — local log 裸印 provider URL / 歷史中轉 token（2026-06-04 安全熱修）

- **來源**：阿喜 2026-06-04 回報老師提醒「凡是有調用密鑰的部分，務必使用變數，不要寫死；`.env` 禁止上傳 GitHub」，進一步追查 AOV 與 Hermes。
- **風險級**：🔴 高（安全；provider key 一旦仍有效，可能被盜用額度或外部呼叫）
- **狀態**：Open→**已大幅緩解**（2026-06-13：實測 chatones proxy `sub.chatones.site` **已 DNS 下線/NXDOMAIN → 舊 token 已失效、無法盜用**，無需 rotate；本次一併執行 `git filter-branch` history rewrite 移除 `dev_claude.ps1` 殘留 token，清 public history 污點 + force push）
- **描述**：目前 HEAD 未追蹤 `.env`，且 `.gitignore` 已排除 `.env` / log；current tracked secret scan PASS。但 AOV 曾有兩類安全風險：(A) 歷史 commit 的 `dev_claude.ps1` 曾寫入舊 `ANTHROPIC_AUTH_TOKEN` / chatones proxy token；(B) 本機 `logs/app.log` 曾記錄含 query key 的 Gemini API URL。若只要求阿喜手動換 key 而不修系統，未來 provider exception / HTTP error 仍可能再次把 key 帶進 log。
- **已完成緩解**：
  - 刪除本機未追蹤的舊中轉腳本 `dev_claude.ps1`（目前不再使用）。
  - 刪除本機舊 `logs/app.log`，避免本機殘留可讀 key。
  - `analyzer/gemini_client.py` 新增 secret redaction：URL query、OpenRouter-like key、Google AI key、generic `sk-*`、Discord webhook 形狀都先遮罩再 log / 回傳錯誤。
  - `test_gemini.py` 改用相同遮罩 helper，避免人工測試腳本印出含 key URL。
  - `tests/test_gemini_model_policy.py` 加三個防復發測試，鎖定 URL key、httpx exception message、OpenRouter-like 值都會被遮罩。
  - 新增 `.githooks/pre-push`，本機 push 前執行 `py -m gov.scan_secrets`；已設定 `core.hooksPath=.githooks`。
- **殘留/需阿喜處理**：
  - provider 端 rotate/revoke：若 Google AI / OpenRouter / chatones proxy 後台仍有舊 key，需在後台刪除或重生；AI 無法替阿喜登入第三方帳號撤銷。
  - Git history 是否 rewrite：歷史 `dev_claude.ps1` 若 token 判定曾公開且仍可能有效，需另開安全專案評估 `git filter-repo` / BFG 清史；這是高 blast radius 動作，不在熱修中自動做。
- **觸發升級**：secret scan 再發現 current tracked 真值、任何 log 再出現 raw key、或 GitHub remote history 中的舊 token 被確認仍有效 → 立即停止 push / 發布，先 revoke/rotate，必要時開 history rewrite 專案。
- **防復發落點**：`py -m gov.scan_secrets`、`.githooks/pre-push`、redaction helper tests、`TASK_HISTORY.md` P108.1 安全熱修紀錄。

---

### R-023：Monitoring review false closure / missing guard prioritization drift（P102 開案）

- **來源**：主公 2026-05-29 指定 `P102 Missing Guard Backlog / Monitoring Review Plan`；P101 已建立 guard index，但 R-016/R-017 monitoring 尚未到期，且 P101 human-only backlog 仍需排序。
- **風險級**：🟡 中
- **狀態**：Open（P102 DRAFT；runtime 未開始，不關閉 R-016/R-017，不補所有 missing guards）
- **描述**：若只看 2026-05-29 latest report / content trust PASS，AI 可能誤把 R-016 或 R-017 提早 close；若只看 P101 human-only backlog，AI 又可能主觀挑錯下一個 guard，造成低 ROI 返工或漏掉 current blocking evidence。
- **緩解策略**：
  - 短期：P102 plan draft 明確採 report-only review，不 close monitoring，不改 existing checker，不接 strict gate。
  - 中期：若主公核准 runtime，產出 monitoring evidence matrix 與 missing guard ranking；用 impact / recurrence / machine-ability / cost 四維度排序。
  - 長期：到 2026-06-01 / 2026-06-02 後，分別用 fresh evidence 裁決 R-016 / R-017 close、keep monitoring 或 escalate。
- **觸發升級**：若 P102 在 monitoring window 未到期前關閉 R-016/R-017、忽略 SLO002/SLO003/CCG005 current issue、一次補所有 missing guards、修改 existing checkers、接 strict gate、或複製 raw report/log/post 內容 → 升為 active blocking，立即回滾並寫 Postmortem。
- **最新證據（2026-05-29）**：5/29 content trust checker PASS；5/29 manifest 是 production / publish_eligible / provider routing disabled。但 SLO checker 仍有 current `SLO002` 2026-05-27 manifest gap 與 `SLO003` doctor severity budget blocking；cost/cache governance 仍有 current `CCG005` degraded（total_llm_calls=31 threshold=20 latest_llm_calls=9）。因此 P102 不應 close R-016/R-017，只能做 review / ranking。

---

### R-022：Known issue guard index drift / false confidence（P101 開案）

- **來源**：主公 2026-05-29 指定 `P101 Known Issue Guard Index`；P98/P99/P100 顯示 AOV 已有多條 known issue guard，但分散在 risk registry、phase plan、runbook、config、checker、tests 與 handoff。
- **風險級**：🟡 中
- **狀態**：Open（P101 CLOSED / ADVISORY GUARD ACTIVE；strict gate blocked）
- **描述**：若沒有單一索引，未來 AI 可能找不到已存在的防線而重修舊問題；但若索引誤把 human-only SOP 標成 machine guard，也會造成 false confidence，讓主公以為某類復發已被系統擋住。
- **緩解策略**：
  - 短期：P101 runtime 已新增 `docs/KNOWN_ISSUE_GUARD_INDEX.md`、`scripts/check_known_issue_guard_index.py`、`tests/test_known_issue_guard_index.py`；checker advisory-only，不修改 existing checks，不升 strict gate。
  - 中期：維護 index 欄位：risk id / human doc / machine guard / focused command / state / gap / next action；缺 guard 要明標 `human-only` 或 `missing-machine-guard`。
  - 長期：每 5-10 個 Phase 或大里程碑後復盤 index；穩定有效的 advisory checker 才可討論 promote，低 ROI 或 false positive 高的規則要 revise / downgrade / remove。
- **觸發升級**：若 P101 把 human-only SOP 誤標為 machine guard、漏列 R-016/R-017/R-020/R-021 這類 active guard、複製 raw report/log content、改 existing checker 造成回歸，或把 index checker 接成 strict gate → 升為 active blocking，立即回滾並寫 Postmortem。
- **最新證據（2026-05-29）**：P101 runtime 已把 R-016 production SLO、R-017 content trust、R-018 RTK、R-019 project flywheel、R-020 generated artifact hygiene、R-021 root legacy hygiene、R-022 index drift 與 GOV-HANDOFF governance drift 納入 `docs/KNOWN_ISSUE_GUARD_INDEX.md`。`scripts/check_known_issue_guard_index.py` 檢查 required columns / required rows / required guard tokens / human-only gap markers；`tests/test_known_issue_guard_index.py` 4 passed。R-018 明確標 `missing-machine-guard` / `human-only`，沒有營造 false confidence。

---

### R-021：Root legacy / debug debris quarantine false deletion（P100 開案）

- **來源**：P98 audit 將 `P100 Root Legacy / Debug Debris Quarantine Plan` 排為 P99 後的下一個最高 ROI 候選；主公於 2026-05-27 要求開 P100。
- **風險級**：🟡 中
- **狀態**：Open（P100 CLOSED / ADVISORY GUARD ACTIVE；cleanup still blocked）
- **描述**：AOV root 目錄混有 product entry、治理文件、debug logs、diff outputs、loose preview/helper scripts 與 static assets。若未先做 reference-first quarantine plan，AI 或未來 cleanup 可能把仍被引用或仍有證據價值的檔案誤刪；但若完全不治理，root 噪音會持續影響接手判斷。
- **緩解策略**：
  - 短期：P100 runtime 已完成 root inventory / safe reference check / decision table / advisory checker；不執行任何 cleanup。
  - 中期：若主公要 actual cleanup，需另開 P100.1 或 future runtime，任何 move/delete 需逐項核准與 rollback plan。
  - 長期：只將穩定、低風險、高 ROI 的 root hygiene 規則升成 advisory checker；strict gate 需另行核准。
- **觸發升級**：若 P100 未經核准刪除、移動、rename root files，修改 `.gitignore` / Actions，讀出 raw debug content，或把 product entry / deployment truth 誤標為可刪 → 升為 active blocking，立即回滾並寫 Postmortem。
- **最新證據（2026-05-27）**：P100 runtime 新增 `docs/ROOT_LEGACY_QUARANTINE.md`、`scripts/check_root_legacy_hygiene.py`、`tests/test_root_legacy_hygiene.py`。Safe reference check 顯示 high-weight debug outputs 主要是治理/known-risk references，不是 active runtime references；`err.log` 仍因 AGENTS 錯誤日誌範例列為 decision-required；loose preview/generation scripts 未找到 active safe-scope references，但只列 archive candidate，不批准 cleanup。Checker default advisory exit 0，`--strict` 才會在 findings 時 exit 1。

---

### R-020：Generated artifact hygiene / stage guard false positives（P99 開案）

- **來源**：P98 audit 裁決下一個最高 ROI 候選為 `P99 Generated Artifact Hygiene Policy / Stage Guard`；主公於 2026-05-27 要求開 P99。
- **風險級**：🟡 中
- **狀態**：Open（P99 CLOSED / ADVISORY GUARD ACTIVE；cleanup still blocked）
- **描述**：AOV repo 內存在 tracked generated/deploy artifacts、old report variants、tracked previews、local untracked reports 與 ignored scratch。若沒有 stage guard，未來 commit 容易誤納 generated/scratch；但若 guard 過早升級為 blocking，也可能因 false positive 讓正常 docs/code commit 變痛苦。
- **緩解策略**：
  - 短期：P99 runtime 已完成 raw-free path-only advisory checker 與 focused tests；不自動 unstage / delete。
  - 中期：使用 `docs/GENERATED_ARTIFACT_POLICY.md` 作為分類來源，commit 前可手動跑 `scripts/check_generated_artifact_hygiene.py`；保持 advisory-only。
  - 長期：觀察 false positive / missed-risk 後，再決定 keep / revise / promote / remove；strict gate 需另行核准。
- **觸發升級**：若 P99 未經核准刪除或移動 reports/previews/assets、修改 `.gitignore` 或 Actions、checker 輸出 raw content、或 advisory guard 阻擋正常 commit → 升為 active blocking，立即回滾並寫 Postmortem。
- **最新證據（2026-05-27）**：P99 runtime 新增 `docs/GENERATED_ARTIFACT_POLICY.md`、`scripts/check_generated_artifact_hygiene.py`、`tests/test_generated_artifact_hygiene.py`。Focused tests 覆蓋 `scratch/`、`data/reports/PREVIEW_*.html`、root debug output、report variants、`ui_previews/`、`backups/`、decision-required paths；normal docs/code/canonical report quiet。Default advisory exit 0；`--strict` 才會在 findings 時 exit 1。

---

### R-019：Project self-optimization flywheel / repo entropy（P98 開案）

- **來源**：主公 2026-05-27 要求開 `P98 Project Flywheel Audit Plan`，希望把 AOV 專案從反覆修舊問題推進到可記憶、可檢查、可防復發的飛輪式優化。
- **風險級**：🔴 高
- **狀態**：Open（P98-P101 CLOSED；不清理、不搬檔、不改 existing runtime）
- **描述**：AOV 專案的複雜度主要來自跨爬蟲、LLM、報告、GitHub Actions、內容可信度、治理文件、skills 與 generated artifacts。若不先分層 audit，直接清理或重構可能誤刪歷史證據、破壞 Pages/report link、讓 TASK_HISTORY / handoff 真相漂移，或把新工具導入變成新的 debug 變因。
- **緩解策略**：
  - 短期：P98 runtime 已完成 report-only audit；明列 forbidden work，不搬移、不刪除、不 rename、不改 `.gitignore`、不改 GitHub Actions、不 stage generated/scratch。
  - 中期：P98 已產出 repo layer inventory、known issue gap、generated artifact hygiene、verification ladder 與 P99+ 候選排序；P99 已把 generated artifact hygiene 轉成 policy + advisory checker + tests；P100 已把 root legacy/debug debris 轉成 quarantine evidence + advisory checker + tests；P101 已把 known issue guard map 轉成 index + advisory checker + tests。
  - 長期：依 audit 結果拆小 Phase，把高 ROI 問題轉成 checker / test / registry / policy；低 ROI 或高風險清理不推進。
- **觸發升級**：若 P98 未經核准就清理檔案、改 runtime、改 workflow、stage 舊 untracked reports/scratch，或把 R-016/R-017 monitoring 誤標 Closed → 升為 active blocking，立即回滾並寫 Postmortem。
- **最新證據（2026-05-29）**：`docs/PHASE_98_AUDIT.md` 完成 metadata audit。核心 runtime 約 49 tracked files / 0.44 MB；generated/deploy artifacts 約 123 files / 22.18 MB；agent/skill layer 約 383 files / 9.30 MB；local `scratch/` 66 files / 12.31 MB 且保持 ignored。P99 已完成 generated artifact policy/checker/tests；P100 已完成 root quarantine evidence/checker/tests；P101 已完成 known issue guard index/checker/tests，不直接刪檔、不改 existing runtime。

---

### R-018：RTK token-saving proxy / toolchain output fidelity（P97 開案）

- **來源**：主公 2026-05-26 要求評估 RTK；RTK 是會壓縮 / 改寫 CLI 輸出的 token-saving 工具，可能影響 Codex / Claude / Gemini 的終端真相。
- **風險級**：🔴 高
- **狀態**：Open（P97 CLOSED / INSTALL BLOCKED；尚未安裝，尚未初始化）
- **描述**：RTK 可能降低 terminal output token 成本，但它位於 AI 與命令輸出之間，若壓縮掉 traceback、測試失敗細節、警告或 security-relevant output，AI 可能做出錯誤判斷。P97 runtime 已證實此風險不是理論：Windows/PowerShell 下 `rtk pytest` 會壓掉 missing file path，`rtk err py -c ...` 會遺失 sentinel error message。全域部署還會影響所有專案與多代理行為；Windows 原生 hook 能力與官方宣稱 savings 也可能有落差。
- **緩解策略**：
  - 短期：P97 已完成 isolated binary 評估；不安裝、不初始化、不全域部署，不把 `@RTK.md` 寫入 AOV `AGENTS.md`。
  - 中期：若主公想繼續，只能另開 future RTK project-local/manual-prefix pilot（P99+ 或獨立 phase）；限制在已知 noisy passing tests，debug / traceback / missing file / security-sensitive output 必須 raw 或 `rtk proxy`。
  - 長期：只有在 future RTK pilot 證明收益穩定且 failure fidelity 不退化時，才可重新討論全域部署；目前 global deployment blocked。
- **最新證據（2026-05-27）**：
  - RTK latest release `v0.42.0` Windows zip checksum PASS；binary 僅位於 `scratch/rtk_eval/bin/rtk.exe`。
  - `Get-Command rtk` runtime 前後皆 `NOT_FOUND`，未加入 PATH。
  - `rtk init --codex --dry-run -v` would create `RTK.md` and patch `AGENTS.md` with `@RTK.md`；tracked diff before/after empty，未套用。
  - Baseline：pytest pass 省 83.0%，pytest missing file 省 72.4%；Git/search 類 0-0.1%；`rtk read` 對 P97 plan 樣本為 -14.2%。
  - Failure diagnostics：missing file path 被壓成 `Pytest: No tests collected`；Python sentinel traceback 被 `rtk err` 改成 `RuntimeError: No active exception to reraise`；`rtk proxy` 保留 raw traceback。
  - Telemetry：`RTK_TELEMETRY_DISABLED=1 (blocked)`；runtime 產生的 local AppData `history.db` / `.hook_warn_last` 已清除。
- **觸發升級**：若未經核准出現 RTK binary、PATH/profile/hook 被修改、AGENTS/CLAUDE/GEMINI 被 RTK patch、telemetry 未關閉、或任何測試錯誤因 RTK 壓縮而被漏判 → 升為 active blocking，立即回滾並寫 Postmortem。

---

### R-017：Website Content Trust / focus hero mismatch / stale articles（P96 monitoring）

- **來源**：主公 2026-05-24～2026-05-26 回報：網站曾多次出現「芽芽觀察室」莫名變「圖倫觀察室」，且頁面中有很多舊文章。
- **風險級**：🟡 中（Monitoring；由 🔴 高降級，2026-05-26 主公核准）
- **狀態**：Open（Monitoring；2026-05-26 主公核准，觀察至 2026-06-02）
- **描述**：R-016 已使 Daily Monitor / production SLO / doctor 進入 monitoring，但這只能證明 pipeline 可發布，不保證前台語意正確。若 `hero_focus.name`、template 標題、Top-5 picker、news history index、`published_date` / `timestamp` 或 LLM summary 任一層漂移，使用者仍會看到錯英雄標題或過期文章，造成網站可信度受損。
- **緩解策略**：
  - 短期：開 P96 Website Content Trust plan；先定義 hero/title/freshness contract，不直接手改 HTML。
  - 中期：P96 runtime 新增內容可信度 checker / regression tests，覆蓋焦點英雄錯標、舊文/unknown date、known issue guard。
  - 長期：若 checker 穩定，評估是否接入 Daily Monitor advisory 或 strict gate。
- **最新證據（2026-05-26）**：
  - P96 runtime commit `f616283` 已推送。
  - 手動 dispatch AoV Daily Monitor run `26455966515` success；cloud auto-sync commit `0618717` 產生 latest report。
  - `py scripts\check_report_content_trust.py --repo-root . --date 2026-05-26` 全 PASS：focus room title PASS、forbidden focus title PASS、`report unknown dates` PASS、focus recent section PASS。
  - 2026-05-26 主公明文核准 `R-017 downgrade to monitoring`；R-017 由 active content-trust risk 降級為 Open（Monitoring），不是 Closed。
- **監控期**：每日或手動 dispatch 後檢查 latest production report、content trust checker、focus room title、`時間未知`、focus recent section、Top-5/general feed 日期可信度。
- **觸發升級**：若 latest production report 再次出現非 `config.HERO_FOCUS_NAME` 的觀察室標題、`圖倫觀察室` / 非焦點觀察室、`時間未知`、Top-5 / hero focus / general feed 出現不可解釋的舊文章污染、content trust checker FAIL、或 checker 通過但主公人工驗收失敗 → 升回 active R-017，另開 content trust follow-up phase 修復。

---

### R-001：模型選擇指引三檔同步無自動檢測（G5-4）

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：`docs/MODEL_SELECTION_GUIDE.md` 主檔變更時，需手動同步 `~/.claude/CLAUDE.md` 與 `~/.gemini/GEMINI.md` 的全域縮版章節。沒有自動檢測機制，可能漂移。
- **緩解策略**：
  - 短期：每次修主檔時手動跑 diff（人工自律）
  - 長期：寫個 `scripts/check-model-guide-sync.sh`（v1.x 後續視需求做）
- **觸發升級**：若漂移導致 Claude / Gemini 端建議不一致 → 升 🔴 高

### R-002：Gemini / Anthropic 新模型大版本上線時的指引腐化

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：Gemini 4 / Claude 5 等大版本發布後，本指引內模型清單、價格、能力對照即過時。沒有自動偵測機制。
- **緩解策略**：
  - 已寫入指引 §8.3：「廠商發布新模型大版本」為強制升版觸發
  - 預設 90 天回顧週期（下次：2026-08-05）
- **觸發升級**：若主公連 3 次選擇與指引建議不符 → 立即升 v2.0

### R-003：AI 是否實際遵循「Opus 卡住主動提醒」強制條款（觀察期）

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open（觀察期）
- **描述**：指引 §3.3 規定 AI 達卡住判定須主動提醒換 Gemini，但這是**行為條款**，需實際使用後驗證 AI 是否真的遵循。
- **緩解策略**：
  - 主公在實戰中觀察至少 3 次「應提醒」情境，記錄 AI 是否主動提醒
  - 若漏提醒次數 ≥ 1 → 在 CLAUDE.md / GEMINI.md 全域章節**強化**該條款
- **觀察截止**：2026-08-05（同 90 天回顧）

---

### R-004：UI/UX 修補無 LINE WebView 自動化迴歸測試（P70.3）

- **來源**：P70.3 收官（2026-05-08）
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`reporter/templates/report.html` 的 CSS / touch event / position 規則改動可能在 LINE in-app browser（WKWebView / Chrome WebView）破壞滑動或互動，但其他環境（桌面、一般行動瀏覽器）正常難以察覺。P70.3 的 `overflow-x: hidden on html` 即此類沉默損壞案例，從 P63.2 拖到 P70.3 約 5 週。
- **緩解策略**：
  - 短期（人工 SOP）：任何 `reporter/templates/` 的修改收官前，主公在 LINE 實機點開 1 個樣本報告驗收
  - 中期：評估 Playwright + iOS WKWebView 模擬（非 LINE app 直測，但接近）的 ROI
  - 長期：若同類沉默損壞 ≥ 2 次再發，升級為自動化 smoke test 必做項
- **觀察截止**：下次 `templates/` 重大改動時 review

---

### R-006：報告頁回戰略門戶按鈕需同步修補現有報告（P70.3.1 衍生）

- **來源**：P70.3.1 收官（2026-05-08）
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`reporter/templates/` 的 HTML 結構改動（如加回首頁按鈕）不會自動反映到已生成的舊報告，需批次 patch 腳本手動補做。目前 10 個 5 月報告已補齊，但未來若有更多改動，仍需人工維護批次腳本。
- **緩解策略**：
  - 短期：結構性 template 改動收官時，附帶一份 idempotent Python patch 腳本，同步更新現有報告
  - 中期：評估 report 生成改為 server-side render（SSR）以消除靜態複製問題
- **觸發升級**：若同步遺漏導致報告體驗分裂 ≥ 2 次 → 中期方案升為必做

---

### R-005：`-webkit-overflow-scrolling: touch` 已 deprecated（G5-1 退化偵測）

- **來源**：P70.3 收官（2026-05-08）
- **風險級**：🟢 低
- **狀態**：Open（觀察期）
- **描述**：`-webkit-overflow-scrolling: touch` 為 iOS 13+ 已 deprecated 屬性，目前保留是「不傷害」原則。若未來 WebKit 移除支援或改為 hard error，可能影響 momentum scroll。
- **緩解策略**：90 天後 review，若 iOS 14+ 普及度 ≥ 95% 則移除此屬性。
- **觀察截止**：2026-08-08

---

### R-011：Orphan SKILL.md 仍為舊格式（22 條 lint warning）

- **來源**：P71.9 收官（2026-05-11）
- **風險級**：🟢 低
- **狀態**：Open（豁免觀察）
- **描述**：P71.8/P71.9 處置的 orphan/archived skill SKILL.md 尚未全面升級為 S1 schema 格式，`lint_skill_registry.py` 對這些檔案產生 22 條 lint warning。這些 skill 均已標記為非 in-use（orphan/archived），不影響正常觸發路徑。
- **緩解策略**：
  - 短期：豁免 orphan/archived skill 的 S1 schema 強制要求；lint 工具已以 `--warn-only` 模式處理這些 warning
  - 中期：若有 orphan skill 復活為 in-use，升級為必做項
- **觸發升級**：orphan skill 重新啟用 → 必須完成 S1 schema 升級才能 commit

---

### R-012：metrics JSONL 無 size cap 與輪轉策略（P72.0 遺留）

- **來源**：P72.0 收官（2026-05-14）/ B-009 通則化
- **風險級**：🟢 低（短期）/ 🟡 中（長期 ≥ 1 年）
- **狀態**：Open（觀察期）
- **描述**：`skill_metrics_logger._run_with_metrics()` append-only 寫入 `~/.claude/skill_metrics.jsonl`，無 size cap、無 rolling、無 retention 政策。19 個 skill × 每天若干次呼叫 × 365 天 ≈ 數萬筆，雖短期單檔大小可控（< 100MB 等級），但缺輪轉策略意味著未來必須 migration。
- **緩解策略**：
  - 短期（< 90 天）：每月主公手動檢查檔案大小，超過 10MB 就 archive 一次
  - 中期：在 `gen_skill_metrics.py` 加 `--rotate` 子命令，按月切檔（`skill_metrics_2026-05.jsonl`）
  - 長期：考慮改用 SQLite 取代 JSONL，原生支援查詢與 retention
- **觸發升級**：檔案 ≥ 50MB → 升 🟡；單次 dashboard 生成耗時 ≥ 5s → 升 🔴 強制做輪轉

---

### R-013：M4 `--sync-rules` anchor heuristic 召回率低（P72.3 遺留）

- **來源**：P72.3 收官（2026-05-14）/ B-006 通則化
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`m4_track_blindspots.py --sync-rules` 用字面 anchor 比對 B-NNN 通則化規則 vs PHASE_TEMPLATE.md，實測 PHASE_TEMPLATE v1.1 已含 B-001/B-003/B-005 對應規則但輸出顯示「已涵蓋 0 條」。Heuristic 沒處理同義改寫、結構性改寫、規則拆分三種變體，可能誤導 AI 或主公以為 PHASE_TEMPLATE 漏接規則而重複加入。
- **緩解策略**：
  - 短期：CLI 輸出最後一行強制印「⚠️ 召回率低，主公人工審核必要」（已落地）
  - 中期：升級 anchor 為「規則關鍵詞 + 同義詞表」比對（如 `test_skill.py` ≈ `skill 測試` ≈ `Exit Criteria 測試項`）
  - 長期：考慮用 embedding 相似度（Gemini embedding API）替代字面比對
- **觸發升級**：主公在 ≥ 2 個 Phase 因為 `--sync-rules` 誤導而重複加入規則 → 升 🔴，強制中期方案落地

---

### R-016：production SLO blocking / landing stale（P84.6 收官揭露）

- **來源**：P84.6 總收官驗證（2026-05-18）
- **風險級**：🟡 中（Monitoring；由 🔴 高降級，2026-05-25 主公核准）
- **狀態**：Open（Monitoring；2026-05-25 主公核准，觀察至 2026-06-01；**2026-06-01 觀察窗到期，P105.1 收官本次不裁決 close——待 fresh production evidence，見緩解策略末 P105.1 連動**）
- **描述**：P84.6 收官矩陣顯示 governance / handoff / runbook / pytest 全數通過，但 production SLO 仍阻塞。2026-05-19 R-016.1 已修補 manifest sync contract，並由既有 canonical report 反建 5/16-5/19 report-only manifests，因此 `SLO002` manifest gap 已收斂；剩餘阻塞為 `SLO001` 連續無 production，`SLO003` 因連續 showcase_forced/degraded 超過門檻，且 landing 仍指向 `data/reports/aov_report_2026-05-16.html`。
- **緩解策略**：
  - 短期：不要把 P84.6 CLOSED 解讀成 production SLO 已恢復；維持 `SLO###` / `DOC###` / health check 作為營運真相。
  - 已完成：`data/runs/**/run_manifest.json` 已解除忽略，`main.py` 與 GitHub Actions fallback push 會同步 `data/runs/`；`scripts/backfill_manifest_from_report.py` 可從既有 canonical report 建立 report-only manifest。
  - 已完成：R-016.2 新增 LLM fallback/secret diagnostics；下一次 Actions 會顯示 `GEMINI_API_KEY` / `OPENAI_API_KEY` 是否配置，manifest 會記錄 `provider.quota_error`、`provider.openai_fallback_configured`、`provider.openai_fallback_used`。
  - 已凍結：2026-05-19 主公明確不想增加 OpenAI API 費用，P85 已凍結 `Evidence-first + Quality-tiered Production + LLM Enrichment Queue` 作為零額外付費修復主線。
  - 已完成：P86 `Gemini Model & Schedule Modernization` 已 CLOSED；本地已移除 2.0 / 2.5 主線 model，改為 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，並將 daily cron 更新至 UTC 08:30。遠端 commit `100460f` 已由 GitHub Actions 產出 `mode=production` report，manifest 顯示 `publish_eligible=true`、`quota_error=false`、`llm_calls=20`；health check production PASS，system doctor 無 blocking、僅 DOC007 advisory。
  - 已完成：P87 `Report Core Contract` 已 CLOSED；新 manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015；P87 採 shadow/advisory，不直接改 quality tier / promotion gate，不關閉 R-016。
  - 已完成：P88 `Deterministic Local Analyzer` 已 CLOSED；LLM 429 / provider exception 時可從真實貼文產出 `analysis_source=local_deterministic` 的 sentiment、keywords、heroes、events、platform breakdown 與 baseline summary；P88 未改 quality tier / promotion gate，R-016 仍 Open。
  - 已完成：P89 `Quality Tier / Promotion Gate` 已 CLOSED；manifest 寫入 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage`，report metadata 顯示 tier/source/coverage，promotion gate 改看 publishable quality tier；`production_local_only` 在 core contract / local baseline 通過時可發布，`showcase_manual` / `error_fallback` 不可發布。2026-05-20 health/doctor 無 blocking；舊產物缺 tier 僅 DOC016 advisory。R-016 仍 Open。
  - 已完成：P90 `Budget Ledger / Cooldown` 已 CLOSED；新增 raw-free budget state、429 cooldown、manifest budget snapshot、DOC017 / CCG006 advisory。Gemini budget/cooldown active 時會停止打 provider 並改走 P88/P89 local baseline；budget ledger 明確標註為 pipeline proxy，不是 provider billing truth。R-016 仍 Open。
  - 已完成：P91 `Cache / Dedupe / Top-N` 已 CLOSED；新增 source selection、保守 dedupe、budget-aware Top-N、local-only merge、manifest `selection` snapshot、doctor `DOC018`、cost governance `CCG007`。預設 `LLM_ANALYSIS_TOP_N=18`，raw source 不刪除，未選來源仍走 deterministic local baseline。2026-05-22 Actions 實跑已產生 P91 selection snapshot：pre-P91 `llm_calls=28` 收斂為 P91 `llm_calls=6`，`total_input_posts=19`、`unique_posts=12`、`duplicate_posts=7`、`local_only_posts=7`，且 local-only 全由 `duplicate_url` 主導。R-016 仍 Open。
  - 已完成：P92 `Enrichment Replay / Local-only 補深讀` 已 CLOSED；新增 artifact-backed enrichment queue、raw-free manifest `enrichment` snapshot、budget-aware manual `scripts/enrichment_replay.py`、GitHub Actions short-retention artifact、doctor `DOC019`、cost governance `CCG008`。Raw queue 僅位於 git-ignored `data/enrichment_queue/` 或 Actions artifact；`duplicate_url` / `duplicate_signature` local-only 預設 skipped / `no_eligible` no-op，不消耗 LLM；replay 使用既有 Gemini path 且關閉 OpenAI fallback。focused tests 66 passed、full pytest 274 passed。R-016 仍 Open。
  - 已完成：P93 `Provider Abstraction / Disabled-by-default Free Provider Slots` runtime 已 CLOSED；新增 `LLMProviderClient` protocol、disabled-by-default `ProviderRouter`、shared provider budget guard、raw-free manifest `provider.routing`、doctor `DOC020`、cost governance `CCG009`、fake-provider / no-call / budget guard tests。所有非 Gemini provider 預設 `enabled=false`；誤開 candidate slot 時 fail-closed，不呼叫 Groq / Cloudflare / GitHub Models；未新增 provider secret、未加入 GitHub Actions `models: read`、未改 daily default。R-016 仍 Open。
  - 已完成：P94 `Doctor / SLO Reclassification` runtime 已 CLOSED；新增 current / historical / residual classification，保留 `SLO001` / `SLO002` / `SLO003` blocking 門檻。2026-05-23 五日 SLO probe 為 `classification=current` 且 `issues=[]`；system doctor 顯示 DOC018 / DOC019 為 `residual` advisory；cost/cache 三日窗將 2026-05-21 pre-P91 `llm_calls=28` 標為 CCG005 `historical` advisory，CLI 不再因舊 spike exit 1。P94 未啟用 provider、未新增 secrets、未改 workflow、未關閉 R-016。
  - 已驗證：P95 `R-016 Closeout Verification` 第一輪 verification 已於 2026-05-24 執行；裁決為 `Keep R-016 Open`。後續 post-P95 AoV Daily Monitor run `26356870400` 已 success，auto-sync commit `65b9f92` 產生 2026-05-24 production report；2026-05-24 SLO 五日窗 `issues=[]`，system doctor 無 blocking，landing 指向最新 production report，provider routing 維持 `router_disabled_legacy_default` / `enabled_slots=0`，5/24 manifest `enrichment.replay_status=no_eligible`。
  - 已凍結：P95.1 `Enrichment Pending Closure` plan 已 FROZEN；P95.1 不靠 2026-05-22 掉出三日窗來假裝收官，而是要在主公另核准 runtime / artifact access 後，對 2026-05-22 enrichment pending eligible=2 做 dry-run / 必要 replay / CCG008 分類修正。P95.1 plan freeze 尚未下載 artifact、尚未讀 raw queue、尚未跑 replay、尚未關閉 R-016。
  - 已驗證：P95.1A `Artifact Dry-run` 已完成；正確 artifact 是 run `26285001843` / artifact `7159368993` / zip entry `2026-05-22/enrichment_queue.json`。queue schema valid，`eligible_count=2`，`skipped_count=8`；dry-run output 為 `eligible=2 will_replay=2 remaining_budget=15 status=dry_run`。P95.1A 未 apply replay、未寫 report、未 stage raw artifact / raw queue。R-016 仍 Open。
  - 已驗證：P95.1B `Apply Replay` 已執行，但 P90 budget guard 因 2026-05-24 `cooldown_active` 安全擋下 LLM replay；2026-05-22 manifest 已由 `replay_status=pending` 轉為 `replay_status=skipped_budget`，`budget_reason=cooldown_active`，`enriched_posts=0`。此狀態比 unknown pending 更可追溯，但尚未完成 replay；R-016 仍 Open。
  - 已驗證：P95.1C `Cooldown Retry` 已於 2026-05-25 09:35 +08 執行成功；dry-run 顯示 `eligible=2 will_replay=2 remaining_budget=20`，apply output 為 `OK: enrichment replay completed; enriched=2/2`。2026-05-22 manifest 已由 `replay_status=skipped_budget` 轉為 `replay_status=completed`，`eligible_posts=2`，`enriched_posts=2`，`budget_decision=call_llm`，`budget_reason=budget_available`，`cooldown_active=false`。Cost governance 三日窗已無 CCG008 current；只剩 2026-05-23/24 no_eligible residual。R-016 仍 Open，待主公裁決 close / downgrade / keep-open。
  - 已驗證：P95.1D `Post-P95.1C Cloud Verification` 已完成；workflow_dispatch run `26379118247` 在 head `9188a92` 上 success，Strict Gate step success，artifact `enrichment-queue-26379118247` id=`7190334548` expires=`2026-05-28T01:53:14Z`，auto-sync commit `d89c3b9` 產生 2026-05-25 production report。2026-05-25 health PASS，SLO `issues=[]`，system doctor 無 blocking，budget `cooldown_active=false` / `llm_calls_used=3` / remaining=17，provider routing 仍 `router_disabled_legacy_default`，CCG008 僅 residual no_eligible。
  - 已裁決：2026-05-25 主公回覆 `push ee8bcba，核准 R-016 downgrade to monitoring`；AI 已 push `ee8bcba`。R-016 由 active blocking risk 降級為 Open（Monitoring），觀察窗 2026-05-25～2026-06-01。此裁決不是 Closed；若 monitoring 觸發條件命中，立即升回 active R-016。
  - 監控期：每日或手動 dispatch 後檢查 latest production report、landing、SLO、system doctor、cost governance、budget/cooldown、provider routing。前台內容可信度（芽芽觀察室、舊文章、known issue guard）另開 R-017 / P96+，不得混回 R-016。
  - 長期：免費 provider 只作 P93 disabled-by-default 插槽候選；不得在未核准前接進主鏈路。
  - 已連動（2026-06-01 P105.1）：daily 首發切 OpenRouter（deepseek-chat）走 FallbackLLMClient、PROVIDER_ROUTER_ENABLED 仍 false——屬「預期 provider 變更」，**非**本 R-016 升級條件之「provider routing 非預期啟用」（P93 router 未啟用、未經 fail-closed guard）。daily dry-run 實測 manifest active_provider=openrouter、quota_error=false、core_contract pass、報告發布。解 fail-closed / 啟用 P93 router 延後為獨立任務（母計畫「啟用 P93 框架」目標部分延後）。觀察窗 2026-06-01 到期，本次不裁決 close（待 fresh production evidence、屬 production SLO 戰線另議）。
- **觸發升級**：monitoring window 內若出現任一條件，升回 active R-016：latest production SLO `issues` 非空、system doctor blocking/degraded、health check FAIL、landing 指向非最新 production report、`CCG008 current` 復發、provider routing 非預期啟用、Gemini budget/cooldown 連續阻斷最新 production，或 GitHub Actions Daily Monitor 連續失敗造成主公無法判讀最新報告。

---

## 已關閉風險（Closed）

### R-032：非巴哈平台 published_date 空值 → 最新動態只有巴哈（P108.4 折衷收官）

- **來源**：P108.3 PoC 實測（2026-06-06）非巴哈平台 published_date 100% 空值
- **風險級**：🟡 中（最新動態多平台多樣性）
- **狀態**：✅ 折衷收官（Closed，2026-06-07 P108.4）
- **描述**：非巴哈平台（Tavily/DDG 搜尋結果）published_date 100% 空值，被 generator `_has_known_post_date` gate 擋出最新動態池 → 池子幾乎只有巴哈文。
- **折衷解法（P108.4，飛輪穩修）**：飛輪二次追問選穩修 E′（非造假 fallback 日期、非 choke point 重構）。picker `_is_parseable_time`（復用 _FMTS 單一解析來源）對無法解析時間的文差異化 decay。**撞上 P108「排除無日期文」可信度契約（test_report_content_trust 2 測試）**，阿喜裁示折衷 A：**芽芽相關無日期文破例進池（generator yaya_pool 用 analyzed_posts、decay 0.6）；無關無日期文仍排除（other_pool 仍 dated_posts，保留可信度防線）**。template 不改（無日期維持「時間未知」誠實顯示）。
- **驗證**：新增 14 測試（_is_parseable_time + decay 對比 + 契約 guard）；content_trust 2 測試更新（focus「芽芽破例進」、general_feed 保持「無關排除」）；全套 474→488 passed。
- **未竟（接受）**：完整多平台（含無關無日期文）未做——與 P108 可信度防線衝突，折衷只破例芽芽；若未來要無關平台也進，需重評可信度 vs 覆蓋取捨。
- **教訓 B-024**：改下游消費行為前，除查程式消費點（B-023），須查測試/契約是否鎖定該行為——本次 S1 漏查 content_trust 契約、動工後才撞上。

---

### R-030：top5_picker 日期解析不支援巴哈相對格式 → 最新動態文章不換（P108.3 治本收官）

- **來源**：P108 阿喜驗收發現「最新動態 800 年沒換」（2026-06-06）
- **風險級**：🟡 中（報告核心價值＝最新動態反映度）
- **狀態**：✅ 已修補（Closed，2026-06-06 P108.3）
- **描述**：`top5_picker._compute_decay`/`_is_too_old` 只認 `%Y-%m-%d` 系列，不認巴哈「昨天 HH:MM」「MM-DD HH:MM」相對格式 → 巴哈文 decay 全 `_DECAY_MIN`(0.300) 相同、age filter 失效 → 排序退化純 score → 每天選同文章。
- **治本（P108.3）**：爬蟲端正規化（非治標改 picker）。新增 `scrapers/date_normalizer.py` 純函式 `normalize_published_date(raw, *, now)`，在 `bahamut_scraper._parse_row` 爬取當下把 published_date 正規化成 ISO（相對時間只能爬取當下解析，故在爬蟲端）；失敗保留原值 + warning（不丟資料）。picker/generator/local_analyzer 下游受益不改碼。
- **驗證**：PoC 涵蓋真實全集 37/37；新增 40 測試（normalizer 32 + 爬蟲整合 4 + 下游受益 4），全套 427→467 passed 0 failed。受益鐵證：decay「昨天 22:39」0.300→0.662、age filter 對巴哈舊文生效。
- **關閉條件**：離線測試證機制生效（Exit A-D）。Exit E（端到端最新動態每天換）由下次日報 cron 自然驗證（阿喜 2026-06-06 裁示暫不 run-now）。
- **殘留**：R-032（非巴哈空值戰線）、R-033（picker 未加防禦 advisory）另立。
- **P108.3.1 補遺（2026-06-07）誠實更正**：R-032 PoC 深挖揭露 P108.3 **僅在 local 路徑生效**——production 主路徑 sentiment(LLM) 的 post 重建用 `getattr(res, "timestamp")`，但 SearchResult 欄位實為 `published_date` 無 timestamp 屬性 → 走 LLM 的文時間遺失成「時間未知」、被 gate 擋出池。**先前標 Closed 屬過早宣稱（只驗單元 + local，未驗 production LLM 端到端）**。P108.3.1 修 sentiment 三處重建改直接存取 `res.published_date`（升級 A，拼錯即爆不靜默）+ 端到端契約測試（升級 B，防同類復發），全套 467→474 passed。至此 P108.3 機制在 production LLM 路徑生效；整體最新動態效果端到端待 cron 終驗。詳見 `docs/postmortems/2026-06-07-phase-108.3.1-llm-rebuild-published-date.md`（blindspot B-023）。

---

### R-028：報告數據可信度 — 平台圖失真 / 熱詞無連結（P108 收官）

- **來源**：P107 run-now 後阿喜 2026-06-02 手機看報告，發現報告呈現/數據失真。爬取已成功，問題在「撈到的資料怎麼呈現/統計」。
- **風險級**：🟡 中（報告核心價值＝數據可信度）
- **狀態**：✅ 已修補（Closed，2026-06-06 P108 + P108.2）
- **三問題收斂結論**：S0 釘死後三問題收斂為兩個真 bug。**A 熱詞空**＝本地 run-now 缺 jieba（6/2 報告 commit 931b71a author＝阿喜本人、非 cron；雲端有 jieba 正常，非 production bug）。**C 平台圖失真**＝LLM schema 只吐 ig/threads/fb 幻覺子集、漏巴哈 24 篇，兩端都壞＝真 bug。**原 B 文章來源錯**經查資料/渲染皆正確，實為 C 的觀感（圖表看不到巴哈、跑到 FB），併入 C。
- **修補（P108）**：(1) C＝抽 `local_analyzer.compute_platform_breakdown()` 真實統計，sentiment.py:509 後覆寫 LLM 版（dynamic_focus 之前，涵蓋圖表＋今日焦點兩消費者）+ generator 拔寫死白名單 + 圖表補巴哈 label/色；(2) A＝本地裝 jieba；(3) 防復發＝`scripts/check_report_credibility.py` advisory checker（real_hot_topics 非空 / platform_breakdown 含真實平台，不阻斷報告）。
- **治本（P108.2）**：jieba 詞典納入 stopwords 多字詞根治「巴哈姆特」切殘；英文虛詞降級版（誠實標示有限清單，中文通用長尾刻意不做）。
- **補修（#2，2026-06-06 阿喜驗收揪出）**：A「點詞看來源」初次只驗「熱詞非空」、漏驗「點擊真有連結」（success criteria 未驗完整）。根因：side panel `_postIndex` 只從 dated_posts 建、YT/IG 無日期文被過濾。修法：改用全集 `all_posts_for_index`，所有熱詞 100% 可點。commit `cd4c16f` + 回歸測試。
- **驗證**：全套 426 passed,0 failed；6/2 重生報告圖表 bahamut:24、熱詞區渲染 10 詞無雜訊。
- **關閉條件**：平台圖真實統計 + 熱詞修復 + checker 防復發落地並測試通過。殘留中文通用長尾為已知啟發式邊界（誠實版預期，非 bug）；報告需 run-now 重新 promote 上線。

---

### R-024：skill metrics 永不生成 — 設計前提錯配（P103.1 關閉）

- **來源**：P103 A3 診斷（2026-05-31）；P103.1 釐清關閉（2026-05-31）
- **風險級**：🟡 中
- **狀態**：✅ 已關閉（Closed，2026-05-31 P103.1）
- **描述**：AOV `.agent/skills/*/` 的 `record()` 在 `_run_with_metrics()` 內、入口 `if __name__ == '__main__'`；Claude Code 以 module/import 模式載入時 `__name__` 不等於 `'__main__'`，`record()` 永不執行，`~/.claude/skill_metrics.jsonl` 從未建立。
- **關閉結論（P103.1）**：非 bug，是**設計前提錯配**——`record()`+`__main__` 接線沒壞，是「設計前提（CLI 程式）vs 實際用法（對話內模擬觸發、skill 不以程式執行）」錯配。hooks 亦不適用（`matcher:Skill` 不觸發 issue #43630、payload 無 skill_name issue #22655）。**accepted 為已知設計限制**；接手者若要 metrics 需另議觸發機制重設計（屬工具鏈/部署層，非引擎 scope）。
- **防復發**：保留 `tests/test_skill_metrics_logger.py::TestImportDoesNotTriggerRecord` 錨點測試；postmortem `docs/postmortems/2026-05-31-phase-103.1-metrics-design-mismatch.md`。

---

### R-007：`.back-to-landing` 未列入 mobile backdrop-filter 停用清單（P70.3.1 審計）

- **來源**：P70.3.1 63 維度審計（2026-05-08）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-08；P76 於 2026-05-16 移至 Closed）
- **描述**：行動版（`@media max-width 768px`）停用 `backdrop-filter` 的 selector 清單未含 `.back-to-landing`，導致按鈕在 mobile 仍觸發模糊效果 → 滑動卡頓風險。
- **修補**：已將 `.back-to-landing` 加入 selector；template + 10 舊報告同步修補。
- **關閉條件**：具體 selector 修補已完成；LINE WebView 長期觀察由 R-004 承接。

---

### R-008：`.back-to-landing` 缺少 :focus 樣式與 aria-label（P70.3.1 審計）

- **來源**：P70.3.1 63 維度審計（2026-05-08）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-08；P76 於 2026-05-16 移至 Closed）
- **描述**：按鈕缺少 `:focus` 可見輪廓（無障礙 a11y 標準），且無 `aria-label`（螢幕閱讀器無法正確識別）。
- **修補**：已補 `.back-to-landing:focus { outline: 2px solid #f472b6; outline-offset: 3px; }` 及 `aria-label="返回戰略門戶首頁"`；template + 10 舊報告同步修補。
- **關閉條件**：已修補，無需進一步觀察。

---

### R-014：4 個歷史 Phase（P63/P64/P69/P70.3）缺 blindspot（M4 偵測）

- **來源**：P72.3 M4 `--status` 偵測（2026-05-14）
- **風險級**：🟢 低
- **狀態**：✅ 已回填（P75，2026-05-16）
- **描述**：M4 協議於 P71.1（2026-05-09）才落地，先前 4 個 Phase（P63/P64/P69/P70.3）的 postmortem 已寫但無對應 blindspots 檔。雖然當時的 postmortem 多少有涵蓋「以為清單」「教訓」，但未按 B-NNN 結構化，造成 `cross_phase_review.py` 無法自動撈取通則化規則。
- **修補**：P75 新增 4 份 blindspot 檔：
  - `docs/postmortems/2026-05-16-phase-63-blindspots.md`（B-011~B-013）
  - `docs/postmortems/2026-05-16-phase-64-blindspots.md`（B-014~B-016）
  - `docs/postmortems/2026-05-16-phase-69-blindspots.md`（B-017~B-019）
  - `docs/postmortems/2026-05-16-phase-70.3-blindspots.md`（B-020~B-022）
- **驗證**：
  - `py scripts/m4_track_blindspots.py --status` → P63/P64/P69/P70.3 全部 `✅ 已配對`
  - `py scripts/cross_phase_review.py` → 可讀到 B-011~B-022，最近 5 個 postmortem 產生 19 條 checklist
- **關閉條件**：4 個缺漏 Phase 均已配對，且新增規則能被 M3 工具召回。

---

### R-015：test_dynamic_focus 3 個 pre-existing 失敗連跑 5 Phase 積欠（P72 遺留）

- **來源**：P72.5 收官審視（2026-05-14）/ B-008 通則化
- **風險級**：🟡 中
- **狀態**：✅ 已修補（P74，2026-05-16）
- **描述**：`test_dynamic_focus.py` 3 個測試案例事件迴圈隔離問題（單檔跑 OK / 全套跑掛），從 P72.0 開始連續 5 個 Phase 被標為「pre-existing 不阻擋」，無人處理。違反 B-008 通則化「連 ≥ 3 個 Phase 標 pre-existing 必須升級為獨立 Phase」原則。
- **根因**：測試使用 `asyncio.get_event_loop().run_until_complete(...)`。單檔執行時 Python 仍會建立預設 loop，但全套測試前序 case 使 event loop policy 進入「已 set_called、目前無 current loop」狀態，導致三個 case 在主執行緒丟 `RuntimeError: There is no current event loop`。
- **修補**：P74 將三處測試執行改為 `asyncio.run(...)`，讓每個 async case 自行建立並關閉事件迴圈；未修改 `analyzer/dynamic_focus.py` production code。
- **驗證**：
  - `py -m pytest tests/test_dynamic_focus.py -q` → 5 passed
  - `py -m pytest -q` → 112 passed
- **關閉條件**：3 個測試案例全綠（單檔 / 全套皆通過）已達成。

### R-009：smart-task-router SKILL.md `deployed_to` 欄位為空（P71.8 遺留）

- **來源**：P71.8 前（2026-05-11 前後發現）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（P71.10，2026-05-14）
- **描述**：P71.8 升級 smart-task-router 為 in-use 時，SKILL.md 的 `deployed_to` 欄位遺留為空陣列 `[]`，未正確標記部署目標 `claude-project`，導致 registry 中部署資訊不完整。
- **修補**：P71.10 將 `deployed_to: []` 修正為 `deployed_to: ["claude-project"]`。

---

### R-010：ui-ux-pro-max skill 缺少 test_skill.py（P71.9 遺留）

- **來源**：P71.9 收官前發現（2026-05-11）
- **風險級**：🟡 中（SKILL_HEALTH 顯示 🔴）
- **狀態**：✅ 已修補（P71.9+，2026-05-11）
- **描述**：P71.9 處置 orphan skill 時，ui-ux-pro-max 升級為 in-use 但未補充 `test_skill.py`，導致 SKILL_HEALTH 顯示該 skill 為 🔴，打破「19 全綠」目標。
- **修補**：P71.9+ 補充 6/6 測試案例（schema lint / CLI 執行 / V1 觸發塊 / when_to_use / 範例查詢 / 輸出格式），達成史上首次 19/19 全綠。

---

## 變更紀錄

- **2026-05-07**：建立檔案（隨 P69 模型選擇指引啟用 STR6）；登記 R-001/R-002/R-003。
- **2026-05-08**：P70.3 收官登記 R-004（UI/UX LINE 迴歸盲區）+ R-005（webkit deprecated 屬性 90 天 review）。P70.3.1 審計追加 R-006（舊報告同步風險）+ R-007（mobile blur fix，已關閉）+ R-008（a11y fix，已關閉）。
- **2026-05-14**：P71.10 收官登記 R-009（deployed_to 空，已關閉）+ R-010（ui-ux-pro-max 無 test，已關閉）+ R-011（orphan lint warning，豁免觀察中）。
- **2026-05-14**：P72.5 收官登記 R-012（metrics JSONL retention）+ R-013（M4 sync-rules anchor heuristic 召回率低）+ R-014（4 個歷史 Phase 缺 blindspot）+ R-015（test_dynamic_focus 積欠升級獨立 Phase）。
- **2026-05-16**：P74 關閉 R-015；`test_dynamic_focus.py` 三個 async case 改用 `asyncio.run(...)`，單檔 5 passed，全套 112 passed。
- **2026-05-16**：P75 關閉 R-014；回填 P63/P64/P69/P70.3 共 4 份 blindspot，新增 B-011~B-022，M4 status 缺漏數歸零。
- **2026-05-16**：P76 狀態清理；R-007/R-008 從 Open 區移至 Closed 區，長期 LINE WebView 觀察仍由 R-004 承接。
- **2026-05-31**：P103.1 關閉 R-024（從 Open 移至 Closed）；確認 metrics 是設計前提錯配（skill 對話式觸發、非 shell 執行），hooks 不適用，accepted 為已知設計限制。
- **2026-06-02**：P106.1 問題 8 收官品質審查登記 R-026（top5 age filter 與 template fallback 倒灌不一致，cross-ref R-017）；同條附帶記錄 generator 未傳 now、空態判斷變數不同源兩個極低風險點。
- **2026-06-02**：P106.1 run-now 正式跑流程揭露爬取層根因，登記 R-027（焦點英雄爬取覆蓋退化 / Dcard Cloudflare 反爬 / 靜默資料淺化，四根因連鎖）；P107 計畫書 DRAFT 立案、過 M1/M2 lint，待凍結。
- **2026-06-02**：P107 S1-S2 收官（焦點接巴哈 + detected_heroes，端到端驗證芽芽進觀察室）後 run-now，阿喜手機看報告發現 3 報告呈現問題，登記 R-028（熱詞無連結 A〔併 P106 既有〕/ 文章來源錯 B / 平台統計缺真實平台 C），待開 P108 報告數據可信度修復系統處理。
- **2026-06-04**：阿喜回報金鑰外洩疑慮，登記 R-029（API key 外洩防線不足：local log 裸印 provider URL / 歷史中轉 token）；同步落地 redaction tests 與 pre-push secret scan guard，provider 端 rotate/revoke 與 history rewrite 另待決策。
- **2026-06-06**：P108 報告數據可信度修復收官，R-028 → Closed。S0 釘死三問題收斂兩 bug（A 熱詞空＝本地缺 jieba 非 production bug；C 平台圖失真＝LLM 幻覺子集、B 併入 C）；platform_breakdown 改真實統計（sentiment 後處理涵蓋圖表＋今日焦點）、拔 generator 寫死白名單、加 advisory checker 防復發。P108.2 治本：jieba 詞典根治「巴哈姆特」切殘 + 英文虛詞降級版。全套 426 passed,0 failed。
- **2026-06-06**：阿喜驗收 P108 重生報告揪 4 點。#2 熱詞點擊無連結＝A 漏修（只驗非空沒驗點擊），_postIndex 改全集補修（commit cd4c16f，427 passed），R-028 補記。新登記 R-030（#4b picker 日期解析→文章不換，另開 P108.3 治本）、R-031（#3/#4a 報告 UX，另開 UX Phase）。
- **2026-06-06**：P108.3 巴哈 published_date ISO 正規化治本收官，R-030 → Closed（從 Open 移至 Closed）。新增 `scrapers/date_normalizer.py`（5 類格式 + 跨年回退）+ bahamut_scraper 爬取當下接入（失敗保留原值 + warning）；PoC 涵蓋 37/37、全套 427→467 passed。build-vs-buy 評估 dateparser（免費但引依賴 + 黑箱）後阿喜核准自己寫。新登記 R-032（非巴哈 published_date 空值被 gate 擋在最新動態池外，空值戰線待開）、R-033（picker 未加相對格式防禦 advisory）。Exit E 端到端待下次 cron 觀察。
- **2026-06-07**：P108.3.1 補遺收官——R-032 PoC 揭露 P108.3 僅 local 路徑生效（production LLM 路徑 sentiment 重建用 `getattr(res,"timestamp")` 漏接 published_date，時間遺失成「時間未知」、走 LLM 文被 gate 擋出池）。修 sentiment 三處重建改直接存取 `res.published_date`（升級 A）+ 端到端契約測試（升級 B，防 P108.3 同類「單元過 production 沒生效」復發）。全套 467→474 passed。R-030 補記過早宣稱、Postmortem + blindspot B-023（改資料層欄位前驗全鏈流向、棄 getattr 靜默 fallback）。Exit E 仍待 cron 終驗。
- **2026-06-07**：P108.4 R-032 空值戰線折衷收官，R-032 → Closed。飛輪二次追問選穩修 E′+契約 guard（非方案 A 造假 fallback、非 choke point 重構）。picker 對無法解析時間的文差異化 decay（芽芽 0.6/無關 0.3，`_is_parseable_time` 復用 _FMTS）。撞 P108「排除無日期文」可信度契約（test_report_content_trust），阿喜裁折衷 A：芽芽無日期文破例進池、無關仍排除。全套 474→488 passed。新 blindspot B-024（改行為前查測試/契約，非只程式消費點）。Exit F 端到端待 cron/run-now 驗。
- **2026-06-14**：P111 CI 報告自癒收官（飛輪 L4→可控 L5）。self-heal 偵測 canonical 報告缺漏→自動 replay 重產 candidate→跑與 cron 逐位元同源的發布閘門（`should_promote` 純函數共用 + `run_checks` 同尺）→通過才 promote，否則 no-op 降級 L4。零 LLM/零重爬/不繞閘門。動工時親核呼叫鏈揪出凍結計畫 S1(c) 字面修法會讓 cron 失去 sidecar（測試抓不到的 G2 綠燈假象）→阿喜核准修法 A（sidecar 綁定 promote_candidate 發布事件）+登記 P111.1 補遺。4 視角對抗審查 3/4 contract_met、1 條 B 級假保證（ui_previews 真 repo 寫入未被三隔離覆蓋）已修並實證。全套 504→514 passed。新登記 R-037（self-heal 邊界 + 主根因 main.py:728 吞例外未治本 + 原 R8 退化保真）、R-038（no-op candidate 進版控，cron 既有非惡化）。新 blindspot B-027。Postmortem 4 通則（L5 窄面/同源閘門/前提機器化/生命週期綁定）。
