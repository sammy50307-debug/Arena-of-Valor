# ACTIVE OPERATION — R-016 Zero-Cost Reliability Program

> 本檔是 L2 短版狀態真相。新視窗一般只需讀 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`；只有 bootstrap 要求時才讀本檔。

## Current State

| 欄位 | 內容 |
|---|---|
| **Program** | R-016 Zero-Cost Evidence-first Reliability Program |
| **Current Phase** | P85（Evidence-first + Quality-tiered Zero-Cost Reliability / FROZEN） |
| **Current Step** | P85 FROZEN：零額外付費 R-016 修復總計畫已凍結；等待主公核准 P86 才能改程式碼 |
| **Mode** | FROZEN |
| **Latest Verified Commit** | `HEAD docs: 凍結 P85 zero-cost reliability plan`（本地 commit，待主公確認 push） |
| **Timezone** | Asia/Taipei |
| **Updated At** | 2026-05-19 |

## Handoff Arbitration Order

若文件互相衝突，依下列順序仲裁：

1. `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP`
2. `docs/ACTIVE_OPERATION.md`
3. 當前 Phase 計畫：`docs/PHASE_85_PLAN.md`
4. R-016 風險登記：`docs/RISK_REGISTRY.md`
5. `TASK_HISTORY.md` 物理證據（只能 anchor search，不全讀）

## Six Anti-Drift Fields

| 欄位 | 當前值 |
|---|---|
| **Current Phase** | P85（FROZEN） |
| **Current Step** | P85 FROZEN：等待主公核准 P86 Gemini Model & Schedule Modernization |
| **Allowed Files** | FROZEN 狀態只允許讀 `docs/PHASE_85_PLAN.md`, `docs/ACTIVE_OPERATION.md`, `docs/RISK_REGISTRY.md`, `NEXT_SESSION_HANDOFF.md`；若要修正 P85 文件真相，可改 docs/handoff/history，但不可改 runtime code |
| **Forbidden Work** | 不全讀 `TASK_HISTORY.md`；不 git push；不 stage unrelated untracked reports；不加 `OPENAI_API_KEY`；不接免費 provider；不改 `.github/workflows/daily_report.yml`；不改 `analyzer/**` / `main.py`；不把 R-016 標記 Closed |
| **Exit Criteria** | P85 只凍結計畫，不關閉 R-016；P86-P95 需逐 Phase 核准與驗證後才能收斂 R-016 |
| **Resume Rule** | 新視窗先讀 `NEXT_SESSION_HANDOFF.md` 頂部 active bootstrap；若主公說「開始」，先確認是核准 P86，再依 P86 scope 動工 |

## State Machine

```text
DRAFT -> FROZEN -> APPROVED -> IN_PROGRESS -> VERIFYING -> CLOSED
```

| 狀態 | AI 可做事項 |
|---|---|
| **DRAFT** | 只能討論，不可改檔 |
| **FROZEN** | 等主公核准，不可改檔 |
| **APPROVED** | 可依計畫動工 |
| **IN_PROGRESS** | 繼續當前 step |
| **VERIFYING** | 只能測試、修同範圍問題 |
| **CLOSED** | 不可再改，開下一 Phase |

## Required Verification

```powershell
git status -sb
git diff --check
py scripts/lint_phase_plan.py docs/PHASE_85_PLAN.md
rg -n "ACTIVE_BOOTSTRAP_START|ACTIVE_BOOTSTRAP_END|ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION" NEXT_SESSION_HANDOFF.md
```

## Latest Evidence

R-016.2 已完成 LLM fallback/secret diagnostics，且 Actions 證據顯示 `GEMINI_API_KEY configured`、`OPENAI_API_KEY missing`。主公明確不想增加 OpenAI API 費用，因此 P85 已把 R-016 修復方向凍結為 Evidence-first + Quality-tiered Production + LLM Enrichment Queue。R-016 仍 Open；P85 不是 production 恢復。

## Next Decision

下一步是主公是否核准 P86。P86 的第一件事是 Gemini Model & Schedule Modernization：開工前需二次查證官方 Gemini rate limit / model availability；核准前不得改程式碼或 workflow。
