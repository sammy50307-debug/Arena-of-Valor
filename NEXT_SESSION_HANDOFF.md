# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-08（P70.5' 收官；75/75 全綠零回歸）
- **狀態**：✅ P70.7 ✅ P70.1 ✅ P70.3 ✅ P70.3.1 ✅ P70.5' 收官；⏳ P71 skill 盤點待動工
- **下個視窗開局**：思考並動工 **P71 — skill 基礎架構建設**（75% 孤兒率治理 + STR9 流程加固）

---

## 🆕 P71 開工指南（Skill 不朽性建設）

### ⭐ 動工指揮文件

> **完整計畫書：[`docs/P71_PLAN.md`](./docs/P71_PLAN.md)**（v1.0 / 2026-05-08 / Opus 4.7 起草）

新視窗開局必讀順序：
1. 本檔（NEXT_SESSION_HANDOFF.md）
2. **`docs/P71_PLAN.md`**（完整 12 階段計畫 + 17 層稽核 + 10 優化點 + 風險表）
3. `docs/OPTIMIZATION_FRAMEWORK.md` v3.1（63 維度 + 3 Patch）
4. `CLAUDE.md` + `GEMINI.md`（全域 + 專案）
5. `memory/MEMORY.md`

### P71 核心目標（主公 2026-05-08 拍板）

> 「**這些 skill 都可以永久被使用不會消失，使用時機是 LLM 自行判斷不需要我提醒**」

- **G1 永久不滅**：跨 IDE / 跨模型 / 跨時代仍活著
- **G2 自動觸發**：LLM 讀 description schema 自動匹配，無需主公點名

### 12 階段速查（細節見 P71_PLAN.md）

```
P71.0  盤點         (寫 SKILL_INVENTORY.md)
P71.1  治理層       (registry.json + lint + STR9)
P71.2  自動觸發引擎 (★ 4 欄 schema + 觸發協議寫雙家全域檔)
P71.3  自包含化     (★ SKILL.md 永久保險)
P71.4  同步工具     (deploy_skills.py + pre-commit + CI)
P71.5  二級分類     (~/skills-shared/ 跨專案倉庫)
P71.6  路由引擎     (smart-task-router 救活)
P71.7  Dashboard    (SKILL_HEALTH.md 自動生成)
P71.8  diff 裁決    (主公逐一裁決 7 個 Gemini-only)
P71.9  孤兒處置     (8 個 orphan：升級或歸檔)
P71.10 Postmortem   (P50 後規則退化根因)
P71.11 B 級延伸     (版本鎖 / 依賴圖 / Permanent Bundle)
```

### 動工前主公須再拍板的小決策（D1-D6）

詳見 P71_PLAN.md 末尾「動工前主公須再拍板的小決策」表格。

### 7 個 Gemini-only diff 裁決順序（P71.5 用）

```
1. ai-news-radar              (536 行)
2. instagram-facebook-dcard   (388 行)
3. html-markdown-distiller    (92)
4. semantic-cache-shield      (90)
5. trend-anomaly-detector     (70)
6. firecrawl-dynamic-breacher (68)
7. multi-thread-synthesizer   (64)
```

### 重大發現（本視窗勘查）

1. ✅ **Gemini Antigravity 已駐紮 7 個 skill**（不是孤兒，是「跨家移居」）
2. ✅ **P43-P50 黃金期建立過「全域部署」傳統**，P50 後規則退化（G5 抗熵實證）
3. ✅ **Gemini 沒有 slash commands 機制**（自然語言觸發 SKILL.md）
4. ✅ **雙端 7 個 skill 嚴重 diff（66-536 行）**，需主公人工裁決

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
