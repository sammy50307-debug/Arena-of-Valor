# Postmortem — P71 Skill Deployment Decay（技術債積壓與批次修復）

- **日期**：2026-05-14
- **影響**：P71.0 盤點時，19 個 skill 中 🔴 7 個不可用、🟡 7 個部分問題，僅 🟢 5 個健康
- **嚴重度**：A（核心功能架構性損壞，但不影響現有報告產出主線）
- **作者**：Sonnet 4.6（主公審核）

---

## 一、症狀

P71.0 盤點（2026-05-09）發現 skill 體系全面退化：

- 19 個 skill 僅 5 個健康（🟢 26%）
- 7 個無法執行（🔴 37%）：缺 `__main__.py`、SKILL.md 格式過舊、未登記 registry
- 7 個部分問題（🟡 37%）：跨專案 shared skill 與本地版本 SKILL.md 有 diff
- 1 個 orphan（已廢棄但沒清除）

---

## 二、根因分析

### 2.1 主因：rule-as-code 無 enforcement-as-code

P43-P50 時代建立「全域部署」傳統，當時靠人工自律維護 skill 狀態。P51+ 隨著 Phase 增多，新增 skill 時沒有機械化阻擋機制確認部署規格是否完整：

- 沒有 pre-commit hook 驗證 SKILL.md schema
- 沒有 CI 自動偵測 `__main__.py` 缺失
- 沒有 SKILL_HEALTH 儀表板可見化退化狀態

**核心教訓（G6 通則化）**：

> **「寫在指令檔但沒機械化阻擋的規則，半衰期約 8-10 個 Phase」**

### 2.2 次因：跨專案 skill 雙端漂移

P71.5 建立 `~/skills-shared/` 獨立 repo 後，7-9 個跨專案 skill 變成需要雙端維護（本地 + shared repo），但當時沒有 diff 偵測機制。P71.8 之前，6 個 shared skill 在 Gemini 端被更新（補 S1 schema），但本地版本從未同步。

### 2.3 次因：orphan skill 缺乏生命週期管理

部分 skill 在開發過程中被廢棄（如 `history-lookup`），但沒有正式 archive 流程，造成 registry 與目錄狀態不一致。

---

## 三、「以為」清單（G2-3）

1. **以為** SKILL.md 有被讀到就等於有被遵守 → 實際上沒有 lint 就等於沒有強制
2. **以為** 跨專案 skill 在 Gemini 端更新後本地也會知道 → 實際上雙端完全獨立，沒有任何通知機制
3. **以為** 7 個 🔴 skill 只是小問題 → 實際上其中 3 個是完全無法從終端執行（缺 `__main__.py`）
4. **以為** orphan skill 閒置即無害 → 實際上拖著舊格式 lint warning、混淆健康看板
5. **以為** `deployed_to` 欄位不填不影響功能 → 實際上造成 registry 不完整，無法追溯部署範圍

---

## 四、修法時程（P71.0 → P71.10）

| Phase | 修法 | 效果 |
|---|---|---|
| P71.0 | 盤點：SKILL_INVENTORY.md | 🟢 5 / 🟡 7 / 🔴 7 可視化 |
| P71.1 | S1 schema 定義 + lint_skill_registry.py + PHASE_TEMPLATE Pre-flight 體檢 | 機械化阻擋基底建立 |
| P71.2 | CLAUDE.md / GEMINI.md 觸發協議 V1 + S2 | 觸發行為規範化 |
| P71.3 | 11 個 `__main__.py` + 終端執行章節 | 🔴 → 可執行 |
| P71.4 | deploy_skills.py + pre-commit hook + CI | 雙向同步工具化 |
| P71.5 | 8 shared skills → `~/skills-shared/` 獨立 repo | 雙端一致性架構 |
| P71.6 | smart-task-router 路由引擎重建（信心分數 + V1 觸發塊）| 路由功能恢復 |
| P71.7 | SKILL_HEALTH.md 自動生成 + GHA | 🟢 11 / 🟡 0 / 🔴 8（看板建立）|
| P71.8 | 6 shared skill Gemini↔本地 diff 裁決 | 🟢 11 → 18（雙端一致）|
| P71.9 | 7 orphan 處置（升級 in-use 或 archive）| 🟢 18 → 19 |
| P71.9+ | ui-ux-pro-max 補 test_skill.py | **🟢 19 / 🟡 0 / 🔴 0（史上首次全綠）** |
| P71.10 | deployed_to 修正 + R-009~011 登記 + Postmortem | 收官文件化 |

---

## 五、預防機制（已部署）

| 機制 | 作用 | 觸發點 |
|---|---|---|
| `lint_skill_registry.py` | S1 schema 驗證 + V1 trace check | pre-commit hook + CI |
| `test_skill.py` per skill | 6 維度自動測試（schema/CLI/V1/when_to_use/範例/輸出）| CI |
| `gen_skill_health.py` | SKILL_HEALTH.md 自動更新 | CI (skill_health.yml) |
| `deploy_skills.py` | 雙向同步本地 ↔ shared | 手動 / CI |
| STR9（Exit Criteria）| 新增/更新 skill 收官前機械化 checklist | Phase 收官前必過 |
| Pre-flight 體檢（STR10）| M1+M2 九視角體檢 | Phase 計畫書凍結前 |

---

## 六、通則化（G6 → P72+ 適用）

1. **任何新 skill 提交必須同時包含 `__main__.py` + `test_skill.py`**（STR9 機械化阻擋）
2. **跨專案 shared skill 雙端 diff 必須在 Phase 收官前解決**（`deploy_skills.py --check`）
3. **`deployed_to` 欄位必填**（lint_skill_registry.py V1-6 check 待加）
4. **任何「規則寫在文件裡」的要求，必須同步建立 enforcement**（G6 通則：rule-as-code = enforcement-as-code）
