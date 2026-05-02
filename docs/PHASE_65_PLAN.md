# 📋 Phase 65 — 最新動態 5 卡精準推送 (Top-5 News Cards)

> **基於 PHASE_TEMPLATE.md v1.0 (混合版) 生成**

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P65 |
| **Phase 名稱** | 最新動態 5 卡精準推送 (Top-5 News Cards) |
| **凍結日期** | 2026-05-03 |
| **影響半徑** | **重大 (10+ 檔)** ─ META3 全層稽核 |
| **預估投入時數** | 6-8 小時（分 5 Stage） |
| **Token budget** | ~30K tokens（picker + index + template + tests） |
| **負責模型** | Opus 4.7（架構判斷）+ Sonnet 4.6（落地實作） |

---

## 1. 目標 (Objective)

把報表頁「最新動態詳情」區塊由 fallback 三層 chain（posts → hero_focus_posts → top_links）改造為 **每日固定 5 張可點擊新聞卡**，每卡直連原文，跨日去重，含「↻ 重複」三級徽章標記。

## 2. 觸發背景 (Why Now)

主公觀察到報表頁右側「最新動態詳情」常顯示「今日暫無相關動態」空狀態，雖然 raw 資料有 12 筆但模板未善用。截圖顯示空態出現在 2026-05-03，主公要求改造為 5 張可點擊卡片，並擔憂連結點進去結果只到入口網站非原文。

## 3. Entry Criteria（入口條件）─ STR4

- [x] 前置 Phase 已收官：Phase 63.3 Landing Page 指揮中心、Phase 63.3.1 補遺
- [x] 資料/依賴已備：raw_*.json 已有 `score` 欄位（0.70-0.98 浮點）、模板已有點擊 anchor
- [x] 主公已核准：2026-05-03 視窗對話確認 Q1-Q5 + 17 項風險全採
- [ ] 風險登記簿無未解高風險：⚠️ R7 Phase 63.2 LINE 滑動失靈未解，已決議「並行推進」(主公裁示 b)

## 4. Exit Criteria（退出條件）─ STR3

- [ ] **資料層**：5 篇文章從 raw 檔依 `score × decay × boost` 排序產出，跨日去重
- [ ] **視覺層**：5 張卡渲染含標題 + 平台 logo + 情緒標籤 + 摘要(60字) + 時間
- [ ] **健康層**：O7 連結預檢通過，所有 url 回 200（4xx/5xx 自動降級替補）
- [ ] **跨端層**：桌面 / 行動端 / LINE 內建瀏覽器三端渲染正常
- [ ] **驗收層**：主公親點 5 張卡，全部到原文（非聚合頁/入口網站）
- [ ] **測試層**：T1 單元測試 ≥ 12 cases 全綠
- [ ] **編年史**：TASK_HISTORY.md 補錄完整 Phase 65 章節 + Obsidian 鏡像 + push origin/main

## 5. ROI 評估 ─ G4-2

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 6-8 h |
| 預估收益等級 | **高** |
| 收益描述 | (1) 主公每日讀報效率：從「無動態」→ 5 篇精選；(2) 解決 example.com 假連結根因（showcase mode 暴露）；(3) 為未來 RSS 輸出 / 點擊追蹤等延伸功能舖路 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表 ─ META2 強制填表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層** | C1, C2, C3, C4, C5, C6（全採） | 純函式設計失誤致 mock 困難 | C3 注入式設計 + T1 單元測試守護 |
| **2. 邏輯層** | L1, L2, L3, L4, L5, L6（全採） | L4 時間衰減誤殺老牌經典攻略 | R14 緩解：`evergreen_flag` 白名單欄位免衰減 |
| **4. 測試層** | T1（必）, T2（契約）, T3（E2E）, T4（snapshot）；T5 mutation 暫緩 | 測試覆蓋盲區 | 覆蓋率 ≥ 90% 才能進 S5 |
| **10. 安全層** | S1（XSS）, S2（外連加固） | 主公注入 raw 資料含惡意 HTML | Jinja2 autoescape + 禁用 `\|safe` on raw |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層** | A1（焦點 boost）, A2（黑名單）, A3（區域平衡） | A1 boost ×1.2 永久壓制非焦點熱文 | R16 緩解：boost 上限不能跨級碾壓 |
| **5. 資料層** | D1（schema 版本化）, D2（14天滾動 + 月歸檔）, D3（source_chain）, D4（_quarantine） | history_index 損毀 | C2 atomic write + R12 .bak 備份 |
| **6. 可觀察性層** | O1（picker 決策 log）, O2（dedup_rate metric）, O3（全空告警 ⚠️） | log 過量燒磁碟 | structured logging + 滾動切割 |
| **7. 韌性層** | R1（history loss → 當日去重 fallback）, R2（og 抓取 5s timeout）, R3（scraper 全死 placeholder mode） | timeout 設太短誤殺慢站 | R1 從 5s 起步，視實測調整 |
| **13. 可維護性層** | M1（TECH_DEBT 登記 T5 mutation 緩採） | 技術債失控 | M3 重構預算：Phase 70 統包還債 |
| **14. 文件層** | DOC1（picker 模組 docstring）, DOC2（ADR：為何選 score×decay 公式） | 接手者讀不懂 | DOC1 docstring 三段式：為何存在/怎麼用/為何不選 X |
| **15. 流程層** | PR1（用此模板）, PR2（Exit Criteria 已列）, PR3（commit `feat(P65):`）| 流程鬆散 | 嚴守規約 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層** | ✅ 觸發（5 卡渲染 + og 抓圖併行） | P1（O(n log n) 排序）, P2（og 圖 lazy load） | n<50 不需優化 | C4 asyncio.gather 並行 |
| **9. UX/A11y 層** | ✅ 觸發（前端視覺改造） | U1（aria-label）, U2（reduced-motion）, U3（情緒標籤色+圖示） | 行動端可讀性差 | W1 進場動畫分批 + W6 平台 logo 統一品牌色 |
| **11. 部署層** | ✅ 觸發（影響 daily_report.yml） | V1（feature flag `ENABLE_TOP5_NEWS`）, V2（保留 report_legacy.html） | CI 模板渲染爆 | R13 緩解：本地 dry-run 攔截 |
| **12. 成本層** | ✅ 觸發（O6 Open Graph 抓圖） | B1（每日 og 抓圖 ≤ 50 次）, B2（history index >1MB 觸發 prune） | 被目標站當 DDoS | R17 緩解：rate limit 1 req/s/host |
| **16. 隱私/合規層** | ⚠️ 觸發（轉貼第三方文章標題/摘要） | PRIV1（不抓會員專屬內容） | 版權爭議 | 僅顯示連結 + 60 字摘要，不轉錄全文 |
| **17. i18n 層** | ❌ 未觸發 | **N/A** — 戰場為台服，TW 區為主，TH/VN 用既有區域標籤無需新 i18n | — | — |

