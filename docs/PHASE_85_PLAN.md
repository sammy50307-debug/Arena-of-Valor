# Phase P85 計畫書 — Evidence-first + Quality-tiered Zero-Cost Reliability（凍結版）

> 草案日期：2026-05-19
> 凍結日期：2026-05-19
> 狀態：FROZEN
> 核准狀態：待主公核准 P86 才能改程式碼

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P85 |
| Phase 名稱 | Evidence-first + Quality-tiered Zero-Cost Reliability Plan |
| 凍結日期 | 2026-05-19 |
| 影響半徑 | P85 本身為標準文件 Phase（3-9 檔）；P86-P95 總戰役為重大範圍（10+ 檔） |
| 預估投入時數 | P85 1-2 h；P86-P95 合計 12-22 h，分段核准 |
| Token budget | P85 20K-35K；後續每 Phase 20K-60K |
| 負責模型 | GPT-5.3-Codex 高；若連 3 輪同錯誤或架構自相矛盾，提醒切 GPT-5.5 高/超高 |

## 0.1 核心結論

在「不增加 OpenAI API 費用」限制下，R-016 的主線解法不再是補 `OPENAI_API_KEY`，也不是立刻接一串免費 provider。主方案凍結為：

```text
Evidence-first + Quality-tiered Production + LLM Enrichment Queue
```

白話定義：

```text
每日報告先靠真實資料與本地 deterministic 分析產出 baseline production。
LLM 有額度時才做深度解讀。
LLM 沒額度時排隊補算，不讓 429 把整份報告降成 showcase_forced。
```

## 0.2 明確不採用的主線

| 不採用 | 原因 |
|---|---|
| OpenAI paid fallback 作為主線 | 主公明確不想增加 API 費用；P85 後不得再把「補 OPENAI_API_KEY」當預設下一步 |
| 多 Gemini key 輪替 | rate limit 通常與 project/plan 綁定，且有規避限制與治理風險 |
| 一開始接 Groq / Cloudflare / GitHub Models 進主鏈路 | 免費額度也有限，會增加 secrets、adapter、debug 複雜度 |
| 把 quota-limited 報告偽裝成 full production | 會誤導主公與 doctor/SLO |
| 繼續讓 LLM 成功成為 production 的必要條件 | 這正是 R-016 會反覆觸發 showcase_forced 的架構根因 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| R-016 修復方向 | Open：等待 production rerun / provider 診斷 | Open：P85 zero-cost plan frozen | R-016 仍未關閉，但修復方向改為零額外付費與 evidence-first | 主公明確表示不想多花 OpenAI API 錢，並要求凍結計畫 | AI 建立，主公核准 |
| P85 計畫 | DRAFT | FROZEN | 計畫已通過標準稽核，可作為後續 P86-P95 source of truth | 本文件完成 17 層、M1、M1.5、M2 與 handoff 同步 | AI 建立，主公已指示「來凍結」 |
| P86 動工 | 尚未開啟 | 待 APPROVED | P86 才開始動 runtime code；P85 不改程式碼 | 主公後續明確核准「開始 P86」 | 主公核准，AI 執行 |

## 1. 目標

凍結一套零額外付費的 R-016 長期修復計畫，讓 429 / quota limit 不再把每日報告整份降級成 `showcase_forced`，而是讓真實資料報告以可追溯品質分級持續發布，LLM 解讀改為可延後補算的增強層。

## 2. 觸發背景

P84.6 已把 production SLO blocking 與 landing stale 揭露為 `R-016`。R-016.1 修補 manifest sync，R-016.2 增加 provider diagnostics。2026-05-19 GitHub Actions 已顯示 `GEMINI_API_KEY configured` 與 `OPENAI_API_KEY missing`，主公接著明確表示不想多花 OpenAI API 錢。因此修復方向必須從「補付費 fallback」改成「Evidence-first 零成本韌性」。

本 Phase 只凍結方向與邊界，不改程式碼。任何 runtime 實作從 P86 起，需主公另行核准。

## 3. Entry Criteria

開工前必須全部達成：

- [x] P77-P84 reliability/governance 戰役已 CLOSED，R-016 保留 Open。
- [x] R-016.1 manifest sync / report-only backfill recovery 已完成並推送。
- [x] R-016.2 LLM fallback / secret diagnostics 已完成並推送。
- [x] 主公明確說明不想增加 OpenAI API 付費成本。
- [x] 主公允許對此優化計畫開多個 Phase 詳細規劃。
- [x] 主公已要求「來凍結」本計畫。

