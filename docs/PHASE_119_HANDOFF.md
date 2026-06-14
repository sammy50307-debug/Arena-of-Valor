# 🤝 P119 交接手冊（整站重設計②報告視覺重構 + token-lint）— 新視窗讀這份 + PHASE_119_PLAN.md 即可動工

> 更新：2026-06-15｜交接人：P118 收官視窗 Claude（Opus 4.8 1M）｜給：P119 動工視窗
> 一句話：**P118 設計系統 + LOOK 已定案（variant-bc，已 push）→ P119 把它「套質感保骨架」套到 live report.html + token-lint advisory 上線。計畫書 v1 已凍結、阿喜核准、§A scope 拍板。**

---

## 🎯 TL;DR — 新視窗第一件事

1. 開局讀 memory（`MEMORY.md` + `project_status.md`，已標 P118 收官/P119 凍結）+ 本手冊 + **`docs/PHASE_119_PLAN.md` v1（凍結，唯一真相源）**。
2. 讀定案 LOOK：**`design-system/variants/variant-bc.html`**（截圖在 `scratch/p118_shots/variant_bc.png`，scratch 不進版控）+ `design-system/MASTER.md`（設計決策 + §6 落地 punch-list）+ `design-system/tokens.css`（要接入的 tokens）。
3. **S0 第一件事：snapshot** `cp reporter/templates/report.html backups/report_before_p119.html`（X1 回退點），再動工。

## 🔒 阿喜已拍板的 scope（§A，不要再問）

- **A1 = 套質感保骨架**：保留現有 report.html 結構/功能**完全不動**，只套 variant-bc 的**質感層**（色/玻璃/光暈/mesh/發光數字/編輯式標題/熱詞/間距/字級）。**功能一個不刪**（戰力面板/音訊/圖表/區域導覽/警示/側欄全留）＝Exit B 硬條件。**不是**把 report 改成 variant-bc 的雜誌版型。
- **A2 = report.html only**（index.html=Landing 留 P121）。
- **A3 = token-lint advisory**（warn 不擋報告）。

## 🎨 要套的質感（從 variant-bc 借，全走 tokens.css）

- 玻璃卡：`var(--color-surface)` + `var(--brand-glass-blur)` + `var(--brand-glass-border)` + `var(--shadow-brand)`，hover 疊 `var(--glow-brand)`
- 霓虹光暈：`--glow-brand` / `--glow-brand-strong`（mascot 品牌保留，**不要**聽通用工具收掉）
- mesh 飽和漸層（粉/薄荷/紫 radial，低透明，見 variant-bc `.bg-mesh`）+ 角色立繪保留
- 編輯式標題：粉色大標 `--color-primary-strong` + 白光暈 text-shadow（**可讀關鍵**，別做暗底粉字）
- 發光數字列（cover-stats）、發光分隔線
- 間距走 4/8px `--space-*`（解 #3）、字級 `--text-*`、行高 `--leading-normal`(中文 1.6)

## 🔵 熱詞 #1：保留藍色（阿喜拍板，務必）

- report.html:1234-1263 既有藍 `linear-gradient(135deg,#1e3a5f,#2563eb)` → **只 tokenize 成 `var(--hot-tag-bg)`（已是藍）+ 加 cursor/hover/focus affordance**。
- **不要改成粉色**。⚠️ `MASTER.md §6 punch-list #1` 寫「重寫成粉系 pill」是 P118 早期、**B+C 定案前**的過時內容——**以本手冊 + PHASE_119_PLAN §1.3 為準（保留藍）**。

## 🛠️ 核心策略：低 blast radius 分段（動的是每天 cron 在跑的生產報告！）

