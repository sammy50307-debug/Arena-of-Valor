# 技術債登記簿 (Tech Debt Registry)

> 受 Phase 64.1 M1（可維護性層）建立，供日後「砍/換/升」決策用。

---

## Phase 64 — Token 優化四層防線（13 元件）

| # | 元件 | 路徑 | 描述 | 建立日期 | 風險 |
|---|---|---|---|---|---|
| 1 | lookup_guide | `memory/history_lookup/lookup_guide.md` | TASK_HISTORY 查詢工作流程指南 | 2026-05-01 | 若查詢模式改變需更新 |
| 2 | phase_map | `memory/history_lookup/phase_map.md` | Phase 索引表（供 Grep+offset 定位） | 2026-05-01 | 每 Phase 需手動 append |
| 3 | WIP_PHASES | `memory/history_lookup/WIP_PHASES.md` | 進行中 Phase 清單 | 2026-05-01 | 收官時需手動移除 |
| 4 | history-tail.sh | `scripts/history-tail.sh` | 擷取 TASK_HISTORY 末尾 Phase | 2026-05-01 | 依賴 `grep -n "^### "` 格式 |
| 5 | finalize-phase.sh | `scripts/finalize-phase.sh` | Phase 收官自動化腳本 | 2026-05-01 | 有互動式 `read`，自動化不友善 |
| 6 | check_history_budget.sh | `.claude/check_history_budget.sh` | PreToolUse hook：查詢計數器 | 2026-05-01 | 依賴 `$CLAUDE_TOOL_INPUT` 環境變數 |
| 7 | setup-claude-hooks.sh | `scripts/setup-claude-hooks.sh` | Hook 初始化腳本 | 2026-05-01 | 手動執行，CI/CD 未整合 |
| 8 | RULES_REGISTRY | `docs/RULES_REGISTRY.md` | 規則登記簿 | 2026-05-01 | 需與實際規則保持同步 |
| 9 | MEMORY.md 鐵律區塊 | `memory/MEMORY.md`（前 5 行） | 四層防線第二層 | 2026-05-01 | MEMORY.md 若被截斷會失效 |
| 10 | CLAUDE.md 禁令 | `CLAUDE.md` | 四層防線第三層 | 2026-05-01 | 跨模型切換需確認仍生效 |
| 11 | TASK_HISTORY 警語 | `TASK_HISTORY.md`（第 1-5 行） | 四層防線第四層 | 2026-05-01 | 若檔案被重建需補回 |
| 12 | UserPromptSubmit hook | `.claude/settings.json` | 四層防線第一層：計數器重置 | 2026-05-01 | settings.json 被覆蓋時失效 |
| 13 | feedback_history_lookup_workflow | `memory/feedback_history_lookup_workflow.md` | 查詢工作流記憶 | 2026-05-01 | 記憶老化需 G5-1 監控 |

---

## Phase 64.1 補強元件（7 項）

| # | 元件 | 路徑 | 描述 | 建立日期 | 風險 |
|---|---|---|---|---|---|
| 1 | rule-decay-check.sh | `scripts/rule-decay-check.sh` | G5-1 規則退化 90 天偵測 | 2026-05-03 | 依賴 git log + py -3；路徑改變需更新 CLAUDE_MEMORY_DIR |
| 2 | rule_usage_index.json | `data/rule_usage_index.json` | 規則使用率索引（每日更新） | 2026-05-03 | 自動生成，損毀後下次掃描自動重建 |
| 3 | rule_decay.log | `logs/rule_decay.log` | 退化掃描日誌（append only） | 2026-05-03 | 長期運行後需月歸檔，否則無限成長 |
| 4 | test_check_history_budget.sh | `tests/test_hooks/test_check_history_budget.sh` | check_history_budget hook 測試 | 2026-05-03 | 需搭配 bash 環境 |
| 5 | test_history_tail.sh | `tests/test_hooks/test_history_tail.sh` | history-tail 測試 | 2026-05-03 | 依賴 mktemp（Linux/Mac/WSL/GitBash） |
| 6 | test_finalize_phase.sh | `tests/test_hooks/test_finalize_phase.sh` | finalize-phase 測試 | 2026-05-03 | 同上 |
| 7 | test_user_prompt_submit.sh | `tests/test_hooks/test_user_prompt_submit.sh` | UserPromptSubmit hook 測試 | 2026-05-03 | hook command 字串若改變需同步更新測試 |

---

## 已知長期技術債

| 項目 | 描述 | 優先級 |
|---|---|---|
| R20 | history-trend-query：markdown 空 cell 問題 | ⏳ P61.1 |
| R23 | history-trend-query：cache 回 deepcopy | ⏳ P61.1 |
| R24 | history-trend-query：cache mtime 失效 | ⏳ P61.1 |
| R29 | history-trend-query：fuzzy threshold 需實戰資料調整 | ⏳ 累積資料後 |
| G5-1 logs | rule_decay.log 長期需月歸檔機制 | ⏳ 90 天後 |

---

*本文件由 Phase 64.1 M1 建立，受可維護性層（層 13）保護。每個新 Phase 的元件清單應在收官時 append 至此。*