## 4. Exit Criteria

P85 達成全部才算凍結完成：

- [ ] `docs/PHASE_85_PLAN.md` 建立，狀態為 FROZEN，明列 P86-P95 順序。
- [ ] `NEXT_SESSION_HANDOFF.md` active bootstrap 指向 P85 FROZEN，避免新視窗回到補 OpenAI key 的舊路線。
- [ ] `docs/ACTIVE_OPERATION.md` 更新為 P85 FROZEN 短版真相。
- [ ] `docs/RISK_REGISTRY.md` 的 R-016 緩解策略更新為 zero-cost evidence-first 路線。
- [ ] `TASK_HISTORY.md` 追加 P85 凍結無損紀錄，不全讀既有歷史。
- [ ] `py scripts/lint_phase_plan.py docs/PHASE_85_PLAN.md` 通過。
- [ ] `git diff --check` 通過。
- [ ] 不修改 runtime code，不新增 provider secrets，不改 GitHub Actions schedule。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | P85 1-2 h；P86-P95 合計 12-22 h |
| 預估收益等級 | 高 |
| 收益描述 | 避免每日報告因 LLM quota 反覆退化成 showcase；降低 API 成本；讓 production 定義回到真實資料與可追溯品質 |
| ROI 結論 | 值得做；這是 R-016 從「補 provider」升級成「主鏈路不依賴 LLM」的必要治理轉向 |

## 6. P86-P95 凍結路線圖

| Phase | 名稱 | 主要目標 | 主要 Allowed Files | 驗收重點 |
|---|---|---|---|---|
| P86 | Gemini Model & Schedule Modernization | 移除即將退役或高風險 Gemini model 依賴，並評估把 daily schedule 移到配額重置後 | `analyzer/gemini_client.py`, `.github/workflows/daily_report.yml`, tests, docs | 不再依賴高停用風險模型；schedule 變更有文件與測試 |
| P87 | Report Core Contract | 定義不靠 LLM 也能 production 的最低真實報告標準 | `analyzer/run_manifest.py`, `reporter/`, `scripts/check_daily_report_health.py`, docs, tests | manifest 可判斷 core data 是否足以 production |
| P88 | Deterministic Local Analyzer | 建立本地情緒、關鍵字、英雄、平台、事件初判，不打外部 LLM | `analyzer/`, tests | 無 LLM 時仍產真實 baseline analysis |
| P89 | Quality Tier / Promotion Gate | 新增 `production_full`, `production_llm_partial`, `production_local_only`, `showcase_manual`, `error_fallback` | `main.py`, `analyzer/run_manifest.py`, `reporter/`, `scripts/system_doctor.py`, tests | 429 不再自動等於 `showcase_forced` |
| P90 | LLM Budget Ledger / Cooldown | 每日 LLM 預算、已用量、停損條件、429 cooldown | `analyzer/gemini_client.py`, `analyzer/cache_manager.py`, `data/runs/**/run_manifest.json`, tests | 超預算時停止打 API，不雪崩 |
| P91 | Cache / Dedupe / Top-N | 只分析新貼文與高價值樣本，提高跨日 cache hit | `analyzer/`, `scrapers/`, tests | LLM miss 顯著下降，重複 URL / 相似內容不重打 |
| P92 | Enrichment Queue / Replay | 超出預算的 LLM 任務排隊，配額恢復後補算並升級報告 | `scripts/`, `data/runs/`, `analyzer/`, tests | degraded 報告可被 replay 升級 |
| P93 | Free Provider Slot（Disabled by Default） | 留出免費 provider adapter 插槽，但預設關閉，不進主鏈路 | `analyzer/llm_provider_*`, config, tests | 沒有 key 時不報錯；啟用前需主公另核 |
| P94 | Doctor / SLO Reclassification | SLO 分清資料問題、程式問題、quota limit、品質分級 | `scripts/system_doctor.py`, `scripts/slo_checker.py`, runbook, tests | doctor 不再把 quota-limited 誤判成普通程式壞 |
| P95 | R-016 Closeout Verification | Actions 實跑、landing、manifest、doctor、SLO、runbook 全驗證 | docs, tests, Actions evidence | R-016 關閉或降級成外部配額觀察風險 |

