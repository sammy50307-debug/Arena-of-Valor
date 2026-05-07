# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-07 晚（P66.1 + P67 收官；P68 待動工）
- **狀態**：✅ P66.1 + P67 已完成；P68 規格凍結待動工
- **下個視窗開局**：直接動工 P68（今日焦點動態 fallback，2-3 小時，可複用 P67 platform_breakdown 統計）

---

## ⚡ 下個視窗開局速查（30 秒看完就能動工）

### 本視窗（2026-05-07）做了什麼

| Phase | 狀態 | Commit | 內容 |
|---|---|---|---|
| **P66.1** | ✅ 已 push | `12b557e` | Top-5 Picker 個人化過濾 + 來源多樣性 |
| **P67** | ✅ 已完成 | 本視窗 | 真實熱詞統計（jieba + side panel）|
| **P68 規格** | 📋 凍結 | — | 今日焦點動態 fallback，規格詳見下方 |

### 5/8 早 8:00 GHA 排程驗收清單（主公親點）

GHA 會自動用 P66.1 新代碼生 5/8 報告。打開 landing page 確認：

| # | 驗收條件 | 通過判定 |
|---|---|---|
| V1 | 5 張新聞卡裡**沒有**「星展」「貝殼幣」字樣 | 除非該文也含「芽芽」（豁免） |
| V2 | 5 卡涵蓋 **≥ 3 個不同平台** | 看左下平台標籤 |
| V3 | Dcard 文章在分數接近時**排序略前** | 微觀察 |
| V4 | 報告整體未崩、5 卡都有顯示 | 對照 P65/P65-hotfix 標準 |

⚠️ 如果 V1/V2 不通過 → 開新視窗報主公，回去看 picker log 找原因。

### 下個視窗動工選項

| 選項 | Phase | 估時 | 依賴 |
|---|---|---|---|
| ~~A~~ | ~~P67 真實熱詞統計~~（✅ 已收官）| — | — |
| **B** | **P68 今日焦點動態 fallback** | 2-3 小時 | P67 platform_breakdown 統計可直接複用 |

**建議路徑**：直接動工 P68（Sonnet 4.6）。

---

## 🔥 下個視窗動工任務（規格已凍）

### 🎯 P66.1（已收官，本段保留歸檔）— Top-5 Picker 個人化過濾與來源多樣性

**主公 2026-05-07 核可動工，本視窗已 commit `12b557e` + push + Obsidian 備份。**

#### 規格凍結

| 項目 | 規格 |
|---|---|
| 黑名單初始詞 | `星展`、`貝殼幣` |
| 黑名單比對 | 標題 + 內文 snippet（contains 部分匹配） |
| 黑名單命中 | 完全排除（從候選池踢掉） |
| 🌸 **芽芽豁免** | **`is_yaya_related` 優先於黑名單**（見 `memory/feedback_yaya_priority.md`） |
| 黑名單 log | `logger.info("filtered by blacklist: 星展 | post=...")` |
| Dcard boost | 分數平手時 Dcard 優先進榜（小幅 source boost 1.05~1.10，不壓過主排序） |
| 多樣性目標 | 5 卡至少 3 個不同平台 |
| 多樣性替換範圍 | **只動「2 張一般卡」段**，不動「3 張芽芽卡」 |
| 多樣性 fallback | 候選池不足 → 允許不滿足，log warning |

#### 影響半徑（標準級 3-9 檔）

1. `analyzer/top5_picker.py` — 主邏輯
2. `configs/personal_blacklist.yaml` — 新建（yaml.safe_load）
3. `tests/test_top5_picker.py` — 補 6+ cases（黑名單×2、芽芽豁免×1、多樣性×3、Dcard boost×1）

#### 演算法流程

