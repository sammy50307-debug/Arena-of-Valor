# 🏛️ 12 層品質優化框架 (12-Layer Quality Framework)

**版本**：v1.0 / 凍結日期：2026-05-03 / 起源：Phase 65 計畫期

> **定位**：本檔為「軟體工程品質的 12 層完整稽核標準」，凡 Phase 開工前必須逐層走過、紀錄該 Phase 動到的層級與緩解措施，避免單純看代碼正確但忽略測試/可觀察性/韌性等隱性缺口。

---

## 📜 使用協議

1. **每個新 Phase 開工前**，AI 必須在草案中逐層列出「本 Phase 要動哪幾層、各層採哪些優化項、各層風險為何」。
2. **每個 Phase 收官前**，AI 必須回頭逐層檢驗實際落地項，缺漏入 TASK_HISTORY 補錄章節。
3. **層級不適用時要明說「N/A 因為 X」**，不能跳過不提。
4. **本框架優於個人偏好**：若主公要求某層省略，需在該 Phase 的計畫書明文記錄豁免理由。

---

## 🌐 12 層全景圖

| # | 層級 | 核心問題 | 何時觸發 |
|---|---|---|---|
| 1 | 代碼層 (Code) | 「這段程式寫得乾淨嗎？」 | 任何修代碼的 Phase |
| 2 | 邏輯層 (Logic) | 「演算法/業務規則對嗎？」 | 含演算法/業務規則的 Phase |
| 3 | 架構層 (Architecture) | 「模組分工合理嗎？」 | 新增模組或重構的 Phase |
| 4 | 測試層 (Testing) | 「壞了會被測出來嗎？」 | 任何修代碼的 Phase |
| 5 | 資料層 (Data) | 「資料完整、可追溯、可遷移嗎？」 | 動到 schema / 儲存的 Phase |
| 6 | 可觀察性層 (Observability) | 「線上壞了找得到嗎？」 | 上線跑的 Phase |
| 7 | 韌性層 (Resilience) | 「外部壞了系統會崩嗎？」 | 依賴外部 API/服務的 Phase |
| 8 | 效能層 (Performance) | 「會不會慢/吃資源？」 | 涉及大量資料/即時體驗的 Phase |
| 9 | UX/A11y 層 | 「人類用得舒服嗎？」 | 涉及前端/UI 的 Phase |
| 10 | 安全層 (Security) | 「會被攻擊或洩漏嗎？」 | 處理使用者輸入/外連/儲存敏感資料的 Phase |
| 11 | 部署層 (DevOps) | 「壞了能回滾嗎？」 | CI/CD/排程相關的 Phase |
| 12 | 成本層 (Cost) | 「外部 API 燒錢嗎？」 | 用付費服務/LLM 的 Phase |

---

## 🧩 各層詳細優化項清單（41 項 checklist）

### 1. 代碼層 (Code) ─ 6 項
- **C1** Pydantic schema 守門：模組入口用 `BaseModel` 驗證，欄位缺失立刻 raise
- **C2** Atomic write：寫檔走 `tmp + os.replace`，避免半寫入損毀
- **C3** 純函式 + 注入式設計：無副作用、依賴從參數注入，方便 unittest mock
- **C4** I/O 併行化：多個外部請求用 `asyncio.gather` 並行，避免序列等待
- **C5** TTL cache：重複爬取/計算用 `functools.lru_cache` + TTL，省成本
- **C6** Structured logging：用 `logger.info(extra={...})` 帶結構欄位，未來 debug 不用猜

### 2. 邏輯層 (Logic) ─ 6 項
- **L1** 鍵值正規化：URL 去 `utm_*` / `fbclid` / 結尾 `/` / `#` 後再比對
- **L2** 平手破局規則：分數相同時依「時間 > 焦點 > 多樣性」三層 tiebreak
- **L3** 多樣性配額：避免單一來源/平台/類別洗版，強制分佈
- **L4** 時間衰減：純 score 排序會讓舊資料反覆上榜，加 recency decay
- **L5** 最低分門檻：寧缺勿濫，不夠時用 placeholder 而非塞垃圾
- **L6** 模糊去重：標題相似度 >85% 視為同一篇（`difflib.SequenceMatcher`）

