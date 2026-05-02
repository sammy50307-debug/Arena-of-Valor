# 📋 PHASE 63.4 計畫書 v0.4（凍結版）

> **每日 CI 報告 Showcase 模式根因修復 — concurrency / git config / cache commit 三 Bug**

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P63.4 |
| **Phase 名稱** | 每日 CI 報告 Showcase 模式根因修復（concurrency / git config / cache commit 三 Bug） |
| **凍結日期** | 2026-05-03 |
| **影響半徑** | 標準（5-7 檔，META3，接近 10 檔上限但仍屬標準） |
| **預估投入時數** | 5-6 h |
| **Token budget** | 60-80 K |
| **負責模型** | Sonnet 4.6（修 bug 範圍明確，不需 Opus） |

---

## 1. 目標

讓每日 CI 排程跑出**真實 LLM 分析報告**（非 showcase 預演數據），且 Fallback push 包含 `data/llm_cache.json` 讓快取跨日生效；報告檔頂帶 metadata 一行供主公一眼判真假。

---

## 2. 觸發背景

P63.3 收官後驗證每日 CI 報告，發現連續多日內容皆為 showcase 假資料。2026-05-03 完成根因診斷，鎖定 3 個獨立 Bug：

1. `concurrency=3` 在 GHA 環境瞬間觸發 429 全滅 → 斷路器熔斷切 showcase
2. workflow 的 `git config` 在 `python main.py` 之後才設定（**待 S0 驗證真根因**：可能不只是 user.name/email，而是 remote URL 的 token 注入問題）
3. Fallback `git add` 漏 `data/llm_cache.json`，每天 19 篇全部重打 LLM

---

## 3. Entry Criteria — STR4

開工前必須全部 ✅：

- [x] 前置 Phase 已收官：P64.1 Token 防線 ✅
- [x] 三檔現況已 Read：`gemini_client.py` / `sentiment.py` / `daily_report.yml` ✅
- [ ] **S0 排查階段完成**（cache key 穩定性 / `llm_client.py` 是否走 CI path / `main.py` 內 push 真根因）
- [ ] 主公已核准本 v0.4 草案：2026-05-03 視窗
- [ ] `docs/RISK_REGISTRY.md` 無未解高風險（待查）

---

## 4. Exit Criteria — STR3

達成全部才算收官：

- [ ] **C-A**：本機 dry-run（`python main.py --run-now --limit 5` 等價路徑）sentiment 分析 5+ 篇資料**不觸發 showcase**
- [ ] **C-B**：`workflow_dispatch` 手動觸發 **2 次**（間隔 ≥10 min），第 2 次 cache hit ≥ 80%
- [ ] **C-C**：第一次正規排程跑完，commit 訊息**不出現** `(Fallback)`，報告檔頂 metadata 顯示 `mode: production`
- [ ] **C-D**：主公親點 1 次排程結果驗收
- [ ] **C-E**：5 個 commit hash + 3 個 GHA run URL + metadata 前後對比，全數記入 TASK_HISTORY

---

## 5. ROI 評估 — G4-2

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 5-6 h |
| 預估收益等級 | **高** |
| 收益描述 | 每日報告恢復真實分析；cache 跨日生效後 LLM 呼叫量 19→3-5 次/日（省 70%+ 成本與配額）；不再每日空轉 |
| ROI 結論 | ✅ 值得做 |

---

## 6. 17 層稽核表 — META2

