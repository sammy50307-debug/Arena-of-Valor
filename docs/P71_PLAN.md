# 🏛️ Phase 71 計畫書 — Skill 不朽性建設（Skill Permanence Architecture）

- **版本**：**v1.2（凍結版）**
- **建立日期**：2026-05-08（v1.0 起草）
- **凍結日期**：2026-05-09（v1.2 主公拍板凍結；v1.1 於 2026-05-08 凍結）
- **預估視窗數**：P71（6-8）+ P72（3-4）+ P73（4-5）= **總計 13-17 視窗**
- **狀態**：⏳ 草案已凍結，待主公核准動工
- **動工指揮文件**：本檔 + `NEXT_SESSION_HANDOFF.md`

---

## 📑 v1.2 變更摘要（vs v1.1）

| 區塊 | v1.1 | v1.2 變更 |
|---|---|---|
| 優化點 | 25 項 | **擴增至 26 項**（S 級新增 **V1 — Skill 觸發強制可見性**）|
| Pre-flight 體檢視角 | M1 共 8 個視角（X4-A ~ X4-H）| **新增 X4-I「主公可見性視角」** |
| CLAUDE.md / GEMINI.md | S2 觸發協議 | 觸發協議補 V1 顯示格式（4 行區塊）|
| `feedback_skill_startup_marker.md` | 簡單啟動標記 | 升級為 V1 完整版（觸發理由 + 信心 + 來源層 + 動作）|
| Exit Criteria | 17 條 | **新增第 18 條：V1 顯示格式 lint 通過** |
| `lint_skill_registry.py` | — | 加 V1-5 trace check（沒印觸發塊就跑 skill = block）|
| 觸發來源 | 黑箱 | **強制可見化**：自動觸發 / 主公口頭點名 / slash command 三種來源各標明 |

**v1.2 設計動機**：
> 主公口諭（2026-05-09）：「當 SKILL 觸發的時候要顯示讓我看到」
>
> 對應威脅：自動觸發越強越黑箱 → 主公看不到「為什麼觸發」→ 信任崩盤、debug 無從下手。V1 把觸發瞬間機械化攤開給主公看。

---

## 📑 v1.1 變更摘要（vs v1.0）

| 區塊 | v1.0 | v1.1 變更 |
|---|---|---|
| 優化點 | 10 項（S/A/B 各分級）| **擴增至 25 項**（C 級必加 8 + 強建 4 + 延伸 13）|
| Phase 拆分 | P71 單獨 | **拆 P71 / P72 / P73 三段** |
| Meta 層級 | 無 | 新增 **Pre-flight 多視角強制體檢 v1.0**（M1-M7）|
| PHASE_TEMPLATE | 不變 | 新增 P71.1 子任務「修 PHASE_TEMPLATE + lint_phase_plan.py」|
| 附錄 D | 無 | 新增「終端機適配協議」|
| 附錄 E | 無 | 新增「安全與永續設計」|
| GEMINI.md | 無 | 新增 Pre-flight 體檢 + Skill 自動觸發協議寫入 |

---

## 🎯 目標（主公核心需求）

> 「**這些 skill 都可以永久被使用不會消失，使用時機是 LLM 自行判斷不需要我提醒**」

拆解為兩個工程目標：

| # | 目標 | 對應威脅 |
|---|---|---|
| **G1 永久不滅** | IDE 改版 / 停服 / 換電腦 / 跨專案 / 規則退化 / AI 模型升級 |
| **G2 自動觸發** | description 太弱 LLM 不認得 / 多 skill 互搶 / LLM 視窗開頭沒讀到提示 |

**v1.1 新增第三目標**：

| **G3 Phase 計畫品質永續** | AI 計畫書天生有「賣完範圍就停」的盲點，必須機械化體檢防止漏洞累積 |

---

## 🪧 觸發

- **2026-05-08 主公拍板 v1.0**：「全部納入優化」「永久不滅」「LLM 自行判斷」「逐 skill 看 diff 主公人工裁決」
- **2026-05-08 主公拍板 v1.1**：「終端機要涵蓋」「meta 層級加入」「P71/P72/P73 拆分」
- **起源**：P70.5' 收官時順帶盤點 skill 庫

---

## 📜 背景情報（本視窗勘查所得）

### B1. Gemini 體系結構

| 對應項目 | Claude 路徑 | Gemini 路徑 | 狀態 |
|---|---|---|---|
| 全域指令檔 | `~/.claude/CLAUDE.md` | `~/.gemini/GEMINI.md` | ✅ 兩家俱備 |
| 專案指令檔 | `<proj>/CLAUDE.md` | `<proj>/GEMINI.md` | Claude ✅ / Gemini ❌（本專案無） |
| 全域 skills | `~/.claude/skills/` | `~/.gemini/antigravity/skills/`（7 個駐紮）| ⚠️ 不對等 |
| 專案 skills | `<proj>/.agent/skills/`（20 個）| `<proj>/.gemini/skills/` | Claude ✅ / Gemini ❌ |
| Slash commands | `.claude/commands/`（2 個）| **無** | Gemini 沒此機制 |
| Handoff 機制 | （無內建） | `~/.gemini/antigravity/handoff/`（4 份實檔）| Gemini 有原生 |
| **啟動標記鐵律** | ✅ | ✅ | ✅ 共用 |
| **17 層框架** | ✅ | ✅ | ✅ 共用 |

**結論**：規則層 95% 共用，入口層 0% 共用。

### B2. 「全域部署」歷史脈絡（規則退化實證）

```
P37 全域系統法典佈建                              ← 起點
P43-P50（黃金期）每個 skill 收官 = 部署到 Gemini 全域
─────────── 黃金期分水嶺 ───────────
P51-P62 開始遺忘
P63+ 完全忘記，新 skill 從未走全域部署流程
```

