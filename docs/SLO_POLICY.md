# SLO / Escalation Policy（P84.2）

> 狀態：ACTIVE（2026-05-18）
> 原則：本政策先 advisory-first；`scripts/slo_checker.py` 只讀 repo 狀態並輸出 SLO issue，不改寫資料、不阻擋 daily workflow。

## 1. SLO 目標

| SLO | 目標 | 預設門檻 | Issue |
|---|---|---|---|
| Production freshness | 最近尾端連續無 production report 不可超過門檻 | `--max-consecutive-no-production 1` | `SLO001` |
| Manifest completeness | SLO window 內不可缺 run manifest | `--max-missing-manifests 0` | `SLO002` |
| Doctor severity budget | doctor degraded day 不可長期累積；blocking day 直接升級 | `--max-doctor-degraded-days 2` | `SLO003` |

## 2. 指令

```powershell
py scripts\slo_checker.py --repo-root . --date 2026-05-18
py scripts\slo_checker.py --repo-root . --date 2026-05-18 --json
py scripts\slo_checker.py --repo-root . --date 2026-05-18 --window-days 7 --max-consecutive-no-production 1
```

## 3. 輸出解讀

- `SLO001`：production freshness 破門檻。若連續 2 天無 production，預設 `DEGRADED`；連續 3 天以上無 production，升級 `BLOCKING`。
- `SLO002`：window 內有日期缺 `data/runs/<date>/run_manifest.json`，預設 `BLOCKING`。
- `SLO003`：doctor severity 超過 budget。若任一天 doctor blocking，升級 `BLOCKING`；若 degraded days 超過門檻，輸出 `DEGRADED`。

## 4. 邊界

- SLO checker 會呼叫 `system_doctor.run_doctor(..., check_landing=False)` 檢查歷史日期，避免舊日期因首頁只指向最新報告而誤報。
- 本階段不接 GitHub Actions blocking gate；若未來要接 CI，先 advisory。
- SLO 結果是 pipeline health signal，不等於外部平台真的沒有輿情。
