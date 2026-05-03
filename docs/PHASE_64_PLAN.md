# Phase 64 — Cache 高層化重構 + 配額韌性強化

- **建立日期**：2026-05-03
- **凍結日期**：2026-05-03
- **過期日期**：2026-08-03（3 個月內未動工自動失效）
- **影響等級**：標準（6-7 檔案）
- **不可逆動作**：無
- **動工先決**：主公口頭確認「P64 動工」
- **前置依賴**：P63.4 已收官（已 push）

---

## 1. 背景與動機

### 1.1 觸發事件
2026-05-03 視窗執行 P63.4 C-B 驗收時，連續觸發 Gemini API 429 配額耗盡：
- 3 個備援模型（gemini-2.0-flash / 2.0-flash-lite / 2.5-flash）全部 429
- 兩輪重試（60s + 120s wait）後仍 429
- 觸發 showcase 斷路器，產出非 production 報告

### 1.2 根本原因（批判思考 — 區分症狀與根因）
- **症狀**：429 quota exhausted
- **根因**：cache key 設計使其對「每日例行跑」完全失效
  - 現行 cache key = `MD5(system_prompt + user_prompt)`
  - `user_prompt` 包含每篇貼文實際內容（每天不同）
  - 結果：每日跑都全部 cache miss，每次都打滿 LLM 呼叫
- **附帶發現的 Bug**：main.py 漏 `git add data/llm_cache.json`，Fallback Push 撿尾包，產生雙 commit（已於本視窗修補 commit `b352fd8`）

### 1.3 目標
- 設計**高層快取（hero+date）**，當天同英雄只需一次完整分析
- 配額**韌性三件套**降低觸發 429 機率
- C-B 驗收能穩定通過（cache hit ≥80%、mode: production）

---

## 2. 核心設計

### 2.1 雙層快取架構

```
L1 高層快取（hero level）— 主力
  key:   hero:{hero_name}:{YYYY-MM-DD}
  value: 整個英雄當天的分析結果（list of analyzed posts）
  命中：跳過整個 batch_chat 批次（零 LLM 呼叫）

L2 低層快取（prompt level）— Fallback / 兼容舊資料
  key:   prompt:{md5(system_prompt|user_prompt)}
  value: 單次 LLM 呼叫結果
  命中：跳過單次 chat() 呼叫

每日總結快取
  key:   daily_summary:{YYYY-MM-DD}
  value: 整份 daily_summary 結構

Apify 爬蟲快取（O1）
  key:   apify:{hero_name}:{YYYY-MM-DD}
  value: 該英雄當天爬蟲結果
```

### 2.2 流程圖

```
analyze_posts(hero, posts, date)
  ├─ 查 L1 hero:{hero}:{date}
  │    ├─ HIT  → return cached_result（零 LLM）✅
  │    └─ MISS → 進入 batch_chat
  ├─ batch_chat → 內部走 L2 cache
  ├─ 整批成功 → 寫入 L1
  └─ 整批失敗（429 showcase）→ 不寫 L1（避免污染）
```

### 2.3 Cache 檔案 schema v2

```json
{
  "schema_version": 2,
  "result_schema_version": 1,
  "entries": {
    "hero:亞瑟:2026-05-03": {
      "result": [...],
      "stored_at": "2026-05-03T00:05:12Z",
      "ttl_days": 7
    },
    "daily_summary:2026-05-03": { ... },
    "apify:亞瑟:2026-05-03": { ... },
    "prompt:abc123def...": { ... }
  },
  "stats": {
    "total_l1_hits": 0,
    "total_l2_hits": 0,
    "total_apify_hits": 0,
    "total_misses": 0
  }
}
```

### 2.4 Migration（schema v1 → v2）
- 載入時偵測無 `schema_version`：自動把舊 12 筆 MD5 key 加 `prompt:` prefix 遷移到 `entries`
- Migration 失敗 fallback 到空 cache（不阻斷主流程）
- 寫入 `data/llm_cache.json.bak` 一份備份

### 2.5 TTL 自動清理
- 載入時掃描所有 entry 的 `stored_at`，>7 天直接刪除
- 預設 TTL = 7 天（配置在 `config.py: CACHE_TTL_DAYS = 7`）

---

## 3. 配額韌性三件套

