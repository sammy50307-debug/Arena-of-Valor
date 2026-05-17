"""Run manifest helpers (P78 baseline)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from analyzer.data_writer import atomic_write_json
from analyzer.run_context import DEFAULT_TIMEZONE_NAME, SOURCE_HASH_VERSION, build_run_id

MANIFEST_SCHEMA_VERSION = 2
ALLOWED_MODES = {
    "production",
    "showcase",
    "showcase_forced",
    "error_fallback",
    "unknown",
}
ALLOWED_STATUS = {"ok", "failed"}
ALLOWED_GATE_MODES = {"off", "shadow", "blocking"}
ALLOWED_SOURCE_HEALTH_STATUS = {"ok", "degraded", "failed", "unknown"}


def _get_source_field(item: Any, key: str) -> str:
    if isinstance(item, dict):
        value = item.get(key, "")
    else:
        value = getattr(item, key, "")
    return str(value or "").strip()


def _count_values(values: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        key = value.lower().strip() or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_source_quality(search_results: Any) -> Dict[str, Any]:
    """Build a raw-free source health snapshot for manifest/doctor."""
    items = search_results if isinstance(search_results, list) else []
    platforms: List[str] = []
    sources: List[str] = []

    for item in items:
        platform = _get_source_field(item, "platform") or "unknown"
        source = _get_source_field(item, "source") or _get_source_field(item, "author") or platform
        platforms.append(platform)
        sources.append(source)

    platform_counts = _count_values(platforms)
    source_count = len(set([s.lower().strip() or "unknown" for s in sources]))
    platform_count = len(platform_counts)
    total_posts = len(items)
    reasons: List[str] = []

    if total_posts == 0:
        status = "failed"
        reasons.append("no_posts")
    else:
        if platform_count <= 1:
            reasons.append("single_platform")
        if source_count <= 1:
            reasons.append("single_source")
        status = "degraded" if reasons else "ok"

    return {
        "status": status,
        "total_posts": total_posts,
        "platform_count": platform_count,
        "platform_counts": platform_counts,
        "source_count": source_count,
        "reasons": reasons,
    }


def _normalize_source_quality(source_quality: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(source_quality, dict):
        return {
            "status": "unknown",
            "total_posts": 0,
            "platform_count": 0,
            "platform_counts": {},
            "source_count": 0,
            "reasons": [],
        }

    platform_counts = source_quality.get("platform_counts", {})
    if not isinstance(platform_counts, dict):
        platform_counts = {}
    clean_platform_counts: Dict[str, int] = {}
    for key, value in platform_counts.items():
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            clean_platform_counts[str(key)] = value

    status = str(source_quality.get("status", "unknown"))
    if status not in ALLOWED_SOURCE_HEALTH_STATUS:
        status = "unknown"

    reasons = source_quality.get("reasons", [])
    if not isinstance(reasons, list):
        reasons = []

    def _non_negative_int(value: Any) -> int:
        try:
            number = int(value or 0)
        except (TypeError, ValueError):
            number = 0
        return max(0, number)

    return {
        "status": status,
        "total_posts": _non_negative_int(source_quality.get("total_posts", 0)),
        "platform_count": _non_negative_int(source_quality.get("platform_count", 0)),
        "platform_counts": clean_platform_counts,
        "source_count": _non_negative_int(source_quality.get("source_count", 0)),
        "reasons": [str(x) for x in reasons if str(x).strip()],
    }


def _normalize_date_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    normalized: List[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        try:
            normalized.append(datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d"))
        except ValueError:
            continue
    return normalized


def build_manifest(
    *,
    run_date: str,
    mode: str,
    raw_path: Optional[Path],
    analysis_path: Optional[Path],
    report_path: Optional[Path],
    meta: Optional[Dict[str, Any]] = None,
    history_delta: Optional[Dict[str, Any]] = None,
    status: str = "ok",
    error: str = "",
    dry_run: bool = False,
    showcase_flag: bool = False,
    replay_source: str = "",
    is_backfill: bool = False,
    gate_mode: str = "shadow",
    eligibility_reasons: Optional[List[str]] = None,
    source_hash: str = "unknown",
    run_id: str = "",
    timezone_name: str = DEFAULT_TIMEZONE_NAME,
    scheduled_utc: str = "",
    source_quality: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a normalized run manifest payload."""
    meta = meta or {}
    history_delta = history_delta or {}
    pulse = history_delta.get("weekly_vol_pulse", {})
    volumes = pulse.get("volumes", []) if isinstance(pulse, dict) else []
    diagnostics = history_delta.get("diagnostics", {}) if isinstance(history_delta, dict) else {}
    source_dates = _normalize_date_list(diagnostics.get("source_dates", []))
    missing_dates = _normalize_date_list(diagnostics.get("missing_dates", []))

    gate_mode = str(gate_mode or "shadow").lower()
    if gate_mode not in ALLOWED_GATE_MODES:
        gate_mode = "shadow"
    eligibility_reasons = [str(x) for x in (eligibility_reasons or []) if str(x).strip()]
    base_eligible = mode == "production" and status == "ok"
    source_hash = str(source_hash or "unknown")
    run_id = str(run_id or build_run_id(run_date, mode, source_hash))
    timezone_name = str(timezone_name or DEFAULT_TIMEZONE_NAME)
    scheduled_utc = str(scheduled_utc or "")
    source_quality = _normalize_source_quality(source_quality)

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "run_date": run_date,
        "run_date_taipei": run_date,
        "timezone": timezone_name,
        "scheduled_utc": scheduled_utc,
        "run_id": run_id,
        "source_hash": source_hash,
        "source_hash_version": SOURCE_HASH_VERSION,
        "status": status,
        "error": error,
        "mode": mode,
        "publish_eligible": base_eligible and (len(eligibility_reasons) == 0),
        "dry_run": bool(dry_run),
        "showcase_flag": bool(showcase_flag),
        "paths": {
            "raw": str(raw_path) if raw_path else "",
            "analysis": str(analysis_path) if analysis_path else "",
            "report": str(report_path) if report_path else "",
        },
        "metrics": {
            "cache_hit": int(meta.get("cache_hit", 0)),
            "l1_hits": int(meta.get("l1_hits", 0)),
            "l2_hits": int(meta.get("l2_hits", 0)),
            "apify_hits": int(meta.get("apify_hits", 0)),
            "llm_calls": int(meta.get("llm_calls", 0)),
            "total_calls": int(meta.get("total_calls", 0)),
        },
        "history": {
            "status": str(meta.get("history_status", "unknown")),
            "weekly_points": len(volumes),
            "source_dates": source_dates,
            "missing_dates": missing_dates,
        },
        "quality": {
            "source_health": source_quality,
        },
        "replay_source": replay_source,
        "is_backfill": bool(is_backfill),
        "eligibility": {
            "gate_mode": gate_mode,
            "decision": "eligible" if (base_eligible and (len(eligibility_reasons) == 0)) else "ineligible",
            "reasons": eligibility_reasons,
            "blocking_enforced": gate_mode == "blocking",
            "shadow_blocked": gate_mode == "shadow" and len(eligibility_reasons) > 0,
        },
    }


