# Postmortem — P110 v2：報告每天每篇文章凍結（雙根因 + 飛輪深探翻案）

- **日期**：2026-06-13
- **Phase**：P110 v2（最新動態文章凍結修復）
- **性質**：根因修復 + 自我優化飛輪深探（Workflow 9-agent 探索 + 24-agent review）
- **嚴重度**：高（每日戰報核心價值失效——報告每天每篇文章完全一樣，拖到阿喜肉眼發現才暴露）

## 背景

阿喜回報「文章沒在更新，特別是芽芽版」。調查證實報告每天每篇文章完全一樣（6/8 manifest = 6/12 manifest，total 35/unique 11/duplicate 24 完全一致）。

## 根因（四層疊加，3 子代理 + Claude 交叉驗證）

1. **爬蟲輸入固定**：巴哈/Dcard 按「相關度」搜尋、零時間排序，每天回同批常青舊文（`bahamut_scraper.py:85-89` qt=1 無 sort；raw 6/2 vs 6/7 URL 重疊 65.7%）。
2. **picker 鎖榜**：芽芽豁免年齡過濾 + decay >2.1 天全觸底 0.3 + 芽芽重複加成 1.5x → 老芽芽文 `final=base×0.3×boost×1.5` 數學上每天必贏。
3. **dedup 指標誤導**：`duplicate_url=24` 是 URL 正規化剝 query 讓巴哈塌縮成 1 key，非文章被刪（誤導指標）。
4. **一頁渲染兩次**（飛輪揪出）：`generator.py:322-323` top5_news = yaya_cards + other_cards → 同篇老芽芽文同時出現在「芽芽觀察室」與「最新動態詳情」= 阿喜看到「完全一樣」最直接的觀感來源。

## 飛輪深探（兩次 Workflow）

- **探索 Workflow（9-agent）**：4 角度提案 + 對抗評審。翻案了原 S1 悲觀假設——**巴哈板最新列表（B.php 不帶 q、class `b-list__row--sticky` 過濾置頂）第 8 列起就是每日輪動 feed**（Claude 親驗 32 列/7 sticky/25 feed，時間戳 `31分前/1小時前/昨天`）；揪出 source_hash 是凍結假陰性盲區、一頁渲染兩次。
- **Review Workflow（24-agent）**：4 維度對抗 review。13 findings 駁回、2 confirmed 皆測試缺口（非 live bug），裁決「可收官」。

## 修法（v2：先治上游 + 治呈現 + 補可觀察，picker 不動）

1. **S1 治上游**：`bahamut_scraper.fetch_board_latest`（板列表撈新文、跳 sticky）+ `date_normalizer` 補裸 MM-DD + main 雙軌（板列表 + 關鍵字補芽芽）。
2. **S2 治呈現**：`generator` top5_news 去重（純一般新文，芽芽歸芽芽觀察室）消除一頁渲染兩次。
3. **S3 補可觀察**：`generator._write_freshness_sidecar`（top5 指紋持久化）+ `check_report_freshness.py` 凍結偵測器（advisory）+ CI step。
4. **S4 picker 不動**：驗證新文 decay 0.83-0.99（排前）vs 老文 0.3（觸底）→ 最新動態靠上游活水 + picker 既有 decay 自然輪動，**無需拆鎖榜**（避免撞芽芽鐵律）。
5. 504 passed（+8）；nice_to_fix 高 ROI guard 順手納入（params 斷言鎖根因①契約 + 降級路徑測試）。

## 教訓與通則化

### B-026（新 blindspot，全域連續編號）

> **(a) 「優先級豁免」設計會反噬成「鎖榜」**——芽芽豁免年齡過濾 + 重複加成 + decay 觸底三者疊加，讓老芽芽文數學上每天必贏。通則：任何「豁免某類內容過濾」的優先設計，必須同時保留「新鮮度區分」，否則「優先」=「老內容永久霸佔」。
> **(b) 「展示層雙軌但機制層共用單一公式」會名實不符**——「最新動態」名為更新、實為相關度榜（dated_posts 從未按 published_date 排序）；top5_news = yaya+other 致一頁渲染兩次。通則：任何「雙軌展示」必須確認機制層真正分流、不重複渲染同一筆。

具體檢查點：
- 設計「優先豁免過濾」時，問「被豁免的老內容會不會永久霸榜」→ 配新鮮度上限/衰減區分。
- 「最新/熱門/精選」等語意化區塊，確認其排序機制與語意一致（最新=時間序，不是相關度榜借殼）。

## 防復發

- **凍結偵測器** `check_report_freshness.py`（advisory）成為長期 guard：連續 N 筆 top5_hash 相同→告警（文案標「可能是芽芽優先預期副作用由阿喜判讀」防誤砍芽芽）。
- **測試 guard**：`test_article_freshness.py`（8 測試）鎖根因①核心契約（板列表不帶 q/qt）+ 降級路徑 + 去重 + 偵測器。
- B-026 待 `cross-phase-review`/`blindspot-tracker` 評估是否納入 PHASE_TEMPLATE 開工檢查。
- 殘留待觀察（R-036）：連續日輪動最終證明待 cron；板列表無時間元素時被擋出 other_pool 的隱性風險。