> S+A 共 11 層必填（Patch-1 標準 Phase），B 級依觸發條件保留 DevOps / Cost。

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. Code** | C-簡化（移除 `concurrency=3` 寫死、改吃常數 `CONCURRENCY_LIMIT`） | 改錯併發參數導致正常路徑變慢 | S1a/S1b/S1c 拆三 commit，每 commit 前後跑 timing 對比 |
| **2. Logic** | L-斷路器條件重設：429 → wait **60s → 120s**（exponential，最多 2 次重試） | 重試邏輯可能遮蔽真正配額耗盡 | wait+retry 上限 2 次，超過仍熔斷 |
| **4. Testing** | T-本機 dry-run + workflow_dispatch 2 次 + 排程 1 次驗證；補 429 retry 單元測試 | 本機無法重現 GHA 429 burst | C-B 條件強制 workflow_dispatch 真跑 |
| **10. Security** | S-secrets 不外洩（git config 改位不影響 token 處理） | 改 workflow 順序若誤動 env 區塊洩 secret | diff 只動 git config step + Fallback add，env 區塊不碰 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. Architecture** | N/A：純 bug fix，不動模組分工 | — | — |
| **5. Data** | D-`llm_cache.json` 納入 commit 範圍，跨日持久化 | cache 持續長大佔 repo 體積 | 預埋 TODO：>5MB 警示、>10MB LRU 清理 |
| **6. Observability** | O-增 log：429 wait 秒數、cache hit/miss 統計；**報告檔頂印 metadata 一行** `<!-- cache_hit: X/Y (Z%) | llm_calls: N | mode: production -->` | log 過量灌爆 GHA console | INFO 級別 + 摘要 1 行/批次 |
| **7. Resilience** | R-降併發 1 + 429 wait 60s→120s 重試 2 次（取代立刻熔斷） | wait 拖慢總執行時間 | 19 篇 × 1s 間隔 ≈ 19s 基線，最壞 +180s 仍在 GHA 6h 限額內 |
| **13. Maintainability** | M-併發數抽到單一常數 `CONCURRENCY_LIMIT`，三處共用 | — | — |
| **14. Documentation** | Doc-TASK_HISTORY 補 P63.4 區塊；Postmortem **必寫**；`data/.cache_policy.md` 一頁說明 cache 入版控約定 | — | — |
| **15. Process** | P-依 v3.1 範本走完 S0/S1a/S1b/S1c/S2/S3/S4 共 7 stage | — | — |

### B 級層（觸發條件式）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **11. DevOps** | CI/CD 排程 ✅ | DO-workflow step 順序重排：`git config` 提前到 `Execute AoV Pipeline` 之前；Fallback `git add` 擴展納入 `data/llm_cache.json` | step 重排破壞 checkout→install→run 鏈 | 只移動 `git config` step，不動其他 step 順序 |
| **12. Cost** | LLM API ✅ | Cost-cache 跨日生效後 Gemini 呼叫量降 70%+ | 無 | — |

其餘 B 級（Performance / UX / Privacy / i18n）整列刪除（未觸發）。

### 層級互鎖驗證 — META5

- [x] 動 Logic → 動 Testing ✅
- [x] 動 Security → 動 Testing ✅
- [x] 動 Data → 動 Maintainability ✅
- [N/A] 動 Architecture → 動 Documentation：不動 Architecture
- [N/A] 動 Performance → 動 Observability：不動 Performance 層

---

## 7. 跨切面 X1-X4

### X1 可逆性 — Reversibility

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 改 `gemini_client.py` 併發/重試邏輯 | 可逆（git revert） | — |
| 改 `sentiment.py` concurrency 參數 | 可逆 | — |
| 改 `daily_report.yml` step 順序 | 可逆 | — |
| `git push` 修復後 commit | 半可逆（push 後可 revert，歷史留痕） | — |
| **commit `data/llm_cache.json` 入版控** | **半可逆**（cache 含 LLM 回應，無敏感資料） | ✅ 主公已親口確認 2026-05-03 |

### 5 commit 回滾優先順序（出狀況時依此 SOP）

| Commit | 回滾優先 | 依賴 | 獨立 revert 影響 |
|---|---|---|---|
| **S1a** 併發 3→1 | P1（最先試） | 無 | 回到 burst 狀態，但若 S1b 已上則 retry 仍能救 |
| **S1b** wait 60s→120s 重試 | P2 | 不依賴 S1a，但配合 S1a 才完整 | 回到立刻熔斷邏輯 |
| **S1c** 抽常數 | P3（最後試） | 依賴 S1a + S1b（常數值來自前兩者） | 純重構回滾，行為不變 |
| **S2** workflow git config 移位 | 獨立 P1 | 無 | Fallback 仍在，雙保險不變 |
| **S3** Fallback add cache | 獨立 P1 | 無 | 回到每日 cache miss |

