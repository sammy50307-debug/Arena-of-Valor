# Postmortem — P72 Metrics 基礎建設 + M3/M4 自動化的順序拼接

- **日期**：2026-05-14
- **範圍**：P72.0 / P72.1 / P72.2 / P72.3 / P72.4（連跑 5 個 Phase）
- **嚴重度**：B（治理基礎建設升級，不影響主線報告產出）
- **作者**：Opus 4.7（主公審核）

---

## 一、症狀（為何需要 P72 系列）

P71 收官（2026-05-11）達成 19/19 skill 全綠，但暴露三個結構性缺口：

1. **SKILL_HEALTH.md 是「靜態評分」**：health 等級靠 `gen_skill_health.py` 一次性掃描檔案，沒有「使用頻率 / 成功率 / 平均耗時」這類運行時數據可佐證。
2. **M3 跨 Phase 審查靠人工撈 postmortems**：每寫新 Phase 計畫書，要主公或 AI 手動讀過往 postmortems 找通則化規則，無自動化。
3. **M4 時效追溯協議在 P71.1 寫好了規則但無自動化**：規則寫在 PHASE_TEMPLATE，但「哪些 Phase 缺 blindspot」「B-NNN 規則有沒有真的反映到 PHASE_TEMPLATE」全靠人工巡檢。

---

## 二、根因分析

### 2.1 主因：治理規則的「規格→工具」斷層

P71 系列建立了大量規則（S1 schema / V1 觸發塊 / M1-M4 協議 / Pre-flight 體檢），但只有 S1/V1 有 lint 工具，M3/M4 規則沒有對應自動化腳本。**規則密度增加 → 人工巡檢負擔指數成長 → 規則退化（G5 抗熵實證）**。

**核心教訓**：
> **「治理規則的『規格』與『工具』必須同 Phase 落地，否則規則半衰期不超過 5 個 Phase」**

### 2.2 次因：可觀察性缺位

P71 完成「rule-as-code = enforcement-as-code」（G6 通則），但 enforcement 結果本身沒有度量。SKILL_HEALTH 只看「結構是否完整」，看不到「實際是否被使用」。

### 2.3 次因：技術債靜默累積

P72 連跑 5 個 Phase 期間，`test_dynamic_focus` 3 個 pre-existing 失敗從未處理，每個 Phase 都標「無回歸」就放過。

---

## 三、「以為」清單（G2-3）

1. **以為** 11 個 skill 全接上 `_run_with_metrics()` 後，metrics JSONL 會立刻有數據 → 實際上要等使用者真正呼叫才會 log，dashboard 初期全是 `--`
2. **以為** M3/M4 自動化能完全取代人工 → 實際上 `--sync-rules` 的 anchor heuristic 召回率低（測試發現「已涵蓋 0 條」明顯低估 PHASE_TEMPLATE v1.1 既有規則）
3. **以為** 設好 `.github/workflows/backup-mirror.yml` 就有第二 remote 自動備份 → 實際上 `BACKUP_REMOTE_URL` secret 沒設，CI 是 no-op
4. **以為** P72 五個 phase 連跑是高效 → 實際上累積了積欠：test_dynamic_focus 從 P72.0 拖到 P72.4 都沒解決
5. **以為** PowerShell 與 bash heredoc 行為一致 → 實際上 PowerShell 不支援 `cat << EOF`，多次 commit 卡在 here-doc syntax error，最終靠 `cat` + 暫存檔繞過
6. **以為** PHASE_TEMPLATE.md 是自動化好對象 → 實際上是凍結文件（X1 不可逆），P72.3 改設計成「只印建議、不自動寫入」

---

## 四、修法時程（P72.0 → P72.4）

| Phase | Commit | 修法 | 效果 |
|---|---|---|---|
| P72.0 | `0894548` | `skill_metrics_logger.py` + 11 × `_run_with_metrics()` + `gen_skill_metrics.py` + 16 單測 | metrics 基礎建設落地 |
| P72.4 | `7855714` | `gen_skill_health.py` 偵測 metrics → 展開 11 欄表格（含 O1/O2/O3）| SKILL_HEALTH 從靜態評分升級為動態看板 |
| P72.1 | `b6119d2` | `scripts/backup_push.py`（local CLI）+ `.github/workflows/backup-mirror.yml` | 雙 remote backup 工具就緒（CI no-op 待設 secret）|
| P72.2 | `a1492db` | `scripts/cross_phase_review.py` 從 postmortems 抽 B-NNN 通則化 + 教訓 + 以為清單 | M3 跨 Phase 審查自動化 |
| P72.3 | `ce904f5` | `scripts/m4_track_blindspots.py`（`--status` / `--scaffold` / `--sync-rules`）+ 21 單測 | M4 時效追溯自動化（含 X1 不可逆隔離）|

### 累積測試成績
- **全套**：109 passed / 3 pre-existing failed（test_dynamic_focus 事件迴圈隔離，全 P72 無回歸）
- **P72.0**：16 單測 / **P72.3**：21 單測

---

## 五、預防機制（已部署）

| 機制 | 作用 | 觸發點 |
|---|---|---|
| `skill_metrics_logger._run_with_metrics()` | 每次 skill `__main__.py` 呼叫自動 log（calls/duration/success）| Skill 執行時 |
| `gen_skill_metrics.py` CLI | 從 JSONL 聚合 O1/O2/O3 數據 | 手動 / CI |
| `gen_skill_health.py` 升級 | 偵測 metrics 自動展開 11 欄 dashboard | GHA `skill_health.yml` |
| `cross_phase_review.py` | M3 跨 Phase 通則化規則自動撈取 | 新 Phase 計畫書 §M3 段落 |
| `m4_track_blindspots.py` | M4 三項命令（`--status` / `--scaffold` / `--sync-rules`）| Phase 收官前驗收 |
| `backup_push.py` + `backup-mirror.yml` | 雙 remote 自動 backup 工具就緒 | local CLI / GHA push |

---

## 六、通則化（G6 → P73+ 適用）

1. **新治理規則必須同 Phase 落地對應自動化工具**（規格-工具同步原則，避免 G5 退化）
2. **任何「自動化建議性決策」必須與「自動化執行」明確切割**（X1 可逆性保證；P72.3 `--sync-rules` 只印不寫的範式）
3. **可觀察性 metrics 必須有 size cap / 滾動策略**（append-only 跑久必爆）
4. **跨平台腳本（bash/PowerShell）必須在開發機實測兩端**（here-doc 不互通是已知陷阱）
5. **積欠 ≥ 3 個 Phase 的測試失敗必須升級為獨立 Phase 處理**（不能再靠「pre-existing 不阻擋」放行）

---

## 七、配對盲點

詳見 [`2026-05-14-phase-72-blindspots.md`](./2026-05-14-phase-72-blindspots.md)（B-005 ~ B-008，4 條）。