**G5-2「規則退化」+ X3「時間敏感性」的活生生標本**。P71 不只解現症，要根治退化機制（透過 M1+M2 機械化體檢）。

### B3. 雙端版本漂移

| 觀察 | 數據 |
|---|---|
| Gemini 端 7 個 skill 建立時間 | 2026-04-17 ~ 04-19 |
| Claude 端 7 個 skill 建立時間 | **全部同一秒 2026-04-25 20:52:30**（一次性批次回流）|
| Diff 行數 | 66 ~ 536 行（嚴重不同步）|

→ Claude 端 Bytes 較多 + 時間較新，但**從未在 Claude 端服役**（Gemini 端才是實戰版本）。

---

## 🏛️ 17 層稽核表（Patch-1：>10 檔 → 全層必填）

### S 級必過 4 層

| # | 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | **Code** | lint_skill_registry.py / deploy_skills.py / smart_task_router 啟用 / lint_phase_plan.py | 跨平台路徑（Win/*nix）| pathlib + os.path.expanduser；CI 跑 Ubuntu 同時驗證 |
| 2 | **Logic** | description schema 自動觸發 / diff 三方合併 / 紅藍對抗驗證 | smart-task-router 誤判 / 紅隊 AI 寫弱攻擊 | 信心閾值 + 攻擊力分數驗證 |
| 4 | **Testing** | 每 skill 必有 test_skill.py / lint 自身有 test / phase plan lint test | lint 太嚴擋 commit | 漸進式（warning → error）|
| 10 | **Security** | deploy_skills.py 跨目錄寫入 / Path traversal 防護（SA1）/ Secrets leakage（SA4） | 誤刪 / 注入 / 洩漏 | dry-run 預設 + auto backup + detect-secrets |

### A 級必過 7 層

| # | 層 | 採用優化項 |
|---|---|---|
| 3 | Architecture | 三層架構 + shared/project 二級分類 |
| 5 | Data | REGISTRY.json schema / SKILL.md frontmatter schema / `schema_version` 演進（F1）|
| 6 | Observability | SKILL_HEALTH.md dashboard / lint log / metrics（O1-O3，P72 落地） |
| 7 | Resilience | self-contained SKILL.md（IDE 全壞還能跑）/ 二級 fallback（D3，P73）|
| 13 | Maintainability | shared/ 跨專案倉庫 / Naming convention（A1）|
| 14 | Documentation | SKILL_INVENTORY / SKILL_HEALTH / changelog（A3，P73）|
| 15 | Process | STR9 + PHASE_TEMPLATE + Pre-flight 體檢 + pre-commit + CI |

### B 級觸發層 6 層

| # | 層 | 觸發 / 採用優化項 |
|---|---|---|
| 8 | Performance | smart-task-router 純規則匹配（不呼叫 LLM）+ registry cache |
| 9 | UX | example_invocations 用主公真實口語 / 終端 vs IDE 雙模 stdout（D1）|
| 11 | DevOps | CI workflow 加 skill + phase plan 雙 lint |
| 12 | Cost | smart-task-router 純 Python 不燒 token |
| 16 | Privacy | instagram-facebook-dcard TOS 警語 |
| 17 | i18n | trigger_keywords 中英雙收 / SKILL.en.md（I1，P73）|

### META + STR + 跨切面

| 條款 | v1.1 檢核 |
|---|---|
| META1 | ✅ S/A/B 全填 |
| META2 | ✅ 無空格 |
| META3 | 重大 Phase（>10 檔）→ 全層必填 |
| META4 | 最高加權 = 4，不暫停 |
| META5 | 動 Logic 必動 Testing ✅；動 Architecture 必動 Documentation ✅ |
| STR9 | 新增於 P71.1（skill 收官 entry_points 機械化檢查）|
| **STR10** | **新增於 P71.1**：**所有 Phase 計畫書必過 Pre-flight 多視角體檢**（M1+M2）|

---

## 🌟 26 優化點完整論證

### ⛔ S 級：必納入 P71，缺一不可（14 項 = 原 S+A 級 + V1）

#### S1 — Description Schema 強制 4 欄（自動觸發引擎）

```yaml
---
name: <skill-name>
type: executable | data | prompt | pipeline
status: in-use | candidate | archived
schema_version: 1                    # ← F1 演進欄
version: x.y.z                       # ← skill 自身版本
description: 一句話定位（≤30 字）

when_to_use:                         # ★ LLM 自動判斷依據
  - 觸發情境 1
when_NOT_to_use:                     # ★ 反例避免誤觸
  - 屬於 skill X 的範圍
trigger_keywords: [中文, English]    # ★ 強匹配信號
example_invocations:                 # ★ few-shot
  - input: "幫我看芽芽聲量"
    skill: history-trend-query

entry_points:
  cli:           "python -m skills.<name>"
  import:        "skills.<name>"
  prompt_paste:  "adapters/prompt_paste/<name>.md"
  claude_slash:  "/<slash>"

environments:                        # ★ D 環境相容性宣告
  ide:         true
  terminal:    true
  antigravity: true
  pure_llm:    true

deployed_to: [claude-project, gemini-global]
requires:
  python: ">=3.10"
  packages: [httpx, pydantic]
depends_on: []                       # B2 依賴圖預留欄位
last_used: 2026-05-08
---
```

#### S2 — CLAUDE.md / GEMINI.md 加「自動觸發指引」

兩家全域指令檔開頭加同一條：
```
對話開始掃描 skills/registry.json 的 when_to_use / trigger_keywords，
匹配到時主動執行 + 標 [<skill-name> 已啟動]，無需主公點名。
信心 < 0.7 詢問 / ≥ 0.9 直接執行。
```

#### S3 — SKILL.md 自包含（永久保險）

最壞情境：Antigravity 停服 / Claude Code 改版 / 換 IDE。**單獨把 `skills/<name>/` 丟給任何 LLM 必須能跑**。

