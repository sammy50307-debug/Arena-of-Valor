# Phase P83 計畫書 — Data Quality / Security（核准版）

> 草案日期：2026-05-17
> 凍結日期：2026-05-17
> 狀態：CLOSED（2026-05-17：P83 data quality / security 已收官）

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| Phase 編號 | P83 |
| 名稱 | Data Quality / Security |
| 影響半徑 | 標準（預估 6-9 檔） |
| 預估投入時數 | 3-5 h |
| Token budget | 45K-70K tokens |
| 負責模型 | GPT-5.3-Codex 高 |

## 0.5 狀態轉換清單

本 Phase 不涉及 skill 生命週期轉換；涉及 daily pipeline 資料品質狀態與安全 gate 的契約化。

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| P83 計畫 | DRAFT | FROZEN | 計畫已完成並通過稽核，尚不可改程式碼 | 本文件建立並通過 lint | AI 建立，主公核准後才進 APPROVED |
| data quality gate | advisory/implicit | explicit planned | 0 posts、來源不足、schema 異常要有明確分類 | P83 實作階段落地 | AI 實作，主公核准 Phase |

## 1. 目標

讓每日監測資料在進入 report / manifest / publish 之前具備明確品質與安全契約：0 posts anomaly 要被標示，source health 可被 doctor/manifest 看見，LLM JSON 不合約要 fail loud 或降級，HTML 輸出不得引入 XSS，raw 與 sanitized analysis 邊界要可追溯。

## 2. 觸發背景

P77-P82 已處理 runtime 止血、manifest、doctor、promotion、replay/backfill、timezone/idempotency。下一個長期風險是「資料本身是否可信與安全」：即使 pipeline 會跑、會寫 manifest、會 promote，如果輸入來源不足、LLM 回傳缺欄位、HTML 注入未被擋、raw content 被錯放到公開輸出，系統仍可能產出看似成功但不可信或有安全風險的報告。

## 3. Entry Criteria

開工前必須全部達成：

- [x] P82 已收官：run context、run_id/source_hash、timezone contract 已落地。
- [x] P80 promotion gate 已存在，P83 可把 data quality 訊號接入但不重寫發布架構。
- [x] P79 doctor 已存在，可擴充資料品質與安全 issue code。
- [x] P78 manifest 已有 schema v2，可擴充 source health / security 欄位。
- [x] 主公核准 P83 計畫，狀態由 FROZEN 轉 APPROVED。

## 4. Exit Criteria

達成全部才算 P83 收官：

- [x] 0 posts anomaly 有明確分類與 manifest 訊號，不再只靠 log 文字判讀。
- [x] source health score / source counts 可被 manifest 與 doctor 讀取。
- [x] LLM daily summary / post analysis 契約不合格時有明確 fail/degrade 行為與測試。
- [x] 報告 template 輸出確認不把 raw HTML/JS 注入到公開頁面。
- [x] raw content 與 sanitized analysis 邊界明確：debug/manifest/report 不寫 secrets 或未清理 raw 原文。
- [x] 新增/更新測試覆蓋 0 posts、bad LLM JSON、HTML escape、source health、raw/sanitized 邊界。
- [x] `py -m pytest -q` 通過，Python 3.8 import guard 不回歸。
- [x] handoff / active / TASK_HISTORY / 總戰役計畫同步收官狀態。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | 3-5 h |
| 預估收益等級 | 高 |
| 收益描述 | 減少假成功報告、來源不足誤判、LLM schema 漂移與公開 HTML 注入風險 |
| ROI 結論 | 值得做，因為 P77-P82 讓流程能穩定跑，P83 讓結果可信且可安全公開 |

## 6. 動工範疇（凍結）

1. 建立 data quality 訊號：0 posts、source count、platform coverage、source health score。
2. 將 data quality 寫入 manifest，並讓 system doctor 能讀出 issue code。
3. 強化 LLM output contract：daily summary / post analysis 缺欄位時明確分類。
4. 確認 report HTML escape 邊界，避免 title/content/url 造成 XSS。
5. 定義 raw content / sanitized analysis 邊界：公開 report、manifest、debug bundle 各自能放什麼。
6. 補測試與文件，避免安全/品質 gate 只存在於口頭規則。