## 7. 報告品質分級凍結

| Quality Tier | 定義 | 可上首頁 | 說明 |
|---|---|---|---|
| `production_full` | 真實來源資料足夠，LLM 單篇與 daily summary 均達標 | 是 | 理想每日狀態 |
| `production_llm_partial` | 真實來源資料足夠，部分 LLM 分析完成，其餘由本地分析補齊 | 是 | 需顯示 LLM coverage |
| `production_local_only` | 真實來源資料足夠，但 LLM 因 quota/cooldown 未執行；本地 deterministic 分析完成 | 是，需清楚標示 | 這是取代 `showcase_forced` 的核心 |
| `showcase_manual` | 主公或 CLI 明確要求展示模式 | 否，除非人工覆核 | 只能作 demo，不代表真實營運 |
| `error_fallback` | 主鏈路資料或程式錯誤，無法達 report core contract | 否 | 需 blocking doctor issue |

## 8. 17 層稽核表

> P85 本身為文件 Phase，但凍結的是 P86-P95 重大戰役，因此全 17 層列出。後續每個實作 Phase 仍需依影響半徑重做自己的稽核表。

| # | 層級 | 採用優化項 / 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | P85 不改 code；P86 起每 Phase 小步 patch | 戰役過大導致一次改太多 | 每 Phase 限定 Allowed Files，先測後收官 |
| 2 | 邏輯層 (Logic) | production 判定從 LLM 成功改成 report core contract + quality tier | local-only 被誤解成 full production | manifest 與報告明列 tier / coverage / reason |
| 3 | 架構層 (Architecture) | LLM 從主鏈路改成 enrichment layer | enrichment queue 侵入主流程 | queue/replay 與 daily report runtime 分離 |
| 4 | 測試層 (Testing) | 每階段補 unit + contract + doctor/SLO tests | 只靠 manual Actions 會漏回歸 | focused tests + full pytest + Actions 實跑證據 |
| 5 | 資料層 (Data) | raw/source/manifest 先完整保存，analysis 可延後 | local analysis 與 LLM analysis 混淆 | manifest 記錄 analyzer_type、coverage、pending queue |
| 6 | 可觀察性層 (Observability) | provider/quota/quality tier/coverage 都進 manifest | 主公只看到成功綠勾卻不知道品質下降 | report metadata + doctor issue code + runbook |
| 7 | 韌性層 (Resilience) | 429/cooldown 只降 LLM enrichment，不降整份報告 | 本地分析品質不足仍上首頁 | report core contract 設最低來源品質門檻 |
| 8 | 效能層 (Performance) | top-N、dedupe、cache-first 降低 LLM miss | 去重過度導致漏掉新聲量 | 去重保留 source count 與代表貼文列表 |
| 9 | UX/A11y 層 | quality tier 需在報告上可讀但不恐嚇使用者 | local-only 標示讓使用者誤會報告不可用 | 用「AI 解讀覆蓋率」而非錯誤口吻 |
| 10 | 安全層 (Security) | 不新增付費 secret；免費 provider 插槽預設關閉 | provider key / raw content 洩漏 | workflow 只印 configured/missing，不印值；adapter 不記 raw prompt |
| 11 | 部署層 (DevOps) | schedule/model 變更分 P86；CI 先 advisory | 改 schedule 造成 missed daily | 先 workflow_dispatch 實跑，再調 cron |
| 12 | 成本層 (Cost) | 零額外付費為硬邊界；budget ledger 限制外部 LLM 呼叫 | 免費 provider 被誤開成新成本或新 quota 依賴 | P93 預設 disabled，啟用需主公另核 |
| 13 | 可維護性層 (Maintainability) | tier/state machine 明文化 | 未來接手者不知道何時 promotion | PHASE_85 + runbook + doctor code mapping |
| 14 | 文件層 (Documentation) | handoff / active / risk / history 同步 | 新視窗讀舊 R-016 指令跑去補 OpenAI key | L1 bootstrap 明寫 no paid fallback |
| 15 | 流程層 (Process) | P85 FROZEN 後，P86 才能動 code | 計畫凍結後直接偷改 runtime | State machine 阻擋：FROZEN 不可改程式碼 |
| 16 | 隱私/合規層 (Privacy) | 真實玩家貼文資料仍需最小化與 retention | queue/replay 長期保存 raw prompt | P92 必須列 retention 與 redaction |
| 17 | i18n/在地化層 | TW/TH/VN 與 Asia/Taipei 日期語意保持 | quota reset 與報告日期跨時區誤判 | P86 使用明確 timezone 與官方 rate-limit 再查證 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 Performance 層 -> 已規劃 Observability 層。