→ 強制：完整輸入 / 輸出 schema、依賴清單 + 版本、純 CLI 執行命令、不引用外部 CLAUDE.md / GEMINI.md。

#### A1 — Shared / Project 二級分類

```
~/skills-shared/                  ← 獨立 git repo（永久備份）
  └─ ai-news-radar / html-markdown-distiller / ... 跨專案 skill
D:/AOV/skills/                    ← 本專案
  └─ history-trend-query / hallucination-judge / ... 專案專屬
```

換電腦 = `git clone` 即活。

#### A2 — 救活 `smart-task-router`

升級為 L2 路由層核心，搭配 S1 schema 工作。

#### A3 — Pre-commit + GitHub Action 雙保險

```
本機 pre-commit:
  ├─ lint_skill_registry.py  (P71)
  └─ lint_phase_plan.py      (P71，新)
CI:
  ├─ skill_lint.yml
  └─ phase_plan_lint.yml     (P71，新)
```

#### A4 — `docs/SKILL_HEALTH.md` 自動 Dashboard

每次 push 自動更新（雙端同步狀態 / 測試 / last_used / health 燈號）。

#### 🆕 V1 — Skill 觸發強制可見性（v1.2 新增 / S 級必加）

**威脅**：自動觸發越強越黑箱 → 主公看不到「為什麼觸發」→ 信任崩盤、debug 無從下手。

**觸發瞬間必顯示格式**（任何 skill 啟動，回覆首段必印此 4 行區塊）：

```
🪧 [<skill-name> 已觸發]
├─ 觸發理由：匹配 trigger_keyword 「芽芽聲量」
├─ 信心分數：0.92
├─ 來源層：smart-task-router (L2) | 主公口頭 | slash command
└─ 動作：執行 history-trend-query
```

**規則矩陣**：

| # | 規則 | 強制度 |
|---|---|---|
| V1-1 | 任何 skill 啟動瞬間，回覆首段必印 4 行觸發塊 | 強制 |
| V1-2 | 信心 < 0.7 = 詢問模式，須額外印「待主公確認 [Y/n]」 | 強制 |
| V1-3 | 三種來源（auto-router / 主公口頭 / slash command）必明標 | 強制 |
| V1-4 | 終端機 plain 模式仍顯示（純文字版，無框線） | 強制 |
| V1-5 | 違規（沒印觸發塊就跑 skill）= `lint_skill_registry.py` trace check 抓 | A 級 |

**落點**：

| 文件 | 修改 |
|---|---|
| `~/.claude/CLAUDE.md` / `~/.gemini/GEMINI.md` | S2 觸發協議補 V1 顯示格式 |
| `memory/feedback_skill_startup_marker.md` | 升級舊「啟動標記」鐵律為 V1 完整版 |
| `scripts/lint_skill_registry.py` | 加 V1-5 trace check |
| 11 個 in-use SKILL.md | example_invocations 範例加 V1 觸發塊示範 |

---

#### 🆕 v1.1 新增 C 級必加（8 項，原強建升級）

##### C1 — stdin pipe 支援
```bash
cat data.json | python -m skills.X --output json | python -m skills.Y
```
Unix 哲學「小工具組合」是終端機最大價值。

##### C3 — `NO_COLOR=1` 標準遵守
業界標準（https://no-color.org/）。CI / log file / 重定向時必須關 ANSI。

##### C5 — `--output json|plain|rich` 三模式
JSON 模式讓 skill 可被 jq / Python / CI 解析 = 真正可組合。

##### C6 — `--help` 強制必有
每個 executable skill 有 `python -m skills.<name> --help`。終端用戶第一動作。

##### SA1 — Path Traversal 防護
skill 接受檔案路徑時驗證；禁絕 `../` 跳出 sandbox。

##### SA4 — Secrets Leakage 防護
pre-commit 加 `detect-secrets`；SKILL.md 範例不可含真實 API key。

##### F1 — `schema_version` 欄位 + 自動 migrator
5 年後 SKILL.md schema 升級時，舊 skill 怎麼遷移？沒這個 = 無法升級。

##### A1-naming — Naming Convention 文件
`kebab-case` 目錄名 vs `snake_case` Python module 名 → 強制對應規則寫進 `docs/SKILL_NAMING.md`。

---

### 🅰️ A 級強建（4 項，→ 移 P72）

| # | 優化點 |
|---|---|
| **O1** | Skill 執行時長 metric（哪個變慢？資源洩漏？）|
| **O2** | Skill 失敗率 metric |
| **O3** | Token 消耗 per-skill metric |
| **D1** | 雙 remote 自動 backup（GitHub 被誤刪 / 駭）|

---

### 🅱️ B 級延伸（13 項，→ 移 P73）

| # | 優化點 |
|---|---|
| A2 | `skills/README.md` 30 秒上手 + 「第一次寫 skill」教學 |
| A3 | per-skill `CHANGELOG.md` |
| SA2 | smart-task-router 防 prompt injection |
| SA3 | semantic-cache-shield 不用 pickle（unsafe deserialization）|
| D2 | Per-Phase skill version pinning |
| D3 | api-quota-guardian 二級 fallback（離線 mock）|
| F2 | `scripts/export_to_mcp.py` 自動轉 MCP / OpenAI function |
| F3 | 1M+ context 後 skill 設計重新檢視 |
| U1 | `~/.claude/skill_usage.log` 對話紀錄 |
| U2 | Skill 推薦系統（事後提醒）|
| P1 | Skill 提案制（SKILL_PROPOSAL.md RFC）|
| P2 | Skill 退役 SOP（30/60/90 天 deprecation）|
| I1 | `SKILL.en.md` 多語系 |

---

## 🛡️ Pre-flight 多視角強制體檢 v1.0（Meta 優化 M1-M7）

