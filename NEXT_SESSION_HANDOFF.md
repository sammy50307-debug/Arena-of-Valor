<!-- ACTIVE_BOOTSTRAP_START -->
# ACTIVE_BOOTSTRAP — READ THIS FIRST

> 本區塊是新視窗唯一當前指令來源。`ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION` 以下只作歷史參考，不可用來決定下一步。

| 欄位 | 內容 |
|---|---|
| **Status** | ACTIVE |
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P90（Budget Ledger / Cooldown / DRAFT） |
| **Current Step** | P89 runtime 已完成本地驗證；下一步建立/凍結 P90 計畫，未核准前不得改 budget runtime |
| **Mode** | DRAFT |
| **Latest Verified Commit** | `HEAD`（P89 runtime commit 建立後即為最新本地真相；若本欄與 repo 狀態不一致，以 `git log -1 --oneline` 為準） |
| **Updated At** | 2026-05-21 Asia/Taipei |

## Required Minimal Reads

1. 本區塊：`ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`（需要短版狀態時）
3. `docs/PHASE_89_PLAN.md`（需要確認剛收官證據時）

## Current Source Of Truth

| 層級 | 檔案 | 用途 |
|---|---|---|
| L1 | `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP` | 唯一開局入口 |
| L2 | `docs/ACTIVE_OPERATION.md` | 當前作戰短版狀態 |
| L3 | 尚待建立 `docs/PHASE_90_PLAN.md` | P90 Budget Ledger / Cooldown 計畫入口 |
| L3-prev | `docs/PHASE_89_PLAN.md` | P89 Quality Tier / Promotion Gate 收官證據 |
| L4 | `docs/RISK_REGISTRY.md` 的 R-016 | R-016 仍 Open 的風險真相 |

## Six Anti-Drift Fields

| 欄位 | 內容 |
|---|---|
| **Current Phase** | P90（DRAFT） |
| **Current Step** | 建立/凍結 `docs/PHASE_90_PLAN.md`；未凍結且未核准前不可改 budget runtime |
| **Allowed Files** | DRAFT 階段只可動 `docs/PHASE_90_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`, `TASK_HISTORY.md`；runtime 核准後才可依 P90 計畫動 code |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不做 P91-P95 runtime；不把 R-016 標記 Closed；不 git push，除非主公明確確認 |
| **Exit Criteria** | P89 runtime 已完成：quality tier contract / promotion gate / metadata / health / doctor / tests；P90 plan 需先完成 17 層稽核與 M1/M2 後才能 runtime |
| **Resume Rule** | 新視窗讀本區塊；若要動 P90，先建立/凍結 `docs/PHASE_90_PLAN.md`，不得直接改 budget runtime |

## Required Verification Commands

