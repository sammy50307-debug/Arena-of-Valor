# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-08（P70.5' 收官；75/75 全綠零回歸）
- **狀態**：✅ P70.7 ✅ P70.1 ✅ P70.3 ✅ P70.3.1 ✅ P70.5' 收官；⏳ P71 skill 盤點待動工
- **下個視窗開局**：思考並動工 **P71 — skill 基礎架構建設**（75% 孤兒率治理 + STR9 流程加固）

---

## 🆕 P71 開工前必讀（skill 盤點結果）

### 殘酷真相

20 個 skill 中只有 4 個真在用（代碼引用），1 個有 slash 入口無代碼引用，**15 個是孤兒**（無入口、無代碼引用）。**退化率 75%，G5 抗熵警報嚴重超標**。

### 主公已拍板（2026-05-08）

- **決策 2 ✅** 三層歸檔：`.agent/skills/in-use/`（4 個）+ `.agent/skills/candidate/`（補入口後可用）+ `.agent/skills/_archive/`（90 天觀察）
- **決策 3 ✅** `docs/PHASE_TEMPLATE.md` 加 **STR9**：「新 skill 收官時必須擇一：(a) 接 `.claude/commands/` slash / (b) 被生產代碼 import / (c) 標記為純知識庫並寫入 SKILL_INVENTORY.md」

### 主公保留待新視窗思考

- **決策 1（哪些孤兒補入口）** 暫不裁決，新視窗開局先**仔細思考 skill 基礎架構**（如何系統化運用、避免再生孤兒、有無共用核心模組可抽取）

### P71 建議範圍（待新視窗開局思考細化）

| 階段 | 動作 | 影響檔案 |
|---|---|---|
| **S0 架構思考** | 先想清楚「skill 基礎架構」：分群？共用核心？dispatch 機制？是否可彼此組合？ | 草案文件 |
| **S1 盤點** | 寫 `docs/SKILL_INVENTORY.md`（每個 skill 狀態、依賴、推薦動作） | +1 文件 |
| **S2 補 slash** | 主公點名的 skill 各補 `.claude/commands/<name>.md` | 視主公決策（3-7 檔） |
| **S3 歸檔** | 確定廢棄的 skill 移到 `.agent/skills/_archive/` | mv 數個目錄 |
| **S4 流程加固** | `PHASE_TEMPLATE.md` 加 STR9；`OPTIMIZATION_FRAMEWORK.md` G5-1 加「skill 90 天 idle」條款 | +2 文件 |
| **S5 Postmortem** | `docs/postmortem/P71_skill_orphans.md`（為何 75% 變孤兒） | +1 文件 |
| **S6 風險登記** | RISK_REGISTRY 加 R-009「skill 生產不接入流程」 | +1 行 |

### Skill 現況分類速查

**🟢 真在用（4）**
- `api-quota-guardian` → `scrapers/tavily_searcher.py`
- `hallucination-judge` → `analyzer/keyword_stats.py`
- `history-trend-query` → `analyzer/data_writer.py` + `/trend`
- `hot-deployer` → `.github/workflows/daily_report.yml`

**🟡 半接入（1）**：`nl-to-prompt-structurer`（有 `/prompt` 但無代碼引用）

**❌ 孤兒（15）**：ai-news-radar / auto-proxy-evader / cot-prompt-compactor / daily-diff-radar / firecrawl-dynamic-breacher / html-markdown-distiller / instagram-facebook-dcard-platform-copywriter / multi-thread-synthesizer / rich-push-formatter / semantic-cache-shield / session-handoff-packager / smart-task-router / trend-anomaly-detector / ui-ux-pro-max / waterfall-search-chain

### 邏輯重疊高風險組（需架構思考時併考）

- 爬蟲韌性三胞胎：`auto-proxy-evader` / `firecrawl-dynamic-breacher` / `multi-thread-synthesizer`
- 趨勢偵測雙胞胎：`trend-anomaly-detector` vs `daily-diff-radar`
- Prompt 工程雙胞胎：`cot-prompt-compactor` vs `nl-to-prompt-structurer`

---

## ⚡ 下個視窗開局速查（30 秒看完就能動工）

### 本視窗（2026-05-08）做了什麼

