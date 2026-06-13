# Phase 111 — CI 報告自癒：偵測報告缺漏自動 replay 重產（飛輪 L4→可控 L5）（v3，已凍結 2026-06-14）

> 狀態：**v3 已凍結（2026-06-14，兩輪飛輪 8 視角對抗審查後修訂，動工前）**
> 戰線：**治理 / 部署（CI 自癒）+ 韌性**——把飛輪交付面從 L4（人工 replay）升到**可控 L5**（偵測→自動修復，**自癒發布決策與正常 cron 同源**）
> 鐵律：`py` 不用 `python`（CI yaml 內 python 是 Linux runner 正確）；TASK_HISTORY 禁全讀；改動前計畫書等同意；push 前問阿喜；**自動修復只重渲染窄面、零額度、不繞品質閘門、不發布 cron 本來不會發布的報告**。

---

## 📜 緣由與兩輪對抗審查

飛輪自我修復審查（2026-06-13）結論：**飛輪無真 L5 自我修復**，多數元件停 L3。最高 ROI 補強 = 把已備的人工 recovery 工具（`replay_run.py`，零 LLM 重渲染）接成偵測驅動。

### 🔴 第一輪對抗審查（2026-06-14，4 視角）揪出 S 級致命洞
report 缺的**最常見原因是品質閘門「刻意」不發布**（main.py:706 寫 analysis → :716 `generate(promote=False)` → :780 `should_promote` 不過閘則 :793 跳過 → analysis 在 report 缺）。原方案 replay 用 `generator.py:94` 預設 `promote=True` 會**自動發布劣質報告到首頁**。→ 修正方向「self-heal 必須與 cron 用同一把尺判發布」。

### 🔵 第二輪對抗審查（D-lite 落地壓測，4 視角）收斂 9 項必修 + 揪出 P110 既有缺陷
採 **D-lite+**：self-heal 重產 candidate(`promote=False`) → 跑**與 main.py 逐位元相同的發布閘門** → 通過才 promote。落地壓測（編排/等價/紅隊/測試）確認可收官，並揪出：①`run_checks` 參數必須逐位元複製 main.py（尤其 `check_landing=False`）②`should_promote` 抽純函數共用防漂移 ③**freshness sidecar 在 `generate(promote=False)` 時無條件寫（generator.py:422）→ no-op 留孤兒污染 P110 凍結偵測器，cron 路徑也有此既有缺陷**。阿喜核准：純函數共用 + sidecar 受 promote gate（飛輪修，一併解 cron）+ scope 微→標準。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P111 |
| **Phase 名稱** | CI 報告自癒（self-heal 重產報告，發布決策與 cron 同源，可控 L5）|
| **凍結日期** | （待阿喜凍結）|
| **影響半徑** | **標準（4-6 檔：daily_report.yml + replay_run.py + run_manifest.py + main.py 1行 + generator.py + 新測試）─ META3** |
| **預估投入時數** | 4-5 h |
| **Token budget** | ~120K tokens（含兩輪對抗審查已花）|
| **負責模型** | Opus 4.8（發布閘門互動 + 安全邊界 + 跨核心檔對齊）|

## 0.5 狀態轉換清單 ─ B-002

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者/核准者 |
|---|---|---|---|---|---|
| 飛輪交付面 | L4（人工 CLI replay）| 可控 L5（CI 偵測→自動 replay 重產）| 可控 L5 = 限重渲染窄面、零額度、可驗證、可回退、**發布決策與 cron 同源（不繞閘門）** | self-heal + 同源閘門 + 收斂驗證 | AI 實作/阿喜核准 |

---

## 1. 目標 (Objective)

在 CI（daily_report.yml）加自癒線：`main.py --run-now` 後若 **canonical 報告缺漏**，自動跑 `replay_run.py --date today --heal-if-missing --check-health`：用既有 analysis 重渲染 candidate(`promote=False`) → **跑與 main.py 逐位元相同的發布閘門**（tier publishable + `run_checks` 健康）→ 通過才 promote 發布、否則 no-op + `::warning::` 降級回 L4。**全自動、零 LLM 額度、零重爬、發布決策與正常 cron 同源（不可能發布 cron 本來不會發布的報告）**。重產報告由既有 Fallback Push 推上。量化：飛輪交付面 L4→可控 L5。

