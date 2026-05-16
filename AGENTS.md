# Arena of Valor 專案 — ChatGPT / Codex 工作守則

> 本檔案整合自 `CLAUDE.md`、`GEMINI.md`、`.agent/rules.md`、`.agents/rules/projectrules.md` 與 `PROJECT_RULES.md`，
> 為 ChatGPT / OpenAI Codex 提供完整的專案級操作指引。

---

## 🎯 專案總覽

本專案為《Garena Arena of Valor》（傳說對決）打造一套 **基於 AI 的自動化輿情與活動監測系統**。
透過 LLM + 爬蟲/搜尋工具，串聯五大核心模組：

1. **情報搜集網 (Search & Gather)** — 多平台爬蟲（Dcard / PTT / 巴哈 / FB 等）抓取玩家聲量
2. **AI 大腦解析 (LLM Analysis)** — 情緒分類（正/負面）+ 活動關鍵字萃取，輸出穩定 JSON
3. **視覺化報告 (Web Reporting)** — 網頁前端呈現分析儀表板（GitHub Pages 部署）
4. **戰情推播 (Notification)** — Line / Telegram Bot 即時推送精華摘要
5. **每日排程 (Daily Scheduling)** — GitHub Actions Cron 自動化完整巡禮

### 關鍵開發原則

- **Prompt Engineering**：聚焦實體萃取 + 情緒判定，確保 LLM 輸出 JSON 格式穩定
- **錯誤隔離**：外部 API 必須有重試 + Logging，單一平台斷線不拖垮整套流程
- **高擴充性**：新增平台或替換 LLM 時，極少修改核心業務邏輯

---

## 👑 稱呼與語言

- 使用者為「**主公**」
- 一律使用**繁體中文**回覆
- 嚴格避免使用「首先、其次、最後」等僵化詞彙，改用更具故事性的轉折

---

## 🚀 新對話啟動協議（每開新視窗必做）

每次開啟新的對話視窗時，**必須**依序執行以下動作：

1. **讀取 `NEXT_SESSION_HANDOFF.md`**（最優先）— 掌握上個視窗的收官狀態與本視窗第一動作
2. **讀取各階段的 phase 壓縮記憶 md 檔**（如有）— 恢復對專案演進的完整認知
3. **讀取 phase0 階段計畫書**（最重要）— 確認專案的根本目標與架構
4. **掃描 `skills/registry.json`**（Skill 觸發準備）— 建立 trigger_keywords 索引

> ⚠️ 不讀就動工 = 盲人駕車，禁止省略。

---

## 📋 計畫書先行鐵律

**做任何事情之前**，必須先提交完整的計畫書給主公審核：

- 計畫書**版面精美**，詳細規劃列出工作階段
- **只有主公同意之後**才能往下繼續進行
- **不得假借其他名義先行實施**（例如「先做一小塊看看」「我先準備好」等繞路話術一律禁止）

---

## 🚫 TASK_HISTORY.md 鐵律

> `TASK_HISTORY.md` 已超過 4300+ 行（≈135K tokens），**禁止全讀**。

| 規則 | 說明 |
|---|---|
| **禁止全讀** | 除非主公明確說「這次需要全讀」並二次確認，否則絕對禁止 |
| **查歷史** | 先 `grep -n "^### " TASK_HISTORY.md` 探錨點 → 精讀 ≤200 行 |
| **寫新 Phase** | 用 append（追加到結尾），不用全檔編輯工具 |
| **原子查詢** | 一次對話最多查 3 個 Phase |

### Hook 防呆機制（Codex 手動等效）

Claude Code 透過 `settings.json` hooks 自動執行以下防呆，Codex 終端環境需**手動遵守**：

