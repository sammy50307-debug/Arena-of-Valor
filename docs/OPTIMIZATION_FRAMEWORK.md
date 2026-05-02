# 🏛️ 17 層品質優化框架 (17-Layer Quality Framework)

**版本**：v2.0 / 凍結日期：2026-05-03 / 升級自 v1.0（12 層 → 17 層 + S/A/B 分級 + 元規則 + 戰略通則）

> **定位**：本檔為「軟體工程品質的 17 層完整稽核標準」，凡 Phase 開工前必須逐層走過、紀錄該 Phase 動到的層級與緩解措施，避免單純看代碼正確但忽略測試/可觀察性/韌性/可維護性等隱性缺口。

---

## 📜 使用協議（強化版）

1. **每個新 Phase 開工前**，AI 必須在草案中逐層列出「本 Phase 要動哪幾層、各層採哪些優化項、各層風險為何」。
2. **每個 Phase 收官前**，AI 必須回頭逐層檢驗實際落地項，缺漏入 TASK_HISTORY 補錄章節。
3. **層級不適用時要明說「N/A 因為 X」**，不能跳過不提。
4. **強制填表機制（META2）**：Phase 計畫書若 17 層稽核表有空格，AI 必須拒絕進入「動工期」。
5. **本框架優於個人偏好**：若主公要求某層省略，需在該 Phase 的計畫書明文記錄豁免理由。
6. **稽核版本鎖（META6）**：本框架版本為 v2.0，新增層或修訂規則需主公親自核准 + 框架版本升級。

---

## 🌐 17 層全景圖（含 S/A/B 優先級）

| # | 層級 | 核心問題 | 觸發時機 | 級別 |
|---|---|---|---|---|
| 1 | **代碼層 (Code)** | 程式寫得乾淨嗎？ | 任何修代碼 Phase | **S** |
| 2 | **邏輯層 (Logic)** | 演算法/業務規則對嗎？ | 含業務規則 Phase | **S** |
| 3 | **架構層 (Architecture)** | 模組分工合理嗎？ | 新模組/重構 Phase | A |
| 4 | **測試層 (Testing)** | 壞了會被測出來嗎？ | 任何修代碼 Phase | **S** |
| 5 | **資料層 (Data)** | 資料完整、可追溯、可遷移嗎？ | 動 schema/儲存 Phase | A |
| 6 | **可觀察性層 (Observability)** | 線上壞了找得到嗎？ | 上線跑的 Phase | A |
| 7 | **韌性層 (Resilience)** | 外部壞了系統會崩嗎？ | 依賴外部服務 Phase | A |
| 8 | **效能層 (Performance)** | 會不會慢/吃資源？ | 大量資料/即時 Phase | B |
| 9 | **UX/A11y 層** | 人類用得舒服嗎？ | 涉及前端 Phase | B |
| 10 | **安全層 (Security)** | 會被攻擊或洩漏嗎？ | 處理輸入/外連 Phase | **S** |
| 11 | **部署層 (DevOps)** | 壞了能回滾嗎？ | CI/CD/排程 Phase | B |
| 12 | **成本層 (Cost)** | 外部 API 燒錢嗎？ | 用付費服務/LLM Phase | B |
| 13 | **可維護性層 (Maintainability)** | 6 個月後還改得動嗎？ | 任何修代碼 Phase | A |
| 14 | **文件層 (Documentation)** | 接手者看得懂嗎？ | 任何修代碼 Phase | A |
| 15 | **流程層 (Process)** | Phase 開工/收官流程一致嗎？ | 所有 Phase | A |
| 16 | **隱私/合規層 (Privacy)** | 抓資料/儲存資料合法嗎？ | 涉及第三方資料 Phase | B |
| 17 | **i18n/在地化層** | 多語/多區域支援嗎？ | 跨區域功能 Phase | B |

### S/A/B 級規則

- **S 級（4 層）**：任何 Phase 必過，不過 = 拒絕進動工期。代碼 / 邏輯 / 測試 / 安全
- **A 級（7 層）**：多數 Phase 必過，視 Phase 性質省略需理由
- **B 級（6 層）**：特定 Phase 必過，觸發條件對應才做

---

## 🧩 各層詳細優化項清單（50 項 checklist）

