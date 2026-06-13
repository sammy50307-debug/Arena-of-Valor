# Postmortem — P111：CI 報告自癒（飛輪 L4→可控 L5，發布決策與 cron 同源）

- **日期**：2026-06-14
- **Phase**：P111（CI self-heal 重產報告，D-lite+ 同源閘門）
- **性質**：飛輪成熟度升級（L4 人工 replay → 可控 L5 偵測→自動修復）+ 凍結後 correctness 修正（修法A）
- **嚴重度**：中（無 live 事故；屬主動升級。但凍結計畫含一個測試抓不到的 cron 回歸缺口，動工時親核才揪出）

## 背景

飛輪自我修復審查（2026-06-13）結論：飛輪無真 L5 自我修復，多數元件停 L3。最高 ROI = 把已備的零額度 recovery 工具 `replay_run.py` 接成偵測驅動：cron 渲染意外失敗（analysis 已寫、report 沒寫）時，CI 自動補產。但第一輪對抗審查揪出 S 級洞——report 缺的**主因是品質閘門「刻意」不發布**，若 replay 用 `generator.py` 預設 `promote=True` 會**自動發布劣質報告到首頁**。故採 D-lite+：self-heal 重產 candidate(`promote=False`) → 跑與 cron 逐位元相同的發布閘門 → 通過才 promote。

## 動工時揪出的凍結計畫缺口（核心教訓）

計畫 S1(c) 要求「`_write_freshness_sidecar` 移入 `generate()` 的 `if promote:` 區塊」以解孤兒。動工視窗親核呼叫鏈發現：**cron 唯一走 `generate(promote=False)`（main.py:716）+ 事後 `promote_candidate()`（main.py:783）**，而 sidecar 需要的 top5 只存在 `generate()` 的 `template_vars`。照字面搬 → cron 永遠 `promote=False` → **sidecar 完全不寫 → P110 凍結偵測器對 cron 整個失效**（不是修孤兒，是砍 cron sidecar）。**測試全綠卻 production 回歸**：P110 測試直接呼叫 `_write_freshness_sidecar`、不經 `generate()`；其餘 `generate(promote=False)` 測試只驗 HTML。阿喜核准**修法 A**：sidecar 改由 `promote_candidate()` 在真正發布時依 `self._pending_freshness` 暫存寫，綁定發布事件（cron/self-heal/dry-run 三路徑統一）。登記 P111.1 補遺。

## 對抗審查（Workflow 4 視角）

3/4 contract_met（同源閘門：should_promote 物理共用 + run_checks 逐位元同尺含 check_landing=False；sidecar 生命週期修法A 正確；CI 韌性）。1 條 B 級真實疑慮：G-i case① 的「git status 零改動」斷言有盲區——`generate()` 寫死複製到真 repo `ui_previews/`（不受 config/chdir 隔離，且 .gitignore 使 git status 看不到 → 假保證）。審查者實測 mtime 證實寫入。已修：補第 4 隔離（fake `shutil.copy2`）使 generate 真正零真-repo 寫入，並補「跑後 ui_previews 該檔不存在」斷言。

## 修法（D-lite+ 同源閘門 + 修法A）

1. **S1 同源閘門地基**：`run_manifest.should_promote(has_candidate, tier, gate_reasons_len)` 純函數，main.py + replay self-heal 物理共用（DRY 防漂移）；sidecar 改由 `promote_candidate` 受 promote gate 寫（修法A）。
2. **S2 replay self-heal**：`--heal-if-missing`——report 在→no-op；tier 非 publishable（含空）→no-op+`::warning::`；重產 candidate→`run_checks` 逐位元複製 main.py:132-139（尤其 `check_landing=False`）→`should_promote` 判定→promote 或 no-op 降級；統一 repo_root 從 config 推導；manifest 標 `self_heal/promoted`。
3. **S3 CI step**：`daily_report.yml` Upload Artifact 後、Fallback Push 前加 step，不加 `if:always()`、`|| echo ::warning::`、`TZ=Asia/Taipei`。
4. **S4 測試**：`test_self_heal_replay.py`——G-i 真跑 generate 5 case + 三（→四）隔離 + git 零改動；修法A 契約釘樁；G-ii subprocess sys.modules 零 LLM SDK。
5. 全套 504→514 passed（0 failed）。

