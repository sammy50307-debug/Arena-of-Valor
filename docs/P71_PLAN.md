# 🏛️ Phase 71 計畫書 — Skill 不朽性建設（Skill Permanence Architecture）

- **建立日期**：2026-05-08
- **計畫書版本**：v1.0
- **預估視窗數**：5-7 個（拆 P71.0 - P71.11 共 12 階段）
- **狀態**：⏳ 計畫書待主公核准動工
- **動工指揮文件**：本檔 + `NEXT_SESSION_HANDOFF.md`

---

## 🎯 目標（主公核心需求）

> 「**這些 skill 都可以永久被使用不會消失，使用時機是 LLM 自行判斷不需要我提醒**」

拆解為兩個工程目標：

| # | 目標 | 對應威脅 |
|---|---|---|
| **G1 永久不滅** | IDE 改版 / 停服 / 換電腦 / 跨專案 / 規則退化 / AI 模型升級 |
| **G2 自動觸發** | description 太弱 LLM 不認得 / 多 skill 互搶 / LLM 視窗開頭沒讀到提示 |

---

## 🪧 觸發

- **2026-05-08 主公拍板**：「全部納入優化」「永久使用」「LLM 自行判斷」「逐 skill 看 diff 主公人工裁決」
- 起源：P70.5' 收官時順帶盤點 skill 庫，發現 75% 退化率（事後勘查 Gemini 端後修正為 40% Claude-only 孤兒，但 P50 後規則退化是真實問題）

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
| **啟動標記鐵律** | ✅ | ✅（GEMINI.md line 60）| ✅ 共用 |
| **17 層框架** | ✅ | ✅（GEMINI.md line 152-177）| ✅ 共用 |

**結論**：規則層 95% 共用，入口層 0% 共用。

### B2. 「全域部署」歷史脈絡（規則退化實證）

```
P37 全域系統法典佈建 (Global Agent Rules)              ← 起點
P43 ai-news-radar 全域部署                             ← 2026-04-17
P44 instagram-facebook-dcard 全域部署                  ← 2026-04-17
P45 html-markdown-distiller 全域部署                   ← 2026-04-18
P46 semantic-cache-shield 全域部署                     ← 2026-04-19
P47 cot-prompt-compactor 全域部署                      ← 2026-04-19
P48-P50  trend-anomaly / multi-thread / firecrawl ...  ← 同期黃金期
─────────── 黃金期分水嶺 ───────────
P51-P62  逐漸忘了部署，紀錄欄位消失
P63+    完全忘記，新 skill 從未走全域部署流程
```

**這是 G5-2「規則退化」+ X3「時間敏感性」的活生生標本**：規則沒消失（仍寫在 GEMINI.md / TASK_HISTORY P37-P50），但**執行行為退化**。P71 不只解現症，要根治退化機制。

### B3. 雙端版本漂移

| 觀察 | 數據 |
|---|---|
| Gemini 端 7 個 skill 建立時間 | 2026-04-17 ~ 04-19（每個對應 P43-P50 收官）|
| Claude 端 7 個 skill 建立時間 | **全部同一秒 2026-04-25 20:52:30**（一次性批次回流）|
| Diff 行數 | 66 ~ 536 行（嚴重不同步）|

→ 之後再無同步。Claude 端 Bytes 較多 + 時間較新，但**從未在 Claude 端服役過**（Gemini 端才是實戰版本）。

---

## 🏛️ 17 層稽核表（Patch-1：>10 檔 → 全層必填）

### S 級必過 4 層

| # | 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | **Code** | lint_skill_registry.py / deploy_skills.py / smart_task_router 啟用 | 跨平台路徑（Windows ~ vs *nix）| pathlib + os.path.expanduser；CI 跑 Ubuntu 同時驗證 |
| 2 | **Logic** | description schema 自動觸發匹配 / diff 三方合併邏輯 | smart-task-router 誤判導致錯啟 skill | 信心閾值 + 主公否決快捷鍵 |
| 4 | **Testing** | 每個 skill 必有 test_skill.py（純孤兒 skill 補上）/ lint 自身有 test | lint 規則太嚴擋住正常 commit | 漸進式上線（先 warning 後 error）|
| 10 | **Security** | deploy_skills.py 寫入跨目錄 / Gemini brain dir 讀寫 | 誤刪主公 Gemini 全域 skill | dry-run 預設、--force 才實寫、自動 backup |

