# Phase 117 — 完成 gov.preflight 統一總指揮：註冊散落 checker + 接管 CI（對齊 Hermes Sentinel）（草案 v1，待阿喜核准）

> 狀態：**v1 已凍結 + S1-S5 收官（2026-06-15，阿喜核准 + lint M1/M2 PASS）**
>
> **動工偏離記錄（誠實，非重大分歧）**：
> 1. **加 `ci` 到 `gov/preflight.py` 的 `--profile` choices**（1-token，原寫死 [fast,full] 會拒 ci）——必要的「啟用新 profile」非重寫編排器邏輯。
> 2. **report_health run 字串含 `--check-git-clean`**——faithful 對齊原 CI Health step。
> 3. **report_content_trust 延後、report_credibility 排除**：content_trust 的 `--date` 無 today 預設（要嘛改 checker 加預設、要嘛 {date} 注入，v1 不碰 checker 故延後）；credibility 的 CLI 是 `sys.argv[1]` 檔案參數式（非 --date）且已在 main.py:722 inline 跑 → 排除。實際註冊 9 個（ci 4 + full 5：report_health/system_doctor/report_freshness/slo + known_issue_guard/artifact_hygiene/root_legacy/handoff_truth/no_fake_stats）。
> 戰線：**治理 / 部署（CI）**——把 Hermes `Sentinel.preflight` 的「一鍵總指揮」優勢補齊到 AOV。
> 鐵律：`py` 不用 `python`（CI yaml 內 python 是 Linux runner 正確；config 內 `run` 字串於 CI 跑故用 python）；TASK_HISTORY 禁全讀；改動前計畫書等同意；push 前問阿喜；**不重寫既有 `gov/preflight.py`（已存在），只註冊 + 接管**。

> 📎 緣由（跨專案飛輪盤點，2026-06-15）：阿喜回報 Hermes 飛輪有一項優於 AOV——`Sentinel.preflight()` 統一總指揮，而 AOV「十餘支 checker 散落、無單一入口」。**交叉核對翻案**：AOV 的 `gov/preflight.py`（P103 從 skills-governance 快照）**早已是該總指揮**（blocking/warning 分級 + 防遞迴 GOV_PREFLIGHT_RUNNING = Hermes 設計 + 讀 config），跨專案 audit 只看 `scripts/check_*` 散落腳本、漏看 `gov/preflight.py`。**真正缺口＝編排器只註冊 4 個 check，10+ 個 `scripts/check_*`/slo/hygiene 全沒註冊進去 → 跑起來不是「全部」**。故本 Phase 是「完成既有編排器的註冊 + 接管 CI」，非重造。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P117 |
| **Phase 名稱** | gov.preflight 統一總指揮：註冊散落 checker + 接管 CI |
| **影響半徑** | **標準（4 檔：governance_config.yaml + daily_report.yml + 新測試 + 收官文件）─ META3** |
| **預估投入** | 3-4 h |
| **負責模型** | Opus 4.8（CI 同源邊界 + checker 介面異質對齊） |
| **前置 Phase** | P103（gov/ 套件回填）；P115（CI scan_secrets/slo 個別 step，本 Phase 將其 DRY 收斂） |

## 0.5 狀態轉換清單 ─ B-002

| 對象 | 原狀態 | 新狀態 | 轉換條件 | 執行者/核准者 |
|---|---|---|---|---|
| gov.preflight 覆蓋面 | 4 check（secret_scan/guard_assertions/governance_doctor/tests）| 全 checker 註冊（+report 類×6 + dev/治理類×4，分 fast/full/ci profile）| 註冊 config + 驗每個 CLI 可跑 + CI 改呼叫 | AI 實作/阿喜核准 |
| CI checker 呼叫 | 個別 step（health/doctor/freshness/slo/scan_secrets 各一）| `py -m gov.preflight --profile ci` 一句（DRY 同源）| 接管 CI + 真驗證待 cron | AI 實作/阿喜核准 |

---

## 1. 目標 (Objective)

把 AOV 散落的 ~10+ 個 checker 註冊進**既有的** `gov/preflight.py` 編排器（`governance_config.yaml` profiles），使 `py -m gov.preflight --profile full`（開發 push 前）/ `--profile ci`（CI 報告產後）真正「一鍵跑完全部 + 統一 blocking/warning 分級 + 一張總表 + 防遞迴」；並讓 `daily_report.yml` 改呼叫 `gov.preflight --profile ci` 取代個別 checker step（DRY，CI 與本地同源）。量化：preflight 註冊 check 從 4 → ~14；CI checker step 從 5 個個別 → 1 句編排。對齊 Hermes Sentinel.preflight #1。

