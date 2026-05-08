# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-08（P70.7 + P70.1 收官）
- **狀態**：✅ P70.7 + P70.1 完成，P70 系列進行中
- **下個視窗開局**：接續 P70 系列，下一個是 P70.3（LINE 滑動失靈）

---

## ⚡ 下個視窗開局速查（30 秒看完就能動工）

### 本視窗（2026-05-08）做了什麼

| Phase | 狀態 | Commit | 內容 |
|---|---|---|---|
| **P70.7** | ✅ 已 push | `40d1874` | 清除 data/ 三個 0-byte raw 殘留（2026-03-23/25/27）|
| **P70.1** | ✅ 已 push | `b9868fb` | Picker 去重懲罰 + 同平台排名衰減 + 芽芽×1.5 bonus |

### P70 系列動工順序（已確認）

```
P70.7 ✅ → P70.1 ✅ → P70.3 → P70.5' → P70.2 → P70.4 → P70.6
```

### 下個視窗動工：P70.3

**內容**：LINE 滑動失靈排查 + 修補  
**估時**：1-2 小時  
**模型**：Sonnet 4.6 起手，偵錯模糊時升 Opus 4.7  
**級別**：微 Phase（S 級）

---

## 🗂️ P70 子 Phase 全覽

| 子 Phase | 內容 | 狀態 | Commit |
|---|---|---|---|
| **P70.7** | 0-byte raw 殘留清理 | ✅ 收官 | `40d1874` |
| **P70.1** | Picker 品質強化（去重懲罰 + 平台衰減）| ✅ 收官 | `b9868fb` |
| **P70.3** | LINE 滑動失靈排查 + 修補 | ⏳ 待動工 | — |
| **P70.5'** | P61.1 統包（R20+R23+R24 cache 邏輯）| ⏳ 待動工 | — |
| **P70.2** | GHA 每日健康巡檢 | ⏳ 待動工 | — |
| **P70.4** | OpenAI fallback | ⏳ 待動工 | — |
| **P70.6** | llm_cache LRU / TTL 機制（預防性）| ⏳ 待動工 | — |

---

## 🔧 P70.1 技術細節（供下視窗 debug 用）

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
| `test_429_retry.py` 2 cases | `GeminiClient._cm` 屬性缺失（P69.1 改 gemini_client.py 後測試未跟上）| ⏳ 待修，建議併入 P70.5' |
| R20/R23/R24 | history-trend-query cache 邏輯瑕疵 | ⏳ P70.5' 統包 |

---

## 🌟 本視窗關鍵決策紀錄

1. **P70.5 SQLite 遷移移除**：技術債健診（2026-05-08）確認 data/ < 200K、無實證痛點、raw post 無互動欄位，SQLite 遷移無 ROI。
2. **P70 拆分 (a) 方案**：依影響半徑機械判斷 S/S+A/全層，不強制全套 63 維度。
3. **dup_factor 梯度**：主公拍板 day1=0.3 / day3=0.2 / day7=0.1（比原提案更嚴格）。
4. **芽芽×1.5**：主公從 ×1.2 升至 ×1.5，確保芽芽即使重複也排最前。
5. **platform_rank 芽芽豁免**：芽芽不佔同平台計數，讓一般文章的平台衰減不受芽芽干擾。

---

## 📋 P70.3 草案要點（下視窗開局讀）

**症狀**：LINE 點開報告後，滑動/觸控失靈（P63.2 遺留問題）。

**排查方向**：
1. `reporter/templates/report.html` 的 touch event handler（`touchstart` / `touchmove` / `touchend`）
2. CSS `overflow` / `position: fixed` 是否阻擋捲動
3. P65 / P67 側邊欄（side panel）新增後是否引入 event 攔截

**開局第一步**：
```bash
grep -n "touchstart\|touchmove\|touchend\|preventDefault\|stopPropagation" reporter/templates/report.html
```

**模型**：Sonnet 4.6 起手；若 touch event 邏輯複雜連 3 輪沒進展 → 升 Opus 4.7

---

*下個視窗讀完此檔即可直接動工 P70.3。*
