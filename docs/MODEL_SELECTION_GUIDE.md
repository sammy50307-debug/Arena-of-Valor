# 模型選擇指引 v1.1（跨 AI 助理通用 / 已定稿）

> **適用對象**：Claude Code（Anthropic）、Gemini CLI / Antigravity（Google）、其他副駕助理。
> **三檔同步協議**：本檔（專案特化主檔）→ `~/.claude/CLAUDE.md` 全域章節（縮版）→ `~/.gemini/GEMINI.md` 全域章節（縮版）。
> **更新日期**：2026-05-07

---

## 🎯 TL;DR（30 秒版）

| 情境 | 用什麼 |
|---|---|
| **不知道用什麼** | **Sonnet 4.6**（預設主力）|
| 不可逆 / 跨多系統 / 偵錯模糊 / 新架構 | **Opus 4.7** |
| Opus 卡住（同題 3 輪解不出 / 自相矛盾）| 換 **Gemini 3.1 Pro (High)** |
| 純機械 / 批次 >50 次 / 一行修法 | **Haiku 4.5** 或 **Gemini 3 Flash** |
| 多模態（圖 / 影片 / 音訊）| **Gemini 3 系列** |
| 一次塞 >200K context | **Gemini**（1M context）|
| 大量便宜跑 | **Gemini 3 Flash**（$0.50/$3）|

**升級階梯**：`Sonnet → Opus → Gemini 3.1 Pro (High) → 主公拍板`

---

## 目錄