## 7. 非範疇（避免偏航）

- 不做 P84 retention、SLO、long-term governance。
- 不重寫 P80 promotion 架構，只接入資料品質訊號。
- 不大改報告視覺設計或版型。
- 不新增爬蟲平台。
- 不更換 LLM provider 或 prompt 架構，除非只是補 contract guard。

## 8. 17 層稽核表

> 影響半徑：標準 Phase（預估 6-9 檔）。依規則列全 17 層。

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | 小型 quality/security helper，避免塞滿 main.py | gate 散落各處難維護 | 集中資料品質判斷與測試 |
| 2 | 邏輯層 (Logic) | 0 posts/source health/LLM contract 分類清楚 | 把外部無資料誤判成系統成功 | 明確 status/reason/score |
| 3 | 架構層 (Architecture) | P83 只提供品質與安全訊號，P80 仍負責發布 | 混修 promotion 導致範圍失控 | 不改 promote 核心流程 |
| 4 | 測試層 (Testing) | bad JSON、0 posts、XSS payload、manifest/doctor 測試 | 只測 happy path | 必測負例與安全 payload |
| 5 | 資料層 (Data) | manifest 擴充 source health 與 quality reasons | manifest 欄位膨脹或不相容 | schema 向後相容、欄位命名清楚 |
| 6 | 可觀察性層 (Observability) | doctor issue code 對應 runbook | 品質問題仍只能翻 log | issue code + manifest reason |
| 7 | 韌性層 (Resilience) | 外部來源不足時 degrade/fail loud | 0 posts 被當正常報告發布 | quality gate 給 promotion 參考 |
| 8 | 效能層 (Performance) | 只計算小型統計與字串 escape | 品質掃描拖慢 daily | 不做大型 NLP 或外部請求 |
| 9 | UX/A11y 層 | 不改 layout，但避免輸出危險內容 | 使用者看到未清理文字或破版 | template escape 測試 |
| 10 | 安全層 (Security) | HTML escape、raw/sanitized 邊界、secret 不外流 | XSS、prompt injection 內容外顯、debug bundle 泄漏 | 安全負例測試與欄位白名單 |
| 11 | 部署層 (DevOps) | CI 先 advisory，再評估是否升 blocking | 太早 blocking 造成 daily 不發 | P83 先分類與可觀測，門檻另議 |
| 12 | 成本層 (Cost) | 不新增 API 呼叫 | 成本不應增加 | 純本地檢查 |
| 13 | 可維護性層 (Maintainability) | quality/security 契約集中 | 半年後不知道何謂健康資料 | helper + tests + docs |
| 14 | 文件層 (Documentation) | plan/handoff/TASK_HISTORY/runbook 同步 | 新視窗誤解 gate 嚴格度 | L1/L2 明確狀態與非範疇 |
| 15 | 流程層 (Process) | FROZEN 後等主公核准 | 未核准先改 security gate | active bootstrap 禁止改碼 |
| 16 | 隱私/合規層 (Privacy) | raw content 不進 manifest/debug public path | 儲存或公開玩家原文過度 | raw/sanitized 欄位白名單 |
| 17 | i18n/在地化層 | 保留繁中輸出，安全處理多語文字 | escape 破壞中文/emoji | 使用 template autoescape 與 unicode 測試 |

## 9. 層級互鎖驗證

- [x] 動 Logic 層 -> 已規劃 Testing 層。
- [x] 動 Architecture 層 -> 已規劃 Documentation 層。
- [x] 動 Data 層 -> 已規劃 Maintainability 層。
- [x] 動 Security 層 -> 已規劃 Testing 層。
- [x] 動 Privacy 層 -> 已規劃 Documentation / Security。

## 10. 跨切面檢查

### X1 可逆性

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 新增 P83 計畫文件 | 可逆 | 不需不可逆確認 |
| 後續新增 quality/security helper | 可逆 | P83 核准後才可做 |
| 後續擴 manifest schema | 半可逆 | 需保留舊 manifest 相容 |
| 後續調整 doctor issue code | 可逆 | runbook 同步即可 |
| 後續 push | 半可逆 | 依專案規則 push 前詢問主公 |