> **本機制是 v1.1 最關鍵新增**：把「主公追問還有沒有漏」自動化、機械化、永久化。
> 寫入 `docs/PHASE_TEMPLATE.md` 作為 STR10，**永久套用所有未來 Phase**。

### 整體架構

```
計畫書 v1.0 草稿
    ↓
Phase 1: 強制填表（具體證據）        ← 沒填空 = lint fail
    ↓
Phase 2: 紅藍對抗（5+ 質疑）         ← 攻擊力分數驗證
    ↓
Phase 3: 歷史交叉（前 5 Phase 漏洞） ← 自動從 postmortems 抽（P72）
    ↓
計畫書通過 → 動工
    ↓（執行完）
Phase 4: 時效追溯（盲點通則化）      ← 體檢清單自我成長（P72）
```

### M1 — 強制填表（P71 必加）

```markdown
## ✈️ Pre-flight 多視角體檢

### X4-A 攻擊者視角（≥1 條，需具體）
- [ ] _______________________

### X4-B 接手者視角（新人第一週撞牆處 ≥1 條）
- [ ] _______________________

### X4-C 災難情境（≥1 個 + 緩解）
- [ ] 情境：_______ / 緩解：_______

### X4-D 5 年後視角（≥1 條）
- [ ] _______________________

### X4-E 終端 vs IDE 雙環境（≥1 條）
- [ ] _______________________

### X4-F 跨平台（Win/Mac/Linux ≥1 條）
- [ ] _______________________

### X4-G 主公個人視角（≥1 條）
- [ ] _______________________

### X4-H 觀測 / 治理視角（≥1 條）
- [ ] _______________________

### X4-I 主公可見性視角（v1.2 新增 / ≥1 條）
- [ ] 本 Phase 哪些自動行為主公看不到？如何攤開？_______________________
```

**lint 規則**：
- 任一空白 → block
- 內容 < 20 字元 → block
- 含「無風險 / N/A / 都好 / TBD」未說明 → block

### M2 — 紅藍對抗（P71 必加，強制 5+ 質疑）

```markdown
## 🔴 紅隊質疑

| # | 質疑（具體） | 攻擊力分數 | 藍隊回應 | 處置 |
|---|---|---|---|---|
| 1 | ... | S 級 | ... | 入計畫範圍 |
| 2 | ... | A 級 | ... | 入 RISK_REGISTRY |
| 3 | ... | | | |
| 4 | ... | | | |
| 5 | ... | | | |
```

**規則**：
- 5 條中至少 2 條 S 級
- 未解質疑必須入 RISK_REGISTRY

### M3 — 歷史交叉審查（→ P72 落地）

從 `docs/postmortems/` 抽前 5 個 Phase 盲點，逐條檢視當前計畫是否重蹈。

### M4 — 時效追溯（→ P72 落地）

每 Phase 收官後寫 `docs/postmortems/<phase>_blindspots.md`：「計畫書沒寫但實際撞到的問題」≥3 條，通則化加入 PHASE_TEMPLATE 體檢清單，版本升級。

### M5 — 自我反證 Falsifiability（→ P73 落地）

| 假設 | 被證明錯誤的條件 | 回滾路徑 |

強迫思考反例 → 提早發現脆弱假設。

### M6 — 跨模型 Cold Review（→ P73 落地）

計畫書 v1.0 完成後，主公一鍵複製給 Gemini 3.1 Pro 做 cold review。Claude 寫 / Gemini 審。

### M7 — Meta 體檢的體檢（→ P73 落地）

每 5 Phase 後檢視體檢清單本身：哪些視角從未發現問題？哪些漏洞反覆發生？升級 v1.0 → v2.0。

---

## ✈️ P71 計畫書本身的 Pre-flight 體檢（M1+M2 自我套用）

### M1 強制填表（本計畫書）

| 視角 | 具體發現 |
|---|---|
| **X4-A 攻擊者** | deploy_skills.py 寫入 `~/.gemini/` 時若主公 Gemini 端有未 commit 的 skill 改動，會被覆蓋（資料毀損攻擊面）|
| **X4-B 接手者** | 新人讀 P71_PLAN 看不懂為什麼 Gemini 端比 Claude 端舊 6 天 → 必須在 SKILL_INVENTORY.md 寫脈絡 |
| **X4-C 災難情境** | `~/skills-shared/` git 倉庫 force push 誤覆蓋 → 緩解：reflog + 主公本機 backup tarball |
| **X4-D 5 年後** | 25 項優化用的 schema_version=1，5 年後 schema_version=5 時舊 skill 不能讀 → migrator 必有 |
| **X4-E 終端 vs IDE** | smart-task-router 在終端 stdin pipe 模式下，可能沒有「主公對話」context 可路由 → 需要 `--no-router` 旗標 fallback |
| **X4-F 跨平台** | symlink 在 Windows 需 admin → P71.4 deploy_skills.py 必須用 copy + lockfile 而非 symlink |
| **X4-G 主公個人** | 主公換電腦時若忘了 clone `~/skills-shared/` → CLAUDE.md / GEMINI.md 開頭加新電腦 setup 提醒 |
| **X4-H 觀測治理** | 25 項優化太多，沒總體進度看板 → P71.7 SKILL_HEALTH.md 也應顯示「P71 本身的進度」|
| **X4-I 主公可見性**（v1.2）| smart-task-router 自動路由是黑箱 → 主公看不到觸發理由 → 信任崩盤 → 強制 V1 觸發塊（4 行）+ lint_skill_registry trace check |

### M2 紅藍對抗（本計畫書）

