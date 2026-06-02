# Phase 106 — 每日戰報品質整修計畫書（草案，待動工）

> 狀態：**計畫書（規劃完成，未執行）**｜建議**換乾淨新 session 執行**
> 來源：P105 切 OpenRouter 首發收官後，阿喜 2026-06-01 用 LINE 實測戰報回報的 8 個品質問題
> 戰線：前端渲染 + 資料品質 + 內容語意（**獨立於已收官的 P105 provider 切換**）
> 鐵律提醒（執行者必讀）：`py` 不用 `python`；TASK_HISTORY 禁全讀（grep 錨點+Read offset）；改動前給阿喜計畫書等同意；**芽芽優先於所有過濾規則**（memory/feedback_yaya_priority.md）

---

## 一、背景與目標

阿喜主要透過 **LINE 推播連結**看每日戰報。P105 把 provider 切到 OpenRouter（deepseek-chat）後，daily 跑得動，但報告本身有一批既有品質問題在 LINE 上暴露。本 phase 系統修復，讓報告在 LINE webview 也完整、且內容有意義。

**退出條件**：8 問題中 P106.1+P106.2 批次修復並驗證；P106.3（大改）視情況排程；問題 6 靠 daily 累積自然解。

---

## 二、8 問題評估表（根因已交叉驗證，含子代理誤判修正）

| # | 問題 | 根因（證據檔:行號） | 修法 | 量 | 信心 |
|---|---|---|---|---|---|
| 1 | 焦點英雄「芽芽」區無文章 | `reporter/generator.py:112` 硬編碼 `hero_focus_name=config.HERO_FOCUS_NAME(芽芽)`，與 `daily_summary.hero_focus.name`（今日動態=艾翠絲）不同步；:116 用硬編碼 name 但 :117-119 summary/comments 取 daily_summary（不一致）→ 名字寫芽芽、貼文用芽芽過濾=空 | name 改從 `daily_summary.hero_focus.name` 動態讀；**但須尊重芽芽優先**（有芽芽貼文時焦點仍是芽芽） | 小 | 高 |
| 2 | 芽芽勝率/ban率沒動 | combat_stats(芽芽 52.8/18.5/45.2) = `analyzer/sentiment.py:693-695` **showcase 假數據寫死值**，非真爬 → 每天固定。`main.py:569-573` stats_scraper 失敗時無 fallback 重試 | 查 stats_scraper 真爬來源+為何失敗；爬失敗顯示「暫無數據」而非假 52.8% | 中 | 高 |
| 3 | 熱詞重疊（傳說/巴哈姆/AOV/情報/造型點開同幾篇） | `analyzer/keyword_stats.py:47-54` 熱詞停用詞讀 `configs/personal_blacklist.yaml`，但該檔只有 2 詞（星展、貝殼幣），通用詞/平台名全沒擋 → 被當熱詞、幾乎每篇都有→重疊 | **分離熱詞停用詞**（見下方陷阱）；新增獨立停用詞庫加平台/通用詞 | 小 | 高 |
| 4 | 分享/心得/決版/Dcard/介紹點開無文章 | 報告 JS `data/reports/aov_report_2026-06-01.html:2496-2500` 用 `topic_to_posts[詞]` 的 url 查 `_postIndex`(key=url)，查不到→「無法取得文章連結」。`_postIndex` 渲染範圍 ≠ topic_to_posts 文章範圍 | 對齊 _postIndex 索引範圍含所有熱詞文章（**執行時先查 _postIndex 怎麼渲染**） | 中 | 中 |
| 5 | 圖表 LINE 看不到 | `aov_report:9-10` 圖表靠外部 CDN（chart.js+echarts），LINE webview 載不到。3 圖表：platformChart(Chart.js)、heatmapChart(ECharts)、weeklyPulseChart(ECharts) | **伺服器端生成 PNG** 嵌入 `<img>`（新增 chart_renderer 模組） | 大 | 高 |
| 6 | 歷史趨勢空 | archive 缺口 5/17~5/31（gemini 斷糧期沒跑 daily）；`analyzer/history.py:25` history_days=7 找不到過去 7 天 archive | **不修**，跑 daily 累積約一週自動補（過去無原始資料不可 backfill） | 0 | 高 |
| 7 | 造型區顯示課金/免費送，非新造型消息 | 熱詞/文章只看詞頻不分內容主題，造型詞=任何含造型的文（不分新造型 vs 課金活動） | 需 LLM 語意分類（新造型 vs 課金）；**難、要設計**，可先用課金關鍵字過濾當 MVP | 大 | 中 |
| 8 | 最新動態詳情卡舊文章 | `reporter/generator.py:304-305` top5_news=top5_picker 選的(yaya 3+一般 2)，選文無時間過濾，舊文(history_index 內)一直被選 | top5_picker 選文加近期時間過濾（只選近 N 天 published_date） | 中 | 中 |

