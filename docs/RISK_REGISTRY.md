# 跨 Phase 風險登記簿（STR6）

> **用途**：登記跨 Phase 不滅的風險、待解隱患、需長期觀察的議題。每個 Phase 收官時主動掃一次，新風險入帳、已解風險標記關閉。
> **建立日期**：2026-05-07（隨 P69 模型選擇指引啟用）
> **格式**：每筆 = 編號 + 標題 + 來源 Phase + 風險級 + 狀態 + 描述 + 緩解策略

---

## 更新 SOP（P84.4）

1. 新增風險時使用下一個未占用 `R-###`，不得重複編號。
2. 仍需觀察或未完成緩解的風險放在 `開放風險（Open）`，且 `狀態` 欄位必須包含 `Open`。
3. 已修補、已豁免關閉或已由其他風險承接的條目移到 `已關閉風險（Closed）`，且 `狀態` 欄位必須包含 `已` 或 `Closed`。
4. Phase 收官前執行：`py scripts\governance_doctor.py --repo-root .`。
5. 若 governance doctor 回報 `GOV###`，先依 `docs/OPERATIONS_RUNBOOK.md` 對應 anchor 修正後再提交。

---

## 開放風險（Open）

### R-001：模型選擇指引三檔同步無自動檢測（G5-4）

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：`docs/MODEL_SELECTION_GUIDE.md` 主檔變更時，需手動同步 `~/.claude/CLAUDE.md` 與 `~/.gemini/GEMINI.md` 的全域縮版章節。沒有自動檢測機制，可能漂移。
- **緩解策略**：
  - 短期：每次修主檔時手動跑 diff（人工自律）
  - 長期：寫個 `scripts/check-model-guide-sync.sh`（v1.x 後續視需求做）
- **觸發升級**：若漂移導致 Claude / Gemini 端建議不一致 → 升 🔴 高

### R-002：Gemini / Anthropic 新模型大版本上線時的指引腐化

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：Gemini 4 / Claude 5 等大版本發布後，本指引內模型清單、價格、能力對照即過時。沒有自動偵測機制。
- **緩解策略**：
  - 已寫入指引 §8.3：「廠商發布新模型大版本」為強制升版觸發
  - 預設 90 天回顧週期（下次：2026-08-05）
- **觸發升級**：若主公連 3 次選擇與指引建議不符 → 立即升 v2.0

### R-003：AI 是否實際遵循「Opus 卡住主動提醒」強制條款（觀察期）

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open（觀察期）
- **描述**：指引 §3.3 規定 AI 達卡住判定須主動提醒換 Gemini，但這是**行為條款**，需實際使用後驗證 AI 是否真的遵循。
- **緩解策略**：
  - 主公在實戰中觀察至少 3 次「應提醒」情境，記錄 AI 是否主動提醒
  - 若漏提醒次數 ≥ 1 → 在 CLAUDE.md / GEMINI.md 全域章節**強化**該條款
- **觀察截止**：2026-08-05（同 90 天回顧）

---

### R-004：UI/UX 修補無 LINE WebView 自動化迴歸測試（P70.3）

- **來源**：P70.3 收官（2026-05-08）
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`reporter/templates/report.html` 的 CSS / touch event / position 規則改動可能在 LINE in-app browser（WKWebView / Chrome WebView）破壞滑動或互動，但其他環境（桌面、一般行動瀏覽器）正常難以察覺。P70.3 的 `overflow-x: hidden on html` 即此類沉默損壞案例，從 P63.2 拖到 P70.3 約 5 週。
- **緩解策略**：
  - 短期（人工 SOP）：任何 `reporter/templates/` 的修改收官前，主公在 LINE 實機點開 1 個樣本報告驗收
  - 中期：評估 Playwright + iOS WKWebView 模擬（非 LINE app 直測，但接近）的 ROI
  - 長期：若同類沉默損壞 ≥ 2 次再發，升級為自動化 smoke test 必做項
- **觀察截止**：下次 `templates/` 重大改動時 review

---

### R-006：報告頁回戰略門戶按鈕需同步修補現有報告（P70.3.1 衍生）