### X2 盲區掃描

- log 副作用：品質 gate 可能讓原本看似成功的 daily 顯示 degraded。
- 中間檔產出：debug bundle 若加入 quality snapshot，必須避免 raw content。
- 系統狀態變更：promotion 是否採用 quality gate 需分階段，避免一口氣 blocking。

### X3 時間敏感性

- 本計畫凍結日期：2026-05-17
- 本計畫過期日期：2026-05-24，超過需重看 template/report/manifest/doctor 是否已變。
- 風險記錄帶日期：已在本文件與 TASK_HISTORY 補錄。

### X4 多角度同行審查

- 主公視角：主公需要知道報告不是「有產出就可信」，而是來源、LLM contract、安全輸出都過關才可信。
- 世界頂尖駭客 / 紅隊攻擊者視角：最危險是玩家內容含 `<script>`、惡意 URL、prompt injection 文本被原樣放進公開 HTML 或 debug bundle；最小緩解是 escape 與欄位白名單。
- 接手者視角：接手者要能從 manifest/doctor 一眼判斷是來源不足、LLM 壞掉、還是 HTML 安全問題。
- X4-J 自動化建議性工具邊界：source health score 是規則化訊號，不代表真實輿情完整性；需在文件標註它是運維健康指標。
- X4-K 使用者端審查官 / Patric 型人格：最容易誤解的是 0 posts 報告看起來很乾淨，實際是資料失明；P83 必須讓這種狀態明確可見。

## 11. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | quality gate 太嚴，正常低聲量日被標 degraded | 中 | 中 | 業務 | 先 advisory，門檻可調且有 reasons |
| R2 | quality gate 太鬆，0 posts 或單一來源仍被當健康 | 中 | 高 | 代碼可控 | 0 posts 必定 anomaly，source health 明確分級 |
| R3 | HTML escape 測試不足，XSS payload 滲入 report | 低 | 高 | 安全 | 加惡意 payload 測試與 template escape 檢查 |
| R4 | manifest/debug bundle 寫入 raw content 或敏感資訊 | 中 | 高 | 隱私/安全 | 白名單欄位，不存 raw content |
| R5 | LLM schema guard 改太多導致現有 fallback 壞掉 | 中 | 中 | 代碼可控 | 先測現有 fallback，再小步加 contract |

**高風險加權檢查（META4）**：
- 高風險數量：3 項。
- 加權分數：R1 1 + R2 2 + R3 2 + R4 2 + R5 1 = 8。
- 是否 >= 5 須請示主公：是；主公已於 2026-05-17 核准，後續依計畫小步動工。

## 12. 工作階段

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| P83.0 | Inventory：source/LLM/report/manifest/debug bundle 的 raw/sanitized 邊界 | R3/R4/R5 | 影響點清單與測試目標明確 |
| P83.1 | 建立 source health / 0 posts anomaly 訊號 | R1/R2 | manifest/doctor 可讀 quality status |
| P83.2 | 強化 LLM output contract guard | R5 | bad JSON / 缺欄位測試通過 |
| P83.3 | HTML escape / XSS payload 防護驗證 | R3 | report 測試確認 payload 被 escape |
| P83.4 | raw / sanitized analysis 邊界寫入文件與測試 | R4 | debug/manifest/report 不含 raw content |
| P83.5 | 收官驗證與 TASK_HISTORY 無損紀錄 | 全部 | pytest / diff check / 收官紀錄 |

## 12.1 P83.0 Inventory 結論（2026-05-17）

### 12.1.1 實際資料流