```
candidates = all_analyzed_posts
↓ [1] 過濾：keep if is_yaya(p) or not blacklist_hit(p)
↓ [2] final_score = relevance × decay × boost(含 Dcard 微 boost)
↓ [3] 分流 yaya_pool / general_pool
↓ [4] yaya: top 3 by score
↓ [5] general: top 2 by score
↓ [6] 多樣性檢查 unique_platforms >= 3?
       若 < 3 且候選池有其他平台 → 替換 general 最低分那張為「未出現平台分數最高」
       若候選池無其他平台 → 接受不滿足 + log warning
↓ [7] 回傳 5 卡
```

#### Exit 條件（✅ 全部達成）

1. ✅ picker **39/39 全綠**（原 23 + P66.1 新增 16，含無限循環迴歸測試）
2. ✅ Smoke test 端到端驗證 5 卡無星展/貝殼幣（dry-run 太久改用合成資料 smoke test）
3. ✅ commit 含 7 檔（configs/yaml + picker + generator + config.py + test + TASK_HISTORY + handoff）
4. ✅ 主公拍板 push（commit `12b557e`，pushed 2026-05-07 晚）
5. ✅ Obsidian TASK_HISTORY 同步備份

**實工時**：約 30 分（含一個實機 bug 修補）

#### 動工期攔截的 bug（記入經驗）

🐛 `enforce_diversity` 在實機 dry-run **無限循環互換**：candidate_pool 含 other_cards 自身 → 被換出的卡又被選回 → web↔youtube 反覆 swap。
- 修法：`swapped_out_urls` set 永久標記 + `max_iterations` 保險 + 補迴歸測試
- 教訓：**單元測試的合成 candidate_pool 應刻意覆蓋「pool 與 selected 重疊」場景**，否則純合成資料會遮蔽此類 bug

---

### 🎯 P67（已核可、規格凍結）— 「熱門關鍵話題」改真實統計（jieba 中文分詞）

**主公 2026-05-07 核可，路線 C，與 P66.1 + P68 連動。**

#### 規格凍結

| 項目 | 規格 |
|---|---|
| 分詞工具 | `jieba` + 自訂詞庫（**不用 CKIP**，PyTorch 太重 GHA 跑不動）|
| 詞庫來源 A | `.agent/skills/hallucination-judge/resources/hero_whitelist.json` v2.3.0（122+ 英雄 + english_aliases）|
| 詞庫來源 B | `configs/aov_terms.yaml`（**新建**，戰隊/賽事/活動術語）|
| 語料範圍 | 當日 fetch 所有文章（未經 P66.1 過濾）|
| 計算單位 | **文章覆蓋率**（同篇文章同詞多次出現只算 1 篇）|
| 詞性過濾 | 名詞 + 動詞（`jieba.posseg`）|
| 停用詞 | `星展`、`貝殼幣`（與 P66.1 黑名單共用 `configs/personal_blacklist.yaml`）|
| 與 AI 關係 | **並存雙欄**：AI 「觀察話題」（語意聚類）+ 統計「真實熱詞」（詞頻）|
| 輸出格式 | **Z：side panel**（點熱詞 → 側欄列所有提及該詞的文章）|
| 排序 | 文章覆蓋數 desc，前 N=10 |

#### 影響半徑（標準級 3-9 檔；實際 8 檔）

| # | 檔案 | 動作 |
|---|---|---|
| 1 | `analyzer/keyword_stats.py` | **新建** — jieba 分詞 + 詞性過濾 + 覆蓋率統計 |
| 2 | `configs/aov_terms.yaml` | **新建** — AOV 戰隊/賽事/活動術語 |
| 3 | `configs/personal_blacklist.yaml` | 與 P66.1 共用（P66.1 先建，P67 import 當停用詞）|
| 4 | `analyzer/sentiment.py` | 改 — 整合 keyword_stats，產 `real_hot_topics` 欄位 |
| 5 | `reporter/templates/report.html` | 改 — 新增「真實熱詞」卡 + side panel HTML/CSS/JS |
| 6 | `reporter/generator.py` | 改 — 傳 `real_hot_topics` + `topic_to_posts` mapping 進模板 |
| 7 | `tests/test_keyword_stats.py` | **新建** — 5+ cases（分詞、停用詞、詞性、覆蓋率、空語料、英雄別名）|
| 8 | `requirements.txt` | 加 `jieba` |

