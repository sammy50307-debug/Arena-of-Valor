"""Generate debug bundles for replay/health diagnostics (P81.3)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional


def _load_json_if_exists(path: Optional[Path]) -> dict:
    if path is None or (not path.exists()):
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": "%s: %s" % (type(exc).__name__, exc)}


def _serialize_checks(checks: Optional[Iterable[Any]]) -> list[dict]:
    out: list[dict] = []
    if not checks:
        return out
    for check in checks:
        name = getattr(check, "name", "<unknown>")
        status = getattr(check, "status", "<unknown>")
        detail = getattr(check, "detail", "")
        out.append({"name": str(name), "status": str(status), "detail": str(detail)})
    return out


def write_debug_bundle(
    *,
    data_dir: Path,
    repo_root: Path,
    run_date: str,
    status: str,
    error: str,
    analysis_path: Optional[Path],
    raw_path: Optional[Path],
    report_path: Optional[Path],
    manifest_path: Optional[Path],
    health_checks: Optional[Iterable[Any]] = None,
    extra: Optional[dict] = None,
) -> Path:
    """Write a self-contained debug bundle JSON and return output path."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(data_dir) / "debug_bundles" / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / ("debug_bundle_%s.json" % ts)

    checks = _serialize_checks(health_checks)
    bundle = {
        "bundle_version": 1,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "run_date": run_date,
        "status": status,
        "error": error,
        "repo_root": str(repo_root.resolve()),
        "paths": {
            "analysis": str(analysis_path) if analysis_path else "",
            "raw": str(raw_path) if raw_path else "",
            "report": str(report_path) if report_path else "",
            "manifest": str(manifest_path) if manifest_path else "",
        },
        "health": {
            "failed_count": len([c for c in checks if c["status"] == "FAIL"]),
            "checks": checks,
        },
        "manifest": _load_json_if_exists(manifest_path),
        "extra": extra or {},
    }
    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path

