"""Source selection helpers for LLM cost control.

The selector decides which real source posts should receive LLM deep reading.
Posts not selected are still retained and analyzed by the local deterministic
baseline; this module must never delete or redact raw source files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit


SELECTION_SCHEMA_VERSION = 1
SELECTION_TRUTH = "source selection only; raw sources retained"

REASON_LLM_SELECTED = "llm_selected"
REASON_DUPLICATE_URL = "duplicate_url"
REASON_DUPLICATE_SIGNATURE = "duplicate_signature"
REASON_LOW_SIGNAL = "low_signal_local_only"
REASON_TOPN_OVERFLOW = "topn_overflow"

ALLOWED_SELECTION_REASONS = {
    REASON_LLM_SELECTED,
    REASON_DUPLICATE_URL,
    REASON_DUPLICATE_SIGNATURE,
    REASON_LOW_SIGNAL,
    REASON_TOPN_OVERFLOW,
}


@dataclass
class SourceSelection:
    llm_posts: List[Any]
    local_only_posts: List[Any]
    snapshot: Dict[str, Any]


def build_source_selection(
    posts: Iterable[Any],
    *,
    max_llm_posts: int,
    budget_remaining: Optional[int] = None,
    hero_focus: str = "",
) -> SourceSelection:
    items = list(posts or [])
    cap = _selection_cap(max_llm_posts, budget_remaining)
    reasons_by_index: Dict[int, str] = {}
    candidates: List[Tuple[int, Any, float]] = []
    seen_urls: set = set()
    seen_title_platforms: set = set()
    seen_signatures: List[Tuple[str, str]] = []

    for index, item in enumerate(items):
        url_key = _normalize_url(_get(item, "url"))
        if url_key and url_key in seen_urls:
            reasons_by_index[index] = REASON_DUPLICATE_URL
            continue
        if url_key:
            seen_urls.add(url_key)

        if _is_low_signal(item):
            reasons_by_index[index] = REASON_LOW_SIGNAL
            continue

        platform = _canonical_text(_get(item, "platform")) or "unknown"
        title_key = _signature_text(_get(item, "title"))
        title_platform_key = (platform, title_key)
        if title_key and title_platform_key in seen_title_platforms:
            reasons_by_index[index] = REASON_DUPLICATE_SIGNATURE
            continue
        if title_key:
            seen_title_platforms.add(title_platform_key)

        signature = _post_signature(item)
        if _near_duplicate(platform, signature, seen_signatures):
            reasons_by_index[index] = REASON_DUPLICATE_SIGNATURE
            continue
        if signature:
            seen_signatures.append((platform, signature))

        candidates.append((index, item, _score_item(item, index, hero_focus)))

    selected_indices = _select_diverse_indices(candidates, cap)
    for index, _item, _score in candidates:
        reasons_by_index[index] = REASON_LLM_SELECTED if index in selected_indices else REASON_TOPN_OVERFLOW

    llm_posts: List[Any] = []
    local_only_posts: List[Any] = []
    reason_counts = {reason: 0 for reason in sorted(ALLOWED_SELECTION_REASONS)}
    selected_platform_counts: Dict[str, int] = {}
    local_platform_counts: Dict[str, int] = {}

    for index, item in enumerate(items):
        reason = reasons_by_index.get(index, REASON_TOPN_OVERFLOW)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        platform = _canonical_text(_get(item, "platform")) or "unknown"
        if reason == REASON_LLM_SELECTED:
            llm_posts.append(item)
            selected_platform_counts[platform] = selected_platform_counts.get(platform, 0) + 1
        else:
            local_only_posts.append(item)
            local_platform_counts[platform] = local_platform_counts.get(platform, 0) + 1

    duplicate_posts = reason_counts.get(REASON_DUPLICATE_URL, 0) + reason_counts.get(REASON_DUPLICATE_SIGNATURE, 0)
    snapshot = normalize_selection_snapshot(
        {
            "schema_version": SELECTION_SCHEMA_VERSION,
            "selection_truth": SELECTION_TRUTH,
            "total_input_posts": len(items),
            "unique_posts": max(0, len(items) - duplicate_posts),
            "duplicate_posts": duplicate_posts,
            "llm_selected_posts": len(llm_posts),
            "local_only_posts": len(local_only_posts),
            "max_llm_items": cap,
            "budget_remaining": _non_negative_int(budget_remaining),
            "selection_reasons": sorted([k for k, v in reason_counts.items() if v > 0]),
            "reason_counts": reason_counts,
            "selected_platform_counts": selected_platform_counts,
            "local_only_platform_counts": local_platform_counts,
        }
    )
    return SourceSelection(llm_posts=llm_posts, local_only_posts=local_only_posts, snapshot=snapshot)


def normalize_selection_snapshot(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    reason_counts = _clean_int_map(value.get("reason_counts", {}), allowed_keys=ALLOWED_SELECTION_REASONS)
    for reason in ALLOWED_SELECTION_REASONS:
        reason_counts.setdefault(reason, 0)
    selected_platform_counts = _clean_int_map(value.get("selected_platform_counts", {}))
    local_only_platform_counts = _clean_int_map(value.get("local_only_platform_counts", {}))
    reasons = value.get("selection_reasons", [])
    if not isinstance(reasons, list):
        reasons = []
    clean_reasons = []
    for reason in reasons:
        text = str(reason or "").strip()
        if text in ALLOWED_SELECTION_REASONS and text not in clean_reasons:
            clean_reasons.append(text)

    total_input = _non_negative_int(value.get("total_input_posts", 0))
    duplicate_posts = _non_negative_int(value.get("duplicate_posts", 0))
    local_only = _non_negative_int(value.get("local_only_posts", 0))
    selected = _non_negative_int(value.get("llm_selected_posts", 0))
    unique_posts = value.get("unique_posts")
    if unique_posts is None:
        unique_posts = max(0, total_input - duplicate_posts)

    return {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selection_truth": SELECTION_TRUTH,
        "total_input_posts": total_input,
        "unique_posts": _non_negative_int(unique_posts),
        "duplicate_posts": duplicate_posts,
        "llm_selected_posts": selected,
        "local_only_posts": local_only,
        "max_llm_items": _non_negative_int(value.get("max_llm_items", 0)),
        "budget_remaining": _non_negative_int(value.get("budget_remaining", 0)),
        "selection_reasons": sorted(clean_reasons),
        "reason_counts": reason_counts,
        "selected_platform_counts": selected_platform_counts,
        "local_only_platform_counts": local_only_platform_counts,
    }


def validate_selection_snapshot(value: Any) -> Tuple[bool, List[str]]:
    if value in ({}, None):
        return True, []
    if not isinstance(value, dict):
        return False, ["selection must be object"]
    errors: List[str] = []
    normalized = normalize_selection_snapshot(value)
    required = {
        "schema_version",
        "selection_truth",
        "total_input_posts",
        "unique_posts",
        "duplicate_posts",
        "llm_selected_posts",
        "local_only_posts",
        "max_llm_items",
        "budget_remaining",
        "selection_reasons",
        "reason_counts",
        "selected_platform_counts",
        "local_only_platform_counts",
    }
    for key in sorted(required):
        if key not in value:
            errors.append("selection.%s is required" % key)
    if value.get("schema_version") != SELECTION_SCHEMA_VERSION:
        errors.append("selection.schema_version must be %s" % SELECTION_SCHEMA_VERSION)
    if value.get("selection_truth") != SELECTION_TRUTH:
        errors.append("selection.selection_truth must declare raw sources retained")
    for key in ("total_input_posts", "unique_posts", "duplicate_posts", "llm_selected_posts", "local_only_posts", "max_llm_items", "budget_remaining"):
        if not isinstance(value.get(key), int) or isinstance(value.get(key), bool) or value.get(key) < 0:
            errors.append("selection.%s must be non-negative integer" % key)
    if normalized["duplicate_posts"] > normalized["total_input_posts"]:
        errors.append("selection.duplicate_posts cannot exceed total_input_posts")
    if normalized["unique_posts"] > normalized["total_input_posts"]:
        errors.append("selection.unique_posts cannot exceed total_input_posts")
    if normalized["llm_selected_posts"] > normalized["max_llm_items"]:
        errors.append("selection.llm_selected_posts cannot exceed max_llm_items")
    if normalized["llm_selected_posts"] + normalized["local_only_posts"] != normalized["total_input_posts"]:
        errors.append("selection selected + local_only must equal total_input_posts")
    if not isinstance(value.get("selection_reasons"), list) or any(str(x) not in ALLOWED_SELECTION_REASONS for x in value.get("selection_reasons", [])):
        errors.append("selection.selection_reasons must be allowed reason list")
    for map_key in ("reason_counts", "selected_platform_counts", "local_only_platform_counts"):
        mapping = value.get(map_key)
        if not isinstance(mapping, dict):
            errors.append("selection.%s must be object" % map_key)
            continue
        for key, count in mapping.items():
            if not isinstance(key, str):
                errors.append("selection.%s keys must be string" % map_key)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                errors.append("selection.%s values must be non-negative integer" % map_key)
    return len(errors) == 0, errors


def merge_local_only_entries(analysis_result: Dict[str, Any], local_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge local-only baseline entries into an analyzer result."""
    result = dict(analysis_result or {})
    if not local_entries:
        return result
    result["posts"] = list(result.get("posts", [])) + list(local_entries)
    result["local_analysis_status"] = "ok"
    if result.get("analysis_source") != "local_deterministic":
        result["analysis_source"] = "mixed"
    return result