## 2. 觸發背景 (Why Now)

跨專案飛輪盤點指出 AOV「checker 散落無單一入口」。交叉核對發現編排器已存在（gov/preflight.py），但 governance_config.yaml 只註冊 4 個 check——10+ 個 `scripts/check_*`（report_health/freshness/credibility/content_trust/no_fake_stats）+ slo + dev-hygiene（known_issue_guard/artifact_hygiene/root_legacy/handoff_truth）全沒進去。P115 才剛在 daily_report.yml 個別加 scan_secrets/slo step——正好本 Phase DRY 收斂進 preflight。

## 3. Entry Criteria

- [x] 前置：P103 gov/ 套件已回填（gov/preflight.py + gov/assertions.py + governance_config.yaml 存在已查證）
- [x] 9 個 scripts/check_*.py 皆有 CLI 入口（grep 確認 `__main__`/argparse/main）
- [ ] **驗證盲區群檢查（B-023/024/027，PHASE_TEMPLATE v1.3）**：本 Phase 接管 CI＝改現有行為，動工前 S1 親核每個 checker 的真實 CLI 呼叫 + exit 語義（advisory always-0 vs exit-1）+ CI 現行 continue-on-error 行為，確認接管不改可觀察結果。
- [ ] 阿喜核准本計畫書凍結

## 4. Exit Criteria

- [ ] **A（註冊）**：`governance_config.yaml` checks 區新增 ~10 個 checker（report_health/freshness/credibility/content_trust/no_fake_stats/slo + known_issue_guard/artifact_hygiene/root_legacy/handoff_truth），各標 level（report 類 warning 對齊現行 advisory；secret_scan/guard_assertions/tests 維持 blocking）+ timeout + `run` 字串（report 類內嵌 `--date $(TZ=Asia/Taipei date +'%Y-%m-%d')`）
- [ ] **B（profile）**：`fast`=secret_scan+guard_assertions（維持，秒級 commit 前）；`full`=fast+governance_doctor+tests+dev/治理類×4（push 前 repo-state）；新增 `ci`=secret_scan+report 類×6（CI 報告產後驗證）
- [ ] **C（每個 CLI 可跑）**：S1 逐一本地跑每個註冊的 `run` 字串確認 exit 0/非0 行為符合 level 設定；無法乾淨跑的（需特殊 context）排除並記錄理由（不硬塞）
- [ ] **D（接管 CI）**：`daily_report.yml` 把 P115+既有個別 step（scan_secrets/health/system_doctor advisory/freshness/slo）換成一句 `py -m gov.preflight --profile ci`（`continue-on-error: true` 保 advisory 不阻斷日報）；`if: failure()` Telegram 告警（P115）+ System Doctor Strict Gate（workflow_dispatch）保留不動
- [ ] **E（測試）**：`tests/test_gov_preflight.py`——①`run_profile` 跑一個受控 profile 聚合正確（blocking/warning 分級）②防遞迴 guard（GOV_PREFLIGHT_RUNNING=1 時略過）③config profiles 引用的 check id 都存在於 checks（防孤兒引用）④**不在測試內跑 `full`/`tests` profile**（避免 pytest→preflight→pytest 遞迴，靠 guard + 受控 profile 雙保險）
- [ ] **F**：全套零回歸（基線 520）；`py -m gov.preflight --profile fast`/`full`/`ci` 本地實跑各印出總表 + 正確退出碼
- [ ] **G**：收官件套（TASK_HISTORY + runbook「一鍵自檢入口」一節 + RISK 登記 checker 散落已收斂 + memory）；CI 接管真驗證待下次 cron（明告）

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 3-4 h |
| 收益等級 | **中-高**（補 Hermes 對標的真實治理缺口；一鍵自檢入口 + CI/本地同源 DRY；未來新 checker 只需註冊一處）|
| ROI | ✅ 高（不重造、復用既有編排器；config 註冊為主 + CI DRY；防止「checker 散落、改 CI 漏跑某個」）|

---