| # | 紅隊質疑 | 攻擊力 | 藍隊回應 | 處置 |
|---|---|---|---|---|
| 1 | P71.5 二級分類 mv 目錄會破壞所有現有 import 路徑（`from skills...` vs `from .agent.skills...`）→ 4 個在用 skill 立即 broken | **S** | 設計 sys.path shim 過渡 + 老路徑 alias 30 天 | 入 P71.5 子任務 |
| 2 | smart-task-router 信心閾值 0.7 / 0.9 是直覺值，沒實證 → 可能誤觸發或漏觸發 | **S** | P71.6 上線後 30 天收集主公否決樣本動態調整 | 入 RISK_REGISTRY R-P71-2 |
| 3 | M1 強制填表 lint 太嚴 → 主公急著 push 小 hot-fix 時被擋住，可能 `--allow-skip` 但養成繞過習慣 | A | 加「`--allow-skip` 自動寫入 RISK_REGISTRY 並在下個 Phase 必須補回」 | 入 lint_phase_plan.py 設計 |
| 4 | 紅藍對抗 AI 自寫，可能寫弱攻擊應付差事 | A | 攻擊力分數要求 ≥2 條 S 級 + lint 檢查是否誇大 | 入 lint 規則 |
| 5 | shared/ 倉庫升級時，所有依賴它的專案同時崩 | **S** | 採 git submodule 鎖版本，主動拉新版才升 | 入 P71.5 + P72 D1 |
| 6 | self-contained SKILL.md 文件爆增（每份 +200 行範例 + schema）→ 主公看不下去 | A | 模板化 + 自動生成 + 摺疊式章節（HTML details）| 入 P71.3 設計 |

最高 S 級 2 條（達標），未解 0 條。

---

## 📋 P71 階段詳細動作（v1.1 含新增子任務）

| # | 階段 | 主要動作 | 檔案數 | 對應優化點 | 視窗 |
|---|---|---|---|---|---|
| **P71.0** | 盤點 | `docs/SKILL_INVENTORY.md` | +1 | — | 0.5 |
| **P71.1** | 治理層 + **體檢機制** | registry.json + lint_skill_registry.py + STR9 + **lint_phase_plan.py + STR10 + 修 PHASE_TEMPLATE 加 M1+M2 章節** | +5 ~ 7 | S1, A3, **M1, M2** | **1.5**（v1.0 是 1）|
| **P71.2** | 自動觸發引擎 | SKILL.md schema 升級（含 `environments` / `schema_version`）+ CLAUDE/GEMINI.md 觸發協議 | 11 + 2 + 1 | S1, S2, F1, A1 | 1 |
| **P71.3** | 自包含化 | 11 個 in-use/Gemini-only skill self-contained + 終端機適配（D1-D3）+ `--help` / JSON output（C5, C6） | 11 個 SKILL.md + 11 個 main.py | S3, C1, C3, C5, C6, D1-D3 | 1.5（v1.0 是 1）|
| **P71.4** | 同步工具 | deploy_skills.py（copy + lockfile，**不用 symlink**）+ pre-commit + CI + Path traversal 防護 + detect-secrets | +3 | A3, SA1, SA4 | 0.5 |
| **P71.5** | 二級分類 | shared/project 拆分 + `~/skills-shared/` git repo + sys.path shim 過渡 | mv 7-9 + 1 repo | A1 | 1 |
| **P71.6** | 路由引擎 | smart-task-router 救活 + registry 接入 + 信心閾值 + 終端模式 fallback | +scripts | A2 | 0.5 |
| **P71.7** | Dashboard | SKILL_HEALTH.md 自動 + GHA + **P71 進度看板** | +1 + workflow | A4 | 0.5 |
| **P71.8** | 7 個 diff 裁決 | 主公逐一裁決（C 方案）| 7 個 SKILL.md | — | 1 |
| **P71.9** | 8 個孤兒處置 | 升級 / 歸檔（主公拍板 D5 後執行）| 8 個目錄 | — | 0.5 |
| **P71.10** | Postmortem | `P71_skill_deployment_decay.md` + `P71_blindspots.md` + R-009 入 RISK_REGISTRY | +2 | M4（首次套用）| 0.3 |

**P71 總計：6.8 - 8.5 個視窗**（v1.0 是 5-7）。

### 動工依賴關係圖

```
P71.0 (盤點) ─→ 啟動所有後續階段
   ↓
P71.1 (治理 + 體檢機制) ←── 最關鍵基底
   ↓
P71.2 (觸發引擎) ─→ 依賴 P71.1
   ↓
P71.3 (自包含化 + 終端適配)
   ↓
P71.4 (同步工具) ──┬─→
P71.5 (二級分類) ──┘
   ↓
P71.6 (路由引擎) → P71.7 (Dashboard)
   ↓
P71.8 (diff 裁決) ←─ 並行可在 P71.4 後任意跑
P71.9 (孤兒處置) ←─ 並行
   ↓
P71.10 (Postmortem，含 M4 首次套用 → 通則化升級體檢清單 v1.0 → v1.1)
```

---

## 📋 P72 範圍宣告（v1.1 新增）

| 階段 | 動作 | 對應優化點 | 視窗 |
|---|---|---|---|
| **P72.0** | metrics 基礎建設（O1-O3）| O1, O2, O3 | 1 |
| **P72.1** | 雙 remote 自動 backup | D1 | 0.5 |
| **P72.2** | 歷史交叉審查機制（M3）| M3 | 0.5 |
| **P72.3** | 時效追溯機制（M4 從手動升級為自動）| M4 | 0.5 |
| **P72.4** | metrics 接入 SKILL_HEALTH.md | — | 0.3 |
| **P72.5** | Postmortem + R 系列風險登記 | — | 0.3 |

**P72 總計：3-4 個視窗**

---

## 📋 P73 範圍宣告（v1.1 新增）