- **S1 tokenize 零視覺變動**：硬編碼 `#hex`/主間距 → `var(--token)`；report `:root` 對映 tokens。改完 dry-run 產出與改前**逐位元/視覺零差異**才算過。
- **S2 視覺質感層**：套上面質感；preview 三寬比對 + 互動點測。
- **S3 token-lint**：`scripts/check_design_tokens.py` flag 殘留硬編碼 → 註冊 `governance_config.yaml` 的 **full** profile（advisory，復用 P117 gov.preflight 總指揮，**不新增 CI step**）。
- **S4 端到端 gate**：generate()/replay 產 report 成功 + 既有 pytest 全套零回歸 + preview 375/768/1440 + LINE WebView UA。
- **S5 收官**。

## 🚫 邊界（務必守）

**不碰**：`reporter/generator.py` 渲染邏輯、Jinja 資料流（保所有 `{% %}`/class/id/`onclick`：switchRegion/openSidePanel/toggleTranslation）、`daily_report.yml`、cron、後端、`index.html`（P121）。只動 report.html 的 CSS/標記樣式 + 新增 checker/config/test。

## 🔑 關鍵 file:line（report.html，動工直接用；MASTER §3/§6 有更多）

- `:root` 既有變數：report.html:13-31（粉櫻品牌色 + glow，要對映 tokens）
- 角色背景：`.fixed-background-fortress` 106-122（yaya_bg.png 已在 live 同目錄）
- 卡片：`.card` 125；`.card-header` 缺 CSS（要補，見 MASTER §6 #2）
- 熱詞：`.hot-tag` 1234-1263（藍，tokenize 保留）；熱詞區 HTML 1765-1778
- feed：`.feed-container` 331-339（#3 已加呼吸）；`.post-card` 347-399；feed HTML 1790-1838（DOM：feed-container>post-container>post-card>a>title/content，P119 沿用既有 DOM 只套樣式）
- `.yaya-highlight` 類未定義、用 inline style（要補類，見 MASTER §6 #3）

## 🚫 鐵律

- `py` 不用 `python`（Windows，跑 ui-ux-pro-max 加 `-X utf8`）
- TASK_HISTORY.md 禁全讀：`grep -n "^### "` 錨點 + Read offset≤200；寫用 `cat >> heredoc`
- **push 前問阿喜**；P120/P121 各自凍結計畫書 + 阿喜核准
- **preview_screenshot MCP 此機環境會逾時故障** → 改 Edge headless CLI：`"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --virtual-time-budget=5000 --window-size=W,H --screenshot=out.png URL`（背景大圖給足 virtual-time；server 用 `.claude/launch.json` 的 p118-design-system 或新建 report 預覽）
- preview server 中途可能掛（ERR_CONNECTION_REFUSED）→ preview_start 重啟
- pre-push hook 在 `.githooks`；snapshot 回退點動工前先建

## 📂 git 現況

- `main` = `a521d5c`（**已 push、main↔origin 同步**）；含 P118 設計系統 design-system/ + 收官。
- P119 凍結 commit（本手冊 + PHASE_119_PLAN v1）：待 commit/push（**push 問阿喜**）。
- 整站重設計藍圖：**P118 地基✅ → P119 報告視覺+token-lint → P120 響應式/LINE/A11y → P121 Landing**。

## ⏳ 不在 P119 範圍（登記，勿混入）

- **#1 熱詞點擊「真的連到來源」的後端行為** / **#2 芽芽內文 placeholder + 芽芽舊文 freshness**：後端/內容戰線，與視覺分開（P119 只做熱詞「可點 affordance」視覺，不碰 side panel 後端）。
- **index.html / Landing**：P121。
- **LINE WebView 正式適配 + A11y 全套**：P120（P119 preview 先順手顧手機寬度即可）。
- P117 雲端 gov.preflight ci 真驗（待 cron）/ R-037 / R-039：數據驅動觸發，不動。

---

*交接手冊 by P118 收官視窗 Claude（Opus 4.8 1M）｜2026-06-15｜新視窗：讀此 + PHASE_119_PLAN.md v1 + variant-bc.html → S0 snapshot → 動工 S1-S5。核心：套質感保骨架（功能零刪）、tokenize-first 低風險、熱詞保藍、token-lint advisory。*