### 1. 代碼層 (Code) ─ S 級 ─ 6 項
- **C1** Pydantic schema 守門：模組入口用 `BaseModel` 驗證，欄位缺失立刻 raise
- **C2** Atomic write：寫檔走 `tmp + os.replace`，避免半寫入損毀
- **C3** 純函式 + 注入式設計：無副作用、依賴從參數注入，方便 unittest mock
- **C4** I/O 併行化：多個外部請求用 `asyncio.gather` 並行，避免序列等待
- **C5** TTL cache：重複爬取/計算用 `functools.lru_cache` + TTL，省成本
- **C6** Structured logging：用 `logger.info(extra={...})` 帶結構欄位，未來 debug 不用猜

### 2. 邏輯層 (Logic) ─ S 級 ─ 6 項
- **L1** 鍵值正規化：URL 去 `utm_*` / `fbclid` / 結尾 `/` / `#` 後再比對
- **L2** 平手破局規則：分數相同時依「時間 > 焦點 > 多樣性」三層 tiebreak
- **L3** 多樣性配額：避免單一來源/平台/類別洗版，強制分佈
- **L4** 時間衰減：純 score 排序會讓舊資料反覆上榜，加 recency decay
- **L5** 最低分門檻：寧缺勿濫，不夠時用 placeholder 而非塞垃圾
- **L6** 模糊去重：標題相似度 >85% 視為同一篇（`difflib.SequenceMatcher`）

### 3. 架構層 (Architecture) ─ A 級 ─ 3 項
- **A1** 焦點/權重 boost 機制：核心目標物件可提權但不能跨級碾壓
- **A2** 黑名單機制：手動加入「絕不顯示」清單，picker 第一步就過濾
- **A3** 區域/類別平衡：依專案戰場主視角分配配額

### 4. 測試層 (Testing) ─ S 級 ─ 5 項
- **T1** 單元測試：核心函式至少 12 cases，覆蓋邊界
- **T2** 契約測試：用 `hypothesis` 自動生成邊界資料驗證 schema
- **T3** E2E 測試：跑完整 pipeline 後 grep 輸出驗證 DOM/結構
- **T4** Snapshot test：鎖死視覺/輸出格式
- **T5** Mutation testing：用 `mutmut` 驗測試強度

### 5. 資料層 (Data) ─ A 級 ─ 4 項
- **D1** Schema 版本化：JSON 檔頂層加 `schema_version: 1`，未來遷移有依據
- **D2** 保留策略：滾動視窗 + 月歸檔，避免無限長大
- **D3** 資料譜系 (lineage)：每筆資料留 `source_chain` 追溯經過哪些模組
- **D4** 髒資料隔離：異常入 `data/_quarantine/`，不污染主流程

### 6. 可觀察性層 (Observability) ─ A 級 ─ 3 項
- **O1** 結構化決策 log：每次重要選擇（誰被踢、為何）寫 log 留痕
- **O2** Metric 收集：每日記錄關鍵指標（如 `dedup_rate` / `boost_count`）
- **O3** 異常告警：當輸出全空/全異常時推播時加 `⚠️` 警示

### 7. 韌性層 (Resilience) ─ A 級 ─ 3 項
- **R1** Fallback 機制：依賴檔損毀時降級到簡化模式，不爆主流程
- **R2** Timeout：所有外部請求設超時，失敗改顯示預設值
- **R3** 灰色降級：核心功能死光時仍能跑 placeholder 模式

### 8. 效能層 (Performance) ─ B 級 ─ 2 項
- **P1** 演算法複雜度評估：標註最壞 case 的 Big-O，超 O(n log n) 需優化
- **P2** Lazy load：非首屏資源延後載入

### 9. UX/A11y 層 ─ B 級 ─ 3 項
- **U1** ARIA 標籤：螢幕閱讀器友善（`aria-label`, `role`）
- **U2** Reduced-motion：尊重 `prefers-reduced-motion`，關閉動效
- **U3** 色盲友善：顏色資訊同時用圖示/文字輔助

### 10. 安全層 (Security) ─ S 級 ─ 2 項
- **S1** XSS 防護：Jinja2 預設 autoescape，禁用 `|safe` on 使用者資料
- **S2** 外連加固：所有外連 `rel="noopener noreferrer nofollow"` + `target="_blank"`

