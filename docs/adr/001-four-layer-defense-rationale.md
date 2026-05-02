# ADR 001 — 四層防線架構設計決策

**日期**：2026-05-01（Phase 64 落地）  
**狀態**：✅ 已採納  
**作者**：主公（決策）+ Sonnet 4.6（設計草案）

---

## 背景與問題

Phase 63 之後，TASK_HISTORY.md 已超過 4000 行（≈135K tokens）。每次新對話若 Claude 全讀，token 消耗 = 135K，換算每天 3 次對話 = **每日燒約 405K tokens**。直接影響：
1. 對話費用飆升
2. Context window 壓縮後，有效推理空間縮小
3. Claude 靠「記憶」而非「查詢」，答案準確度反而下降

需要一個機制，在**不損失知識完整性**的前提下，壓制每次對話初始 token 消耗。

---

## 決策

採用「四層防線」架構，從四個不同方向同時限制 TASK_HISTORY 的誤讀行為：

### 層一：Hook 層（行為攔截）
- **實作**：`.claude/settings.json` 的 `UserPromptSubmit` hook  
- **效果**：每次對話啟動時，自動在 Claude 的 prompt 中注入鐵律提醒，並重置查詢計數器為 0
- **為何選此層**：Hook 是系統層的強制執行，不依賴 Claude 的「記憶」或「意願」

### 層二：MEMORY.md 鐵律（索引層）
- **實作**：`memory/MEMORY.md` 頂部加入 ⛔ 鐵律警語區塊  
- **效果**：MEMORY.md 是每次對話必讀文件，等同在 context 入口處設置路障
- **為何選此層**：MEMORY.md 會被 Claude Code 自動注入，等同系統提示的一部份

### 層三：CLAUDE.md 明文化（規則層）
- **實作**：專案 `CLAUDE.md` 明文列出 TASK_HISTORY 禁全讀規則  
- **效果**：所有與此專案互動的 Claude 實例均受約束
- **為何選此層**：CLAUDE.md 是 Claude Code 的 project-level system prompt，任何模型切換後仍有效

### 層四：TASK_HISTORY 警語（自我防衛層）
- **實作**：TASK_HISTORY.md 第 1-5 行加入明顯警語  
- **效果**：即使 Claude 真的嘗試全讀，第一眼就看到「禁止繼續」的指示
- **為何選此層**：Defense in depth — 前三層失效時的最後防線

---

## 考慮的替代方案

### 方案 A：拆分 TASK_HISTORY（棄選）
將 TASK_HISTORY.md 按 Milestone 切成多個檔案。  
**棄選原因**：破壞「編年史主權」準則（CHRONICLE_SOVEREIGNTY），且 grep 跨檔查詢更複雜。

### 方案 B：自動產生摘要版（棄選）
每 Phase 完成後自動產生 summary_history.md。  
**棄選原因**：違反「無損存檔協議」（LOSSLESS_TECH_ARCHIVE_PROTOCOL）——摘要永遠比原文損失資訊。

### 方案 C：單一 Hook 攔截（棄選）
只用 hook，不做 MEMORY/CLAUDE.md 層的冗餘設計。  
**棄選原因**：單點故障風險高；hook 失效時（settings.json 被覆蓋、模型切換）完全失守。

---

## 結果與量化效益

| 指標 | 改善前 | 改善後 |
|---|---|---|
| 對話初始 token 消耗 | ~135K | ~5-10K |
| 節省比例 | — | **92-96%** |
| Hook 觸發率 | — | 每次對話 = 100% |
| 誤全讀次數（Phase 64 後） | 每次 | 0 次（主觀回報） |

---

## 後續維護注意事項

1. **settings.json 變更**需先備份（`.before-p64.bak`），見 Phase 64.1 #6
2. **Rule decay 監控**：`scripts/rule-decay-check.sh` 每日掃描，確認四層規則未腐爛，見 Phase 64.1 #2
3. **Hook 測試覆蓋**：4 個 hook scripts 均有 `tests/test_hooks/` 覆蓋，見 Phase 64.1 #1

---

*此 ADR 受 STR6 跨 Phase 風險登記簿保護；若日後決定廢棄四層防線，需更新本 ADR 狀態並補錄 Postmortem。*