- **來源**：P70.3.1 收官（2026-05-08）
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`reporter/templates/` 的 HTML 結構改動（如加回首頁按鈕）不會自動反映到已生成的舊報告，需批次 patch 腳本手動補做。目前 10 個 5 月報告已補齊，但未來若有更多改動，仍需人工維護批次腳本。
- **緩解策略**：
  - 短期：結構性 template 改動收官時，附帶一份 idempotent Python patch 腳本，同步更新現有報告
  - 中期：評估 report 生成改為 server-side render（SSR）以消除靜態複製問題
- **觸發升級**：若同步遺漏導致報告體驗分裂 ≥ 2 次 → 中期方案升為必做

---

### R-005：`-webkit-overflow-scrolling: touch` 已 deprecated（G5-1 退化偵測）

- **來源**：P70.3 收官（2026-05-08）
- **風險級**：🟢 低
- **狀態**：Open（觀察期）
- **描述**：`-webkit-overflow-scrolling: touch` 為 iOS 13+ 已 deprecated 屬性，目前保留是「不傷害」原則。若未來 WebKit 移除支援或改為 hard error，可能影響 momentum scroll。
- **緩解策略**：90 天後 review，若 iOS 14+ 普及度 ≥ 95% 則移除此屬性。
- **觀察截止**：2026-08-08

---

### R-011：Orphan SKILL.md 仍為舊格式（22 條 lint warning）

- **來源**：P71.9 收官（2026-05-11）
- **風險級**：🟢 低
- **狀態**：Open（豁免觀察）
- **描述**：P71.8/P71.9 處置的 orphan/archived skill SKILL.md 尚未全面升級為 S1 schema 格式，`lint_skill_registry.py` 對這些檔案產生 22 條 lint warning。這些 skill 均已標記為非 in-use（orphan/archived），不影響正常觸發路徑。
- **緩解策略**：
  - 短期：豁免 orphan/archived skill 的 S1 schema 強制要求；lint 工具已以 `--warn-only` 模式處理這些 warning
  - 中期：若有 orphan skill 復活為 in-use，升級為必做項
- **觸發升級**：orphan skill 重新啟用 → 必須完成 S1 schema 升級才能 commit

---

### R-012：metrics JSONL 無 size cap 與輪轉策略（P72.0 遺留）

- **來源**：P72.0 收官（2026-05-14）/ B-009 通則化
- **風險級**：🟢 低（短期）/ 🟡 中（長期 ≥ 1 年）
- **狀態**：Open（觀察期）
- **描述**：`skill_metrics_logger._run_with_metrics()` append-only 寫入 `~/.claude/skill_metrics.jsonl`，無 size cap、無 rolling、無 retention 政策。19 個 skill × 每天若干次呼叫 × 365 天 ≈ 數萬筆，雖短期單檔大小可控（< 100MB 等級），但缺輪轉策略意味著未來必須 migration。
- **緩解策略**：
  - 短期（< 90 天）：每月主公手動檢查檔案大小，超過 10MB 就 archive 一次
  - 中期：在 `gen_skill_metrics.py` 加 `--rotate` 子命令，按月切檔（`skill_metrics_2026-05.jsonl`）
  - 長期：考慮改用 SQLite 取代 JSONL，原生支援查詢與 retention
- **觸發升級**：檔案 ≥ 50MB → 升 🟡；單次 dashboard 生成耗時 ≥ 5s → 升 🔴 強制做輪轉

---

### R-013：M4 `--sync-rules` anchor heuristic 召回率低（P72.3 遺留）

- **來源**：P72.3 收官（2026-05-14）/ B-006 通則化
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`m4_track_blindspots.py --sync-rules` 用字面 anchor 比對 B-NNN 通則化規則 vs PHASE_TEMPLATE.md，實測 PHASE_TEMPLATE v1.1 已含 B-001/B-003/B-005 對應規則但輸出顯示「已涵蓋 0 條」。Heuristic 沒處理同義改寫、結構性改寫、規則拆分三種變體，可能誤導 AI 或主公以為 PHASE_TEMPLATE 漏接規則而重複加入。
- **緩解策略**：
  - 短期：CLI 輸出最後一行強制印「⚠️ 召回率低，主公人工審核必要」（已落地）
  - 中期：升級 anchor 為「規則關鍵詞 + 同義詞表」比對（如 `test_skill.py` ≈ `skill 測試` ≈ `Exit Criteria 測試項`）
  - 長期：考慮用 embedding 相似度（Gemini embedding API）替代字面比對
