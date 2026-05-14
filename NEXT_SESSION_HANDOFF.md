# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-14（P72.3 收官，連跑 5 個 phase）
- **狀態**：✅ P72.0 / P72.1 / P72.2 / P72.3 / P72.4 全收官；⏳ **P72.5 待動工**
- **下個視窗開局**：直接動工 **P72.5 — Postmortem + R 系列風險登記**（P72 系列收官 phase）

---

## 🚀 下個視窗動工：P72.5 — Postmortem + R 系列風險登記

**目標**：為 P72 系列（P72.0~P72.4）寫 postmortem + blindspots，並把本系列暴露的新風險登入 RISK_REGISTRY。是 P72 系列的最後一塊。

### P72.5 工作清單

1. **寫 P72 postmortem**：`docs/postmortems/2026-05-14-phase-72-<topic>.md`
   - 主題建議：「metrics 基礎建設 + M3/M4 自動化的順序拼接」
   - 涵蓋 P72.0-P72.4 的核心教訓（≥ 3 條「我以為」事件）

2. **寫 P72 blindspots**：直接用 `py scripts/m4_track_blindspots.py --scaffold p72` 生成樣板，再填 ≥ 3 條 B-NNN
   - 候選盲點：
     - `--sync-rules` anchor heuristic 太嚴格（測試發現「已涵蓋 0 條」明顯低估）
     - PowerShell 與 bash heredoc 不互通（多次 commit 卡在這）
     - test_dynamic_focus 3 個 pre-existing 失敗一直沒解（事件迴圈隔離）

3. **登入 RISK_REGISTRY**：R-012+ 系列
   - R-012 候選：metrics JSONL 檔無 size cap → 跑久了會無限長
   - R-013 候選：M4 sync-rules anchor heuristic 召回率低
   - R-014 候選：4 個歷史 phase（P63/P64/P69/P70.3）缺 blindspot（M4 偵測出來）

4. **回填歷史 phase blindspots**（可選，視時間）：
   - `py scripts/m4_track_blindspots.py --status` 看缺哪些
   - 對 P63/P64/P69/P70.3 逐一 `--scaffold` 後人工填寫

### 入口條件（P72.5 Entry Criteria）

- ✅ P72.0~P72.4 全收官
- ✅ M4 自動化腳本（scripts/m4_track_blindspots.py）可用
- ✅ 19/19 skill 維持全綠

### 退出條件（P72.5 Exit Criteria）

- ✅ P72 postmortem 寫好（≥ 3 條核心教訓）
- ✅ P72 blindspots 寫好（≥ 3 條 B-NNN）
- ✅ RISK_REGISTRY 新增 ≥ 2 條 R 系列
- ✅ `--status` 對 P72 顯示「已配對」

### 參考文件

- `docs/P71_PLAN.md`（v1.2 凍結版）§ P72 範圍宣告
- `docs/RISK_REGISTRY.md` — R-009~011 已登記，P72.5 接續 R-012+
- `scripts/m4_track_blindspots.py` —— P72.3 新建，本 phase 直接套用

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
- **全套**：109 passed / 3 failed（3 failed 為 pre-existing test_dynamic_focus 事件迴圈隔離，全 P72 系列無回歸）
- **P72.0**：16 單測
- **P72.3**：21 單測

### 已知遺留問題（P72.5 候選盲點素材）

1. **test_dynamic_focus 3 個 pre-existing 失敗**：跑單檔 OK、跑全套會掛，事件迴圈共用問題。連跑 5 個 Phase 都沒處理，已成積欠。
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
P70.7 ✅ → P70.1 ✅ → P70.3 ✅ → P70.3.1 ✅ → P70.5' ✅ → P71 ⏳ → P70.2 → P70.4 → P70.6
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
| **P70.2** | GHA 每日健康巡檢 | ⏳ 待動工 | — |
| **P70.4** | OpenAI fallback | ⏳ 待動工 | — |
| **P70.6** | llm_cache LRU / TTL 機制（預防性）| ⏳ 待動工 | — |

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
| GHA 連 2 天（5/7、5/8）無報告 | 原因未排查完（本機無 API key 無法 E-C/E-D 測試）| ⏳ P70.2 排查 |

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
