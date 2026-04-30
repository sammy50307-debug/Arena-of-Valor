# 📋 Phase 63 子計畫書 v1.2（凍結待動工）

- **凍結日期**：2026-04-26 深夜
- **凍結視窗**：Claude Code session `486ea5c2-9ab9-41e0-8457-66122dc2d1e6`
- **入編日期**：2026-04-27（補登）
- **權威性**：本檔為 Phase 63.1 / 63.2 / 63.3 的**完整無損草案**，TASK_HISTORY.md 對應段落為骨架精煉版，**遇到細節衝突以本檔為準**。

---

## 🌐 大背景

Phase 63 GitHub Actions 自動排程部署當晚（2026-04-26），主公發現兩個獨立問題：

1. **GitHub Pages 戰報停在 2026-04-05**（落後 21 天）
2. **LINE 點按鈕進去網頁「畫面有在跑只是滑動不了」**

當晚連夜診斷出三條路徑：63.1（landing page 自動更新）、63.2（LINE 滑動排查）、63.3（Landing UI/UX 統一）。

---

## 📜 Phase 63.1 — Landing Page 自動指向最新戰報（手機+桌機完美 RWD）

### 🎯 目標

每次產出新戰報時，自動回頭改寫 root `index.html` 的 **4 個 href + 顯示文字**，讓 landing page 永遠指向最新（與最近 4 份）戰報，**最新 + 4 份歷史 = 共 5 份**。

### 🔍 根因診斷

`index.html` 第 220/227/231/235 行，**4 個地方都寫死指向 `aov_report_2026-04-05.html`**：

```html
[第 220 行] <a href="data/reports/aov_report_2026-04-05.html" class="main-btn">
[第 221 行]    進入最新戰報 (2026-03-30)        ← 連結+文字都要動
[第 227 行] <a href="...aov_report_2026-04-05.html" class="history-item">
[第 229 行]    03/29 戰報                       ← 連結+文字都要動
[第 231-237 行] 同上 ×2
```

**主程式產出新報告之後沒有任何步驟回頭更新 `index.html`**，所以 Pages 永遠停在 4-5 那份。

### 🔬 完整診斷紀錄（2026-04-26 當晚）

| 項目 | 狀態 | 證據 |
|---|---|---|
| 今日報告是否產生 | ✅ 有 | `origin/main` 新增 `data/reports/aov_report_2026-04-26.html`（commit `d116281`）|
| github-actions[bot] 是否推 commit | ✅ 有 | `a777f69..d116281` 是 bot 自動推的 |
| **landing page 是否更新** | ❌ **沒有** | `index.html` 4 處 `href` 全寫死 `2026-04-05.html` |
| **LINE「滑不動」根因** | ⏳ 待釐清 | → 已拆成 Phase 63.2 |

### 🧱 子階段拆解

```
Phase 63.1.0  人工前置 — index.html 結構 3→5 + 全平台 RWD CSS
Phase 63.1.1  自動化 — reporter/generator.py 加 _update_landing_page()
Phase 63.1.2  防呆 — 報告不足 5 份時的退化處理
```

### 🛠️ 實作位置

`reporter/generator.py:211` — 在 `canonical_path` 同步完之後、`yaya_bg.png` 同步之前，插入新邏輯（**約 30 行**）。

### 🔧 邏輯流程（63.1.1）

```
1. 掃 data/reports/aov_report_YYYY-MM-DD.html （只抓主版本，跳過 _v2/_v3 等）
2. 依日期 desc 排序，取前 5 份
3. 讀 root index.html
4. 用嚴格 regex 替換 5 個 <a href> 與對應顯示文字：
   • href 用全日期：data/reports/aov_report_2026-04-26.html
   • main-btn 文字：進入最新戰報 (2026-04-26)
   • history-item 文字：04/26 戰報 (MM/DD)
5. 比對內容若無變化則 skip 寫入（避免 git 噪音）
6. 整段用 try/except 包，失敗不阻斷主流程
```

### 🛡️ 安全護欄

