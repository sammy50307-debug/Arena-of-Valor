# 🔄 P103 / P103.1 交接手冊（GOV-PORT 回填 AOV — 接手續做）

> **給下一個視窗的你**（cwd = `D:/Coding Project/Arena of Valor`）：讀完這份你就能接手。
> 使用者叫**阿喜**（稱「主公」，繁體中文）。本手冊**自包含**，不依賴前一對話記憶。撰於 2026-05-31。
> ⚠️ 任何貼入的程式/設定，機敏值一律 `***REDACTED***`（資安 > 紀錄）。

---

## 0. 30 秒上手 + 開場必讀

- **你要做什麼**：完成 **P103.1（metrics 議題收尾）** 的三個文件動作；之後（可選）做 **AOV 全貌架構巡覽**。
- **cwd**：`D:/Coding Project/Arena of Valor`（讓 AOV 的 CLAUDE.md / CI / 17 層框架生效）。
- **開場必讀（依序）**：
  1. **本手冊**（P103_SESSION_HANDOFF.md）
  2. `D:/skills-governance/docs/BACKFILL_AOV_HANDOFF.md`（回填全脈絡：為何回填、6 項清單、執行鐵律、§9 開場 prompt）
  3. `docs/P103_BACKFILL_AOV_PLAN.md`（P103 凍結計畫書，已過 M1/M2）
- **⚠️ 動工前先給計畫書、等主公核准**——但 P103.1 三動作是純文件收尾（無程式、無 blast radius），主公已定方向，可直接做（見 §3）。

---

## 1. 背景：這條線是什麼

GOV-PORT Program 把 AOV 的成熟治理抽成獨立 repo `D:/skills-governance`（融合 Hermes 兩亮點 + 補缺口），**P103 就是把融合改良過的引擎「回填」裝回 AOV 母本**，完成「AOV→抽出融合→回填」閉環。核心哲學：知識落進產物（code/test/checker/config），不靠對話記憶。

---

## 2. ✅ P103 已完成（已 commit + push，**別重做**）

| 項目 | 狀態 |
|---|---|
| 計畫書 commit | `085182b`（main）`docs: 開 P103 回填 AOV 計畫書並凍結` |
| 執行 commit | `b27d2e4`（分支 `P103-backfill-aov`）`feat: P103 回填 AOV...` |
| 遠端 | 已 push `origin/P103-backfill-aov`（GitHub: sammy50307-debug/Arena-of-Valor） |
| 測試 | **308 passed**（基線 307 + A3 新增 1），preflight fast 全綠 |

**Stage A（順手修，都已對拍綠）**：
- **A1**：`scripts/lint_phase_plan.py` X4 視角 9→11（補 X4-J 自動化建議性工具邊界、X4-K 使用者端審查官）+ docstring。
- **A1b**：全域 `C:/Users/sammy/.claude/CLAUDE.md:271` 同源漂移修正（9→11 視角）。
- **A2**：新增 `scripts/governance_utils.py::extract_blindspot_entries`，消除 `cross_phase_review._extract_blindspots` × `m4_track_blindspots.extract_blindspot_rules` 重複（兩者改 delegate）。
- **A3**：metrics 根因診斷（見 §3）+ `tests/test_skill_metrics_logger.py` 補現象錨點測試 + `RISK_REGISTRY` 登記 R-024。

**Stage B（引擎回填，全 advisory/shadow，零 strict）**：
- 新增 `gov/`（`__init__.py` / `utils.py` / `preflight.py` / `assertions.py` / `scan_secrets.py`）——**AOV 自包含快照**（2026-05-31，複製自 skills-governance，非 live 引用）。
- 新增 `governance_config.yaml`（preflight profiles fast/full + 密鑰 patterns）。
- `gov/preflight.py`：blocking/warning 分級 + 防遞迴 `GOV_PREFLIGHT_RUNNING`，CLI 末行印 X4-J 免責。
- `gov/assertions.py`：4 型斷言（exists/contains/absent/task）+ is_env 降噪 + lint_guards + `--allow-skip` + CLI 末行免責。
- `gov/scan_secrets.py`：.env 比對 + 特徵聯集，**絕不回傳真值**。
- `dev_claude.ps1` 加 `# allowlist-secret`（chatones proxy token，非官方 key，B4 掃描的 false positive）。