### 3. 架構層 (Architecture) ─ 3 項
- **A1** 焦點/權重 boost 機制：核心目標物件可提權但不能跨級碾壓
- **A2** 黑名單機制：手動加入「絕不顯示」清單，picker 第一步就過濾
- **A3** 區域/類別平衡：依專案戰場主視角分配配額

### 4. 測試層 (Testing) ─ 5 項
- **T1** 單元測試：核心函式至少 12 cases，覆蓋邊界
- **T2** 契約測試：用 `hypothesis` 自動生成邊界資料驗證 schema
- **T3** E2E 測試：跑完整 pipeline 後 grep 輸出驗證 DOM/結構
- **T4** Snapshot test：鎖死視覺/輸出格式
- **T5** Mutation testing：用 `mutmut` 驗測試強度

### 5. 資料層 (Data) ─ 4 項
- **D1** Schema 版本化：JSON 檔頂層加 `schema_version: 1`，未來遷移有依據
- **D2** 保留策略：滾動視窗 + 月歸檔，避免無限長大
- **D3** 資料譜系 (lineage)：每筆資料留 `source_chain` 追溯經過哪些模組
- **D4** 髒資料隔離：異常入 `data/_quarantine/`，不污染主流程

### 6. 可觀察性層 (Observability) ─ 3 項
- **O1** 結構化決策 log：每次重要選擇（誰被踢、為何）寫 log 留痕
- **O2** Metric 收集：每日記錄關鍵指標（如 `dedup_rate` / `boost_count`）
- **O3** 異常告警：當輸出全空/全異常時推播時加 `⚠️` 警示

### 7. 韌性層 (Resilience) ─ 3 項
- **R1** Fallback 機制：依賴檔損毀時降級到簡化模式，不爆主流程
- **R2** Timeout：所有外部請求設超時，失敗改顯示預設值
- **R3** 灰色降級：核心功能死光時仍能跑 placeholder 模式

### 8. 效能層 (Performance) ─ 2 項
- **P1** 演算法複雜度評估：標註最壞 case 的 Big-O，超 O(n log n) 需優化
- **P2** Lazy load：非首屏資源延後載入

### 9. UX/A11y 層 ─ 3 項
- **U1** ARIA 標籤：螢幕閱讀器友善（`aria-label`, `role`）
- **U2** Reduced-motion：尊重 `prefers-reduced-motion`，關閉動效
- **U3** 色盲友善：顏色資訊同時用圖示/文字輔助

### 10. 安全層 (Security) ─ 2 項
- **S1** XSS 防護：Jinja2 預設 autoescape，禁用 `|safe` on 使用者資料
- **S2** 外連加固：所有外連 `rel="noopener noreferrer nofollow"` + `target="_blank"`

### 11. 部署層 (DevOps) ─ 2 項
- **V1** Feature flag：新功能開關 env var，CI 跑通才開
- **V2** Rollback 路徑：保留前一版檔案/分支，異常可秒切回

### 12. 成本層 (Cost) ─ 2 項
- **B1** 配額預算：外部 API/爬取設每日上限
- **B2** 大小監控：索引/快取檔超閾值觸發 prune

---

## 🛡️ 風險清單共通模式

每層都應檢查：
- **環境/外部依賴風險**：無法 100% 由代碼解，需實測收尾
- **代碼可控風險**：可用設計/測試直接消除
- **內容/業務風險**：需主公裁示的取捨

---

## 📋 Phase 開工模板（必填）

```markdown
### Phase XX 12 層稽核表

| 層級 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| 代碼層 | C1, C2, C3 | ... | ... |
| 邏輯層 | L1, L2 | ... | ... |
| ... | ... | ... | ... |
| **N/A 層級**：效能層 | — | 本 Phase 純文件改動，無效能影響 | — |
```

---

*本框架受「無損技術存檔協議」保護，修訂需經主公核准並更新版本號。*