## 6. 17 層稽核表 ─ META2

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | config 註冊（宣告式）+ daily_report.yml 一句取代多 step + 新測試 | run 字串 CLI 呼叫錯/exit 語義誤判 | S1 逐一本地實跑每個 run 字串驗 exit；不重寫 preflight |
| **2. 邏輯** | profile 分級（fast/full/ci）+ level（blocking/warning）對齊現行 advisory | 接管 CI 改變可觀察結果（原 advisory 變 blocking 擋日報）| report 類全 warning + CI step continue-on-error；逐位元對齊現行行為 |
| **4. 測試** | test_gov_preflight 驗聚合/分級/防遞迴/孤兒引用 | 測試內跑 full→pytest 遞迴 | 受控 profile + 防遞迴 guard 雙保險，測試不跑 full/tests |
| **10. 安全** | secret_scan 維持 blocking 進 ci profile；不新增授權/外呼 | 接管後 secret_scan 漏跑 | ci profile 明列 secret_scan；保留為 blocking |

### A 級（提示填）
| 層 | 採用/N-A | 風險 | 緩解 |
|---|---|---|---|
| **3. 架構** | 復用既有 gov/preflight 編排器，只註冊（DRY 收斂散落 checker）| 過度集中單點 | preflight 已有防遞迴 + per-check timeout + 分級，單點失敗 graceful |
| **6. 可觀察性（核心）** | 一張總表（per-check PASS/WARN/FAIL + tail + runbook 指針）取代散落輸出 | always-0 advisory checker 在表中恆顯 PASS | 計畫書/runbook 明記：always-0 checker 的告警看 tail 輸出非 status；必要時該 checker 改回非0 |
| **7. 韌性** | per-check timeout + 防遞迴 + CI continue-on-error 降級 | 某 checker 掛住拖垮編排 | per-check timeout（config 既有）+ subprocess 隔離 |
| **11. 部署（核心）** | daily_report.yml 接管（DRY）| CI 真驗證無法本地跑 | YAML 驗證 + 本地實跑 gov.preflight；真驗證待 cron（同 P111 S3/P115）|
| **13. 可維護性** | 未來新 checker 只註冊 config 一處 + runbook 入口 | config 漂移 | test 驗 profile 引用無孤兒 + runbook 記入口 |
| **14. 文件** | 計畫書 + TASK_HISTORY + runbook + RISK + memory | — | 收官件套 |
| **15. 流程** | 標準 Phase（5 stage）| — | — |

### B 級（條件式）
| 層 | 觸發 | 採用 | 風險 | 緩解 |
|---|---|---|---|---|
| **12. 成本** | CI 改動 | preflight subprocess 各 checker 零 LLM/零外呼 | 比個別 step 略慢 | post-pipeline 跑、可接受；per-check timeout |
| **8 效能/9 UX/16 隱私/17 i18n** | 未觸發 | — | — | N/A |

### 層級互鎖 ─ META5
- [x] Logic→Testing｜[x] Architecture→Documentation（接管 CI 動部署→文件）｜[x] Security→Testing｜[ ] Performance→N/A

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| governance_config.yaml 註冊 check | 可逆（git revert）| 宣告式、不改 checker |
| daily_report.yml 接管 CI | 可逆（git revert 回個別 step）| YAML 驗證 + 本地跑 |
| 新增 test_gov_preflight | 可逆 | — |
| push 本改動 | 半可逆 | **push 前問阿喜** |

### X2 盲區掃描
- [x] always-0 advisory checker 在總表恆顯 PASS（看 tail 非 status）——明記 runbook
- [x] CI 接管後若某 checker 行為與原個別 step 不同（如 expected-mode 參數）——S1 逐位元對齊
- [x] 系統狀態：一鍵入口存在但團隊/未來是否真用——runbook 記入口 + commit hook 可選（不本期）

### X3 時間敏感性
- 草案 2026-06-15；gov/preflight 為 skills-governance 快照（非 live 引用），上游升級需人工重快照（既有狀態，非本 Phase 惡化）

