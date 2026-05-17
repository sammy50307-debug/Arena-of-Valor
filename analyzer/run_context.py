"""Run date and identity helpers for daily pipeline runs (P82)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any, Iterable, Optional


DEFAULT_TIMEZONE_NAME = "Asia/Taipei"
SOURCE_HASH_VERSION = 1


@dataclass(frozen=True)
class RunContext:
    """Normalized run context shared by raw, analysis, report, and manifest paths."""

    run_date: str
    compact_date: str
    display_date: str
    timezone_name: str
    started_at_utc: str
    started_at_local: str


def get_run_timezone(timezone_name: str = DEFAULT_TIMEZONE_NAME) -> tzinfo:
    """Return the configured daily-run timezone.

    Asia/Taipei does not use DST, so a fixed UTC+8 offset is sufficient and
    keeps Python 3.8 CI independent from zoneinfo backports.
    """
    normalized = str(timezone_name or DEFAULT_TIMEZONE_NAME)
    if normalized in {"Asia/Taipei", "Asia/Taiwan", "Taipei"}:
        return timezone(timedelta(hours=8), name="Asia/Taipei")
    if normalized.upper() == "UTC":
        return timezone.utc
    raise ValueError("unsupported run timezone: %s" % normalized)


def build_run_context(
    *,
    now_utc: Optional[datetime] = None,
    timezone_name: str = DEFAULT_TIMEZONE_NAME,
) -> RunContext:
    """Build a stable run context from a UTC instant."""
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    elif now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    run_tz = get_run_timezone(timezone_name)
    local_dt = now_utc.astimezone(run_tz)
    run_date = local_dt.strftime("%Y-%m-%d")
    return RunContext(
        run_date=run_date,
        compact_date=local_dt.strftime("%Y%m%d"),
        display_date=local_dt.strftime("%m/%d"),
        timezone_name=getattr(run_tz, "tzname", lambda _: timezone_name)(local_dt) or timezone_name,
        started_at_utc=now_utc.isoformat().replace("+00:00", "Z"),
        started_at_local=local_dt.isoformat(),
    )


def _stable_source_item(value: Any) -> dict:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, dict):
        value = {"value": str(value)}
    return {
        "url": str(value.get("url", "")),
        "title": str(value.get("title", "")),
        "platform": str(value.get("platform", "")),
        "region": str(value.get("region", "")),
    }


def build_source_hash(items: Iterable[Any], *, hash_version: int = SOURCE_HASH_VERSION) -> str:
    """Build a deterministic source hash without storing raw post content."""
    stable_items = [_stable_source_item(item) for item in items]
    stable_items.sort(key=lambda item: (item["url"], item["title"], item["platform"], item["region"]))
    payload = {
        "hash_version": hash_version,
        "items": stable_items,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_run_id(run_date: str, mode: str, source_hash: str) -> str:
    """Return the manifest run_id contract: date + mode + source hash prefix."""
    normalized_mode = str(mode or "unknown").strip() or "unknown"
    hash_prefix = str(source_hash or "unknown")[:12]
    return "%s-%s-%s" % (run_date, normalized_mode, hash_prefix)
