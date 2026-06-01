"""gov.shadow_ledger — shadow guard 判定的 append-only 流水帳（ledger）。

G3a（P104.3）：記錄每次 shadow guard 判定，供 G3b 判讀「連續零誤判 → 可考慮升 strict」。
設計：
- append-only jsonl，每筆 {v, ts, guard, assert, ok}（v=schema version，未來格式可演進）。
- silent no-op on error：寫入失敗（權限/磁碟/路徑）絕不拋例外、不拖垮 check() 主流程。
- read_records 容錯：壞行 skip、檔案不存在回 []，讓 G3b 讀取永不崩。
快照日期：2026-06-01（P104.3 / G3a）。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1


def append(records: list[dict], ledger_path: Path, max_lines: int = 5000) -> None:
    """把 shadow 判定逐筆 append 到 jsonl；每筆補上 v(schema) 與 ts。

    append 後若行數超 max_lines → 自動 rotate（size cap，呼應 R-012 防無限長大）。
    silent no-op on error：任何 IO/序列化失敗都靜默吞掉，不拖垮健檢主流程。
    """
    if not records:
        return
    try:
        ledger_path = Path(ledger_path)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        with ledger_path.open("a", encoding="utf-8") as f:
            for r in records:
                row = {"v": SCHEMA_VERSION, "ts": ts, **r}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — ledger 失敗絕不拖垮健檢主流程
        return
    rotate(ledger_path, max_lines)


def rotate(ledger_path: Path, max_lines: int = 5000, keep: int | None = None) -> None:
    """ledger 超 max_lines → 保留後 keep 行（較新）+ 記一筆 rotate meta + 印警告。

    D（可追溯）：rotate 會切斷歷史，故記 meta（event=rotate）讓 summarize 知道「曾輪轉」、
    consecutive_clean 可能被低估。keep 預設 max_lines//2。silent on error 不拖垮主流程。
    """
    if keep is None:
        keep = max_lines // 2
    try:
        ledger_path = Path(ledger_path)
        if not ledger_path.exists():
            return
        lines = ledger_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if len(lines) <= max_lines:
            return
        dropped = len(lines) - keep
        kept = lines[-keep:] if keep > 0 else []
        ts = datetime.now().isoformat(timespec="seconds")
        meta = json.dumps({"v": SCHEMA_VERSION, "ts": ts, "event": "rotate", "dropped": dropped},
                          ensure_ascii=False)
        ledger_path.write_text(meta + "\n" + "\n".join(kept) + "\n", encoding="utf-8")
        print(f"🟡 shadow_ledger 輪轉（rotate）：裁掉 {dropped} 行、保留最新 {keep} 行（防無限長大）")
    except Exception:  # noqa: BLE001 — 輪轉失敗不拋、不拖垮主流程
        pass


def read_records(ledger_path: Path) -> list[dict]:
    """讀回 ledger 全部 record。容錯：壞行 skip、檔案不存在回 []（G3b 讀取永不崩）。"""
    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        return []
    out: list[dict] = []
    try:
        for line in ledger_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:  # noqa: BLE001 — 壞行 skip，不崩
                continue
    except Exception:  # noqa: BLE001 — 讀檔失敗回已收集的
        pass
    return out
