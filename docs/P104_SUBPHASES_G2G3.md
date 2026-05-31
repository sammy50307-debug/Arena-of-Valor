# P104 子 Phase 執行卡 — G2/G3 拆解（P104.2 / P104.3 / P104.4）

> **母計畫書**：`docs/P104_NEXT_STAGE_FUSION_PLAN.md`（FROZEN，已過 17 層 + M1/M2 lint）
> **本卡**：主公 2026-05-31 核准「3-phase 拆 + 精簡執行計畫」深度。每個子 phase 獨立 commit、可回退。
> ⚠️ **接手建議**：fresh session 或換模型執行——P104 G1 的 session 曾幻覺 3 次（長 context + 混亂工具信號）。
> **鐵律**：用 `py` 不用 `python`；禁全讀 TASK_HISTORY；push 前問主公；**先寫測試/guard 再實作**（讓防線能反抓作者幻覺）。

---

## 共同基線與防幻覺紀律

- **測試基線**：313 passed（含 G1 `tests/test_assertions.py` 5 個）。每個子 phase Exit 須 **≥313 不退**。
- **G1 現狀**（已 commit `0e7d5b1` + push）：`governance_config.yaml` 有 5 個 shadow guard，`py -m gov.assertions --check` = 5 guard / 8 斷言 / 0 失敗 / exit 0。
- **防幻覺**：每次寫檔／改檔後，用**獨立命令**（`git diff` / Read / `--check` / `pytest`）交叉核對，**不信工具回傳訊息**（G1 session 實證：Edit 回傳訊息曾誤報改了哪個檔、--check 數字曾被腦補）。
- **dry-run → 拍板 → 可回退**：每個 phase 動工前給主公看 dry-run。

---

## P104.2（G2）— health.py 回填「壞了會叫」

**目標**：AOV 補上「主動跑 skill smoke + 失敗發 Discord 告警」的 runtime 防線（現有 `scripts/gen_skill_health.py` 只出靜態看板、不跑 test、不告警）。

**scope（4 步）**：
1. 複製 `D:/skills-governance/gov/health.py` → `AOV/gov/health.py`（源 76 行：`check_skill` 跑 `test_skill.py` smoke、`notify_discord` 發告警、`run`/`main`）。
2. **路徑在地化**：源用 `root/"skills"`（health.py:62），但 **AOV skill 實際在 `.agent/skills/`**（見 R-024 描述）→ 動工**先驗證 AOV 真實 skill 路徑**再改，不照搬。
3. **Discord 告警 graceful**：webhook 從 `.env` 的 `DISCORD_WEBHOOK` 讀（health.py:36-44），未設或佔位符 → 只印不發。**webhook 絕不進 git**（資安最高，推送前掃描）。
4. **與 gen_skill_health.py 分工**：health.py = 跑 smoke + 告警（runtime checker）；gen_skill_health.py = 出靜態 Markdown 看板。寫分工說明（docstring + 一處 docs）。

**影響檔**：`gov/health.py`（新）、`tests/test_health.py`（新）、分工說明（docstring/docs）。約 3-4 檔。
**Exit**：`py -m gov.health` 跑通；無 webhook 時 graceful 只印不發；新測試綠；全套 ≥313+。
**可逆**：半可逆（刪 health.py 即還原）。
**風險**：路徑契約對不上（.agent/skills）→ 動工先驗證 + 測試覆蓋；webhook 外洩 → .env + 佔位符 + 推送前掃描。

---

## P104.3（G3a）— shadow 顯式分支 + ledger 寫入

**目標**：讓 shadow 成為一等公民——目前 `check()` 對 shadow **無顯式分支**（assertions.py:85-95，靠「非 advisory 不跳過 + 非 strict 不 FAIL」的縫隙），shadow 失敗會混進 `failures`、與 strict 視覺難分。

**scope（3 步）**：
1. `gov/assertions.py` `check()` 加 **shadow 顯式分支**：shadow guard 失敗記入獨立 `shadow_findings`（不混 `failures`、不設 FAIL、exit 仍 0）。**不得破壞 G1 既有 advisory（skip）/ strict（FAIL）行為**。
2. 新增 `gov/shadow_ledger.py`：append-only jsonl，記每次 shadow 判定（guard id / assert / ok / ts）。silent no-op on error（不拖垮主流程）。
3. `check()` 跑 shadow guard 時寫 ledger。

**影響檔**：`gov/assertions.py`（改 check）、`gov/shadow_ledger.py`（新）、`tests/`（補）。約 3 檔。
**Exit**：shadow guard 判定寫入 ledger；exit 0 不誤擋；**G1 的 5 guard + `test_assertions.py` 全綠不退**；新測試綠。
**可逆**：半可逆（git 回退 + 刪 ledger 檔）。
**dry-run 要點**：改 check() 前先 Read assertions.py 確認插入點；改完**立刻對拍 `test_assertions.py`**（G1 的 advisory/strict/shadow 行為不能壞）。

---

## P104.4（G3b）— shadow 觀察判讀 + size cap

**目標**：把 ledger 變成「升 strict 的決策依據」+ 防無限長大。

**scope（3 步）**：
1. 讀 shadow ledger 統計：每個 guard 的「評估次數 / 失敗次數 / 連續零誤判」。
2. **size cap / 輪轉**：ledger 超過上限（如 5000 行）保留後半（呼應 R-012 metrics retention 教訓）。
3. 產出「某 guard 觀察期零誤判 → 可考慮升 strict」**判讀報告**（**只印建議、不自動升 strict**——X1 不可逆隔離、X4-K 人工裁決，呼應 P72.3 `--sync-rules` 只印不寫範式）。

**影響檔**：`gov/shadow_ledger.py`（加讀取/統計/輪轉）或新 `gov/shadow_review.py`、`tests/`。約 2-3 檔。
**Exit**：能報告 guard 觀察統計；ledger 有 size cap；測試綠 ≥313+。
**可逆**：半可逆。
**dry-run 要點**：升 strict 判讀**只印不自動改 config**（人工拍板才升）。

---

## 收官（P104 整體，三子 phase 完成後）

- 更新母計畫書 `P104_NEXT_STAGE_FUSION_PLAN.md` 狀態轉換 → DONE。
- TASK_HISTORY 追加 P104 整體收官（cat>>heredoc）。
- 可選：postmortem（若過程觸發「我以為」或設計缺陷）。
- **G4 metrics 維持緩**（R-024 已 Closed，accepted 設計限制；要做需另議觸發機制重設計，非引擎 scope）。

---

## 執行順序

`P104.2（獨立）` → `P104.3（建 ledger）` → `P104.4（依賴 .3 的 ledger）`。每個獨立 dry-run → 拍板 → commit → 可回退。
