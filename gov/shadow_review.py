"""gov.shadow_review — 讀 shadow_ledger，判讀「某 guard 觀察期零誤判 → 可考慮升 strict」。

G3b（P104.4）：**只印建議、絕不自動改 config**（X1 不可逆隔離、X4-K 人工裁決，
呼應 P72.3 --sync-rules 只印不寫範式）。

飛輪 v2 判準（防「假零誤判升錯 guard」這個高風險誤判）：
- A. 結合 lint_guards：被標弱/幽靈護欄的 guard，即使零誤判也不建議升。
- B. 時間跨度：要 batches≥N 且 span_days≥M（防短時間刷次數的假象，避免虛榮指標）。

CLI：py -m gov.shadow_review [--n 30] [--days 7]
快照日期：2026-06-01（P104.4 / G3b）。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from gov.utils import find_repo_root, load_config
from gov.assertions import lint_guards
from gov import shadow_ledger


def _span_days(first_ts: str, last_ts: str) -> int:
    try:
        return (datetime.fromisoformat(last_ts) - datetime.fromisoformat(first_ts)).days
    except Exception:  # noqa: BLE001 — 壞 ts 視為 0 跨度
        return 0


def summarize(records: list[dict]) -> dict:
    """per-guard 統計：batches / assert_evals / failures / consecutive_clean / span_days / rotated。

    batches=distinct ts；consecutive_clean=從最新 ts 批次往回連續「該批次全 ok」的次數。
    rotated=ledger 含 rotate meta（曾輪轉 → consecutive_clean 可能被低估）。
    """
    rotated = any(r.get("event") == "rotate" for r in records)
    collected: dict[str, list] = {}
    for r in records:
        if r.get("event") == "rotate":
            continue
        gid = r.get("guard")
        if gid is None:
            continue
        collected.setdefault(gid, []).append(r)

    out: dict[str, dict] = {}
    for gid, rows in collected.items():
        batches = sorted({r.get("ts", "") for r in rows})
        failures = sum(1 for r in rows if not r.get("ok", False))
        # ts 批次級：每批次是否全 ok（同 ts 任一 assert 失敗 → 該批次失敗）
        batch_ok: dict[str, bool] = {}
        for r in rows:
            ts = r.get("ts", "")
            batch_ok[ts] = batch_ok.get(ts, True) and bool(r.get("ok", False))
        consec = 0
        for ts in reversed(batches):
            if batch_ok.get(ts, False):
                consec += 1
            else:
                break
        out[gid] = {
            "batches": len(batches),
            "assert_evals": len(rows),
            "failures": failures,
            "consecutive_clean": consec,
            "first_ts": batches[0] if batches else "",
            "last_ts": batches[-1] if batches else "",
            "span_days": _span_days(batches[0], batches[-1]) if batches else 0,
            "rotated": rotated,
        }
    return out


def recommend(stats: dict, weak: bool, n: int = 30, m_days: int = 7) -> tuple[bool, str]:
    """升 strict 建議判讀（只回建議，不改 config）。

    建議 = failures==0 且 batches≥n 且 span_days≥m_days 且 非弱護欄。
    任一不滿足 → 不建議，並回原因。
    """
    if stats.get("failures", 0) > 0:
        return False, f"有 {stats['failures']} 次失敗，標的可能腐化或不穩"
    if weak:
        return False, "⚠️ 被 lint 標為弱/幽靈護欄，零誤判可能是假象（不可升 strict）"
    if stats.get("batches", 0) < n:
        return False, f"觀察不足（{stats.get('batches', 0)}/{n} 次）"
    if stats.get("span_days", 0) < m_days:
        return False, f"觀察時間太短（{stats.get('span_days', 0)}/{m_days} 天）"
    return True, (f"連續零誤判 {stats.get('consecutive_clean', 0)} 次、跨 {stats['span_days']} 天、"
                  f"非弱護欄 → 可考慮升 strict（人工裁決）")


def _weak_guard_ids(root: Path) -> set:
    """跑 lint_guards 取得被標弱/幽靈護欄的 guard id 集合（A：擋假零誤判）。"""
    cfg = load_config(root)
    guards = cfg.get("guards", []) or []
    weak = set()
    for w in lint_guards(guards):
        gid = w.split(":", 1)[0].strip()  # lint 訊息格式 "<gid>: ..."
        if gid:
            weak.add(gid)
    return weak


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="shadow ledger 判讀：零誤判 guard 升 strict 建議（只印不改 config）")
    ap.add_argument("--n", type=int, default=30, help="建議升 strict 的最少觀察次數")
    ap.add_argument("--days", type=int, default=7, help="建議升 strict 的最少觀察天數")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = find_repo_root()
    records = shadow_ledger.read_records(root / "data" / "shadow_ledger.jsonl")
    stats = summarize(records)
    weak_ids = _weak_guard_ids(root)

    if not stats:
        print("（shadow ledger 無資料；先跑 py -m gov.assertions --check 累積判定）")
        return 0

    print(f"📊 shadow 判讀報告（門檻：≥{args.n} 次 且 ≥{args.days} 天 零誤判；只印建議·人工裁決）")
    for gid, s in sorted(stats.items()):
        ok, reason = recommend(s, weak=gid in weak_ids, n=args.n, m_days=args.days)
        flag = "🟢 建議考慮升 strict" if ok else "⏳ 維持 shadow"
        rot = "（曾輪轉）" if s.get("rotated") else ""
        print(f"  {flag}｜{gid}：{s['assert_evals']} 筆 / {s['batches']} 批次 / "
              f"失敗 {s['failures']} / 連續零誤判 {s['consecutive_clean']}{rot} / 跨 {s['span_days']} 天")
        print(f"      → {reason}")
    print("ℹ️  升 strict 為不可逆動作，本工具只印建議，需人工於 governance_config.yaml 拍板。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
