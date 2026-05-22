"""Enrichment queue helpers for local-only replay (P92).

The queue may contain raw post content because replay needs the original source
payload. Only the normalized snapshot is safe to write into run_manifest.json.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from analyzer.data_writer import atomic_write_json
from analyzer.source_selection import (
    REASON_DUPLICATE_SIGNATURE,
    REASON_DUPLICATE_URL,
    REASON_LOW_SIGNAL,
    REASON_TOPN_OVERFLOW,
    build_source_id,
)


ENRICHMENT_SCHEMA_VERSION = 1
ENRICHMENT_TRUTH = "raw replay queue; do not commit to repo"
ENRICHMENT_SNAPSHOT_TRUTH = "raw-free enrichment snapshot only"
RETENTION_TRUTH = "raw queue is git-ignored locally and short-retention in GitHub Actions artifacts"

STATUS_NOT_AVAILABLE = "not_available"
STATUS_PENDING = "pending"
STATUS_NO_ELIGIBLE = "no_eligible"
STATUS_DRY_RUN = "dry_run"
STATUS_COMPLETED = "completed"
STATUS_PARTIAL = "partial"
STATUS_SKIPPED_BUDGET = "skipped_budget"
STATUS_FAILED = "failed"

ALLOWED_REPLAY_STATUSES = {
    STATUS_NOT_AVAILABLE,
    STATUS_PENDING,
    STATUS_NO_ELIGIBLE,
    STATUS_DRY_RUN,
    STATUS_COMPLETED,
    STATUS_PARTIAL,
    STATUS_SKIPPED_BUDGET,
    STATUS_FAILED,
}

ELIGIBLE_SELECTION_REASONS = {REASON_TOPN_OVERFLOW}
SKIP_REASON_REPLAY_CAP = "replay_cap_overflow"


def enrichment_queue_path(queue_dir: Path, run_date: str) -> Path:
    return Path(queue_dir) / str(run_date) / "enrichment_queue.json"


def build_enrichment_queue(
    *,
    run_date: str,
    source_hash: str,
    local_only_posts: Iterable[Any],
    local_only_reasons: Iterable[str],
    max_replay_posts: int,
    retention_days: int,
    created_at_utc: Optional[str] = None,
) -> Dict[str, Any]:
    posts = list(local_only_posts or [])
    reasons = list(local_only_reasons or [])
    if len(reasons) < len(posts):
        reasons.extend(["unknown"] * (len(posts) - len(reasons)))
    max_replay_posts = _non_negative_int(max_replay_posts)
    created_at_utc = created_at_utc or (datetime.utcnow().isoformat() + "Z")

    topn_candidates = [
        (index, _score_post(post))
        for index, (post, reason) in enumerate(zip(posts, reasons))
        if reason in ELIGIBLE_SELECTION_REASONS
    ]
    topn_candidates.sort(key=lambda row: row[1], reverse=True)
    eligible_indices = {index for index, _score in topn_candidates[:max_replay_posts]}

    records: List[Dict[str, Any]] = []
    for index, post in enumerate(posts):
        reason = str(reasons[index] or "unknown")
        eligible = index in eligible_indices
        skip_reason = ""
        if not eligible:
            if reason in ELIGIBLE_SELECTION_REASONS:
                skip_reason = SKIP_REASON_REPLAY_CAP
            else:
                skip_reason = _skip_reason_for_selection_reason(reason)
        records.append(
            {
                "source_id": build_source_id(post),
                "reason": reason,
                "eligible": eligible,
                "skip_reason": skip_reason,
                "platform": _text(_get(post, "platform")) or "unknown",
                "score": _score_post(post),
                "raw_post": _post_to_dict(post),
            }
        )

    eligible_count = len([record for record in records if record.get("eligible")])
    skipped_count = max(0, len(records) - eligible_count)
    queue = {
        "schema_version": ENRICHMENT_SCHEMA_VERSION,
        "enrichment_truth": ENRICHMENT_TRUTH,
        "run_date": str(run_date),
        "source_hash": str(source_hash or "unknown"),
        "generated_at_utc": created_at_utc,
        "source_count": len(records),
        "eligible_count": eligible_count,
        "skipped_count": skipped_count,
        "replay_max_posts": max_replay_posts,
        "retention_days": _non_negative_int(retention_days),
        "retention_truth": RETENTION_TRUTH,
        "records": records,
    }
    queue["queue_digest"] = _queue_digest(queue)
    return queue


def write_enrichment_queue(queue_dir: Path, queue: Dict[str, Any]) -> Path:
    run_date = str(queue.get("run_date") or datetime.utcnow().strftime("%Y-%m-%d"))
    path = enrichment_queue_path(Path(queue_dir), run_date)
    atomic_write_json(path, queue)
    return path


def load_enrichment_queue(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def eligible_records(queue: Dict[str, Any], max_items: Optional[int] = None) -> List[Dict[str, Any]]:
    records = queue.get("records", []) if isinstance(queue, dict) else []
    if not isinstance(records, list):
        return []
    selected = [record for record in records if isinstance(record, dict) and bool(record.get("eligible"))]
    if max_items is not None:
        selected = selected[: _non_negative_int(max_items)]
    return selected


def build_enrichment_snapshot(
    queue: Optional[Dict[str, Any]],
    *,
    queue_path: Optional[Path] = None,
    replay_status: str = "",
    enriched_posts: int = 0,
    budget_snapshot: Optional[Dict[str, Any]] = None,
    artifact_retention_days: Optional[int] = None,
) -> Dict[str, Any]:
    if not isinstance(queue, dict):
        return normalize_enrichment_snapshot(
            {
                "schema_version": ENRICHMENT_SCHEMA_VERSION,
                "enrichment_truth": ENRICHMENT_SNAPSHOT_TRUTH,
                "queue_available": False,
                "artifact_retention_days": _non_negative_int(artifact_retention_days),
                "replay_status": STATUS_NOT_AVAILABLE,
            }
        )

    source_count = _non_negative_int(queue.get("source_count", 0))
    eligible_count = _non_negative_int(queue.get("eligible_count", 0))
    skipped_count = _non_negative_int(queue.get("skipped_count", 0))
    if not replay_status:
        replay_status = STATUS_PENDING if eligible_count else STATUS_NO_ELIGIBLE

    skipped_reason_counts: Dict[str, int] = {}
    eligible_reason_counts: Dict[str, int] = {}
    for record in queue.get("records", []) if isinstance(queue.get("records", []), list) else []:
        if not isinstance(record, dict):
            continue
        if record.get("eligible"):
            reason = str(record.get("reason") or "unknown")
            eligible_reason_counts[reason] = eligible_reason_counts.get(reason, 0) + 1
        else:
            reason = str(record.get("skip_reason") or record.get("reason") or "unknown")
            skipped_reason_counts[reason] = skipped_reason_counts.get(reason, 0) + 1

    budget_snapshot = budget_snapshot if isinstance(budget_snapshot, dict) else {}
    snapshot = {
        "schema_version": ENRICHMENT_SCHEMA_VERSION,
        "enrichment_truth": ENRICHMENT_SNAPSHOT_TRUTH,
        "queue_available": True,
        "queue_ref": _display_path(queue_path),
        "queue_digest": str(queue.get("queue_digest") or _queue_digest(queue)),
        "source_count": source_count,
        "eligible_posts": eligible_count,
        "skipped_posts": skipped_count,
        "enriched_posts": _non_negative_int(enriched_posts),
        "artifact_retention_days": _non_negative_int(
            artifact_retention_days if artifact_retention_days is not None else queue.get("retention_days", 0)
        ),
        "replay_status": replay_status if replay_status in ALLOWED_REPLAY_STATUSES else STATUS_NOT_AVAILABLE,
        "eligible_reason_counts": eligible_reason_counts,
        "skipped_reason_counts": skipped_reason_counts,
        "budget_decision": str(budget_snapshot.get("decision", "") or ""),
        "budget_reason": str(budget_snapshot.get("decision_reason", "") or ""),
        "budget_remaining": _non_negative_int(budget_snapshot.get("remaining_llm_calls", 0)),
        "cooldown_active": bool(budget_snapshot.get("cooldown_active", False)),
    }
    return normalize_enrichment_snapshot(snapshot)


def normalize_enrichment_snapshot(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    status = str(value.get("replay_status", STATUS_NOT_AVAILABLE) or STATUS_NOT_AVAILABLE)
    if status not in ALLOWED_REPLAY_STATUSES:
        status = STATUS_NOT_AVAILABLE
    return {
        "schema_version": ENRICHMENT_SCHEMA_VERSION,
        "enrichment_truth": ENRICHMENT_SNAPSHOT_TRUTH,
        "queue_available": bool(value.get("queue_available", False)),
        "queue_ref": str(value.get("queue_ref", "") or ""),
        "queue_digest": str(value.get("queue_digest", "") or ""),
        "source_count": _non_negative_int(value.get("source_count", 0)),
        "eligible_posts": _non_negative_int(value.get("eligible_posts", 0)),
        "skipped_posts": _non_negative_int(value.get("skipped_posts", 0)),
        "enriched_posts": _non_negative_int(value.get("enriched_posts", 0)),
        "artifact_retention_days": _non_negative_int(value.get("artifact_retention_days", 0)),
        "replay_status": status,
        "eligible_reason_counts": _clean_int_map(value.get("eligible_reason_counts", {})),
        "skipped_reason_counts": _clean_int_map(value.get("skipped_reason_counts", {})),
        "budget_decision": str(value.get("budget_decision", "") or ""),
        "budget_reason": str(value.get("budget_reason", "") or ""),
        "budget_remaining": _non_negative_int(value.get("budget_remaining", 0)),
        "cooldown_active": bool(value.get("cooldown_active", False)),
    }


def validate_enrichment_queue(value: Any) -> Tuple[bool, List[str]]:
    if not isinstance(value, dict):
        return False, ["enrichment queue must be object"]
    errors: List[str] = []
    required = {
        "schema_version",
        "enrichment_truth",
        "run_date",
        "source_hash",
        "source_count",
        "eligible_count",
        "skipped_count",
        "retention_days",
        "retention_truth",
        "records",
    }
    for key in sorted(required):
        if key not in value:
            errors.append("queue.%s is required" % key)
    if value.get("schema_version") != ENRICHMENT_SCHEMA_VERSION:
        errors.append("queue.schema_version must be %s" % ENRICHMENT_SCHEMA_VERSION)
    if value.get("enrichment_truth") != ENRICHMENT_TRUTH:
        errors.append("queue.enrichment_truth must declare raw queue")
    records = value.get("records", [])
    if not isinstance(records, list):
        errors.append("queue.records must be list")
        records = []
    source_count = _non_negative_int(value.get("source_count", 0))
    eligible_count = _non_negative_int(value.get("eligible_count", 0))
    skipped_count = _non_negative_int(value.get("skipped_count", 0))
    if source_count != len(records):
        errors.append("queue.source_count must equal records length")
    if eligible_count + skipped_count != source_count:
        errors.append("queue eligible + skipped must equal source_count")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append("queue.records[%s] must be object" % index)
            continue
        if not record.get("source_id"):
            errors.append("queue.records[%s].source_id is required" % index)
        if "raw_post" not in record:
            errors.append("queue.records[%s].raw_post is required" % index)
    return len(errors) == 0, errors


def validate_enrichment_snapshot(value: Any) -> Tuple[bool, List[str]]:
    if value in ({}, None):
        return True, []
    if not isinstance(value, dict):
        return False, ["enrichment must be object"]
    errors: List[str] = []
    normalized = normalize_enrichment_snapshot(value)
    required = {
        "schema_version",
        "enrichment_truth",
        "queue_available",
        "source_count",
        "eligible_posts",
        "skipped_posts",
        "enriched_posts",
        "artifact_retention_days",
        "replay_status",
        "eligible_reason_counts",
        "skipped_reason_counts",
        "budget_remaining",
        "cooldown_active",
    }
    for key in sorted(required):
        if key not in value:
            errors.append("enrichment.%s is required" % key)
    if value.get("schema_version") != ENRICHMENT_SCHEMA_VERSION:
        errors.append("enrichment.schema_version must be %s" % ENRICHMENT_SCHEMA_VERSION)
    if value.get("enrichment_truth") != ENRICHMENT_SNAPSHOT_TRUTH:
        errors.append("enrichment.enrichment_truth must declare raw-free snapshot")
    if not isinstance(value.get("queue_available"), bool):
        errors.append("enrichment.queue_available must be boolean")
    if value.get("replay_status") not in ALLOWED_REPLAY_STATUSES:
        errors.append("enrichment.replay_status must be allowed status")
    for key in ("source_count", "eligible_posts", "skipped_posts", "enriched_posts", "artifact_retention_days", "budget_remaining"):
        if not isinstance(value.get(key), int) or isinstance(value.get(key), bool) or value.get(key) < 0:
            errors.append("enrichment.%s must be non-negative integer" % key)
    if normalized["eligible_posts"] + normalized["skipped_posts"] != normalized["source_count"]:
        errors.append("enrichment eligible + skipped must equal source_count")
    if normalized["enriched_posts"] > normalized["eligible_posts"]:
        errors.append("enrichment.enriched_posts cannot exceed eligible_posts")
    for key in ("eligible_reason_counts", "skipped_reason_counts"):
        if not isinstance(value.get(key), dict):
            errors.append("enrichment.%s must be object" % key)
            continue
        for reason, count in value.get(key, {}).items():
            if not isinstance(reason, str):
                errors.append("enrichment.%s keys must be string" % key)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                errors.append("enrichment.%s values must be non-negative integer" % key)
    if not isinstance(value.get("cooldown_active"), bool):
        errors.append("enrichment.cooldown_active must be boolean")
    return len(errors) == 0, errors


def _skip_reason_for_selection_reason(reason: str) -> str:
    if reason in {REASON_DUPLICATE_URL, REASON_DUPLICATE_SIGNATURE, REASON_LOW_SIGNAL}:
        return reason
    return str(reason or "unknown")


def _queue_digest(queue: Dict[str, Any]) -> str:
    records = queue.get("records", []) if isinstance(queue, dict) else []
    safe_records = []
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict):
                continue
            safe_records.append(
                {
                    "source_id": record.get("source_id", ""),
                    "reason": record.get("reason", ""),
                    "eligible": bool(record.get("eligible", False)),
                    "skip_reason": record.get("skip_reason", ""),
                }
            )
    payload = {
        "schema_version": queue.get("schema_version", ENRICHMENT_SCHEMA_VERSION),
        "run_date": queue.get("run_date", ""),
        "source_hash": queue.get("source_hash", ""),
        "records": safe_records,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _post_to_dict(post: Any) -> Dict[str, Any]:
    if isinstance(post, dict):
        raw = dict(post)
    elif hasattr(post, "to_dict") and callable(getattr(post, "to_dict")):
        raw = post.to_dict()
    elif is_dataclass(post):
        raw = asdict(post)
    else:
        raw = {
            "title": _get(post, "title"),
            "content": _get(post, "content"),
            "url": _get(post, "url"),
            "source": _get(post, "source"),
            "platform": _get(post, "platform"),
            "score": _get(post, "score", 0),
            "region": _get(post, "region", "TW"),
            "published_date": _get(post, "published_date"),
            "detected_heroes": _get(post, "detected_heroes", []),
        }
    return json.loads(json.dumps(raw, ensure_ascii=False, default=str))


def _display_path(path: Optional[Path]) -> str:
    if not path:
        return ""
    parts = list(Path(path).parts)
    if "data" in parts:
        return "/".join(parts[parts.index("data") :])
    return Path(path).name


def _clean_int_map(value: Any) -> Dict[str, int]:
    if not isinstance(value, dict):
        return {}
    clean: Dict[str, int] = {}
    for key, count in value.items():
        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            clean[str(key)] = count
    return clean


def _score_post(post: Any) -> float:
    try:
        return float(_get(post, "score", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _text(value: Any) -> str:
    return str(value or "").strip()


def _get(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _non_negative_int(value: Any) -> int:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    return max(0, number)