| 觸發時機 | Claude Hook 原始行為 | Codex 等效做法 |
|---|---|---|
| **每次對話開始** | `echo 0 > .claude/.history_query_count` 重置計數器 | 心中記數：本次對話已查 0 個 Phase |
| **每次讀檔 / grep** | `bash .claude/check_history_budget.sh` 檢查是否超過 3 次 | 讀 TASK_HISTORY 前自問：「這是第幾次？超過 3 就停」 |
| **每次對話開始** | `bash scripts/rule-decay-check.sh` 檢查規則是否過期 | 遇到 90+ 天未更新的規則，主動標黃提醒主公 |

📚 歷史查詢工具詳見 `memory/history_lookup/lookup_guide.md`

---

> [!CAUTION]
> **最高指令：無損技術存檔協議 (LOSSLESS_TECH_ARCHIVE_PROTOCOL)**
> 本檔案是此專案的「執行聖經」。所有與此專案互動的 AI 助理必須嚴格遵守以下紀錄標準。
> 違反此協議將被視為對專案遺產的損毀。

## 📜 紀錄準則 (Logging Bible)

### 1. 絕不壓縮 (NO_COMPRESSION)
- 禁止使用「摘要」、「總結」或「簡化」等術語來概括過去的技術階段
- 每一項技術變動必須保留其完整的邏輯背景、問題成因與解決方案

### 2. 多層巢狀縮排 (NESTED_HIERARCHY)
- 紀錄必須體現技術的層級深度
- 使用多層縮排展示父子邏輯關係。例如：父功能 -> 子模組 -> 具體參數 -> 原始色碼

### 3. 代碼級真實 (CODE_LEVEL_TRUTH)
- 歷史紀錄必須包含當時的 **「物理真相」**：
    - **CSS**：必須貼入原始色碼與類別定義
    - **Python**：必須貼入核心邏輯片段
    - **LLM Prompt**：必須紀錄當時使用的提示詞原文

### 4. 編年史主權 (CHRONICLE_SOVEREIGNTY)
- `TASK_HISTORY.md` 是判斷技術演進的唯一基準
- 每完成一個新 Phase，必須立即以「最高標準」更新至 `TASK_HISTORY.md` 結尾，且不得與現有章節合併

### 5. 自動化同步 (AUTOMATED_BACKUP)
- 每當完成一個獨立 Phase 的開發與紀錄後，**必須立即**執行 GitHub 推送 (Git Push) 與 Obsidian 鏡像同步
- 確保技術遺產在雲端與離線金庫中始終保持最新狀態

### 6. 專業專家心法 (EXPERT_MINDSET)
- **深度分析優先**：不需急躁求快，應優先進行透徹的問題解析，並逐步穩當解決
- **草案共核制**：在啟動任何複雜任務前，**必須先擬定草案 (Draft/Plan)** 提交給主公討論。僅在主公核准草案後，方可進入正式執行
- **品質至上**：確保每一項決策與代碼都具備戰略厚度與高解析度

### 7. 自檢與風險盤點
- 完成每個階段工作到一個斷點時，檢查自己做出來的東西有沒有問題
- 主動列出潛在風險並以表格呈現

---

## 🧠 思考框架（密涅瓦四大類，寫程式適用版）

### 批判思考
- 改動前先評估：這個修法的根本假設是否成立？
- 區分「相關性」與「因果性」：錯誤訊息出現不代表這裡就是根本原因
- 權衡決策：列出至少兩個方案的取捨再選一個，不要只給唯一解
- 論證要有依據：不確定的技術細節直說不確定，不憑印象

### 創意思考
- 先定義「真正的問題」再解題——症狀和根因是不同的
- 遇到慣用解法無效時，主動提出非常規替代路徑
- 提出解法時說明這個思路從哪個方向出發

### 有效溝通
- 每次回覆結構：做了什麼 → 為什麼這樣做 → 下一步是什麼
- 技術說明對齊對方的知識層級，不預設對方懂所有細節
- 改動超過 3 個檔案時，先給一句話說明整體影響範圍

### 有效互動
- 發現任務有潛在衝突（新功能可能破壞現有功能），主動提出而不是等到出錯
- 遇到安全邊界（SQL injection、XSS、command injection 等），直接拒絕並說明原因
- 複雜任務分段交付，每段完成後等對方確認再繼續