- **觸發升級**：主公在 ≥ 2 個 Phase 因為 `--sync-rules` 誤導而重複加入規則 → 升 🔴，強制中期方案落地

---

### R-016：production SLO blocking / landing stale（P84.6 收官揭露）

- **來源**：P84.6 總收官驗證（2026-05-18）
- **風險級**：🔴 高
- **狀態**：Open
- **描述**：P84.6 收官矩陣顯示 governance / handoff / runbook / pytest 全數通過，但 production SLO 仍阻塞。2026-05-19 R-016.1 已修補 manifest sync contract，並由既有 canonical report 反建 5/16-5/19 report-only manifests，因此 `SLO002` manifest gap 已收斂；剩餘阻塞為 `SLO001` 連續無 production，`SLO003` 因連續 showcase_forced/degraded 超過門檻，且 landing 仍指向 `data/reports/aov_report_2026-05-16.html`。
- **緩解策略**：
  - 短期：不要把 P84.6 CLOSED 解讀成 production SLO 已恢復；維持 `SLO###` / `DOC###` / health check 作為營運真相。
  - 已完成：`data/runs/**/run_manifest.json` 已解除忽略，`main.py` 與 GitHub Actions fallback push 會同步 `data/runs/`；`scripts/backfill_manifest_from_report.py` 可從既有 canonical report 建立 report-only manifest。
  - 已完成：R-016.2 新增 LLM fallback/secret diagnostics；下一次 Actions 會顯示 `GEMINI_API_KEY` / `OPENAI_API_KEY` 是否配置，manifest 會記錄 `provider.quota_error`、`provider.openai_fallback_configured`、`provider.openai_fallback_used`。
  - 已凍結：2026-05-19 主公明確不想增加 OpenAI API 費用，P85 已凍結 `Evidence-first + Quality-tiered Production + LLM Enrichment Queue` 作為零額外付費修復主線。
  - 已完成：P86 `Gemini Model & Schedule Modernization` 已 CLOSED；本地已移除 2.0 / 2.5 主線 model，改為 `gemini-3.1-flash-lite` -> `gemini-3.5-flash`，並將 daily cron 更新至 UTC 08:30。遠端 commit `100460f` 已由 GitHub Actions 產出 `mode=production` report，manifest 顯示 `publish_eligible=true`、`quota_error=false`、`llm_calls=20`；health check production PASS，system doctor 無 blocking、僅 DOC007 advisory。
  - 已完成：P87 `Report Core Contract` 已 CLOSED；新 manifest 會產生 `quality.core_contract`，health check 會顯示 core contract PASS/WARN，system doctor 新增 DOC015；P87 採 shadow/advisory，不直接改 quality tier / promotion gate，不關閉 R-016。
  - 已完成：P88 `Deterministic Local Analyzer` 已 CLOSED；LLM 429 / provider exception 時可從真實貼文產出 `analysis_source=local_deterministic` 的 sentiment、keywords、heroes、events、platform breakdown 與 baseline summary；P88 未改 quality tier / promotion gate，R-016 仍 Open。
  - 已完成：P89 `Quality Tier / Promotion Gate` 已 CLOSED；manifest 寫入 `quality.tier` / `quality.analysis_source` / `quality.llm_coverage`，report metadata 顯示 tier/source/coverage，promotion gate 改看 publishable quality tier；`production_local_only` 在 core contract / local baseline 通過時可發布，`showcase_manual` / `error_fallback` 不可發布。2026-05-20 health/doctor 無 blocking；舊產物缺 tier 僅 DOC016 advisory。R-016 仍 Open。
  - 已完成：P90 `Budget Ledger / Cooldown` 已 CLOSED；新增 raw-free budget state、429 cooldown、manifest budget snapshot、DOC017 / CCG006 advisory。Gemini budget/cooldown active 時會停止打 provider 並改走 P88/P89 local baseline；budget ledger 明確標註為 pipeline proxy，不是 provider billing truth。R-016 仍 Open。
  - 已完成：P91 `Cache / Dedupe / Top-N` 已 CLOSED；新增 source selection、保守 dedupe、budget-aware Top-N、local-only merge、manifest `selection` snapshot、doctor `DOC018`、cost governance `CCG007`。預設 `LLM_ANALYSIS_TOP_N=18`，raw source 不刪除，未選來源仍走 deterministic local baseline。2026-05-22 Actions 實跑已產生 P91 selection snapshot：pre-P91 `llm_calls=28` 收斂為 P91 `llm_calls=6`，`total_input_posts=19`、`unique_posts=12`、`duplicate_posts=7`、`local_only_posts=7`，且 local-only 全由 `duplicate_url` 主導。R-016 仍 Open。
  - 已完成：P92 `Enrichment Replay / Local-only 補深讀` 已 CLOSED；新增 artifact-backed enrichment queue、raw-free manifest `enrichment` snapshot、budget-aware manual `scripts/enrichment_replay.py`、GitHub Actions short-retention artifact、doctor `DOC019`、cost governance `CCG008`。Raw queue 僅位於 git-ignored `data/enrichment_queue/` 或 Actions artifact；`duplicate_url` / `duplicate_signature` local-only 預設 skipped / `no_eligible` no-op，不消耗 LLM；replay 使用既有 Gemini path 且關閉 OpenAI fallback。focused tests 66 passed、full pytest 274 passed。R-016 仍 Open。
  - 已完成：P93 `Provider Abstraction / Disabled-by-default Free Provider Slots` runtime 已 CLOSED；新增 `LLMProviderClient` protocol、disabled-by-default `ProviderRouter`、shared provider budget guard、raw-free manifest `provider.routing`、doctor `DOC020`、cost governance `CCG009`、fake-provider / no-call / budget guard tests。所有非 Gemini provider 預設 `enabled=false`；誤開 candidate slot 時 fail-closed，不呼叫 Groq / Cloudflare / GitHub Models；未新增 provider secret、未加入 GitHub Actions `models: read`、未改 daily default。R-016 仍 Open。
  - 已完成：P94 `Doctor / SLO Reclassification` runtime 已 CLOSED；新增 current / historical / residual classification，保留 `SLO001` / `SLO002` / `SLO003` blocking 門檻。2026-05-23 五日 SLO probe 為 `classification=current` 且 `issues=[]`；system doctor 顯示 DOC018 / DOC019 為 `residual` advisory；cost/cache 三日窗將 2026-05-21 pre-P91 `llm_calls=28` 標為 CCG005 `historical` advisory，CLI 不再因舊 spike exit 1。P94 未啟用 provider、未新增 secrets、未改 workflow、未關閉 R-016。
  - 已驗證：P95 `R-016 Closeout Verification` 第一輪 verification 已於 2026-05-24 執行；裁決為 `Keep R-016 Open`。後續 post-P95 AoV Daily Monitor run `26356870400` 已 success，auto-sync commit `65b9f92` 產生 2026-05-24 production report；2026-05-24 SLO 五日窗 `issues=[]`，system doctor 無 blocking，landing 指向最新 production report，provider routing 維持 `router_disabled_legacy_default` / `enabled_slots=0`，5/24 manifest `enrichment.replay_status=no_eligible`。
  - 已凍結：P95.1 `Enrichment Pending Closure` plan 已 FROZEN；P95.1 不靠 2026-05-22 掉出三日窗來假裝收官，而是要在主公另核准 runtime / artifact access 後，對 2026-05-22 enrichment pending eligible=2 做 dry-run / 必要 replay / CCG008 分類修正。P95.1 plan freeze 尚未下載 artifact、尚未讀 raw queue、尚未跑 replay、尚未關閉 R-016。
  - 已驗證：P95.1A `Artifact Dry-run` 已完成；正確 artifact 是 run `26285001843` / artifact `7159368993` / zip entry `2026-05-22/enrichment_queue.json`。queue schema valid，`eligible_count=2`，`skipped_count=8`；dry-run output 為 `eligible=2 will_replay=2 remaining_budget=15 status=dry_run`。P95.1A 未 apply replay、未寫 report、未 stage raw artifact / raw queue。R-016 仍 Open。
  - 已驗證：P95.1B `Apply Replay` 已執行，但 P90 budget guard 因 2026-05-24 `cooldown_active` 安全擋下 LLM replay；2026-05-22 manifest 已由 `replay_status=pending` 轉為 `replay_status=skipped_budget`，`budget_reason=cooldown_active`，`enriched_posts=0`。此狀態比 unknown pending 更可追溯，但尚未完成 replay；R-016 仍 Open。
  - 已驗證：P95.1C `Cooldown Retry` 已於 2026-05-25 09:35 +08 執行成功；dry-run 顯示 `eligible=2 will_replay=2 remaining_budget=20`，apply output 為 `OK: enrichment replay completed; enriched=2/2`。2026-05-22 manifest 已由 `replay_status=skipped_budget` 轉為 `replay_status=completed`，`eligible_posts=2`，`enriched_posts=2`，`budget_decision=call_llm`，`budget_reason=budget_available`，`cooldown_active=false`。Cost governance 三日窗已無 CCG008 current；只剩 2026-05-23/24 no_eligible residual。R-016 仍 Open，待主公裁決 close / downgrade / keep-open。
  - 中期：P86-P95.1 分段處理 model/schedule、report core contract、本地 deterministic analysis、quality tier、budget ledger、cache/dedupe、enrichment replay、provider abstraction、doctor/SLO 重分類、closeout verification 與 enrichment pending closure；下一步是 commit / push P95.1C completed docs，之後由主公裁決 R-016 close / downgrade / keep-open。若追求完美收尾，建議 push 後手動 dispatch post-2026-05-25 Daily Monitor 補最新雲端證據。
  - 長期：免費 provider 只作 P93 disabled-by-default 插槽候選；不得在未核准前接進主鏈路。