### 11. 部署層 (DevOps) ─ B 級 ─ 2 項
- **V1** Feature flag：新功能開關 env var，CI 跑通才開
- **V2** Rollback 路徑：保留前一版檔案/分支，異常可秒切回

### 12. 成本層 (Cost) ─ B 級 ─ 2 項
- **B1** 配額預算：外部 API/爬取設每日上限
- **B2** 大小監控：索引/快取檔超閾值觸發 prune

### 13. 可維護性層 (Maintainability) ─ A 級 ─ 3 項
- **M1** 技術債登記簿：`docs/TECH_DEBT.md` 列待還清項與優先級
- **M2** 廢棄標記：`@deprecated` 函式留 N 個月 grace period
- **M3** 重構預算：每 5 Phase 預留 1 個小 Phase 還債

### 14. 文件層 (Documentation) ─ A 級 ─ 3 項
- **DOC1** 模組頂部 docstring：說「為何存在 / 怎麼用 / 為何不選 X」
- **DOC2** ADR (Architecture Decision Records)：重大決策記在 `docs/adr/NNN-title.md`
- **DOC3** Runbook：常見故障處置 SOP（如「LLM API 429 怎辦」）

### 15. 流程層 (Process) ─ A 級 ─ 3 項
- **PR1** Phase 計畫書統一模板：凍結後就是這版（見 `docs/PHASE_TEMPLATE.md`）
- **PR2** Phase 退出條件 (Exit Criteria)：明確列「達到 ABC 才算收官」
- **PR3** Commit message 規範：`<type>(P##): <subject>`

### 16. 隱私/合規層 (Privacy) ─ B 級 ─ 2 項
- **PRIV1** 資料來源合法性：爬蟲遵守 robots.txt，不抓會員專屬內容
- **PRIV2** PII 脫敏：使用者 ID/email 等敏感欄位儲存前 hash

### 17. i18n/在地化層 ─ B 級 ─ 2 項
- **I18N1** 文字外部化：UI 字串集中於 `locales/*.json`，避免硬編碼
- **I18N2** 區域分離渲染：TW/TH/VN 模板各自處理日期/貨幣/排版差異

---

## 🧬 元規則（META 規則本身的規則）

| # | 規則 | 內容 |
|---|---|---|
| **META1** | **層級優先級分 S/A/B 級** | 已落地於上方表格 |
| **META2** | **強制填表機制** | Phase 計畫書若稽核表有空格，AI 必須拒絕進入動工期 |
| **META3** | **影響半徑分級** | 動 1-2 檔 = 微 Phase（簡化稽核）、3-9 檔 = 標準、10+ 檔 = 重大（強制全層 + 凍結計畫書） |
| **META4** | **稽核投票權重** | 每層風險評為高/中/低，全層加權 ≥ 5 高風險時須暫停請示主公 |
| **META5** | **層級互鎖規則** | 動 Logic 層必動 Testing 層、動 Architecture 層必動 Documentation 層 |
| **META6** | **稽核版本鎖** | 本框架有版本號 (v2.0)，新增層需主公親自核准 + 框架版本升級 |

### META3 影響半徑分級表

| 半徑 | 動檔範圍 | 稽核標準 | 計畫書 |
|---|---|---|---|
| **微 Phase** | 1-2 檔 | 僅 S 級 4 層 | 簡化版 (對話即可) |
| **標準 Phase** | 3-9 檔 | S + A 共 11 層 | 必須凍結 PHASE_##_PLAN.md |
| **重大 Phase** | 10+ 檔 | 全 17 層 | 凍結 + 主公核准 + 風險登記簿更新 |

### META5 層級互鎖規則表

| 動到的層 | 必須同步動的層 | 理由 |
|---|---|---|
| 邏輯層 (Logic) | 測試層 (Testing) | 業務規則必須有測試守護 |
| 架構層 (Architecture) | 文件層 (Documentation) | 模組分工要 ADR 留痕 |
| 資料層 (Data) | 可維護性層 (Maintainability) | schema 變更要登記 TECH_DEBT |
| 安全層 (Security) | 測試層 (Testing) | 安全修復必須有 regression test |
| 效能層 (Performance) | 可觀察性層 (Observability) | 效能優化要有 metric 驗證 |

---

## 🌍 戰略通則 (STR Cross-Phase Rules)

