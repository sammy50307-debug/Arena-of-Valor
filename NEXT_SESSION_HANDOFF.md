# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-07（本視窗 P65 收官 + P65-hotfix 收官）
- **狀態**：P65 收官 ✅（commit `210045c`） + P65-hotfix 收官 ✅（補 `@keyframes popIn`，根因為老 bug 被 P65 暴露）

---

## 🔥 下個視窗最優先任務

### 🎯 P66.1（已核可、規格凍結）— Top-5 Picker 個人化過濾與來源多樣性

**主公 2026-05-07 核可，先休息，下個視窗直接動工。**

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
2. `config/personal_blacklist.yaml` — 新建（yaml.safe_load）
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

#### Exit 條件

1. picker 29+ 單元測試全綠（原 23 + 新增 6）
2. 本機 dry-run 重生報告，人工確認 5 卡無星展/貝殼幣
3. commit 含 yaml + picker + test + TASK_HISTORY 補 P66.1 段
4. 主公拍板 push

**估時**：30-45 分鐘

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

| Phase | Commit | 內容 |
|---|---|---|
| P65 | `210045c` | Top-5 News Cards 全套實作 |
| docs | `1c30976` | NEXT_SESSION_HANDOFF 更新 |
| docs | `2caeb48` | T0 緊急排查交接筆記 |
| P65-hotfix | (待 push) | 補 `@keyframes popIn`：修右欄 5 卡 opacity:0 老 bug |

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

- **P66.1**（已核可，本檔上方規格凍結）— Top-5 Picker 個人化過濾 + 多樣性
- **P67**（主公 2026-05-07 拍板路線 C）— 「熱門關鍵話題」改真實統計（jieba/CKIP 中文分詞，半天～1 天）
- **P68**（主公 2026-05-07 拍板「動態生成」）— 「今日焦點」fallback 改動態生成（2-3 小時，可複用 P67 統計成果）
- 待重排：每日健康巡檢 GHA、P63.2 LINE 滑動失靈、OpenAI fallback、SQLite 取代 JSON

> P66.1 收官後，主公會回頭詳細規劃 P67/P68。

### 📝 主公 2026-05-07 P65-hotfix 後留下的兩個 UX 議題（待擬草案）

詳見 `memory/project_p66_pending_topics.md`：

1. **Top-5 News Cards 部分文章「沒意義」**：主公感覺右欄某些條目品質低。下次討論前需主公提供具體案例截圖才能對症下藥。
2. **「熱門關鍵話題」這個元件作用是什麼**：主公對該元件用途不清楚。要查資料源 / 用途說明 → 判斷「保留 / 改 / 移除」。