**驗證指令**（接手可自行覆驗）：
```
py -m pytest tests/ -q                        # 應 308 passed
py -c "import sys;sys.path.insert(0,'.');from gov.preflight import run_profile;print(run_profile('fast')['summary'])"  # ✅ preflight 通過
```

---

## 3. 🎯 P103.1 你要接手的核心：metrics 議題收尾

### 3.1 釐清結論（已完成，主公已定方向）

**問題**：`~/.claude/skill_metrics.jsonl` 從未生成（11 個 `.agent/skills/*/` 的 metrics 一直是空）。

**兩層根因**（已查證）：
1. **Claude Code hooks 記不了**：`PostToolUse` 的 `matcher:"Skill"` 目前不觸發（官方 issue #43630），payload 無 `skill_name`（issue #22655「不規畫」），Stop hook 要自己解析 transcript（無 duration、成本高）。
2. **更根本**：AOV 的 `.agent/skills/*/__main__.py` 是**手動 CLI 工具**（`py __main__.py "query"`），`record()` 接在 `_run_with_metrics()` 的 `if __name__=="__main__"`。但這些 skill 實際**多是「對話內由 Claude 讀 SKILL.md 模擬觸發」，不是 shell 跑程式** → 根本沒有執行點可記 metrics。

**關鍵「我以為」（G2-3）**：藍圖以為「metrics 空 = import 接線 bug → hooks 可修」；實情是「skill 不以程式執行 → hooks 也救不了」。`record()`+`__main__` 接線**沒壞**，是「設計前提（CLI 程式）vs 實際用法（對話模擬）**錯配**」。

**主公裁示（2026-05-31）**：**關閉 R-024，承認設計限制**（不強行做做不出來的 hooks 方案）。

### 3.2 待執行三動作（P103.1 收尾，純文件、可逆）

**動作 1：寫 postmortem**
- 路徑：`docs/postmortems/2026-05-31-phase-103.1-metrics-design-mismatch.md`
- 格式參考：`docs/postmortems/2026-05-14-phase-72-metrics-and-m3m4-stitching.md`（有「症狀/根因/以為清單/修法/教訓」結構）
- 必記：上述「我以為」+ 通則化教訓 →
  > **「移植他處的『根因診斷』不能照搬結論，要先驗證目標環境的實際前提。」**（Evidence-first 在動筆寫 hooks 計畫書前就擋下了錯誤方向。）
- 嚴重度：B（治理收尾，不影響主線）。

**動作 2：關閉 R-024**
- 檔案：`docs/RISK_REGISTRY.md`
- R-024 現在在「開放風險（Open）」section（約第 21 行，標題 `### R-024：skill metrics 永不生成...`）。
- 依 SOP（檔案第 9-15 行）：把整個 R-024 區塊從 Open **移到「已關閉風險（Closed）」section（第 297 行）**，狀態欄改含「已」或「Closed」，補上結論：「非 bug，是設計前提錯配；hooks 不適用，accepted 為已知設計限制；接手者若要 metrics 需另議觸發機制重設計。」
- 移完跑 `py scripts/governance_doctor.py --repo-root .` 確認無 GOV### 報錯。

**動作 3：TASK_HISTORY 追加 P103.1**
- **鐵律**：用 `cat >> "TASK_HISTORY.md" << 'EOF'`（bash），**不可用 Edit**（12004 行禁全讀）。
- 內容六塊：目標/觸發/釐清結論/三動作/狀態。標明「方案重定位、R-024 關閉、設計限制 accepted」。

---

## 4. ⏸️ 懸而未決（接手請向主公確認）

1. **AOV 全貌架構巡覽**：主公選了「派 2-3 個 Explore 子代理掃 pipeline（scrapers→analyzer→generator→reporter）/ 治理體系（24 checker/skills/hooks）/ docs 知識體系，回傳架構地圖」，但**尚未執行**（被換視窗指令打斷）。子代理**必須傳 TASK_HISTORY 禁全讀禁令**。
2. **「這次+全讀」TASK_HISTORY**：主公一度輸入觸發詞想全讀 TASK_HISTORY（12004 行），但隨即改要交接手冊覆蓋掉。**接手若主公重提，需二次確認才放行全讀**。
3. **P103 分支合併**：`P103-backfill-aov` 尚未 merge 回 main，待主公決定何時 PR/merge。

