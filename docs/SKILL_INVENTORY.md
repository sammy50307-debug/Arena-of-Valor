# Skill 完整盤點清單
- **版本**：v1.0
- **建立日期**：2026-05-09（P71.0 產出）
- **下次更新**：P71.2 SKILL.md schema 升級完畢後

---

## 📊 概覽統計

| 指標 | 數值 |
|---|---|
| Claude 端 skill 總數 | 20 |
| Gemini 端 skill 總數 | 7 |
| 雙端共有（待 diff 裁決）| 7 |
| Claude 僅有（in-use）| 5 |
| Claude 僅有（orphan）| 8 |
| SKILL.md 有 frontmatter schema | **0 / 20**（P71.2 補）|
| 有 `__main__.py` / `main.py` | **0 / 20** |
| 有 slash command | 2（`/prompt`, `/trend`）|
| 有測試 | 18 / 20（缺：ai-news-radar、instagram-facebook-dcard、ui-ux-pro-max）|

> **孤兒率：8/20 = 40%**（P71 目標：降至 0）

---

## 🗂️ 完整盤點表（20 Claude + 7 Gemini）

### 分類一：Claude in-use（5 個）

| Skill | Type | Claude | Gemini | Slash | Test | Claude 更新 |
|---|---|---|---|---|---|---|
| `api-quota-guardian` | exec | ✅ in-use | ❓ ND | — | ✅ | 2026-04-25 |
| `hallucination-judge` | data | ✅ in-use | ❓ ND | — | ✅ | 2026-04-25 |
| `history-trend-query` | pipe | ✅ in-use | ❓ ND | `/trend` | ✅ (4) | 2026-04-25 |
| `hot-deployer` | exec | ✅ in-use (GHA) | ❓ ND | — | ✅ | 2026-04-25 |
| `nl-to-prompt-structurer` | pipe | 🟡 /prompt only | ❓ ND | `/prompt` | ✅ | 2026-04-26 |

> ND = Not Deployed（未確認是否在 Gemini 端）

---

### 分類二：Gemini 實戰版（7 個）— 待 diff 裁決

Claude 端於 2026-04-25 一次性批次回流，但從未在 Claude 端服役；Gemini 端為實戰版本。

| Skill | Type | Claude 狀態 | Gemini 狀態 | Diff 行數 | Claude 更新 | Gemini 更新 |
|---|---|---|---|---|---|---|
| `ai-news-radar` | pipe | ⚠️ stale | ✅ in-use | **536 行** | 2026-04-25 | 2026-04-17 |
| `firecrawl-dynamic-breacher` | exec | ⚠️ stale | ✅ in-use | 68 行 | 2026-04-25 | 2026-04-19 |
| `html-markdown-distiller` | exec | ⚠️ stale | ✅ in-use | 92 行 | 2026-04-25 | 2026-04-18 |
| `instagram-facebook-dcard-platform-copywriter` | prompt | ⚠️ stale | ✅ in-use | **388 行** | 2026-04-25 | 2026-04-17 | → **歸檔** |
| `multi-thread-synthesizer` | exec | ⚠️ stale | ✅ in-use | 64 行 | 2026-04-25 | 2026-04-19 |
| `semantic-cache-shield` | exec | ⚠️ stale | ✅ in-use | 90 行 | 2026-04-25 | 2026-04-19 |
| `trend-anomaly-detector` | exec | ⚠️ stale | ✅ in-use | 70 行 | 2026-04-25 | 2026-04-19 |

> Claude 端 SKILL.md 比 Gemini 端新（日期較後），但 Gemini 端是實戰版本（行數較少 = 較精簡）。
> → **P71.8 由主公逐一裁決 diff，決定雙端統一版本**

---

### 分類三：孤兒（8 個）— 待主公拍板處置

