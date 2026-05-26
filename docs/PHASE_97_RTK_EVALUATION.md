# Phase P97 Runtime Evidence — RTK Token Savings Evaluation

> Status: COMPLETED / INSTALL BLOCKED. 主公已核准 P97 evaluation runtime；本文件記錄隔離下載、dry-run、baseline、failure diagnostics、telemetry 與 rollback 證據。P97 結論是不全域部署、不執行 `rtk init`、不把 RTK 寫進 AOV `AGENTS.md`。

---

## 0. Runtime Boundary

| 項目 | 裁決 |
|---|---|
| Runtime 日期 | 2026-05-27 Asia/Taipei |
| Binary 模式 | Isolated only: `scratch/rtk_eval/bin/rtk.exe` |
| 全域 PATH | 未加入；`Get-Command rtk` runtime 前後皆 `NOT_FOUND` |
| Project init | 未執行；只跑 `rtk init --codex --dry-run -v` |
| Global init | 未執行 |
| Telemetry | `RTK_TELEMETRY_DISABLED=1`；`telemetry status` 顯示 blocked |
| GitHub Actions | 未修改 |
| Daily Monitor | 未修改 |
| 全域 `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` | 未修改 |

---

## 1. Source Verification

| 來源 | Runtime 查到的重點 | 裁決 |
|---|---|---|
| GitHub releases API | latest release: `v0.42.0`，published `2026-05-24T15:42:11Z`，非 prerelease | 使用 latest Windows binary 做隔離評估 |
| `https://www.rtk-ai.app/docs/getting-started/installation/` | Windows prebuilt binary 是 `rtk-x86_64-pc-windows-msvc.zip`；官方建議用 `rtk --version` / `rtk gain` 驗證 | 採用 zip，不用 Cargo，不用 curl pipe |
| `https://www.rtk-ai.app/docs/getting-started/quick-start/` | `--dry-run` 會列出 would-change，且不寫入 | 只跑 dry-run |
| `https://www.rtk-ai.app/docs/getting-started/supported-agents/` | Codex CLI 是 AGENTS.md instructions 類；Windows native auto-rewrite 不完整 | 不把 Codex 視為透明 hook 收益 |
| `https://www.rtk-ai.app/docs/getting-started/configuration/` | `RTK_TELEMETRY_DISABLED=1` 可禁用 telemetry；`rtk proxy` 可保留 raw 行為 | P97 預設禁用 telemetry，failure debug 可用 proxy/raw |
| `https://www.rtk-ai.app/docs/resources/telemetry/` | telemetry 需 opt-in；可用 `rtk telemetry status` 檢查 | 本輪 status 顯示未同意且 env blocked |

---

## 2. Binary And Checksum Evidence

| 項目 | 值 |
|---|---|
| Release | `v0.42.0` |
| Downloaded asset | `rtk-x86_64-pc-windows-msvc.zip` |
| Local zip | `scratch/rtk_eval/downloads/rtk-x86_64-pc-windows-msvc.zip` |
| Extracted exe | `scratch/rtk_eval/bin/rtk.exe` |
| Expected SHA256 | `527552ec419988ff4a862415ba28d5aa7c1148ef3dc926ae11a4c133e63a7491` |
| Actual SHA256 | `527552ec419988ff4a862415ba28d5aa7c1148ef3dc926ae11a4c133e63a7491` |
| Checksum verdict | PASS |
| `rtk --version` | `rtk 0.42.0` |
| `rtk gain` before tests | `No tracking data yet.` |

Evidence files are intentionally kept under git-ignored `scratch/rtk_eval/` and are not staged.

---

## 3. Dry-run Evidence

Command:

```powershell
$env:RTK_TELEMETRY_DISABLED = "1"
.\scratch\rtk_eval\bin\rtk.exe init --codex --dry-run -v
```

Observed would-change:

| Would-change | Details | Runtime decision |
|---|---|---|
| Create `RTK.md` | Contains Codex guidance: always prefix shell commands with `rtk` | Not applied |
| Patch project `AGENTS.md` | Adds `@RTK.md` reference at file end | Not applied |
| Footer | `[dry-run] Nothing written.` | PASS |

Tracked git status before/after dry-run:

| Check | Result |
|---|---|
| `git status --porcelain=v1 --untracked-files=no` before | empty |
| same command after | empty |
| tracked_changed | `false` |

Verdict: dry-run was truthful for tracked repo files. However, a real `rtk init --codex` would modify project instructions, so it must remain blocked unless主公 opens a later install phase.

---

## 4. Telemetry And Local Residue Evidence

Telemetry status:

```text
consent:       never asked
enabled:       no
env override:  RTK_TELEMETRY_DISABLED=1 (blocked)
device hash:   (no salt file)
```

Local side effect found after running RTK commands:

| Path | Meaning | Cleanup |
|---|---|---|
| `C:\Users\sammy\AppData\Local\rtk\history.db` | local savings history, 24576 bytes | removed |
| `C:\Users\sammy\AppData\Local\rtk\.hook_warn_last` | local hook warning marker | removed |

Cleanup verification:

| Check | Result |
|---|---|
| `C:\Users\sammy\AppData\Local\rtk` exists after cleanup | `false` |
| `history.db` exists after cleanup | `false` |
| `.hook_warn_last` exists after cleanup | `false` |

Verdict: RTK was not installed, but normal command use did create local AppData tracking residue. P97 removed the residue after saving evidence.

---

## 5. Baseline Matrix

Token estimate uses `ceil(chars / 4)` as a rough comparison only.

| Sample | Raw command | RTK command | Raw exit | RTK exit | Raw chars | RTK chars | Savings | Fidelity verdict |
|---|---|---|---:|---:|---:|---:|---:|---|
| Git status | `git status --short --branch` | `rtk git status --short --branch` | 0 | 0 | 1132 | 1131 | 0.1% | PASS but no practical savings |
| Git log | `git log -20 --oneline --decorate` | `rtk git log -20 --oneline --decorate` | 0 | 0 | 1097 | 1097 | 0.0% | PASS but no savings |
| Search | `git grep -n -E P97\|R-018\|RTK -- docs NEXT_SESSION_HANDOFF.md` | `rtk git grep ...` | 0 | 0 | 15654 | 15654 | 0.0% | PASS but no savings |
| File read | `Get-Content docs\PHASE_97_PLAN.md -TotalCount 180` | `rtk read docs\PHASE_97_PLAN.md` | 0 | 0 | 12842 | 14664 | -14.2% | FAIL for savings in this sample |
| Pytest pass | `py -m pytest -q tests\test_report_content_trust_checker.py` | `rtk pytest -q tests\test_report_content_trust_checker.py` | 0 | 0 | 100 | 17 | 83.0% | PASS; good candidate |
| Pytest missing file | `py -m pytest -q tests\__p97_rtk_missing_file__.py` | `rtk pytest -q tests\__p97_rtk_missing_file__.py` | 4 | 4 | 98 | 27 | 72.4% | WARNING; path detail lost |

Post-matrix `rtk gain`:

| Metric | Result |
|---|---|
| Total commands | 8 |
| Tokens saved | 22 |
| Efficiency meter | 0.3% |
| Top command | `rtk pytest -q ...` saved 21 tokens / 84.0% |

Verdict: RTK is useful for selected noisy test outputs, but this AOV Windows sample does not support broad claims for Git/search/read commands.

---

## 6. Failure Diagnostics Check

### 6.1 Pytest Missing File

Raw stderr preserved exact missing path:

```text
ERROR: file or directory not found: tests\__p97_rtk_missing_file__.py
```

RTK output:

```text
Pytest: No tests collected
```

Verdict: exit code was preserved, but the actionable missing path was removed. This is acceptable only for quick high-level status, not for debugging.

### 6.2 Python Traceback Via `rtk err`

Raw stderr contained sentinel:

```text
RuntimeError: RTK_EVAL_SENTINEL_FAILURE stack trace marker
```

RTK stderr changed the message:

```text
RuntimeError: No active exception to reraise
```

`rtk proxy py -c ...` preserved the raw sentinel.

Verdict: `rtk err` is not approved for Python inline failure diagnostics on this Windows/PowerShell setup. Any later pilot must route unknown failures through raw command or `rtk proxy`, not compressed `rtk err`.

---

## 7. Exit Criteria Verdict

| P97 evaluation criterion | Result | Evidence |
|---|---|---|
| Dry-run proves would-change and no repo writes | PASS | Would create `RTK.md`, patch `AGENTS.md`; tracked diff stayed empty |
| Baseline covers at least 6 command classes | PASS | 6 samples in matrix |
| Failure diagnostics remain actionable | FAIL | Missing path and sentinel were lost in two samples |
| Telemetry disabled | PASS | `RTK_TELEMETRY_DISABLED=1 (blocked)` |
| Rollback path verified | PASS | isolated binary only; AppData residue removed |
| Decision gate reached | PASS | Do not install globally; optional P98 project-local/manual-prefix pilot only |

---

## 8. Decision

P97 runtime decision:

- Do not deploy RTK globally.
- Do not run `rtk init --codex`.
- Do not add `@RTK.md` to AOV `AGENTS.md`.
- Do not put RTK into PATH.
- Do not use RTK for Python inline failures, unknown debug failures, `git grep`, or plan/document reads.
- RTK may be worth a later P98 pilot only as a manual-prefix helper for known noisy passing test commands, with raw/proxy fallback mandatory.

Recommended P98 shape if主公 wants to continue:

| Candidate | Rule |
|---|---|
| `rtk pytest -q <known focused tests>` | Allowed in manual pilot when the goal is high-level pass/fail compaction |
| `rtk proxy <cmd>` | Allowed when wanting RTK tracking without filtering |
| raw command | Required for debugging, traceback, missing file, security-sensitive output, or unfamiliar failure |
| `rtk init --codex` | Still blocked until a separate install phase and explicit主公 approval |
| global deployment | Blocked; evidence is not strong enough |

P97 final裁決: RTK has a narrow useful lane, but it is not trustworthy enough for global deployment in the current AOV Windows/Codex workflow.

