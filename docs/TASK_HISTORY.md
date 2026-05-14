
### P71.10 — Postmortem + R-009~011 風險登記（2026-05-14）

**目標**：P71 整體收官：補錄風險登記、產出 Postmortem + Blindspots 文件、修正 deployed_to 欄位。

**觸發**：NEXT_SESSION_HANDOFF.md P71.10 工作清單（P71.9 全綠收官後的最終收官步驟）。

**17 層稽核表（微 Phase，1-2 檔 S 級必填）**：

| 層 | 評估 |
|---|---|
| 1 代碼 | SKILL.md deployed_to 欄位修正（1 行）、RISK_REGISTRY 新增 3 筆 |
| 2 邏輯 | R-009/010 已解 → Closed；R-011 orphan lint → Open 豁免；均正確分類 |
| 4 測試 | 純文件 Phase，無邏輯可測 |
| 10 安全 | 無安全面向 |

**物理真相（完成項）**：

| 項目 | 結果 |
|---|---|
| `deployed_to` 修正 | `.agent/skills/smart-task-router/SKILL.md` `deployed_to: []` → `["claude-project"]` |
| R-009 登記 | RISK_REGISTRY.md — Closed（deployed_to 空，P71.10 修補）|
| R-010 登記 | RISK_REGISTRY.md — Closed（ui-ux-pro-max 無 test，P71.9+ 修補）|
| R-011 登記 | RISK_REGISTRY.md — Open（orphan lint warning，豁免觀察中）|
| Postmortem | `docs/postmortems/2026-05-14-phase-71-skill-deployment-decay.md` |
| Blindspots | `docs/postmortems/2026-05-14-phase-71-blindspots.md`（M4 首次套用，5 條盲點）|

**跨 Phase 學習（G6 + STR8）— P71.0 ~ P71.9 九段教訓**：

1. **P71.0**：盤點前可見性為零 → 教訓：任何體系健康狀態必須可量化、可視化
2. **P71.1**：先建 enforcement 才有後面所有自動化 → 教訓：rule-as-code 必配 enforcement-as-code
3. **P71.2**：觸發協議不透明讓 AI 自由心證 → 教訓：觸發行為必須有 V1 可見性標記
4. **P71.3**：`__main__.py` 缺失是最常見卡點 → 教訓：新 skill 必須 day-1 就有終端入口點
5. **P71.4**：手動同步必敗 → 教訓：deploy_skills.py 這類工具應在架構確定後即刻建立
6. **P71.5**：雙端架構需要 diff 偵測 → 教訓：多端版本 = 多端 lint，不能假設人工同步
7. **P71.6**：路由引擎 3 輪沒進展時應換模型 → 教訓：卡住判定要機械化，不能靠 AI 自覺
8. **P71.7**：SKILL_HEALTH 看板讓問題從「以為還好」變成「數字在那裡」→ 教訓：可觀察性優先
9. **P71.8/9**：批次裁決應預估時間給主公 → 教訓：人工裁決點要帶時間估計和格式設計

**P71 里程碑**：🟢 19 / 🟡 0 / 🔴 0（史上首次全綠，2026-05-11 達成）

**狀態**：✅ P71 全部收官（P71.0 ~ P71.10）

