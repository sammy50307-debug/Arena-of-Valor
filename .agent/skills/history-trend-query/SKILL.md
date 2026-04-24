---
name: history-trend-query
description: 過去 N 天英雄/情緒/平台走勢的被動查詢器。補 Phase 50 trend-anomaly-detector（主動告警）的缺口，提供 pull 式時序檢視與多格式渲染（sparkline/Markdown/HTML/JSON）。Phase 61 分五階段開工，本檔隨階段推進逐步擴寫。
version: 0.3.1-S3
---

# 歷史走勢查詢器 (History Trend Query)

「芽芽戰情室」Milestone 5 Phase 61 特種兵。

## 🎯 定位

| 角色 | 職責 |
|---|---|
| Phase 50 `trend-anomaly-detector` | **主動** push / Z-Score 算異常 / 紅黃警報 |
| **Phase 61 本 skill** | **被動** pull / 拉時序 / 展示數字與圖表 |

不做異常偵測（交給 P50），不做推播格式化（交給 P59 rich-push-formatter），不做 NL 查詢（待 P62 附加 scope 回補）。

## 📂 目錄結構（開工進度）

```
history-trend-query/
├── SKILL.md                         ← 本檔（隨階段擴寫）
├── scripts/
│   ├── time_series_loader.py        ✅ S1：時序載入 + 缺日標記 + schema 驗證
│   ├── query.py                     ✅ S2+S3：hero_trend（含 weighted）
│   ├── renderer.py                  ✅ S3：sparkline / Markdown / HTML SVG
│   └── anomaly_marker.py            ⏳ S5：薄介面（Detector 可呼叫）
├── resources/
│   └── schema_version.json          ✅ S1：欄位契約
├── test_skill.py                    ✅ S1：7 項驗收測試
├── test_query.py                    ✅ S2：10 項查詢核心測試（含 weighted）
└── test_renderer.py                 ✅ S3：11 項渲染器測試
```

## 🧱 Stage 1 地基（已完成）

### TimeSeriesLoader

**職責**：依日期範圍掃 `data/analysis_YYYYMMDD.json`，回傳時序列表；缺日顯式標 `status='missing'` + warning log，schema 不合標 `status='invalid'`。

**API**：

```python
from time_series_loader import TimeSeriesLoader

loader = TimeSeriesLoader()                          # 預設讀 <project>/data/
loader = TimeSeriesLoader(data_dir="/custom/path")   # 自訂

# 單日
entry = loader.load_day("2026-04-05")
# => {"date": "2026-04-05", "status": "ok", "data": {...}}
# 缺檔 => {"status": "missing", "reason": "file_not_found", "data": None}
# 壞資料 => {"status": "invalid", "reason": "schema_mismatch", "missing_fields": [...]}

# 區間
series = loader.load_range("2026-03-30", "2026-04-05")   # 7 個 entry

# 末 N 天
series = loader.load_last_n_days(14, until="2026-04-05") # 末 14 天
```

### Schema Contract (`resources/schema_version.json`)

| 層級 | 必要欄位 |
|---|---|
| top_level | `date`, `total_posts`, `overall`, `sentiment_distribution`, `platform_breakdown`, `hero_stats` |
| overall | `sentiment_score`, `trend` |
| sentiment_distribution | `positive`, `negative`, `neutral` |

缺任一即 `status='invalid'` + `missing_fields` 列出。

### 驗收結果（S1 測試 7/7 全綠）

| # | 測試 | 驗證重點 |
|---|---|---|
| T1 | 真實資料載入 | 2026-04-05 實檔正確 parse + validate |
| T2 | 缺日偵測 | 未來日期 → status=missing + warning log |
| T3 | Schema contract | 缺欄位 → status=invalid + missing_fields 列齊 |
| T4 | load_range 含缺日 | 7 天區間 5 日缺 → 皆標 missing |
| T5 | validate() 好資料 | 回 (True, []) |
| T6 | load_last_n_days | n=3, until=04-05 → 回 04-03~04-05 |
| T7 | 區間反序防呆 | start > end → ValueError |

## 🛠️ CLI (debug 用)

```bash
py scripts/time_series_loader.py --start 2026-03-30 --end 2026-04-05
```

輸出每日 status + has_data 摘要（JSON）。

## 🧭 Stage 2 查詢核心（已完成）