| # | 通則 | 內容 |
|---|---|---|
| **STR1** | **Phase 計畫書統一樣板** | 凍結 `docs/PHASE_TEMPLATE.md`，新 Phase 用 `cp PHASE_TEMPLATE.md PHASE_##_PLAN.md` 起手 |
| **STR2** | **TASK_HISTORY 章節格式統一** | 每章節必含「目標 / 觸發背景 / 17 層稽核表 / 物理真相 / 風險清單 / 狀態」六塊 |
| **STR3** | **Phase 退出條件 (Exit Criteria)** | 計畫書必含「達到 ABC 三項才算收官」明文條款 |
| **STR4** | **Phase 入口條件 (Entry Criteria)** | 開工前需確認「依賴的前置 Phase 已收官、相關資料已備、主公核准」 |
| **STR5** | **Phase 命名規約** | 主線 P##、子分支 P##.#、補遺 P##.#.#，禁止跳號 |
| **STR6** | **跨 Phase 風險登記簿** | `docs/RISK_REGISTRY.md` 記錄所有 Phase 列管中的風險 |
| **STR7** | **Phase 影響半徑表** | 每 Phase 收官時更新「動了哪些檔 / 影響哪些 skill / 影響哪些既有功能」 |
| **STR8** | **跨 Phase 學習復盤** | 每 5 Phase 跑一次「上 5 個 Phase 哪裡踩雷、17 層哪層最常漏」的復盤章節 |

---

## 📋 Phase 開工模板（必填，符合 META2 強制填表）

```markdown
### Phase XX 17 層稽核表

| 層級 | 級別 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1. 代碼層 | S | C1, C2, C3 | ... | ... |
| 2. 邏輯層 | S | L1, L2, L4 | ... | ... |
| 3. 架構層 | A | A1 | ... | ... |
| 4. 測試層 | S | T1, T2 | ... | ... |
| 5. 資料層 | A | D1, D2 | ... | ... |
| 6. 可觀察性層 | A | O1 | ... | ... |
| 7. 韌性層 | A | R1, R2 | ... | ... |
| 8. 效能層 | B | **N/A** | 本 Phase 為視覺改造，無效能影響 | — |
| 9. UX/A11y 層 | B | U1, U2 | ... | ... |
| 10. 安全層 | S | S1, S2 | ... | ... |
| 11. 部署層 | B | V1 | ... | ... |
| 12. 成本層 | B | **N/A** | 不用付費 API | — |
| 13. 可維護性層 | A | M1 | ... | ... |
| 14. 文件層 | A | DOC1, DOC2 | ... | ... |
| 15. 流程層 | A | PR1, PR2, PR3 | ... | ... |
| 16. 隱私/合規層 | B | **N/A** | 不抓會員資料 | — |
| 17. i18n 層 | B | **N/A** | 中文單語 | — |

### Exit Criteria（退出條件）
- ✅ 條件 A：...
- ✅ 條件 B：...
- ✅ 條件 C：...

### Entry Criteria（入口條件）
- ✅ 前置 Phase 已收官
- ✅ 資料/依賴已備
- ✅ 主公核准
```

---

---

## 🏛️ 治理層 (Governance Tier) ─ 6 維度 / 24 項

> 治理層管「框架本身的健康度 + AI 與主公的協作模式」，是 17 層之外的元維度。

### G1. 規則治理 (Rule Governance) ─ 4 項
- **G1-1** Dead rule detection：每季度掃 `MEMORY.md` / `PROJECT_RULES.md`，標出 90 天未觸發的規則
- **G1-2** Rule conflict 仲裁：兩條規則衝突時明文定義誰優先
- **G1-3** Rule deprecation policy：廢棄規則打 `~~strikethrough~~` 留 30 天 grace，再進 `docs/RULES_GRAVEYARD.md`
- **G1-4** 規則版本鎖：每條規則綁版本號，覆蓋時舊版進歸檔

### G2. AI 認知與行為防火牆 (Cognition) ─ 5 項
- **G2-1** 反偷懶機制：禁止「先做一點點看看」、禁止「我覺得應該可以」憑印象作答
- **G2-2** 認知偏差防火牆：確認偏差 / 近因偏差 / 樂觀偏差三項自我警示
- **G2-3** 「我以為」清單：AI 每次假設必須驗證才能下結論
- **G2-4** 戰術 vs 戰略區分：主公問戰術不主動跳到戰略
- **G2-5** 草案完整度自檢：草案出爐前 AI 自問「主公看了能直接答 Y/N 嗎？」

