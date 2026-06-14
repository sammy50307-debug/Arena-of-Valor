# 🤝 P118 交接手冊（整站重設計①設計系統地基）— 新視窗讀這份 + PHASE_118_PLAN.md 即可動工

> 更新：2026-06-15｜交接人：規劃視窗 Claude（Opus 4.8 1M）｜給：P118 動工視窗
> 一句話：**整站重設計 4-Phase 啟動。P118 計畫書 v1 已凍結（飛輪版、阿喜核准、lint PASS）→ 新視窗執行 P118（產設計系統 tokens + mockup，給阿喜定案 LOOK，不動 live 報告）。**

---

## 🎯 TL;DR — 新視窗第一件事

1. 開局讀 memory（`MEMORY.md` + `project_status.md`，已標 P118 凍結）+ 本手冊 + **`docs/PHASE_118_PLAN.md` v1（凍結，唯一真相源）**。
2. P118 已凍結、阿喜已核准，**直接動工 S1-S5**（守「不動 live 模板」邊界）。
3. 動工前置已完成：ui-ux-pro-max 已修復+註冊（見下）；git 同步於 `8cba6b2`、工作區乾淨。

## 🎨 美學方向（阿喜 2026-06-15 拍板，不要再問）

**混搭：保留「芽芽」粉櫻品牌色 + 吉祥物識別，採儀表板的清晰結構/資訊層級/專業間距。**
（ui-ux-pro-max 對 gaming 預設推 Retro-Futurism 霓虹色——**不要採用**，那會蓋掉芽芽品牌。只取 dashboard 的「結構/間距/層級」，色彩用芽芽品牌色。）

## 🌀 飛輪脊椎（這版 P118-121 與「重漆一次」的關鍵差別，務必落地）

原穩修＝重漆一次會再飄；飛輪版讓設計系統成 machine-enforced 契約：
- **tokens 唯一真相源**：`design-system/tokens.css` 是全站色/間距/字級單一來源；report.html/index.html 一律 `var(--token)`、**禁硬編碼**。
- **token-lint 進 gov.preflight（復用 P117 總指揮）**：`scripts/check_design_tokens.py` flag 硬編碼 `#hex`/任意 px → 註冊進 `governance_config.yaml` 的 `full` profile（**P119 上線，advisory**）。這是防 UX 債（今天 #1/#2/#3）無聲復發的核心。
- **preview-driven 驗證**：P119-121 用 `preview_*` 工具 render→截圖 375/768/1440 + LINE WebView UA（B-020 盲點鐵律），取代一次性肉眼。
- **反膨脹**：不做 component-partial 大重構、不做重型 Playwright CI；token-lint 先 advisory。

## 🔧 ui-ux-pro-max 狀態（已修好，這次的重點工具）

- **已修復**：原 search.py/core.py/design_system.py 被舊 git 毀損清空（0 行），已從上游 `nextlevelbuilder/ui-ux-pro-max-skill` 還原（scripts+data 版本一致，commit `3ba25b2`）。
- **已註冊**：複製到 `~/.claude/skills/ui-ux-pro-max`（+ copywriter/hallucination-judge/cot-prompt-compactor/session-handoff-packager 共 5 個）→ harness 已掃到、**會自動觸發**。
- **怎麼用**（Windows 加 `-X utf8` 避編碼）：
  ```
  py -X utf8 .agent/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist
  py -X utf8 .agent/skills/ui-ux-pro-max/scripts/search.py "<kw>" --domain style|typography|ux|color
  ```
  `--persist` 會寫 `design-system/MASTER.md` + `design-system/pages/`。

## 🎨 必保留的芽芽品牌色（從 report.html :root 萃取，寫進 tokens.css override 區）

