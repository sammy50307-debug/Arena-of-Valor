# Arena of Valor — 設計系統 MASTER（混搭：芽芽粉櫻品牌色 + 儀表板結構）

> P118 整站重設計①設計系統地基 ｜ 2026-06-15 ｜ Opus 4.8
> **唯一真相源**：`design-system/tokens.css`。本檔說明每組 token 用途 + 混搭綜合決策 + 芽芽品牌鎖定理由。
> 原始 ui-ux-pro-max 輸出留存於 `design-system/aov/MASTER.md`（provenance，未經混搭修飾）。

---

## 0. 定案 LOOK（阿喜 S4 簽核，2026-06-15）

> ✅ **定案方向 = `design-system/variants/variant-bc.html`（B+C 融合：雜誌封面風 × 霓虹玻璃）**。P119 以此為唯一視覺依據。

**美學定位**：保留芽芽身份（**滿版角色立繪 / 粉櫻主色 / 薄荷 / 🌸 吉祥物 / 櫻花動效 / 光暈**），疊上**雜誌編輯式版型**（大 hero 主標 + 頭條大版位 + 01/02/03 編輯精選 + 多欄故事）＋**霓虹玻璃質感**（mesh 飽和漸層 + 霜面玻璃 panel + 發光邊框 + 發光數字列）。熱詞統計**保留藍色 pill**（阿喜拍板，僅加 cursor/hover/focus 可點 affordance）。

### S4 LOOK 迭代史（防後人重蹈覆轍）
| 版本 | 方向 | 阿喜裁決 | 教訓 |
|---|---|---|---|
| v1 | 儀表板扁平（聽 ui-ux-pro-max「反 Ornate / 無背景 / dashboard-flat」）| ❌「比之前還醜」 | **通用設計工具把吉祥物品牌個性洗成企業後台**——通用建議不可硬套 mascot 粉絲站 |
| v2 | 中度翻新（加回立繪/光暈/藍熱詞/飽和）| ⚠️「變好了但跟之前長得好像」 | 太保守＝看不出升級價值 |
| variant A/B/C | Bento / 雜誌 / 霓虹玻璃 三方向 | 選 **B+C** | C 單獨用對比過低（暗紗+粉字）；B 結構+可讀性強 |
| **variant-bc** | **B 編輯結構 + C 霓虹玻璃（修對比）** | ✅ **定案** | 淺紗+白光暈深字＝可讀；發光只在 panel 不在文字；藍熱詞還原 |

> ⚠️ **ui-ux-pro-max 通用建議不可套 mascot 品牌**（B-NNN 級教訓）：它推的 dashboard-flat / 反-Ornate / 無背景 / Fira 字體 / 藍色票，套到芽芽＝災難。只取「4/8px 間距紀律 / 資訊層級 / token 化 / a11y checklist」這些**結構性**建議，**視覺個性以阿喜審美為準**。

## 1. 混搭綜合決策表（設計腦 synthesis）

| 面向 | ui-ux-pro-max 推薦 | 芽芽品牌既有 | **混搭決策** | 依據 |
|---|---|---|---|---|
| 風格/結構 | Data-Dense Dashboard（KPI 卡/grid/層級/filtering） | 手刻無系統 | ✅ **取 dashboard 結構** | style domain |
| 主色 | `#1E40AF` 藍 + amber | `#db2777`/`#be185d` 粉 | ✅ **鎖芽芽粉**（override 藍） | color domain「Soft pink」專業色票驗證 |
| 背景 | `#F8FAFC` 純灰 | 粉→薄荷漸層 | ✅ **保留漸層** | 品牌識別 |
| 字體 | Fira Code/Fira Sans（技術 mono） | Outfit + Noto Sans TC | ✅ **留品牌字**（Outfit 幾何感本就 dashboard-friendly；Fira 太技術不合吉祥物品牌） | typography domain |
| 間距 | 4/8px scale（xs→3xl） | ad-hoc rem | ✅ **採 4/8px scale** | 解 #3 鬆散/貼太近；UX 鐵則 touch ≥8px |
| 陰影 | 中性微陰影 sm→xl | 粉霓虹 glow + neon-breath | ✅ **採微陰影 + 1 道柔粉品牌陰影**；棄 neon | Anti-pattern「Ornate design」 |
| icon | SVG（Heroicons/Lucide），**禁 emoji** | emoji 📊📰 品牌個性 | ⚖️ **保留 emoji 當品牌資產**（明文 override 通用規則）+ 補 `aria-hidden`/`role` | 吉祥物品牌例外，記於 §4 |
| 互動 | hover 過渡 150-300ms / cursor-pointer / row highlight | neon pulse | ✅ **採克制 hover + cursor-pointer 全可點**；棄 neon pulse | Pre-Delivery Checklist |
| 熱詞 #1 | cursor-pointer + 非純色傳達 | 藍漸層 pill（off-brand）+ 純色可點 | ✅ **重設計：粉 pill + 連結 affordance（底線/icon）+ focus 環** | color-only=HIGH 嚴重度 |