### X2 盲區掃描

- [x] log 副作用：429 wait 60s/120s 時 GHA console 多 ~3 分鐘沉默期
- [x] 中間檔產出：`data/llm_cache.json` 將被 commit 進 repo（首次 commit 體積 +X KB）
- [x] 系統狀態變更：commit 訊息不再帶 `(Fallback)`，可作為「修復成功」自動指標
- [x] 報告 metadata 行可作為未來自動偵測「showcase 復發」的 hook 點

### X3 時間敏感性 — Time Decay

- 凍結日期：**2026-05-03**
- 過期日期：**2026-07-03**（凍結 +60 天）— 之後若 Gemini API quota / pricing 變動需重審 wait 60s/120s 與併發策略
- cache 入版控決策過期日：**2026-08-03**（+90 天）— 屆時若 cache 體積 >5MB 觸發 LRU 重議
- 風險記錄帶日期 ✅

### X4 多角度同行審查

- **主公視角**：3 Bug 拆 5 commit、報告檔頂 metadata 一眼判真假、回滾 SOP 明文 ─ 涵蓋驗收與應變
- **攻擊者視角**：429 wait 60s→120s 若被 API 端持續節流，第 2 次 wait 後仍 429 → 落回原斷路器，不擴大攻擊面；secrets 區塊未動
- **接手者視角**：`CONCURRENCY_LIMIT` 抽常數後改一處即可；`data/.cache_policy.md` 解釋 cache 為何入版控；Postmortem 留 G2-3「我以為」診斷脈絡

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 本機無法重現 GHA 429 burst，修了沒驗證到 | 中 | 高 | 環境依賴 | C-B 強制 workflow_dispatch 真跑 |
| R2 | wait 60s+120s + 併發=1 拖慢執行時間超隱性閾值 | 低 | 中 | 代碼可控 | 加總時長監控 log；GHA 上限 6h 不會撞 |
| R3 | `llm_cache.json` 入版控後體積膨脹 | 中 | 低 | 業務 | >5MB 警示、>10MB LRU 清理（預埋 TODO） |
| R4 | Fallback step 修好後 main.py push 仍失敗（Bug 2 真根因可能不是 git config） | 中 | 中 | 環境依賴 | **S0 排查 main.py push 實作**；Fallback 不刪保留雙保險 |
| R5 | cache key 含時間因素導致 commit 後仍 miss | 中 | 高 | 代碼可控 | **S0 排查 cache key 計算邏輯** |
| R6 | `analyzer/llm_client.py:99` 也走 CI path 同樣 burst | 中 | 中 | 代碼可控 | **S0 排查 llm_client.py 是否被 daily pipeline 呼叫** |

**META4 加權檢查**：
- 高=0×2=0, 中=5×1=5, 低=1×0.5=0.5，**總 5.5 分 ≥ 5**
- ⚠️ **觸發 META4 請示主公**：本 phase 風險集中在「環境依賴」與「診斷正確性」三項中風險（R1/R4/R5），全靠 S0 排查階段化解。**主公確認 S0 排查作為 Entry Criteria 強制項**：✅ 已納入

---

## 9. 工作階段（7 Stages）

