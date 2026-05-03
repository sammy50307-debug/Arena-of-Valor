# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-03（本視窗 P61.1 + P63.1.1 收官）
- **狀態**：P61.1 / P63.1.x 全收官 ✅，P65 待動工，P64 E-C/E-D 等配額重置

---

## 🔥 下個視窗最優先任務

### T1 — P65 動工（主公已裁示）

**計畫書**：`docs/PHASE_65_PLAN.md`（凍結草案，直接開工）

**目標**：報表頁「最新動態詳情」從空狀態改造為 **每日固定 5 張可點擊新聞卡**，直連原文，跨日去重，含「↻ 重複」三級徽章。

**動工先決**（Entry Criteria 已全過）：
- 主公 2026-05-03 已口頭確認 Q1-Q5 + 17 項風險全採 ✅
- P65 B1 先修（開工第一項，見下）

**B1 先修（開工前第一件事）**：
- 問題：`analyzer/sentiment.py` showcase 路徑 `analyze_posts` 回傳 `list`，`main.py` 預期 `dict`
- 症狀：TypeError 被 outer except 吃掉 → 降級 `_empty_summary` → 報告品質損失
- 位置：[analyzer/sentiment.py](analyzer/sentiment.py) L198（showcase 路徑 `return analyzed`）
- 修法：`return {"posts": analyzed, "is_showcase": True}` 與正常路徑統一

**5 個 Stage**：

| Stage | 內容 | 驗收 |
|---|---|---|
| S1 偵察 | ✅ 已完成（資料層真相 1-5） | — |
| S2 picker 主邏輯 | `analyzer/top5_picker.py`（score×decay×boost） | T1 ≥ 12 cases 全綠 |
| S3 history_index | `data/news_history_index.json` + atomic write | 連跑 3 天不重複 |
| S4 模板 5 卡 block | 模板重寫 + 視覺 + a11y | 0/3/5 篇三情境渲染正確 |
| S5 跨端驗收 | 桌面/行動/LINE 三端 + 主公親點 5 連結 | 主公親口 ✅ |

**Exit Criteria（7 項，全需過）**：
1. 5 篇文章依 score×decay×boost 排序產出，跨日去重
2. 5 張卡渲染含標題 + 平台 logo + 情緒標籤 + 摘要(60字) + 時間
3. O7 連結預檢通過，所有 url 回 200（4xx/5xx 自動降級替補）
4. 桌面/行動/LINE 三端渲染正常
5. 主公親點 5 張卡，全部到原文
6. T1 單元測試 ≥ 12 cases 全綠
7. TASK_HISTORY + Obsidian + push origin/main

---

### T2 — P64 E-C/E-D 驗收（等 UTC 00:00 Gemini 配額重置）

**剩餘 Exit Criteria**：

| # | 條件 | 方式 | 狀態 |
|---|---|---|---|
| E-C | 本機 `--dry-run` 跑兩次，第二次 L1 hit ≥ 95% | `py -3 main.py --dry-run` × 2 | ⬜ 待配額重置 |
| E-D | GHA `workflow_dispatch` 連跑兩次（間隔 ≥5min），第二次 `mode: production` + L1 hit ≥ 80% | GitHub Actions 手動點 | ⬜ 待配額重置 |

**E-C 驗收指令**：
```bash
# 第一次（cache miss，正常打 API）
py -3 main.py --dry-run

# 第二次（L1 應命中，零 LLM 呼叫）
py -3 main.py --dry-run --force
# 觀察 log：「L1 快取命中 (hero:combined:YYYY-MM-DD)」
# 觀察 _meta.l1_hits ≥ 1, llm_calls = 0
```

**E-D 驗收步驟**：
1. GitHub repo → Actions → AoV Daily Monitor → 右上「Run workflow」
2. 等第一次跑完，確認 commit msg 含 `[mode:production ...]`
3. 間隔 ≥5min 再跑第二次
4. 第二次報告第一行：`<!-- l1_hits: X | mode: production -->`

---

## 本視窗完成摘要（2026-05-03）

| Phase | Commit | 內容 |
|---|---|---|
| P61.1 | `f697853` | R20 date sort / R23 deepcopy / R24 mtime cache key，69/69 全綠 |
| P63.1.1 | `220f6ae` | `_update_landing_page` bug×2 修補，第 5 筆 04-28 正確填入 |
| P63.1.1 | `714750b` | git add 補 `index.html`（main.py + GHA yml），自動推播完整 |
| docs | `d76ba8b` | TASK_HISTORY + WIP_PHASES 補錄 |

---

## 後置不做（P65 明列，留後續）

- P65 候選：partial result 保護（O6）
- P65 候選：多 API key 輪換（O7）
- P66：每日健康巡檢 GHA（O5）
- P67 候選：OpenAI fallback（O8，觀察期）
- P68 候選：SQLite 取代 JSON（O9，條目 > 1000 才考慮）
- P63.2：LINE 滑動失靈（等 P65 S5 並行測試）
- P63.3：Landing UI/UX 統一（中長期）