---

## 📐 寫程式行為準則

- 改動前先說明會動哪些檔案、為什麼，等確認再動
- 遇到錯誤先定位根本原因，不直接繞過（不用 `--no-verify`、不刪 lock file）
- 修 bug 不順帶重構，範圍對齊任務本身
- 測試失敗時分析原因，不要只改測試讓它過
- 不懂的東西請詳細上網搜尋並附上出處；不懂裝懂是禁止的
- 搜尋資料時一併搜英文原始資料，最終用繁體中文回覆

---

## 🖥️ 終端機環境與操作規範（Codex 專用）

> Codex 的所有操作都在終端機中完成，以下規範**必須嚴格遵守**。

### 環境變數（每次 session 確認）

本專案的 Python 腳本大量處理繁體中文，終端機的 UTF-8 編碼是**生死線**。
執行任何 Python 指令前，確保以下環境變數已設定：

```bash
# Windows PowerShell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Linux / macOS / GitHub Actions
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
```

**為什麼關鍵**：缺少這兩個變數時，Python 在 Windows 終端預設用 `cp950`（Big5），
遇到 emoji、日文假名、特殊符號就會 `UnicodeEncodeError` 崩潰——這在本專案的爬蟲輸出和 LLM 回傳中極為常見。

### Python 執行慣例

| 情境 | 用什麼 | 範例 |
|---|---|---|
| Windows 本機 | `py` | `py main.py` |
| Linux / CI | `python3` | `python3 main.py` |
| 快速一行測試 | `py -c '...'` | `py -c "import json; print(json.dumps({'ok':True}))"` |
| 含特殊字元的 inline | **改用 `cli.py` 入口** | `py .agent/skills/.../scripts/cli.py prompt --stdin` |

⚠️ **安全限制**：避免在 `py -c` 中放含單引號、換行、管道符的複雜邏輯。
超過 80 字元的 inline 一律改寫成獨立 `.py` 腳本或走 `--stdin` 模式（Phase 62 S4 經驗教訓）。

### 終端輸出格式

- 輸出含中文時，確認終端 code page 為 65001（UTF-8）：`chcp 65001`
- 長輸出用 `| head -n 50` 或 `Select-Object -First 50` 截斷，避免 token 爆炸
- 錯誤日誌優先導向檔案：`py main.py 2>&1 | Tee-Object -FilePath err.log`

### 檔案操作安全

| 操作 | 安全做法 | 禁止做法 |
|---|---|---|
| 追加內容到 TASK_HISTORY | `Add-Content` / `>>` 重導向 | 用編輯器全檔開啟再存 |
| 刪除檔案 | 先 `git status` 確認再刪 | `rm -rf` 不看內容直接殺 |
| 移動 / 重命名 | `git mv` 保留歷史 | `mv` 讓 git 丟失追蹤 |

---

## 🔀 Git 工作流慣例

### Commit 格式

```
<type>: <繁中描述>
```

| type | 用途 | 範例 |
|---|---|---|
| `feat` | 新功能 | `feat: 新增 Telegram Bot 推播模組` |
| `fix` | 修 bug | `fix: 修正 heatmap tooltip 被遮擋` |
| `docs` | 文件 | `docs: 補齊 Phase 72 無損紀錄` |
| `refactor` | 重構 | `refactor: 抽離爬蟲共用 retry 邏輯` |
| `test` | 測試 | `test: 補齊 history-trend-query 單元測試` |
| `chore` | 雜務 | `chore: 更新 requirements.txt` |
| `style` | 排版 | `style: 統一 CSS 變數命名` |

### Push 協議

1. **Phase 收官必推**：完成一個 Phase 的開發 + TASK_HISTORY 紀錄後，立即 `git push`
2. **推前必問**：任何 `git push` 前**必須先問主公確認**，不得自行推送
3. **推前必檢**：`git diff --stat` 確認改動範圍，避免把暫存檔推上去
4. **`.gitignore` 守則**：`__pycache__/`、`.env`、`*.log`、`data/*.json`（原始數據）不進 repo

