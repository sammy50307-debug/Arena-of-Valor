# Phase P97 計畫書 — RTK Token Savings Evaluation（CLOSED / INSTALL BLOCKED）

> 狀態：CLOSED / INSTALL BLOCKED。主公已於 2026-05-26 核准 `P97 plan freeze`，並於 2026-05-27 核准 `P97 evaluation runtime`。P97 已完成隔離 binary 實測、dry-run、baseline matrix、failure diagnostics、telemetry 與 rollback 檢查；結論是不全域部署、不執行 `rtk init --codex`、不把 `@RTK.md` 寫入 AOV `AGENTS.md`。完整證據見 `docs/PHASE_97_RTK_EVALUATION.md`。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P97 |
| **Phase 名稱** | RTK Token Savings Evaluation |
| **建立日期** | 2026-05-26 |
| **影響半徑** | 標準 (plan 4 檔；runtime docs 6 檔；RTK binary / logs 僅在 git-ignored scratch，未 stage) |
| **預估投入時數** | plan 0.8h；evaluation runtime 1.5-2.5h；installation runtime 視結果另開 |
| **Token budget** | plan 18K；evaluation runtime 35K |
| **負責模型** | GPT-5.3-Codex（repo 文件 / 本機檢查）；若涉及全域設定與多代理衝突，升 GPT-5.5 高 |

## 0.5 狀態轉換清單

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者 / 核准者 |
|---|---|---|---|---|---|
| R-018 RTK Token Savings Tooling | New | Open | RTK 被列入待評估工具風險，不代表已安裝 | 主公開 P97 plan | AI 建帳，主公審核 |
| P97 plan | FROZEN | CLOSED | 評估 runtime 已完成，並做出 install blocked 裁決 | 主公核准 `P97 evaluation runtime` 且 evidence gate 完成 | 主公 / AI |
| RTK binary | Not installed | Isolated evaluation completed | 僅下載到 `scratch/rtk_eval/bin/rtk.exe`，未加入 PATH，runtime 後不留下 AppData residue | P97 runtime 完成 | AI |
| RTK project integration | Not enabled | Blocked pending optional P98 | `rtk init --codex --dry-run` 顯示會新增 `RTK.md` 並 patch `AGENTS.md`，P97 不套用 | P97 failure diagnostics 未通過 | 主公 |
| RTK global deployment | Not enabled | Blocked | 全域 hook / 全域規則仍禁止 | 需另開 P98+ 並由主公明文核准 | 主公 |

---

## 1. 目標 (Objective)

用可回滾、可量測、低干擾的方式評估 RTK 是否真的能降低本專案 AI 工具輸出 token 成本，同時不犧牲 debug 可信度、terminal 真相、全域規則穩定性與隱私。

## 2. 觸發背景 (Why Now)

主公先前提出想安裝 GitHub 上約 5 萬星的 RTK token-saving 工具，並要求若效果優秀再評估是否全域部署。P96/R-017 已完成 runtime 並降級 monitoring，因此 RTK 不再插隊內容修復主線，可以另開 R-018/P97 進行保守評估。

## 2.1 官方資料查證（2026-05-26）

| 來源 | 查到的重點 | P97 裁決 |
|---|---|---|
| GitHub repo `rtk-ai/rtk` | README 稱 RTK 是 CLI proxy，會在輸出進 LLM context 前過濾與壓縮；宣稱常見命令可省 60-90%，單 Rust binary，Windows 可用 prebuilt binary。URL: `https://github.com/rtk-ai/rtk` | 視為高潛力但需本地實測，不採宣稱值當決策依據 |
| RTK Installation docs | 官方警告 `rtk` 名稱有碰撞；Cargo 必須用 `cargo install --git https://github.com/rtk-ai/rtk rtk`，Windows 可下載 `rtk-x86_64-pc-windows-msvc.zip`；`rtk gain` 可驗證是否裝對。URL: `https://www.rtk-ai.app/docs/getting-started/installation/` | 本機目前無 `cargo`，有 `winget`；runtime 優先評估 Windows binary / winget，不用 Cargo |
| RTK Quick Start docs | `rtk init --global` 是全域；`rtk init` 可單專案；`--dry-run` 會列出將改哪些檔且不寫入。URL: `https://www.rtk-ai.app/docs/getting-started/quick-start/` | P97 runtime 第一門只允許 dry-run，不允許直接 init |
| Supported Agents docs | Codex CLI 是 AGENTS.md instructions 類，屬 prompt-level guidance，不是透明 hook；Windows native 自動 rewrite 不完整，WSL 才有完整 shell hook。URL: `https://www.rtk-ai.app/docs/getting-started/supported-agents/` | 本機 Windows 原生不能假設完整 hook；全域部署收益可能低於宣稱 |
| Configuration / Telemetry docs | config 文件列 telemetry 設定與 `RTK_TELEMETRY_DISABLED=1`；telemetry privacy 頁稱需明確同意且不收 code、path、full command lines。URL: `https://www.rtk-ai.app/docs/getting-started/configuration/`、`https://www.rtk-ai.app/docs/resources/telemetry/` | 文件存在「預設 enabled vs 需 consent」解讀差異；P97 預設禁用 telemetry |