### A 級必過 7 層

| # | 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 3 | **Architecture** | 三層架構（L1 純 Python / L2 路由 / L3 雙家入口）+ shared/project 二級分類 | 過度抽象增加複雜度 | shared 倉庫獨立，AOV-only 仍在專案 |
| 5 | **Data** | REGISTRY.json schema / SKILL.md frontmatter schema | schema 太嚴前期阻塞 | 漸進，先空欄位 placeholder 再補 |
| 6 | **Observability** | SKILL_HEALTH.md 自動生成 dashboard / lint log | 假綠燈（lint 過但實際壞）| CI dry-run 真執行而非僅 schema 驗證 |
| 7 | **Resilience** | self-contained SKILL.md（IDE 全壞還能跑）| 增加每份檔 size | 接受，永久性 ROI 高 |
| 13 | **Maintainability** | shared/ 跨專案倉庫獨立 git | 兩個 repo 增管理成本 | submodule 或 subtree 自動同步 |
| 14 | **Documentation** | SKILL_INVENTORY.md / SKILL_HEALTH.md / 各 skill SKILL.md 升級 | 文件量爆增 | 模板化、自動生成 |
| 15 | **Process** | STR9 + PHASE_TEMPLATE 加 Skill Exit Criteria + pre-commit + CI | AI/主公仍可繞過 | 規則寫在 CLAUDE.md / GEMINI.md 雙寫 |

### B 級觸發層 6 層

| # | 層 | 觸發 | 採用優化項 |
|---|---|---|---|
| 8 | **Performance** | smart-task-router 每 prompt 執行匹配 → token 成本 | registry.json 快取 + 早退（match 後不繼續）|
| 9 | **UX** | 觸到 `.claude/commands/` + `SKILL.md` 觸發描述 → 主公讀到要懂 | example_invocations 用主公真實口語 |
| 11 | **DevOps** | 觸到 `.github/workflows/` → 部署層 | CI workflow 加 skill 驗證 step |
| 12 | **Cost** | smart-task-router 每次匹配計算 → 累積 token 成本 | 純 Python 規則（不呼叫 LLM）|
| 16 | **Privacy** | `instagram-facebook-dcard-platform-copywriter` TOS | SKILL.md 警語 + 主公手動觸發 only |
| 17 | **i18n** | 中英雙語 description / when_to_use | trigger_keywords 同時收中英 |

### META 6 條檢查

| # | 條款 | 檢核 |
|---|---|---|
| META1 | S/A/B 分級 | ✅ 上表全填 |
| META2 | 強制填表 | ✅ 無空格 |
| META3 | 影響半徑 | **重大 Phase（>10 檔）→ 全層必填** |
| META4 | 風險加權 | 最高為 P71.5 diff 裁決誤判（主公需求拍板）= 4，未達 5，不暫停 |
| META5 | 層級互鎖 | 動 Logic（smart-router）必動 Testing（test_router.py）✅；動 Architecture 必動 Documentation（SKILL_INVENTORY）✅ |
| META6 | 稽核版本鎖 | 不引入新層，沿用 v3.1 |

---

## 🌟 10 優化點完整論證

### S 級：必納入 P71，缺一不可

#### S1 — Description Schema 強制 4 欄（自動觸發引擎）

**問題**：目前多數 SKILL.md 只有一句 description，LLM 看不出何時該觸發。

**解法**：強制 frontmatter schema：

```yaml
---
name: <skill-name>
type: executable | data | prompt | pipeline
status: in-use | candidate | archived
version: x.y.z
description: 一句話定位（≤30 字）

when_to_use:                      # ★ LLM 自動判斷依據
  - 觸發情境 1（具體場景）
  - 觸發情境 2

when_NOT_to_use:                  # ★ 反例避免誤觸
  - 屬於 skill X 的範圍
  - 太簡單不必動用

trigger_keywords:                 # ★ 強匹配信號
  - [中文關鍵字 1, English keyword 1, ...]

example_invocations:              # ★ few-shot 範例
  - input: "幫我看過去 7 天芽芽聲量"
    skill: history-trend-query
  - input: "把這段話改成三平台文案"
    skill: instagram-facebook-dcard-platform-copywriter

entry_points:
  cli:           "python -m skills.<name>"
  import:        "skills.<name>"
  prompt_paste:  "adapters/prompt_paste/<name>.md"
  claude_slash:  "/<slash>"  # 可選

deployed_to:
  - claude-project
  - gemini-global

requires:
  python: ">=3.10"
  packages: [httpx, pydantic, ...]

depends_on:                       # 可選
  - <other-skill-name>

last_used: 2026-05-08
---
```