### 層級互鎖驗證 ─ META5

- [x] 動 Logic 層 → 已動 Testing 層（T1-T4）
- [x] 動 Architecture 層 → 已動 Documentation 層（DOC2 ADR）
- [x] 動 Data 層 → 已動 Maintainability 層（M1 TECH_DEBT）
- [x] 動 Security 層 → 已動 Testing 層（T1 含 XSS regression）
- [x] 動 Performance 層 → 已動 Observability 層（O2 metric）

---

## 7. 跨切面檢查 ─ X1-X4

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 `analyzer/top5_picker.py` | 可逆（刪檔即可） | — |
| 新增 `data/news_history_index.json` | 半可逆（去重歷史會丟） | — |
| 修改 `reporter/templates/report.html` | 可逆（git revert） | — |
| 修改 `reporter/generator.py` | 可逆 | — |
| commit + push origin/main | 半可逆（push 後其他 clone 已同步） | — |
| 刪除 `report_legacy.html` 舊樣板 | **不可逆** | ❌ V2 規定保留，禁止刪 |

**不可逆動作**：無（V2 已要求保留 legacy）

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] log 副作用：picker 每次決策寫入 `logs/top5_decisions.log`（O1）
- [x] 中間檔產出：`data/news_history_index.json` 每日更新（含 .bak 備份）
- [x] 系統狀態變更：feature flag `ENABLE_TOP5_NEWS=true` 寫入 `.env`

### X3 時間敏感性 (Time Decay)

- 本計畫凍結日期：2026-05-03
- 本計畫過期日期：2026-08-03（3 個月，若未動工需重新審視）
- 風險記錄帶日期：✅ 全部 R1-R17 帶 2026-05-03 戳記

### X4 多角度同行審查 (Multi-Role Review)

- **主公視角**：5 張卡可點到原文 ✅、跨日不重複 ✅、UI 與報表既有質感一致 ✅。**通過**。
- **攻擊者視角**：⚠️ R5 score 來源未驗（爬蟲原生 vs LLM 推估）、⚠️ S1 若 raw 資料源被注入 `<script>` XSS 仍需 Jinja2 守住、⚠️ R17 og 抓圖被偵測為爬蟲導致 ban。**待 S1 開工驗證**。
- **接手者視角**：DOC2 ADR 必寫「為何 score × decay × boost 不選別的公式」，半年後新人才能改參數。**通過**。

---