- [§1 6 模型總表](#1-6-模型總表)
- [§2 快速決策表（任務 × 影響半徑）](#2-快速決策表)
- [§3 決策樹](#3-決策樹)
  - 3.1 升 Opus / Pro High 的 5 連問
  - 3.2 降 Haiku / Flash 的 3 連問
  - 3.3 升級階梯（Opus 卡住協議）
  - 3.4 對話中切換模型的判斷
  - 3.5 Anthropic 還是 Google？
- [§4 6 維度權重對照](#4-6-維度權重對照)
- [§5 跨助理特例與已知限制](#5-跨助理特例與已知限制)
- [§6 AOV 專案特化情境](#6-aov-專案特化情境)
- [§7 使用協議](#7-使用協議)

---

## 1. 6 模型總表

| 模型 | 提供商 | 最佳 use case（一句話）| 速度 | 成本 (in/out per 1M, USD) | Context | 知識截止 |
|---|---|---|---|---|---|---|
| **Sonnet 4.6** | Anthropic | 日常工程實作首選，平衡 80% 場景 | 快 | $3 / $15 | 200K | 2025-08 |
| **Opus 4.7** | Anthropic | 不可逆決策、跨系統推理、新架構設計 | 中慢 | $15 / $75 | 200K | 2025-08 |
| **Haiku 4.5** | Anthropic | 批次、低延遲、純機械轉換 | 極快 | $1 / $5 | 200K | 2025-08 |
| **Gemini 3.1 Pro (High)** | Google | Opus 解不出時的換腦 fallback、超長 context 推理 | 慢 | $2 / $12（≤200K）；$4 / $18（>200K）| 1M in / 64K out | 官方未公開 |
| **Gemini 3.1 Pro (Low)** | Google | 多模態 + 中等推理；無法完全關 thinking | 中 | 同上（thinking 用量低）| 1M in / 64K out | 官方未公開 |
| **Gemini 3 Flash** | Google | 大量便宜、長 context 輕推理、多模態快通 | 極快 | $0.50 / $3 | 1M in / 64K out | 官方未公開 |

> ⚠️ **Gemini Pro 實務劣化警告**：社群實測指出 **200K+ tokens 開始出錯增多**，500-600K+ 明顯失準；Vertex API 路徑曾回 131,072 tokens rate limit error。重要任務建議控在 200K 內，1M 是上限不是常用區。

> 註：Anthropic 為公開定價；Gemini 抓自 [官方 pricing](https://ai.google.dev/gemini-api/docs/pricing)（2026-05-07）。Google 從未公開 Gemini knowledge cutoff（已多方查證無果）。

---

## 2. 快速決策表

> **影響半徑分級**（17 層框架 META3）：1-2 檔 = 微 / 3-9 檔 = 標準 / 10+ 檔 = 重大
> ⭐ = AOV 日常高頻情境（5 秒落點區）

| 任務類型 ↓ / 影響半徑 → | 1-2 檔（微）| 3-9 檔（標準）| 10+ 檔（重大）|
|---|---|---|---|
| 程式碼小改（typo / 格式 / 一行修法）| Haiku 4.5 / Gemini 3 Flash | Sonnet 4.6 | Sonnet 4.6 |
| ⭐ 程式碼新增（新模組 / 新功能）| Sonnet 4.6 | **Sonnet 4.6** | Opus 4.7 → 卡住升 Gemini Pro High |
| ⭐ 重構（搬程式 / 改介面）| Sonnet 4.6 | Sonnet 4.6 / Gemini Pro Low | Opus 4.7 → 卡住升 Gemini Pro High |
| 架構設計（新系統 / 新流程）| — | **Opus 4.7** | Opus 4.7 → 卡住升 Gemini Pro High |
| 偵錯（症狀清楚 / 已定位）| Sonnet 4.6 | Sonnet 4.6 | Opus 4.7 |
| ⭐ 偵錯（症狀模糊 / 跨系統）| Sonnet 4.6 | **Opus 4.7** → 卡住升 Gemini Pro High | Opus 4.7 → 卡住升 Gemini Pro High |
| ⭐ 文件 / 翻譯 / 整理 | Haiku 4.5 / Gemini 3 Flash | Sonnet 4.6 | Sonnet 4.6 |
| ⭐ 對話 / 規劃 / 草案討論 | Sonnet 4.6 | Sonnet 4.6 | **Opus 4.7** |
| 批次操作（>50 次重複）| — | Haiku 4.5 / Gemini 3 Flash | Sonnet 4.6（重要批次）|
| 多模態（圖 / 影片 / 音訊）| Gemini 3 Flash | Gemini Pro Low | Gemini Pro High |
| ⭐ 資料分析（找趨勢 / 比對 / 統計）| Sonnet 4.6 | Sonnet 4.6 | Opus 4.7 → 卡住升 Gemini Pro High |
| 教學 / 解釋概念 | Sonnet 4.6 | Sonnet 4.6 | Sonnet 4.6 |

---

## 3. 決策樹

### 3.1 升 Opus 4.7 / Gemini 3.1 Pro (High) — 5 連問

任一答「是」就升：

1. **不可逆（X1）嗎？** force-push / drop schema / 刪倉 / 改 prod 設定
2. **需要跨多個系統聯合推理？** 不只一個檔、要同時權衡多模組
3. **症狀和根因可能不在同一層？** 同題已換 3 輪解法仍沒進展
4. **需要創意 / 設計新架構？** 不是套既有 pattern
5. **17 層稽核風險加權 ≥ 5？**（META4 暫停請示閾值）

### 3.2 降 Haiku 4.5 / Gemini 3 Flash — 3 連問

**全部**答「是」才降：

1. **純機械轉換**？格式轉 / 一對一映射 / 模板填充
2. **批次量大或時延敏感**？單次成本要壓低
3. **不需推理，照樣畫葫蘆**？沒有判斷力需求

### 3.3 升級階梯（Opus 卡住協議）

```
Sonnet 4.6（預設）
  ↓ 升級觸發（§3.1 五連問任一是）
Opus 4.7（深度推理）
  ↓ 卡住觸發（見下）
Gemini 3.1 Pro (High)（換廠牌、換思路、長 context）
  ↓ 仍卡住
主公拍板下一步（拆分任務 / 找文件 / 換人問）
```

**Opus 卡住的可觀察判定**（任一達成 = 卡住）：

- 同一題在對話中**連 3 輪**都沒解到
- AI 推理出現**自相矛盾**（前一輪結論與後一輪相反）
- 主公明確表達「**卡住了**」「**換個思路**」「**這個沒用**」
- 修了 3 次 bug 仍出現同樣 error trace

**AI 行為守則**：
- ✅ 達卡住判定 → **AI 必須主動提醒主公換 Gemini 3.1 Pro (High)**，並附理由（不能只說「換換看」）
- ✅ 提醒模板：「主公，這題 Opus 4.7 已連 [N] 輪沒進展（[具體症狀]），建議切 Gemini 3.1 Pro (High) — 1M context 可一次塞更多檔，推理路徑不同可能繞開盲點」
- ❌ 不可在主公沒問之前自己一直耗在 Opus 上
- ❌ 主公拒絕換時尊重決定，不再二次提醒

### 3.4 對話中要不要切換模型？

已經在某模型對話到一半，是否該切？

| 情況 | 動作 |
|---|---|
| 任務性質完全改變（例：從寫程式 → 設計新架構）| **切**，並重新走 §3.1 |
| 同任務但卡住（達 §3.3 卡住判定）| **AI 主動提醒切到 Gemini 3.1 Pro (High)**（升級階梯下一階，見 §3.3）|
| 同任務、同模型、進展順利 | **不切**，避免上下文流失 |
| 主公主動要求切 | **無條件切**，不質疑 |
| 切換成本（要重述上下文）> 切換收益 | **不切**，先請 AI 整理交接摘要 |

### 3.5 Anthropic 還是 Google 怎麼選？

| 情境 | 建議 |
|---|---|
| 工具串接（MCP / function call）密集 | Anthropic（Claude 工具使用更穩）|
| 超長 context（>200K）| Gemini（1M 上下文，但留意 200K+ 劣化）|
| 多模態（圖 / 影片 / 音訊）| Gemini |
| 中文 / 繁中創作 | 兩家皆可，個別比較看當下任務 |
| 純程式碼（標準 stack）| Anthropic Sonnet/Opus 略強 |
| 大量批次便宜跑 | Gemini 3 Flash 最便宜 |
| Opus 卡住的換腦 fallback | Gemini 3.1 Pro (High)（不同推理路徑）|

---

## 4. 6 維度權重對照

| 維度 | Sonnet 4.6 | Opus 4.7 | Haiku 4.5 | Gemini Pro High | Gemini Pro Low | Gemini 3 Flash |
|---|---|---|---|---|---|---|
| 任務類型適配 | 全能 | 重思考 | 輕任務 | 重思考 | 全能 | 輕中任務 |
| 影響半徑容忍 | 3-9 檔 | 10+ 檔 | 1-2 檔 | 10+ 檔 | 3-9 檔 | 1-2 檔 |
| 可逆性風險容忍 | 半可逆 | 不可逆 | 可逆 | 不可逆 | 半可逆 | 可逆 |
| 語意深度 | 中高 | 極高 | 低中 | 極高 | 中高 | 中 |
| 速度 | 快 | 中慢 | 極快 | 慢 | 中 | 極快 |
| 成本 | 中 | 高 | 低 | 中 | 中低 | 極低 |

---

## 5. 跨助理特例與已知限制

- **Claude Code 子代理（Agent tool）**：模型由系統依 agent 類型決定，主公**無法手動切換** → 不在本指引選擇範圍。
- **Gemini 3 系列 `thinkingLevel`**（取代舊版 `thinkingBudget`）：

  | 設定 | 行為 | 主公列舉對應 |
  |---|---|---|
  | `minimal` | 約等於關閉思考（**僅 Gemini 3 Flash 支援**）| — |
  | `low` | 最小延遲，簡單任務 | **Gemini 3.1 Pro (Low)** |
  | `medium` | 平衡推理 | — |
  | `high` | 最深推理（**3.1 Pro 與 3 Flash 預設**）| **Gemini 3.1 Pro (High)** |

  - **重要限制**：Gemini 3.1 Pro **無法完全關閉 thinking**，最低只能到 `low`
  - 舊版 `thinkingBudget` 仍向後相容，但用在 Gemini 3 Pro 可能不穩，官方建議改用 `thinkingLevel`

- **Claude Fast 模式**：僅 Opus 4.7 有，加速但不降模型；Sonnet / Haiku 無 Fast 模式
- **Gemini 3 Pro Preview**（無 .1）已於 **2026-03-09 deprecated**，全部遷移到 3.1 Pro
- **Gemini 3.1 Flash-Lite**：本指引未納入（更輕量但能力低於 Flash，主公列舉中未提）

---

## 6. AOV 專案特化情境

| 場景 | 建議模型 | 理由 |
|---|---|---|
| 預設日常 Phase 動工 | **Sonnet 4.6** | 平衡 + 速度 + 成本 |
| Phase 開工的 17 層稽核草案討論 | **Opus 4.7** | 多維權衡 |
| jieba / 詞庫 / template 等純工程 | Sonnet 4.6 | 標準工程實作 |
| Postmortem 寫作 | Sonnet 4.6 | 結構化敘事 |
| 跨 Phase 學習復盤（每 5 Phase）| **Opus 4.7** | 跨歷史推理 |
| 真實熱詞分析 / 熱門關鍵話題（P67）| Sonnet 4.6 | 標準 8 檔工程 |
| 不可逆動作（push / 改 GHA / 改 vault 結構）討論 | **Opus 4.7** | X1 不可逆守則 |
| **報告爬蟲修 bug** | **Opus 4.7** → 連 3 輪卡住 AI 主動提醒升 Gemini 3.1 Pro (High) | 爬蟲 bug 常跨網站結構 + 解析 + 反爬，需深推理 |
| 大量報告產出 / 批次轉換 | Gemini 3 Flash | 成本最低 |

---

## 7. 使用協議

1. **Phase 計畫書**：在「動工模型」欄填本指引推薦的模型 + 理由（一句話）
2. **動工中切模型**：依 §3.4 判斷；任務性質改變 → 主公手動切換並在對話中註明
3. **AI 行為強制條款**：達 §3.3 卡住判定 → AI **必須主動提醒**升級，不可隱忍硬撐
4. **本指引版本鎖**：v1.x 為小幅修訂；新增層級 / 重大改動需走 17 層框架 META6 版本鎖流程

---

## 8. 治理與運維（v1.1 新增）

### 8.1 影響半徑表（STR7）

| 檔案 | 角色 | 變更時連帶 |
|---|---|---|
| `docs/MODEL_SELECTION_GUIDE.md` | 主檔（完整版）| TASK_HISTORY 補段 + 變更紀錄 |
| `~/.claude/CLAUDE.md`（全域章節）| 跨專案縮版（Claude）| 與主檔縮版同步 |
| `~/.gemini/GEMINI.md`（全域章節）| 跨專案縮版（Gemini）| 與主檔縮版同步 + thinkingLevel 對應表 |
| `memory/reference_model_guide.md` | AOV 記憶索引 | 30 秒速查更新 |
| `memory/feedback_workflow.md` | Phase 工作流 | Co-Authored-By 模型欄聯動 |

**規模**：5 檔 = 標準級影響半徑。

### 8.2 X4 三角審紀錄（2026-05-07）

| 視角 | 提問 | 結論 |
|---|---|---|
| **主公** | 日常翻表 5 秒能落點嗎？| ✅ TL;DR + ⭐ 標已優化 |
| **攻擊者** | 有沒有可被誤用的漏洞？| ⚠️ 任務描述若被「裝小」（例：把 10+ 檔講成 1-2 檔）會降到 Haiku 誤用 → **緩解**：§3.2 三連問**全部**為是才降，已是雙保險 |
| **接手者** | 6 個月後另一位 AI 能直接用嗎？| ✅ TOC + 目錄 + 變更紀錄齊全；§5 thinkingLevel 對應表消除歧義 |

### 8.3 回顧週期與升級觸發（X3）

- **預設回顧週期**：90 天（下次回顧：**2026-08-05**）
- **強制升版觸發**（任一達成）：
  - Gemini / Anthropic 任一廠商發布**新模型大版本**（例：Gemini 4 / Claude 5）
  - 主公**連 3 次**對某情境的選擇與本指引建議不符
  - 任一條規則被發現**已 stale**（如 deprecation、價格變動）
- **G5-1 沒人用偵測**：本指引若 **180 天內** TASK_HISTORY 無任何 Phase 引用 → 主公檢視是否已被冷落 / 框架失靈

### 8.4 回退協議（X1 半可逆動作）

若本指引需整份廢棄：

```bash
# 1. 移除主檔
rm docs/MODEL_SELECTION_GUIDE.md

# 2. 從全域檔移除追加章節（手動編輯，刪除 "## 模型選擇指引" 至檔尾）
#    ~/.claude/CLAUDE.md
#    ~/.gemini/GEMINI.md

# 3. 移除 memory 索引
rm memory/reference_model_guide.md
# 並從 MEMORY.md 刪除對應行

# 4. 還原 feedback_workflow.md Step 4 的 Co-Authored-By 寫法
```

**回退成本**：~5 分鐘人工編輯，無資料損失（本指引純文檔）。

### 8.5 Deprecation 政策（G1-3）

當有 v2.0 取代本指引：

1. v1.x 主檔頂部加 `> ⚠️ **DEPRECATED**：v2.0 已上線，本檔保留 30 天供回查` banner
2. 30 天後移入 `docs/archive/` 並從 MEMORY.md 索引移除
3. 全域兩檔（CLAUDE.md / GEMINI.md）的章節**立即**換成 v2.0 縮版

---

## 變更紀錄

- **v1.1（2026-05-07）**：跑 63 維度 + 3 Patch 完整稽核後修補 14 項。決策表加「資料分析 / 教學解釋」、「批次 1-2 檔」格改 N/A；§3.1/§3.4 卡住用詞統一；新增 §8 治理與運維（影響半徑表 / X4 三角審紀錄 / 回顧週期 / 回退協議 / deprecation 政策）。命中率從 ~65% 推到 ~93%。
- **v1.0（2026-05-07）**：定稿。新增 TL;DR、目錄、§3.4 對話中切換、§5 thinkingLevel 對應表、決策表 ⭐ 高頻標記、最佳 use case 一句話欄。卡住判定從「30 分鐘」改為「連 3 輪 / 自相矛盾 / 主公明確表達」更可執行。刪除已過期的 §8 拍板項。
- **v0.3（2026-05-07）**：主公拍板 4 題回收。新增「報告爬蟲修 bug」場景；新增 §3.3 升級階梯；不納入 Batch 價；確認 (High)/(Low) = thinkingLevel。
- **v0.2（2026-05-07）**：WebFetch + WebSearch 補資料。Context 確認 1M/64K；thinkingLevel 四級補上；3.1 Pro 無法關 thinking 標明；knowledge cutoff 作罷。
- **v0.1（2026-05-07）**：初稿，待主公審核。