**效益**：LLM 開局掃描 registry.json 即可自動匹配 → 主公口語觸發無需點名。

#### S2 — CLAUDE.md / GEMINI.md 加「自動觸發指引」

兩家全域指令檔開頭加同一條：

```
## 🤖 Skill 自動觸發協議

對話開始時，掃描 `<proj>/skills/registry.json` 中所有 skill 的
`when_to_use` / `trigger_keywords`，比對使用者輸入。
匹配到時：
  1. 主動執行該 skill
  2. 回覆首段標 `[<skill-name> 已啟動]`
  3. 無需主公點名 / 無需 slash 觸發

衝突排序：
  - 多 skill 匹配 → 用 smart-task-router 信心分數最高者
  - 信心 < 0.7 → 詢問主公二選一
  - 信心 ≥ 0.9 → 直接執行
```

**效益**：每新視窗 LLM 開局立即就位 → 規則寫進指令檔不靠記憶。

#### S3 — SKILL.md 自包含（永久保險）

**最壞情境**：Antigravity 停服、Claude Code 改版、主公換 IDE。**單獨 `skills/<name>/` 目錄丟給任何 LLM，必須能跑起來**。

→ 強制 self-contained：
- 完整輸入 schema（不引用外部）
- 完整輸出 schema
- 依賴清單 + 版本鎖
- 純 CLI 執行命令（`python -m skills.<name> --input '{}'`）
- **不引用外部 CLAUDE.md / GEMINI.md** → 該抽的條款抄一份進 SKILL.md

**效益**：核災級保險，任何時代都活著。

---

### A 級：強烈建議納入 P71

#### A1 — Shared / Project 二級分類

```
~/skills-shared/                  ← 獨立 git repo（永久備份）
├── ai-news-radar/                ← 跨專案
├── html-markdown-distiller/
├── instagram-facebook-dcard-platform-copywriter/
├── semantic-cache-shield/
├── cot-prompt-compactor/
├── nl-to-prompt-structurer/
├── session-handoff-packager/
├── ui-ux-pro-max/
└── smart-task-router/

D:/AOV/skills/                    ← 本專案
├── history-trend-query/          ← 專案專屬（依賴 AOV 資料）
├── hallucination-judge/          ← 專案專屬（hero whitelist）
├── api-quota-guardian/           ← 跨專案？待主公裁決
└── hot-deployer/                 ← AOV 專屬（GHA 部署）
```

**換電腦 = `git clone ~/skills-shared` + 各專案 clone 各自 repo**。永久備份解決。

#### A2 — 救活 `smart-task-router`（之前是孤兒）

它的設計目的正是路由引擎核心：
> 「根據輸入自然語言，自動比對關鍵字判斷最適合的 skill，回傳路由決策與信心等級」

升級為 L2 路由層核心，搭配 S1 schema 工作。

#### A3 — Pre-commit hook + GitHub Action 雙保險

```
本機 pre-commit (.git/hooks/pre-commit):
  └─ python scripts/lint_skill_registry.py
     ├─ frontmatter schema 驗證
     ├─ entry_points 真的可呼叫
     ├─ Claude/Gemini 雙端 diff 警示
     └─ 90 天無 last_used → 警告

CI (.github/workflows/skill_lint.yml):
  ├─ 同上 lint
  ├─ 跑每個 skill 的 test_skill.py
  ├─ deploy_skills.py dry-run
  └─ 失敗 = block PR
```

**規則不靠人記得**。

#### A4 — `docs/SKILL_HEALTH.md` 自動生成 Dashboard

每次 push 自動更新：