### 3.1 Pre-flight Check
- `batch_chat` 入口前打一個 1-token 輕量請求探活
- 失敗則直接 raise → showcase mode（省去 3 分鐘空等 retry）

### 3.2 降級 Wait 加長
- 現行：`_429_waits = [60, 120]`
- 改為：`_429_waits = [60, 300, 900]`（1min → 5min → 15min）
- 理由：Gemini free tier RPM 通常 1 分鐘 reset，但若 RPD 耗盡需等更久；長 wait 讓 cron 排程跑完，仍可在 30min 內結束

### 3.3 Lockfile 防重複觸發
- `data/.last_successful_run` 紀錄上次 production 模式成功時間戳
- 若 < 30 分鐘前剛跑過，本次 run 直接 return cached report（不重打 API）
- 強制重跑：`--force` flag

---

## 4. 順手優化（O1-O4）

| # | 項目 | 落實 Stage |
|---|---|---|
| O1 | Apify 爬蟲結果快取 | S3 |
| O2 | commit msg 帶 mode + cache hit rate | S4 |
| O3 | 設定參數抽到 `config.py` | S1 |
| O4 | `result_schema_version` 欄位 | S1 |

---

## 5. 盲區三件

### B1 secret 洩漏 grep
- 在 S2 結束時 grep gemini_client.py 確認 log 不含 `?key=` 等 query string
- 若有 → masked 為 `?key=***`

### B2 GHA concurrency group
- 在 `.github/workflows/daily_report.yml` 加：
  ```yaml
  concurrency:
    group: aov-daily-monitor
    cancel-in-progress: false
  ```
- 防主公手快連點兩次 workflow_dispatch

### B3 OPENAI_API_KEY 為空（觀察項）
- GHA log 顯示 `OPENAI_API_KEY: ` 空值
- 目前用不到，記錄起來，未來做 OpenAI fallback（O8）時補

---

## 6. Stage 分解（5 Stage）

| Stage | 內容 | 影響檔案 | 可逆性 |
|---|---|---|---|
| **S1** | 抽 `analyzer/cache_manager.py`：CacheManager 類別、schema v2、migration、TTL 清理、O3/O4 | 1 新檔 + `config.py` | 可逆 |
| **S2** | `gemini_client.py` 改用 CacheManager（L2 等價遷移）+ Pre-flight + 降級 wait + B1 secret 檢查 | 1 改 | 可逆 |
| **S3** | `sentiment.py` L1 入口/出口 + daily_summary cache + `crawler/apify_client.py` Apify cache + Lockfile | 2-3 改 | 可逆 |
| **S4** | 報告 metadata 加 l1/l2/apify hits + commit msg 強化 + B2 concurrency group | `main.py` + workflow yaml | 可逆 |
| **S5** | 單元測試 5+ cases：L1/L2 hit/miss、migration、TTL 清理、429 不污染、Lockfile | 1 新測試檔 | 可逆 |

**影響半徑**：6-7 檔（標準級）

---

## 7. 17 層稽核表

| # | 層 | 適用 | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|---|---|
| 1 | 代碼 (S) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | 邏輯 (S) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | 架構 (A) | ✅ | ✅ | — | ✅ | — | — |
| 4 | 測試 (S) | ✅ | — | — | — | — | ✅ |
| 5 | 資料 (A) | ✅ | ✅ migration | — | — | — | ✅ |
| 6 | 可觀察性 (A) | ✅ | ✅ stats | — | — | ✅ metadata | — |
| 7 | 韌性 (A) | ✅ | ✅ TTL | ✅ retry | ✅ Lockfile | — | ✅ |
| 8 | 效能 (B) | ✅ | ✅ TTL 防膨脹 | — | ✅ apify cache | — | — |
| 9 | UX | N/A | — | — | — | — | — |
| 10 | 安全 (S) | ✅ | — | ✅ B1 secret grep | — | — | — |
| 11 | 部署 (B) | ✅ | — | — | — | ✅ B2 concurrency | — |
| 12 | 成本 (B) | ✅ | — | — | ✅ apify+L1 | — | — |
| 13 | 可維護性 (A) | ✅ | ✅ 抽 CacheManager | — | — | — | — |
| 14 | 文件 (A) | ✅ | ✅ cache_policy.md 更新 | — | — | — | — |
| 15 | 流程 (A) | ✅ | ✅ Phase Plan + Postmortem | — | — | — | ✅ |
| 16 | 隱私 | N/A | — | — | — | — | — |
| 17 | i18n | N/A | — | — | — | — | — |

