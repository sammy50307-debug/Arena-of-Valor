# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-08（P70.3 + P70.3.1 全部修補完成，含 R-007/R-008 補強；待主公 LINE 實機驗收）
- **狀態**：✅ P70.7 + P70.1 收官；🟡 P70.3 + P70.3.1 修補完成、待驗收 + commit/push
- **下個視窗開局**：①確認 P70.3 EC3/EC4 驗收結果並 commit/push ②動工 P70.5'

---

## ⚡ 下個視窗開局速查（30 秒看完就能動工）

### 本視窗（2026-05-08）做了什麼

| Phase | 狀態 | Commit | 內容 |
|---|---|---|---|
| **P70.7** | ✅ 已 push | `40d1874` | 清除 data/ 三個 0-byte raw 殘留（2026-03-23/25/27）|
| **P70.1** | ✅ 已 push | `b9868fb` | Picker 去重懲罰 + 同平台排名衰減 + 芽芽×1.5 bonus |
| **P70.3** | 🟡 待 commit/push | — | LINE 滑動失靈：template 拆 html/body + touch-action:pan-y + 10 舊報告同步修補 + index.html 預防性修補 |
| **P70.3.1** | 🟡 待 commit/push | — | 報告頁加「← 回戰略門戶」按鈕 + R-007（mobile blur）+ R-008（:focus + aria-label）補強；template + 10 舊報告全部同步 |

### P70 系列動工順序（已確認）

```
P70.7 ✅ → P70.1 ✅ → P70.3 🟡 → P70.5' → P70.2 → P70.4 → P70.6
```

### 下個視窗動工：先收 P70.3 → 再動 P70.5'

**P70.3 收尾任務**（10 分鐘）：
1. 確認主公 LINE 實機驗收結果（清快取後 5/6 報告是否可滑）
2. 若 OK → 拆兩個 commit + push（見下節「P70.3 commit 計畫」）
3. 若不 OK → git revert 修補 + 升 Opus 4.7 重查根因

**P70.5' 動工**（接續）：見下方「P70.5' 統包內容」

---

## 🗂️ P70 子 Phase 全覽

| 子 Phase | 內容 | 狀態 | Commit |
|---|---|---|---|
| **P70.7** | 0-byte raw 殘留清理 | ✅ 收官 | `40d1874` |
| **P70.1** | Picker 品質強化（去重懲罰 + 平台衰減）| ✅ 收官 | `b9868fb` |
| **P70.3** | LINE 滑動失靈排查 + 修補 | 🟡 待驗收+commit | — |
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

## 📋 P70.3 收尾與 commit 計畫（下視窗讀完即可執行）

### 已完成內容

**根因**：`reporter/templates/report.html` 的 `html, body { overflow-x: hidden }` 把 `overflow-x` 套在 `html` 元素上，LINE WebView 將 `html` 視為 viewport scroll container，遇到 hidden 即停止轉發 touch scroll → 整頁滑不動。

**治本（template）**：拆分 `html, body {}` → 獨立 `html {}` + `body {}`；body 加 `touch-action: pan-y` + WebKit bug #153852 註解

**治標（10 個舊主版報告）**：`data/reports/aov_report_2026-05-{01..10}.html` 已批次套用相同 CSS 修補（idempotent Python 替換）

**X2 盲區補做（index.html）**：landing page 也有相同 CSS 風險，預防性套用相同修補

**衍生產出**：
- 新檔：`docs/postmortems/2026-05-08-p70.3-line-scroll-postmortem.md`
- 更新：`docs/RISK_REGISTRY.md`（R-004 + R-005）
- 更新：`TASK_HISTORY.md`（P70.3 主段 + 收官補錄）

### Exit Criteria

- [x] EC1：template 修補 + comment 補 spec 連結
- [x] EC2：10 個 5 月主版舊報告同步修補
- [x] EC2.5：X2 盲區補做 — `index.html` 預防性修補
- [ ] **EC3**：主公在 LINE 實機重新點 5/6（清快取或外部瀏覽器開）驗證滑動恢復 ← **待主公驗收**
- [ ] EC4：未來新生成報告（下次 GHA 跑成功後）二次驗收

### Commit 計畫（建議拆兩 commit，主公定奪 push）

**Commit 1：P70.3 治本+治標**
```
fix(P70.3): LINE 滑動失靈根治 — html/body 拆分 + touch-action:pan-y

- reporter/templates/report.html：拆分 html, body 規則，html 移除 overflow-x:hidden，body 補 touch-action: pan-y（防 LINE WebView swallow vertical pan events）
- data/reports/aov_report_2026-05-{01..10}.html：10 個舊主版報告批次套用相同 CSS 修補
- index.html：landing page 預防性套用（X2 盲區掃描補做）
- 根因：LINE WebView 將 html 視為 viewport scroll container，overflow:hidden on html 會停止轉發 touch scroll（WebKit bug #153852）
```

**Commit 2：P70.3 docs 補錄**
```
docs(P70.3): postmortem + RISK_REGISTRY + TASK_HISTORY 收官

- 新增 postmortem：失誤學「我以為 CSS 在所有環境都 OK」加進防火牆清單
- RISK_REGISTRY 新登記 R-004（UI/UX LINE 迴歸盲區）+ R-005（webkit-overflow-scrolling 90 天 review）
- TASK_HISTORY 補 Exit Criteria + 收官紀錄
- NEXT_SESSION_HANDOFF 收尾段更新
```

### 若 EC3 驗收失敗

`git checkout -- reporter/templates/report.html data/reports/ index.html` 還原所有修補 → 升 Opus 4.7 重查根因（不要硬撐 Sonnet）。

---

*下個視窗讀完此檔即可直接動工 P70.3 收尾或 P70.5'。*
