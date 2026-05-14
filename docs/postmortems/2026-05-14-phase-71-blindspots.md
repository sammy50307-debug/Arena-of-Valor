# P71 Blindspots — M4 首次套用

> **M4 協議**（P71.1 定義）：每個 Phase 收官後寫此檔，記錄「計畫書沒寫但實際撞到的問題」≥ 3 條，通則化後加入 PHASE_TEMPLATE 體檢清單並升版。
>
> **本檔狀態**：P71 是 M4 協議首次套用的 Phase，結果已驅動 PHASE_TEMPLATE v1.0 → v1.1 升版（P71.1，2026-05-09）。

- **Phase**：P71（P71.0 ~ P71.10）
- **日期**：2026-05-14
- **對應 Postmortem**：[2026-05-14-phase-71-skill-deployment-decay.md](./2026-05-14-phase-71-skill-deployment-decay.md)

---

## 計畫書沒寫、實際撞到的問題

### B-001：跨專案 Shared Skill 雙端漂移無偵測機制

**計畫書原寫**：P71.5 建立 `~/skills-shared/` 作為跨專案 skill 的獨立 repo。

**實際撞到**：P71.7 SKILL_HEALTH 掃描後發現，6 個 shared skill 在 Gemini 端已被更新（補 S1 schema），本地端從未同步，雙端 diff 無人知曉。原計畫書沒有「雙端 diff 偵測」的 exit criteria 或 checkpoint。

**通則化**：
> 任何建立「多端版本」架構的 Phase，Exit Criteria 必須包含「雙端 diff = 0」的機械化驗證項。

**已加入**：PHASE_TEMPLATE v1.1 STR9 §entry_points 機械化 checklist。

---

### B-002：Orphan Skill 生命週期管理真空

**計畫書原寫**：P71.9 處置 8 個 orphan skill（升級 or 歸檔）。

**實際撞到**：處置過程發現 orphan 的定義不清楚——「孤兒」到底是「沒有 registry 紀錄」、「registry 有但 SKILL.md 過舊」、還是「目錄存在但從未使用」？三種情況需要不同處置方式，但計畫書只寫了「視必要性補齊或豁免」，導致 P71.9 當下需要臨時請主公拍板 D5 決策。

**通則化**：
> 任何 Phase 涉及「生命週期狀態轉換」（active/archived/orphan）的 skill/模組，計畫書必須明定：(a) 狀態定義、(b) 每種狀態的轉換條件、(c) 轉換執行者（AI 或主公拍板）。

**已加入**：PHASE_TEMPLATE v1.1 M1 視角 X4-I「主公可見性」──哪些轉換需主公拍板須明文標注。

---

### B-003：`test_skill.py` 未列入 Phase 開工必要條件

**計畫書原寫**：P71.3 補齊 `__main__.py` 讓 skill 可從終端執行。

**實際撞到**：補完 `__main__.py` 後，P71.7 SKILL_HEALTH 仍顯示部分 skill 為 🔴，原因是 health 評分加入「test 存在」這個維度，而計畫書完全沒提 `test_skill.py`。ui-ux-pro-max 一直到 P71.9+ 才補上，成為全綠里程碑的最後一塊拼圖。

**通則化**：
> 任何新增或升級 skill 的 Phase，Exit Criteria 必須明列「`test_skill.py` 存在且通過 ≥ 5 個測試案例」。不存在測試 = skill 未完成。

**已加入**：PHASE_TEMPLATE v1.1 STR9 §entry_points checklist 第 5 欄「test_skill.py 存在」。

---

### B-004：`deployed_to` 欄位無 lint 強制

**計畫書原寫**：S1 schema 定義了 `deployed_to` 欄位。

**實際撞到**：P71.8 將 smart-task-router 升級為 in-use 時，`deployed_to` 遺留為空陣列 `[]`，lint 不阻擋（因為 lint 只驗 schema 格式，不驗欄位值），一直到 P71.10 收官盤點才發現。

**通則化**：
> Schema lint 要同時驗「欄位存在」與「欄位值有意義」。`deployed_to: []` 對 in-use skill 應視為 lint warning（或 error）。

**待加入**：`lint_skill_registry.py` V1-6 check（planned for P72+）。

---

### B-005：Phase 計畫書中「主公人工裁決點」標記不足

**計畫書原寫**：P71.8 說「7 個 diff 裁決完畢」。

**實際撞到**：裁決過程需要主公逐一看 diff 並選方案（A/B/C），但計畫書只有一行表格，沒有說明「裁決格式是什麼」、「AI 提供哪些資訊」、「主公需要花多少時間」。實際執行時 AI 需臨場設計裁決表格，造成一個子任務就用掉整個視窗。

**通則化**：
> 任何計畫書中含有「主公人工裁決」的任務項目，必須在計畫書中預估「裁決點數量 × 預計每點時間」，並說明「AI 提供的資訊格式」，以便主公評估視窗成本。

**已加入**：PHASE_TEMPLATE v1.1 M1 視角 X4-G「主公個人視角」規定含主公決策點的任務必須帶時間估計。

---

## 體檢清單升版摘要

| 版本 | 升版內容 | 驅動 Phase |
|---|---|---|
| v1.0 | 初版（63 維度框架 + 17 層稽核 + M1 九視角 + M2 紅藍對抗）| P71.0 之前 |
| **v1.1** | + STR9（Skill 收官 entry_points 機械化 checklist）+ STR10 Pre-flight 體檢 + X4-I「主公可見性」視角 | **P71.1（2026-05-09）** |
| v1.2（待議）| + `deployed_to` lint 強制 + Orphan 狀態定義章節 | 計畫中（P72+）|

---

## 給下一個 Phase 的提醒

1. **B-001**：新建任何多端架構 → 計畫書必含雙端 diff 驗證 exit criteria
2. **B-002**：狀態轉換任務 → 明文定義每種狀態 + 轉換責任人
3. **B-003**：Skill 新增/升級 → `test_skill.py` 是 done 的必要條件，不是加分項
4. **B-004**：Schema 擴充 → lint 要同時驗格式 + 值有意義
5. **B-005**：人工裁決點 → 預估點數 + 時間，方便主公分配視窗