```markdown
| Skill | Type | Claude | Gemini | Last Used | Tests | Health |
|---|---|---|---|---|---|---|
| history-trend-query | pipeline | ✅ in-use | ⚠️ ND | 5/8 | 75/75 | 🟢 |
| ai-news-radar | pipeline | ⚠️ stale | ✅ in-use | 4/25 | 0/0 | 🟡 |

> Health 圖例：🟢 雙端同步 + 有測試 + 30 天內用過
>             🟡 單端 / 缺測試 / 30-90 天未用
>             🔴 雙端漂移 / 90+ 天未用 / 測試 fail
```

**主公一眼看出誰生病**。

---

### B 級：P71 後期或 P72

#### B1 — Skill 版本鎖（Semantic Versioning）

每個 SKILL.md 必有 `version: x.y.z`，registry.json 鎖版本。
- patch (x.y.Z)：bug 修，自動同步
- minor (x.Y.z)：新功能，主公確認後同步
- major (X.y.z)：破壞性變更，必須先寫 migration guide

防「skill 改了但呼叫方沒改」隱性破裂。

#### B2 — 依賴圖（registry.json 加 `depends_on`）

刪 / 改某 skill 前 lint 自動檢查反向依賴，避免連鎖斷裂。

#### B3 — Permanent Bundle（年度核災備份）

每 N 個 Phase（或每年）打包整個 `skills/` 為單檔：
```
skill_bundle_v2026-Q2.tar.gz
└── README_PORTABLE.md  ← 任何 LLM 讀完即可在純檔案系統上跑
```
上傳 GitHub Release。**所有 IDE / 工具消失後，這個 bundle 還活著**。

---

## 📋 12 階段詳細動作

| # | 階段 | 主要動作 | 影響檔案數 | 對應優化點 | 預估視窗 |
|---|---|---|---|---|---|
| **P71.0** | 盤點 | `docs/SKILL_INVENTORY.md`（雙端狀態 + diff + 推薦動作） | +1 | — | 0.5 |
| **P71.1** | 治理層 | `skills/registry.json` + `lint_skill_registry.py` + STR9 寫 PHASE_TEMPLATE | +3 ~5 | S1, A3 | 1 |
| **P71.2** | 自動觸發引擎 | SKILL.md schema 升級到 4 欄 + CLAUDE/GEMINI.md 觸發協議 | 4-7 個 SKILL.md + 2 全域 + 1 專案 | **S1, S2** | 1 |
| **P71.3** | 自包含化 | 4+7 個在用/Gemini-only skill 補完 self-contained 元素 | 11 個 SKILL.md | **S3** | 1 |
| **P71.4** | 同步工具 | `scripts/deploy_skills.py` + pre-commit + CI workflow | +2 ~ 3 | A3 | 0.5 |
| **P71.5** | 二級分類 | shared/project 拆分 + `~/skills-shared/` 倉庫建立 | mv 7-9 個目錄 + 新 repo | **A1** | 1 |
| **P71.6** | 路由引擎 | smart-task-router 救活 + 接 registry + S1 schema | +scripts | **A2** | 0.5 |
| **P71.7** | Dashboard | `docs/SKILL_HEALTH.md` 自動生成 + GHA 整合 | +1 + workflow 修 | A4 | 0.5 |
| **P71.8** | 7 個 diff 裁決 | 主公逐 skill 看 diff 決定主版本（C 方案）| 7 個 SKILL.md（已存在）| — | 1 |
| **P71.9** | 8 個孤兒處置 | 主公點名要的 → schema 升級；其他 → `_archive/` | 8 個目錄 | — | 0.5 |
| **P71.10** | Postmortem | `docs/postmortems/P71_skill_deployment_decay.md` + R-009 | +1 | — | 0.3 |
| **P71.11** | B 級延伸 | 版本鎖 / 依賴圖 / Permanent Bundle | +工具 + 文件 | B1, B2, B3 | 1 |

**總計約 8 個視窗工作量**，可拆 P71 主體（P71.0-P71.10）+ P72（P71.11 移出）。

### 動工順序與依賴

