# Runbook / Risk Registry Governance Policy（P84.4）

> 狀態：ACTIVE（2026-05-18）
> 原則：新增 issue code 必須同時新增 runbook anchor；移動風險條目時，section 與 `狀態` 必須一致。

## 1. 機械檢查項

| Check | 規則 | Issue |
|---|---|---|
| Issue code mapping | `scripts/system_doctor.py`、`scripts/slo_checker.py`、`scripts/check_handoff_truth.py`、`scripts/governance_doctor.py` 內的 `DOC/SLO/HND/GOV###` 都必須有 runbook anchor | `GOV001` |
| Duplicate runbook anchor | `docs/OPERATIONS_RUNBOOK.md` 不得重複定義同一個 `<a id="..."></a>` | `GOV002` |
| Risk status section | Open section 內狀態必須含 `Open`；Closed section 內狀態必須含 `已` 或 `Closed` | `GOV003` |
| Duplicate risk id | `docs/RISK_REGISTRY.md` 不得重複使用同一個 `R-###` | `GOV004` |

## 2. 指令

```powershell
py scripts\governance_doctor.py --repo-root .
py scripts\governance_doctor.py --repo-root . --json
```

## 3. 更新 SOP

1. 新增任何 `DOC###` / `SLO###` / `HND###` / `GOV###` 時，同一個 commit 必須更新 `docs/OPERATIONS_RUNBOOK.md`。
2. Runbook anchor 使用 lowercase：`<a id="doc001"></a>`。
3. 風險仍需觀察時留在 `開放風險（Open）`，且狀態必須以 `Open` 開頭或包含 `Open`。
4. 風險已修補或已豁免關閉時移到 `已關閉風險（Closed）`，且狀態必須明確包含 `已` 或 `Closed`。
5. 每次 P84.4 相關收官前跑 governance doctor；若有 `GOV###`，先依 runbook 修正後再提交。

## 4. 邊界

- checker 只驗證可機械判定的格式與對應關係，不判斷風險內容是否策略正確。
- checker 不會修改 `docs/RISK_REGISTRY.md` 或 `docs/OPERATIONS_RUNBOOK.md`。
- `GOV###` 是治理層 issue code，不代表 daily runtime pipeline 失敗。
