"""tests/test_shadow_review.py — G3b：shadow 判讀報告 + size cap 的契約測試。

先寫測試再實作（TDD）。P104.4 / G3b（飛輪 v2：A 結合品質、B 時間跨度、C 矩陣鎖、D rotate 可追溯）。
測試慣例對齊 test_shadow_ledger.py：sys.path 注入、tmp_path 隔離、write_text utf-8。

涵蓋：
- C. recommend() 升 strict 建議矩陣鎖（failures/batches/span/weak 四維度）
- B. summarize() 時間跨度 span_days + ts 批次級 consecutive_clean
- D. rotate() 保留後半 + meta record + 警告；summarize 標 rotated
- size cap：append(max_lines=) 超限自動 rotate，不無限長大
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from gov import shadow_ledger, shadow_review


# ── C. 升 strict 建議矩陣鎖（契約：四維度組合定死，防未來判讀邏輯改錯）──
@pytest.mark.parametrize("failures,batches,span,weak,expect", [
    (0, 50, 30, False, True),    # 全達標 → 建議
    (1, 50, 30, False, False),   # 有失敗 → 不建議
    (0,  5, 30, False, False),   # 觀察不足（batches<30）→ 不建議
    (0, 50,  1, False, False),   # 時間太短（span<7）→ 不建議（B）
    (0, 50, 30, True,  False),   # 弱護欄 → 不建議（A：防假零誤判升錯 guard）
])
def test_recommend_matrix(failures, batches, span, weak, expect):
    stats = {"failures": failures, "batches": batches, "span_days": span}
    ok, reason = shadow_review.recommend(stats, weak=weak, n=30, m_days=7)
    assert ok is expect, f"failures={failures} batches={batches} span={span} weak={weak}: {reason}"
    assert isinstance(reason, str) and reason, "須附建議/不建議的原因說明"


# ── B. summarize 基本統計：batches(distinct ts) / assert_evals / failures ──
def test_summarize_basic():
    records = [
        {"guard": "G", "assert": "a", "ok": True, "ts": "2026-06-01T10:00:00"},
        {"guard": "G", "assert": "b", "ok": True, "ts": "2026-06-01T10:00:00"},  # 同 ts 批次
        {"guard": "G", "assert": "a", "ok": False, "ts": "2026-06-02T10:00:00"},
    ]
    s = shadow_review.summarize(records)["G"]
    assert s["batches"] == 2          # 2 個 distinct ts
    assert s["assert_evals"] == 3     # 3 筆 record
    assert s["failures"] == 1


# ── B. 時間跨度 span_days ──
def test_summarize_time_span():
    records = [
        {"guard": "G", "assert": "a", "ok": True, "ts": "2026-06-01T10:00:00"},
        {"guard": "G", "assert": "a", "ok": True, "ts": "2026-06-10T10:00:00"},
    ]
    s = shadow_review.summarize(records)["G"]
    assert s["span_days"] == 9        # 06-01 → 06-10


# ── B. ts 批次級 consecutive_clean（從最新往回，連續「該批次全 ok」的次數）──
def test_summarize_consecutive_clean():
    records = [
        {"guard": "G", "assert": "a", "ok": False, "ts": "2026-06-01T10:00:00"},  # 批次失敗
        {"guard": "G", "assert": "a", "ok": True, "ts": "2026-06-02T10:00:00"},   # 全 ok
        {"guard": "G", "assert": "a", "ok": True, "ts": "2026-06-03T10:00:00"},   # 全 ok
    ]
    s = shadow_review.summarize(records)["G"]
    assert s["consecutive_clean"] == 2  # 06-02、06-03，回到 06-01 失敗停


# ── D. summarize 偵測 rotate meta → 標 rotated ──
def test_summarize_marks_rotated():
    records = [
        {"event": "rotate", "dropped": 100, "ts": "2026-06-01T00:00:00"},
        {"guard": "G", "assert": "a", "ok": True, "ts": "2026-06-02T10:00:00"},
    ]
    s = shadow_review.summarize(records)["G"]
    assert s["rotated"] is True, "ledger 曾輪轉應被標記（consecutive_clean 可能被低估）"


# ── D. rotate：超 max_lines 保留後半 + 記 meta + 印警告 ──
def test_rotate_keeps_latter_half_and_logs_meta(tmp_path: Path, capsys):
    led = tmp_path / "led.jsonl"
    for i in range(10):
        shadow_ledger.append([{"guard": f"G{i}", "assert": "a", "ok": True}], led, max_lines=10000)
    shadow_ledger.rotate(led, max_lines=4, keep=2)
    out = shadow_ledger.read_records(led)
    metas = [r for r in out if r.get("event") == "rotate"]
    assert len(metas) == 1, "應記一筆 rotate meta"
    assert metas[0]["dropped"] >= 1
    assert any(r.get("guard") == "G9" for r in out), "保留後半（較新的 G9 應在）"
    captured = capsys.readouterr()
    assert "輪轉" in captured.out or "rotate" in captured.out.lower(), "rotate 應印警告"


# ── size cap：append(max_lines=) 超限自動 rotate，不無限長大 ──
def test_append_auto_rotate_on_cap(tmp_path: Path):
    led = tmp_path / "led.jsonl"
    for i in range(30):
        shadow_ledger.append([{"guard": "G", "assert": "a", "ok": True}], led, max_lines=6)
    out = shadow_ledger.read_records(led)
    assert len(out) <= 12, f"超 max_lines 應自動輪轉、不無限長大，實際 {len(out)}"


# ── G3a 既有 append（不傳 max_lines）行為不退：預設大、不觸發 rotate ──
def test_append_default_no_rotate(tmp_path: Path):
    led = tmp_path / "led.jsonl"
    shadow_ledger.append([{"guard": "G", "assert": "a", "ok": True}], led)  # 不傳 max_lines
    out = shadow_ledger.read_records(led)
    assert len(out) == 1
    assert not any(r.get("event") == "rotate" for r in out), "單筆不該觸發 rotate"


# ── main() smoke：讀真實 ledger 跑不崩、exit 0（只印不改 config）──
def test_main_smoke():
    rc = shadow_review.main([])
    assert rc == 0