### G3. 緊急應變層 (Emergency Response) ─ 4 項
- **G3-1** 紅色警報 SOP：資料毀損 / API 全死 / git 斷裂三種頂級災難各有 1-page SOP
- **G3-2** 不可逆動作分級：force push / rm -rf / DROP TABLE 強制四步驟（說明→備份→主公口頭確認→執行）
- **G3-3** 死線檢查清單 (Pre-flight)：破壞性動作前 5 項勾選
- **G3-4** 半夜應變最小可行路徑：主公睡著時遇異常的「停下不做、寫好交接、等天亮」協議

### G4. 量化決策層 (Metrics-Driven) ─ 4 項
- **G4-1** Framework 自身有效性 metric：統計 17 層哪幾層 catch 最多問題 / 最常被漏
- **G4-2** ROI 評估規範：每個優化項標「預估投入時數 / 預估收益等級」
- **G4-3** Token budget per Phase：超 budget 強制拆分
- **G4-4** Prompt cache hit rate：跨對話統計命中率，低於 60% 觸發提示

### G5. 抗熵防範層 (Anti-Entropy) ─ 4 項
- **G5-1** 規則退化警示：每月跑「規則遵守率」自我檢查
- **G5-2** 記憶老化偵測：memory 檔老於 N 天且無觸發，主動建議主公審視
- **G5-3** 跨時間自洽性：過去決策 vs 現在決策衝突時先翻 commit log 找原因
- **G5-4** 檔案漂移監控：規則檔被修但無 commit message 說明，警示

### G6. 失誤學 / 事後檢討 (Postmortem) ─ 3 項
- **G6-1** 踩坑必寫 Postmortem：主公否決重來 / AI 大誤判 / 緊急修復後必寫 `docs/postmortems/YYYY-MM-DD-title.md`
- **G6-2** Blameless 但可學習：不檢討「誰錯」，檢討「制度為何沒擋住」
- **G6-3** Postmortem 通則化：同類錯誤踩 3 次升級為框架規則
- **G6-4** 季度復盤聚合：每季把所有 Postmortem 聚合，看哪 5 大反覆踩坑

---

## 🎯 跨切面 (Cross-Cutting Concerns) ─ 4 項

> 跨切面不是層也不是規則，是貫穿所有層的關注點。

| # | 名稱 | 描述 |
|---|---|---|
| **X1** | **可逆性 (Reversibility)** | 每個動作標「可逆 / 半可逆 / 不可逆」，不可逆需主公親口確認 |
| **X2** | **盲區掃描 (Blind Spot)** | 每 Phase 收官問「主公看不到哪些東西？」（log / 中間檔 / 副作用） |
| **X3** | **時間敏感性 (Time Decay)** | 規則 / 決議 / 風險記錄都帶日期，過期自動標黃 |
| **X4** | **多角度同行審查 (Multi-Role Review)** | 重大決策由 AI 自扮 3 角色（主公 / 攻擊者 / 接手者）各自評一輪 |

---

## 📊 完整框架總覽 v3.0

| 維度 | 數量 | 級別 |
|---|---|---|
| 品質層 (17 層) | 17 層 / 50 項 checklist | 技術層 |
| 元規則 (META) | 6 條 | 規則的規則 |
| 戰略通則 (STR) | 8 條 | 跨 Phase |
| 治理層 (G1-G6) | 6 維度 / 24 項 | 規則的健康 |
| 跨切面 (X1-X4) | 4 項 | 關注點 |
| **總計** | **17 層 + 18 元規則 + 24 治理項 + 4 跨切面 = 63 個維度** | — |

---

## 📊 版本歷史

- **v1.0** (2026-05-03)：12 層初版
- **v2.0** (2026-05-03)：升級為 17 層 + S/A/B 分級 + 6 條 META + 8 條 STR + 50 項 checklist
- **v3.0** (2026-05-03)：加入治理層 G1-G6（24 項）+ 跨切面 X1-X4（4 項），總計 63 維度

---

*本框架受「無損技術存檔協議」保護，修訂需經主公核准並更新版本號。*