- **觸發升級**：若 P86-P95 完成後仍連續無可發布 production tier ≥ 3 天，或 landing 指向非最新健康報告造成主公誤判 → 升級為 P95 closeout blocking issue，不得關閉 R-016。

---

## 已關閉風險（Closed）

### R-007：`.back-to-landing` 未列入 mobile backdrop-filter 停用清單（P70.3.1 審計）

- **來源**：P70.3.1 63 維度審計（2026-05-08）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-08；P76 於 2026-05-16 移至 Closed）
- **描述**：行動版（`@media max-width 768px`）停用 `backdrop-filter` 的 selector 清單未含 `.back-to-landing`，導致按鈕在 mobile 仍觸發模糊效果 → 滑動卡頓風險。
- **修補**：已將 `.back-to-landing` 加入 selector；template + 10 舊報告同步修補。
- **關閉條件**：具體 selector 修補已完成；LINE WebView 長期觀察由 R-004 承接。

---

### R-008：`.back-to-landing` 缺少 :focus 樣式與 aria-label（P70.3.1 審計）

- **來源**：P70.3.1 63 維度審計（2026-05-08）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-08；P76 於 2026-05-16 移至 Closed）
- **描述**：按鈕缺少 `:focus` 可見輪廓（無障礙 a11y 標準），且無 `aria-label`（螢幕閱讀器無法正確識別）。
- **修補**：已補 `.back-to-landing:focus { outline: 2px solid #f472b6; outline-offset: 3px; }` 及 `aria-label="返回戰略門戶首頁"`；template + 10 舊報告同步修補。
- **關閉條件**：已修補，無需進一步觀察。

