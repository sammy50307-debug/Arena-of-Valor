# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-07（本視窗 P65 收官）
- **狀態**：P65 收官 ✅（commit `210045c`），P64 E-C/E-D 等配額重置，P66+ 候選

---

## 🔥 下個視窗最優先任務

### T1 — P65 S5 跨端驗收（主公親點）

P65 程式碼已 push，GitHub Pages 已更新。**剩最後一關**：

| # | 條件 | 狀態 |
|---|---|---|
| V1 | 有芽芽文章的日子，左欄「芽芽近期動態」顯示 3 張卡 | ⬜ 待真實資料日驗收 |
| V2 | 無芽芽文章日，左欄顯示「🌸 今天芽芽在森林裡休息喔~」 | ✅ 已驗（2026-05-06） |
| V3 | 右欄「最新動態詳情」顯示 5 張卡（3 芽芽優先 + 2 補位） | ✅ 已驗 |
| V4 | 主公親點 5 張卡，全部到原文（非聚合頁） | ⬜ 待真實資料日驗收 |
| V5 | 行動端 / LINE 三端版面正常 | ⬜ 待驗收 |

---

### T2 — P64 E-C/E-D 驗收（等 Gemini 配額重置）

**E-C 驗收指令**：
```bash
# 第一次（cache miss）
py -3 main.py --dry-run

# 第二次（L1 應命中，零 LLM 呼叫）
py -3 main.py --dry-run --force
```

**E-D 驗收步驟**：
1. GitHub repo → Actions → AoV Daily Monitor → 右上「Run workflow」
2. 等跑完確認 commit msg 含 `[mode:production ...]`
3. 間隔 ≥5min 再跑第二次
4. 第二次報告第一行：`<!-- l1_hits: X | mode: production -->`

---

## 本視窗完成摘要（2026-05-07）

| Phase | Commit | 內容 |
|---|---|---|
| P65 | `210045c` | Top-5 News Cards：picker + url_normalizer + history_indexer + 模板 5 卡 + 芽芽觀察室近期動態 + 休息訊息 |

**P65 架構說明**：
- 左欄「芽芽 觀察室」：`top5_yaya`（最多 3 篇芽芽文章卡片）
- 右欄「最新動態詳情」：`top5_news`（3 芽芽 + (5-N) 一般補滿 = 5 張）
- 無芽芽文章日左欄顯示「🌸 今天芽芽在森林裡休息喔~」
- 排序公式：`final_score = relevance_score × decay × boost`（decay=時間衰減, boost=1.2 芽芽）
- 去重：14 天 history_index，atomic write + .bak

---

## 後置候選（P66+）

- P66：每日健康巡檢 GHA（O5）
- P63.2：LINE 滑動失靈（S5 並行測試）
- P67：OpenAI fallback（O8，觀察期）
- P68：SQLite 取代 JSON（O9，條目 > 1000 才考慮）
- P63.3：Landing UI/UX 統一（中長期）