| 節點 | 物理真相 | raw / sanitized 判定 | P83 風險 |
|---|---|---|---|
| Source ingress | `main.py` 由 waterfall + Dcard + 巴哈收集 `SearchResult`，若 `all_results` 為空目前會提前 `return` | raw；尚未形成 manifest / doctor 可見的 0 posts 訊號 | 0 posts 可能只停在 log，不會進入 manifest |
| Raw JSON | `main.py` 寫出 `data/raw_YYYYMMDD.json`，內容為 `[r.to_dict()]` | raw；含 title/content/url/platform/source/region | 可供 replay，但不得直接進公開或 debug bundle 內容 |
| Single-post LLM | `analyzer/sentiment.py` 把壓縮後 title/content 送進 LLM；結果與原 post 合併成 `analyzed_posts` | post 為 raw，analysis 為 sanitized-ish 但未明文標記 | LLM 回傳缺欄位時目前只靠 schema 請求與 fallback，缺少明確 issue code |
| Daily summary | `generate_daily_summary()` 回傳 summary；`analyzer/data_writer.py` 只補最小 top-level 欄位 | sanitized-ish；仍含 LLM 字串、reasoning、summary | bad JSON / 缺欄位目前會 fallback，但 manifest 無契約狀態 |
| Analysis JSON | `main.py` 只把 `daily_summary` 寫入 `analysis_YYYYMMDD.json` | sanitized-ish，不含完整 raw posts | replay 會再讀 raw JSON 重新組 report posts |
| Report HTML | `reporter/generator.py` 設 `autoescape=True`，template 多數文字用 Jinja escape，JS 區塊用 `tojson` | public sanitized output | URL scheme 未被明確驗證；JS `innerHTML` 仍會把 URL 字串拼入 href |
| Manifest | `analyzer/run_manifest.py` schema v2 只有 paths/metrics/history/eligibility | metadata only，不含 raw content | 尚無 source health / quality / security 欄位 |
| Debug bundle | `scripts/debug_bundle.py` 只寫 paths、health checks、manifest、extra；不讀 raw/analysis/report 內容 | diagnostic metadata | 目前相對安全；後續若加 quality snapshot 必須白名單，不能塞 raw content |
| Doctor | `scripts/system_doctor.py` 讀 manifest + health checks | metadata observer | 尚無 data quality/security issue code |

### 12.1.2 盤點後修正的動工前提

- `main.py` 是 P83.1 必要觸點：source health / 0 posts anomaly 若要被寫入 manifest，必須在 source 收集後、`build_manifest()` 前形成品質訊號；原 allowed files 未列 `main.py`，本 inventory 將其列為可動檔。
- `debug_bundle.py` 目前沒有直接外洩 raw content；P83.4 僅需守住未來新增欄位的白名單，不需要重寫 bundle 架構。
- `report.html` 的文字 escape 基礎存在，但 URL 安全不是 HTML escape 可解；P83.3 測試需包含 `javascript:` URL、quote breakout、`<script>` title/content。
- `data_writer.validate_summary()` 只能算最小 schema 補洞，不等於 LLM contract guard；P83.2 需獨立測 bad daily summary / bad single-post analysis。

### 12.1.3 P83.1 最小實作切入點

1. 在 source 收集後建立 quality snapshot：`total_posts`、`platform_counts`、`source_count`、`status`、`reasons`。
2. 將 quality snapshot 寫入 manifest schema v3 或 v2 向後相容欄位。
3. doctor 增加 data quality issue code：0 posts blocking/degraded、source coverage advisory。
4. 測試先覆蓋 `0 posts`、`single source`、`normal multi-source` 三組，不先重寫 promotion gate。

## 12.2 P83.1 實作結果（2026-05-17）

### 12.2.1 已落地範圍

| 項目 | 實作位置 | 行為 |
|---|---|---|
| source quality snapshot | `analyzer/run_manifest.py` | 新增 `build_source_quality()`，輸出 `status`、`total_posts`、`platform_count`、`platform_counts`、`source_count`、`reasons` |
| manifest quality 欄位 | `analyzer/run_manifest.py` | `build_manifest()` 寫入 `quality.source_health`；`validate_manifest()` 驗證欄位型別 |
| 0 posts manifest | `main.py` | `all_results` 為空時不只 log + return，會寫 failed manifest，reason=`no_posts` |
| 正常 source health | `main.py` | source 收集後建立 quality snapshot，隨 manifest 寫出 |
| doctor issue code | `scripts/system_doctor.py` | `DOC013` 代表 0 posts blocking，`DOC014` 代表 source health degraded advisory |
| runbook | `docs/OPERATIONS_RUNBOOK.md` | 補 DOC013 / DOC014 處置步驟 |
| 測試 | `tests/test_run_manifest.py`, `tests/test_system_doctor.py` | 覆蓋 no posts、multi-source、single-source degraded、manifest contract、doctor code |