---

### R-014：4 個歷史 Phase（P63/P64/P69/P70.3）缺 blindspot（M4 偵測）

- **來源**：P72.3 M4 `--status` 偵測（2026-05-14）
- **風險級**：🟢 低
- **狀態**：✅ 已回填（P75，2026-05-16）
- **描述**：M4 協議於 P71.1（2026-05-09）才落地，先前 4 個 Phase（P63/P64/P69/P70.3）的 postmortem 已寫但無對應 blindspots 檔。雖然當時的 postmortem 多少有涵蓋「以為清單」「教訓」，但未按 B-NNN 結構化，造成 `cross_phase_review.py` 無法自動撈取通則化規則。
- **修補**：P75 新增 4 份 blindspot 檔：
  - `docs/postmortems/2026-05-16-phase-63-blindspots.md`（B-011~B-013）
  - `docs/postmortems/2026-05-16-phase-64-blindspots.md`（B-014~B-016）
  - `docs/postmortems/2026-05-16-phase-69-blindspots.md`（B-017~B-019）
  - `docs/postmortems/2026-05-16-phase-70.3-blindspots.md`（B-020~B-022）
- **驗證**：
  - `py scripts/m4_track_blindspots.py --status` → P63/P64/P69/P70.3 全部 `✅ 已配對`
  - `py scripts/cross_phase_review.py` → 可讀到 B-011~B-022，最近 5 個 postmortem 產生 19 條 checklist
- **關閉條件**：4 個缺漏 Phase 均已配對，且新增規則能被 M3 工具召回。