| 階段 | 動作 | 對應優化點 |
|---|---|---|
| **P73.0** | `skills/README.md` + 新人入門 | A2 |
| **P73.1** | per-skill CHANGELOG.md 機制 | A3 |
| **P73.2** | smart-task-router 安全強化 | SA2 |
| **P73.3** | semantic-cache-shield pickle 替換 | SA3 |
| **P73.4** | Per-Phase skill version pinning | D2 |
| **P73.5** | api-quota-guardian 二級 fallback | D3 |
| **P73.6** | export_to_mcp.py | F2 |
| **P73.7** | 1M+ context 後 skill 設計檢視 | F3 |
| **P73.8** | skill_usage.log + 推薦系統 | U1, U2 |
| **P73.9** | Skill 提案制 + 退役 SOP | P1, P2 |
| **P73.10** | 多語系 SKILL.en.md | I1 |
| **P73.11** | M5-M7 高階 meta（自我反證 / Cold Review / 體檢的體檢）| M5, M6, M7 |
| **P73.12** | Postmortem | — |

**P73 總計：4-5 個視窗**（按需 cherry-pick，未必全做）

---

## 📦 影響半徑（P71 部分）

| 檔案類型 | 動作 | 數量 |
|---|---|---|
| 新增 docs/ | SKILL_INVENTORY / SKILL_HEALTH / SKILL_NAMING / postmortem | 4 |
| 新增 scripts/ | lint_skill_registry / lint_phase_plan / deploy_skills | 3 |
| 新增 skills/ | registry.json / __init__.py / loader.py | 3 |
| 新增 adapters/prompt_paste/ | 11 通用 paste prompt | 11 |
| 新增 .github/workflows/ | skill_lint.yml + phase_plan_lint.yml | 2 |
| 新增 repo | `~/skills-shared/` 獨立 git | 1 |
| 修改 11 個 in-use/Gemini-only SKILL.md | schema 升級 + self-contained + 終端機適配 | 11 |
| 修改 ~/.claude/CLAUDE.md + ~/.gemini/GEMINI.md | 觸發協議 + Pre-flight 體檢 | 2 |
| 修改 <proj>/CLAUDE.md + 新增 <proj>/GEMINI.md | 專案級 | 2 |
| 修改 PHASE_TEMPLATE.md | STR9 + STR10 + M1+M2 章節 | 1 |
| 修改 MODEL_SELECTION_GUIDE.md | 三檔同步擴展為 N 檔 | 1 |
| 修改 RISK_REGISTRY / RULES_REGISTRY | R-009 ~ R-011 + STR9/10 註冊 | 2 |
| 移動 .agent/skills/ → skills/ | 20 目錄 | 20 |
| 歸檔 | 0-5 | — |
| **總計** | — | **約 60-80 檔 + 1 新 repo** |

**重大 Phase（≫10 檔）→ Patch-1 全層稽核完整**。

---

## ⚠️ 風險登記（v1.1 擴增）

| ID | 風險 | 加權 | 緩解 |
|---|---|---|---|
| R-P71-1 | deploy_skills.py 誤刪 Gemini skill | 4 | dry-run + auto backup |
| R-P71-2 | smart-task-router 信心閾值不準 | 3 | 30 天動態調 |
| R-P71-3 | lint 太嚴擋 commit | 2 | --allow-skip 自動入 RISK |
| R-P71-4 | shared/ 與專案漂移 | 3 | submodule 鎖版本 |
| R-P71-5 | SKILL.md schema 過嚴 | 2 | 漸進式 |
| R-P71-6 | P71.5 diff 裁決遺失改進 | 3 | git tag pre-P71.5 |
| R-P71-7 | CLAUDE/GEMINI.md 雙寫漂移 | 3 | sync_global_rules.py |
| R-P71-8 | self-contained SKILL.md 爆增 | 2 | 自動生成 |
| R-P71-9 | router 跑每 prompt 燒 token | 2 | 純 Python 規則 |
| R-P71-10 | Antigravity 改版改 skill 路徑 | 3 | self-contained + shared/ |
| **R-P71-11** 🆕 | **P71.5 mv 目錄破壞 import 路徑** | **4** | sys.path shim + 30 天 alias |
| **R-P71-12** 🆕 | **紅藍對抗 AI 寫弱攻擊** | 3 | 攻擊力分數 ≥2 條 S 級 lint |
| **R-P71-13** 🆕 | **Windows symlink 失敗** | 3 | 改用 copy + lockfile |
| **R-P71-14** 🆕 | **detect-secrets 誤判擋 commit** | 2 | allowlist 機制 |
| **R-P71-15** 🆕 | **schema_version migrator 漏改** | 3 | CI 跑 v0 → vN 全鏈遷移測試 |

---

## ✅ Exit Criteria（P71 完整 17 條）

1. ✅ `docs/SKILL_INVENTORY.md` 完整盤點
2. ✅ `skills/registry.json` 完整登記
3. ✅ 11 個 in-use/Gemini-only SKILL.md 通過 schema lint
4. ✅ 11 個有對應 `adapters/prompt_paste/<name>.md`
5. ✅ `scripts/deploy_skills.py` 雙向同步可正確運作（含 Windows）
6. ✅ pre-commit hook + CI workflow（雙 lint）上線
7. ✅ `docs/SKILL_HEALTH.md` 自動生成
8. ✅ `~/skills-shared/` 獨立 repo 建立 + 7-9 跨專案 skill 入駐
9. ✅ smart-task-router 對 5+ 種輸入正確路由
10. ✅ CLAUDE.md / GEMINI.md 觸發協議 + Pre-flight 體檢協議寫入
11. ✅ STR9 + STR10 寫入 PHASE_TEMPLATE
12. ✅ 7 個 diff 裁決完畢，雙端版本一致
13. ✅ 8 個孤兒處置完畢
14. ✅ Postmortem + R-009/011 入 RISK_REGISTRY
15. ✅ 全套測試零回歸
16. 🆕 ✅ `lint_phase_plan.py` 通過自我體檢測試
17. 🆕 ✅ P71_blindspots.md 寫畢，體檢清單升級 v1.0 → v1.1
18. 🆕 ✅ **V1 觸發塊**：11 個 in-use skill 全數通過 `lint_skill_registry.py` V1-5 trace check（觸發瞬間必印 4 行區塊；違規 = block）