## 2. 觸發背景 (Why Now)

飛輪審查證實無真 L5。情境：cron 渲染**意外失敗**（main.py:728 generate 例外被吞，但 analysis 已寫）→ 報告缺漏要人工 replay。接成自動後 CI 自己補產。**但發布決策必須與 cron 同一把尺**（D-lite+ 核心），否則會繞品質閘門自動發布劣質報告。

## 3. Entry Criteria

- [x] 前置：P110 收官；replay_run.py 零 LLM 重渲染（已查證）
- [x] 兩輪飛輪對抗審查完成（致命洞 + 9 項落地必修，Claude 親核 file:line）
- [x] 主公核准凍結（含 L5 安全邊界 + 同源閘門 + scope 標準確認）─ 阿喜 2026-06-14 核准（純函數共用 + sidecar promote gate + scope 微→標準）
- [x] 風險登記簿無未解高風險阻擋

## 4. Exit Criteria

- [ ] **A（同源閘門地基）**：`run_manifest.py` 加 `should_promote(has_candidate, tier, gate_reasons_len)` 純函數；`main.py:780` 改呼叫它（邏輯不變）；`generator.py` 的 `_write_freshness_sidecar` 移入 `if promote` 區塊（sidecar 受 promote gate）
- [ ] **B（replay self-heal）**：`replay_run.py` 加 `--heal-if-missing`：analysis 缺→1；report 缺判定（統一 repo_root，重用 `report_path`）；tier 非 publishable（含空）→no-op+`::warning::`；candidate stem 斷言；`generate(promote=False)`；`run_checks` **逐位元複製 main.py:132-139**（`expected_mode='production', check_git_clean=False, check_landing=False, expected_report_path=candidate`）；`should_promote` 純函數判定→conditional `promote_candidate`；manifest 移到 promote 後反映 promoted/no-op
- [ ] **C（CI step）**：daily_report.yml 在 Upload Artifact(89) 後、Fallback Push(91) 前加 step；`TZ=Asia/Taipei`；**不加 if:always()**；`|| echo ::warning::` 不阻斷
- [ ] **D（可觀察）**：`::warning::` 由 heal Python print（觸發/no-op/失敗）；manifest 標 `self_heal`/`promoted`
- [ ] **E（G-i 端到端）**：`tests/test_self_heal_replay.py` 真實跑 `generate`（棄 `_fake_generate` 寫死路徑）5 case + 三道隔離（index_file 導 tmp / patch news_indexer / chdir），跑完 `git status` 真 repo 零改動：①缺+publishable+health pass→promote+canonical+index 指向+manifest is_backfill ②tier 非 publishable（含空）→no-op+::warning:: ③publishable+health fail→candidate 在但不 promote+index 未改 ④report 在→no-op 零副作用(mtime 不變+generate 未呼叫) ⑤analysis 缺→1
- [ ] **F（G-ii 零額度 guard）**：subprocess 乾淨進程 `import scripts.replay_run` 後斷言 `sys.modules` 不含具體 LLM client（`openrouter_client`/openai/google.genai/httpx 等，**不列 Protocol base**）；失敗訊息印實際命中
- [ ] **G**：全套零回歸（基線 504）含 P110 freshness 測試；YAML 驗證；收官件套 + 飛輪成熟度 L4→可控 L5 + RISK/postmortem

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 4-5 h |
| 收益等級 | **高** |
| 收益 | 飛輪首個真 L5（發布決策與 cron 同源）；報告意外缺漏自動補產；零額度；**對抗審查擋下「繞閘門自動發布」釀禍 + 順帶修 P110 sidecar 既有缺陷 + 立 should_promote 共用防漂移**|
| ROI | ✅ 高（雖 scope 升標準，但每處皆對抗審查證據撐腰、高 ROI 防復發 guard）|

---