```
P71.0 (盤點) ─→ 啟動所有後續階段所需的事實基礎
   ↓
P71.1 (治理) ←── 必先於所有 schema 升級
   ↓
P71.2 (觸發引擎) ─→ 依賴 P71.1 的 registry schema
   ↓
P71.3 (自包含) ─→ 依賴 P71.2 的 schema 完成
   ↓
P71.4 (同步工具) ──┬─→ 跨平台寫入需 P71.3 完成
P71.5 (二級分類) ──┘
   ↓
P71.6 (路由引擎) ─→ 依賴 P71.2 的 schema + P71.4 的 deploy 工具
   ↓
P71.7 (Dashboard) ─→ 依賴 P71.6 的 health metric
   ↓
P71.8 (diff 裁決) ←─ 並行：主公人工裁決，可在 P71.4 完成後任意時機跑
P71.9 (孤兒處置)  ←─ 並行：與 P71.8 不衝突
   ↓
P71.10 (Postmortem) ─→ 全部完成後寫
   ↓
P71.11 (B 級延伸) ─→ 可移出為 P72
```

---

## 🎯 P71.5 Diff 裁決協議（C 方案細化）

7 個 Gemini-only skill 的 Claude 端比 Gemini 端新 6-8 天 + 多 100~400 bytes、diff 達 66-536 行。**逐 skill 主公人工裁決**：

### 裁決流程（每個 skill 重複）

```
Step 1: 我自動產出 diff 報告（claude_vs_gemini.diff）
        + 摘要兩端關鍵差異（章節 / 條款新增 / 修改）

Step 2: 主公看 diff，三選一：
        (a) 取 Claude 為主版本（覆蓋 Gemini 端）
        (b) 取 Gemini 為主版本（覆蓋 Claude 端）
        (c) 手動合併（主公點出哪些章節要保留 / 改寫）

Step 3: 我執行裁決，更新雙端 + 寫入 registry.json `last_audit`
```

### 裁決順序（依重要性）

```
1. ai-news-radar          (diff 536 行 — 最大)
2. instagram-facebook... (diff 388 行)
3. html-markdown-distiller (diff 92)
4. semantic-cache-shield (diff 90)
5. trend-anomaly-detector (diff 70)
6. firecrawl-dynamic-breacher (diff 68)
7. multi-thread-synthesizer (diff 64)
```

預估 7 個 skill 全裁決約 1 個視窗（每個 5-10 分鐘）。

---

## 📦 影響半徑

| 檔案類型 | 動作 | 預估數量 |
|---|---|---|
| **新增** `docs/` | SKILL_INVENTORY.md / SKILL_HEALTH.md / P71_PLAN.md / postmortem | 4 |
| **新增** `scripts/` | lint_skill_registry.py / deploy_skills.py | 2 |
| **新增** `skills/` | registry.json / __init__.py / loader.py | 3 |
| **新增** `adapters/prompt_paste/` | 11 個通用 paste prompt | 11 |
| **新增** `.github/workflows/` | skill_lint.yml | 1 |
| **新增** repo | `~/skills-shared/` 獨立 git | 1 repo |
| **修改** `<proj>/skills/<name>/SKILL.md` | 11 個 in-use/Gemini-only skill schema 升級 | 11 |
| **修改** `~/.claude/CLAUDE.md` + `~/.gemini/GEMINI.md` | 觸發協議 | 2 |
| **修改** `<proj>/CLAUDE.md` + 新增 `<proj>/GEMINI.md` | 專案級觸發協議 | 2 |
| **修改** `docs/PHASE_TEMPLATE.md` | STR9 加入 | 1 |
| **修改** `docs/MODEL_SELECTION_GUIDE.md` | 三檔同步協議擴展為 N 檔 | 1 |
| **修改** `docs/RISK_REGISTRY.md` | R-009 / R-010 / R-011 | 1 |
| **修改** `docs/RULES_REGISTRY.md` | STR9 註冊 | 1 |
| **移動** `.agent/skills/<name>/` → `skills/<name>/` | 目錄遷移 | 20 個目錄 |
| **歸檔** `.agent/skills/_archive/<name>/` | 確定廢棄者 | 0 ~ 5 個 |
| **總計** | — | **約 50-70 個檔案異動 + 1 個新 repo** |

**重大 Phase（≫10 檔）→ Patch-1 全層稽核已完整。**

---

## ⚠️ 風險登記