## 教訓與通則化

### 通則（4 條，自計畫 §11 凍結 + 動工驗證）

> **通則1（L5 窄面）**：L5 自動修復限「低風險、可驗證、可回退」窄面；只重渲染、不可逆不碰、push 沿用既有授權。升 L5 先問「自動動作最壞會做什麼」。
> **通則2（同源閘門，核心）**：自動修復的「發布/對外」決策必須與被修復系統用**同一把尺**（物理共用同一行 `should_promote`），不可自己簡化判定——本專案 report 缺主因是品質閘門刻意擋下，self-heal 若自己決定 promote 會繞閘門發布劣質報告。`run_checks` 參數（尤其 `check_landing`）也要逐位元對齊，否則尺鬆/緊。
> **通則3（前提機器化）**：L5 零額度前提用 `sys.modules` 執行期斷言機器化（subprocess 乾淨進程，鎖具體 client 名非 Protocol base），勝過掃頂層 import 字串。
> **通則4（生命週期綁定）**：副作用檔（sidecar）的生命週期必須綁在它代表的事件（發布）上——sidecar 該受 promote gate，否則 candidate-only/no-op 路徑留孤兒污染下游偵測器。

### B-027（新 blindspot，全域連續編號）

> **凍結計畫的字面修法可能與真實架構矛盾，且既有測試抓不到——動工前必親核呼叫鏈，不照字面盲改。** P111 計畫假設「發布路徑＝`generate(promote=True)`」，但真實架構是 candidate-first（`generate(promote=False)`+事後 `promote_candidate`）。照字面搬 sidecar 會讓 cron 失去 sidecar，而 P110 測試直接呼叫 `_write_freshness_sidecar`、不經 generate → 全綠假象。
>
> **延伸：測試斷言不能宣稱比實際驗到的更強。** case① 的「git status 零改動」斷言因 `ui_previews/` 被 .gitignore 忽略而通過，卻宣稱「零副作用」——實際 generate 寫了真 repo 工作目錄（gitignored 看不到）。對抗審查連 mtime 都實證。通則：副作用斷言要涵蓋「git 看不到的工作目錄寫入」，否則 gitignore 會給假保證。

具體檢查點：
- 凍結計畫動工時，對「移動/改寫某副作用」的指令，先 `grep` 真實呼叫鏈（誰用 promote=False/True、資料在哪個 scope），確認字面修法不會打破其他路徑。
- 寫「零副作用/不弄髒 repo」斷言時，問「有沒有寫死的、不受 config/chdir 隔離、且被 .gitignore 遮蔽的真-repo 寫入點」→ 補對應隔離 + 比對工作目錄殘留，不只比 `git status`。

## 防復發

- **同源閘門物理共用** `run_manifest.should_promote`：main.py:780 與 self-heal 共用一行，未來改發布判定自動波及兩處（測試只護一行）。
- **零額度 guard** `test_zero_llm_sdk_on_import`（G-ii）：subprocess 乾淨進程斷言 import replay_run 後 sys.modules 無具體 LLM client，金絲雀實證偵測有效。
- **修法A 契約釘樁** `test_sidecar_bound_to_promote_event`：cron 式序列 sidecar 綁定 promote 事件、no-op 不留孤兒，機器化防復發。
- **docstring 反向指針**：`replay_run.py` 模組 docstring 寫明同源契約（改 should_promote/run_checks/heal 流程須重審 L5）。
- 殘留（R-037）：主根因 `main.py:728` generate 例外被吞未治本（症狀面已補救）；self-heal top5 退化保真；自動化邊界 X3 過期日 2026-09-14 重審。
- 殘留（R-038）：no-op candidate 仍被 Fallback Push 撈進版控（cron 既有行為，非 P111 惡化）。
- B-027 待 `cross-phase-review`/`blindspot-tracker` 評估是否納入 PHASE_TEMPLATE 開工檢查。
