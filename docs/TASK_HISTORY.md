
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

### P72.0 — Skill Metrics 基礎建設（O1-O3）（2026-05-14）

**目標**：為 skill CLI 執行建立可量化指標基礎，讓 SKILL_HEALTH 從「存在/缺失」升級到「活躍度/命中率」。

**對應優化點**：O1（執行時長）/ O2（失敗率）/ O3（Token 消耗）

**17 層稽核**（標準 Phase 14 檔 S+A 必過）：
- S 級全過：Code/Logic/Testing/Security
- A 級全過：Architecture（R-P72-02）/ Data（R-P72-01）/ Observability / Resilience / Maintainability / Documentation / Process
- B 級 N/A：無外部 API / 無 UI / 無部署 / 無 i18n

**物理真相**：
- scripts/skill_metrics_logger.py（NEW）— record() / load_all() / summarize()，寫至 ~/.claude/skill_metrics.jsonl
- scripts/gen_skill_metrics.py（NEW）— CLI reader，輸出 O1/O2/O3 表格
- 	ests/test_skill_metrics_logger.py（NEW）— 16/16 全綠
- .agent/skills/*/ 11 個 __main__.py（UPDATED）— 加 _run_with_metrics() wrapper
- scripts/gen_skill_health.py（UPDATED）— P71 全收官標記 + P72.0 行加入

**測試結果**：
- 	est_skill_metrics_logger.py：16/16 ✅
- 全套：91 tests = 88 passed + 3 failed（pre-existing test_dynamic_focus event loop 問題，非本次引入）
- **零回歸**

**風險登記**：
- R-P72-01：skill_metrics.jsonl 無限增長（延 P73 加輪換）
- R-P72-02：4層 parents[3] path 跳轉在目錄重組後可能失效（接受，目錄結構已固定）
- R-P72-03：O3 token 為 placeholder 0，P72.4 整合再填真實值

**退出條件**：✅ logger 建立 / ✅ 11 __main__.py 更新 / ✅ gen_skill_metrics.py 建立 / ✅ 16/16 測試全綠 / ✅ SKILL_HEALTH 更新

### P72.4 — metrics 接入 SKILL_HEALTH.md（2026-05-14）

**目標**：把 P72.0 建立的 O1/O2/O3 metrics 接入 SKILL_HEALTH Dashboard，health table 自動展開含 Calls / Avg ms / Fail% / Avg Tok 四欄。

**物理真相**：
- scripts/gen_skill_health.py（UPDATED）：
  - 頂層 import skill_metrics_logger（try/except graceful fallback）
  - load_metrics_stats() 讀 ~/.claude/skill_metrics.jsonl → summarize
  - _metric_cells() 回傳 (calls, avg_ms, fail_pct, avg_tok) display strings
  - has_metrics=True 時 table 自動展開 4 個 metrics 欄位
  - 新增「Metrics 狀態」區塊：無資料時顯示提示
  - P71-P72 進度看板加入 P72.4 行
- docs/SKILL_HEALTH.md（UPDATED）：重新生成，🟢19/19 維持

**測試**：88/91 passed（無新 regression；3 failures 為 pre-existing test_dynamic_focus 問題）

**退出條件**：✅ gen_skill_health.py 更新 / ✅ 生成腳本正常執行 / ✅ dashboard metrics 區塊正確顯示 / ✅ 零回歸

### P72.1 — 雙 remote 自動 backup（2026-05-14）

**目標**：為 AOV repo 建立雙 remote backup 基礎設施，防止 GitHub 誤刪或帳號被駭。

**物理真相**：
- scripts/backup_push.py（NEW）：push 當前 branch 到所有已設定 remote；1個 remote 時印出設定指南
- .github/workflows/backup-mirror.yml（NEW）：push main 時自動 mirror；無 BACKUP_REMOTE_URL secret 時 no-op

**待主公做的一次性設定**：
  1. 建立第二個 GitHub repo（不同帳號為佳）
  2. git remote add backup <url>
  3. GitHub repo → Settings → Secrets → BACKUP_REMOTE_URL = https://<TOKEN>@github.com/...
  4. 執行 py -3 scripts/backup_push.py 完成第一次 push

**使用方式**：
  `
  py -3 scripts/backup_push.py --status    # 查 remote 狀態
  py -3 scripts/backup_push.py --dry-run   # 模擬
  py -3 scripts/backup_push.py             # 實際 push 所有 remote
  `

**退出條件**：✅ 腳本建立 / ✅ CI workflow 建立 / ✅ dry-run 正常 / ✅ 設定指引清晰