## 9. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| P85 文件凍結 | 可逆 | 主公已要求凍結 |
| 後續 P86 model list / schedule 變更 | 可逆 | 需 P86 核准 |
| 後續 quality tier / promotion gate 變更 | 半可逆 | 需 P89 核准與 Actions 實跑 |
| 後續免費 provider adapter | 可逆 | 預設 disabled，啟用需另核 |
| 實刪資料、覆寫 production 歷史 | 不可逆 | 本戰役禁止，除非主公另行親口確認 |

### X2 盲區掃描

- 主公看不到的自動行為：quota cooldown 可能讓某些貼文暫時不進 LLM，需要 manifest 顯示 pending count。
- 中間檔產出：P92 queue 會產生待補算任務，必須有 retention 與 retry limit。
- 系統狀態變更：P89 後 landing 可能接受 `production_local_only`，需避免主公以為那等於 full AI report。
- 供應商邊界：免費 provider 插槽若啟用，會新增外部資料傳輸面，必須另做 security/privacy 審查。

### X3 時間敏感性

- 本計畫凍結日期：2026-05-19
- 本計畫過期日期：2026-06-02；因 Gemini model availability / pricing / rate limit 可能變動，P86 開工前必須二次查證官方文件。
- 風險記錄帶日期：已在 R-016 與 TASK_HISTORY 補錄。

### X4 多角度同行審查

| 視角 | 發現 |
|---|---|
| 主公視角 | 主公真正要的是不要再因 429 看到假展示報告，而不是增加新的 API 帳單；品質分級需用白話顯示。 |
| 世界頂尖駭客 / 紅隊攻擊者視角 | 主要攻擊面是 provider secrets、raw prompt logs、CI env 洩漏與 replay queue 保存原文；每個後續 Phase 必須避免輸出 secret 值與 raw prompt。 |
| 接手者視角 | 接手者只讀 handoff 與本文件要能知道：OpenAI paid fallback 不是主線，P86 才能開始改 code。 |
| X4-J 自動化建議性工具邊界 | 本計畫會引入 deterministic analyzer 與 quality tier，這些是規則判定，不等於人類語義真相；false negative 要在 P88 測試列明。 |
| X4-K 使用者端審查官 / Patric 型人格 | 使用者最容易誤解 `production_local_only` 是低品質或壞掉；報告 UI 需要清楚說這是真實資料、AI 解讀覆蓋率較低。 |

## 10. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | local-only production 被誤解成 full AI report | 中 | 高 | 業務 / UX | quality tier、coverage、reason 必須 user-visible 與 machine-readable |
| R2 | 本地 deterministic analyzer 品質不足 | 中 | 中 | 代碼可控 | P88 先做 baseline，不替代所有 LLM insight；只補最低 production contract |
| R3 | promotion gate 放太寬導致低品質報告上首頁 | 中 | 高 | 邏輯 | P87 先定 report core contract，再改 promotion |
| R4 | queue/replay 長期堆 raw data | 中 | 高 | 隱私 / 資料 | P92 必須含 retention、redaction、max retries |
| R5 | 免費 provider adapter 讓 debug 變複雜 | 中 | 中 | 架構 | P93 預設 disabled，不進主鏈路，不在 P86-P92 啟用 |
| R6 | Gemini 官方模型/配額資訊過期 | 中 | 高 | 外部依賴 | P86 開工前二次查證官方文件與當日日期 |
| R7 | 改 schedule 影響既有 daily rhythm | 低 | 中 | DevOps | 先手動 workflow_dispatch 實跑，cron 變更單獨驗收 |

高風險加權檢查（META4）：

- 高影響風險：R1、R3、R4、R6。
- 加權分數：8 分。
- 是否 >= 5 須請示主公：是；P85 僅凍結計畫，P86-P95 每個高風險實作 Phase 仍需主公核准後才動工。