### HistoryTrendQuery.hero_trend

**API**：

```python
from query import HistoryTrendQuery

q = HistoryTrendQuery()                              # 預設走 S1 loader
q = HistoryTrendQuery(data_dir="/custom/path")       # 或自訂資料夾
q = HistoryTrendQuery(loader=my_loader)              # 或注入現成 loader

r = q.hero_trend("芽芽", days=14, until="2026-04-05")
```

### 回傳結構

```python
{
  "hero": "芽芽",
  "days": 14,
  "range": {"start": "2026-03-23", "end": "2026-04-05"},
  "points": [
    {"date": "...", "status": "ok|missing|invalid|hero_absent",
     "count": int|None, "avg_sentiment": float|None},
    ...
  ],
  "summary": {
    "days_requested": 14,
    "days_ok": 3,            # status=ok 且英雄在 hero_stats
    "days_missing": 8,       # 檔案缺
    "days_invalid": 0,       # schema 不合（R5 合約：絕不進統計）
    "days_hero_absent": 3,   # 檔在但英雄不在 hero_stats
    "total_count": 16,
    "avg_sentiment_mean": 0.88,
    "coverage_ratio": 0.214
  }
}
```

### 四種 status 語意

| status | 意義 | count | avg_sentiment |
|---|---|---|---|
| `ok` | 有效資料、英雄有紀錄 | 實數 | 實數 |
| `missing` | 檔案不存在或 JSON 壞 | None | None |
| `invalid` | schema 不合（R5：絕不進統計） | None | None |
| `hero_absent` | 檔 ok、但該日英雄不在 hero_stats | 0 | None |

### 驗收結果（S2 測試 8/8 全綠）

T1 實資料單日、T2 含缺日區間、T3 hero_absent、T4 R5 合約、T5 參數防呆、T6 summary 恆等式、T7 coverage_ratio、T8 loader/data_dir 互斥。

### CLI Debug

```bash
py scripts/query.py --hero 芽芽 --days 14 --until 2026-04-05
```

## 🎨 Stage 3 渲染統一（已完成）

### TrendRenderer

同一 hero_trend 字典 → 四種輸出格式；灰點策略嚴格區分 absent 與 missing。

```python
from renderer import TrendRenderer

r = TrendRenderer()                          # metric 預設 count
r = TrendRenderer(metric="avg_sentiment")    # 或畫情緒走勢

spark_uni = r.sparkline(trend)                       # "▁·?█"
spark_asc = r.sparkline(trend, ascii_fallback=True)  # "_.?^"
md = r.markdown_table(trend)                         # Markdown 表格
svg = r.html_svg(trend, width=600, height=140)       # inline SVG
```

### 灰點策略對照表（R9 主公裁示）

| status | sparkline | ASCII | SVG |
|---|---|---|---|
| `ok` | `▁~█` 8 級正規化 | `_.-~^` 5 級 | 桃紅圓點 r=4 `#db2777` |
| `hero_absent` | `·` 中點 | `.` | 灰色小圓點 r=2 `#aaaaaa` |
| `missing` | `?` | `?` | 不畫、虛線斷開 |
| `invalid` | `?` | `?` | 不畫 |

### 驗收結果（S3 測試 16/16 全綠）

T1-T11 同前；**S3.5 補強**：T12 每日一標、T13 30 天自適應、T14 `x_axis=False` 停用、T15 `<script>` escape、T16 date 屬性注入防禦。

### S3.5 補強（R12 + R15）

- **R12** `html_svg(x_axis=True)` 自適應刻度：n≤7 每日、n≤31 每 7 天、n≤90 每 14 天、>90 每 30 天；末點一律標記
- **R15** `html.escape(quote=True)` 三處入口：hero name / range 日期 / title 屬性

### CLI Debug

```bash
py scripts/renderer.py --hero 芽芽 --days 7 --until 2026-04-05 --format spark
py scripts/renderer.py --hero 芽芽 --days 7 --until 2026-04-05 --format svg > out.svg
```

## 🚧 後續 Stage（草案待開工）

| Stage | 內容 | 狀態 |
|---|---|---|
| S4 多維度 | 多英雄/情緒/平台別 + min-max 正規化 + `raw=True` | ⏳ |
| S5 效能+介面+外掛 | LRU cache + `/trend` slash + `anomaly_marker.py` | ⏳ |