## 2.2 本機初始盤點（2026-05-26）

| 檢查 | 結果 | 解讀 |
|---|---|---|
| `Get-Command rtk` | NOT_FOUND | 本機尚未安裝 RTK |
| `Get-Command cargo` | NOT_FOUND | 不應走 Cargo 安裝作為首選 |
| `Get-Command winget` | FOUND | 可評估 winget 或 GitHub release binary |
| `git status -sb` | main 同步 origin，只剩舊 untracked 暫存檔 | P97 plan 不應 stage 舊 reports / scratch / skills 暫存 |

## 2.3 方案取捨

| 方案 | 做法 | 優點 | 缺點 | 裁決 |
|---|---|---|---|---|
| A. 直接全域安裝 RTK | 立即 `rtk init --global` 或改全域 AGENTS/CLAUDE/GEMINI | 可能最快省 token | 會改所有專案與多代理行為，debug 真相可能被壓縮 | 不採用 |
| B. 只做官方資料 + dry-run + 本機盤點 | 不安裝，只建立評估矩陣 | 風險最低 | 無法量測實際收益 | 本 plan 採用 |
| C. 專案層試跑 | 只在 AOV project 做 `rtk init --codex --dry-run`，必要時用 isolated binary 手動 `rtk <cmd>` | 可量測，不碰全域 | 仍需下載 binary，需主公 runtime 核准 | P97 runtime 候選 |
| D. WSL full hook 評估 | 在 WSL 裡評估透明 hook | 最接近官方 full hook | 需新增環境變因，可能影響 Codex Windows workflow | 延後 |
| E. 全域部署 | 三家代理都套 RTK | 若成功收益最大 | 影響半徑最大，回滾與誤壓縮成本高 | 只允許 P98+，需另核准 |

## 2.4 P97 runtime 實測裁決（2026-05-27）

完整證據見 `docs/PHASE_97_RTK_EVALUATION.md`。本段只保留收官裁決。

| 檢查 | 結果 | 裁決 |
|---|---|---|
| Release / checksum | `v0.42.0` Windows zip；SHA256 `527552ec419988ff4a862415ba28d5aa7c1148ef3dc926ae11a4c133e63a7491` match | binary 來源 PASS |
| 安裝範圍 | 只解壓到 `scratch/rtk_eval/bin/rtk.exe`；`Get-Command rtk` 前後皆 `NOT_FOUND` | 未全域安裝 PASS |
| Dry-run | `rtk init --codex --dry-run -v` would create `RTK.md` and add `@RTK.md` to `AGENTS.md`; tracked diff before/after empty | 可預覽 PASS；但 real init 仍 blocked |
| Telemetry | `consent=never asked`、`enabled=no`、`RTK_TELEMETRY_DISABLED=1 (blocked)` | PASS |
| Local residue | RTK runtime 建立 `C:\Users\sammy\AppData\Local\rtk\history.db` / `.hook_warn_last`；已移除 | rollback PASS；但列為副作用 |
| Baseline | 6 samples；pytest pass 省 83.0%，pytest missing file 省 72.4%，Git/search 幾乎 0%，`rtk read` 反而 -14.2% | 只適合窄場景 |
| Failure diagnostics | missing file path 被壓成 `No tests collected`；`rtk err py -c ...` sentinel 變成 `No active exception to reraise`；`rtk proxy` 保留 raw | FAIL；禁止全域部署 |

