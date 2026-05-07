# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-07（本視窗 P65 收官）
- **狀態**：P65 收官 ✅（commit `210045c`），**⚠️ 緊急：GitHub Pages 最新動態詳情未顯示**

---

## 🔥 下個視窗最優先任務

### T0 — ⚠️ 緊急排查：GitHub Pages 最新動態詳情無文章

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
| V3 | 右欄「最新動態詳情」顯示 5 張卡 | ⚠️ GitHub Pages 待確認 |
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

## 後置候選（P66+）

- P66：每日健康巡檢 GHA
- P63.2：LINE 滑動失靈
- P67：OpenAI fallback（觀察期）
- P68：SQLite 取代 JSON（條目 > 1000 才考慮）