### X4 多角度審查
- **主公**：阿喜要對齊 Hermes 一鍵總指揮。翻案發現 AOV 已有編排器，本 Phase 完成註冊 + 接管 CI。
- **紅隊**：見 M2。
- **接手者**：未來新 checker 只註冊 governance_config.yaml 一處；runbook 記 `py -m gov.preflight` 為一鍵自檢。
- **X4-J 自動化邊界**：preflight 為規則型啟發式（末行已有召回率免責）；只報告/分級，不 auto-fix。
- **X4-K 使用者端審查官**：明告「一鍵入口跑的是已註冊的 checker；註冊清單即覆蓋邊界，未註冊的不會被跑」。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| RP1 | 接管 CI 改變可觀察行為（advisory 變擋日報）| 中 | 高 | 部署 | report 類全 warning + CI gov.preflight step `continue-on-error: true`；S1 逐位元對齊現行 |
| RP2 | 某 checker 無乾淨 CLI / 需特殊 context 跑不動 | 中 | 中 | 代碼 | S1 逐一本地實跑；跑不動的排除 + 記理由（不硬塞）|
| RP3 | always-0 advisory checker 在總表恆顯 PASS、告警被埋 | 中 | 低 | 可觀察 | runbook 明記看 tail；必要時該 checker 改非0（列 future，非本期）|
| RP4 | 測試內跑 full→pytest→preflight 遞迴 | 低 | 中 | 測試 | 防遞迴 guard + 測試用受控 profile（不跑 full/tests）雙保險 |
| RP5 | CI 真驗證無法本地跑 | 中 | 低 | 部署 | YAML 驗證 + 本地實跑 gov.preflight 三 profile；真驗證待 cron（明告，同 P111 S3）|
| RP6 | report 類 run 字串日期注入（$(date)）在 CI bash 正確、本地 Win 不同 | 低 | 低 | 代碼 | CI 走 bash（Linux runner）正確；本地驗用固定 --date 跑 |

**META4 加權**：RP1 高影響但已用「report 類 warning + continue-on-error + 逐位元對齊」緩解 → 緩解後中。<5，無須請示（阿喜已核准方向）。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 驗收 |
|---|---|---|
| **S1 checker CLI 盤點** | 逐一本地實跑 9 個 check_* + slo 的 CLI（含所需 args + exit 語義 advisory-0 vs exit-1），記錄可註冊清單 + 排除項理由；對齊現行 CI 個別 step 的參數（expected-mode/threshold/window-days）| 每個註冊候選有可跑指令 + exit 語義表 |
| **S2 config 註冊** | `governance_config.yaml` checks 區補 ~10 checker（level/timeout/run）+ profiles 補 full（+dev/治理類）+ 新增 ci（report 類）| `py -m gov.preflight --profile fast/full/ci` 本地各跑出總表 |
| **S3 接管 CI** | `daily_report.yml` 把個別 checker step 換成 `py -m gov.preflight --profile ci`（continue-on-error）；保留 failure-alert + Strict Gate | YAML 解析 + step 邏輯對齊現行 advisory |
| **S4 測試** | `tests/test_gov_preflight.py`（聚合/分級/防遞迴/孤兒引用，受控 profile 不跑 full/tests）| 全套 520→+N passed 零回歸 |
| **S5 收官** | TASK_HISTORY + runbook（一鍵自檢入口節）+ RISK（checker 散落收斂）+ memory | 件套齊 |

---

## 10. 影響檔案清單 ─ STR7

**修改**：`governance_config.yaml`（註冊 ~10 checker + profiles）、`.github/workflows/daily_report.yml`（接管 CI，個別 step → gov.preflight）
**新增**：`tests/test_gov_preflight.py`
**收官**：`TASK_HISTORY.md` / `docs/RISK_REGISTRY.md` / `docs/OPERATIONS_RUNBOOK.md`（一鍵入口節）
**不碰**：`gov/preflight.py`（已存在、不重寫）、各 `scripts/check_*.py` 邏輯（只註冊不改）、failure-alert/Strict Gate（P115/既有保留）

---

## 11. Postmortem 預埋點 ─ G6

位置：`docs/postmortems/2026-06-15-phase-117-preflight-consolidation.md`（若觸發）

> **通則1（先查再造）**：跨專案/跨工具「對方比我好」的盤點，落地前必先交叉核對本專案是否已有等價機制（本 Phase：AOV 已有 gov/preflight，audit 過時）——別照搬重造已存在的東西（呼應 B-027 親核 + B-028 反膨脹）。
> **通則2（散落收斂）**：同類工具（checker/guard）累積到 ~10+ 個時，需一個宣告式註冊的單一入口，否則「改流程漏跑某個」遲早發生；入口存在 ≠ 已收斂，要驗證全部都註冊進去。

---

## ✈️ Pre-flight 多視角體檢 ─ STR10

### M1 強制填表（十一視角）