P97 final decision:
- 不全域部署 RTK。
- 不執行 `rtk init --codex`。
- 不把 `@RTK.md` 寫入 AOV `AGENTS.md`。
- 不把 RTK 加入 PATH。
- 若主公想繼續，只能另開 P98 project-local/manual-prefix pilot，且限定已知 noisy passing tests；任何 debug / traceback / missing file / security-sensitive output 必須 raw 或 `rtk proxy`。

## 3. Entry Criteria（入口條件）

開工前必須全部達成：
- [x] R-017 已降級 Open（Monitoring），P96 不再阻擋 RTK 評估。
- [x] 主公已明確下令「開 RTK evaluation plan」。
- [x] 已查官方 RTK repo / docs，不憑印象寫安裝建議。
- [x] 已確認 P97 plan 階段不安裝、不初始化、不改全域規則。
- [x] 主公核准 P97 plan freeze。
- [x] 主公另行核准 P97 evaluation runtime，才可下載或執行 RTK binary。

## 4. Exit Criteria（退出條件）

P97 plan freeze 退出條件：
- [x] `docs/PHASE_97_PLAN.md` 通過 `scripts/lint_phase_plan.py`。
- [x] `NEXT_SESSION_HANDOFF.md` / `docs/ACTIVE_OPERATION.md` 指向 R-018 / P97 FROZEN。
- [x] `docs/RISK_REGISTRY.md` 建立 R-018 Open 風險。
- [x] `TASK_HISTORY.md` 追加 P97 plan / freeze 物理真相。

P97 evaluation runtime 未來退出條件：
- [x] 用 dry-run 證明 RTK 會改哪些檔，且沒有未核准全域寫入。
- [x] 建立 baseline：至少 6 類命令的 raw output tokens / lines 與 RTK output tokens / lines 對照。
- [x] 驗證失敗診斷不被壓到無法修 bug：已完成驗證，但結果 **FAIL**，因此阻擋 install/global deployment。
- [x] 驗證 telemetry 關閉：`RTK_TELEMETRY_DISABLED=1`，`telemetry status` 顯示 blocked。
- [x] 驗證回滾路徑：isolated binary 未加入 PATH；AppData residue 已清除；project-local init 未套用。
- [x] 明確裁決三選一：P97 不裝；若要繼續，另開 P98 project-local/manual-prefix pilot，不開全域部署。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 預估投入時數 | plan 0.8h；runtime 1.5-2.5h |
| 預估收益等級 | 中到高 |
| 收益描述 | 若 RTK 對 `pytest`、`git diff`、`rg`、`git status` 等命令有效，可能減少大量 terminal output tokens；但 Codex on Windows 可能只是 prompt-level guidance，實際收益需量測 |
| ROI 結論 | ✅ 值得評估；❌ 不值得直接全域安裝 |

---

## 6. 17 層稽核表

### S 級層（必填，4 層）

| 層 | 採用優化項 | 該層風險 | 緩解 |
|---|---|---|---|
| **1. 代碼層 (Code)** | P97 plan 不改 runtime code；未來只允許新增評估腳本或 docs | 把工具評估誤寫成專案功能改動 | evaluation runtime 只碰 `docs/` / optional `scripts/rtk_*`，不得改 app logic |
| **2. 邏輯層 (Logic)** | 建 token saving 評估矩陣：節省率、診斷完整性、回滾性、隱私 | 只看省 token，忽略 debug 真相被壓縮 | 每個命令同時評估「省多少」與「有沒有少掉關鍵錯誤」 |
| **4. 測試層 (Testing)** | 未來 runtime 要跑 dry-run、baseline compare、failure sample | 裝了覺得快，實際壞了才知道 | 評估未過不得全域部署；全域部署另開 P98 |
| **10. 安全層 (Security)** | 禁止 curl pipe install；禁用 telemetry；不改 secrets / PATH / shell profile | 安裝腳本或 hook 改全域設定，或外送用量資料 | 僅允許官方 release / winget / dry-run；下載與初始化都需主公核准 |

### A 級層（提示填，7 層）