| 風險 | 護欄 |
|---|---|
| regex 誤傷 index.html 其他內容 | 鎖定 `data/reports/aov_report_\d{4}-\d{2}-\d{2}\.html` 嚴格模式 |
| `data/reports/` 為空時 crash | 先檢查 list 非空，否則 skip |
| 重複寫入造成 git 噪音 | 內容比對 unchanged 則不寫 |
| 主流程被連累 | try/except 包住，失敗只 log warning |
| 報告不足 5 份 | 63.1.2 用「— 暫無歷史報告」+ `href="#"` 佔位 |

### 📊 6 項潛在風險評估

| # | 風險 | 嚴重度 | 說明 | 處置方案 |
|---|---|---|---|---|
| **R1** | **CSS `.history-grid` 排版破版** | 🟠 中高 | 原始設計 3 個 item 並排，多半用 `grid-template-columns: repeat(3, 1fr)` 或 flex。塞 5 個進去可能變兩行、擠變形、間距亂掉。 | 寫程式前**先 Read 完整 index.html 的 CSS**，看 `.history-grid` 的實際定義，必要時同步調整 grid 欄數 / 加 `flex-wrap` |
| **R2** | **首次部署需動 HTML 結構** | 🟠 中 | 目前 index.html 只有 3 個 `<a class="history-item">`，要 5 份就**得先加 2 個 `<a>` 區塊**才能讓 regex 找到目標。這把工作從「純文字替換」升級到「結構修改 + 替換」。 | 計畫裡新增「**Phase 63.1.0 前置作業**」：手動先把 index.html 從 3 個 `<a>` 擴成 5 個（一次性動作） |
| **R3** | **手機橫向擠爆** | 🟡 中 | landing page 在手機 viewport 寬度約 360-414px，5 個 history-item 並排每個只剩 ~70px，文字「04/26 戰報」絕對裝不下。 | 加 mobile breakpoint：`@media (max-width: 768px) { .history-grid { grid-template-columns: 1fr; } }` 讓 5 個直排 |
| **R4** | **報告數不足 5 份時的退化** | 🟢 低 | 系統剛部署或 reports 目錄被清空時，可能只有 1~4 份。5 份是 hardcoded 期望值，少於 5 要怎麼處理？ | Python 端：if `len(reports) < 5`，能補幾個就補幾個，剩下的 history-item 用「— 暫無歷史報告」+ `href="#"` 佔位（避免空 href 失效或 404） |
| **R5** | **早期報告格式不一致** | 🟢 低 | 主公本機 `data/reports/` 有從 2026-03-18 到今天的報告，跨度 39 天，早期格式可能跟最新模板有差異（例如 Phase 33 之前的版本）。多列 5 份會把更早期、長相不一致的報告暴露給訪客。 | 短期不處理（反正只是歷史檔），如真的視覺差太多，未來可加「最早可顯示日期」白名單 |
| **R6** | **重複觸發寫入產生 git 噪音** | 🟢 低 | 每次跑 generator 都改 index.html，5 份比 3 份要動的字數多了 ~67%，git diff 訊雜度上升。 | 維持原本的「內容比對 unchanged 則 skip 寫入」護欄即可 |

### 💻 資源成本分析（5 份 vs 3 份）

| 資源面向 | 3 份 | 5 份 | 影響 |
|---|---|---|---|
| **DOM 節點數** | 3 個 `<a>` | 5 個 `<a>` | 多 2 個元素 ≈ 多 0.001ms 解析時間 |
| **HTTP 請求** | 0（連結不預載） | 0 | **完全相同** |
| **圖片資源** | 3 個 lucide icon | 5 個 lucide icon | icon 本來就用 inline SVG，多畫 2 個 ≈ 多 50 bytes |
| **CSS 複雜度** | 1 個 grid | 1 個 grid（+1 條 RWD media query） | 多 1 行 CSS |
| **JS 執行** | 無變化 | 無變化 | **完全相同** |
| **頁面總大小** | ~15KB | ~15.2KB | 增加 0.2KB（< 1%） |

**結論**：5 份的「資源成本」連討論的價值都沒有。**真正會多花的是「視覺成本」**——手機上 5 個並排會變很擁擠，這就是為什麼 R3 必須做 RWD。