#### Side Panel UX

- 桌機：右側滑入面板，列出該熱詞 mapping 的所有文章標題 + 連結 + 平台
- 行動：底部彈出 modal
- 資料結構：`topic_to_posts: Dict[str, List[post_id]]`（不存全文，避免 HTML 爆肥）

#### 17 層稽核（S+A 必過）

| 層 | 動作 |
|---|---|
| S1 代碼 | jieba 詞典載入 `@lru_cache`，避免每次重載 |
| S2 邏輯 | 覆蓋率口徑：同篇同詞 = 1（用 set 去重）|
| S4 測試 | 5+ cases 覆蓋邊界 |
| S10 安全 | `yaml.safe_load`，路徑硬編碼 |
| A3 架構 | keyword_stats 獨立模組，不耦合 sentiment 既有邏輯 |
| A5 資料 | `topic_to_posts` 存 post_id 不存全文 |
| A6 觀察 | `logger.info("keyword_stats: N posts → M topics")` |
| A7 韌性 | jieba 載入失敗 → fallback 用 AI hot_topics |
| A13 維護 | 詞典更新流程寫 README |
| A14 文件 | TASK_HISTORY P67 段 + handoff 更新 |
| A15 流程 | 標準 Phase 流程 |
| B9 UX | side panel 行動端 fallback modal |

#### Exit 條件

1. `tests/test_keyword_stats.py` 5+ cases 全綠
2. 本機 dry-run 重生報告，主公親點熱詞驗證 side panel 開合
3. AI 「觀察話題」+ 統計「真實熱詞」雙欄並存無衝突
4. commit 含 keyword_stats + aov_terms.yaml + sentiment + template + generator + test + TASK_HISTORY 補 P67 段
5. 主公拍板 push

**估時**：半天 ~ 1 天

---

### 🎯 P68（已核可、規格凍結）— 「今日焦點」fallback 改動態生成

**主公 2026-05-07 核可，與 P67 平行（複用平台統計成果）。**

#### 規格凍結

| 項目 | 規格 |
|---|---|
| 觸發條件 | **只在 `history_delta.alerts` 為空時**觸發；有歷史警報照舊渲染 |
| 資料來源 | **B** top5_news 頭條 + **D** 芽芽相關文章數（含較昨日 ±N）+ **E** 平台熱度（前三平台篇數）|
| 文案組裝 | **解法 B**：模板組句 → AI（Gemini）潤飾成自然中文 |
| 條目數 | **動態 c**：有資料就出、沒資料就略，上限 3 條 |
| 段落結構 | **單段** — label 直接含資訊，advice 取消（去掉 tactical-box）|
| 溢位處理 | **C**：超過 3 條 → 在「台服消息資訊中心」（`overview` 欄位）**下方新開 sub-block**，不覆蓋 overview |
| AI 失敗 fallback | 直接用模板組句（粗糙但不空）|
| 成本 | ~300 token / 日，且只在無歷史警報時觸發 |

#### 影響半徑（標準級；5 檔）

| # | 檔案 | 動作 |
|---|---|---|
| 1 | `analyzer/dynamic_focus.py` | **新建** — B/D/E 收集 + 模板組句 + AI 潤飾 |
| 2 | `analyzer/sentiment.py` | 改 — `alerts` 空時呼叫 dynamic_focus，產 `dynamic_alerts` 欄位 |
| 3 | `reporter/templates/report.html` | 改 — fallback 區改用 `dynamic_alerts`、單段渲染、台服消息資訊中心新 sub-block |
| 4 | `reporter/generator.py` | 改 — 傳 `dynamic_alerts` + `overflow_alerts` 進模板 |
| 5 | `tests/test_dynamic_focus.py` | **新建** — 5 cases（無資料、僅 D、僅 E、滿三條溢位、AI 失敗 fallback）|