## 11. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| S1 | P85 文件與 handoff 凍結 | 新視窗偏航補 OpenAI key | lint + handoff truth |
| S2 | P86-P89 主鏈路重定義 | 429 -> showcase_forced | unit/contract/Actions evidence |
| S3 | P90-P92 降呼叫量與補算 | 每日反覆撞 quota | manifest budget + replay evidence |
| S4 | P93-P95 備援插槽與收官 | 長期 provider / SLO 漂移 | doctor/SLO/runbook/closeout |

## 12. 影響檔案清單

P85 新增：

- `docs/PHASE_85_PLAN.md`

P85 修改：

- `NEXT_SESSION_HANDOFF.md`
- `docs/ACTIVE_OPERATION.md`
- `docs/RISK_REGISTRY.md`
- `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`
- `TASK_HISTORY.md`（append only）

P85 不修改：

- `analyzer/**`
- `reporter/**`
- `main.py`
- `.github/workflows/daily_report.yml`
- `scripts/**`
- `data/**`

## 13. Forbidden Work

- P85 不改任何 runtime code。
- P85 不新增或要求 `OPENAI_API_KEY`。
- P85 不接 Groq / Cloudflare / GitHub Models。
- P85 不調整 GitHub Actions cron。
- P85 不改 promotion gate。
- P85 不把 R-016 標記為 Closed。
- P85 不 stage unrelated untracked reports / scratch / backups。
- P85 不 git push；push 仍需主公明確確認。