## 2. Token 群用途（對照 tokens.css）

| 群組 | token 範例 | 用途 |
|---|---|---|
| **(A) 品牌鎖** | `--brand-pink #db2777`、`--brand-gradient`、`--brand-glass*` | 從 report.html:13-31 萃取，**強制保留**不被推薦色蓋（RP2） |
| **色階** | `--pink-50..900`、`--slate-50..900`、`--mint-*` | 原子色階，元件不直接用裸 hex |
| **語意色** | `--color-text/-muted/-subtle`、`--color-primary/-strong`、`--color-positive/-negative/-neutral` | **P119 消費層**：report.html 硬編碼換成這些 |
| **間距** | `--space-1..16`（4/8px 基準） | 卡片內距/feed gap/區塊外距；解 #3 |
| **字級** | `--text-xs..4xl`、`--weight-*`、`--leading-*` | 模組化階梯；中文內文 `--leading-normal 1.6` |
| **圓角** | `--radius-sm..3xl`、`--radius-full` | card 28px、post-card 24px、pill 999px（對齊既有） |
| **陰影** | `--shadow-xs..xl`、`--shadow-brand(-hover)` | 微陰影 + 柔粉品牌陰影（取代 neon glow） |
| **動效** | `--ease-out`、`--dur-fast/base/slow` | 150-300ms 過渡；`prefers-reduced-motion` 已關 |
| **層級** | `--z-base/sticky/overlay/panel/toast` | 側欄/遮罩堆疊 |
| **a11y** | `--focus-ring` | 鍵盤焦點可見環 |

## 3. 三關鍵元件規格（mockup.html 落地 + P119 對齊 report.html）

1. **區塊卡片** `.card`：`--color-surface` + `--brand-glass-blur` + `--radius-3xl` + `--space-8` 內距 + `--shadow-brand`。header = emoji icon + h2（`--text-xl` / `--color-primary-strong`）。
   - 對應 report.html:125 `.card` + `.card-header`。
2. **真實熱詞統計** `.hot-tag`（**#1 重設計**）：粉系 pill（`--color-primary-soft` 底 / `--color-primary` 字）+ 底線或 `🔗` affordance + `cursor:pointer` + `--focus-ring` + `.tag-count` 計數。
   - 對應 report.html:1234-1263；**棄藍漸層**，資訊不只靠顏色（UX color-only HIGH）。
3. **文章 feed + 滾輪** `.feed-container`/`.post-card`：feed `--space-6` gap + `--space-2` padding（#3 呼吸）；post-card `--color-surface-sub` + `--radius-2xl` + `--space-6` 內距。元件列：region-tag + platform + 重複徽章 + #序/分數；標題 `--color-primary`（line-clamp 2）+ 內文 `--color-text-muted`（line-clamp 3、`--leading-normal`）。
   - 對應 report.html:331-399 + 1790-1829。

## 4. Pre-Delivery Checklist（P119 機器/人工驗收門；token-lint advisory 守護）