## 6. 17 層稽核表 ─ META2

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | replay self-heal gate + run_manifest should_promote 純函數 + generator sidecar gate + CI step | 多檔協同、run_checks 參數、日期 TZ | gate 下沉 Python 可測；run_checks 逐位元複製 main.py:132-139；TZ=Asia/Taipei；純函數零依賴 |
| **2. 邏輯** | self-heal 發布決策**與 main.py:780 逐位元同源**（should_promote 共用）；tier publishable + run_checks 同尺 | 繞閘門發布劣質報告 / 漂移 / 誤觸發 | should_promote 純函數共用（物理防漂移）；run_checks 同參數；tier 空→no-op；三組合已驗等價 |
| **4. 測試** | G-i 真跑 generate 5 case + 三隔離 + G-ii sys.modules subprocess 零額度 | monkeypatch 寫死路徑繞契約 / session 污染假紅 | 棄 `_fake_generate` 真跑釘三方路徑契約；G-ii 乾淨進程驗；黑名單鎖具體 client 名 |
| **10. 安全（核心）** | 零 LLM/零重爬/零額度/不可逆不碰/**不繞閘門（同源 should_promote）**；既有 Fallback Push 不新增授權；G-ii 執行期零外呼 guard | 自動發布劣質報告 / 燒額度 | should_promote 共用 + run_checks 同尺；replay 零 LLM 已查證 + G-ii sys.modules 實測 158 模組零 SDK |

### A 級（提示填）
| 層 | 採用/N-A | 風險 | 緩解 |
|---|---|---|---|
| **3. 架構（核心）** | 抽 `should_promote` 純函數至 run_manifest，main.py + replay 共用（DRY 同源）| 抽函數破壞 main.py 既有行為 | 純搬一行 AND 邏輯、main.py 既有測試零回歸驗證 |
| **5. 資料** | replay 用既有 analysis 重渲染（不改數據）；sidecar 受 promote gate | analysis 壞 / sidecar 孤兒 | quarantine 隔離；**sidecar 移入 if promote（解 self-heal + cron 孤兒）**|
| **6. 可觀察性** | `::warning::` Python print + manifest self_heal/promoted/is_backfill | 靜默自癒 / manifest 失真 | manifest 移到 promote 後反映實況；no-op 不標假發布 |
| **7. 韌性（核心）** | 失敗 graceful 降級 L4 + health check 仍報 | replay 崩潰中斷 CI | step 不阻斷、不加 if:always()、不無限重試 |
| **13. 可維護性** | self-heal step 註解 + replay_run docstring 反向指針 + should_promote 共用 | 誤擴大 / 改 replay 破前提 / 兩把尺漂移 | 註解 + docstring 契約 + G-ii guard + 純函數物理共用 |
| **14. 文件** | 計畫書 + TASK_HISTORY + postmortem + RISK + runbook | — | 收官件套 |
| **15. 流程** | 標準 Phase（5 stage）| — | — |

### B 級（條件式）
| 層 | 觸發 | 採用 | 風險 | 緩解 |
|---|---|---|---|---|
| **11. 部署（核心）** | 改 daily_report.yml | self-heal step | CI step 失敗中斷 | `\|\| echo ::warning::` + 不加 if:always() + 置 Fallback Push 前 |
| **12. 成本** | CI 自動動作 | replay 零 LLM（重渲染）| 誤觸發 / transitive import 破前提 | replay 零 LLM 已查證 + G-ii sys.modules 執行期斷言 |
| **8 效能/9 UX/16 隱私/17 i18n** | 未觸發 | — | — | N/A |

### 層級互鎖 ─ META5
- [x] Logic→Testing｜[x] Architecture→Documentation（抽 should_promote 動架構→文件）｜[x] Data→Maintainability｜[x] Security→Testing｜[ ] Performance→N/A

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| run_manifest 加 should_promote 純函數 + main.py:780 改呼叫 | 可逆（git revert，邏輯不變）| 既有測試驗 |
| generator sidecar 移入 if promote | 可逆（git revert）| P110 freshness 測試驗不回歸 |
| replay_run 加 --heal-if-missing | 可逆（預設不傳旗標行為不變）| — |
| CI 自動重產**通過閘門**報告 + 發布 | 半可逆、對外可見 | **同源 should_promote 保證不發布 cron 本不發布的** |
| CI 自動 push（既有 Fallback Push）| 半可逆 | 沿用既有授權，不新增 |
| push 本計畫改動到 origin | 半可逆 | **push 前問阿喜** |

### X2 盲區掃描
- [x] log：`::warning::` 觸發/no-op/失敗（Python print）
- [x] 中間檔：manifest 標 self_heal/promoted/is_backfill；**sidecar 受 promote gate（no-op 不留孤兒）**
- [x] 系統狀態：CI 在報告意外缺（且通過閘門）時自動補產發布；不通過閘門則 no-op
- [x] 已知限制（future）：no-op 的 candidate 檔仍被 Fallback Push 撈進版控 + GitHub Pages 直連 URL（cron 既有行為，非 P111 惡化，登記 R-038）

### X3 時間敏感性
- 凍結日期：（待）／過期日期：2026-09-14／風險帶日期：✅
- replay_run / should_promote / evaluate_publish_gate / sidecar 任一改動需重審 L5 前提與同源性

### X4 多角度審查
- **主公**：阿喜要飛輪真有全自動 L5。D-lite+ 全自動 + 發布決策與 cron 同源（should_promote 共用）+ 順帶修 P110 sidecar 缺陷。
- **紅隊**：繞閘門（should_promote 共用 + run_checks 同尺修）、燒額度（G-ii sys.modules 實測零 SDK）、漂移（純函數物理共用）、sidecar 孤兒（promote gate）、半發布（步驟6 後驗 index）。
- **接手者**：should_promote 共用一行邏輯、docstring 反向指針、G-i 真跑釘三方路徑契約。
- **X4-J 自動化邊界**：確定性條件觸發 + 同源閘門，非啟發式；自動執行故嚴守同源 + 失敗降級 + log。
- **X4-K 使用者端審查官**：明告自動補產僅限「通過 cron 同款閘門」的報告；不通過則 no-op；no-op candidate 仍進版控（cron 既有，R-038 登記）。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| **R7** | 自動 replay 繞品質閘門發布劣質報告 | 中 | 高 | 安全 | **should_promote 純函數與 main.py 共用 + run_checks 逐位元同尺**；不可能發布 cron 本不發布的 |
| **R11** | run_checks 參數漂移破「同一把尺」（尤其 check_landing 漏 False → 自癒永遠降級）| 中 | 高 | 代碼 | 逐位元複製 main.py:132-139 + G-i case 驗；計畫書/註解明寫 |
| **R10** | should_promote 兩把尺漂移（未來改 main.py 不同步）| 中 | 中 | 可維護 | **抽純函數物理共用一行**；測試只護一行 |
| **R9** | freshness sidecar 孤兒（no-op 留 sidecar 污染 P110 凍結偵測器；cron 也有）| 中 | 中 | 資料 | **sidecar 受 promote gate（一併解 cron）**；P110 freshness 測試驗不回歸 |
| R1 | self-heal 無限循環 | 低 | 中 | 代碼 | 只 report 缺觸發、CI 一 run 一次、no-op 抗重入 |
| R2 | 自動 replay 燒 LLM 額度 | 低 | 中 | 成本 | replay 零 LLM 已查證 + G-ii sys.modules 實測 158 模組零 SDK |
| R3 | replay 失敗中斷 CI | 中 | 低 | 代碼 | `\|\| echo ::warning::` + 不加 if:always() + health check 照跑 |
| R4 | 誤觸發（report 在但內容壞）| 中 | 低 | 業務 | 先只做「report 缺」窄面（登記 future）|
| R5 | YAML/shell/日期 TZ 錯 | 中 | 低 | 代碼 | gate 下沉 Python；TZ=Asia/Taipei 對齊 health check |
| R6 | 自動修復未來誤擴大不可逆 | 低 | 高 | 業務 | 註解 + docstring + postmortem 通則 + 不可逆仍問阿喜 |
| R8 | replay top5 與正式版略異（analysis 空 fallback post.score）| 中 | 低 | 資料 | 已知限制（退化版補救），登記收官 |

**META4 加權**：R7+R11（兩 S 級，已用同源 should_promote + run_checks 同尺緩解）+ R9/R10（A 級，promote gate + 純函數共用緩解）→ 發現時高、緩解後中。**≥5 須請示已執行**——阿喜 2026-06-14 核准採 D-lite+ 完整版 + scope 微→標準。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解風險 | 驗收 |
|---|---|---|---|
| **S1 同源閘門地基** | (a) `run_manifest.py` 加 `should_promote(has_candidate, tier, gate_reasons_len)->bool` 純函數（= `has_candidate and is_publishable_quality_tier(tier) and gate_reasons_len==0`）；(b) `main.py:780` 改呼叫（邏輯不變）；(c) `generator.py` `_write_freshness_sidecar`（:422-427）移入 `if promote:` 區塊（:385，受 promote gate）| R7,R9,R10 | main.py 既有測試 + P110 freshness 測試零回歸 |
| **S2 replay self-heal（D-lite+）** | `replay_run.py` 加 `--heal-if-missing`：①analysis 缺 return1（既有）②report 缺判定（統一 repo_root/config.REPORTS_DIR，重用 `report_path`）→在則 no-op return0 ③`is_publishable_quality_tier(_meta.quality_tier)` 非可發布（含空）→no-op+`::warning::`(區分空/非可發布) return0 ④斷言 candidate.stem==aov_report_date ⑤`generate(promote=False)` ⑥`run_checks` 逐位元複製 main.py:132-139 →gate_reasons ⑦`should_promote(True, tier, len(gate_reasons))`→`promote_candidate`(CI 預設 index_file 改 repo index) 否則 no-op+`::warning::` ⑧manifest 移到此後、標 self_heal/promoted ⑨`--check-health` 僅 promote 時 gate 住。docstring 反向指針 | R7,R11,manifest | gate 單元 + 與 main 等價 + 零 LLM |
| **S3 CI step** | daily_report.yml Upload Artifact(89) 後、Fallback Push(91) 前加 step（不加 if:always()）：`REPORT_DATE=$(TZ=Asia/Taipei date +'%Y-%m-%d'); python scripts/replay_run.py --date "$REPORT_DATE" --heal-if-missing --check-health \|\| echo "::warning::self-heal failed, staying L4"`；註解硬寫窄面+同源邊界 | R3,R5,R6 | YAML 語法 + 位置/條件邏輯 |
| **S4 測試（G-i+G-ii）** | `tests/test_self_heal_replay.py`：G-i 真跑 generate 5 case（見 Exit E）+ 三隔離（index_file→tmp、patch `reporter.generator._indexer.save_index`、chdir tmp）+ 跑後 `git status` 真 repo 零改動；G-ii subprocess 乾淨進程驗 sys.modules 黑名單（具體 client 名，grep 自證） | 全部（防復發）| 5 case 綠 + G-ii 綠 + 504 零回歸 |
| **S5 收官** | TASK_HISTORY + 飛輪成熟度 L4→可控 L5 + RISK（R-037 self-heal 邊界/R-038 no-op candidate 進版控/R8/治本寫序）+ postmortem（同源閘門 + DRY 防漂移 + sidecar gate 通則）+ runbook（查 manifest self_heal/is_backfill）+ memory | — | 件套齊 |

---

## 10. 影響檔案清單 ─ STR7

**新增**：`tests/test_self_heal_replay.py`（G-i 5 case + G-ii）

**修改（核心）**：
- `analyzer/run_manifest.py`（+`should_promote` 純函數 ~3 行）
- `main.py`（:780 改呼叫 should_promote，1 行；邏輯不變）
- `reporter/generator.py`（`_write_freshness_sidecar` 移入 `if promote` 區塊；解 self-heal + cron 孤兒）
- `scripts/replay_run.py`（+`--heal-if-missing` gate ~25 行 + manifest 順序 + docstring 契約）
- `.github/workflows/daily_report.yml`（+1 self-heal step ~6 行）

**修改（收官）**：`TASK_HISTORY.md` / `docs/RISK_REGISTRY.md`

**影響但未直接改**：`scripts/check_daily_report_health.py`（被 import `report_path`/`run_checks`，不改）；`main.py` 的 `evaluate_publish_gate`（被 self-heal 比照其 run_checks 參數，不改）；**治本對象 main.py:728 generate 例外被吞（登記 future，不碰）**

---

## 11. Postmortem 預埋點 ─ G6

位置：`docs/postmortems/2026-06-14-phase-111-ci-self-heal.md`（若觸發）

> **通則1（L5 窄面）**：L5 自動修復限「低風險、可驗證、可回退」窄面；只重渲染、不可逆不碰、push 沿用既有授權。升 L5 先問「自動動作最壞會做什麼」。
> **通則2（同源閘門，核心）**：**自動修復的「發布/對外」決策必須與被修復系統用同一把尺（物理共用同一行 `should_promote`），不可自己簡化判定**——本專案 report 缺主因是品質閘門刻意擋下，self-heal 若自己決定 promote 會繞閘門發布劣質報告。run_checks 參數（尤其 check_landing）也要逐位元對齊，否則尺鬆/緊。
> **通則3（前提機器化）**：L5 零額度前提用 `sys.modules` 執行期斷言機器化（subprocess 乾淨進程，鎖具體 client 名非 Protocol base），勝過掃頂層 import 字串。
> **通則4（生命週期綁定）**：副作用檔（sidecar）的生命週期必須綁在它代表的事件（發布）上——sidecar 該受 promote gate，否則 candidate-only/no-op 路徑留孤兒污染下游偵測器。

---

## ✈️ Pre-flight 多視角體檢 ─ STR10（凍結前必過）

### M1 強制填表（十一視角）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | (0) 致命：promote=True 繞閘門→**should_promote 共用 + run_checks 同尺修**；(1) run_checks 參數漂移（check_landing 漏 False→自癒永降級）→逐位元複製 main.py:132-139；(2) sidecar 孤兒污染凍結偵測器→promote gate；(3) 無限循環→no-op 抗重入；(4) 燒額度→G-ii sys.modules 實測零 SDK；(5) 半發布→步驟6 後驗 index。零新 secret/零付費。 |
| **X4-B 接手者** | should_promote 共用一行 + replay_run docstring 反向指針 + self-heal step 註解 + postmortem 4 通則；G-i 真跑釘三方路徑契約防腐化。 |
| **X4-C 災難情境** | self-heal step 崩潰中斷 CI → `\|\| echo ::warning::` 不擴散 + 不加 if:always() + 後續 health check 照跑 + 降級 L4。 |
| **X4-D 5 年後** | replay_run/should_promote/evaluate_publish_gate/sidecar 任一改動需重審同源性與零額度；postmortem 記錄前提 + G-ii guard + 純函數共用使 main.py:780 改動自動波及 D-lite。 |
| **X4-E 終端 vs IDE** | 純 CI yaml + shell + python script，無終端互動；本地驗證用 py。 |
| **X4-F 跨平台** | self-heal 跑 GitHub Actions Linux runner（python 3.8，--heal-if-missing 用 store_true + future annotations 已驗 3.8 相容）；`TZ=Asia/Taipei date` Linux 語法與既有 health check 一致；本地 Win 用 py。 |
| **X4-G 主公個人視角** | 阿喜要全自動 L5。D-lite+ 全自動 + 發布決策與 cron 同源。收官明告「自動補產僅限通過 cron 同款閘門的報告，標 is_backfill 可辨識」。 |
| **X4-H 觀測/治理** | `::warning::` Python print + manifest self_heal/promoted/is_backfill + CI log 可追；飛輪成熟度 L4→可控 L5。 |
| **X4-I 主公可見性** | 自動行為：意外缺漏且通過閘門時自動補產+push（既有授權）。攤開：收官明寫 + log + manifest + 不通過不發布 + no-op candidate 進版控（R-038）。 |
| **X4-J 自動化建議性工具邊界** | 確定性條件觸發 + 同源閘門，非啟發式；自動執行故嚴守同源 + 失敗降級 + log，不擴及不可逆。 |
| **X4-K 使用者端審查官/Patric** | 誤解風險「自癒=修一切/no-op=零外洩」。緩解：明界定僅「通過 cron 同款閘門的報告才發布」；no-op candidate 仍進版控是 cron 既有行為（R-038 登記，非 P111 惡化）。 |

> **主公裁決錨點(B-005)**：3 裁決點已執行 =（1）should_promote 抽純函數共用（核准）；（2）sidecar 受 promote gate 飛輪修（核准）；（3）scope 微→標準 + 凍結（核准）。

### M1.5 八人格顧問團

| 人格 | 觸發 | 發現 |
|---|---|---|
| **Jarvis 總控** | 固定 | ✅ 目標單一（自癒線 + 同源閘門）、邊界明確、5 stage |
| **Ken 紅隊** | 固定 | 🔴 兩輪揪洞（繞閘門 + 9 落地必修）→should_promote 共用 + run_checks 同尺 + sidecar gate + G-ii sys.modules（R7/R9/R10/R11）|
| **Patric 使用者審查** | 固定 | ⚠️ 「自癒=修一切/no-op=零外洩」→文件界定通過閘門才發布 + R-038 登記（X4-K）|
| **Jimmy 文件主筆** | 觸發 | ✅ should_promote 共用 + docstring 指針 + postmortem 4 通則 |
| **Marcus 數據分析** | 觸發（量測觸發頻率）| ✅ 本地可查範圍觸發 0 次（低頻最後防線）+ tier 空 8/11 高頻→no-op 路徑須正確（已納 G-i case②）|
| **Oliver 設計審查** | N/A | 不涉 UI/視覺。N/A。 |
| **Penny CFO** | 觸發 | ✅ replay 零 LLM（G-ii sys.modules 實測 158 模組零 SDK）；不觸發 main.py 重跑 |
| **Jason DevOps（核心）** | 觸發 | ✅ step 不阻斷、不加 if:always()、TZ 對齊、置 Fallback Push 前、沿用既有授權、rollback=git revert、3.8 相容、run_checks 參數 check_landing=False |

### M2 紅藍對抗（≥5 條，≥2 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 7 | **【S 級】** replay promote=True 繞品質閘門自動發布劣質報告（report 缺主因是閘門刻意擋下）？ | S | 0 | Claude 親核 file:line（main.py:706/716/780/793、generator.py:94）。**D-lite+：self-heal 重產 candidate(promote=False)→跑與 main.py 逐位元同源的閘門→通過才 promote**。should_promote 抽純函數物理共用。 | 入計畫範圍（R7+S1/S2+通則2）|
| 8 | **【S 級】** run_checks 參數漂移破「同一把尺」（check_landing 漏 False→candidate 未 promote 時 landing 假陽性 FAIL→自癒永遠降級 L4）？ | S | 0 | 逐位元複製 main.py:132-139（expected_mode=production, check_git_clean=False, **check_landing=False**, expected_report_path=candidate）；不沿用 replay 既有 --check-health 慣例；G-i case 驗。 | 入計畫範圍（R11+S2）|
| 1 | **【S 級】** 自動 replay 燒 LLM 額度？ | S | 0 | replay 零 LLM 已查證 + **G-ii subprocess sys.modules 實測 import 158 模組零 SDK marker**（鎖具體 client 名非 Protocol base 避誤報）。 | 入計畫範圍（R2+S4+Penny）|
| 9 | should_promote 兩把尺未來漂移？ | A | 0 | **抽零依賴純函數放 run_manifest，main.py:780 + D-lite 物理共用一行**；測試只護一行。 | 入計畫範圍（R10+S1）|
| 10 | freshness sidecar 孤兒污染 P110 凍結偵測器（no-op 留 sidecar，cron 也有）？ | A | **1（cron 既有）** | **sidecar 移入 generate 的 if promote 區塊**（受 promote gate），一併解 self-heal + cron；P110 freshness 測試驗不回歸。 | 入計畫範圍（R9+S1，飛輪修）|
| 2 | 自動修復誤擴大不可逆？ | B | 0 | 註解 + docstring 契約 + postmortem 通則 + 不可逆仍問阿喜。 | 入計畫範圍（R6）|
| 3 | self-heal 崩潰中斷 CI？ | B | 0 | `\|\| echo ::warning::` + 不加 if:always() + health check 照跑 + 降級 L4。 | 入計畫範圍（R3+S3）|
| 4 | 自動 push 新增授權？ | B | 0 | 不新增——既有 Fallback Push 推；本計畫 push 仍問阿喜。 | 入計畫範圍（X1+R6）|

> 未解質疑：無（質疑 #10 揭露 P110 cron 既有孤兒 sidecar，採飛輪修一併解；no-op candidate 進版控登記 R-038 為 cron 既有行為）。

---

## 12. 凍結戳記

- **凍結人**：阿喜 + Claude（Opus 4.8 1M）雙方確認
- **凍結時間**：2026-06-14
- **凍結後變更**：禁止；如需改，新增「Phase 111.X 補遺」章節
- **凍結依據**：兩輪飛輪對抗審查（8 視角）+ Claude 親核 file:line + lint M1/M2 PASS + 阿喜核准 3 裁決點

---

*受 17 層品質框架 v3.1 + STR1/STR10 保護。狀態：草案 v3，待阿喜凍結。*
*建立 2026-06-13｜v2 修訂 2026-06-14（第一輪對抗審查揪 promote 繞閘門 S 級洞，補 publishable gate）｜v3 修訂 2026-06-14（第二輪 D-lite 落地壓測收斂 9 必修：run_checks 同尺/should_promote 純函數共用/sidecar promote gate/G-i 真跑/G-ii sys.modules，scope 微→標準，阿喜核准）｜兩輪共 8 視角對抗審查 + Claude 親核 file:line，未動工。*

---

## 📌 Phase 111.1 補遺（凍結後變更，2026-06-14 動工時發現 + 阿喜核准）

> 凍結機制要求：凍結後變更須新增補遺章節（見 §12）。本補遺記錄動工視窗在實作 S1(c) 時，
> 親核呼叫鏈發現的凍結計畫 correctness 缺口，及阿喜核准的修正。

### 缺口：S1(c)「sidecar 移入 `generate()` 的 if promote 區塊」照字面做會讓 cron 失去 sidecar

**物理真相（動工時親核 file:line）**：
- cron 唯一一次呼叫 `generator.generate(..., promote=False)`（[main.py:716](../main.py)），發布是事後另呼叫 `generator.promote_candidate(...)`（[main.py:783](../main.py)）。
- `_write_freshness_sidecar` 需要 `top5_news/top5_yaya`，這資料只存在 `generate()` 的 `template_vars`，`promote_candidate()` 拿不到。
- 故若照計畫字面把 sidecar 移入 `generate()` 的 `if promote:`，cron 永遠走 `promote=False` → **sidecar 完全不寫 → P110 凍結偵測器對 cron 整個失效**（不是修孤兒，是砍掉 cron sidecar）。
- 為何凍結前未抓到：P110 測試直接呼叫 `gen._write_freshness_sidecar(...)`，不經 `generate()`；其餘 `generate(promote=False)` 測試只驗 HTML、不驗 sidecar → 測試全綠但 production 已回歸（G2 綠燈假象）。
- 根因：計畫作者假設「發布路徑＝`generate(promote=True)`」，但真實架構是「candidate-first（過閘門才促）」，generate(promote=False) 是必要前提、不能改。

### 修正：修法 A（阿喜 2026-06-14 核准）

sidecar 改由 `generator.promote_candidate()` 在**真正發布時**寫——`generate()` 把 top5 暫存到 `self._pending_freshness`，`promote_candidate()` 依 stash（`pending[0]==report_date` 防 instance 復用殘留）寫 sidecar。綁定「真實發布事件」，三條路徑統一：
- cron（generate(promote=False)+外部 promote_candidate）→ 寫 ✅（不再失去）
- replay self-heal 通過閘門 promote → 寫 ✅
- no-op / gate-fail / dry-run / candidate-only → 不寫 ✅（解孤兒）

落點：[reporter/generator.py](../reporter/generator.py) `generate` 暫存 + 移除無條件寫、`promote_candidate` 受 promote gate 寫。

### 動工時新增的兩項（對抗審查驅動，非擴 scope）

- **修法A 契約釘樁測試** `test_sidecar_bound_to_promote_event`：cron 式序列（generate(promote=False) 不寫 → 外部 promote_candidate 才寫）+ 防孤兒，把修法A 命脈機器化防復發。
- **G-i case① 第 4 隔離**（fake `gen_mod.shutil.copy2`）：4 視角對抗審查揪出原 case① 的「git status 零改動」斷言有盲區——`generate()` 寫死複製到真 repo `ui_previews/`（不受 config/chdir 隔離、且 .gitignore 使 git status 看不到 → 假保證）。補隔離 4 使 generate 真正零真-repo 寫入，斷言誠實化。

### 驗收

全套 504→514 passed（+10：原 8 + tier 空 + 修法A 釘樁），0 failed。4 視角對抗審查：3/4 contract_met，1 條 B 級（上述 ui_previews 假保證）已修並實證（測試跑後真 repo ui_previews 該檔不存在）。
