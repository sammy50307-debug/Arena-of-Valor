"""
analyzer/data_writer.py — Phase 56.5 Stage 2 producer 端治本

提供：
  - atomic_write_json：先寫 .tmp 再 os.replace，避免半寫殘檔（R7）
  - validate_summary：依 history-trend-query schema_version.json 檢查契約（R21）
  - coerce_to_schema：補齊缺欄位至最小契約，含安全預設值

契約權威檔：.agent/skills/history-trend-query/resources/schema_version.json
（與 P61 loader 共用同一份契約，避免雙端漂移）
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / ".agent" / "skills" / "history-trend-query" / "resources" / "schema_version.json"
)
_SCHEMA: Dict[str, Any] = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_REQ: Dict[str, List[str]] = _SCHEMA.get("required_fields", {})

_TOP_DEFAULTS: Dict[str, Any] = {
    "total_posts": 0,
    "overall": {"sentiment_score": 0.0, "trend": "Stable"},
    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
    "platform_breakdown": {},
    "hero_stats": {},
}


def validate_summary(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """檢查 data 是否符合契約。回 (is_valid, missing_fields)。"""
    missing: List[str] = []
    for k in _REQ.get("top_level", []):
        if k not in data:
            missing.append(k)
    overall = data.get("overall")
    if isinstance(overall, dict):
        for k in _REQ.get("overall", []):
            if k not in overall:
                missing.append(f"overall.{k}")
    sd = data.get("sentiment_distribution")
    if isinstance(sd, dict):
        for k in _REQ.get("sentiment_distribution", []):
            if k not in sd:
                missing.append(f"sentiment_distribution.{k}")
    return (len(missing) == 0, missing)


def coerce_to_schema(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """補齊缺欄位至契約最小。回 (補齊後 dict, 補了哪些欄位)。"""
    out: Dict[str, Any] = dict(data)
    filled: List[str] = []

    for k, default in _TOP_DEFAULTS.items():
        if k not in out:
            out[k] = dict(default) if isinstance(default, dict) else default
            filled.append(k)

    if isinstance(out.get("overall"), dict):
        for k, v in _TOP_DEFAULTS["overall"].items():
            if k not in out["overall"]:
                out["overall"][k] = v
                filled.append(f"overall.{k}")

    if isinstance(out.get("sentiment_distribution"), dict):
        for k, v in _TOP_DEFAULTS["sentiment_distribution"].items():
            if k not in out["sentiment_distribution"]:
                out["sentiment_distribution"][k] = v
                filled.append(f"sentiment_distribution.{k}")

    return out, filled


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """寫到 path.tmp → fsync → os.replace 為 path。避免半寫殘檔（R7）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        raise


__all__ = ["validate_summary", "coerce_to_schema", "atomic_write_json"]
