# 規則登記簿 v0.4

> 修改任一規則 → 對照本表掃一遍同步點 → 防止漏改

| 規則 | hook | MEMORY.md | CLAUDE.md | TASK_HISTORY 警語 | lookup_guide |
|---|:---:|:---:|:---:|:---:|:---:|
| 禁全讀 TASK_HISTORY | ✅ | ✅ | ✅ | ✅ | ✅ |
| 觸發詞「這次+全讀」 | ✅ | — | ✅ | — | ✅（詳版+正則）|
| 原子查詢守則 / 3-Phase 上限 | ✅ | — | ✅ | — | ✅（詳版） |
| 子代理禁令傳遞 | ✅ | — | ✅ | — | ✅ |
| Hook 狀態檔計數 | ✅（PreToolUse） | — | — | — | ✅（機制說明） |
| Bash heredoc 追加 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 失誤恢復 SOP | — | — | — | — | ✅ |

## 同步點清單（修規則時對照）

| 檔案 | 角色 |
|---|---|
| `.claude/settings.json` | UserPromptSubmit hook 注入鐵律文字 |
| `.claude/check_history_budget.sh` | PreToolUse 計數器 |
| `CLAUDE.md` | 子代理繼承的物理防線 |
| `memory/MEMORY.md` | auto-load 鐵律 4 行 |
| `memory/feedback_history_lookup_workflow.md` | 記憶：工作流要點 |
| `memory/history_lookup/lookup_guide.md` | 詳版規則 + 觸發詞正則 + SOP |
| `memory/history_lookup/phase_map.md` | Phase 索引地圖 |
| `memory/history_lookup/WIP_PHASES.md` | 進行中 Phase 清單 |
| `TASK_HISTORY.md`（第 1 行） | 物理硬碰警語 |
| `memory/feedback_startup_ritual.md` | 開局儀式第 7 項 |