---

## 🎓 跨 Phase 學習

### 為何 P43-P50「全域部署」傳統消失？

| 假說 | 對應 P71 對策 |
|---|---|
| 認知負擔超載 | A3（pre-commit + CI 自動執行）|
| 缺乏機械化阻擋 | A3 + STR9 → 違規不能 commit |
| 規則隱性繼承斷裂 | S2 + Pre-flight 體檢 → 每視窗開局必讀 |

### 通則化（給 G6 失誤學）

> **「寫在指令檔但沒機械化阻擋的規則，半衰期約 8-10 個 Phase」**
>
> → 適用所有專案：rule-as-code 必須有 enforcement-as-code 配套。

**v1.1 新通則**：

> **「AI 給出計畫書時會傾向『賣完當前範圍就停』，必須有強制體檢機制（M1-M7）打破此盲點」**
>
> → 適用所有 Phase：計畫書必過 Pre-flight 體檢才能動工。

---

## 🚦 動工執行協議

### 視窗 1（下個視窗開局）

```
1. 讀 NEXT_SESSION_HANDOFF.md → P71_PLAN.md (v1.1 凍結版)
2. 跑 P71.0（盤點）：寫 SKILL_INVENTORY.md
3. 主公拍板 D1-D6 小決策
4. commit + push
```

### 視窗 2-3（治理 + 觸發引擎 + 自包含）

```
P71.1（含 M1+M2 體檢機制 + lint_phase_plan.py + 修 PHASE_TEMPLATE）
P71.2（觸發引擎）
P71.3（自包含 + 終端適配）
```

### 視窗 4-5（同步 + 二級分類 + 路由）

```
P71.4 → P71.5 → P71.6
P71.5 主公確認 ~/skills-shared 路徑
```

### 視窗 6-7（Dashboard + 裁決 + 收官）

```
P71.7 → P71.8（主公人工裁決 7 skill）→ P71.9 → P71.10
P71.10 寫 P71_blindspots.md（M4 首次套用）
```

---

## 📌 動工前主公須再拍板的小決策

| # | 決策 | 預設答案 |
|---|---|---|
| D1 | `~/skills-shared/` 真實路徑 | `D:/skills-shared/` |
| D2 | shared/ 是新建 repo 還是 GitHub 上傳 | 兩階段：本機 git init → 後上 GitHub |
| D3 | smart-task-router 信心閾值 | 0.7 詢問 / 0.9 直接執行 |
| D4 | pre-commit 違規 = block 還是 warning | 起始 warning，2 週後升 block |
| D5 | 8 個孤兒哪些保留 | daily-diff-radar / rich-push-formatter / session-handoff-packager / waterfall-search-chain / api-quota-guardian；其他歸檔 |
| D6 | 是否在本機建 `<proj>/.gemini/` | 是 |
| **D7** 🆕 | **修 `~/.claude/CLAUDE.md` 同步 GEMINI.md 的 Pre-flight 體檢協議** | 是（三檔同步協議要求）|
| **D8** 🆕 | **lint_phase_plan.py 是否阻擋 hot-fix 緊急 commit** | 加 `--allow-skip` 但自動入 RISK_REGISTRY |

---

## 📎 附錄 A — 20 個 skill 處置決定快照

| Skill | Type | Claude | Gemini | 處置 |
|---|---|---|---|---|
| api-quota-guardian | exec | ✅ in-use | ❓ ND | 雙端部署 + registry 註冊（A1 跨專案）|
| hallucination-judge | data | ✅ in-use | ❓ ND | 雙端部署 + registry（AOV 專屬）|
| history-trend-query | pipe | ✅ in-use + /trend | ❓ ND | 雙端部署 + registry（AOV 專屬）|
| hot-deployer | exec | ✅ in-use (GHA) | ❓ ND | AOV 專屬 + registry |
| nl-to-prompt-structurer | pipe | 🟡 /prompt only | ❓ ND | 雙端部署 + registry（A1 跨專案）|
| ai-news-radar | pipe | ⚠️ stale | ✅ in-use | **diff 裁決（536 行）→ 雙端統一** |
| firecrawl-dynamic-breacher | exec | ⚠️ stale | ✅ in-use | **diff 裁決（68）** |
| html-markdown-distiller | exec | ⚠️ stale | ✅ in-use | **diff 裁決（92）** |
| instagram-facebook-dcard | prompt | ⚠️ stale | ✅ in-use | **diff 裁決（388）** |
| multi-thread-synthesizer | exec | ⚠️ stale | ✅ in-use | **diff 裁決（64）** |
| semantic-cache-shield | exec | ⚠️ stale | ✅ in-use | **diff 裁決（90）** |
| trend-anomaly-detector | exec | ⚠️ stale | ✅ in-use | **diff 裁決（70）** |
| auto-proxy-evader | exec | ❌ orphan | ❌ orphan | 主公裁決（與三胞胎合併？）|
| cot-prompt-compactor | prompt | ❌ orphan | ❌ orphan | 主公裁決（被 nl-to-prompt 取代？）|
| daily-diff-radar | exec | ❌ orphan | ❌ orphan | **保留**：補 slash + 接報告流程 |
| rich-push-formatter | exec | ❌ orphan | ❌ orphan | **保留**：補 slash + LINE bot |
| session-handoff-packager | pipe | ❌ orphan | ❌ orphan | **保留**：補 slash 對應 Gemini handoff |
| smart-task-router | exec | ❌ orphan | ❌ orphan | **救活**：作為 L2 路由引擎 |
| ui-ux-pro-max | data | ❌ orphan | ❌ orphan | 主公裁決 |
| waterfall-search-chain | exec | ❌ orphan | ❌ orphan | **保留**：與 api-quota-guardian 配對 |

---

## 📎 附錄 B — 動工前必讀文件鏈

