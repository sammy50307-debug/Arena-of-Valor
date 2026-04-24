---
name: history-trend-query
description: 過去 N 天英雄/情緒/平台走勢的被動查詢器。補 Phase 50 trend-anomaly-detector（主動告警）的缺口，提供 pull 式時序檢視與多格式渲染（sparkline/Markdown/HTML/JSON）。Phase 61 分五階段開工，本檔隨階段推進逐步擴寫。
version: 0.1.0-S1
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
│   ├── query.py                     ⏳ S2：HistoryTrendQuery 主類別
│   ├── renderer.py                  ⏳ S3：sparkline / Markdown / HTML 統一渲染
│   └── anomaly_marker.py            ⏳ S5：薄介面（Detector 可呼叫）
├── resources/
│   └── schema_version.json          ✅ S1：欄位契約
└── test_skill.py                    ✅ S1：七項驗收測試
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

## 🚧 後續 Stage（草案待開工）

| Stage | 內容 | 狀態 |
|---|---|---|
| S2 查詢核心 | 單英雄時序 + Python API（純 JSON） | ⏳ |
| S3 渲染統一 | sparkline / Markdown / HTML 三格式同源 | ⏳ |
| S4 多維度 | 多英雄/情緒/平台別 + min-max 正規化 | ⏳ |
| S5 效能+介面+外掛 | LRU cache + `/trend` slash + `anomaly_marker.py` | ⏳ |