### 12.2.2 驗證

- `py -m pytest -q tests/test_run_manifest.py tests/test_system_doctor.py` -> 22 passed
- `py -3.8 -c "import main; import analyzer.run_manifest; import scripts.system_doctor; print('py38 import ok')"` -> passed
- `py -m pytest -q` -> 170 passed

### 12.2.3 下一步

P83.2：強化 LLM output contract guard。只處理 daily summary / post analysis 缺欄位或型別不合格時的 fail/degrade 訊號，不更換 LLM provider、不大改 prompt。

## 12.3 P83.2 實作結果（2026-05-17）

### 12.3.1 已落地範圍

| 項目 | 實作位置 | 行為 |
|---|---|---|
| schema required guard | `analyzer/sentiment.py` | 新增 `_validate_schema_payload()`，檢查 required 欄位與基本型別 |
| single-post contract | `analyzer/sentiment.py` | 單篇 LLM analysis 缺欄位時降級成 `分析失敗`，寫入 `llm_contract.status=degraded` |
| batch diagnostic | `analyzer/sentiment.py` | `analyze_posts()` 回傳 `contract_status` / `contract_errors` |
| daily summary contract | `analyzer/sentiment.py` | daily summary 缺欄位時丟 `LLMContractError`，走 fallback summary 並寫 `llm_contract.status=degraded` |
| valid contract marker | `analyzer/sentiment.py` | valid single-post / daily summary 會標 `llm_contract.status=ok` |
| tests | `tests/test_sentiment_contract.py`, `tests/test_showcase_modes.py` | 覆蓋 bad single-post、valid single-post、bad daily summary、valid daily summary、既有 showcase fixture |

### 12.3.2 驗證

- `py -m pytest -q tests/test_sentiment_contract.py tests/test_showcase_modes.py tests/test_openai_fallback.py` -> 13 passed
- `py -3.8 -c "import analyzer.sentiment; print('py38 sentiment import ok')"` -> passed

### 12.3.3 下一步

P83.3：HTML escape / XSS payload 防護驗證。測試應包含 `<script>` title/content、quote breakout、`javascript:` URL；不改 layout。

## 12.4 P83.3 實作結果（2026-05-17）

### 12.4.1 已落地範圍

| 項目 | 實作位置 | 行為 |
|---|---|---|
| URL scheme 白名單 | `reporter/generator.py` | 新增 `_safe_report_url()`，只允許 `http` / `https` 且必須有 netloc；其他輸出 `#` |
| report post copy | `reporter/generator.py` | 新增 `_copy_entry_with_safe_url()`，渲染前複製 post 並替換危險 URL，不 mutate 原輸入 |
| template 前處理 | `reporter/generator.py` | `generate()` 開頭先 sanitise `analyzed_posts`，讓 Top5、feed、side panel 共用安全 URL |
| XSS 測試 | `tests/test_report_security.py` | 惡意 title/content/summary/recommendation 會被 Jinja escape；`javascript:` URL 不進 HTML |

### 12.4.2 驗證

- `py -m pytest -q tests/test_report_security.py tests/test_report_generator_landing.py tests/test_generator_landing.py` -> 6 passed
- `py -3.8 -c "import reporter.generator; print('py38 generator import ok')"` -> passed

### 12.4.3 下一步

P83.4：raw / sanitized analysis 邊界文件與測試。重點是 debug bundle / manifest / report 不寫 raw content，並以測試鎖住白名單。

## 12.5 P83.4 實作結果（2026-05-17）

### 12.5.1 已落地範圍

| 項目 | 實作位置 | 行為 |
|---|---|---|
| debug extra 白名單 | `scripts/debug_bundle.py` | 新增 `SAFE_EXTRA_KEYS = {"quarantine_path", "expected_mode", "checked_health"}` |
| extra sanitizer | `scripts/debug_bundle.py` | 新增 `_sanitize_extra()`，只保留白名單 key 與 primitive value |
| raw content 不打包 | `scripts/debug_bundle.py` | 維持只寫 raw path，不讀 raw file content |
| security test | `tests/test_debug_bundle_security.py` | 驗證 raw file payload 與 unsafe extra 不進 debug bundle JSON |