## 8. 風險清單（17 項彙整）

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 真實 url 是聚合頁非原文 | 中 | 高 | 環境依賴 | S5 主公親點驗收 |
| R2 | 去重索引無限長大 | 低 | 低 | 代碼可控 | D2 滾動 14 天 + 月歸檔 |
| R3 | 連續多天無新文章 | 中 | 中 | 業務 | 模板兜底「近期動態冷清」 |
| R4 | showcase 跨日去重全標重複 | 高 | 中 | 代碼可控 | `--bypass-dedup` 旗標 |
| R5 | score 來源不明 | 中 | 中 | 環境依賴 | S2 開工先驗 WaterfallSearcher |
| R6 | yaya-highlight 與「↻ 重複」視覺衝突 | 中 | 低 | 代碼可控 | 重複卡優先級高於 highlight |
| R7 | LINE 滑動失靈沿襲 P63.2 | 中 | 中 | 環境依賴 | S5 LINE 實測 + 並行推進 P63.2 |
| R8 | 三層 fallback chain 與新 picker 衝突 | 高 | 高 | 代碼可控 | S4 明確以新 picker 取代 |
| R9 | url normalize 規則不全 | 中 | 中 | 代碼可控 | L1 去 utm/fbclid/結尾斜線 |
| R10 | 文章被原作者刪除 → 404 | 中 | 中 | 環境依賴 | O7 健康預檢自動降級 |
| R11 | LINE 反詐騙改寫外連 | 中 | 低 | 環境依賴 | 已知特性，無解 |
| R12 | history_index 損毀 | 低 | 高 | 代碼可控 | C2 atomic write + .bak |
| R13 | CI 因模板變動爆 | 中 | 高 | 代碼可控 | 本地 dry-run 攔截 |
| R14 | 時間衰減誤殺老牌經典 | 中 | 中 | 業務 | evergreen_flag 白名單 |
| R15 | fuzzy dedup 誤判 | 低 | 低 | 代碼可控 | threshold 0.85 保守 |
| R16 | boost ×1.2 永久壓制熱文 | 中 | 中 | 業務 | boost 上限不跨級碾壓 |
| R17 | 並行 HEAD 預檢被當 DDoS | 低 | 中 | 環境依賴 | rate limit 1 req/s/host |

**高風險加權檢查（META4）**：
- 高機率高影響：R8（高高）= 4
- 高機率中影響：R4（高中）= 3
- 中機率高影響：R1, R12, R13（各 3）= 9
- 加權分數：**16 分**（遠超 5）→ ⚠️ **須暫停請示主公**

> ⚠️ **META4 觸發**：本 Phase 加權 16 分，主公已於草案討論期確認接受所有風險，本警示已紀錄於凍結戳記。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S1 偵察** ✅ | 已完成（資料層真相 1-5） | R5 部分釐清 | 報告已提交 |
| **S2 picker 主邏輯** | `analyzer/top5_picker.py` 含 score×decay×boost + L1-L6 + A1-A3 | R6, R8, R9, R14, R15, R16 | T1 ≥ 12 cases 全綠 |
| **S3 history_index** | `data/news_history_index.json` + atomic write + .bak | R2, R4, R12 | 連跑 3 天 url 不重複 |
| **S4 模板 5 卡 block** | 模板重寫 + W1-W6 視覺 + O3-O5/O8-O9 + U1-U3 a11y | R3, R6, R8, R13 | 0/3/5 篇三情境視覺正確 |
| **S5 跨端 + 真實連結驗收** | 桌面/行動/LINE 三端 + 主公親點 5 連結 + R7 P63.2 滑動並行測試 | R1, R7, R10, R11, R17 | 主公親口 ✅ |

---

## 10. 影響檔案清單 ─ STR7

**新增**：
- `analyzer/top5_picker.py`（picker 主邏輯）
- `analyzer/url_normalizer.py`（L1）
- `analyzer/news_history_indexer.py`（D2 + C2）
- `data/news_history_index.json`（去重索引）
- `data/url_blacklist.json`（A2）
- `tests/test_top5_picker.py`（T1, T2）
- `tests/test_news_history_indexer.py`
- `tests/snapshots/top5_render_snapshot.html`（T4）
- `docs/adr/001-top5-scoring-formula.md`（DOC2）

**修改**：
- `reporter/templates/report.html`（5 卡 block 重寫，+150/-30 預估）
- `reporter/generator.py`（注入 picker 結果，+50 行）
- `config.py`（新增 `HERO_BOOST_FACTOR`, `ENABLE_TOP5_NEWS`, `OG_FETCH_DAILY_LIMIT`）
- `.env.example`（feature flag 範例）

**刪除**：
- 無

**影響但未直接修改**：
- `reporter/templates/components/*`（若有共用元件）
- `.github/workflows/daily_report.yml`（CI 跑得通才行）
- LINE 推播戰報（5 卡會出現在每日推播）

---

## 11. Postmortem 預埋點 ─ G6

收官後若觸發以下情境必寫 Postmortem：
- [ ] 主公中途否決重來（特別是 W2 boost 公式）
- [ ] S5 主公親點 5 連結，任一張未到原文
- [ ] LINE 內建瀏覽器渲染失常導致 5 卡完全打不開
- [ ] CI daily_report.yml 因模板變動爆且未在本地 dry-run 攔截

Postmortem 位置：`docs/postmortems/2026-MM-DD-phase-65-<topic>.md`

---

## 12. 凍結戳記

- **凍結人**：主公（核准）+ Opus 4.7（草擬）
- **凍結時間**：2026-05-03
- **凍結後變更**：禁止；如需修改，新增章節「Phase 65.X 補遺」並引用本檔

---

*本計畫書受 17 層品質框架 v3.0 + STR1 戰略通則保護，依 PHASE_TEMPLATE.md v1.0 (混合版) 生成。*