| 層 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|
| **3. 架構層 (Architecture)** | RTK 作為工具鏈層，不進 AOV runtime pipeline | 混入 Daily Monitor 或報告生成流程 | 明列 Forbidden Work：不改 workflow、不改 production scripts |
| **5. 資料層 (Data)** | 評估只記 command class、lines/tokens、pass/fail，不記完整敏感輸出 | raw command output 可能含路徑、token、貼文資料 | raw logs 只放 git-ignored scratch；TASK_HISTORY 只記統計 |
| **6. 可觀察性層 (Observability)** | 使用 `rtk gain`、line count、token estimate、failure readability 表 | 只憑感覺說省 token | runtime 需產出 `docs/PHASE_97_RTK_EVALUATION.md` 或等價矩陣 |
| **7. 韌性層 (Resilience)** | 保留 `RTK_DISABLED=1` 和 uninstall / remove-rule 路徑 | RTK 壓縮錯誤導致 AI 誤判 | 高風險命令可列 exclude；失敗時讀 tee/raw output |
| **13. 可維護性層 (Maintainability)** | 先專案層再全域層；全域需另 phase | 多工具全域規則互相打架 | Codex / Claude / Gemini 分別建評估與回滾清單 |
| **14. 文件層 (Documentation)** | P97 plan / evaluation evidence / handoff / active / risk / history 同步 | 下一窗以為已經可以安裝 | Mode 維持 CLOSED / INSTALL BLOCKED；P98 pilot / install 仍需另核准 |
| **15. 流程層 (Process)** | Plan -> freeze -> evaluation runtime -> install decision -> optional P98 | 評估和安裝混在一起 | P97 禁止全域部署；只給決策依據 |

### B 級層（條件式，6 層）

| 層 | 觸發條件 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|---|
| **8. 效能層 (Performance)** | CLI output compression | 量測常用命令 lines/tokens 節省率 | 節省率只在官方樣本漂亮 | 以 AOV 實際命令實測 |
| **9. UX/A11y 層** | 終端輸出給 AI / 主公看 | 評估錯誤訊息是否仍白話可懂 | 壓縮後人類更難讀 | 失敗樣本需人工可讀 |
| **11. 部署層 (DevOps)** | 可能改 hook / PATH / 全域設定 | 全域部署後置 | 影響所有專案與模型 | P97 禁止全域；P98 才討論 |
| **12. 成本層 (Cost)** | token / API 成本 | 建立 savings threshold | 花時間裝工具但省不到 | 未達 50% 實測 savings 不推進 |
| **16. 隱私/合規層 (Privacy)** | telemetry / command metadata | 預設 opt-out、只記匿名統計 | 文件對 telemetry 預設描述不一致 | runtime 必查 `rtk telemetry status` 並禁用 |
| **17. i18n/在地化層** | Windows + 繁中終端 | 保留 UTF-8 / PowerShell 行為 | 中文輸出被截斷或亂碼 | runtime command 全設 UTF-8，檢中文輸出 |

### 層級互鎖驗證

- [x] 動 Logic 層 -> 已動 Testing 層：P97 runtime 必有 baseline / dry-run / failure sample。
- [x] 動 Architecture 層 -> 已動 Documentation 層：RTK 只屬工具鏈，不進 production pipeline。
- [x] 動 Data 層 -> 已動 Maintainability 層：只記統計，不保存 raw 敏感輸出。
- [x] 動 Security 層 -> 已動 Testing 層：telemetry / hook / rollback 都列驗證。
- [x] 動 Performance 層 -> 已動 Observability 層：節省率必須用矩陣呈現。

---

## 7. 跨切面檢查

### X1 可逆性 (Reversibility)

| 動作 | 可逆性 | 主公確認 |
|---|---|---|
| 建立 P97 plan 文件 | 可逆 | 主公已要求開 plan |
| 更新 handoff / active / risk / history | 可逆 | 本次同步 plan 狀態 |
| `rtk --version` / `rtk gain` 檢查 | 可逆 | runtime 前可做，但若 rtk 不存在只記錄 |
| 下載 RTK binary | 半可逆 | 需主公核准 P97 runtime |
| `rtk init --dry-run` | 可逆 | 需主公核准 P97 runtime |
| `rtk init` project-local | 半可逆 | 需主公另核准 |
| `rtk init --global` | 半可逆且高風險 | P97 禁止，需 P98+ 主公親口核准 |