## 14. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] P86-P95 任一階段使 production report 更少產出。
- [ ] quality tier 讓主公或使用者誤判報告品質。
- [ ] queue/replay 保存不該保存的 raw data。
- [ ] 免費 provider adapter 被誤開，產生非預期成本或隱私風險。
- [ ] 有任何「我以為 LLM 不在主鏈路，結果仍被 runtime 依賴」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-85-r016-zero-cost-reliability.md`

## 15. 外部資料再查證要求

P86 開工前必須重新查官方文件，不得沿用 P85 凍結當下印象：

- Gemini API rate limits：確認 RPD/RPM/TPM 與 reset semantics。
- Gemini API pricing / model availability：確認可用模型與 shutdown / deprecation。
- 若 P93 要評估免費 provider：只可用官方 docs，並記錄免費額度、條款、rate limit、資料使用邊界。

## 16. Pre-flight 多視角體檢（STR10）

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| X4-A 世界頂尖駭客 / 紅隊攻擊者 | 攻擊面包含 GitHub Actions secrets、provider key 洩漏、raw prompt logs、queue/replay 長期保存原文與 provider adapter SSRF 類濫用；最小緩解是 P85 禁止新增 provider，P92/P93 再逐項審查。 |
| X4-B 接手者視角 | 半年後接手者應從 handoff 讀到 P85 FROZEN，再讀本文件知道 P86 才能改程式碼，且 OpenAI paid fallback 不是主線。 |
| X4-C 災難情境 | 情境：quality tier 放太寬導致低品質 local-only 報告上首頁；緩解：P87 先定 report core contract，P89 才改 promotion gate。 |
| X4-D 5 年後視角 | 五年後 LLM provider 可能全換，但 evidence-first 架構仍有效，因為 production 依賴真實資料、manifest、quality tier，而不是單一模型。 |
| X4-E 終端 vs IDE | 本地 PowerShell 與 GitHub Ubuntu shell 的時區、encoding、cron 行為不同；後續命令需設定 UTF-8，schedule 改動要在 Actions 實跑驗證。 |
| X4-F 跨平台 Win/Mac/Linux | Windows 本機用 `py`，GitHub Actions 用 `python`；P86-P95 不得把 shell date 當核心邏輯，日期與 quota reset 要由 Python / manifest 明確表示。 |
| X4-G 主公個人視角 | 主公不想多花錢，也不想反覆看到假展示模式；計畫必須把「零額外付費」與「429 不等於報告壞」寫進入口。 |
| X4-H 觀測 / 治理 | R-016 不能靠口頭記憶關閉；doctor、SLO、manifest、handoff 都要能看出 quality tier、quota reason、LLM coverage。 |
| X4-I 主公可見性 | 主公看不到 cache miss、cooldown、queue pending 與 local analyzer 覆蓋率；後續必須把這些變成 manifest 欄位與報告 metadata。 |
| X4-J 自動化建議性工具邊界 | deterministic analyzer 與 quality tier 都是啟發式判斷，可能漏掉反諷、跨語言梗與社群暗語；P88 必須明列 false negative 測試。 |
| X4-K 使用者端審查官 / Patric 型人格 | 報告若顯示 `production_local_only` 但沒有白話說明，使用者會以為資料壞了；UI/metadata 必須說明真實資料足夠，只是 AI 解讀覆蓋率較低。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| Jarvis 型總控 | 固定必看 | 目標、邊界、派工、下一步是否清楚 | 觸發；P85 只凍結計畫，P86 才能動工 |
| Ken 型紅隊 / 技術長 | 固定必看 | 技術假設、安全邊界、權限、secrets、CI/CD | 觸發；禁止新增 provider secret，queue/replay 另做安全審查 |
| Patric 型使用者端審查官 | 固定必看 | 主公 / 使用者 / 接手者是否會誤解 | 觸發；quality tier 必須白話，不可讓 local-only 看起來像壞掉 |
| Jimmy 型文件主筆 | 改 docs / TASK_HISTORY / handoff 時觸發 | 文字可追溯、有來源、避免空泛 | 觸發；handoff/active/risk/history 同步 P85 FROZEN |
| Marcus 型數據分析師 | 涉及數據、趨勢、判斷依據時觸發 | 沒數據時是否明說 | 觸發；P85 不聲稱已降低 429，只凍結實驗與指標方向 |
| Oliver 型設計審查 | 涉及 UI、報告、圖表時觸發 | 視覺層級、可讀性、資訊密度 | 條件觸發；P89 需要處理報告中的 tier 顯示方式 |
| Penny 型 CFO | 涉及 API 成本、排程成本、付費工具時觸發 | ROI、預算上限、成本停損 | 觸發；OpenAI paid fallback 排除，free provider 預設 disabled |
| Jason 型執行 / DevOps | 涉及部署、CI、Git、腳本、環境差異時觸發 | 可執行性、rollback、環境變數、跨 shell | 觸發；P86 schedule/model 改動必須 Actions 實跑 |

### M2 紅藍對抗

| # | 紅隊質疑（具體） | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 如果 local-only 也能上首頁，是否等於把品質標準放低，讓使用者以為 AI 報告已完整？ | **S** | 0 | quality tier 必須 user-visible，manifest 必須記錄 LLM coverage 與 reason | 入計畫範圍 |
| 2 | 如果 deterministic analyzer 對反諷、泰文、越文社群語境判錯，會不會比 showcase 更危險？ | **S** | 0 | P88 只能做最低 baseline，不宣稱深度洞察；高價值樣本仍進 enrichment queue | 入計畫範圍 |
| 3 | queue/replay 會不會變成新的資料堆積與隱私風險？ | A | 0 | P92 必須先設 retention、redaction、retry cap，不得無限保存 raw prompt | 入計畫範圍 |
| 4 | 改 schedule 到 quota reset 後是否可能錯過主公早上看報告的使用情境？ | A | 0 | P86 需比較早報 local-only 與下午 enrichment 的雙段發布可能性 | 入計畫範圍 |
| 5 | 免費 provider 插槽即使 disabled，也可能讓未來 AI 誤以為可以直接啟用。 | A | 0 | P93 啟用需主公另核；handoff Forbidden Work 明列不可自動接 provider | 入計畫範圍 |
| 6 | R-016 可能其實還有 landing/promotion bug，不只 quota 問題；Evidence-first 會不會偏題？ | **S** | 0 | P89/P94 必須同時驗證 promotion gate 與 SLO，不能只看 provider diagnostics | 入計畫範圍 |

## 17. 狀態機與下一步

```text
P85: FROZEN
P86: DRAFT_PENDING_APPROVAL
P87-P95: ROADMAP_ONLY
```

下一步不是改程式碼，而是主公核准是否進入：

```text
P86 Gemini Model & Schedule Modernization
```

P86 開工前必須重新讀：

1. `NEXT_SESSION_HANDOFF.md` active bootstrap
2. `docs/PHASE_85_PLAN.md`
3. P86 開工前查證 Gemini 官方 rate limit / model availability
