"""Skill metrics logger — O1/O2/O3 基礎建設 (P72.0).

Records one JSON line per invocation to ~/.claude/skill_metrics.jsonl:
  {"skill": "...", "ts": "2026-05-14T10:00:00Z", "duration_ms": 123,
   "exit_code": 0, "tokens_in": 0, "tokens_out": 0}

O1: execution duration  →  duration_ms
O2: failure rate        →  exit_code != 0
O3: token consumption   →  tokens_in / tokens_out (placeholder; filled by callers when known)
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

METRICS_FILE = Path.home() / ".claude" / "skill_metrics.jsonl"


def record(
    skill_name: str,
    duration_ms: float,
    exit_code: int,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> None:
    """Append one metrics entry. Silently no-ops on any I/O error."""
    entry: dict[str, Any] = {
        "skill": skill_name,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_ms": round(duration_ms),
        "exit_code": exit_code,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }
    try:
        METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_all(metrics_file: Path | None = None) -> list[dict]:
    """Return all records from the metrics log (newest-first optional)."""
    path = metrics_file or METRICS_FILE
    if not path.exists():
        return []
    records: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def summarize(records: list[dict]) -> dict[str, dict]:
    """Aggregate records by skill → per-skill O1/O2/O3 stats dict."""
    agg: dict[str, dict] = defaultdict(lambda: {
        "calls": 0,
        "failures": 0,
        "total_duration_ms": 0.0,
        "total_tokens_in": 0,
        "total_tokens_out": 0,
    })
    for r in records:
        skill = r.get("skill", "unknown")
        s = agg[skill]
        s["calls"] += 1
        if r.get("exit_code", 0) != 0:
            s["failures"] += 1
        s["total_duration_ms"] += r.get("duration_ms", 0)
        s["total_tokens_in"] += r.get("tokens_in", 0)
        s["total_tokens_out"] += r.get("tokens_out", 0)
    # compute averages
    result: dict[str, dict] = {}
    for skill, s in agg.items():
        calls = s["calls"]
        result[skill] = {
            "calls": calls,
            "failures": s["failures"],
            "failure_rate_pct": round(s["failures"] / calls * 100, 1) if calls else 0.0,
            "avg_duration_ms": round(s["total_duration_ms"] / calls) if calls else 0,
            "total_tokens_in": s["total_tokens_in"],
            "total_tokens_out": s["total_tokens_out"],
            "avg_tokens_in": round(s["total_tokens_in"] / calls) if calls else 0,
            "avg_tokens_out": round(s["total_tokens_out"] / calls) if calls else 0,
        }
    return result