#### 17 層稽核（S+A 必過）

| 層 | 動作 |
|---|---|
| S1 代碼 | dynamic_focus 獨立模組，純函數設計 |
| S2 邏輯 | D 的「較昨日 ±N」讀昨日 history_index，缺值 fallback「(首日)」 |
| S4 測試 | 5 cases 含 AI 失敗時退回模板組句 |
| S10 安全 | overview 不被覆蓋（測試 assert）|
| A3 架構 | dynamic_focus 與 P67 keyword_stats 平行，不互依賴 |
| A6 觀察 | `logger.info("dynamic_focus: B=...,D=...,E=...,n_alerts=N,overflow=M")` |
| A7 韌性 | AI 失敗 fallback 模板組句 |
| A12 成本 | ~300 token / 日，只在無歷史警報時觸發 |
| A13 維護 | 模組註解寫清楚 B/D/E 來源 |
| A14 文件 | TASK_HISTORY P68 段 + handoff 更新 |
| B9 UX | 單段文案視覺：去 tactical-box，直接顯示 label 自然句 |

#### Exit 條件

1. test_dynamic_focus 5 cases 全綠
2. dry-run 兩情境：有警報走原邏輯（迴歸）/ 無警報走動態 fallback
3. overview 未被覆蓋（assert）
4. AI 斷網模擬 → 模板組句仍出現
5. commit + TASK_HISTORY 補 P68 段
6. 主公拍板 push

**估時**：2-3 小時（複用 P67 平台統計成果）

---

### T0 — ✅ 已修補（保留下方排查紀錄供查證）：GitHub Pages 最新動態詳情無文章

**收官摘要（2026-05-07）**：
- 根因：`reporter/templates/report.html` 引用 `animation: popIn` 但 `@keyframes popIn` 從未定義（4 月黃金版 V16 起即如此）→ `.post-card` 永遠 `opacity: 0`
- P65 把 `.post-card` 用於右欄 Top-5，首次讓老 bug 浮上水面
- 修法：補 11 行 CSS keyframe 到 template + `aov_report_2026-05-06.html`（升級方案：直接 patch 不重生，零 API 配額）
- 詳見 TASK_HISTORY.md「Phase 65-hotfix」段

**下方為原排查紀錄（保留供日後追溯）**：

**症狀**：主公 LINE 連結點進去，右欄「最新動態詳情」看不到 5 張新聞卡。

**已知事實**：
- 本機 `aov_report_2026-05-06.html` 確認有 5 張 post-card，href 和標題都在
- Git HEAD（`210045c`）的 HTML 也確認有 5 張卡
- 懷疑方向：
  1. GitHub Pages 快取未更新（先請主公強制刷新試試）
  2. GHA 在我 push 之後又跑了一次，用舊代碼覆蓋了 HTML（查 GitHub Actions log）
  3. JavaScript 篩選器把所有卡片隱藏了（查 region filter 初始狀態）

**排查步驟（開局第一件事）**：
```bash
# 1. 查 GitHub Actions 最新一次跑的 commit
# GitHub → Actions → AoV Daily Monitor → 最新一次 run → 看用哪個 commit

# 2. 本機確認 HTML 有 5 卡
py -3 -c "
from pathlib import Path
html = Path('data/reports/aov_report_2026-05-06.html').read_text(encoding='utf-8')
print('post-card 數:', html.count('class=\"post-card'))
"

# 3. 若 GHA 覆蓋了：手動重跑 GHA（用新代碼）
# GitHub → Actions → AoV Daily Monitor → Run workflow
```

---

### T1 — P65 S5 跨端驗收（主公親點）