```
1. NEXT_SESSION_HANDOFF.md
2. docs/P71_PLAN.md（本檔，v1.1 凍結版）
3. docs/OPTIMIZATION_FRAMEWORK.md v3.1
4. docs/PHASE_TEMPLATE.md（含 STR9 + STR10 + M1+M2 體檢）
5. CLAUDE.md / GEMINI.md（含 Pre-flight 體檢協議 + Skill 自動觸發協議）
6. memory/MEMORY.md
```

---

## 📎 附錄 C — 不朽性自證情境

### G1 永久不滅

| 情境 | 期望結果 |
|---|---|
| 換新電腦 | `git clone` 兩個 repo 即活 |
| Antigravity 停服 | `python -m skills.<name>` 純 CLI 仍活 |
| 換用 GPT / 其他 LLM | `adapters/prompt_paste/<name>.md` paste 即可 |
| 誤刪 .claude/ 整個目錄 | skills/ 完整無損，redeploy 即可 |
| 5 年後回來 | self-contained SKILL.md 仍可被未來模型讀懂 |

### G2 自動觸發

| 情境 | 期望結果 |
|---|---|
| 「幫我看芽芽聲量」 | 自動觸發 `/trend hero 芽芽` |
| 「改成 IG 貼文」 | 自動觸發 instagram-facebook-dcard |
| 「打包對話給下個視窗」 | 自動觸發 session-handoff-packager |
| 「分析昨天和今天差異」 | 自動觸發 daily-diff-radar |

### 🆕 G3 計畫品質永續（v1.1）

| 情境 | 期望結果 |
|---|---|
| 主公開新 Phase 計畫書 | 必須過 M1+M2 體檢才能 commit |
| AI 想偷懶寫弱攻擊 | 攻擊力分數 lint 擋下 |
| AI 寫「無風險 N/A」應付 | 具體性 lint 擋下 |
| Phase 收官 | 必寫 blindspots.md，體檢清單自我成長 |

---

## 📎 附錄 D — 終端機適配協議（v1.1 新增）

### D1 雙模 stdout 設計

```python
# 偵測機制
def detect_output_mode() -> str:
    if os.environ.get("NO_COLOR"):
        return "plain"
    if not sys.stdout.isatty():
        return "plain"  # 被 pipe 或 redirect
    if os.environ.get("CLAUDE_CODE_TERM"):
        return "plain"  # Claude Code CLI 模式
    return "rich"
```

可用 `--output rich|plain|json` 強制覆蓋。

### D2 終端機觸發協議

CLAUDE.md / GEMINI.md 加：
> 終端機環境（`stdin.isatty() == True` 或無 IDE selection）下，skill 觸發前詢問主公「使用 plain 輸出？」，避免亂碼

### D3 環境相容性宣告

SKILL.md frontmatter `environments` 欄：

```yaml
environments:
  ide:         true
  terminal:    true
  antigravity: true
  pure_llm:    true
```

不相容環境 → lint 自動擋誤觸發。

### 終端機深度（v1.1 補強 4 條）

- **C1 stdin pipe** — `cat x | python -m skills.X | python -m skills.Y`
- **C3 `NO_COLOR=1`** — 業界標準（https://no-color.org/）
- **C5 `--output json`** — 機器可讀，jq / Python / CI 可解析
- **C6 `--help`** — 終端用戶第一動作

---

## 📎 附錄 E — 安全與永續設計（v1.1 新增）

### Path Traversal 防護（SA1）

```python
from pathlib import Path

def safe_resolve(user_path: str, base: Path) -> Path:
    resolved = (base / user_path).resolve()
    if base not in resolved.parents and resolved != base:
        raise ValueError(f"Path traversal: {user_path}")
    return resolved
```

所有 skill 接受檔案路徑時必呼叫。

### Secrets Leakage 防護（SA4）

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

SKILL.md 範例 API key 必須是 `<your-api-key>` placeholder。

### Schema 演進（F1）

```yaml
# SKILL.md frontmatter
schema_version: 1
```

`scripts/migrate_skill_schema.py`：
```
v1 → v2: 新增 environments 欄
v2 → v3: 新增 telemetry 欄
...
```

CI 跑 v0 → vN 全鏈遷移測試。

### Naming Convention（A1-naming）

```
目錄名 (kebab-case)              Python module (snake_case)
─────────────────────            ──────────────────────────
ai-news-radar/                  → from skills.ai_news_radar
history-trend-query/            → from skills.history_trend_query

自動轉換：name.replace('-', '_')
lint 阻擋不一致命名
```

---

## 🔚 結語

P71 不是修復幾個孤兒 skill，是建立 **Skill 不朽性架構** + **Phase 計畫品質永續機制**。

最終測驗：

1. **G1 不朽**：5 年後主公換電腦 / 換 IDE / 換 LLM，skill 仍能完整運作
2. **G2 自動**：LLM 開局自動匹配，主公口語觸發無需點名
3. **G3 永續**：未來所有 Phase 計畫書必過 M1+M2 體檢才能動工

---

## 🧊 凍結聲明

**本計畫書 v1.2 於 2026-05-09 由主公拍板凍結**：

- 不再變更設計（**26 項**優化點 + Pre-flight 體檢機制 9 視角 + P71/P72/P73 拆分）
- v1.2 變更點：S 級新增 V1（Skill 觸發強制可見性）+ M1 體檢新增 X4-I（主公可見性視角）
- 後續是執行而非設計
- 動工時若需偏離本計畫，必須先 commit 計畫書 v1.3 並標明變更理由
- v1.2 為 baseline，所有偏離有可追溯版本依據

---

*計畫書版本：v1.2（凍結版）/ 2026-05-09 / Opus 4.7 起草 + 主公拍板*
*v1.1 / 2026-05-08（25 項優化點 + Pre-flight 體檢 8 視角）*
*v1.0 / 2026-05-08（10 項優化點起草）*