---

### R-015：test_dynamic_focus 3 個 pre-existing 失敗連跑 5 Phase 積欠（P72 遺留）

- **來源**：P72.5 收官審視（2026-05-14）/ B-008 通則化
- **風險級**：🟡 中
- **狀態**：✅ 已修補（P74，2026-05-16）
- **描述**：`test_dynamic_focus.py` 3 個測試案例事件迴圈隔離問題（單檔跑 OK / 全套跑掛），從 P72.0 開始連續 5 個 Phase 被標為「pre-existing 不阻擋」，無人處理。違反 B-008 通則化「連 ≥ 3 個 Phase 標 pre-existing 必須升級為獨立 Phase」原則。
- **根因**：測試使用 `asyncio.get_event_loop().run_until_complete(...)`。單檔執行時 Python 仍會建立預設 loop，但全套測試前序 case 使 event loop policy 進入「已 set_called、目前無 current loop」狀態，導致三個 case 在主執行緒丟 `RuntimeError: There is no current event loop`。
- **修補**：P74 將三處測試執行改為 `asyncio.run(...)`，讓每個 async case 自行建立並關閉事件迴圈；未修改 `analyzer/dynamic_focus.py` production code。
- **驗證**：
  - `py -m pytest tests/test_dynamic_focus.py -q` → 5 passed
  - `py -m pytest -q` → 112 passed
- **關閉條件**：3 個測試案例全綠（單檔 / 全套皆通過）已達成。

### R-009：smart-task-router SKILL.md `deployed_to` 欄位為空（P71.8 遺留）

- **來源**：P71.8 前（2026-05-11 前後發現）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（P71.10，2026-05-14）
- **描述**：P71.8 升級 smart-task-router 為 in-use 時，SKILL.md 的 `deployed_to` 欄位遺留為空陣列 `[]`，未正確標記部署目標 `claude-project`，導致 registry 中部署資訊不完整。
- **修補**：P71.10 將 `deployed_to: []` 修正為 `deployed_to: ["claude-project"]`。

---

### R-010：ui-ux-pro-max skill 缺少 test_skill.py（P71.9 遺留）

- **來源**：P71.9 收官前發現（2026-05-11）
- **風險級**：🟡 中（SKILL_HEALTH 顯示 🔴）
- **狀態**：✅ 已修補（P71.9+，2026-05-11）
- **描述**：P71.9 處置 orphan skill 時，ui-ux-pro-max 升級為 in-use 但未補充 `test_skill.py`，導致 SKILL_HEALTH 顯示該 skill 為 🔴，打破「19 全綠」目標。
- **修補**：P71.9+ 補充 6/6 測試案例（schema lint / CLI 執行 / V1 觸發塊 / when_to_use / 範例查詢 / 輸出格式），達成史上首次 19/19 全綠。

---

## 變更紀錄

- **2026-05-07**：建立檔案（隨 P69 模型選擇指引啟用 STR6）；登記 R-001/R-002/R-003。
- **2026-05-08**：P70.3 收官登記 R-004（UI/UX LINE 迴歸盲區）+ R-005（webkit deprecated 屬性 90 天 review）。P70.3.1 審計追加 R-006（舊報告同步風險）+ R-007（mobile blur fix，已關閉）+ R-008（a11y fix，已關閉）。
- **2026-05-14**：P71.10 收官登記 R-009（deployed_to 空，已關閉）+ R-010（ui-ux-pro-max 無 test，已關閉）+ R-011（orphan lint warning，豁免觀察中）。
- **2026-05-14**：P72.5 收官登記 R-012（metrics JSONL retention）+ R-013（M4 sync-rules anchor heuristic 召回率低）+ R-014（4 個歷史 Phase 缺 blindspot）+ R-015（test_dynamic_focus 積欠升級獨立 Phase）。
- **2026-05-16**：P74 關閉 R-015；`test_dynamic_focus.py` 三個 async case 改用 `asyncio.run(...)`，單檔 5 passed，全套 112 passed。
- **2026-05-16**：P75 關閉 R-014；回填 P63/P64/P69/P70.3 共 4 份 blindspot，新增 B-011~B-022，M4 status 缺漏數歸零。
- **2026-05-16**：P76 狀態清理；R-007/R-008 從 Open 區移至 Closed 區，長期 LINE WebView 觀察仍由 R-004 承接。