### 📐 RWD 規格定案

#### 桌機端（≥1024px）
- 5 個 history-item 一字排開、間距均勻
- hover 時有微妙的視覺反饋
- 完整 glassmorphism / 動畫特效全開

#### 平板端（768px ~ 1023px）
- 5 個 history-item 可考慮 → 變成 1 排 5 個（間距縮小）或 3+2 排版
- 動畫保留但粒子數量酌減

#### 手機端（< 768px）— **強制驗收條件**
```
[ 04/26 戰報 ]   ← 全寬、置中、44px 高
[ 04/25 戰報 ]
[ 04/24 戰報 ]   ← 5 個直排
[ 04/23 戰報 ]
[ 04/22 戰報 ]
```
- CSS：`grid-template-columns: 1fr;` + `gap: 12px;` + 加大觸控目標
- 字級放大保證可讀性
- **觸控目標 ≥ 44px**（蘋果 HIG 標準）
- 粒子動畫降頻或關閉（Phase40 Bible 早記載過粒子是性能殺手）

#### LINE in-app browser 端（最嚴苛）
- 等 Phase 63.2 釐清滑動問題後，這個算「特殊 client」加開兼容測試

### ✅ 測試計畫

1. 本機跑 `py main.py --showcase`（會走完 generator 全流程）
2. `git diff index.html` → 應該只有 5 個 href + 5 段文字 + RWD CSS 變動
3. 用瀏覽器開本機 `index.html` 看畫面是否正確（桌機 + 手機 viewport 模擬器）
4. 跑完 push 後上 GitHub Pages 看真實生效

### 📦 改動清單

- ✏️ `index.html`：手動加 2 個 `<a class="history-item">`、補 mobile RWD CSS（一次性，~10 行）
- ✏️ `reporter/generator.py`：新增 `_update_landing_page()` ~30 行
- 🚫 不動 `main.py` / config / 戰報模板

### ⏱️ 工作量估計

- 63.1.0 人工前置：5 分鐘
- 63.1.1 寫程式：5 分鐘
- 63.1.2 防呆：3 分鐘
- 本機測試：3 分鐘
- commit + push：2 分鐘
- **總計：~18 分鐘**

---

## 🔍 Phase 63.2 — LINE 戰報頁滑動失靈排查（待主公測試）

### 🎯 主公證詞（關鍵線索）

> 「畫面有在跑只是我滑動不了」

→ 這個證據非常關鍵——通常指向**觸控事件被攔截**，而不是渲染卡頓。

### 🔬 LINE 連結真相（已查）

`notifier/line_bot.py:51` 與 `main.py:286`：

```python
daily_summary["report_url"] = f"{base_url}/data/reports/aov_report_{date_str}.html"
```

**主公點 LINE 按鈕跳到的不是 landing page，而是戰報網頁本身** (`aov_report_*.html`)。所以「滑不動」的根因不在 landing page，而在**戰報頁本身**。

### 🕵️ 3 大嫌疑

| # | 嫌疑 | 機率 | 排查方法 |
|---|---|---|---|
| **A** | **戰報頁有 `fixed` 全螢幕背景層 z-index 太高，吃掉觸控事件** | 🔴 高 | 檢查戰報 template `#fixed-background-fortress` 的 `pointer-events` |
| **B** | **戰報頁 body / main 的 `overflow` 被 CSS 鎖死** | 🟡 中 | 搜 `overflow:\s*hidden` |
| **C** | **LINE in-app browser 對 `backdrop-filter` + `position: fixed` 處理有 bug** | 🟡 中 | 用主公 Chrome / Safari 直接開同網址測試是否正常 |

### 🧪 主公明天測試 SOP（最快判斷法）

**用手機原生 Chrome / Safari 直接貼那個戰報網址**——

- 如果在原生瀏覽器**也滑不動** → 是嫌疑 A 或 B（網頁本身 bug）
- 如果在原生瀏覽器**滑得動** → 是嫌疑 C（LINE 內建瀏覽器 bug，那要改成「點按鈕用外部瀏覽器開」）

### 📌 對照測試結果決定動工方向

