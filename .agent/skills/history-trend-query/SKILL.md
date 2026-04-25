---
name: history-trend-query
description: 過去 N 天英雄 / 整體輿情 / 平台別走勢的被動查詢器。補 Phase 50 trend-anomaly-detector（主動告警）的缺口，提供 pull 式時序檢視、四種視覺化格式（sparkline/Markdown/HTML SVG/JSON）、多英雄共圖、跨軌與獨立軌正規化、fuzzy 英雄名比對、LRU cache 加速。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[history-trend-query 已啟動]`。

# 歷史走勢查詢器 (History Trend Query) — v1.0

「芽芽戰情室」**Milestone 5 Phase 61** 旗艦特種兵。被動 pull 時序資料、四維度查詢、四格式渲染，搭配薄介面 `anomaly_marker` 可選擇性掛上異常標記。

---

## 🎯 定位與分工

| 角色 | 職責 |
|---|---|
| Phase 50 `trend-anomaly-detector` | **主動** push / Z-Score 算異常 / 紅黃警報 |
| **Phase 61 本 skill (Query)** | **被動** pull / 拉時序 / 展示數字與圖表 |
| Phase 59 `rich-push-formatter` | 推播格式化（不在本 skill scope） |
| Phase 62 `nl-to-prompt-structurer` | 自然語言查詢介面（待 P62 收官回補） |

**解耦原則**：Query ↔ Detector 透過共用 `loader` + 薄函式 `anomaly_marker` 對接，互不依賴對方內部演算法。

---

## 📂 檔案結構（v1.0 完整）

```
history-trend-query/
├── SKILL.md                         ← 本檔（v1.0 完整文件）
├── scripts/
│   ├── time_series_loader.py        ✅ S1 + S5 F1 LRU cache
│   ├── query.py                     ✅ S2/S4/S5 — hero/heroes/overall/platform 四模式
│   ├── renderer.py                  ✅ S3/S4/S5 — sparkline/Markdown/HTML SVG + 多軌 + anomaly overlay
│   └── anomaly_marker.py            ✅ S5 F7 薄介面（純函式 z-score）
├── resources/
│   └── schema_version.json          ✅ S1 欄位契約
├── test_skill.py                    ✅ 10/10  TimeSeriesLoader + cache
├── test_query.py                    ✅ 24/24  HistoryTrendQuery 四模式 + axis + fuzzy
├── test_renderer.py                 ✅ 27/27  TrendRenderer 四格式 + 多軌 + legend wrap + anomaly
└── test_anomaly_marker.py           ✅  5/5   z-score 邊界 / 防呆 / value_key 切換
                                     ─────
                                     總計 66/66 全綠
```

外部觸發：[`.claude/commands/trend.md`](../../../.claude/commands/trend.md)（`/trend` slash command）。

---

## 🧱 Stage 1 — TimeSeriesLoader（時序地基 + LRU cache）

```python
from time_series_loader import TimeSeriesLoader

loader = TimeSeriesLoader()                              # 預設讀 <project>/data/
loader = TimeSeriesLoader(data_dir="/custom/path")
loader = TimeSeriesLoader(cache_size=64)                 # S5 F1：自訂 cache 容量

# 單日
entry = loader.load_day("2026-04-05")
#   ok      → {"date": "...", "status": "ok", "data": {...}}
#   缺檔     → {"status": "missing", "reason": "file_not_found", "data": None}
#   壞 schema → {"status": "invalid", "reason": "schema_mismatch", "missing_fields": [...]}

# 區間（命中 cache 時 O(1) 回同一 list 物件）
series = loader.load_range("2026-03-30", "2026-04-05")

# 末 N 天
series = loader.load_last_n_days(14, until="2026-04-05")

# Cache 管理
loader.cache_stats()    # → {"size": ..., "max_size": ..., "hits": ..., "misses": ...}
loader.clear_cache()    # 熱重載 data 後或測試環境呼叫
```

### Schema Contract（`resources/schema_version.json`）

| 層級 | 必要欄位 |
|---|---|
| top_level | `date`, `total_posts`, `overall`, `sentiment_distribution`, `platform_breakdown`, `hero_stats` |
| overall | `sentiment_score`, `trend` |
| sentiment_distribution | `positive`, `negative`, `neutral` |

缺任一即 `status='invalid'` + `missing_fields` 列出。

### ⚠ Cache 契約（R23）

- `load_range` 命中 cache 時回**同一 list 物件**——caller **不得就地修改** series 或內部 entry，否則會污染下次呼叫
- 若需修改，先 `copy.deepcopy` 自己的副本
- 熱重載 `data/` 目錄後 cache **不會自動失效**，呼叫端需手動 `clear_cache()`

---

## 🧭 Stage 2 + S5 — HistoryTrendQuery 四模式

```python
from query import HistoryTrendQuery, DAYS_HARD_CAP