**交叉驗證關鍵收穫**（執行者注意，別重蹈）：
- 問題 2 子代理曾誤判「有資料=正常」，實為 showcase 假數據——**勿被假數據騙**
- 問題 4 子代理曾用本地舊 analysis（real_hot_topics=[]）誤判，線上其實有熱詞——**以線上/雲端 production 資料為準**

---

## 三、⚠️ 三個執行陷阱（必讀，否則會踩雷）

1. **問題 3 — blacklist 共用陷阱**：`configs/personal_blacklist.yaml` **同時**是「Top-5 picker 排除黑名單」+「熱詞停用詞」（yaml 註解:4-5）。若直接把「傳說」加進去，picker 會排除所有含「傳說對決」的文章（=幾乎全部）→ 報告變空！
   → **解法：新建 `configs/keyword_stopwords.yaml` 獨立熱詞停用詞庫**，keyword_stats 改讀它（不動 picker blacklist）。加：傳說、傳說對決、巴哈姆特、巴哈、AOV、Dcard、PTT、分享、心得、介紹、決版、決板、情報、討論、問題、文章 等平台/通用詞。
2. **芽芽優先鐵律**：問題 1/8 改焦點/選文邏輯時，芽芽相關文章不得被過濾掉（memory/feedback_yaya_priority.md）。
3. **問題 4/8 待執行時確認的細節**：_postIndex 渲染範圍（找 reporter template 的 posts 索引）、top5_picker 的時間欄位（analyzer/top5_picker.py 的 published_date 用法）——動工前先 grep 確認，勿憑本計畫書臆測。

---

## 四、分批執行計畫

| 批次 | 問題 | 性質 | 建議 |
|---|---|---|---|
| **P106.1 快修批** | 1 焦點動態、3 熱詞停用詞、8 時間過濾 | 小～中改、CP 值高、立竿見影 | 先做 |
| **P106.2 資料批** | 2 勝率真爬、4 熱詞索引對齊 | 中改、需查 scraper/template | 次做 |
| **P106.3 大改批** | 5 圖表 PNG、7 造型語意分類 | 大、要設計新模組 | 排程/視情況 |
| 自然解 | 6 趨勢空 | 跑 daily 累積 | 與 B 任務並行 |

每批獨立 commit + 驗證（基線目前 400 passed 不可退；改 logic 必補測試）。

---

## 五、17 層稽核（觸及層，動工前逐層填）

- **S 代碼/邏輯/測試/安全**：焦點選擇邏輯、熱詞停用詞分離、時間過濾、PNG 生成；每項補單元測試；PNG 中文字體防亂碼
- **A 架構**：chart_renderer 新模組 vs generator 解耦；keyword_stopwords 獨立於 blacklist
- **A 資料**：combat_stats 真爬 vs 假數據；topic_to_posts↔_postIndex 對齊
- **B UX**：LINE webview 相容（PNG）、熱詞有意義、最新動態時效
- 動工前跑 `/lint-phase-plan` 過 M1（11 視角）+ M2（紅藍對抗 ≥5）

---

## 六、風險

- R-P106-1：問題 3 改 blacklist 誤殺文章（共用陷阱）→ 分離停用詞庫 + 測試驗證 picker 不受影響
- R-P106-2：問題 5 PNG 化改動大（generator+template+新模組）→ 先單圖 PoC 再全面
- R-P106-3：問題 7 造型語意分類燒 LLM 額度 + 準確度未知 → 先關鍵字 MVP，語意分類另評估
- R-P106-4：改報告渲染可能影響既有測試 → 每批跑全套（400 passed 不退）

---

## 七、交接給新 session 的執行指引

1. 開局讀本計畫書 + memory（project_status / feedback_yaya_priority）+ `docs/PHASE_TEMPLATE.md`
2. 從 **P106.1 快修批**起，每問題：先 grep 確認根因 code → 寫測試 → 修 → 驗證 → commit
3. 問題 4/8 動工前先確認待查細節（第三節陷阱 3）
4. **B 任務（爬資料驗品質）可並行背景跑**（跑 daily 累積 archive + 燒 OpenRouter 額度驗資料），與報告整修不衝突
5. 全部以「阿喜 LINE 實際看得到、內容有意義」為最終驗收

---

_計畫書建立：2026-06-01｜P105 收官後即時規劃，未執行_