def _selection_cap(max_llm_posts: int, budget_remaining: Optional[int]) -> int:
    cap = _non_negative_int(max_llm_posts)
    if budget_remaining is not None:
        cap = min(cap, _non_negative_int(budget_remaining))
    return cap


def _select_diverse_indices(candidates: List[Tuple[int, Any, float]], cap: int) -> set:
    if cap <= 0 or not candidates:
        return set()
    ranked = sorted(candidates, key=lambda row: row[2], reverse=True)
    selected: List[int] = []
    selected_set = set()
    seen_platforms = set()

    for index, item, _score in ranked:
        if len(selected) >= cap:
            break
        platform = _canonical_text(_get(item, "platform")) or "unknown"
        if platform in seen_platforms:
            continue
        selected.append(index)
        selected_set.add(index)
        seen_platforms.add(platform)

    for index, _item, _score in ranked:
        if len(selected) >= cap:
            break
        if index in selected_set:
            continue
        selected.append(index)
        selected_set.add(index)

    return selected_set


def _near_duplicate(platform: str, signature: str, existing: List[Tuple[str, str]]) -> bool:
    if not signature:
        return False
    for seen_platform, seen_signature in existing[-100:]:
        if seen_platform != platform:
            continue
        if signature == seen_signature:
            return True
        if min(len(signature), len(seen_signature)) < 24:
            continue
        if SequenceMatcher(None, signature, seen_signature).ratio() >= 0.92:
            return True
    return False