def manifest_path(data_dir: Path, run_date: str) -> Path:
    """Return manifest path under data/runs/YYYY-MM-DD/run_manifest.json."""
    return Path(data_dir) / "runs" / run_date / "run_manifest.json"


def write_manifest(data_dir: Path, manifest: Dict[str, Any]) -> Path:
    """Persist manifest atomically and return its path."""
    ok, errors = validate_manifest(manifest)
    if not ok:
        raise ValueError("invalid run manifest: %s" % "; ".join(errors))
    run_date = manifest.get("run_date", datetime.utcnow().strftime("%Y-%m-%d"))
    out = manifest_path(Path(data_dir), str(run_date))
    atomic_write_json(out, manifest)
    return out


def validate_manifest(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate run manifest contract and return (ok, error_messages)."""
    errors: List[str] = []
    if not isinstance(manifest, dict):
        return False, ["manifest must be an object"]

    required = {
        "schema_version",
        "generated_at",
        "run_date",
        "status",
        "error",
        "mode",
        "publish_eligible",
        "dry_run",
        "showcase_flag",
        "paths",
        "metrics",
        "history",
        "replay_source",
        "is_backfill",
        "eligibility",
    }
    for key in sorted(required):
        if key not in manifest:
            errors.append("missing field: %s" % key)

    schema_version = manifest.get("schema_version")
    if schema_version not in {1, MANIFEST_SCHEMA_VERSION}:
        errors.append("schema_version must be 1 or %s" % MANIFEST_SCHEMA_VERSION)

    run_date = manifest.get("run_date")
    if isinstance(run_date, str):
        try:
            datetime.strptime(run_date, "%Y-%m-%d")
        except ValueError:
            errors.append("run_date must be YYYY-MM-DD")
    else:
        errors.append("run_date must be string")

    if schema_version == MANIFEST_SCHEMA_VERSION:
        for key in ("run_date_taipei", "timezone", "scheduled_utc", "run_id", "source_hash"):
            if key not in manifest:
                errors.append("missing field: %s" % key)
            elif not isinstance(manifest.get(key), str):
                errors.append("%s must be string" % key)
        if manifest.get("run_date_taipei") != manifest.get("run_date"):
            errors.append("run_date_taipei must equal run_date for Asia/Taipei daily runs")
        source_hash_version = manifest.get("source_hash_version")
        if source_hash_version != SOURCE_HASH_VERSION:
            errors.append("source_hash_version must be %s" % SOURCE_HASH_VERSION)
        expected_run_id = build_run_id(str(manifest.get("run_date", "")), str(manifest.get("mode", "")), str(manifest.get("source_hash", "")))
        if manifest.get("run_id") != expected_run_id:
            errors.append("run_id must equal run_date + mode + source_hash prefix")

    status = manifest.get("status")
    if status not in ALLOWED_STATUS:
        errors.append("status must be one of: %s" % ", ".join(sorted(ALLOWED_STATUS)))

    mode = manifest.get("mode")
    if not isinstance(mode, str) or not mode:
        errors.append("mode must be non-empty string")
    elif mode not in ALLOWED_MODES:
        errors.append("mode must be one of: %s" % ", ".join(sorted(ALLOWED_MODES)))

    eligibility = manifest.get("eligibility", {})
    eligibility_reasons = []
    if isinstance(eligibility, dict):
        reasons = eligibility.get("reasons", [])
        if isinstance(reasons, list):
            eligibility_reasons = [r for r in reasons if isinstance(r, str) and r.strip()]

    expected_eligible = mode == "production" and status == "ok" and len(eligibility_reasons) == 0
    if manifest.get("publish_eligible") is not expected_eligible:
        errors.append(
            "publish_eligible must equal (mode == 'production' and status == 'ok' and no eligibility.reasons)"
        )

    for bool_key in ("dry_run", "showcase_flag", "is_backfill"):
        if not isinstance(manifest.get(bool_key), bool):
            errors.append("%s must be boolean" % bool_key)

    if not isinstance(manifest.get("replay_source"), str):
        errors.append("replay_source must be string")

    eligibility = manifest.get("eligibility")
    if not isinstance(eligibility, dict):
        errors.append("eligibility must be object")
    else:
        gate_mode = eligibility.get("gate_mode")
        if gate_mode not in ALLOWED_GATE_MODES:
            errors.append("eligibility.gate_mode must be one of: %s" % ", ".join(sorted(ALLOWED_GATE_MODES)))
        decision = eligibility.get("decision")
        if decision not in {"eligible", "ineligible"}:
            errors.append("eligibility.decision must be 'eligible' or 'ineligible'")
        reasons = eligibility.get("reasons")
        if not isinstance(reasons, list) or any(not isinstance(v, str) for v in reasons):
            errors.append("eligibility.reasons must be string list")
        for key in ("blocking_enforced", "shadow_blocked"):
            if not isinstance(eligibility.get(key), bool):
                errors.append("eligibility.%s must be boolean" % key)

    paths = manifest.get("paths")
    if not isinstance(paths, dict):
        errors.append("paths must be object")
    else:
        for key in ("raw", "analysis", "report"):
            if key not in paths:
                errors.append("paths.%s is required" % key)
            elif not isinstance(paths.get(key), str):
                errors.append("paths.%s must be string" % key)

    metrics = manifest.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be object")
    else:
        for key in ("cache_hit", "l1_hits", "l2_hits", "apify_hits", "llm_calls", "total_calls"):
            value = metrics.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append("metrics.%s must be non-negative integer" % key)

    history = manifest.get("history")
    if not isinstance(history, dict):
        errors.append("history must be object")
    else:
        if not isinstance(history.get("status"), str):
            errors.append("history.status must be string")
        weekly_points = history.get("weekly_points")
        if not isinstance(weekly_points, int) or isinstance(weekly_points, bool) or weekly_points < 0:
            errors.append("history.weekly_points must be non-negative integer")
        for key in ("source_dates", "missing_dates"):
            values = history.get(key, [])
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                errors.append("history.%s must be string list" % key)

    quality = manifest.get("quality")
    if quality is not None:
        if not isinstance(quality, dict):
            errors.append("quality must be object")
        else:
            source_health = quality.get("source_health")
            if not isinstance(source_health, dict):
                errors.append("quality.source_health must be object")
            else:
                health_status = source_health.get("status")
                if health_status not in ALLOWED_SOURCE_HEALTH_STATUS:
                    errors.append(
                        "quality.source_health.status must be one of: %s"
                        % ", ".join(sorted(ALLOWED_SOURCE_HEALTH_STATUS))
                    )
                for int_key in ("total_posts", "platform_count", "source_count"):
                    value = source_health.get(int_key)
                    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                        errors.append("quality.source_health.%s must be non-negative integer" % int_key)
                platform_counts = source_health.get("platform_counts")
                if not isinstance(platform_counts, dict):
                    errors.append("quality.source_health.platform_counts must be object")
                else:
                    for key, value in platform_counts.items():
                        if not isinstance(key, str):
                            errors.append("quality.source_health.platform_counts keys must be string")
                        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                            errors.append("quality.source_health.platform_counts values must be non-negative integer")
                reasons = source_health.get("reasons")
                if not isinstance(reasons, list) or any(not isinstance(v, str) for v in reasons):
                    errors.append("quality.source_health.reasons must be string list")

    return len(errors) == 0, errors