q = HistoryTrendQuery()                              # 預設 loader
q = HistoryTrendQuery(data_dir="/custom/path")
q = HistoryTrendQuery(loader=my_loader)              # 注入既有 loader
```

### Mode 1：hero_trend（單英雄）

```python
r = q.hero_trend(
    "芽芽", days=14, until="2026-04-05",
    weighted=False,    # avg_sentiment 是否以 count 加權
    fuzzy=True,        # 預設啟用 fuzzy 比對
)
```

**回傳**：

```python
{
  "hero": "芽芽",
  "resolved_from": None,   # fuzzy 命中時為原輸入字串、否則 None
  "days": 14,
  "range": {"start": "2026-03-23", "end": "2026-04-05"},
  "points": [{"date": "...", "status": "ok|missing|invalid|hero_absent",
              "count": int|None, "avg_sentiment": float|None}, ...],
  "summary": {
    "days_requested", "days_ok", "days_missing", "days_invalid",
    "days_hero_absent", "total_count", "avg_sentiment_mean",
    "avg_sentiment_mode": "weighted|arithmetic", "coverage_ratio"
  }
}
```

### Mode 2：heroes_trend（多英雄比對，上限 5 軌）

```python
r = q.heroes_trend(
    ["芽芽", "悟空", "凱恩"], days=14,
    raw=False,                # True → 不算 normalized_count
    normalize_axis="cross",   # "cross" 全軌共軸 / "per" 各軌獨立
    fuzzy=True,
)
# r["heroes"] 為 list of hero_trend，每點多 normalized_count ∈ [0,1]
```

### Mode 3：overall_trend（整體輿情，三情緒並陳）

```python
r = q.overall_trend(days=30, raw=False, normalize_axis="cross")
# 每 ok 點：{"total_posts", "positive", "negative", "neutral", "normalized_total"}
# summary：positive_sum / negative_sum / neutral_sum / total_posts_sum
```

### Mode 4：platform_trend（平台別走勢）

```python
r = q.platform_trend(days=14, raw=False, normalize_axis="cross")
# r["platforms"]：所有 ok 日聯集出現的平台名稱（保序）
# r["platform_data"][p_name]：該平台時序，缺平台日標 absent / post_count=0
```

### 四種 status 語意（嚴格區分）

| status | 意義 | count / value |
|---|---|---|
| `ok` | 有效資料、實體在 | 實數 |
| `missing` | 檔案不存在或 JSON 壞 | None |
| `invalid` | schema 不合 / platform_breakdown 格式錯（R5+R18 合約：絕不進統計） | None |
| `hero_absent` | 檔 ok、但該日英雄不在 hero_stats | 0 |
| `absent` | （platform 模式專用）檔 ok、該平台缺 | 0 |

### S5 防呆與契約

| 項目 | 邊界 | 行為 |
|---|---|---|
| `days` 硬上限 | 90 天 (`DAYS_HARD_CAP`) | 超過 ValueError；91 噴、90 通過；`bool` 不被視為 1/0 |
| `heroes` 上限 | 5 軌 | 超過 ValueError |
| `normalize_axis` | "cross" / "per" | 其他值 ValueError（含 raw=True 也驗） |
| `platform_breakdown` 嚴驗 (R18) | 非 dict / entry 非 dict / `post_count` 非數值 | 該日該平台標 invalid |
| Fuzzy hero match (R10) | cutoff=0.6 | 命中時改寫 `hero` 欄、`resolved_from` 帶原輸入 |

### ⚠ Fuzzy 契約（R29 / R33）

- fuzzy 用 `difflib.get_close_matches`，**對中文字符是字元級比對**，偶有誤命中（例如「悟空」可能命中「孫悟空」）
- 不要把 fuzzy 結果當權威——**永遠看 `resolved_from` 欄位**判斷是否被改寫
- 若不放心，呼叫時設 `fuzzy=False` 關閉
- `heroes_trend` 中 `hero_names[i]` 與 `heroes[i].hero` 在 fuzzy 命中時會不一致——比對請用 `heroes[i].resolved_from or heroes[i].hero`

---

## 🎨 Stage 3 + S5 — TrendRenderer 渲染統一

```python
from renderer import TrendRenderer

r = TrendRenderer(metric="count")            # 或 "avg_sentiment"

# 單軌（hero_trend）
r.sparkline(trend)                           # Unicode block: "▁·?█"
r.sparkline(trend, ascii_fallback=True)      # ASCII: "_.?^"
r.markdown_table(trend)                      # Markdown 表
r.html_svg(trend, width=600, height=160, x_axis=True)

# 多軌（heroes_trend / platform_trend）
r.render_multi_svg(multi, width=720, height=220)
r.render_multi_markdown(multi)
```

### 灰點策略對照表（R9）

| status | sparkline | ASCII | SVG |
|---|---|---|---|
| `ok` | `▁~█` 8 級 | `_.-~^` 5 級 | 桃紅圓點 r=4 `#db2777` |
| `hero_absent` / `absent` | `·` | `.` | 灰圓點 r=2 `#aaaaaa` |
| `missing` | `?` | `?` | 不畫、虛線斷開 |
| `invalid` | `?` | `?` | 不畫 |