def _post_signature(item: Any) -> str:
    title = _signature_text(_get(item, "title"))
    content = _signature_text(_get(item, "content"))
    return (title + " " + content[:180]).strip()


def _is_low_signal(item: Any) -> bool:
    text = _signature_text("%s %s" % (_get(item, "title"), _get(item, "content")))
    return len(text) < 12


def _score_item(item: Any, index: int, hero_focus: str) -> float:
    score = _safe_float(_get(item, "score"), 0.0)
    title = str(_get(item, "title") or "")
    content = str(_get(item, "content") or "")
    combined = title + " " + content
    hero = str(hero_focus or "").strip()
    if hero and hero in combined:
        score += 0.25
    if len(content) >= 80:
        score += 0.05
    if len(title) >= 8:
        score += 0.03
    score -= index * 0.0001
    return score


def _normalize_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.upper() == "N/A":
        return ""
    try:
        parts = urlsplit(text)
    except ValueError:
        return text.lower().rstrip("/")
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = re.sub(r"/+$", "", parts.path or "/")
    return urlunsplit((scheme, netloc, path, "", "")).lower()


def _signature_text(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _canonical_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower()) or "unknown"


def _get(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _non_negative_int(value: Any) -> int:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    return max(0, number)


def _clean_int_map(value: Any, allowed_keys: Optional[set] = None) -> Dict[str, int]:
    if not isinstance(value, dict):
        return {}
    clean: Dict[str, int] = {}
    for key, count in value.items():
        text = str(key or "").strip()
        if not text:
            continue
        if allowed_keys is not None and text not in allowed_keys:
            continue
        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            clean[text] = count
    return clean