| Stage | 內容 | 解掉的風險 | 驗收 | Commit |
|---|---|---|---|---|
| **S0** 排查 | (a) 驗證 cache key 穩定性<br>(b) 確認 `llm_client.py` 是否走 daily pipeline<br>(c) Read `main.py` 內 push 實作確認 Bug 2 真根因 | R4/R5/R6 | 排查報告納入 TASK_HISTORY；若診斷錯誤觸發計畫補遺 | 無（純研讀） |
| **S1a** Bug 1-A | 併發 3→1（僅這一行）`gemini_client.py:36/176/184` + `sentiment.py:184` | R1 主因 | 本機 dry-run 不熔斷 | C1 |
| **S1b** Bug 1-B | 429 wait 60s→120s 重試 2 次 + 補單元測試 | R1 副因 | 單元測試綠 | C2 |
| **S1c** Bug 1-C | 抽常數 `CONCURRENCY_LIMIT` 三處共用 | M | grep 確認單一定義來源 | C3 |
| **S2** Bug 2 | 依 S0 結論修：若是 git config → 移 step；若是 token → 改 push 命令 | R4 | workflow_dispatch commit 訊息無 `(Fallback)` | C4 |
| **S3** Bug 3 | Fallback `git add data/llm_cache.json`；報告檔頂 metadata；新增 `data/.cache_policy.md` | R3 / O | 第 2 次 workflow_dispatch cache hit ≥80% | C5 |
| **S4** 收官 | TASK_HISTORY 補錄 + Postmortem **必寫** + push（push 必問） | — | 主公點頭 + 5 commit hash + 3 GHA run URL 留痕 | — |

---

## 10. 影響檔案清單 — STR7

**修改**：
- `analyzer/gemini_client.py`（~15 行：常數 + 429 wait/retry 邏輯）
- `analyzer/sentiment.py`（1 行：concurrency=3 → 改吃常數）
- `analyzer/llm_client.py`（**S0 排查後決定**，可能 1 行同步調整）
- `.github/workflows/daily_report.yml`（~5 行：git config step 上移 + Fallback add 擴展）
- `main.py`（**S0 排查後決定**，可能修 push 實作）
- 報告生成器（檔頂 metadata 注入點，S0 排查確認位置後修）

**新增**：
- `docs/postmortems/2026-05-XX-phase-63-4-showcase-rootcause.md`（**必寫**）
- `data/.cache_policy.md`（cache 入版控約定，~30 行）

**間接受影響**：
- `data/llm_cache.json` 首次進入版控
- `data/reports/` 後續內容變為真實分析（非 showcase）

**總計**：4-6 檔修改 + 2 檔新增 = **6-8 檔**（仍標準 Phase 範圍）

---

## 11. Postmortem 預埋點 — G6（必寫）

本 phase **強制必寫** Postmortem，主題：

> **「GHA 環境下併發假設不能延用本機開發直覺」**
> ─ G2-3「我以為 concurrency=3 安全」事件已確認發生於診斷階段

通則化進 G6 失誤學季度聚合，候選通則：
- 「跨環境效能假設必須在目標環境驗證」
- 「斷路器熔斷條件必須有重試緩衝，不可一觸即發」
- 「persistent state（cache / artifact）必須與 commit 範圍對齊」

Postmortem 位置：`docs/postmortems/2026-05-XX-phase-63-4-showcase-rootcause.md`

---

## 12. G3 紅色警報 SOP（修復後第一週監控）

修復推上後 **2026-05-XX ~ 2026-05-XX+7 天** 為觀察期：

- **每日 09:00**（台北時間，排程跑完後）主公親檢一次 CI 結果
- 檢查項：
  1. commit 訊息無 `(Fallback)`
  2. 報告檔頂 metadata `mode: production`（非 `showcase`）
  3. cache hit ≥ 50%（首日除外）
- **連敗 SOP**：若連續 2 日任一檢查項失敗：
  ```bash
  # 立刻 disable cron，避免每日 noise commit
  # 編輯 .github/workflows/daily_report.yml，註釋 cron 行：
  #   - cron: '0 0 * * *'   # DISABLED 2026-05-XX 因 P63.4 修復未生效
  git commit -am "ops: 暫停 daily_report cron（P63.4 修復連敗待診斷）"
  git push
  ```
- 觀察期過後（7 日全綠）視為修復確認，本 SOP 解除

---

## 13. 凍結戳記

- **凍結人**：主公（口頭核准）+ Claude（草案撰寫）
- **凍結時間**：**2026-05-03**
- **凍結後變更**：禁止；如需修改，新增章節「Phase 63.4.X 補遺」並引用本檔
- **過期日**：2026-07-03（60 天）

---

*本計畫書受 17 層品質框架 v3.1（63 維度）+ STR1 戰略通則保護，依 `docs/PHASE_TEMPLATE.md` v1.0 範本生成。*