**META4 風險加權**：標準級 + 無不可逆 + 17 層全覆蓋 = **3 分**（無需請示）

---

## 8. Exit Criteria

| # | 條件 | 驗收方式 | 誰執行 |
|---|---|---|---|
| E-A | 5 Stage 全部 commit + push | `git log` | Claude |
| E-B | 單元測試全綠 | `pytest tests/test_cache_manager.py` | Claude |
| E-C | 本機 dry-run 跑兩次：第二次 L1 hit ≥ 95% | 本機測試 | Claude（需主公提供 API key） |
| E-D | GHA 連跑兩次（間隔 ≥5 min），第二次 mode: production + L1 hit ≥ 80% | GHA Actions | Claude（需配額充足時段） |
| E-E | TASK_HISTORY + Postmortem 寫完 | docs 確認 | Claude |
| E-F | NEXT_SESSION_HANDOFF 更新 | 主公確認 | Claude |

---

## 9. 風險登記

| 風險 | 機率 | 嚴重度 | 緩解 |
|---|---|---|---|
| schema migration 出錯，舊 12 筆 cache 損毀 | 低 | 中 | `.bak` 備份 + 載入失敗自動空 cache |
| L1 cache key 命中過於寬鬆 | 中 | 低 | 接受設計（同一天結果通常穩定）；保留 `--no-cache` flag |
| TTL 清理 bug 誤刪當天 cache | 低 | 中 | 單元測試覆蓋邊界；TTL = 7 天緩衝 |
| 重構觸及 sentiment.py 主流程，潛在回歸 | 中 | 高 | S5 單元測試 + 本機 dry-run 兩次驗證 |
| GHA Gemini 配額仍不足 | 高 | 中 | 配額三件套降低觸發；最差情況 P65 做 OpenAI fallback (O8) |
| Apify cache key 設計沒考慮抓不同 hashtag | 中 | 低 | key 設計可擴充 `apify:{hero}:{tag}:{date}` |

---

## 10. 影響半徑表

| 檔案 | Stage | 改動類型 |
|---|---|---|
| `analyzer/cache_manager.py`（新） | S1 | 新增 |
| `config.py` | S1 | 加參數 |
| `analyzer/gemini_client.py` | S2 | 重構 cache 介面 |
| `analyzer/sentiment.py` | S3 | 加 L1 入口出口 |
| `crawler/apify_client.py` | S3 | 加 Apify cache（檔名待 S3 確認） |
| `main.py` | S4 | metadata + Lockfile |
| `.github/workflows/daily_report.yml` | S4 | concurrency group |
| `tests/test_cache_manager.py`（新） | S5 | 新增 |

**合計**：6-7 檔（標準級）

---

## 11. 後置不做（明列以防漂移）

P64 不做、留待後續：
- **O5** 每日健康巡檢 GHA → 獨立 P66
- **O6** partial result 保護 → P65 候選
- **O7** 多 API key 輪換 → P65 候選
- **O8** OpenAI fallback → 觀察期再決定
- **O9** SQLite 取代 JSON → 條目 > 1000 筆才考慮
- **O10** state checkpoint → 觀察期
- **O11-O20** 全部後置

---

## 12. 動工檢查表

進入 S1 前確認：
- [ ] 主公口頭「P64 動工」
- [ ] P63.4 C-B 已驗收完（或主公確認 P63.4 不阻擋 P64）
- [ ] 本機 git status 乾淨
- [ ] 本視窗 Token 充足（建議 > 80% 才起手）

---

## 13. 收官 Checklist

- [ ] 5 Stage 全部 commit + push
- [ ] E-A ~ E-F Exit Criteria 全打勾
- [ ] TASK_HISTORY.md 加 P64 紀錄（cat >> heredoc）
- [ ] `docs/postmortems/2026-XX-XX-phase-64-cache-hierarchy.md` 寫完
- [ ] NEXT_SESSION_HANDOFF 更新到 P65 候選
- [ ] G6 失誤學：本 Phase 是否有「我以為」清單需通則化

---

*本計畫書於 2026-05-03 視窗凍結，下視窗開工。*