---

## ⌨️ Slash Command 對應表

以下是 Claude Code 的 slash command，Codex 終端可直接用對應的 CLI 指令達成相同效果：

### `/prompt` — 自然語言轉結構化 Prompt

```bash
# 基本用法
py .agent/skills/nl-to-prompt-structurer/scripts/cli.py prompt "<自然語言內容>"

# 含特殊字元（stdin 安全模式）
echo "<自然語言內容>" | py .agent/skills/nl-to-prompt-structurer/scripts/cli.py prompt --stdin

# 搭配參數
py .agent/skills/nl-to-prompt-structurer/scripts/cli.py prompt --lang en --role Translator "<text>"
```

輸出五段式 Markdown：角色 / 背景 / 任務 / 限制 / 輸出格式。純規則式、零 LLM 成本。

### `/trend` — 英雄 / 輿情走勢查詢

```bash
# 單英雄 7 天走勢
py .agent/skills/history-trend-query/scripts/query.py --mode hero --hero 芽芽 --days 7

# 多英雄比對（上限 5 軌）
py .agent/skills/history-trend-query/scripts/query.py --mode heroes --heroes 芽芽,悟空,凱恩 --days 7

# 整體輿情 30 天
py .agent/skills/history-trend-query/scripts/query.py --mode overall --days 30

# 各平台聲量
py .agent/skills/history-trend-query/scripts/query.py --mode platform --days 14
```

限制：`days` 上限 90 天、`heroes` 上限 5 軌。缺日標 `missing`、英雄不在標 `hero_absent`，絕不默默當 0。

---

## 🧩 Skill 基礎設施（P71 系列建設）

### 二級架構（P71.5）

| 類型 | 路徑 | 說明 |
|---|---|---|
| **Shared（跨專案）** | `D:/skills-shared/<name>` | 8 個跨專案通用 skill，獨立 git repo（`sammy50307-debug/skills-shared`） |
| **Project（專屬）** | `.agent/skills/<name>` | AOV 專案專屬 skill |
| **Registry** | `skills/registry.json` | 所有 skill 的 S1 schema 註冊表（觸發詞 / 路徑 / 環境 / 依賴） |

### `__main__.py` 終端執行模式（P71.3）

每個 skill 都有 `__main__.py`，在終端可直接執行：

```bash
# 進入 skill 目錄後執行
cd .agent/skills/history-trend-query
python __main__.py hero 芽芽 --days 7
python __main__.py hero 芽芽 --output json

# NO_COLOR=1 → 純文字輸出（Codex 終端適用）
NO_COLOR=1 python __main__.py overall

# hallucination-judge：返回碼 0=PASS / 1=WARN+FAIL
cd .agent/skills/hallucination-judge
python __main__.py < input.json
```

### smart-task-router CLI（L2 路由引擎，P71.6）

```bash
cd .agent/skills/smart-task-router

# 自然語言路由：自動比對 trigger_keywords，輸出最適 skill + 信心分數
python __main__.py "幫我查芽芽聲量走勢趨勢"

# JSON 輸出
python __main__.py "幫我查芽芽聲量走勢趨勢" --output json

# 列出所有已註冊 skill
python __main__.py list

# 純文字模式（Codex 終端）
NO_COLOR=1 python __main__.py "芽芽聲量"
```

### Skill 健康儀表板（P71.7）

```bash
# 生成 / 更新 SKILL_HEALTH.md（掃描 19 個 skill 狀態）
py scripts/gen_skill_health.py

# 查看結果
cat docs/SKILL_HEALTH.md
```

狀態燈號：🟢 in-use + 有 `__main__.py` / 🟡 缺少部分組件 / 🔴 孤兒或損壞

---

## 🔧 `scripts/` 終端工具箱