| # | 條件 | 狀態 |
|---|---|---|
| V1 | 有芽芽文章的日子，左欄「芽芽近期動態」顯示 3 張卡 | ⬜ 待真實資料日驗收 |
| V2 | 無芽芽文章日，左欄顯示「🌸 今天芽芽在森林裡休息喔~」 | ✅ 本機已驗 |
| V3 | 右欄「最新動態詳情」顯示 5 張卡 | ✅ 本機驗證通過（hotfix 後）|
| V4 | 主公親點 5 張卡，全部到原文 | ⬜ 待驗收 |
| V5 | 行動端 / LINE 三端版面正常 | ⬜ 待驗收 |

---

### T2 — P64 E-C/E-D 驗收（等 Gemini 配額重置）

```bash
# E-C：兩次 dry-run 驗 L1 cache
py -3 main.py --dry-run   # 第一次，cache miss
py -3 main.py --dry-run --force  # 第二次，L1 應命中

# E-D：GitHub Actions → Run workflow × 2（間隔 ≥5min）
```

---

## 本視窗完成摘要（2026-05-07）

| Phase | Commit | 狀態 | 內容 |
|---|---|---|---|
| P65 | `210045c` | ✅ pushed | Top-5 News Cards 全套實作 |
| docs | `1c30976` | ✅ pushed | NEXT_SESSION_HANDOFF 更新 |
| docs | `2caeb48` | ✅ pushed | T0 緊急排查交接筆記 |
| **P65-hotfix** | `5605a45` | ✅ pushed | 補 `@keyframes popIn`：修右欄 5 卡 opacity:0 老 bug |
| docs（P66.1）| `56b4c86` | ✅ pushed | P66.1 計畫書凍結到 handoff |
| docs（P67/P68）| `e6fb365` | ✅ pushed | 後置候選更新：P67 真實統計、P68 動態生成 |
| **P63.1.2 hotfix** | `665fbe6` | ✅ pushed | canonical sync SameFileError 修補：解 GHA 連 3 天未更新 landing page |
| **P66.1** | `12b557e` | ✅ pushed | Top-5 Picker 個人化過濾（黑名單+芽芽豁免+Dcard boost+多樣性）+ 動工期攔截 enforce_diversity 無限循環 bug |

### 新 P0 修補：P63.1.2（landing page 凍結）

**根因**：`reporter/generator.py:268` canonical sync 在 GHA 第一次跑當日（aov_report_YYYY-MM-DD.html 不存在）→ output_path == canonical_path → `shutil.copy2` 拋 SameFileError → 整個 try fail → `_update_landing_page` 從未被執行。GHA 5/4/5/5/5/6 三次 commit 都沒帶 index.html。

**修法**：(A) 加 same-file 守衛 (B) 拆 try 把 landing page 與 sync 解耦 (C) 本機 index.html 補成指向 05-06 一併 push。

**驗證**：新增 `tests/test_generator_landing.py`（2 cases 全綠）、本機 simulate GHA 環境、線上 curl 確認 landing 主按鈕 = 05-06 ✅。

**未來行為**：5/8 早上 8:00 GHA 用修補後代碼自動跑，主公開 landing page 應看到 05-08 戰報。若仍卡 05-06，代表還有別的 bug 需追。

**P65 架構**：
- 左欄「芽芽 觀察室」：`top5_yaya`（最多 3 篇芽芽文章卡，無芽芽日顯示休息訊息）
- 右欄「最新動態詳情」：`top5_news`（3 芽芽優先 + (5-N) 一般補滿 = 5 張）
- 排序：`final_score = relevance_score × decay × boost`
- 去重：14 天 history_index，atomic write + .bak
- 舊「🔗 專屬討論連結」已移除

**新增檔案**：
- `analyzer/top5_picker.py`
- `analyzer/url_normalizer.py`
- `analyzer/news_history_indexer.py`
- `tests/test_top5_picker.py`（23 cases 全綠）

---

## 後置候選