| ID | 風險 | 機率 | 影響 | 加權 | 緩解 |
|---|---|---|---|---|---|
| **R-P71-1** | deploy_skills.py 誤刪 Gemini 全域 skill | 中 | 高 | 4 | dry-run 預設、--force 才實寫、自動 backup 至 `~/.gemini/.skill_backups/` |
| **R-P71-2** | smart-task-router 誤觸發 skill | 中 | 中 | 3 | 信心閾值 0.7、`<0.9` 詢問主公確認 |
| **R-P71-3** | lint 規則太嚴擋住正常 commit | 中 | 低 | 2 | 漸進式（先 warning 後 error），允許 `--allow-skip` 但記錄 |
| **R-P71-4** | shared/ 倉庫與專案版本漂移 | 中 | 中 | 3 | git submodule + auto sync hook |
| **R-P71-5** | SKILL.md schema 過嚴前期阻塞 | 低 | 中 | 2 | 強制欄位用 placeholder 起步，逐 Phase 補完 |
| **R-P71-6** | P71.5 diff 裁決遺失歷史改進 | 低 | 高 | 3 | 裁決前 git tag pre-P71.5，可隨時還原 |
| **R-P71-7** | CLAUDE.md / GEMINI.md 雙寫漂移 | 中 | 中 | 3 | sync_global_rules.py 工具 + 三檔同步協議擴展 |
| **R-P71-8** | self-contained SKILL.md 文件爆增 | 高 | 低 | 2 | 接受，永久 ROI 高；自動生成減人工 |
| **R-P71-9** | smart-task-router 每 prompt 都跑 → token 成本 | 中 | 低 | 2 | 純 Python 規則匹配（不呼叫 LLM）+ registry 快取 |
| **R-P71-10** | Antigravity 後續改版改變 skill 路徑 | 低 | 高 | 3 | self-contained 已預防、shared/ 倉庫獨立保險 |

**最高加權 = 4 < 5，META4 不暫停請示主公。** 但 R-P71-1 緊密監控（涉外部目錄寫入）。

---

## ✅ Exit Criteria（P71 退出條件）

P71 整體收官需全部滿足：

1. ✅ `docs/SKILL_INVENTORY.md` 列出每個 skill 的雙端狀態 + 處置決定
2. ✅ `skills/registry.json` 完整登記所有 in-use + candidate skill
3. ✅ 11 個 in-use/Gemini-only skill SKILL.md 通過 schema lint
4. ✅ 11 個 skill 有對應 `adapters/prompt_paste/<name>.md` 通用版
5. ✅ `scripts/deploy_skills.py` 可正確雙向同步（dry-run + 實寫測試過）
6. ✅ pre-commit hook + CI workflow 上線並通過
7. ✅ `docs/SKILL_HEALTH.md` 自動生成且每日更新
8. ✅ `~/skills-shared/` 獨立 git repo 建立 + 7-9 個跨專案 skill 入駐
9. ✅ smart-task-router 接 registry，能對 5+ 種典型輸入正確路由
10. ✅ CLAUDE.md / GEMINI.md 觸發協議寫入並同步
11. ✅ STR9 寫入 `docs/PHASE_TEMPLATE.md`
12. ✅ 7 個 diff 裁決完畢，雙端版本一致
13. ✅ 8 個 Claude-only 孤兒處置完畢（升級 / 歸檔）
14. ✅ Postmortem 寫完，R-009 入 RISK_REGISTRY
15. ✅ 全套測試零回歸（含新增的 lint 測試）

---

## 🎓 跨 Phase 學習（P50 後規則退化的根因）

### 為何 P43-P50「全域部署」傳統消失？

**假說 1：認知負擔超載**
P43-P50 是密集 skill 開發期，每個 Phase 規模小、流程單一（寫 skill → 測試 → 部署）。P51 後 Phase 範圍擴大（涉及多模組、跨檔案），「全域部署」這條 SOP 被擠出工作記憶。

**假說 2：缺乏機械化阻擋**
全域部署規則寫在 GEMINI.md / TASK_HISTORY 但**沒有 lint / hook / CI 阻擋**。AI 和主公都可繞過，沒人記得 = 規則消失。

**假說 3：規則隱性繼承斷裂**
P43-P50 同期開發，AI 在連續視窗內保有「這 Phase 要部署到全域」的記憶。P51 換主題後，新視窗開局只讀到 CLAUDE.md / GEMINI.md，但**指令檔沒明示「skill 收官必部署」**，所以 AI 忘了。