### X2 盲區掃描 (Blind Spot)

主公看不到但會發生的：
- [x] Windows 原生 RTK 對 Codex 可能只是 AGENTS.md 指令，不是透明 hook。
- [x] 壓縮輸出可能省 token，但也可能拿掉 debug 關鍵上下文。
- [x] telemetry 文件存在預設狀態解讀差異，必須保守關閉。
- [x] 全域 hook 會影響其他專案，不只 AOV。
- [x] `rtk` 名稱有不同專案碰撞，必須用 `rtk gain` 驗證安裝對象。

### X3 時間敏感性 (Time Decay)

- 本計畫建立日期：2026-05-26。
- 本計畫原過期日期：2026-06-02；P97 runtime 已於 2026-05-27 完成。若未來開 P98，需重新查 RTK 官方 docs / releases。
- R-017 monitoring window：2026-05-26～2026-06-02；RTK 評估不得干擾監控。
- 風險記錄帶日期：✅。

### X4 多角度同行審查

- **主公視角**：主公要的是省 token 但不要把專案弄壞；本計畫用「先量測、再安裝、最後才全域」降低決策壓力。
- **世界頂尖駭客 / 紅隊攻擊者視角**：攻擊面是供應鏈下載、hook 攔截命令、telemetry、PATH 污染與壓縮掉安全告警；最小緩解是不用 curl pipe、先 dry-run、禁 telemetry、保留 disable/uninstall。
- **接手者視角**：接手者需要知道 RTK 尚未安裝；P97 只是評估計畫，任何 install 都必須看 runtime evidence。
- **X4-J 自動化建議性工具邊界**：RTK 的 savings / rewrite 是建議性工具輸出，召回率與壓縮品質非 100%；失敗診斷仍需人工抽看 raw output。
- **X4-K 使用者端審查官 / Patric 型人格**：若裝完後 AI 更常漏看錯誤，省 token 反而造成更多返工；所以 user-facing 成功標準是「省且不失真」。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | RTK 壓縮掉錯誤細節，導致 AI 修錯方向 | 中 | 高 | 工具 / 邏輯 | failure sample 必測；保留 raw / tee / RTK_DISABLED |
| R2 | 全域部署影響其他專案、Claude、Gemini、Codex 行為 | 中 | 高 | 流程 / 工具 | P97 禁止全域；P98 才可討論 |
| R3 | 安裝來源或名稱碰撞裝到錯的 `rtk` | 中 | 高 | 供應鏈 | 只用官方 repo/release/winget，驗證 `rtk gain` |
| R4 | telemetry / usage metadata 不符合主公隱私偏好 | 中 | 中 | 隱私 | 預設 `RTK_TELEMETRY_DISABLED=1`，runtime 檢 `telemetry status` |
| R5 | Windows 原生不支援完整 hook，收益低於預期 | 高 | 中 | 環境 | 分別評估 Windows prompt-level、manual prefix、WSL full hook |
| R6 | RTK evaluation 干擾 R-017 monitoring 或 Daily Monitor | 低 | 中 | 流程 | 不改 workflow、不改 AOV runtime、不在 CI 啟用 |

**高風險加權檢查（META4）**：
- 高風險數量：3 項。
- 加權分數：7 分（高=2, 中=1, 低=0.5）。
- 是否 >= 5 須請示主公：是；P97 plan 只凍結評估路線，runtime / install 需主公另核准。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解掉的風險 | 驗收 |
|---|---|---|---|
| **S0 Plan / Source Verification** | 查官方 docs、記錄本機狀態、建立 R-018 | 避免靠印象安裝 | plan lint / handoff truth / governance doctor 通過 |
| **S1 Dry-run Only** | 若 runtime 核准，只跑 `rtk init --codex --dry-run -v` 或等價 dry-run | 確認會改哪些檔 | 無磁碟寫入，列出 would-change |
| **S2 Isolated Binary Evaluation** | 不放 PATH；用 isolated binary 手動測 `rtk git status` 等 | 測收益且不污染全域 | baseline matrix 完成 |
| **S3 Failure Diagnostics Check** | 用失敗命令測 RTK 是否保留關鍵錯誤 | 避免省 token 造成修錯 | 已驗證；failure readability FAIL，阻擋 install |
| **S4 Privacy / Rollback Check** | telemetry disable、uninstall、remove-rule、RTK_DISABLED | 確認可逆 | rollback checklist PASS |
| **S5 Decision Gate** | 不裝 / project-local / P98 global plan 三選一 | 防止滑坡到全域 | 主公裁決 |

