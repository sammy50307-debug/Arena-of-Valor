# P106.1 快修批 — Session 交接（2026-06-02）

> 用途：原 session 偏重（Opus 4.8 1M context + 讀多檔），阿喜回報當機數次。
> 換乾淨新視窗時讀本檔即可無縫接手 P106.1 剩餘工作，**不必重新摸索**。

## 開局必讀（依序）
1. `docs/PHASE_106_REPORT_QUALITY_PLAN.md` — 計畫書，**第三節「三個陷阱」必看**
2. `memory/feedback_yaya_priority.md` — 芽芽優先鐵律
3. 本檔

## 阿喜已拍板的決策（勿再問）
- **問題 1 焦點英雄 = 方案 B**：固定芽芽 + 友善空態（**不做**動態焦點/艾翠絲）
- **B 任務（爬資料驗品質）= 先確認再跑**，**不自動跑**。已查：`main.py:698-723` dry-run 只跳過推播（不是 early return），前面 `:690 generate(promote=False)` 報告僅候選不 promote → **dry-run 確認不會推未修報告給阿喜（安全）**。唯 archive 是否累積純讀 code 推不準，啟動 `py main.py --run-now --dry-run` 後**看 `data/` 有無當天新增即可確認**。

## 進度
- ✅ **問題 3（熱詞停用詞分離）= 完成且已 commit**（`595b432 fix(P106.1)`）。全套 402 passed。
- 🔄 **問題 8（top5 時間過濾）= 進行中，code 未動**。調查已完成（見下，直接接手）。
- ⬜ **問題 1（方案 B 友善空態）= 未開始**。

## 問題 8 — 已查證據（接手直接用，勿重查）
**根因**：`top5_picker.py` 只有時間衰減（`_compute_decay` :92-112，舊文分數降但不排除），無「天數上限」；`config.py` 無 MAX_AGE 設定。

**修法**：
1. `config.py:183` 後加 `TOP5_MAX_AGE_DAYS = int(os.getenv("TOP5_MAX_AGE_DAYS", "14"))`
2. `top5_picker.py` `pick_top5` 的 `filtered_posts` 迴圈（:240-250，黑名單過濾處）加「超過 N 天排除」，**比照黑名單給芽芽豁免**（`_is_yaya_related` :139-152），**無日期文章保留**（不誤殺）
3. 測試加：①15 天前一般文被排除 ②15 天前芽芽文保留 ③無日期文保留

**⚠️ 已查出的踩雷風險（最重要，沒注意會弄掛既有測試）**：
- `test_top5_picker.py:59` `NOW=datetime(2026,5,3)`、`:30` fixture `timestamp="2026-05-03"`。
- 若新過濾用真實 `datetime.now()`（=2026-06-02）當「今天」基準 → fixture（5/03，距今 ~30 天）**全被砍 → 既有測試掛掉**。
- **解法**：時間過濾**必須用 `pick_top5` 既有的 `now` 參數**（:194 簽名、:232 `now = now or datetime.now()`）當基準，**不可另寫 `datetime.now()`**。測試都注入 `now=NOW`，過濾基準=NOW(5/03)，fixture 安全。新增「舊文」測試請用「NOW 往前推 15 天」的日期。
- `_get_timestamp`（:177-179）取 `published_date or timestamp`，沿用即可。

## 問題 1（方案 B）— 修法方向
- `generator.py:234-237` `hero_focus_posts` 用 `_focus_text_evidence(p, "芽芽")` 過濾 → 今日無芽芽文則空。
- 方案 B：渲染時若 `hero_focus_posts` 為空 → 顯示友善 placeholder（如「今日尚無芽芽相關討論」）而非空白區，可補全網焦點。
- **動工前先** grep `hero_focus_posts` 在 `templates/report.html`（或 reporter 模板）的渲染區，確認空態怎麼接。
- 不踩陷阱 2：**不得過濾掉芽芽文章**。

## 三個陷阱（計畫書第三節）
1. **blacklist 共用** → 已用獨立 `keyword_stopwords.yaml` 解（問題 3）。問題 8/1 勿再共用 picker blacklist。
2. **芽芽優先** → 問題 8 時間過濾、問題 1 焦點都要芽芽豁免。
3. **動工前 grep 確認** → 問題 8 時間欄位已確認（`_get_timestamp` 取 published_date/timestamp）；問題 1 模板空態待 grep。

## 鐵律
- `py` 不用 `python`；TASK_HISTORY 禁全讀（grep 錨點 + Read offset≤200）；每批獨立 commit + 跑全套（402 passed 不退）；**push 必先問阿喜**。
- 每批收官補 TASK_HISTORY（`cat >> heredoc`，不用 Edit）。