| Phase | 狀態 | Commit | 內容 |
|---|---|---|---|
| **P70.7** | ✅ 已 push | `40d1874` | 清除 data/ 三個 0-byte raw 殘留（2026-03-23/25/27）|
| **P70.1** | ✅ 已 push | `b9868fb` | Picker 去重懲罰 + 同平台排名衰減 + 芽芽×1.5 bonus |
| **P70.3** | ✅ 已 push | `a2a6d39` | LINE 滑動失靈根治（html/body 拆分 + touch-action:pan-y）+ 10 舊報告同步 + index.html 預防性修補 |
| **P70.3.1** | ✅ 已 push | `a2a6d39` | 報告頁加「← 回戰略門戶」按鈕 + R-007（mobile blur）+ R-008（:focus + aria-label）補強；主公 LINE 實機驗收通過 |
| **P70.3 docs** | ✅ 已 push | `ae07746` | postmortem（含第十節）+ RISK_REGISTRY R-006/007/008 + TASK_HISTORY 補錄 |

### P70 系列動工順序

```
P70.7 ✅ → P70.1 ✅ → P70.3 ✅ → P70.3.1 ✅ → P70.5' ✅ → P71 ⏳ → P70.2 → P70.4 → P70.6
```

### 下個視窗動工：P70.5'

---

## 🗂️ P70 子 Phase 全覽

| 子 Phase | 內容 | 狀態 | Commit |
|---|---|---|---|
| **P70.7** | 0-byte raw 殘留清理 | ✅ 收官 | `40d1874` |
| **P70.1** | Picker 品質強化（去重懲罰 + 平台衰減）| ✅ 收官 | `b9868fb` |
| **P70.3** | LINE 滑動失靈排查 + 根治 | ✅ 收官 | `a2a6d39` |
| **P70.3.1** | 報告頁「← 回戰略門戶」按鈕 | ✅ 收官 | `a2a6d39` |
| **P70.5'** | test_429_retry P69.1 技術債（R20/R23/R24 已於 P61.1 落地）| ✅ 收官 | 待 commit |
| **P70.2** | GHA 每日健康巡檢 | ⏳ 待動工 | — |
| **P70.4** | OpenAI fallback | ⏳ 待動工 | — |
| **P70.6** | llm_cache LRU / TTL 機制（預防性）| ⏳ 待動工 | — |

---

## 🔧 P70.5' 統包內容（下視窗直接動工）

### 背景

P70.5 原為 SQLite 遷移，在 2026-05-08 技術債健診中確認無 ROI（data/ < 200K、無實證痛點），已移除。P70.5' 改為處理 **P61.1 遺留的 cache 邏輯瑕疵**（R20/R23/R24）+ 既有技術債 `test_429_retry.py`。

### P70.5' 範圍

| 項目 | 描述 | 來源 |
|---|---|---|
| **R20** | history-trend-query cache 邏輯瑕疵 | P61 遺留 |
| **R23** | （同上，具體見下） | P61 遺留 |
| **R24** | （同上，具體見下） | P61 遺留 |
| **test_429_retry.py 2 cases** | `GeminiClient._cm` 屬性缺失（P69.1 改 gemini_client.py 後測試未跟上）| P69.1 技術債 |

### R20/R23/R24 技術細節

P61 history-trend-query 引入了 L1/L2 cache 機制：
- **L1** = `hero:{name}:{date}`
- **L2** = `prompt:{md5(system|user)}`（L2 一定跨日 miss，因 date 嵌入 prompt）

具體瑕疵需開工時查 P61 TASK_HISTORY 段落確認（grep `### P61` → Read offset）。

### test_429_retry.py 技術細節

P69.1 修改了 `gemini_client.py`，導致 `GeminiClient._cm` 屬性缺失，兩個測試 case 失敗：
- 測試未跟上 P69.1 的 API 改動
- 目前全套：73/73 零回歸（排除這 2 cases）

---

## 🔧 P70.1 技術細節（供 debug 用）

### 新增參數（config.py P70.1 區塊）