```powershell
git status -sb
git diff --check
py scripts\lint_phase_plan.py docs\PHASE_89_PLAN.md
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Do Not

- 不要使用本檔 archive 舊段落的「下個視窗」文字決定下一步。
- 不要全讀 `TASK_HISTORY.md`；需要歷史時只用 anchor search。
- 不要把 P89 CLOSED 解讀成 R-016 CLOSED；R-016 仍 Open，後續要走 P90-P95。
- 不要回到「加 OpenAI paid fallback」當主線；主公已明確不想多花 OpenAI API 錢。
- 不要自動接 Groq / Cloudflare / GitHub Models；免費 provider 只列 P93 disabled-by-default 候選。
- 不要把 R-016 標記 Closed；P89 是 quality gate 子問題收官，不是 R-016 closeout。
- 不要直接改 P90 runtime code；P90 目前需先建立/凍結計畫，並等主公核准才能動工。
- 不要 git push，除非主公明確確認。

<!-- ACTIVE_BOOTSTRAP_END -->

<!-- ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION -->

# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-16（**P76 RISK_REGISTRY / HANDOFF 狀態清理已收官**）
- **狀態**：✅ P72.0~P72.5 全收官 + AGENTS.md 已上線 + **PHASE_TEMPLATE v1.2 已寫入** + **P73 OpenAI/Codex 模型選擇指引已更新** + ✅ **P74 關閉 R-015** + ✅ **P70.2 每日健康檢查已接入 GHA** + ✅ **P75 關閉 R-014** + ✅ **P70.4 OpenAI fallback 已落地** + ✅ **P70.6 cache retention 已落地** + ✅ **P76 狀態帳本清理**；最新已推 commit 為 `614dc13`
- **下個視窗第一動作**：讀本檔頂部 → `git status -sb` → 若看到 P76 本地 commit ahead，先詢問主公是否 push；目前主線待動工清單已清空

---

## 🚦 新視窗開局指南（2026-05-16）

### 目前物理狀態

- 最新已推 commit：`614dc13 feat: 補上 llm cache LRU`
- 推送狀態：`main -> origin/main` 已完成到 `614dc13`；P76 若已本地 commit，仍需主公確認後才能 push
- tracked 變更：P76 收官後理想狀態應只有本地 ahead commit，無 tracked dirty；若有 tracked dirty，先查來源
- untracked 檔案：仍有 `.agents/skills/source-command-*`、`.claude/.rule_decay_last_run`、`.codex/`、`backups/`、`data/reports/*.html`、`scratch/` 等既有未追蹤檔；本視窗沒有納入 commit，下一窗不要誤 stage

### 本視窗最新完成事項

1. **P76 / RISK_REGISTRY + HANDOFF 狀態清理**
   - R-007 / R-008 從 Open 區移至 Closed 區；LINE WebView 長期觀察仍由 R-004 承接
   - handoff 頂部最新已推 commit 修正為 `614dc13`
   - 清除「P75/P70.4/P70.6 本地 commits 待 push」的過期描述
2. **P70.6 / llm_cache LRU / TTL**
   - `CacheManager` schema 升 v3，v2 load 自動補 `last_accessed`
   - 新增 `CACHE_MAX_ENTRIES`（預設 500），`get()` 命中更新 last_accessed，`set()` / `save()` / `_load()` 執行 LRU eviction
   - 明確未 stage `data/llm_cache.json`；只改程式與測試
   - 驗證：`tests/test_cache_manager.py` 12 passed；全套 `py -m pytest -q` → 126 passed
3. **P70.4 / OpenAI fallback**
   - 新增 `analyzer/fallback_llm_client.py`：Gemini primary / OpenAI secondary wrapper
   - 升級 `analyzer/llm_client.py`：支援 `cache_manager`、`response_schema`、Gemini uppercase schema → OpenAI lowercase JSON Schema
   - `SentimentAnalyzer()` 預設改用 fallback wrapper；OpenAI key 未設時維持既有 showcase_forced 路徑
   - 驗證：`tests/test_openai_fallback.py` 5 passed；全套 `py -m pytest -q` → 124 passed
4. **P75 / R-014 歷史 Phase blindspot 回填**
   - 新增 4 份 M4 blindspot：P63 / P64 / P69 / P70.3
   - 新增 B-011~B-022 共 12 條通則化盲點
   - 驗證：`py scripts/m4_track_blindspots.py --status` → 缺 blindspot 0；`py scripts/cross_phase_review.py` 可讀到新增規則
   - RISK_REGISTRY：R-014 已移至 Closed
5. **P74 / R-015 test_dynamic_focus 事件迴圈隔離修復**
   - 根因：`tests/test_dynamic_focus.py` 三個 async case 使用 `asyncio.get_event_loop().run_until_complete(...)`，全套測試前序 case 使 current event loop 不存在，導致 `RuntimeError: There is no current event loop in thread 'MainThread'`
   - 修法：三處改為 `asyncio.run(...)`
   - 驗證：`py -m pytest tests/test_dynamic_focus.py -q` → 5 passed；`py -m pytest -q` → 112 passed
   - RISK_REGISTRY：R-015 已移至 Closed
6. **P70.2 / GHA 每日健康巡檢與無報告根因排查**
   - S0 證據：5/7、5/8 canonical 報告目前存在，但由 `a2a6d39`（P70.3，2026-05-08 21:27 +08）後補；當前 `index.html` 主按鈕仍指 `aov_report_2026-05-06.html`
   - 新增：`scripts/check_daily_report_health.py`，檢查 canonical report、metadata mode、landing main link、可選 git clean
   - 測試：`tests/test_daily_report_health.py` 7 cases；全套 `py -m pytest -q` → 119 passed
   - Workflow：`.github/workflows/daily_report.yml` fallback push 後新增 `Daily Report Health Check`

### 前一視窗完成事項

1. **P72.5 補遺**：`docs/PHASE_TEMPLATE.md` 升 v1.2
   - X4-A 升級為「世界頂尖駭客 / 紅隊攻擊者」
   - 新增 X4-K「使用者端審查官 / Patric 型人格」
   - 新增 M1.5「八人格顧問團觸發檢查」
   - M4 驗收：`py scripts/m4_track_blindspots.py --sync-rules` → 9/10 規則涵蓋；B-007 留待 CLAUDE.md / 鐵律 v0.5
2. **P73**：`docs/MODEL_SELECTION_GUIDE.md` 升 v1.2
   - 新增 OpenAI / ChatGPT / Codex 分支
   - 核心口訣：想清楚用 GPT-5.5，動工省錢用 GPT-5.3-Codex，小事用 Mini，卡住升高/超高
   - 新增凍結計畫書：`docs/PHASE_73_PLAN.md`

### 新視窗建議路線

| 優先 | 任務 | 為什麼 |
|---|---|---|
| 1 | **主線待辦已清空** | P75 / P70.4 / P70.6 均已推送；P76 若為本地 ahead，等主公確認 push |
| 2 | **Open risks 盤點** | R-001/R-002/R-003/R-004/R-005/R-006/R-011/R-012/R-013 仍屬觀察或後續增強 |

### 開工注意

- 不要全讀 `TASK_HISTORY.md`；查歷史先 `rg -n "^### " TASK_HISTORY.md` 或讀尾端。
- 下一個 Phase 必須用 `docs/PHASE_TEMPLATE.md` v1.2：含 X4-A 紅隊、X4-K 使用者端審查、M1.5 八人格 Persona Overlay。
- 模型選擇依 P73 新規則：策略/治理用 GPT-5.5，高風險動工或 repo patch 用 GPT-5.3-Codex。
- Push 前仍須主公確認；不要自動 stage untracked 報告檔。

---

## ✅ 本視窗已完成：P73 模型選擇指引 v1.2 OpenAI / Codex 分支

**背景**：主公回鍋 ChatGPT / Codex 後，實際可用模型集中在 GPT-5.5 與 GPT-5.3-Codex。原 P69 `docs/MODEL_SELECTION_GUIDE.md` v1.1 仍以 Sonnet / Opus / Gemini 為主，會讓未來 Phase 的「負責模型」欄與現況漂移。

**凍結計畫書**：`docs/PHASE_73_PLAN.md`

**核心規則**：
- 想清楚 / 計畫 / 治理規則 / 重大決策 → **GPT-5.5 + 高**
- 進 repo 動工 / 改檔 / 跑測試 / 修 bug → **GPT-5.3-Codex + 中/高**
- 小任務 / 摘要 / 翻譯 / 表格 / 語氣 → **GPT-5.4-Mini + 低/中**
- 卡住 → 升高 / 超高，或在 GPT-5.5 與 GPT-5.3-Codex 之間切換視角

**修改檔案**：
- `docs/PHASE_73_PLAN.md`：P73 凍結計畫書
- `docs/MODEL_SELECTION_GUIDE.md`：升 v1.2，新增 OpenAI / ChatGPT / Codex 分支
- `docs/PHASE_TEMPLATE.md`：負責模型欄補 GPT-5.5 / GPT-5.3-Codex / GPT-5.4-Mini
- `AGENTS.md`：Codex 新視窗縮版模型規則同步
- `TASK_HISTORY.md`：追加 P73 無損紀錄

**官方查證來源**：
- OpenAI Codex rate card
- OpenAI API pricing
- GPT-5.5 in ChatGPT Help Center
- Introducing GPT-5.3-Codex

---

## ⚡ 本視窗（2026-05-14 晚間）做了什麼

| 項目 | Commit | 內容 |
|---|---|---|
| **AGENTS.md** | `7bf490e` | 新增 ChatGPT / Codex 專用工作守則（503 行 / 17 段落），整合自 CLAUDE.md + GEMINI.md + .agent/rules.md + .agents/rules/projectrules.md。含終端機環境規範、Skill 基礎設施、scripts 工具箱、63 維度稽核 |
| **P72 收官紀錄** | `244ff72` | commit 先前未推的 TASK_HISTORY +109 行 / RISK_REGISTRY R-012~R-015 / HANDOFF 更新 |
| **P72.5 postmortem** | `6f1bc32` | commit 先前未推的 2 份 postmortem + blindspots（B-006~B-010） |

### AGENTS.md 涵蓋內容（17 段落速查）

1. 專案總覽（五大模組）
2. 稱呼與語言（主公 / 繁中）
3. **新對話啟動協議**（讀 handoff → phase 記憶 → phase0 → registry）
4. **計畫書先行鐵律**（版面精美 / 主公同意才動工）
5. TASK_HISTORY 鐵律 + Hook 防呆（Codex 手動等效表）
6. 無損技術存檔協議（7 條紀錄準則）
7. 密涅瓦思考框架（4 大類）
8. 寫程式行為準則
9. **終端機環境與操作規範**（UTF-8 / py 慣例 / chcp / 檔案安全）
10. **Git 工作流慣例**（commit 格式 7 type / push 必問主公）
11. **Slash Command 對應表**（/prompt + /trend 的 CLI 入口）
12. **Skill 基礎設施**（二級架構 / __main__.py / smart-task-router / 健康儀表板）
13. **scripts 終端工具箱**（12 個腳本速查）
14. 模型選擇指引（含 Gemini thinkingLevel + 200K+ 劣化警告）
15. 17 層品質框架 v3.1（63 維度 + 3 Patch）
16. Skill 自動觸發協議（S2 + V1 + 終端 plain 模式）
17. 專案關鍵路徑速查表

### 63 維度稽核結果

- S 級 4 層 **全 PASS**
- 稽核發現 2 項已當場修正：① Push 必問主公（L230）② test commit type 補齊（L223）

---

## ✅ 本視窗已完成：PHASE_TEMPLATE v1.2 寫入

**背景**：P72.5 收官時 `--sync-rules` 暴露 R-013 anchor heuristic 召回率低，主公決定（選項 C）先消化 B-NNN 通則化規則升版 PHASE_TEMPLATE.md。2026-05-15 主公再次確認採「方案 C」：原 v1.2 六條 + 八人格 Persona Overlay 一起落地。

### v1.2 升版內容（**已寫入**）

> **X1 不可逆動作**：PHASE_TEMPLATE.md 是凍結文件。本次升版已獲主公 2026-05-14「全核可」與 2026-05-15「方案 C」確認，已依流程寫入。

| # | 來源 | 動作 | 插入位置 |
|---|---|---|---|
| **1** | B-002 (P71) | 新增 **§0.5「狀態轉換清單」**（條件式必填）：若本 Phase 涉及 skill/模組生命週期轉換（active/archived/orphan），明定 (a) 狀態定義 (b) 轉換條件 (c) 轉換執行者 | §0 元資料之後 |
| **2** | B-004 (P71) | **§STR9 表格下加備註**：「schema lint 要同時驗『欄位存在』與『欄位值有意義』；`deployed_to: []` 對 in-use skill 視為 warning」 | §STR9 表格下方 |
| **3** | B-006 (P72) | **§7 X4 加新項 X4-J「自動化建議性工具邊界」**：列出本 Phase 引入的字面比對啟發式 + 標注「召回率僅供參考」邊界 | §7 X4 之後 |
| **4** | ~~B-007~~ | ⚠️ **跳過**（屬 CLAUDE.md 鐵律範圍，留待另開鐵律 v0.5 升版議題）| — |
| **5** | B-008 (P72) | **§M2 紅藍對抗表格加必填欄位「pre-existing 失敗計次」**：每條 pre-existing failing test 記錄已被多少 Phase 跳過，≥ 3 須升為獨立 Phase | §M2 表格加一欄 |
| **6** | B-009 (P72) | **§6 A 級可觀察性層加備註**：「本 Phase 若引入 append-only 檔案（log/metrics/audit trail），必須明列 size cap / rolling policy / retention SOP 三項中至少一項」 | §6 可觀察性層 |
| **7** | B-010 (P72) | **§11 Postmortem 預埋點加備註框**：「下個 B-NNN / R-NNN 編號查詢命令：`grep -h '^### [BR]-' docs/**.md \| sort -u \| tail`；B-NNN/R-NNN 全域連續，禁止 Phase 內局部編號」 | §11 之後加備註框 |
| **8** | 2026-05-15 主公新增 | **方案 C：Persona Overlay**：X4-A 升級為世界頂尖駭客 / 紅隊攻擊者；新增 X4-K 使用者端審查官；新增 §M1.5 八人格顧問團觸發檢查 | §7 X4 / §M1 / §M1.5 |

### 版本戳記更新（必做）

**舊**（PHASE_TEMPLATE.md 第 234 行附近）：
```
*樣板版本：v1.1（2026-05-09 P71.1 新增 STR9/STR10/Pre-flight 體檢 M1+M2）*
```

**新**：
```
*樣板版本：v1.2（2026-05-15 P72.5 補遺寫入：Exit Criteria 錨點 / §0.5 狀態轉換清單 / STR9 lint 強化備註 / X4-A 紅隊升級 / X4-J 自動化工具邊界 / X4-K 使用者端審查官 / M1.5 八人格 Persona Overlay / M2 pre-existing 計次 / §6 retention 備註 / §11 B-NNN 查詢備註 / 主公裁決錨點）*
```

### 額外連帶更新（本視窗處理）

1. **P71 blindspots 體檢清單升版摘要表格**：v1.2 欄已從「待議」改「已落地（2026-05-15 P72.5 補遺寫入）」。
2. **P72 blindspots 體檢清單升版摘要表格**：v1.2 欄已從「待議」改「已落地（2026-05-15 P72.5 補遺寫入）」；B-007 標為 CLAUDE.md 鐵律範圍，未塞入 PHASE_TEMPLATE。
3. **TASK_HISTORY 追加 P72.5 補遺段落**：記錄 v1.2 + Persona Overlay 寫入動作。
4. **驗收**：`py scripts/m4_track_blindspots.py --sync-rules` 已跑通；9/10 條 B-NNN 規則被 PHASE_TEMPLATE 涵蓋，唯一剩餘 B-007 屬 CLAUDE.md / 鐵律 v0.5 範圍，刻意不塞入模板。

### 後續候選 Phase

寫完 v1.2 後，主公可選：
- ✅ P70.2 GHA 每日健康巡檢已於 2026-05-16 收官
- ✅ P70.4 OpenAI fallback 已於 2026-05-16 收官
- ✅ P70.6 llm_cache LRU / TTL 已於 2026-05-16 收官
- ✅ R-014 歷史 4 Phase blindspot 回填（P63/P64/P69/P70.3）已於 P75 收官
- ✅ R-015 已於 P74 收官關閉（2026-05-16）

---

---

## 🚀 下個視窗候選動工選項（主公擇一）

### 已完成：P70.2 — GHA 每日健康巡檢
P70.2 已新增 `scripts/check_daily_report_health.py` 並接入 `.github/workflows/daily_report.yml`。

### 已完成：P70.4 — OpenAI fallback
Gemini 429 / provider down 時會嘗試 OpenAI fallback；OpenAI key 未設或 fallback 也失敗時維持既有降級語意。

### 已完成：P70.6 — llm_cache LRU / TTL 機制（預防性）
`CacheManager` 已升 v3，新增 `last_accessed` 與 max entries LRU；全套測試 126 passed。

### 已完成：R-014 收尾 — 4 個歷史 Phase blindspot 回填
P75 已補齊 P63/P64/P69/P70.3 blindspots，新增 B-011~B-022，`m4_track_blindspots.py --status` 缺漏數 0。

### 已完成：R-015 — test_dynamic_focus 獨立 Phase
P74 已完成修復並關閉 R-015；下個視窗不需再排此項。

---

## ✅ P72.5 收官紀錄（2026-05-14）

**產出**：
| 檔案 | 內容 |
|---|---|
| `docs/postmortems/2026-05-14-phase-72-metrics-and-m3m4-stitching.md` | P72 系列 postmortem，4 條核心教訓 + 6 條「以為」清單 |
| `docs/postmortems/2026-05-14-phase-72-blindspots.md` | B-006~B-010 共 5 條盲點（含通則化；B-010 為本 Phase 自踩編號衝突）|
| `docs/RISK_REGISTRY.md` | 新增 R-012/R-013/R-014/R-015（4 條開放風險）|
| `TASK_HISTORY.md` | 追加 P72.0~P72.5 共 6 段收官紀錄（+108 行）+ 2026-05-15 P72.5 補遺 |

**驗收**：`py scripts/m4_track_blindspots.py --status` → P72 顯示「✅ 已配對」

**X1 不可逆動作隔離**：P72.5 收官當下 PHASE_TEMPLATE.md v1.2 升版項曾記為「待議」；2026-05-15 主公確認方案 C 後，已於 P72.5 補遺寫入 PHASE_TEMPLATE v1.2 + Persona Overlay。

**待 commit**：本視窗收尾時主公拍板（守則「push 必問」）。

---

## ⚡ 本視窗（2026-05-14）做了什麼 — P72 系列連跑 5 Phase

| Phase | Commit | 內容 |
|---|---|---|
| **P72.0** | `0894548` | Skill Metrics 基礎建設：`scripts/skill_metrics_logger.py` + 11 × __main__.py 接 `_run_with_metrics()` + `scripts/gen_skill_metrics.py` CLI + 16 單測 |
| **P72.4** | `7855714` | metrics 接入 SKILL_HEALTH.md：gen_skill_health.py 偵測 metrics 自動展開 11 欄表格（含 O1/O2/O3 數據）|
| **P72.1** | `b6119d2` | 雙 remote 自動 backup：`scripts/backup_push.py`（local CLI）+ `.github/workflows/backup-mirror.yml`（CI），尚未設 BACKUP_REMOTE_URL secret 所以 CI 是 no-op |
| **P72.2** | `a1492db` | M3 歷史交叉審查自動化：`scripts/cross_phase_review.py` 從 postmortems 抽 B-NNN 通則化 + 核心教訓 + 以為清單，輸出 Markdown checklist 供新 Phase 計畫書 §M3 段落使用 |
| **P72.3** | `ce904f5` | M4 時效追溯自動化：`scripts/m4_track_blindspots.py`（--status / --scaffold / --sync-rules）+ 21 單測，**不可逆動作隔離**（不自動寫 PHASE_TEMPLATE.md）|

### 累積測試成績
- **P72 當時全套**：109 passed / 3 failed（3 failed 為 pre-existing test_dynamic_focus 事件迴圈隔離，全 P72 系列無回歸）
- **P74 後全套**：112 passed，R-015 已關閉
- **P72.0**：16 單測
- **P72.3**：21 單測

### 已知遺留問題（P72.5 候選盲點素材）

1. ✅ **test_dynamic_focus 3 個 pre-existing 失敗**：已於 P74 關閉；三處改 `asyncio.run(...)`，單檔 5 passed，全套 112 passed。
2. **`--sync-rules` anchor heuristic 召回率低**：實測 PHASE_TEMPLATE v1.1 已含 B-001/003/005 規則但 anchor 沒匹配上。文件已標「主公人工審核」但仍是粗糙設計。
3. **metrics JSONL 無 size cap**：`~/.claude/skill_metrics.jsonl` append-only，跑久會無限長。
4. **P72 commits 尚未 push**：本視窗收尾時主公決定。

### 本視窗未做（為何沒做）

- ❌ **push 到 origin/main**：守則「push 必問」，等主公拍板
- ❌ **P72.5**（postmortem + 風險登記）：刻意留下個視窗開工，給足思考空間寫盲點

---

---

## ⚡ 本視窗（2026-05-11）做了什麼

| Phase | Commit | 內容 |
|---|---|---|
| **P71.6** | `ba7352f` | smart-task-router 救活：router.py 接 S1 schema registry / 數值信心分數 / V1 觸發塊 / `__main__.py` CLI / 8/8 測試全綠 |
| **P71.7** | 本次視窗 | `scripts/gen_skill_health.py` + `docs/SKILL_HEALTH.md` + `.github/workflows/skill_health.yml`：19 skill 狀態 🟢5 🟡7 🔴7 |
| **P71.8** | 本次視窗 | 6 stale shared skills Gemini 同步（S1 schema + __main__.py 推入）；🟢 11 / 🟡 0 |
| **P71.9** | 本次視窗 | 7 orphan → in-use，補 S1 schema + 7 × __main__.py；🟢 18 / 🟡 0 / 🔴 1 |
| **P71.9+** | 本次視窗 | ui-ux-pro-max 補 `test_skill.py`（6/6）；**🟢 19 / 🟡 0 / 🔴 0 史上首次全綠** |

### P71.6 技術細節

**信心算法**：
- `trigger_keywords` 命中：每個 +0.2（強匹配）
- `when_to_use` 命中：每條描述 ≥2 詞 +0.05（弱匹配）
- `when_NOT_to_use` 命中：每條 ≥2 詞 −0.2（負向）

**閾值（D3 決定）**：
- ≥ 0.9 → `AUTO`（直接執行 + 印 V1）
- 0.7 ~ 0.89 → `CONFIRM`（詢問主公 [Y/n]）
- < 0.7 → `NO_MATCH`（不觸發）

**CLI 用法**：
```bash
cd .agent/skills/smart-task-router
python __main__.py "幫我查芽芽聲量走勢趨勢"
python __main__.py "幫我查芽芽聲量走勢趨勢" --output json
python __main__.py list
NO_COLOR=1 python __main__.py "芽芽聲量"
```

---

## ⚡ 本視窗（2026-05-09）做了什麼

| Phase | Commit | 內容 |
|---|---|---|
| **P71.3** | `fb4548c`（合併）| 11 個 `__main__.py` + SKILL.md 終端執行章節 |
| **P71.4** | `fb4548c` | `deploy_skills.py`（copy+lockfile+SA1）+ `.pre-commit-config.yaml`（SA4）+ 2 CI workflows + `--warn-only`（D4）|
| **P71.5** | `7c9e607` | 8 shared skills → `D:/skills-shared/`（獨立 git repo，已 push GitHub）+ registry.json 絕對路徑 |

### 重要架構變更（P71.5）

- **`D:/skills-shared/`**：獨立 git repo（`sammy50307-debug/skills-shared`，private）
  - 8 個跨專案 skill：ai-news-radar / api-quota-guardian / firecrawl-dynamic-breacher / html-markdown-distiller / multi-thread-synthesizer / nl-to-prompt-structurer / semantic-cache-shield / trend-anomaly-detector
- **`.agent/skills/`**：只剩 AOV 專屬 3 個（history-trend-query / hallucination-judge / hot-deployer）+ 9 個 orphan（P71.9 待處置）
- **`skills/registry.json`**：shared skill 的 `claude_path` 已改為絕對路徑 `D:/skills-shared/X`，並加 `"shared": true`

### P71.4 工具速查

```bash
py -3 scripts/deploy_skills.py --list           # 看所有 skill 路徑
py -3 scripts/deploy_skills.py                  # dry-run 預覽
py -3 scripts/deploy_skills.py --execute --backup  # 實際同步到 Gemini
pre-commit install                              # 安裝 hook（首次）
# D4：2026-05-23 後移除 .pre-commit-config.yaml 的 --warn-only 升為 block
```

---

## 🆕 P71 進度看板（2026-05-09 更新）

### ⭐ 動工指揮文件

> **完整計畫書：[`docs/P71_PLAN.md`](./docs/P71_PLAN.md)**（**v1.2 凍結版** / 2026-05-09）

新視窗開局必讀順序：
1. 本檔（NEXT_SESSION_HANDOFF.md）
2. **`docs/P71_PLAN.md`**（v1.2 凍結：26 優化點 + Pre-flight 9 視角 + P71/P72/P73 拆分）
3. `docs/SKILL_INVENTORY.md`（P71.0 盤點成果）
4. `skills/registry.json`（P71.2 升級完成，S1 schema 全備）

### P71 核心目標（主公 2026-05-08/09 拍板）

> 「**這些 skill 都可以永久被使用不會消失，使用時機是 LLM 自行判斷不需要我提醒**」
> 「**當 SKILL 觸發的時候要顯示讓我看到**」（V1 觸發塊）

### P71 階段進度

| 階段 | 內容 | 狀態 | Commit |
|---|---|---|---|
| **P71.0** | SKILL_INVENTORY.md 盤點（20 skill 分類） | ✅ | `ffb9ebe` |
| **P71.1** | registry.json + lint + PHASE_TEMPLATE + Pre-flight 體檢 | ✅ | `5029486` |
| **P71.2** | S1 schema × 11 SKILL.md + S2/V1 觸發協議 × 全域指令檔 | ✅ | `b1fa1ac` |
| **P71.3** | 11 skill 自包含化 + `__main__.py` + 終端適配 | ✅ | 本次視窗 |
| **P71.4** | deploy_skills.py + pre-commit + CI + SA1/SA4 | ✅ | 本次視窗 |
| **P71.5** | 8 shared skills → D:/skills-shared/ + registry 絕對路徑 | ✅ | 本次視窗 |
| **P71.6** | smart-task-router 救活（L2 路由） | ✅ | `ba7352f` |
| **P71.7** | SKILL_HEALTH.md Dashboard | ✅ | 本次視窗 |
| **P71.8** | 7 個 Gemini diff 主公裁決 | ✅ | 本次視窗 |
| **P71.9** | 7 個 orphan 啟用 | ✅ | 本次視窗 |
| **P71.10** | Postmortem + R-009~011 | ⏳ | — |

### D1-D8 決策（全部已拍板，見 SKILL_INVENTORY.md）

| # | 決策 | 已確認 |
|---|---|---|
| D1 | ~/skills-shared/ 路徑 = `D:/skills-shared/` | ✅ |
| D2 | 本機 git init → 後上 GitHub | ✅ |
| D3 | 信心閾值 0.7 詢問 / 0.9 直接執行 | ✅ |
| D4 | pre-commit 起始 warning | ✅ |
| D5 | instagram-facebook-dcard 歸檔；其餘 19 全保留 | ✅ |
| D6 | 建 `<proj>/.gemini/` | ✅ |
| D7 | 修全域 CLAUDE.md 同步 Pre-flight 協議 | ✅ 已執行 |
| D8 | lint_phase_plan.py --allow-skip 自動入 RISK | ✅ |

### 7 個 Gemini-only diff 裁決順序（P71.5 用）

```
1. ai-news-radar              (536 行)
2. instagram-facebook-dcard   (388 行)
3. html-markdown-distiller    (92)
4. semantic-cache-shield      (90)
5. trend-anomaly-detector     (70)
6. firecrawl-dynamic-breacher (68)
7. multi-thread-synthesizer   (64)
```

### 重大發現（本視窗勘查）

1. ✅ **Gemini Antigravity 已駐紮 7 個 skill**（不是孤兒，是「跨家移居」）
2. ✅ **P43-P50 黃金期建立過「全域部署」傳統**，P50 後規則退化（G5 抗熵實證）
3. ✅ **Gemini 沒有 slash commands 機制**（自然語言觸發 SKILL.md）
4. ✅ **雙端 7 個 skill 嚴重 diff（66-536 行）**，需主公人工裁決

---

## ⚡ 下個視窗開局速查（30 秒看完就能動工）

### 本視窗（2026-05-08）做了什麼

| Phase | 狀態 | Commit | 內容 |
|---|---|---|---|
| **P70.7** | ✅ 已 push | `40d1874` | 清除 data/ 三個 0-byte raw 殘留（2026-03-23/25/27）|
| **P70.1** | ✅ 已 push | `b9868fb` | Picker 去重懲罰 + 同平台排名衰減 + 芽芽×1.5 bonus |
| **P70.3** | ✅ 已 push | `a2a6d39` | LINE 滑動失靈根治（html/body 拆分 + touch-action:pan-y）+ 10 舊報告同步 + index.html 預防性修補 |
| **P70.3.1** | ✅ 已 push | `a2a6d39` | 報告頁加「← 回戰略門戶」按鈕 + R-007（mobile blur）+ R-008（:focus + aria-label）補強；主公 LINE 實機驗收通過 |
| **P70.3 docs** | ✅ 已 push | `ae07746` | postmortem（含第十節）+ RISK_REGISTRY R-006/007/008 + TASK_HISTORY 補錄 |

### P70 系列動工順序

```
P70.7 ✅ → P70.1 ✅ → P70.3 ✅ → P70.3.1 ✅ → P70.5' ✅ → P71 ✅ → P70.2 ✅ → P75/R-014 ✅ → P70.4 ✅ → P70.6 ✅
```

### ✅ P71.3 收官（2026-05-09）

**已完成**：11 個 `__main__.py` 建立 + 11 個 SKILL.md 補「終端執行」章節。

**執行方式**（以 history-trend-query 為例）：
```bash
cd .agent/skills/history-trend-query
python __main__.py hero 芽芽 --days 7
python __main__.py hero 芽芽 --output json
NO_COLOR=1 python __main__.py overall
```

**重要設計決策**：
- `python -m skills.<name>` 是 P71.5 目標（需改目錄為底線命名）；P71.3 用 `python __main__.py`
- `_output_mode()` 每個 `__main__.py` inline（自包含），不引跨 skill 共用模組
- hallucination-judge 返回碼：0=PASS / 1=WARN+FAIL

### ✅ P71.4 收官（2026-05-09）

**已完成**：`deploy_skills.py`（copy + lockfile + SA1）+ `.pre-commit-config.yaml`（SA4 detect-secrets）+ 2 CI workflows。

**關鍵決策**：
- D4：pre-commit `--warn-only`（exit 0）；CI 不用 `--warn-only`（block）；2026-05-23 後本機升 block
- SA1：`safe_path()` 驗三根目錄（PROJECT_ROOT / ~/.gemini / D:/skills-shared）
- `.secrets.baseline` 空 results{}；誤報更新：`detect-secrets scan --update .secrets.baseline`

**使用方式**：
```bash
py -3 scripts/deploy_skills.py --list             # 看可部署清單
py -3 scripts/deploy_skills.py                    # dry-run 預覽
py -3 scripts/deploy_skills.py --execute --backup # 實際同步（含備份）
pre-commit install                                 # 安裝 hook（首次）
```

### 下個視窗動工：P71.5

**P71.5 任務**：shared/project 二級分類 + `~/skills-shared/`（`D:/skills-shared/`）git repo 建立 + sys.path shim 過渡

對應優化點：A1
注意：mv 目錄會破壞 import 路徑（R-P71-11），需設計 shim 或 alias

---

## 🗂️ P70 子 Phase 全覽

| 子 Phase | 內容 | 狀態 | Commit |
|---|---|---|---|
| **P70.7** | 0-byte raw 殘留清理 | ✅ 收官 | `40d1874` |
| **P70.1** | Picker 品質強化（去重懲罰 + 平台衰減）| ✅ 收官 | `b9868fb` |
| **P70.3** | LINE 滑動失靈排查 + 根治 | ✅ 收官 | `a2a6d39` |
| **P70.3.1** | 報告頁「← 回戰略門戶」按鈕 | ✅ 收官 | `a2a6d39` |
| **P70.5'** | test_429_retry P69.1 技術債（R20/R23/R24 已於 P61.1 落地）| ✅ 收官 | 待 commit |
| **P70.2** | GHA 每日健康巡檢 | ✅ 收官 | `72cbb25` |
| **P70.4** | OpenAI fallback | ✅ 收官 | `089119f` |
| **P70.6** | llm_cache LRU / TTL 機制（預防性）| ✅ 收官 | `614dc13` |

---

## 🔧 P70.5' 統包內容（下視窗直接動工）

### 背景

P70.5 原為 SQLite 遷移，在 2026-05-08 技術債健診中確認無 ROI（data/ < 200K、無實證痛點），已移除。P70.5' 改為處理 **P61.1 遺留的 cache 邏輯瑕疵**（R20/R23/R24）+ 既有技術債 `test_429_retry.py`。

### P70.5' 範圍

| 項目 | 描述 | 來源 |
|---|---|---|
| **R20** | history-trend-query cache 邏輯瑕疵 | P61 遺留 |
| **R23** | （同上，具體見下） | P61 遺留 |
| **R24** | （同上，具體見下） | P61 遺留 |
| **test_429_retry.py 2 cases** | `GeminiClient._cm` 屬性缺失（P69.1 改 gemini_client.py 後測試未跟上）| P69.1 技術債 |

### R20/R23/R24 技術細節

P61 history-trend-query 引入了 L1/L2 cache 機制：
- **L1** = `hero:{name}:{date}`
- **L2** = `prompt:{md5(system|user)}`（L2 一定跨日 miss，因 date 嵌入 prompt）

具體瑕疵需開工時查 P61 TASK_HISTORY 段落確認（grep `### P61` → Read offset）。

### test_429_retry.py 技術細節

P69.1 修改了 `gemini_client.py`，導致 `GeminiClient._cm` 屬性缺失，兩個測試 case 失敗：
- 測試未跟上 P69.1 的 API 改動
- 目前全套：73/73 零回歸（排除這 2 cases）

---

## 🔧 P70.1 技術細節（供 debug 用）

### 新增參數（config.py P70.1 區塊）

| 參數 | 值 | 說明 |
|---|---|---|
| `DUP_PENALTY_DAY1` | 0.3 | 1 天內重複文章懲罰因子 |
| `DUP_PENALTY_DAY3` | 0.2 | 2-3 天重複懲罰因子 |
| `DUP_PENALTY_DAY7` | 0.1 | 4-7 天重複懲罰因子 |
| `PLATFORM_RANK_DECAY` | 0.1 | 同平台每多一篇衰減率 |
| `PLATFORM_RANK_MIN` | 0.3 | 同平台衰減下限 |
| `YAYA_REPEAT_BONUS` | 1.5 | 芽芽重複文章加成（不扣反加）|

### picker metadata 新欄位

每張卡的 `card["picker"]` 新增：
- `dup_factor`：去重懲罰倍率（非重複=1.0，芽芽重複=1.5）
- `platform_rank`：同平台第幾篇（芽芽卡無此欄位）
- `platform_penalty`：同平台降權倍率（芽芽卡無此欄位）

### 芽芽雙豁免規則

1. `is_dup=True` + 芽芽 → `dup_factor=1.5`（加分）
2. 芽芽文章不計入 `platform_seen` 計數 → 一般文章的 platform_rank 不受芽芽影響

### 測試狀態

- `tests/test_top5_picker.py`：45/45 全綠（原 39 + P70.1 新增 6）
- 全套：73/73 零回歸（排除 P69.1 既有失敗的 test_429_retry 2 cases）

---

## ⚠️ 既有技術債（非本 Phase 引入）

| 項目 | 描述 | 狀態 |
|---|---|---|
| `test_429_retry.py` 2 cases | `GeminiClient._cm` 屬性缺失（P69.1 改 gemini_client.py 後測試未跟上）| ✅ P70.5' 已修，75/75 全綠 |
| R20/R23/R24 | history-trend-query cache 邏輯瑕疵 | ✅ P61.1 已落地（renderer.py / time_series_loader.py） |
| Skill 75% 孤兒率 | 20 個 skill 中 15 個無入口無代碼引用 | ⏳ P71 全面治理 |
| GHA 連 2 天（5/7、5/8）無報告 | P70.2 已完成本機證據盤點；5/7、5/8 報告由 `a2a6d39` 後補，首頁主按鈕曾停在 5/6；已新增 health checker 防復發 | ✅ P70.2 收官 |

---

## 🌟 本視窗關鍵決策紀錄

1. **P70.5 SQLite 遷移移除**：技術債健診（2026-05-08）確認 data/ < 200K、無實證痛點、raw post 無互動欄位，SQLite 遷移無 ROI。
2. **P70 拆分 (a) 方案**：依影響半徑機械判斷 S/S+A/全層，不強制全套 63 維度。
3. **dup_factor 梯度**：主公拍板 day1=0.3 / day3=0.2 / day7=0.1（比原提案更嚴格）。
4. **芽芽×1.5**：主公從 ×1.2 升至 ×1.5，確保芽芽即使重複也排最前。
5. **platform_rank 芽芽豁免**：芽芽不佔同平台計數，讓一般文章的平台衰減不受芽芽干擾。
6. **P70.3.1 方案 B**：主公選方案 B（在報告頁加回首頁按鈕），不改 LINE bot 邏輯。

---

## 📋 P70.3 / P70.3.1 收官紀錄（供後續 debug 參考）

### P70.3 根因

`reporter/templates/report.html` 的 `html, body { overflow-x: hidden }` 把 `overflow-x` 套在 `html` 元素上，LINE WebView 將 `html` 視為 viewport scroll container，遇到 hidden 即停止轉發 touch scroll → 整頁滑不動（WebKit bug #153852）。

### P70.3 修法

- `html {}` 只保留 `width: 100%`（移除 `overflow-x: hidden`）
- `body {}` 保留 `overflow-x: hidden` + `-webkit-overflow-scrolling: touch` + 新增 `touch-action: pan-y`

### P70.3.1 修法

- `.back-to-landing` pill：`background: rgba(255,255,255,0.55); backdrop-filter: blur(10px); border-radius: 999px; color: #be185d;`
- 連結：`https://sammy50307-debug.github.io/Arena-of-Valor/`
- R-007：加入 `@media (max-width: 768px)` backdrop-filter 停用 selector
- R-008：`:focus { outline: 2px solid #f472b6; }` + `aria-label="返回戰略門戶首頁"`

### 影響範圍

- template（未來所有新報告）
- `data/reports/aov_report_2026-05-{01..10}.html`（已 push）
- `index.html`（landing page 預防性修補）

---

*下個視窗讀完此檔即可直接動工 P70.5'。*