### P71 對症下藥

| 假說 | 對應對策 |
|---|---|
| 認知負擔超載 | A3（pre-commit + CI 自動執行）→ 不靠記憶 |
| 缺乏機械化阻擋 | A3 + STR9 → 違規不能 commit |
| 規則隱性繼承斷裂 | S2（CLAUDE.md / GEMINI.md 寫觸發協議）→ 每視窗開局必讀 |

### 通則化（給 G6 失誤學）

**通則**：「**寫在指令檔但沒機械化阻擋的規則，半衰期約 8-10 個 Phase**」

→ 適用所有專案：rule-as-code 必須有 enforcement-as-code 配套。

---

## 🚦 動工執行協議

### 視窗 1（本視窗已收尾，下一視窗開局）

```
1. 開新視窗，鐵律 v0.4 啟動
2. 讀 NEXT_SESSION_HANDOFF.md → 跳到 P71_PLAN.md
3. 跑 P71.0（盤點）：寫 SKILL_INVENTORY.md
4. commit + push（push 必問）
```

### 視窗 2-3（治理層 + 觸發引擎）

```
跑 P71.1（治理層）→ P71.2（觸發引擎）→ P71.3（自包含化）
每階段獨立 commit + push 必問
```

### 視窗 4-5（同步工具 + 二級分類）

```
跑 P71.4（同步工具）→ P71.5（二級分類）→ P71.6（路由引擎）
P71.5 涉及移動目錄與建新 repo，主公需確認 ~/skills-shared 路徑
```

### 視窗 6（Dashboard + 裁決）

```
跑 P71.7（Dashboard）→ P71.8（7 個 diff 裁決，主公人工）
```

### 視窗 7（收官）

```
跑 P71.9（孤兒處置）→ P71.10（Postmortem）
P71.11 移出為 P72 或同視窗收尾（視 token 餘量）
```

---

## 📌 動工前主公須再拍板的小決策

| # | 決策 | 預設答案（若未拍板） |
|---|---|---|
| D1 | `~/skills-shared/` 真實路徑（C: 還 D:）| `D:/skills-shared/`（與 AOV 同碟，避免跨碟同步問題）|
| D2 | shared/ 是新建 repo 還是 GitHub 上傳 | 兩階段：先本機 git init，後上 GitHub |
| D3 | smart-task-router 信心閾值 | 預設 0.7 詢問、0.9 直接執行；可微調 |
| D4 | pre-commit hook 違規 = block 還是 warning | 起始 warning，2 週後升 block |
| D5 | 8 個孤兒中哪些保留 | 我推薦：daily-diff-radar / rich-push-formatter / session-handoff-packager / waterfall-search-chain / api-quota-guardian（已用）；其他 3 個歸檔 |
| D6 | 是否在本機建 `<proj>/.gemini/` 專案目錄 | 是（即使 Antigravity 沒明確支援，未來可能加入）|

---

## 📎 附錄 A — 20 個 skill 當前狀態快照