### 多軌色盤（S4 R16）

| 軌索引 | 色碼 | |
|---|---|---|
| 0 | `#db2777` | 旗艦桃紅（與單軌 ok 同色，視覺主軸） |
| 1 | `#0ea5e9` | 青 |
| 2 | `#f59e0b` | 琥珀 |
| 3 | `#8b5cf6` | 紫 |
| 4 | `#10b981` | 翠 |

### S5 渲染強化

- **F6 Legend 自動換行 (R19)**：`render_multi_svg` 5 軌長名超過 width 時自動折下一列、SVG height 動態擴增（`legend_row_step=16px`）
- **F7 Anomaly overlay**：`html_svg(trend, anomaly_flags=[...])` 在 True 位置畫 `r=7` 紅圈外環 `#dc2626`；長度需與 points 一致、否則 ValueError
- **R12 x 軸刻度自適應**：n≤7 每日 / n≤31 每 7 天 / n≤90 每 14 天 / >90 每 30 天 + 末點強制標
- **R14 Markdown pipe 跳脫**：所有 cell 過 `_md_escape`
- **R15 SVG 防 XSS**：hero name / range / title 屬性過 `html.escape(quote=True)`

### normalize_axis 視覺差異（R31）

| axis | 看的是 | 適用情境 |
|---|---|---|
| `"cross"`（預設） | **量級對比**：5 軌共用同一 min-max，量級差 10 倍時小軌道會被壓平 | 比聲量大小 |
| `"per"` | **形狀對比**：每軌各自 0~1，看波動模式 | 比走勢趨勢 |

---

## 🛡️ Stage 5 F7 — anomaly_marker（薄介面外掛）

純函式、零依賴、與 Detector 解耦。任何模組可呼叫。

```python
from anomaly_marker import mark_anomalies, mark_anomalies_with_scores

trend = q.hero_trend("芽芽", days=30)

# 旗標版：list[bool]，True = 異常
flags = mark_anomalies(trend["points"], z_threshold=2.0, value_key="count")

# 分數版：list[float|None]，回原始 z-score；不合格點 None
scores = mark_anomalies_with_scores(trend["points"])

# 串接 renderer 畫紅圈
svg = TrendRenderer().html_svg(trend, anomaly_flags=flags)
```

### 邊界行為

| 情境 | 結果 |
|---|---|
| 空 list | `[]` |
| 樣本數 < 2 | 全 `False` |
| 全相同值（std=0） | 全 `False`（with_scores 版回 `0.0`） |
| `status != 'ok'` | 該位置 `False` |
| `value` 非數值（含 bool/str/None） | 該位置 `False` |
| `z_threshold` 預設 | 2.0（約 95% 信賴區間） |

---

## 🎯 `/trend` Slash Command（S5 F8）

外部入口：[`.claude/commands/trend.md`](../../../.claude/commands/trend.md)

```
/trend hero 芽芽 14
/trend heroes 芽芽,悟空,凱恩 7
/trend overall 30
/trend platform 14 --axis per
```

執行時 AI 會：先標 `[history-trend-query 已啟動]` → 呼叫 CLI → 美化結果回覆。

---

## 🛠️ CLI Debug

```bash
# 載入器
py scripts/time_series_loader.py --start 2026-03-30 --end 2026-04-05

# 查詢核心（四模式）
py scripts/query.py --mode hero     --hero 芽芽 --days 14 --until 2026-04-05 [--weighted]
py scripts/query.py --mode heroes   --heroes 芽芽,悟空 --days 7 [--raw]
py scripts/query.py --mode overall  --days 30
py scripts/query.py --mode platform --days 14 [--raw]

# 渲染（含多軌）
py scripts/renderer.py --mode hero --hero 芽芽 --days 7 --format svg > out.svg
py scripts/renderer.py --mode heroes --heroes 芽芽,悟空 --days 7 --format multi-svg > out.svg

# 異常標記
py scripts/anomaly_marker.py --hero 芽芽 --days 30 --threshold 2.0
```

---

## 📊 v1.0 驗收：66/66 全綠

| 檔 | 項數 | 涵蓋 |
|---|---|---|
| `test_skill.py` | 10 | T1-T7 loader 基礎 + T8-T10 LRU cache |
| `test_query.py` | 24 | T1-T16 四模式 + T17-T24 days cap / fuzzy / axis / bool 防呆 |
| `test_renderer.py` | 27 | T1-T24 四格式 + 多軌 + R12/R14/R15 + T25 legend wrap + T26-T27 anomaly overlay |
| `test_anomaly_marker.py` | 5 | T1-T5 z-score 邊界 / 防呆 / value_key |

零回歸、零外部相依（純標準庫）。
