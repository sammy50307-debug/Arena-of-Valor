# P108 報告數據可信度修復 — Session 交接 + 計劃（2026-06-02）

> 用途：今日完成 P107 焦點英雄爬取覆蓋修復 S1-S2 並收官，下次主線轉 P108。換新視窗讀本檔即可無縫接手。
> 模型建議：機械改動 Sonnet 4.6；偵錯/跨系統/新架構 Opus 4.8。

## 開局必讀（依序）
1. 本檔
2. `docs/RISK_REGISTRY.md` → R-028（P108 三問題）、R-027（Dcard 延後）、R-026（top5 倒灌）
3. `memory/project_status.md`（最新進度，頂部 P107 收官區塊）
4. TASK_HISTORY 查 P107（`grep -n "^### P107" TASK_HISTORY.md` → `Read offset:N limit:200`，**禁全讀**）

---

## 今日戰果（全已 push origin/main）
- **P106.1 收尾**：問題8 top5 時間過濾 / 問題1 芽芽空態 placeholder / Opus 品質審查（R-026 top5↔fallback 倒灌）
- **P107 S1-S2 焦點英雄爬取覆蓋修復**（觸發：阿喜質疑「0 篇芽芽」）：
  - **S0 四根因**：HERO_FOCUS_KEYWORDS dead config / content 只標題 / detected_heroes 沒做 / keyword 過濾（R-027）
  - **S1 接 Tavily → 真實驗證失敗 → 完整回退**：Tavily 全網搜短名「芽芽」撈同名雜訊（IG網紅/菜單/其他遊戲），含芽芽真文 0 篇。**教訓：不先 PoC 驗證假設就接線會白做**
  - **S2 巴哈治本**：PoC 證巴哈搜「芽芽」8/8 命中真遊戲文 → `main.py` 接 `HERO_WATCHLIST` + 派 2 並行子代理補 `detected_heroes` → **端到端芽芽進觀察室**（30次、picker 3篇）
  - commits：`ea0929e`(log) / `1e91005`(計畫書+R-027) / `7f268df`(S2) / `fb5b137`(收官) / `5f262d5`(R-028)；基線 406→412 passed
- **子代理方法論**：v1.3 成功範本 + 6 點 checklist **升格全域 `~/.claude/CLAUDE.md`**
- **阿喜手機驗收**：芽芽文質量好✅，但發現 3 報告問題 → 登記 R-028 開 P108

## 當前狀態
- **git**：main 與 origin 同步、乾淨（只 `.claude/.history_query_count` hook 檔 unstaged，不管）
- **環境**：playwright + chromium **已裝**（~150MB，S3 Dcard 可能用）；cloudscraper 已卸載
- **stash**：5 個堆積（`{0}-{3}` dry-run/temp 副產物可清、`{4}` P63.4 WIP 待確認內容）
- **測試**：412 passed, 4 skipped

---

## 🔜 下次主線：P108 報告數據可信度修復（R-028）

> **重要前提**：爬取已成功（芽芽進觀察室），P108 問題全在「撈到的資料怎麼**呈現/統計**」，不是爬取。

### 三問題（全有數據證據）
| # | 問題 | 根因（已診斷）| 修法方向 |
|---|---|---|---|
| **A** | 熱詞無連結 | `real_hot_topics=0` / `topic_to_posts=0` → 「真實熱詞統計」區（藍色 hot-tag 點詞看來源）無數據整區不渲染。**P106 既有剩餘問題「熱詞無連結」** | 查 `real_hot_topics` 生成（jieba 詞頻）為何空——資料層斷在哪 |
| **B** | 文章來源不正確 | 文章卡片來源欄位渲染錯（`top_links=3` 有料但標示可能誤）| 追 `generator.py` 文章 source/platform 渲染邏輯 |
| **C** | 平台統計缺真實平台 | `platform_breakdown` 只 `ig/threads/fb`（LLM 固定子集 `sentiment.py:101`+`prompts.py:93`），**沒統計巴哈 24 篇/Dcard**；`local_analyzer.py:215` 有真實統計卻沒採用 | 改用 local_analyzer 真實統計 |

### P108 子階段建議（待開工前細化）
- **S0 前置驗證**（記取 P107 教訓：先驗證資料層再改）：
  - real_hot_topics 生成在哪斷掉？（keyword_stats 生成 vs generator 傳入 vs 渲染）
  - platform_breakdown 為何用 LLM 版而非 local_analyzer 真實版？（generator 取哪個）
- **S1（C，最明確、高 ROI）**：platform_breakdown 改採 `local_analyzer.py:215` 真實統計（含所有平台）
- **S2（A）**：修 real_hot_topics 生成邏輯
- **S3（B）**：追文章來源渲染
- **S4 防復發**：加 checker 守報告數據可信度（real_hot_topics 非空 / platform_breakdown 含實際平台 / 來源正確），防靜默失真
- **鐵律**：每項先驗證資料層、再改呈現層（不倉促逐個修，避免重蹈 P107 S1 沒驗證就改的覆轍）

### P108 開工前須做
完整計畫書（17 層稽核 + M1/M2 體檢，`lint-phase-plan` 驗），對齊 `docs/PHASE_TEMPLATE.md`。**本交接只給方向，非凍結計畫書**。

---

## 次要待辦
- **S3 Dcard**（R-027）：Cloudflare 鎖死，cloudscraper/WebFetch/playwright headless **全 403/Just-a-moment**。需 playwright-**stealth** 或 **Apify** 才能過。實測巴哈已撈 **28 篇**豐富芽芽文，Dcard 投報比惡化 → **延後評估**。Dcard 內容質量高（WebSearch 索引證實深度攻略：配裝/玩法/心得），技術門檻高是卡點。
- **stash 清理**：5 個（改天連 P108 一起清；`{4}` P63.4 WIP 要先確認內容再決定）
- **playwright+chromium 去留**：S3 若放棄可卸載（~150MB）
- **P106 其他剩餘 4 個**：勝率假數據 / 圖表PNG化 / 趨勢空 / 造型語意（project_status 記）

## 鐵律提醒
- `py` 不用 `python`；TASK_HISTORY 禁全讀（grep 錨點 + Read offset≤200）；**push 必問阿喜**
- 子代理派遣前過全域 6 點 checklist；**先 PoC 驗證假設再落地**
- 報告問題**先驗證資料層再改呈現層**，不倉促
- 每批獨立 commit + 跑全套（412 passed 不退）；收官補 TASK_HISTORY（`cat >> heredoc`）
