# 🤝 P111 交接手冊 v3（新視窗開局讀這份 + PHASE_111_PLAN.md v3 即可無縫動工）

> 更新：2026-06-14｜交接人：規劃視窗 Claude（Opus 4.8 1M）｜給：P111 動工視窗
> 一句話：**P111 計畫書 v3 已凍結（lint PASS、阿喜核准）→ 新視窗動工 S1-S5（D-lite+ 全自動 L5，發布決策與 cron 同源）。**

---

## 🎯 TL;DR — 新視窗第一件事

1. 開局讀 memory（`MEMORY.md` + `project_status.md`，已標 P111 v3 凍結）+ 本手冊 + **`docs/PHASE_111_PLAN.md` v3（凍結版，唯一真相源）**
2. P111 已凍結、無需再確認凍結，**直接動工 S1 → S5**（守 L5 邊界 + 同源閘門）
3. 動工前置已完成：P110 尾巴已 commit（`f44a04d`）；工作區乾淨

---

## 📐 設計 = D-lite+（全自動，發布決策與 cron 逐位元同源）

self-heal **不自己決定發布**，而是跑與 main.py 完全相同的發布閘門：
```
analysis 缺 → return 1（既有）
report 在（重用 check_daily_report_health.report_path，統一 repo_root）→ no-op return 0
tier 非 publishable（含 tier 空，is_publishable_quality_tier）→ no-op + ::warning:: 降級 L4
斷言 candidate.stem == aov_report_<date>
generate(promote=False) → candidate
run_checks(candidate) 逐位元複製 main.py:132-139 → gate_reasons
should_promote(True, tier, len(gate_reasons)) → promote_candidate；否則 no-op + ::warning::
--check-health re-check（僅 promote 時 gate 住）
```
**核心承諾**：self-heal 不可能發布 cron 本來不會發布的報告（用同一把尺）。

## 🔴 兩輪飛輪 8 視角對抗審查結論（已 Claude 親核 file:line，新視窗不用重查）

- **第一輪揪 S 級致命洞**：report 缺主因是品質閘門**刻意不 promote**（main.py:706 寫 analysis → :716 `generate(promote=False)` → :780 `should_promote` 不過閘 → :793 跳過 → analysis 在 report 缺）。replay 用 `generator.py:94` 預設 `promote=True` 會**自動發布劣質報告到首頁**。→ 故需 D-lite+ 同源閘門。
- **第二輪 D-lite 落地壓測收斂 9 必修**（已全納入 v3 計畫書 §9 Stages）：
  - run_checks 參數**逐位元複製 main.py:132-139**（尤其 `check_landing=False`，否則 candidate 未 promote 時 landing 假陽性 FAIL → 自癒永遠降級）
  - `should_promote` 抽純函數放 run_manifest，main.py:780 + D-lite 共用（防漂移）
  - **freshness sidecar 受 promote gate**（generator.py:422 無條件寫 → no-op 留孤兒污染 P110 凍結偵測器；**cron 路徑也有此既有缺陷**，飛輪修一併解）
  - manifest 移到 conditional promote 之後、標 self_heal/promoted
  - G-i 真跑 generate 5 case（棄 _fake_generate 寫死路徑）+ 三隔離；G-ii sys.modules subprocess 鎖具體 client 名

## 🔑 已核實關鍵 file:line（新視窗動工直接用）
- `generator.py:89-95` generate(promote=True 預設)；:374-383 candidate version；:385-393 if promote→promote_candidate；:422-427 `_write_freshness_sidecar` 無條件（**S1 要移入 :385 if promote**）；:479-496 promote_candidate（os.replace + :495 _update_landing_page）
- `main.py:706` 寫 analysis；:716 generate(promote=False)；:773 evaluate_publish_gate；:780 `should_promote = bool(candidate) and is_publishable_quality_tier(tier) and len(gate_reasons)==0`（**S1 改呼叫純函數**）；:793-799 跳過 promote；:728-730 generate 例外被吞（主根因，治本登記 future）；:106-153 evaluate_publish_gate（run_checks 參數範本）
- `run_manifest.py:40-44` PUBLISHABLE={production_full,production_llm_partial,production_local_only}；:215-216 is_publishable_quality_tier（**S1 加 should_promote 純函數**）
- `check_daily_report_health.py:58-59` report_path；:127-135 run_checks 簽名；:168-171 canonical exists；:350 main return
- `replay_run.py:20-23` 零 LLM import；:117-120 analysis 缺 return1；:167-168 generate（**S2 改 promote=False + gate**）；:189-209 --check-health
- CI：`daily_report.yml:63-80` Execute Pipeline；:82-89 Upload Artifact；:91-97 Fallback Push（git add data/reports/ index.html）；self-heal step 插 89 後 91 前

## 🛡️ L5 安全邊界（動工必守）
零 LLM 額度（G-ii 已實測 import 158 模組零 SDK）/ 重渲染窄面 / **不繞品質閘門（should_promote 共用 + run_checks 同尺）** / 失敗 graceful 降級 L4（`|| echo ::warning::`，不加 if:always()）/ 不新增 push 授權（沿用 Fallback Push）/ TZ=Asia/Taipei / 不可逆仍問阿喜。

## 📋 5 Stages（詳見 v3 計畫書 §9）
- **S1 同源閘門地基**：run_manifest 加 should_promote 純函數 / main.py:780 改呼叫 / generator sidecar 移入 if promote。驗：main.py 既有 + P110 freshness 測試零回歸。
- **S2 replay self-heal**：replay_run 加 `--heal-if-missing`（上方流程）+ docstring 反向指針。
- **S3 CI step**：daily_report.yml 加 self-heal step。
- **S4 測試**：tests/test_self_heal_replay.py（G-i 真跑 5 case + 三隔離；G-ii sys.modules subprocess）。
- **S5 收官**：TASK_HISTORY + 飛輪成熟度 L4→可控 L5 + RISK(R-037/R-038/R8) + postmortem(4 通則) + memory + runbook。

## 🚫 鐵律
- `py` 不用 `python`（本地 Win）；**CI yaml 內 python 正確**（Linux runner）
- TASK_HISTORY.md 禁全讀：`grep -n "^### "` 錨點 + Read offset≤200；寫用 Add-Content here-string
- 改動前計畫書已凍結（v3）；**push 前問阿喜**；稱呼「阿喜」繁中
- pre-push hook 在 `.githooks`（core.hooksPath），非 .git/hooks

## 📂 git 現況
- `main` = `f44a04d`（**P110 v2 尾巴一致性硬化，標當前 Claude，本地未 push、領先 origin 1**）；前一 commit `b49f9a8`（P110）
- **untracked 待 P111 動工一起 commit**：`docs/PHASE_111_PLAN.md`（v3 凍結）+ 本手冊
- pre-existing untracked（`.codex/`、`scratch/`、`.agents/skills/source-command-*` 等）非本線、勿碰
- **量測腳本**：`scratch/p111_trigger_freq.py` / `p111_manifest_scan.py`（飛輪 Evidence：本地觸發 0 次 + tier 空 8/11 高頻），收官可清

## 📖 memory 落點
- `project_status.md`：P111 v3 凍結 + 8 視角審查 + D-lite+ 設計（已更新）
- `RISK_REGISTRY.md`：收官時登記 R-037（self-heal 邊界）/R-038（no-op candidate 進版控，cron 既有）

---

*交接手冊 v3 by 規劃視窗 Claude｜新視窗：讀此 + PHASE_111_PLAN.md v3 → 直接動工 S1-S5。D-lite+ 同源閘門 + 9 必修是重點。*