- ✅ **P66.1**（已收官 commit `12b557e` pushed 2026-05-07 晚）
- **P67**（規格已凍，本檔上方）— 「熱門關鍵話題」改真實統計（jieba 中文分詞，半天～1 天）
- **P68**（規格已凍，本檔上方）— 「今日焦點」fallback 改動態生成（2-3 小時，可複用 P67 統計成果）
- 待重排：每日健康巡檢 GHA、P63.2 LINE 滑動失靈、OpenAI fallback、SQLite 取代 JSON

### 📝 動工順序建議

| 順序 | Phase | 估時 | 為什麼 |
|---|---|---|---|
| 1 | **P67** | 半天~1 天 | 獨立、無依賴；P68 會複用其平台統計 |
| 2 | **P68** | 2-3 小時 | 複用 P67 平台 group_by 成果，減重複工 |

但若主公想**先觀察 5/8 GHA 跑出的真實 P66.1 報告**再動工，C 選項也合理（避免發現 bug 時 P67/P68 已堆上去難回退）。

---

## 🌟 本視窗（2026-05-07 晚）關鍵交流摘要

供下視窗 AI 快速進入狀況：

1. **P66.1 動工流程暢順**：規格凍結（上視窗）→ 動工 30 分 → 攔截 1 個 bug → 收官。標準流程沒卡關。
2. **P67/P68 設計討論完整**：每個拍板項目都有「為什麼選這個」的理由——下視窗動工時不需重新討論，直接看規格表動手。
3. **路徑微調**：原規畫 `config/personal_blacklist.yaml` 衝突 `config.py`，改 `configs/`（複數）。P67 / P68 也沿用這個目錄。
4. **新增的 picker 公開 API**：
   - `pick_top5(..., record_history=True)`（向後相容）
   - `enforce_diversity(yaya_cards, other_cards, candidate_pool, *, min_platforms=3)`
   - 兩者皆有 docstring + 測試覆蓋
5. **記憶補充**：本次 dry-run 跑太久（>1 分鐘）改用 smoke test。下次動工 P67 jieba 分詞時，要預留時間做真實 dry-run（jieba 分詞效能需驗證）。

---

## ⚡ P69 Ad-hoc 收官補錄（2026-05-07 晚加場）

**Phase 69 — 跨 AI 助理模型選擇指引 v1.1** 已於本日 ad-hoc 動工 + 收官，**插入在 P67/P68 動工之前**。

### 收官重點

- ✅ 主檔 `docs/MODEL_SELECTION_GUIDE.md`（v1.1，含 §8 治理與運維）
- ✅ 三檔同步：~/.claude/CLAUDE.md + ~/.gemini/GEMINI.md + memory/reference_model_guide.md
- ✅ STR6 啟用：新建 `docs/RISK_REGISTRY.md`（R-001~R-003）
- ✅ TASK_HISTORY Phase 69 段已寫入
- ✅ 跑 63 維度 + 3 Patch 完整稽核（命中率 ~93%）
- ✅ commit `c969d49` + push origin/main

### 對下視窗的影響

- **P67/P68 規格不變**，仍可照本檔上方規格動工
- **動工模型建議改用本指引推薦**：P67/P68 都屬「標準 8 檔工程」→ **Sonnet 4.6**（不要用 Opus，省成本；卡住才升）
- commit 流程的 `Co-Authored-By` 欄位**不要再寫死 Opus 4.7**，依當下動工模型填（feedback_workflow.md 已修）

### 新增的長期觀察項（90 天後檢視）

- R-001：三檔同步無自動檢測（手動自律中）
- R-002：Gemini / Anthropic 新模型大版本上線時的腐化風險
- R-003：AI 是否實際遵循「Opus 卡住主動提醒」強制條款（觀察期至 2026-08-05）

### 編號說明

P69 屬於**治理類 ad-hoc Phase**，不在原 handoff 規劃內，但已正式登記為 Phase 69。原 handoff 規劃的「下個 P67 / 後續 P68」**編號維持不變**，下視窗動工順序：

```
P69（已收官）→ P67（待動工，建議 Sonnet 4.6）→ P68（待動工，建議 Sonnet 4.6）
```