- [ ] report.html/index.html 無硬編碼 `#hex` / 任意 px（換 `var(--token)`）— **token-lint P119 上線**
- [ ] 所有可點元素有 `cursor:pointer`（#1）
- [ ] hover/狀態切換用 150-300ms 過渡
- [ ] 文字對比 ≥ 4.5:1（**實算 WCAG，非憑感覺**）：`#be185d` on 白 ≈ 6.0:1 ✅；`#db2777` on 白 ≈ 4.6:1 ⚠️剛過、on 粉底 `#fdf2f8` ≈ 4.3:1 ❌小字邊緣不過 → **小字優先用 `--color-primary-strong`（#be185d）**，`#db2777` 僅用於大標題/邊框/icon；P119 上線前以 WebAIM Contrast Checker 復驗並標 WCAG 等級。`--color-positive` 已由 mint-600 升 mint-700（#047857 ~5.3:1 留餘裕）
- [ ] 鍵盤焦點可見（`--focus-ring`）
- [ ] `prefers-reduced-motion` 已尊重
- [ ] 響應式 375 / 768 / 1024 / 1440 + LINE WebView UA（P120）
- [ ] 資訊不只靠顏色傳達（情緒/可點 配 icon/文字）
- **品牌例外（明文）**：保留 emoji 作吉祥物品牌個性，視為裝飾性 → 補 `aria-hidden="true"`，語意另以文字承載（不違反 a11y）。mockup 情緒徽章符號（◕◒◔）已包 `aria-hidden`、`.is-hot` 焦點環已改雙環（粉底上可見）。
- **token-lint 範圍例外（明文，反膨脹）**：token-lint（P119）應掃**色值（#hex）＋主間距/字級**，**不**掃元件內單用微尺寸（icon 框 40px、scrollbar 6px、底線 offset 3px、icon 字號 1.1-1.2em）。這些是一次性元件尺寸，過度抽象成 token 反增維護成本、且讓 lint 太吵（低 ROI 規則該降級）。微尺寸保留為字面值是刻意決策。

## 5. 邊界與時效

- **P118 不動 live**：本檔 + tokens.css + mockup.html 皆 sandbox；report.html/index.html/generator.py 不碰，外觀真正改變在 **P119**。
- ui-ux-pro-max 為設計顧問（啟發式、召回率僅供參考）；最終 LOOK 由阿喜人工簽核（X4-J）。
- 快照時效（X3）：ui-ux-pro-max 庫升級需重產 `design-system/aov/MASTER.md`；本綜合決策以 2026-06-15 為準。

## 6. P119 報告落地補帳清單（5-lens 對抗審查產出 · RP1「美但套不進」防線）

> P118 不動 live；以下為 mockup↔report.html 的已知落差，P119 動工 punch-list（Evidence→Contract）。動工前以 UX lint 比對 mockup class 名 vs report.html HTML。

| # | 落差 | report.html 現況 | P119 動作 | 嚴重度 |
|---|---|---|---|---|
| 1 | `.hot-tag` 色彩倒置（**#1 核心**） | 藍漸層 `#1e3a5f→#2563eb`、白字（report.html:1240-1263） | 整段重寫成粉系 pill + `›`/底線 affordance + focus 環（照 mockup:.hot-tag） | **S** |
| 2 | `.card-header`/`.card-icon` 無 CSS | HTML 用類但 CSS 0 行（report.html:1525-1527 等） | 補 card-header/icon CSS（照 mockup） | **S** |
| 3 | `.yaya-highlight` 類未定義 | 用 inline `style="background:#fdf2f8;color:#db2777"`（report.html:1805,1829） | 加 `.yaya-highlight` 類 + 移除 inline，改 token 漸層 | A |
| 4 | 語意層(C) 未覆蓋全部元件 | `.post-platform`(#e2e8f0/#475569)、`.region-tag.tag-tw`(藍)、score 等散置裸值 | tokens.css 擴 `--platform-*`/`--region-*` 語意 token；report.html 一對一替換 | A |
| 5 | DOM 巢狀差異 | `.feed-container>.post-container>.post-card(div)>a>title/content`（report.html:1790-1838） | P119 沿用 report.html 既有 DOM，只套 token 樣式（mockup 為視覺+class 名參考，非 DOM 規格） | B |
| 6 | post-content 行高不一 | 硬編碼 `line-height:1.7`（report.html:398） | 換 `var(--leading-normal)`（1.6）統一 | B |

**P119 上線同步**：`scripts/check_design_tokens.py`（token-lint）註冊進 `governance_config.yaml` 的 `full` profile（advisory），掃 report.html/index.html 硬編碼 `#hex`/主間距 px → 防 #1/#2/#3 類設計債無聲復發。