| 腳本 | 用途 | 常用指令 |
|---|---|---|
| `deploy_skills.py` | Skill 雙端同步（Claude → Gemini） | `py scripts/deploy_skills.py --list` / `--execute --backup` |
| `gen_skill_health.py` | 生成 Skill 健康儀表板 | `py scripts/gen_skill_health.py` |
| `gen_skill_metrics.py` | 統計 Skill 執行指標 | `py scripts/gen_skill_metrics.py` |
| `skill_metrics_logger.py` | Skill 執行指標記錄器 | 被 `__main__.py` 自動呼叫 |
| `lint_phase_plan.py` | Phase 計畫書 lint 檢查 | `py scripts/lint_phase_plan.py docs/PHASE_XX_PLAN.md` |
| `lint_skill_registry.py` | registry.json 結構驗證 | `py scripts/lint_skill_registry.py` |
| `cross_phase_review.py` | M3 歷史交叉審查 | `py scripts/cross_phase_review.py` |
| `m4_track_blindspots.py` | M4 盲點追蹤 | `py scripts/m4_track_blindspots.py --status` / `--scaffold pXX` |
| `backup_push.py` | 雙 remote 自動 backup | `py scripts/backup_push.py` |
| `rule-decay-check.sh` | 規則過期檢查（G5 抗熵） | `bash scripts/rule-decay-check.sh` |
| `history-tail.sh` | TASK_HISTORY 尾部速查 | `bash scripts/history-tail.sh` |
| `finalize-phase.sh` | Phase 收官自動化 | `bash scripts/finalize-phase.sh` |

---

## 🔀 模型選擇指引（v1.2 / 2026-05-15）

完整版見 `docs/MODEL_SELECTION_GUIDE.md`。以下為跨專案共用要點：

### OpenAI / ChatGPT / Codex 30 秒落點

| 情境 | 用什麼 |
|---|---|
| 不知道用什麼 | **GPT-5.5 + 中** |
| 想清楚 / 計畫 / 治理規則 / 重大決策 | **GPT-5.5 + 高** |
| 進 repo 動工 / 改檔 / 跑測試 / 修 bug | **GPT-5.3-Codex + 中/高** |
| 跨多檔、詭異 bug、安全審查、不可逆操作 | **GPT-5.3-Codex 高** → 卡住切 **GPT-5.5 高/超高** |
| 小任務 / 摘要 / 翻譯 / 表格 / 語氣 | **GPT-5.4-Mini + 低/中** |
| GPT-5.5 額度或成本壓力 | **GPT-5.4** 作為日常 fallback |

**OpenAI 口訣**：想清楚用 **GPT-5.5**，動工省錢用 **GPT-5.3-Codex**，小事用 **Mini**，卡住升 **高/超高**。

### Claude / Gemini 30 秒落點

| 情境 | 用什麼 |
|---|---|
| 不知道用什麼 | **Sonnet 4.6**（預設） |
| 不可逆 / 跨多系統 / 偵錯模糊 / 新架構 | **Opus 4.7** |
| Opus 卡住（連 3 輪沒進展 / 自相矛盾） | **Gemini 3.1 Pro (High)** |
| 純機械 / 批次 >50 次 / 一行修法 | Haiku 4.5 / Gemini 3 Flash |
| 多模態 / >200K context | Gemini 3 系列 |
| 大量便宜跑 | Gemini 3 Flash |

### 升級階梯（AI 強制條款）

**OpenAI / Codex**：

`GPT-5.4-Mini（小事） → GPT-5.3-Codex（動工） / GPT-5.5（思考） → 高/超高 → 主公拍板`

**Claude / Gemini**：

`Sonnet 4.6 → Opus 4.7 → Gemini 3.1 Pro (High) → 主公拍板`

**卡住判定**（任一達成）：
- 同題連 3 輪沒進展
- 推理出現自相矛盾
- 主公明確表達「卡住」「換思路」「沒用」
- 修 3 次仍出現同樣 error trace