---

## 5. 🔒 鐵律 / 協議（必守，違反會被糾正）

- **TASK_HISTORY.md 禁全讀**（12004 行）：查→`grep -n "^### " TASK_HISTORY.md` 找錨點→`Read offset:N limit:200`；寫→`cat >> ... << 'EOF'`；一次對話最多查 3 個 Phase；子代理必傳此禁令。觸發詞「這次」+「全讀」+二次確認才放行。
- **模型協議**（記憶 `feedback-model-switch-reminder`）：**寫計畫書/搞計畫前主動提醒主公切 Opus**；執行階段預設 Sonnet 省成本；遇偵錯模糊/跨系統/新架構/安全/不可逆主動喊「建議升 Opus」。P103 實證：Opus 規劃→Sonnet 執行可行。
- **環境**：**必須用 `py` launcher**，不要用 `python`（指向 WindowsApps Store stub，非互動空退出 exit 49）。Python 3.10.8 + pytest 9.0.3。
- **git**：push / 不可逆動作前**先問主公**；commit 訊息結尾加 `Co-Authored-By: Claude <模型> <noreply@anthropic.com>`。
- **計畫書**：須過 `py scripts/lint_phase_plan.py <檔>`（現驗 **11 視角** X4-A~K + M2 ≥5 條含 ≥2 S 級；S 級攻擊力欄要寫 `**S**` 或「S 級」才被 lint 認得）。
- **資安最高**：機敏值一律 `.env` + 佔位符，絕不進 git；推送前掃描。

---

## 6. 🗺️ 關鍵檔案地圖

| 用途 | 路徑 |
|---|---|
| P103 凍結計畫書 | `docs/P103_BACKFILL_AOV_PLAN.md` |
| 回填引擎（已裝） | `gov/`（utils/preflight/assertions/scan_secrets）+ `governance_config.yaml` |
| A2 去重共用函式 | `scripts/governance_utils.py` |
| 風險登記（R-024 待關） | `docs/RISK_REGISTRY.md`（Open 約 21 行 / Closed 297 行）|
| postmortem 範例 | `docs/postmortems/2026-05-14-phase-72-metrics-and-m3m4-stitching.md` |
| 回填總脈絡（開場讀）| `D:/skills-governance/docs/BACKFILL_AOV_HANDOFF.md` |
| 施工藍圖（融合 schema）| `D:/Coding Project/Hermes-Agent-Dev-Project/docs/gov-port/G0_DEEPDIVE_BLUEPRINT.md` |
| 引擎源（快照來源）| `D:/skills-governance/gov/` |

---

## 7. 📋 開新 session 第一個 prompt（可直接複製貼上）

> 阿喜你好。這個 session 接手 **P103.1（GOV-PORT 回填 AOV 的 metrics 議題收尾）**。
> 請先依序讀：①`P103_SESSION_HANDOFF.md`（本交接手冊，自包含）②`D:/skills-governance/docs/BACKFILL_AOV_HANDOFF.md`（回填全脈絡）。
> P103 引擎回填已完成並 push（分支 P103-backfill-aov，308 tests 綠）。P103.1 結論已定：**metrics 用 hooks 記不了（設計錯配），關閉 R-024、承認設計限制**。
> 你要做三個純文件動作：①寫 postmortem 記錄這個「我以為」②把 R-024 從 RISK_REGISTRY 的 Open 移到 Closed ③TASK_HISTORY 追加 P103.1（cat>>heredoc，禁全讀）。
> 守鐵律：用 `py` 不用 `python`；TASK_HISTORY 禁全讀；push 前問我；要搞計畫時提醒我切 Opus。做完給我看。

---

*接手順利。P103.1 是 GOV-PORT 回填的小尾巴——誠實面對「metrics 設計錯配」這個發現，把它記成 postmortem 教訓即可，不要強行做不通的 hooks 方案。*