| 視角 | 發現 |
|---|---|
| **X4-A 紅隊** | 見 M2。核心：接管 CI 改 advisory 行為（warning+continue-on-error 對齊）；checker 無 CLI（S1 排除）；always-0 告警被埋（runbook）；測試遞迴（guard+受控 profile）。 |
| **X4-B 接手者** | 未來新 checker 只註冊 config 一處；runbook 記 `py -m gov.preflight` 入口；test 防孤兒引用。 |
| **X4-C 災難** | 某 checker 掛→per-check timeout + subprocess 隔離 + CI continue-on-error，不拖垮日報。 |
| **X4-D 5 年後** | gov/preflight 是 skills-governance 快照（X3）；config 宣告式易讀；接手者一眼看 profiles 知覆蓋面。 |
| **X4-E 終端 vs IDE** | 本地 py 跑三 profile 驗；CI 走 python（Linux runner）。 |
| **X4-F 跨平台** | run 字串日期注入 $(date) CI bash 正確；本地 Win 驗用固定 --date；`_resolve_python` 已處理 Win python stub。 |
| **X4-G 主公視角** | 阿喜要對齊 Hermes 一鍵總指揮。明告：翻案發現已有編排器，本 Phase 是完成註冊 + 接管 CI，非重造。 |
| **X4-H 觀測/治理** | 把散落各處的 checker 輸出收斂成一張總表（per-check PASS/WARN/FAIL + tail + runbook 指針），CI 與本地用同一個 `gov.preflight` 入口、同源同分級，未來新增 checker 只註冊 config 一處即全鏈生效。 |
| **X4-I 主公可見性** | 不新增任何對外發布/推播行為（僅整合既有 checker）；阿喜端可見變化是 CI log 從 5 段分散輸出整合成一張總表，更易一眼判讀今日治理狀態；本地也能 `py -m gov.preflight` 一鍵自檢。 |
| **X4-J 自動化邊界** | preflight 規則型啟發式、只報告分級不 auto-fix、末行召回率免責。 |
| **X4-K 使用者端審查官** | 誤解「一鍵=跑了所有可能檢查」→明界定：跑的是**已註冊**的 checker，註冊清單＝覆蓋邊界。 |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | **【S 級】** 接管 CI 後 report 類 checker 從 advisory（continue-on-error）變成 gov.preflight blocking → 一次 freshness/credibility 告警就擋掉/中斷日報？ | S | 0 | report 類全標 `level: warning`（gov.preflight warning 不進 blocking、exit 0）+ CI gov.preflight step `continue-on-error: true` 雙保險；S1 逐位元對齊現行個別 step 的 advisory 行為。 | 入計畫（RP1+S1/S3）|
| 2 | **【S 級】** `full` profile 含 `tests`，測試跑 gov.preflight 會 pytest→preflight→pytest 無限遞迴？ | S | 0 | 防遞迴 guard（GOV_PREFLIGHT_RUNNING=1 子進程略過，gov/preflight.py:34 已驗）+ test_gov_preflight 用受控 profile（不跑 full/tests）雙保險。 | 入計畫（RP4+S4）|
| 3 | 某 checker 無乾淨 CLI / 需特殊 context（如 check_report_credibility 原是 import-only）跑不動？ | A | 0 | S1 逐一本地實跑；9 個 check_* 已驗有 __main__；跑不動的排除 + 記理由（不硬塞、不為註冊而註冊）。 | 入計畫（RP2+S1）|
| 4 | always-0 advisory checker（如 freshness sys.exit(0)）在總表恆顯 PASS、凍結告警被埋？ | A | 1（checker 既有設計）| runbook 明記「看 tail 輸出非 status」；必要時該 checker 改回非0（列 future，非本期惡化）。 | 入計畫（RP3）|
| 5 | 重造了已存在的 gov/preflight？ | A | 0 | **明確不重寫** gov/preflight.py（已存在）；本 Phase 只動 config 註冊 + CI 接管 + 測試。通則1 防「先查再造」。 | 入計畫（§10 不碰清單）|
| 6 | CI 真驗證無法本地跑、會不會帶 bug 上 production？ | B | 0 | YAML 解析 + 本地實跑三 profile + S1 逐位元對齊現行；真驗證待 cron（同 P111 S3/P115 已驗模式）。 | 入計畫（RP5）|

> 未解質疑：無。

---

## 12. 凍結戳記（待填）

- **凍結人**：（待阿喜核准）+ Claude（Opus 4.8 1M）
- **凍結依據**：（待）M1/M2 PASS + 阿喜核准 + 交叉核對翻案（AOV 已有 gov/preflight、本 Phase 只完成註冊+接管）

---

*狀態：草案 v1，待阿喜核准。受 17 層框架 v3.1 + STR1/STR10 保護。建立 2026-06-15（跨專案 Hermes 飛輪盤點觸發，交叉核對翻案後右尺寸為「完成既有編排器」）。*