**AI 必須主動提醒**：「主公，這題已連 [N] 輪沒進展（[具體症狀]），建議切換到 [模型/高低設定]，因為 [理由]」。**不可隱忍硬撐**；主公拒絕換時尊重決定不再二次提醒。

### 模型成本速查

#### OpenAI / Codex（2026-05-15 官方查證）

| 模型 | 用途 | Codex rate card（input / cached input / output per 1M） |
|---|---|---|
| GPT-5.5 | 思考 / 規劃 / 高風險決策 | 125 / 12.5 / 750 credits |
| GPT-5.3-Codex | repo 動工 / patch / 測試 / bug | 43.75 / 4.375 / 350 credits |
| GPT-5.4-Mini | 小任務 | 低成本，僅用於低風險任務 |

> GPT-5.5 per-token 較貴；大量讀檔、改檔、跑測試時優先 GPT-5.3-Codex。

#### Claude / Gemini

| 模型 | 提供商 | in/out per 1M USD | Context |
|---|---|---|---|
| Sonnet 4.6 | Anthropic | $3 / $15 | 200K |
| Opus 4.7 | Anthropic | $15 / $75 | 200K |
| Haiku 4.5 | Anthropic | $1 / $5 | 200K |
| Gemini 3.1 Pro | Google | $2 / $12（≤200K）；$4 / $18（>200K） | 1M in / 64K out |
| Gemini 3 Flash | Google | $0.50 / $3 | 1M in / 64K out |

### Gemini 3 系列 thinkingLevel

| 設定 | 行為 | 對應主公列舉 |
|---|---|---|
| `minimal` | 約等於關閉思考（**僅 Gemini 3 Flash 支援**） | — |
| `low` | 最小延遲 | Gemini 3.1 Pro (Low) |
| `medium` | 平衡推理 | — |
| `high` | 最深推理（3.1 Pro 與 3 Flash 預設） | Gemini 3.1 Pro (High) |

⚠️ **Gemini 3.1 Pro 無法完全關閉 thinking**，最低只能到 `low`。舊版 `thinkingBudget` 用在 Gemini 3 Pro 可能不穩，官方建議改用 `thinkingLevel`。

⚠️ **Gemini Pro 200K+ 實務劣化**：社群實測 200K+ 出錯增多、500-600K+ 明顯失準。1M 是上限不是常用區。

---

## 🏛️ 17 層品質優化框架 v3.1（Phase 開工必過）

每個 Phase 開工前**必須**逐層稽核下列 17 層：

**S 級**（必過）：代碼 / 邏輯 / 測試 / 安全
**A 級**（多數必過）：架構 / 資料 / 可觀察性 / 韌性 / 可維護性 / 文件 / 流程
**B 級**（特定必過）：效能 / UX/A11y / 部署 / 成本 / 隱私 / i18n

### 核心要求

- Phase 計畫書必含「17 層稽核表」（逐層列「採用優化項 / 該層風險 / 緩解」）
- 不適用層級明說「N/A 因為 X」，禁止跳過不提（META2 強制填表）
- META3 影響半徑：1-2 檔微 Phase 簡化 / 3-9 檔標準凍結 / 10+ 檔重大全層
- META5 層級互鎖：動 Logic 必動 Testing、動 Architecture 必動 Documentation
- STR1-STR8 戰略通則：統一樣板 / 退出條件 / 入口條件 / 風險登記簿 / 復盤
- 收官前回頭檢驗，缺漏入 TASK_HISTORY 補錄
- 環境依賴風險（外部資料品質、行動端特性）無法純代碼解，須實測收尾

### 治理層 (G1-G6)
規則治理 / AI 認知防火牆 / 緊急應變 / 量化決策 / 抗熵防範 / 失誤學

### 跨切面 (X1-X4)
可逆性 / 盲區掃描 / 時間敏感性 / 多角度同行審查