### 12.5.2 驗證

- `py -m pytest -q tests/test_debug_bundle_security.py tests/test_system_doctor.py` -> 8 passed
- `py -3.8 -c "import scripts.debug_bundle; print('py38 debug bundle import ok')"` -> passed

### 12.5.3 下一步

P83.5：收官驗證。需跑全套 pytest、`git diff --check`、狀態文件切 CLOSED / P84 DRAFT，並準備 commit；push 前需主公確認。

## 12.6 P83.5 收官驗證（2026-05-17）

### 12.6.1 驗證

- `py -m pytest -q` -> 176 passed
- `py -3.8 -c "import main; import analyzer.run_manifest; import analyzer.sentiment; import reporter.generator; import scripts.debug_bundle; import scripts.system_doctor; print('py38 p83 import ok')"` -> passed
- `git diff --check` -> passed（僅 CRLF working-copy warning，無 whitespace error）

### 12.6.2 收官結論

P83 已完成 data quality / security 的五個目標：

1. 0 posts anomaly 有 manifest 與 doctor 訊號。
2. source health / source counts 可被 manifest 與 doctor 讀取。
3. LLM output contract bad payload 會明確降級並有測試。
4. report HTML 文字 escape 與 URL scheme 防線有測試。
5. debug bundle raw/sanitized 邊界以 extra 白名單鎖住。

## 13. 影響檔案清單

**新增**：
- `docs/PHASE_83_PLAN.md`
- 後續可能新增：`tests/test_data_quality.py`、`tests/test_report_security.py` 或同等測試檔

**修改（計畫核准後才可動）**：
- `main.py`：P83.0 inventory 確認為 source health / 0 posts anomaly 寫入 manifest 的必要呼叫端。
- `analyzer/run_manifest.py`：可能加入 data quality/security 欄位。
- `scripts/system_doctor.py`：加入 data quality/security issue code。
- `reporter/generator.py` 或 template 測試：確認 HTML escape 邊界。
- `analyzer/data_writer.py` / `analyzer/sentiment.py`：視 LLM contract inventory 決定是否小改。
- `scripts/debug_bundle.py`：若加入 quality snapshot，需遵守 raw/sanitized 白名單。
- `tests/*`：補 data quality / security 負例測試。
- `NEXT_SESSION_HANDOFF.md`, `docs/ACTIVE_OPERATION.md`, `TASK_HISTORY.md`, `docs/DAILY_MONITORING_RELIABILITY_PROGRAM.md`：狀態同步。

**刪除**：
- 無預期刪除。

**影響但未直接修改**：
- P80 promotion gate：P83 可能提供 quality reasons，但不重寫 promote 流程。
- P79 doctor/runbook：P83 issue code 需對應 runbook。
- P78/P82 manifest contract：需保留向後相容。

## 14. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：