| Skill | Type | Claude | Gemini | Tests | 處置 |
|---|---|---|---|---|---|
| api-quota-guardian | exec | ✅ in-use | ❓ ND | ✅ | 雙端部署、registry 註冊 |
| hallucination-judge | data | ✅ in-use | ❓ ND | ✅ | 雙端部署、registry 註冊 |
| history-trend-query | pipe | ✅ in-use + /trend | ❓ ND | ✅✅✅✅ | 雙端部署、registry 註冊（AOV 專屬留專案）|
| hot-deployer | exec | ✅ in-use (GHA) | ❓ ND | ✅ | AOV 專屬（GHA 部署）、registry 註冊 |
| nl-to-prompt-structurer | pipe | 🟡 /prompt only | ❓ ND | ✅ | 雙端部署、registry 註冊 |
| ai-news-radar | pipe | ⚠️ stale | ✅ in-use | ❌ | **diff 裁決（536 行）** |
| firecrawl-dynamic-breacher | exec | ⚠️ stale | ✅ in-use | ✅ | **diff 裁決（68 行）** |
| html-markdown-distiller | exec | ⚠️ stale | ✅ in-use | ✅ | **diff 裁決（92 行）** |
| instagram-facebook-dcard-platform-copywriter | prompt | ⚠️ stale | ✅ in-use | ❌ | **diff 裁決（388 行）** |
| multi-thread-synthesizer | exec | ⚠️ stale | ✅ in-use | ✅ | **diff 裁決（64 行）** |
| semantic-cache-shield | exec | ⚠️ stale | ✅ in-use | ✅ | **diff 裁決（90 行）** |
| trend-anomaly-detector | exec | ⚠️ stale | ✅ in-use | ✅ | **diff 裁決（70 行）** |
| auto-proxy-evader | exec | ❌ orphan | ❌ orphan | ✅ | 主公裁決（與三胞胎合併？）|
| cot-prompt-compactor | prompt | ❌ orphan | ❌ orphan | ✅ | 主公裁決（被 nl-to-prompt 取代？）|
| daily-diff-radar | exec | ❌ orphan | ❌ orphan | ✅ | **推薦保留**：補 slash + 接報告流程 |
| rich-push-formatter | exec | ❌ orphan | ❌ orphan | ✅ | **推薦保留**：補 slash + LINE bot 整合 |
| semantic-cache-shield | exec | （見上）| | | |
| session-handoff-packager | pipe | ❌ orphan | ❌ orphan | ✅ | **推薦保留**：補 slash 對應 Gemini handoff |
| smart-task-router | exec | ❌ orphan | ❌ orphan | ✅ | **救活**：作為 L2 路由引擎 |
| ui-ux-pro-max | data | ❌ orphan | ❌ orphan | ❌ | 主公裁決（未來改報告版面用）|
| waterfall-search-chain | exec | ❌ orphan | ❌ orphan | ✅ | 主公裁決（與 api-quota-guardian 配對使用）|

**圖例**：✅ 對等部署 / ⚠️ 漂移 / ❌ 無 / ❓ 未確認 / ND not deployed

---

## 📎 附錄 B — 動工前必讀的文件鏈

新視窗開局：

```
1. NEXT_SESSION_HANDOFF.md（指引到本檔）
2. docs/P71_PLAN.md（本檔，完整計畫）
3. docs/OPTIMIZATION_FRAMEWORK.md v3.1（17 層 + 6 META + 8 STR + 24 治理 + 4 跨切面 + 3 Patch）
4. docs/PHASE_TEMPLATE.md（Phase 樣板）
5. CLAUDE.md / GEMINI.md（全域 + 專案）
6. memory/MEMORY.md（記憶索引）
```

---

## 📎 附錄 C — 完成後的「不朽性」自證

P71 全收官後，模擬以下情境驗證 G1（永久不滅）：

| 情境 | 期望結果 |
|---|---|
| 換新電腦：`git clone <主專案> + git clone ~/skills-shared` | 所有 skill 立即可用 |
| 主公某天 Antigravity 停用 | `python -m skills.<name>` 仍可純 CLI 跑 |
| 主公換用 GPT / 其他 LLM | `adapters/prompt_paste/<name>.md` 直接 paste 可用 |
| 主公不小心刪除 `.claude/` 整個目錄 | skills/ 完整無損，重新 deploy 即可 |
| 主公 5 年後回來看 | SKILL.md self-contained 可被未來模型直接讀懂 |

驗證 G2（自動觸發）：

| 情境 | 期望結果 |
|---|---|
| 主公新視窗說「幫我看芽芽聲量」 | LLM 自動觸發 `/trend hero 芽芽`，無需點名 |
| 主公說「把這段話改成 IG 貼文」 | LLM 自動觸發 instagram-facebook-dcard-platform-copywriter |
| 主公說「打包這次對話給下個視窗」 | LLM 自動觸發 session-handoff-packager |
| 主公說「分析昨天和今天的差異」 | LLM 自動觸發 daily-diff-radar |

---

## 🔚 結語

P71 不是修復幾個孤兒 skill，是**建立 skill 的不朽性架構**——讓 skill 跨 IDE / 跨模型 / 跨時代不失效，且能被 LLM 自動發現、自動觸發。

這個架構的最終測驗是：**P71 收官 5 年後，主公換了電腦、換了 IDE、換了 LLM 模型，這些 skill 仍能完整運作**。

主公核准動工，新視窗從 P71.0 起跑。

---

*計畫書版本：v1.0 / 2026-05-08 / Opus 4.7 起草*