- 主粉：`#be185d`（pink-700）/ 邊框粉 `#db2777`（pink-600, glass-border rgba 0.2）
- 背景漸層：`linear-gradient(135deg, #fdf2f8 0%, #f0fdf4 100%)`（粉→薄荷）
- glass：`rgba(255,255,255,0.7)` + blur
- mint accent：`#10b981`；text-main `#1e293b`；text-muted `#64748b`
- sakura 櫻花動畫（.sakura-container）

## 📋 P118 五階段（詳見 PHASE_118_PLAN.md §9）

- **S1 設計系統產出**：ui-ux-pro-max `--design-system --persist`（混搭 kw）→ MASTER.md；萃取品牌色；--domain 補間距/字體/卡片細節。
- **S2 tokens 定義**：`design-system/tokens.css`（芽芽品牌色 + 儀表板中性階 + spacing scale 4/8px〔解 #3 根因〕+ type/radii/shadow）。Ultracode 可並行 judge panel 產 2-3 token 方向評分綜合。
- **S3 mockup**：`design-system/mockup.html`（**獨立 sandbox、不依賴 generate()**）3 關鍵元件（卡片/熱詞統計/feed+滾輪），**用 report.html 真實 Jinja 區塊結構 + 真實資料形狀**（長中文標題/多熱詞壓版面）。
- **S4 定案**：截圖給阿喜簽核 LOOK，不滿意迭代（不進 P119）。
- **S5 收官**：TASK_HISTORY + memory + P119 計畫書預告。

## 🔑 關鍵 file:line（report.html，動工直接用）

- `:root` 品牌色：report.html:13-25
- `.feed-container`（最新動態滾輪，#3 已加呼吸空間）：report.html:331-339
- `.post-card`：report.html:345；熱詞統計區：搜 `真實熱詞統計`；芽芽近期動態：report.html:1550；最新動態詳情+feed：report.html:1785-1788
- 報告由 `reporter/generator.py generate()` 渲染（P118 不動它）

## 🚫 P118 邊界（務必守）

**不碰** `reporter/templates/report.html` / `index.html` / `reporter/generator.py` / CI / 後端——P118 只產 `design-system/`（MASTER/tokens/mockup）。**報告外觀真正改變在 P119 才上線。**

## 🚫 鐵律

- `py` 不用 `python`（Windows，加 `-X utf8` 跑 ui-ux-pro-max）
- TASK_HISTORY.md 禁全讀：`grep -n "^### "` 錨點 + Read offset≤200；寫用 `cat >> heredoc`
- 改動前計畫書已凍結；**push 前問阿喜**；每個後續 Phase（P119-121）各自凍結計畫書 + 阿喜核准
- pre-push hook 在 `.githooks`

## 📂 git 現況

- `main` = `8cba6b2`（**已 push、main↔origin 同步**）；含 skill 修復 `3ba25b2` + P118 計畫書凍結 `8cba6b2`
- 整站重設計藍圖：**P118 地基 → P119 報告視覺+token-lint上線 → P120 響應式/LINE/A11y → P121 Landing**

## ⏳ 不在 P118 範圍（登記，勿混入）

- **#1 熱詞點擊無連結** / **#2 芽芽內文 placeholder + 芽芽舊文 freshness**：後端/內容戰線，與視覺重設計分開，另議（#2 牽涉 llm_coverage partial 成本取捨 + R-036）。
- **P117 雲端 gov.preflight ci** 真驗證：待下次 cron（台北每天 16:30）或阿喜手動 workflow_dispatch 看 Actions log 的「🛡️ Preflight CI Profile」步驟。
- R-037（main.py:728 吞例外）/ R-039（真即時 cron-miss）：數據驅動觸發，沒到條件不動。

---

*交接手冊 by 規劃視窗 Claude（Opus 4.8 1M）｜2026-06-15｜新視窗：讀此 + PHASE_118_PLAN.md v1 → 直接動工 P118 S1-S5。混搭方向 + 飛輪脊椎（tokens 唯一源 + token-lint + preview 驗證）是重點。*