---

## 10. 影響檔案清單

**新增**：
- `docs/PHASE_97_PLAN.md`
- `docs/PHASE_97_RTK_EVALUATION.md`

**修改**：
- `NEXT_SESSION_HANDOFF.md`：切到 R-018 / P97 CLOSED / INSTALL BLOCKED。
- `docs/ACTIVE_OPERATION.md`：切到 R-018 / P97 CLOSED / INSTALL BLOCKED。
- `docs/RISK_REGISTRY.md`：新增並更新 R-018 Open / install blocked。
- `TASK_HISTORY.md`：追加 P97 plan / freeze / runtime 物理真相。
- P97 runtime closeout：上述 4 檔同步切到 P97 CLOSED / install blocked。

**刪除**：
- 無。

**影響但未直接修改**：
- 全域 `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`（P97 禁止修改）。
- Windows PATH / shell profile / Codex CLI behavior（P97 禁止修改）。
- GitHub Actions / Daily Monitor（P97 禁止修改）。
- `scratch/rtk_eval/`：保存下載、checksum、command output 與 matrix 證據；git-ignored，不 stage。
- `C:\Users\sammy\AppData\Local\rtk`：runtime 曾短暫產生 local savings DB；已在 P97 rollback 中移除。

---

## 11. Postmortem 預埋點

收官後若觸發以下情境，必寫 Postmortem：
- [ ] 未核准卻修改全域設定。
- [ ] RTK 造成測試錯誤被遮蔽。
- [ ] telemetry 未依計畫關閉。
- [ ] 裝錯同名 `rtk` package。
- [ ] 全域部署後其他專案行為被污染。

Postmortem 位置：`docs/postmortems/YYYY-MM-DD-phase-97-rtk-evaluation.md`

---

## 12. Forbidden Work（P97 邊界）

- 不安裝 RTK。
- 不執行 `rtk init`，包含 project-local 與 global。
- 不改全域 AGENTS / CLAUDE / GEMINI。
- 不改 PATH、PowerShell profile、shell hook、Codex settings。
- 不啟用 telemetry。
- 不用 `curl | sh`。
- 不把 RTK 接進 GitHub Actions / Daily Monitor。
- 不 stage unrelated untracked reports / scratch / skills 暫存目錄。

---

## 13. Pre-flight 多視角體檢

### M1 強制填表

| 視角 | 具體發現（不得留空）|
|---|---|
| **X4-A 世界頂尖駭客 / 紅隊攻擊者** | RTK 的高風險不是程式碼本身，而是供應鏈下載、hook 攔截命令、telemetry 與全域規則污染；必須 dry-run、禁 telemetry、保留回滾。 |
| **X4-B 接手者** | 接手者需要清楚看到 P97 只是 evaluation plan，尚未安裝；否則下一窗可能誤以為可以直接全域 init。 |
| **X4-C 災難情境** | 情境：全域 hook 壓掉 pytest 失敗細節，AI 誤判 bug 已修好。緩解：failure sample 必測，未過不得安裝。 |
| **X4-D 5 年後** | 五年後 RTK 可能改名、改 telemetry、或 Codex hook 能力不同；計畫需帶日期，runtime 前必重新查官方文件。 |
| **X4-E 終端 vs IDE** | 終端要能看到 raw 與 compressed 對照；IDE / 文件要看懂哪些檔會被 dry-run 改動，避免無感全域污染。 |
| **X4-F 跨平台 Win/Mac/Linux** | 主公目前在 Windows；官方文件指出 Windows native hook 能力有限，WSL 才接近完整 hook，因此不能照 macOS/Linux 成效推論。 |
| **X4-G 主公個人視角** | 主公想省 token，但更怕專案一直壞；本計畫先用小範圍證據決策，讓主公不用自己分辨 hook 與 prompt-level 差異。 |
| **X4-H 觀測 / 治理** | RTK 若只看官方 60-90% 宣稱會失真；P97 要用 AOV 實際命令建立 savings / fidelity / rollback 三軸觀測。 |
| **X4-I 主公可見性** | 主公看不到 PATH、hook、telemetry、AGENTS patch；所以 dry-run output、would-change list、telemetry status 必須攤開。 |
| **X4-J 自動化建議性工具邊界** | RTK 壓縮結果不是完整真相，只是 token-saving view；任何失敗修復仍需能回到 raw output 或 disable RTK。 |
| **X4-K 使用者端審查官 / Patric 型人格** | 如果工具讓 AI 更省但更常問錯問題，主公體感會變差；評估成功必須同時省 token 與保留關鍵錯誤訊息。 |