| 參數 | 值 | 說明 |
|---|---|---|
| `DUP_PENALTY_DAY1` | 0.3 | 1 天內重複文章懲罰因子 |
| `DUP_PENALTY_DAY3` | 0.2 | 2-3 天重複懲罰因子 |
| `DUP_PENALTY_DAY7` | 0.1 | 4-7 天重複懲罰因子 |
| `PLATFORM_RANK_DECAY` | 0.1 | 同平台每多一篇衰減率 |
| `PLATFORM_RANK_MIN` | 0.3 | 同平台衰減下限 |
| `YAYA_REPEAT_BONUS` | 1.5 | 芽芽重複文章加成（不扣反加）|

### picker metadata 新欄位

每張卡的 `card["picker"]` 新增：
- `dup_factor`：去重懲罰倍率（非重複=1.0，芽芽重複=1.5）
- `platform_rank`：同平台第幾篇（芽芽卡無此欄位）
- `platform_penalty`：同平台降權倍率（芽芽卡無此欄位）

### 芽芽雙豁免規則

1. `is_dup=True` + 芽芽 → `dup_factor=1.5`（加分）
2. 芽芽文章不計入 `platform_seen` 計數 → 一般文章的 platform_rank 不受芽芽影響

### 測試狀態

- `tests/test_top5_picker.py`：45/45 全綠（原 39 + P70.1 新增 6）
- 全套：73/73 零回歸（排除 P69.1 既有失敗的 test_429_retry 2 cases）

---

## ⚠️ 既有技術債（非本 Phase 引入）

| 項目 | 描述 | 狀態 |
|---|---|---|
| `test_429_retry.py` 2 cases | `GeminiClient._cm` 屬性缺失（P69.1 改 gemini_client.py 後測試未跟上）| ✅ P70.5' 已修，75/75 全綠 |
| R20/R23/R24 | history-trend-query cache 邏輯瑕疵 | ✅ P61.1 已落地（renderer.py / time_series_loader.py） |
| Skill 75% 孤兒率 | 20 個 skill 中 15 個無入口無代碼引用 | ⏳ P71 全面治理 |
| GHA 連 2 天（5/7、5/8）無報告 | 原因未排查完（本機無 API key 無法 E-C/E-D 測試）| ⏳ P70.2 排查 |

---

## 🌟 本視窗關鍵決策紀錄

1. **P70.5 SQLite 遷移移除**：技術債健診（2026-05-08）確認 data/ < 200K、無實證痛點、raw post 無互動欄位，SQLite 遷移無 ROI。
2. **P70 拆分 (a) 方案**：依影響半徑機械判斷 S/S+A/全層，不強制全套 63 維度。
3. **dup_factor 梯度**：主公拍板 day1=0.3 / day3=0.2 / day7=0.1（比原提案更嚴格）。
4. **芽芽×1.5**：主公從 ×1.2 升至 ×1.5，確保芽芽即使重複也排最前。
5. **platform_rank 芽芽豁免**：芽芽不佔同平台計數，讓一般文章的平台衰減不受芽芽干擾。
6. **P70.3.1 方案 B**：主公選方案 B（在報告頁加回首頁按鈕），不改 LINE bot 邏輯。

---

## 📋 P70.3 / P70.3.1 收官紀錄（供後續 debug 參考）

### P70.3 根因

`reporter/templates/report.html` 的 `html, body { overflow-x: hidden }` 把 `overflow-x` 套在 `html` 元素上，LINE WebView 將 `html` 視為 viewport scroll container，遇到 hidden 即停止轉發 touch scroll → 整頁滑不動（WebKit bug #153852）。

### P70.3 修法

- `html {}` 只保留 `width: 100%`（移除 `overflow-x: hidden`）
- `body {}` 保留 `overflow-x: hidden` + `-webkit-overflow-scrolling: touch` + 新增 `touch-action: pan-y`

### P70.3.1 修法

- `.back-to-landing` pill：`background: rgba(255,255,255,0.55); backdrop-filter: blur(10px); border-radius: 999px; color: #be185d;`
- 連結：`https://sammy50307-debug.github.io/Arena-of-Valor/`
- R-007：加入 `@media (max-width: 768px)` backdrop-filter 停用 selector
- R-008：`:focus { outline: 2px solid #f472b6; }` + `aria-label="返回戰略門戶首頁"`

### 影響範圍

- template（未來所有新報告）
- `data/reports/aov_report_2026-05-{01..10}.html`（已 push）
- `index.html`（landing page 預防性修補）

---

*下個視窗讀完此檔即可直接動工 P70.5'。*
