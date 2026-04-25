---
description: 查詢過去 N 天的英雄 / 整體輿情 / 平台別走勢（呼叫 history-trend-query skill）
allowed-tools: Bash, Read
argument-hint: <hero|heroes|overall|platform> [hero_name|hero_a,hero_b,...] [days] [--until YYYY-MM-DD] [--axis cross|per] [--raw] [--format json|md|svg|spark]
---

# /trend

被動查詢「芽芽戰情室」過去 N 天的時序資料，呼叫 `.agent/skills/history-trend-query/` skill。

> **執行此 slash 時，回覆首段必須先標 `[history-trend-query 已啟動]`**（依本專案 skill 啟動標記鐵律）。

## 使用語法

| 模式 | 範例 | 說明 |
|---|---|---|
| `hero`     | `/trend hero 芽芽 14`              | 單英雄時序 |
| `heroes`   | `/trend heroes 芽芽,悟空,凱恩 7`    | 多英雄比對（上限 5 軌） |
| `overall`  | `/trend overall 30`                | 整體輿情走勢 + 三情緒分布 |
| `platform` | `/trend platform 14`               | 各平台聲量走勢 |

可選旗標：
- `--until 2026-04-05`  指定末日（預設今日）
- `--axis cross|per`    多軌正規化模式（預設 cross）
- `--raw`               不做跨軌正規化（純原值）
- `--format spark|md|svg|json`  輸出格式（預設視 mode 自動）
- `--no-fuzzy`          禁用 hero name 模糊比對（hero 模式專用）

## 你（AI）應做的事

1. **首段標註** `[history-trend-query 已啟動]`
2. 解析參數，呼叫對應 CLI：

   ```bash
   # hero
   py .agent/skills/history-trend-query/scripts/query.py \
      --mode hero --hero <name> --days <n> [--until ...] [--weighted]

   # heroes (多英雄)
   py .agent/skills/history-trend-query/scripts/query.py \
      --mode heroes --heroes <a,b,c> --days <n> [--raw]

   # overall
   py .agent/skills/history-trend-query/scripts/query.py \
      --mode overall --days <n>

   # platform
   py .agent/skills/history-trend-query/scripts/query.py \
      --mode platform --days <n>
   ```

   若需視覺化，改呼叫 `scripts/renderer.py`（同樣參數 + `--format spark|spark-ascii|md|svg|multi-svg|multi-md`）。

3. **回覆主公**：
   - JSON 結果：抽取 `summary` 重點欄位、列出異常日（若 `resolved_from` 非 null 要主動告知模糊命中）
   - SVG / Markdown：直接呈現
   - 若觸發 `days > 90`：明確告訴主公「超過 90 天硬上限，建議分段查詢」

## 限制與契約

- `days` 上限 **90 天**（R11 LRU cache + R22 多軌效能保護）
- `heroes` 上限 **5 軌**（SVG palette 與 legend 上限）
- 缺日 / schema 不合 / 英雄不在會分別標 `missing` / `invalid` / `hero_absent`，**絕不**默默當 0
- 若使用者打錯英雄名（如「芽芽X」），fuzzy match (cutoff=0.6) 會嘗試命中真名，命中時結果帶 `resolved_from` 欄
- LRU cache 命中時回傳同一 list 物件——caller **不得**就地修改 series

## 範例

```
主公：/trend hero 芽芽 7

AI：[history-trend-query 已啟動]
    執行 py .agent/skills/history-trend-query/scripts/query.py --mode hero --hero 芽芽 --days 7
    → 7 天內 ok=2、missing=4、hero_absent=1，total_count=12，coverage=28.6%
    （詳見 sparkline 與表格）
```