### M1.5 八人格顧問團觸發檢查

| 人格 | 觸發規則 | 檢查重點 | 是否觸發 / 發現 |
|---|---|---|---|
| **Jarvis 型總控** | 固定必看 | RTK 和 R-017 monitoring 是否混線 | 觸發；P97 是新 R-018 工具鏈戰線，不動網站 runtime。 |
| **Ken 型紅隊 / 技術長** | 工具安裝 / hook / telemetry | 供應鏈、全域 hook、PATH、telemetry | 觸發；禁止 curl pipe install，runtime 前只 dry-run。 |
| **Patric 型使用者端審查官** | 主公是否理解下一步 | 白話說清楚不安裝、不全域 | 觸發；計畫用三段門禁：評估、專案層、全域層。 |
| **Jimmy 型文件主筆** | 改 docs / handoff / history | 文件是否防下一窗誤安裝 | 觸發；handoff 明列 RTK Forbidden Work。 |
| **Marcus 型數據分析師** | ROI / token saving | savings 不能只看官方宣稱 | 觸發；runtime 必做 baseline matrix。 |
| **Oliver 型設計審查** | 終端輸出可讀性 | 壓縮後錯誤是否好讀 | 觸發；failure sample 要人工可讀。 |
| **Penny 型 CFO** | token / 成本 | 是否省到值得承擔工具風險 | 觸發；未達實測 threshold 不推進。 |
| **Jason 型執行 / DevOps** | Windows / PATH / shell hook | 回滾、環境污染、跨 shell | 觸發；P97 禁止 PATH/profile/hook 寫入。 |

### M2 紅藍對抗

| # | 紅隊質疑（具體）| 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | RTK 壓縮掉真正的 traceback，AI 看到綠色摘要卻漏掉根因。 | S 級 | 0 | runtime 必含 failure sample 與 raw fallback；失敗樣本不過不得安裝。 | 入計畫範圍 |
| 2 | 全域 init 影響所有專案與多代理，之後 bug 來源難追。 | S 級 | 0 | P97 禁止全域；全域部署需 P98+ 與主公另核准。 | 入計畫範圍 |
| 3 | 官方文件對 telemetry 預設狀態有解讀差異，可能誤送 usage metrics。 | S 級 | 0 | 預設 `RTK_TELEMETRY_DISABLED=1`，runtime 必查 telemetry status。 | 入計畫範圍 |
| 4 | Windows 原生對 Codex 只是 instructions，不是真 hook，收益可能很低。 | A 級 | 0 | 分 Windows prompt-level、manual prefix、WSL hook 三路評估。 | 入計畫範圍 |
| 5 | 裝到同名 Rust Type Kit，誤以為 RTK 可用。 | A 級 | 0 | 只用官方來源；用 `rtk gain` 驗證正確套件。 | 入計畫範圍 |
| 6 | 為了省 token 新增大量流程，反而拖慢修 bug。 | B 級 | 0 | 只做短矩陣；未達 50% 實測 savings 或診斷退化就停止。 | 入計畫範圍 |

---

## 14. STR9 — Skill 收官 entry_points 機械化檢查

| Skill 名稱 | SKILL.md 啟動標記 | registry.json 登記 | `claude_path` 目錄存在 | slash_command 設定 |
|---|---|---|---|---|
| N/A | 本 Phase 不新增或收官 skill | N/A | N/A | N/A |
