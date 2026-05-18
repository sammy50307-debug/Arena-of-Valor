# P77-P84 Daily Monitoring Reliability Program（總戰役計畫）

> 狀態：FROZEN STRATEGY
> 凍結日期：2026-05-16
> 目的：讓每日監測系統不只「現在能跑」，而是長期可用、壞了能定位、發布不誤導、資料可追溯。

---

## 1. 總目標

把 AOV 每日輿情監測系統從「靠檔名、慣例、fallback、人工 handoff 串起來」升級成具備下列能力的長期運維管線：

- 主鏈路 runtime bug 會 fail loud，不會被假資料掩護。
- 每次 daily run 有權威狀態來源。
- preview / production / backfill 有明確邊界。
- 報告產生不等於發布，必須通過 promotion gate。
- 壞資料可隔離，缺日可回放，失敗可定位。
- 新視窗只讀最小入口也能知道正確下一步。

---

## 2. 最終路線

| Phase | 名稱 | 核心目的 | 狀態 |
|---|---|---|---|
| **P77** | 止血 | 修主鏈路已知 bug：history、fallback、landing、report health | CLOSED（外部配額阻塞） |
| **P78** | 合約 / Manifest | 建 run manifest、schema、publish eligibility，先 shadow mode | CLOSED（P78.2 已落地） |
| **P79** | Doctor | 建 `system_doctor.py`，統一本地與 CI 診斷 | CLOSED（2026-05-17：CI advisory 實跑驗證完成） |
| **P80** | Promotion / Atomic Write | candidate 通過驗證才 promote，寫檔原子化 | CLOSED（2026-05-17：P80.1 CI workflow_dispatch 實跑通過） |
| **P81** | Replay / Quarantine / Backfill | 支援單日回放、壞資料隔離、缺日補跑 | CLOSED（P81.3 已落地） |
| **P82** | Idempotency / Timezone | 同日重跑不污染，日期統一 Asia/Taipei | CLOSED（2026-05-17：run context + run_id/source_hash 已落地） |
| **P83** | Data Quality / Security | 資料品質 gate、HTML escape、LLM output contract | CLOSED（2026-05-17：data quality/security 已收官） |
| **P84** | Long-Term Governance | retention、SLO、handoff truth、risk registry、runbook | APPROVED（2026-05-18：P84.3 handoff truth 已完成，下一步 P84.4 governance） |

---

## 3. 跨 Phase 固定規則

| 規則 | 內容 |
|---|---|
| **Scope Control** | 每個 Phase 只處理一類根因；runtime、contract、doctor、promotion 不混修 |
| **Shadow First** | 新合約、新 doctor 先 advisory，不立刻阻擋 production |
| **Fail Loud** | 程式錯誤不可被 fallback 假裝正常 |
| **Promotion Only** | 生成報告不等於發布；合格 candidate 才能 promote |
| **Last Known Good** | 今日失敗時保留上一份健康 report，但必須標示資料日期 |
| **Privacy Redaction** | raw 原文、secret 不進 manifest/debug bundle |
| **Definition of Done** | 每 Phase 必跑測試、health、文件收官、diff check |
| **Handoff Truth** | 新視窗下一步只看 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap |

---

## 4. 戰略取捨

| 方案 | 優點 | 缺點 | 決策 |
|---|---|---|---|
| A. 只修 P77-P81 | 快速救火 | 長期治理不足，容易復發 | 不採為完整方案 |
| B. 鎖定 P77-P84，額外優化納入驗收條款 | 主鏈路、合約、觀測、發布、治理完整；不過度擴 Phase | 每個 Phase 計畫更嚴格 | **採用** |
| C. 繼續擴到 P90+ | 最完整 | 戰線太長，延誤修真 bug | 暫不採 |

---

## 5. Phase 詳細方向

### P77 止血

修目前已知讓系統不可信的問題：

- `HistoryResolver` 非 showcase 路徑 `archives` 未定義。
- fallback 假趨勢掩蓋程式錯誤。
- `index.html` 指向舊報告。
- preview report 混入 canonical / production 判斷。
- repo-state smoke test 缺失。

P77 只止血，不導入 manifest/schema/promotion gate。

### P78 合約 / Manifest

建立 run truth source：

- `data/runs/YYYY-MM-DD/run_manifest.json`
- schema version
- history source dates / missing dates
- cache hit / LLM calls
- degraded reasons
- publish eligibility

策略：先 shadow mode，只報告不阻擋。

### P79 Doctor

建立一鍵診斷：

- `scripts/system_doctor.py --local`
- `scripts/system_doctor.py --ci`
- BLOCKING / DEGRADED / ADVISORY 分級
- `docs/OPERATIONS_RUNBOOK.md`

### P80 Promotion / Atomic Write

發布安全化：

```text
candidate report -> validate -> health pass -> atomic promote -> update index
```

- `.tmp` 寫檔後 rename
- preview / production 分流
- validate/pass 後才能 update index

### P81 Replay / Quarantine / Backfill

- `scripts/replay_run.py --date YYYY-MM-DD`
- `data/quarantine/`
- CI debug bundle
- backfill report 明確標記

### P82 Idempotency / Timezone

- 報告日期以 Asia/Taipei 為準
- `run_id = date + mode + source_hash`
- 同日 rerun 可預期，不互相污染
- GHA UTC schedule 對映台北日期

### P83 Data Quality / Security

- 狀態：CLOSED（2026-05-17：data quality/security 已收官）
- 0 posts anomaly
- source health score
- LLM JSON contract
- HTML escape 防 XSS
- raw / sanitized analysis 邊界

### P84 Long-Term Governance

- 狀態：APPROVED（2026-05-18：P84.3 Handoff truth checker 已完成；下一步 P84.4 Risk registry / runbook governance）
- retention policy
- LLM cost / cache hit 監控
- SLO：連續 N 天無 production report 即升級
- handoff truth check
- risk registry 更新
- phase0 缺口處理

---

## 6. 全戰役 Definition of Done

每個 Phase 收官前至少完成：

- `git status -sb` 確認 dirty 範圍。
- `git diff --check` 通過。
- 相關測試或文件驗證通過。
- 不 stage unrelated untracked files。
- `NEXT_SESSION_HANDOFF.md` active bootstrap 更新到下一步。
- `TASK_HISTORY.md` 只 append 物理真相，不全檔編輯。
- Push 前必須先問主公。

---

## 7. 新視窗最小讀取策略

新視窗平常只需讀：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. active bootstrap 指定的當前 Phase 計畫

不需要每次讀：

- 全部 `TASK_HISTORY.md`
- 本總戰役全文
- 所有 phase memory
- 所有風險登記

若需要查歷史，只能 anchor search，不全讀。