| 測試結果 | 動工方向 |
|---|---|
| 原生瀏覽器也滑不動 | 改戰報 template CSS（修 A 或 B） |
| 原生瀏覽器滑得動 | 改 LINE button 行為（加參數強制外部瀏覽器開） |

---

## 🎨 Phase 63.3 — Landing Page UI/UX 風格統一（已選策略 C）

### 🎯 主公訴求

> 「Landing 跟 Report 風格相近、但要有可辨識的差異」

這是經典的「品牌語言一致性 vs 場域辨識度」問題。

### 🎨 設計策略 3 選 1（當晚草案）

#### 策略 A：同色系不同濃度
- Report：飽和的桃紅 + 櫻花粉漸層（高彩度、繁複）
- Landing：**同色系但低明度**——桃紅退到 5% 透明度當點綴，主背景偏暗（深紫/墨黑）
- 差異辨識度：⭐⭐⭐⭐
- 設計工作量：⭐⭐

#### 策略 B：同視覺元素不同密度
- Report：櫻花粒子滿版、玻璃卡片堆疊、資訊密集
- Landing：**簡約版**——只保留 1 朵巨大櫻花作 hero、玻璃卡片只有 1 張置中、資訊極簡
- 差異辨識度：⭐⭐⭐⭐⭐
- 設計工作量：⭐⭐⭐

#### 策略 C：同調性不同色相 ✅（**主公已選定**）
- Report：桃紅 / 櫻色（暖色、活潑）
- Landing：**同樣 glassmorphism + 同樣字型 + 同樣動畫節奏，但改成藍紫色系**（冷色、沈穩——像「指揮中心入口」對比「戰場前線」）
- 差異辨識度：⭐⭐⭐⭐⭐
- 設計工作量：⭐⭐⭐⭐

### 🎨 策略 C 配色定案

**核心定調**：「**指揮中心入口**（Landing）vs **戰場前線**（Report）」雙場域對比

| 元素 | Report（戰場前線）| Landing（指揮中心入口） |
|---|---|---|
| 主色相 | 桃紅 `#db2777` / 櫻粉 | **藍紫冷色** — 候選：靛 `#6366f1` / 皇家紫 `#7c3aed` / 深海藍 `#1e3a8a` |
| 強調色 | 暖橘 / 玫瑰 | **冷青** — 電光藍 `#22d3ee` / 霓虹紫 `#a855f7` |
| 字型 | 同（保留品牌一致性） | 同（保留） |
| 玻璃質感 | 同（保留 glassmorphism） | 同（保留） |
| 動畫節奏 | 同（保留櫻花/呼吸燈節奏） | 同（節奏一致，但粒子改成「資料流光點」或「星塵」這類冷調象徵） |
| 情緒語感 | 熱血、活躍、戰鬥 | 冷靜、戰略、運籌帷幄 |

### ⏳ 未拍板事項

具體配色組合（靛 / 皇家紫 / 深海藍三選一）、動畫元素細節（資料流光點 vs 星塵），等真正進入 63.3 時主公再做最終決定。今晚先記錄方向。

---

## 📦 最終待辦清單（凍結）

```
☐ Phase 63.1.0  index.html 結構 3→5 + 桌機橫排 + 手機直排 RWD CSS
☐ Phase 63.1.1  reporter/generator.py 加 _update_landing_page()
☐ Phase 63.1.2  報告不足 5 份的退化處理
☐ Phase 63.2    主公手機對照測試（LINE vs 原生瀏覽器）→ 決定修哪邊
☐ Phase 63.3    Landing 改色（策略 C：藍紫冷色 + 保留品牌語言）
```

---

## 🔗 相關檔案座標

- `index.html`（landing page，root）
- `reporter/generator.py:211`（63.1.1 動工點）
- `notifier/line_bot.py:51`（LINE button URL 來源）
- `main.py:286`（report_url 組裝點）
- `Phase40_Flagship_Bible.md`（Report 端視覺真經，63.3 設計時參考）

---

*本檔由 2026-04-26 視窗 `486ea5c2-9ab9-41e0-8457-66122dc2d1e6` 凍結，於 2026-04-27 補登。*