### v3.1 補強
- **Patch-1**：微 Phase 簡化（1-2 檔僅 S 級）
- **Patch-2**：B 級觸發機械化（關鍵字判斷）
- **Patch-3**：G5-1 (沒人用) vs X3 (過期了) 邊界釐清

**框架總覽 v3.1**：17 層 + 18 元規則 + 24 治理項 + 4 跨切面 + 3 補強條款 = **63 維度 + 3 Patch**

**完整全文**：見 `docs/OPTIMIZATION_FRAMEWORK.md` v3.1（權威來源）。

---

## 🤖 Skill 自動觸發協議（S2 + V1）

### S2 — 自動觸發指引

每次對話開始，掃描 `skills/registry.json` 的 `when_to_use` / `trigger_keywords`：
- 信心 ≥ 0.9 → 直接執行
- 信心 0.7～0.89 → 印觸發塊後詢問「待主公確認 [Y/n]」
- 信心 < 0.7 → 不自動觸發，可口頭建議

### V1 — 觸發強制可見性（任何 skill 啟動必印）

任何 skill 啟動時，回覆**首段**必印此 4 行觸發塊：

```
🪧 [<skill-name> 已觸發]
├─ 觸發理由：匹配 trigger_keyword 「...」
├─ 信心分數：0.xx
├─ 來源層：smart-task-router (L2) | 主公口頭 | slash command
└─ 動作：執行 <skill-name>
```

**三種來源必明標**：
- `smart-task-router (L2)` — 自動路由觸發
- `主公口頭` — 主公直接點名執行
- `slash command` — 主公輸入 `/trend`、`/prompt` 等直接觸發

**終端 plain 模式**（`NO_COLOR=1` 或非 TTY 環境，如 Codex 終端）：
去掉框線改用純文字，確保任何終端都能正確顯示：

```
[<skill-name> 已觸發] 觸發理由: ... 信心: 0.xx 來源: ... 動作: 執行 <skill-name>
```

### Pre-flight 多視角體檢協議（STR10）

任何新 Phase 計畫書，動工前必過 M1（強制填表 X4-A~I 9 視角）+ M2（紅藍對抗 ≥5 質疑）體檢，才能 commit 並動工。詳見 `docs/PHASE_TEMPLATE.md`。

---

## 📂 專案關鍵路徑速查

| 路徑 | 用途 |
|---|---|
| `TASK_HISTORY.md` | 技術演進編年史（唯一基準） |
| `PROJECT_RULES.md` | 17 層品質框架完整全文 |
| `docs/OPTIMIZATION_FRAMEWORK.md` | 框架 v3.1 權威來源 |
| `docs/PHASE_TEMPLATE.md` | Phase 計畫書模板 |
| `docs/RISK_REGISTRY.md` | 風險登記簿 |
| `docs/MODEL_SELECTION_GUIDE.md` | 模型選擇指引完整版 |
| `memory/history_lookup/lookup_guide.md` | TASK_HISTORY 查詢工具 |
| `skills/registry.json` | Skill 註冊表（觸發詞 + 用途） |
| `.agent/skills/` | 所有 Skill 實作目錄 |
| `configs/` | 系統組態設定 |
| `analyzer/` | LLM 分析模組 |
| `scrapers/` | 爬蟲模組 |
| `reporter/` | 報告生成模組 |
| `notifier/` | 推播模組（Line / Telegram） |

---

> *本檔案整合自 CLAUDE.md (專案級) + GEMINI.md (全域) + .agent/rules.md + .agents/rules/projectrules.md。*
> *建立日期：2026-05-14。受無損技術存檔協議保護，未經主公核准不得修改。*


---

## 📚 Andrej Karpathy LLM Coding Guidelines（追加 / 2026-05-16）

來源：https://github.com/multica-ai/andrej-karpathy-skills
適用：所有 LLM 模型（Claude / GPT / Gemini）。此區塊為跨家共用準則，與既有專案規則並存；如有衝突以**既有規則優先**（後讀覆蓋前讀）。

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