- [ ] 主公否決 quality gate 門檻設計。
- [ ] XSS/security 測試發現既有 report 有高風險暴露。
- [ ] manifest/debug bundle 曾寫入不該公開的 raw content。
- [ ] 有任何「我以為 template autoescape 足夠，結果不是」事件。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-83-data-quality-security.md`

## 15. Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現 |
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | 具體攻擊面是玩家內容、標題、URL 或 LLM 摘要含 script / HTML / prompt injection，被寫入公開 report 或 debug bundle；最小緩解是 escape、URL 驗證與 raw 欄位白名單。 |
| **X4-B 接手者** | 接手者需要從 manifest 與 doctor 直接分辨 0 posts、來源不足、LLM schema 破壞、HTML 安全問題，不能只靠翻散落 log。 |
| **X4-C 災難情境** | 情境：某天外部來源全掛但 pipeline 仍產出漂亮空報告並 promote；緩解：0 posts anomaly 必定進 manifest/doctor。 |
| **X4-D 5 年後** | 五年後來源平台或 LLM 可能全換，但 data quality/security contract 應仍能靠 source health、schema guard、escape 測試維持。 |
| **X4-E 終端 vs IDE** | 本 Phase 驗證必須用 pytest/CLI，不依賴瀏覽器人工肉眼看 report，XSS payload 要在測試裡機械判斷。 |
| **X4-F 跨平台 Win/Mac/Linux** | HTML escape、JSON schema、path 白名單應用 Python 標準工具與 Jinja 行為，不依賴 shell 或平台特定命令。 |
| **X4-G 主公個人視角** | 主公最在乎報告可信與安全公開；P83 要把「今天沒有資料」與「系統壞了」分開標示，不讓主公猜。 |
| **X4-H 觀測 / 治理** | 若品質與安全只存在測試中，線上壞了仍難定位；manifest/doctor 必須能輸出 quality/security reason。 |
| **X4-I 主公可見性** | 自動清洗、escape、quality score 都是主公看不到的行為；收官時需列出欄位、門檻與實測 payload。 |
| **X4-J 自動化建議性工具邊界** | source health score 只能代表本 pipeline 觀測到的來源健康，不代表整體社群真實聲量，必須保留人工判讀空間。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 使用者可能把 0 posts 解讀成「今天沒人在討論」，實際可能是爬蟲或 API 壞；P83 必須讓報告與診斷語義避免誤導。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| Jarvis 型總控 | 固定必看 | 目標、邊界、下一步 | 已觸發；P83 只做 data quality/security，不做 P84 governance。 |
| Ken 型紅隊 / 技術長 | 固定必看 | 技術假設、安全邊界 | 已觸發；XSS、raw leak、debug bundle 外洩是本 Phase 核心風險。 |
| Patric 型使用者端審查官 | 固定必看 | 是否誤解或死路 | 已觸發；0 posts 必須避免被誤讀成正常無聲量。 |
| Jimmy 型文件主筆 | 改 docs / handoff | 可追溯與來源 | 已觸發；需補 TASK_HISTORY 與 handoff 狀態。 |
| Marcus 型數據分析師 | 涉及數據判斷 | 定量/定性分清 | 已觸發；source health score 是運維指標，不是完整輿情結論。 |
| Oliver 型設計審查 | 涉及 UI | 視覺與 A11y | 條件觸發；不改 layout，但錯誤狀態文案需避免誤導。 |
| Penny 型 CFO | 涉及成本 | API 成本與停損 | 已觸發；本 Phase 不新增外部 API，避免品質檢查帶來成本。 |
| Jason 型執行 / DevOps | 涉及 CI/Git | 可執行性與 rollback | 已觸發；doctor/CI 先 advisory，避免立刻阻斷 daily。 |

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | 0 posts 可能代表來源掛掉，不是社群沒聲量，若 promote 會誤導主公。 | **S** | 0 | 0 posts anomaly 必須寫入 manifest/doctor，並提供 promotion 參考。 | 入計畫範圍 |
| 2 | 玩家文章標題含 `<script>`，若模板某處使用 safe 或字串拼接會造成 XSS。 | **S** | 0 | 加 XSS payload 測試，檢查公開 HTML 只出現 escape 後內容。 | 入計畫範圍 |
| 3 | debug bundle 若加入 quality snapshot，可能把 raw content 或 secret 一起寫出。 | **S** | 0 | 設 raw/sanitized 白名單，只寫 count/hash/reason，不寫原文。 | 入計畫範圍 |
| 4 | LLM schema guard 太嚴，可能把可用降級報告全擋掉。 | A | 0 | 先分 fail/degrade，不一律 blocking；門檻留在 P83 計畫中明列。 | 入計畫範圍 |
| 5 | source health score 可能被誤用成真實社群聲量品質分。 | A | 0 | 文件標明它是 pipeline 觀測健康指標，不代表全網完整性。 | 入計畫範圍 |
| 6 | P83 若順手改 prompt/provider，會把品質治理變成模型重構。 | A | 0 | 非範疇明確禁止，不更換 provider 或大改 prompt。 | 入計畫範圍 |

## 16. 狀態機

`DRAFT -> FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED`

目前狀態：`CLOSED`。P83 已收官；新視窗不可再改 P83，下一步只能進 P84 DRAFT 起草 `docs/PHASE_84_PLAN.md`。