| Skill | Type | Claude | Gemini | Test | 預設處置（P71_PLAN D5）|
|---|---|---|---|---|---|
| `auto-proxy-evader` | exec | ❌ orphan | ❌ orphan | ✅ | **保留**：納入 firecrawl 爬蟲流程 |
| `cot-prompt-compactor` | prompt | ❌ orphan | ❌ orphan | ✅ | **保留**：補 trigger_keywords 後自動觸發 |
| `daily-diff-radar` | exec | ❌ orphan | ❌ orphan | ✅ | **保留**：補 slash + 接報告流程 |
| `rich-push-formatter` | exec | ❌ orphan | ❌ orphan | ✅ | **保留**：補 slash + LINE bot |
| `session-handoff-packager` | pipe | ❌ orphan | ❌ orphan | ✅ | **保留**：補 slash 對應 Gemini handoff |
| `smart-task-router` | exec | ❌ orphan | ❌ orphan | ✅ | **救活**：P71.6 L2 路由引擎 |
| `ui-ux-pro-max` | data | ❌ orphan | ❌ orphan | ❌ | **保留**：修介面時自動觸發 |
| `waterfall-search-chain` | exec | ❌ orphan | ❌ orphan | ✅ | **保留**：與 api-quota-guardian 配對 |

---

## 🔧 現況診斷

### 缺失清單（P71 前）

| 項目 | 狀態 |
|---|---|
| SKILL.md S1 frontmatter schema | ❌ 全 20 個都缺（無 type/status/when_to_use/trigger_keywords 等）|
| `__main__.py` / `main.py` | ❌ 全 20 個都缺（無法 `python -m skills.<name>` 執行）|
| `skills/registry.json` | ❌ 不存在 |
| `adapters/prompt_paste/` | ❌ 不存在 |
| `docs/SKILL_HEALTH.md` | ❌ 不存在 |
| `scripts/lint_skill_registry.py` | ❌ 不存在 |
| `scripts/lint_phase_plan.py` | ❌ 不存在 |
| `scripts/deploy_skills.py` | ❌ 不存在 |
| `<proj>/GEMINI.md` | ❌ 不存在 |
| `~/skills-shared/` 獨立 repo | ❌ 不存在 |
| `.github/workflows/skill_lint.yml` | ❌ 不存在 |
| V1 觸發塊（P71 v1.2 新增）| ❌ 未實作 |

### 已有基礎

| 項目 | 狀態 |
|---|---|
| 18 / 20 skill 有測試 | ✅ |
| `/prompt` + `/trend` slash command | ✅ |
| Gemini 端 7 個 skill 實戰運作中 | ✅ |
| `~/.claude/CLAUDE.md` + `~/.gemini/GEMINI.md` 全域規則 | ✅ |

---

## 📌 動工前主公須拍板的小決策（D1-D8）

| # | 決策 | 預設答案 | 主公確認 |
|---|---|---|---|
| D1 | `~/skills-shared/` 真實路徑 | `D:/skills-shared/` | ✅ |
| D2 | shared/ 建法：本機 git init → 後上 GitHub | 兩階段 | ✅ |
| D3 | smart-task-router 信心閾值 | 0.7 詢問 / 0.9 直接執行 | ✅ |
| D4 | pre-commit 違規模式 | warning 起（2 週後升 block）| ✅ |
| D5 | 孤兒處置 | `instagram-facebook-dcard` 歸檔；其餘 19 個全保留 | ✅ |
| D6 | 是否建 `<proj>/.gemini/` | 是 | ✅ |
| D7 | 修 `~/.claude/CLAUDE.md` 同步 Pre-flight 體檢協議 | 是 | ✅ |
| D8 | lint_phase_plan.py 阻擋 hot-fix 緊急 commit | `--allow-skip` 自動入 RISK_REGISTRY | ✅ |

---

## 🗺️ 後續階段對照

| P71 階段 | 動作 | 本盤點提供資料 |
|---|---|---|
| P71.1 | 建 registry.json + lint_skill_registry.py | 20 個 skill 清單 + type 分類 |
| P71.2 | S1 frontmatter schema 升級 | 全 20 個需補 |
| P71.3 | 自包含化 + __main__.py | 全 20 個需補 |
| P71.5 | 二級分類（shared / project）| 依 A1 判斷 |
| P71.8 | diff 裁決 | 7 個待裁決（diff 行數見上）|
| P71.9 | 孤兒處置 | 8 個（預設處置見上）|

---

*P71.0 盤點完成 / 2026-05-09 / Sonnet 4.6*
