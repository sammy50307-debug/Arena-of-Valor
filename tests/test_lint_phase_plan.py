from __future__ import annotations

import scripts.lint_phase_plan as lint


def test_m2_lint_ignores_numbered_17_layer_table():
    content = """
## 5. 17 層稽核表

| # | 層級 | 採用優化項 / N/A 理由 | 該層風險 | 緩解 |
|---|---|---|---|---|
| 1 | 代碼層 (Code) | helper | drift | centralize |
| 2 | 邏輯層 (Logic) | rules | wrong gate | tests |

## Pre-flight 多視角體檢

### M2 紅藍對抗

| # | 紅隊質疑 | 攻擊力 | pre-existing 失敗計次 | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | A | **S** | 0 | handle | 入計畫範圍 |
| 2 | B | **S** | 0 | handle | 入計畫範圍 |
| 3 | C | A | 0 | handle | 入計畫範圍 |
| 4 | D | A | 0 | handle | 入計畫範圍 |
| 5 | E | A | 0 | handle | 入計畫範圍 |
"""
    lint.errors.clear()
    lint.warnings.clear()

    lint.lint_red_team_m2(content)

    assert lint.errors == []
    assert lint.warnings == []

