# Handoff Truth Policy（P84.3）

> 狀態：ACTIVE（2026-05-18）
> 原則：新視窗只用 `NEXT_SESSION_HANDOFF.md` 頂部 `ACTIVE_BOOTSTRAP` 決定下一步；archive 舊段落只作歷史參考。

## 1. 機械檢查項

| Check | 規則 | Issue |
|---|---|---|
| Active markers | `ACTIVE_BOOTSTRAP_START` / `ACTIVE_BOOTSTRAP_END` 各只能有一個，且 start 必須在檔案最前面 | `HND001` |
| Required fields | 頂部狀態表必須有 Status / Program / Current Phase / Current Step / Mode / Latest Verified Commit / Updated At | `HND002` |
| Mode state | Mode 必須是狀態機允許值：DRAFT / FROZEN / APPROVED / IN_PROGRESS / VERIFYING / CLOSED | `HND003` |
| Six Anti-Drift Fields | 必須有 Current Phase / Current Step / Allowed Files / Forbidden Work / Exit Criteria / Resume Rule | `HND004` |
| Bootstrap consistency | 頂部 Current Phase/Step/Mode 必須與 Six Anti-Drift Fields 一致 | `HND005` |
| Archive boundary | `ARCHIVE_BELOW_DO_NOT_USE_FOR_NEXT_ACTION` 必須在 active bootstrap 之後 | `HND006` |
| ACTIVE_OPERATION consistency | `docs/ACTIVE_OPERATION.md` 的 Current Phase/Step/Mode 必須與 handoff 一致 | `HND007` |

## 2. 指令

```powershell
py scripts\check_handoff_truth.py --repo-root .
py scripts\check_handoff_truth.py --repo-root . --json
```

## 3. 邊界

- checker 只解析 active bootstrap，不解析 archive 舊段落。
- Current Step 以 `P##.#` step id 判定一致，允許描述文字不同。
- Current Phase 以 `P##` phase id 判定一致，允許括號內狀態描述不同。
- 此 checker 不判斷下一步內容是否策略正確；它只確保入口檔沒有自相矛盾。
