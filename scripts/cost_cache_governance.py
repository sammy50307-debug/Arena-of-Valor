"""Cost/cache governance checker for P84.5.

This checker reports pipeline cost proxies only. It does not estimate provider
bills and never prints cached LLM result content.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analyzer.run_context import build_run_context


RUNBOOK_PATH = "docs/OPERATIONS_RUNBOOK.md"
REPORT_META_RE = re.compile(
    r"cache_hit:\s*(\d+)\s*/\s*(\d+)\s*\((\d+)%\)\s*\|\s*llm_calls:\s*(\d+)\s*\|\s*mode:\s*([^|<]+)"
)

SEV_BLOCKING = "BLOCKING"
SEV_DEGRADED = "DEGRADED"
SEV_ADVISORY = "ADVISORY"

ISSUE_CATALOG = {
    "metrics_source_missing": {"code": "CCG001", "name": "metrics source missing"},
    "metrics_invalid": {"code": "CCG002", "name": "metrics invariant"},
    "cache_hit_low": {"code": "CCG003", "name": "cache hit rate low"},
    "cache_store_stats": {"code": "CCG004", "name": "cache store stats"},
    "llm_call_budget": {"code": "CCG005", "name": "llm call budget"},
    "budget_cooldown": {"code": "CCG006", "name": "budget cooldown"},
    "selection_throttle": {"code": "CCG007", "name": "selection throttle"},
    "enrichment_replay": {"code": "CCG008", "name": "enrichment replay"},
}


@dataclass
class DailyCostCacheMetric:
    date: str
    source: str
    mode: str
    manifest_present: bool
    report_metadata_present: bool
    cache_hit: int
    total_calls: int
    llm_calls: int
    l1_hits: int = 0
    l2_hits: int = 0
    apify_hits: int = 0
    cache_hit_rate_pct: int = 0
    budget_decision: str = ""
    budget_reason: str = ""
    budget_cooldown_active: bool = False
    budget_llm_calls_used: int = 0
    selection_total_input_posts: int = 0
    selection_llm_selected_posts: int = 0
    selection_local_only_posts: int = 0
    selection_duplicate_posts: int = 0
    selection_max_llm_items: int = 0
    enrichment_queue_available: bool = False
    enrichment_eligible_posts: int = 0
    enrichment_skipped_posts: int = 0
    enrichment_enriched_posts: int = 0
    enrichment_replay_status: str = ""


@dataclass
class CacheStoreSummary:
    path: str
    exists: bool
    schema_version: int
    entry_count: int
    size_bytes: int
    total_l1_hits: int
    total_l2_hits: int
    total_apify_hits: int
    total_misses: int
    total_hits: int
    observed_hit_rate_pct: int


@dataclass
class CostCacheIssue:
    code: str
    severity: str
    name: str
    detail: str
    runbook: str


@dataclass
class CostCacheResult:
    date: str
    window_days: int
    min_cache_hit_rate_pct: int
    max_llm_calls: int
    total_cache_hit: int
    total_calls: int
    total_llm_calls: int
    aggregate_cache_hit_rate_pct: int
    billing_truth: str
    days: List[DailyCostCacheMetric]
    cache_store: CacheStoreSummary
    issues: List[CostCacheIssue]

    @property
    def blocking_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_BLOCKING])

    @property
    def degraded_count(self) -> int:
        return len([x for x in self.issues if x.severity == SEV_DEGRADED])


def taipei_today() -> str:
    return build_run_context().run_date


def _runbook_link(code: str) -> str:
    return "%s#%s" % (RUNBOOK_PATH, code.lower())


def _issue(key: str, severity: str, detail: str) -> CostCacheIssue:
    entry = ISSUE_CATALOG[key]
    return CostCacheIssue(
        code=entry["code"],
        severity=severity,
        name=entry["name"],
        detail=detail,
        runbook=_runbook_link(entry["code"]),
    )


def _date_window(end_date: str, window_days: int) -> List[str]:
    if window_days < 1:
        raise ValueError("window_days must be >= 1")
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("date must use YYYY-MM-DD format")
    start = end - timedelta(days=window_days - 1)
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(window_days)]


def _pct(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return int(round((numerator / denominator) * 100))


def _int_metric(metrics: Dict[str, object], key: str) -> int:
    value = metrics.get(key, 0)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("metrics.%s must be non-negative integer" % key)
    return value


def _safe_non_negative_int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _manifest_metric(repo_root: Path, date_str: str) -> Tuple[Optional[DailyCostCacheMetric], Optional[str]]:
    path = repo_root / "data" / "runs" / date_str / "run_manifest.json"
    if not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics = payload.get("metrics", {})
        if not isinstance(metrics, dict):
            return None, "metrics must be object in %s" % path
        cache_hit = _int_metric(metrics, "cache_hit")
        total_calls = _int_metric(metrics, "total_calls")
        llm_calls = _int_metric(metrics, "llm_calls")
        l1_hits = _int_metric(metrics, "l1_hits")
        l2_hits = _int_metric(metrics, "l2_hits")
        apify_hits = _int_metric(metrics, "apify_hits")
        budget = payload.get("budget", {})
        budget_decision = ""
        budget_reason = ""
        budget_cooldown_active = False
        budget_llm_calls_used = 0
        if isinstance(budget, dict):
            budget_decision = str(budget.get("decision", "") or "")
            budget_reason = str(budget.get("decision_reason", "") or "")
            budget_cooldown_active = bool(budget.get("cooldown_active", False))
            used = budget.get("llm_calls_used", 0)
            budget_llm_calls_used = used if isinstance(used, int) and not isinstance(used, bool) and used >= 0 else 0
        selection = payload.get("selection", {})
        selection_total_input_posts = 0
        selection_llm_selected_posts = 0
        selection_local_only_posts = 0
        selection_duplicate_posts = 0
        selection_max_llm_items = 0
        if isinstance(selection, dict):
            selection_total_input_posts = _safe_non_negative_int(selection.get("total_input_posts", 0))
            selection_llm_selected_posts = _safe_non_negative_int(selection.get("llm_selected_posts", 0))
            selection_local_only_posts = _safe_non_negative_int(selection.get("local_only_posts", 0))
            selection_duplicate_posts = _safe_non_negative_int(selection.get("duplicate_posts", 0))
            selection_max_llm_items = _safe_non_negative_int(selection.get("max_llm_items", 0))
        enrichment = payload.get("enrichment", {})
        enrichment_queue_available = False
        enrichment_eligible_posts = 0
        enrichment_skipped_posts = 0
        enrichment_enriched_posts = 0
        enrichment_replay_status = ""
        if isinstance(enrichment, dict):
            enrichment_queue_available = bool(enrichment.get("queue_available", False))
            enrichment_eligible_posts = _safe_non_negative_int(enrichment.get("eligible_posts", 0))
            enrichment_skipped_posts = _safe_non_negative_int(enrichment.get("skipped_posts", 0))
            enrichment_enriched_posts = _safe_non_negative_int(enrichment.get("enriched_posts", 0))
            enrichment_replay_status = str(enrichment.get("replay_status", "") or "")
    except Exception as exc:
        return None, "%s: %s" % (path, exc)
    return (
        DailyCostCacheMetric(
            date=date_str,
            source="manifest",
            mode=str(payload.get("mode", "unknown")),
            manifest_present=True,
            report_metadata_present=False,
            cache_hit=cache_hit,
            total_calls=total_calls,
            llm_calls=llm_calls,
            l1_hits=l1_hits,
            l2_hits=l2_hits,
            apify_hits=apify_hits,
            cache_hit_rate_pct=_pct(cache_hit, total_calls),
            budget_decision=budget_decision,
            budget_reason=budget_reason,
            budget_cooldown_active=budget_cooldown_active,
            budget_llm_calls_used=budget_llm_calls_used,
            selection_total_input_posts=selection_total_input_posts,
            selection_llm_selected_posts=selection_llm_selected_posts,
            selection_local_only_posts=selection_local_only_posts,
            selection_duplicate_posts=selection_duplicate_posts,
            selection_max_llm_items=selection_max_llm_items,
            enrichment_queue_available=enrichment_queue_available,
            enrichment_eligible_posts=enrichment_eligible_posts,
            enrichment_skipped_posts=enrichment_skipped_posts,
            enrichment_enriched_posts=enrichment_enriched_posts,
            enrichment_replay_status=enrichment_replay_status,
        ),
        None,
    )


def _report_metric(repo_root: Path, date_str: str) -> Tuple[Optional[DailyCostCacheMetric], Optional[str]]:
    path = repo_root / "data" / "reports" / ("aov_report_%s.html" % date_str)
    if not path.exists():
        return None, None
    try:
        prefix = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:5])
        match = REPORT_META_RE.search(prefix)
        if not match:
            return None, "report metadata missing or invalid in %s" % path
        cache_hit = int(match.group(1))
        total_calls = int(match.group(2))
        llm_calls = int(match.group(4))
        mode = match.group(5).strip()
    except Exception as exc:
        return None, "%s: %s" % (path, exc)
    return (
        DailyCostCacheMetric(
            date=date_str,
            source="report_metadata",
            mode=mode,
            manifest_present=False,
            report_metadata_present=True,
            cache_hit=cache_hit,
            total_calls=total_calls,
            llm_calls=llm_calls,
            cache_hit_rate_pct=_pct(cache_hit, total_calls),
        ),
        None,
    )


def _validate_day_metric(metric: DailyCostCacheMetric) -> Optional[str]:
    if metric.total_calls == 0 and (metric.cache_hit > 0 or metric.llm_calls > 0):
        return "%s total_calls=0 but cache_hit=%s llm_calls=%s" % (
            metric.date,
            metric.cache_hit,
            metric.llm_calls,
        )
    if metric.cache_hit > metric.total_calls:
        return "%s cache_hit=%s exceeds total_calls=%s" % (metric.date, metric.cache_hit, metric.total_calls)
    if metric.llm_calls > metric.total_calls:
        return "%s llm_calls=%s exceeds total_calls=%s" % (metric.date, metric.llm_calls, metric.total_calls)
    return None


def _cache_store_summary(repo_root: Path, issues: List[CostCacheIssue]) -> CacheStoreSummary:
    path = repo_root / "data" / "llm_cache.json"
    if not path.exists():
        issues.append(_issue("cache_store_stats", SEV_ADVISORY, "data/llm_cache.json missing"))
        return CacheStoreSummary(str(path), False, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    size = path.stat().st_size
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(_issue("cache_store_stats", SEV_DEGRADED, "%s is not valid json: %s" % (path, exc)))
        return CacheStoreSummary(str(path), True, 0, 0, size, 0, 0, 0, 0, 0, 0)

    entries = payload.get("entries", {})
    stats = payload.get("stats", {})
    if not isinstance(entries, dict):
        issues.append(_issue("cache_store_stats", SEV_DEGRADED, "cache entries must be object"))
        entries = {}
    if not isinstance(stats, dict):
        issues.append(_issue("cache_store_stats", SEV_DEGRADED, "cache stats must be object"))
        stats = {}

    def stat_int(key: str) -> int:
        value = stats.get(key, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            issues.append(_issue("cache_store_stats", SEV_DEGRADED, "cache stats.%s must be non-negative integer" % key))
            return 0
        return value

    total_l1 = stat_int("total_l1_hits")
    total_l2 = stat_int("total_l2_hits")
    total_apify = stat_int("total_apify_hits")
    total_misses = stat_int("total_misses")
    total_hits = total_l1 + total_l2 + total_apify
    return CacheStoreSummary(
        path=str(path),
        exists=True,
        schema_version=int(payload.get("schema_version", 0) or 0),
        entry_count=len(entries),
        size_bytes=size,
        total_l1_hits=total_l1,
        total_l2_hits=total_l2,
        total_apify_hits=total_apify,
        total_misses=total_misses,
        total_hits=total_hits,
        observed_hit_rate_pct=_pct(total_hits, total_hits + total_misses),
    )


def evaluate_cost_cache(
    repo_root: Path,
    date_str: str,
    window_days: int = 7,
    min_cache_hit_rate_pct: int = 20,
    max_llm_calls: int = 20,
) -> CostCacheResult:
    repo_root = Path(repo_root).resolve()
    dates = _date_window(date_str, window_days)
    issues: List[CostCacheIssue] = []
    days: List[DailyCostCacheMetric] = []

    for current in dates:
        metric, error = _manifest_metric(repo_root, current)
        if metric is None:
            fallback, fallback_error = _report_metric(repo_root, current)
            metric = fallback
            error = error or fallback_error
        if error:
            issues.append(_issue("metrics_invalid", SEV_BLOCKING, error))
        if metric is not None:
            validation_error = _validate_day_metric(metric)
            if validation_error:
                issues.append(_issue("metrics_invalid", SEV_BLOCKING, validation_error))
            days.append(metric)

    if not days:
        issues.append(
            _issue(
                "metrics_source_missing",
                SEV_BLOCKING,
                "no manifest metrics or report metadata found in window=%s" % ",".join(dates),
            )
        )

    cache_store = _cache_store_summary(repo_root, issues)
    total_cache_hit = sum(day.cache_hit for day in days)
    total_calls = sum(day.total_calls for day in days)
    total_llm_calls = sum(day.llm_calls for day in days)
    aggregate_hit_rate = _pct(total_cache_hit, total_calls)

    if total_calls > 0 and aggregate_hit_rate < min_cache_hit_rate_pct and total_llm_calls > 0:
        issues.append(
            _issue(
                "cache_hit_low",
                SEV_ADVISORY,
                "aggregate_cache_hit_rate_pct=%s threshold=%s total_calls=%s"
                % (aggregate_hit_rate, min_cache_hit_rate_pct, total_calls),
            )
        )

    if total_llm_calls > max_llm_calls:
        issues.append(
            _issue(
                "llm_call_budget",
                SEV_DEGRADED,
                "total_llm_calls=%s threshold=%s" % (total_llm_calls, max_llm_calls),
            )
        )

    cooldown_days = [
        day
        for day in days
        if day.budget_decision == "skip_llm" or day.budget_cooldown_active or day.budget_reason in {"cooldown_active", "budget_exhausted", "budget_state_malformed"}
    ]
    if cooldown_days:
        issues.append(
            _issue(
                "budget_cooldown",
                SEV_ADVISORY,
                "budget_skip_days=%s reasons=%s"
                % (
                    ",".join(day.date for day in cooldown_days),
                    ",".join(sorted({day.budget_reason or "unknown" for day in cooldown_days})),
                ),
            )
        )

    selection_over_cap = [
        day
        for day in days
        if day.selection_total_input_posts > 0
        and day.selection_max_llm_items >= 0
        and day.selection_llm_selected_posts > day.selection_max_llm_items
    ]
    if selection_over_cap:
        issues.append(
            _issue(
                "selection_throttle",
                SEV_DEGRADED,
                "selected_over_cap_days=%s"
                % ",".join("%s:%s>%s" % (day.date, day.selection_llm_selected_posts, day.selection_max_llm_items) for day in selection_over_cap),
            )
        )
    else:
        throttled_days = [
            day
            for day in days
            if day.selection_total_input_posts > 0
            and (day.selection_local_only_posts > 0 or day.selection_duplicate_posts > 0)
        ]
        if throttled_days:
            issues.append(
                _issue(
                    "selection_throttle",
                    SEV_ADVISORY,
                    "selection_days=%s"
                    % ",".join(
                        "%s:selected=%s local_only=%s duplicate=%s cap=%s"
                        % (
                            day.date,
                            day.selection_llm_selected_posts,
                            day.selection_local_only_posts,
                            day.selection_duplicate_posts,
                            day.selection_max_llm_items,
                        )
                        for day in throttled_days
                    ),
                )
            )

    enrichment_failed = [
        day
        for day in days
        if day.enrichment_replay_status == "failed"
    ]
    if enrichment_failed:
        issues.append(
            _issue(
                "enrichment_replay",
                SEV_DEGRADED,
                "enrichment_failed_days=%s" % ",".join(day.date for day in enrichment_failed),
            )
        )
    else:
        enrichment_pending = [
            day
            for day in days
            if day.enrichment_queue_available
            and day.enrichment_replay_status in {"pending", "skipped_budget", "partial", "no_eligible"}
        ]
        if enrichment_pending:
            issues.append(
                _issue(
                    "enrichment_replay",
                    SEV_ADVISORY,
                    "enrichment_days=%s"
                    % ",".join(
                        "%s:status=%s eligible=%s skipped=%s enriched=%s"
                        % (
                            day.date,
                            day.enrichment_replay_status,
                            day.enrichment_eligible_posts,
                            day.enrichment_skipped_posts,
                            day.enrichment_enriched_posts,
                        )
                        for day in enrichment_pending
                    ),
                )
            )

    return CostCacheResult(
        date=date_str,
        window_days=window_days,
        min_cache_hit_rate_pct=min_cache_hit_rate_pct,
        max_llm_calls=max_llm_calls,
        total_cache_hit=total_cache_hit,
        total_calls=total_calls,
        total_llm_calls=total_llm_calls,
        aggregate_cache_hit_rate_pct=aggregate_hit_rate,
        billing_truth="pipeline proxy only; not provider billing truth",
        days=days,
        cache_store=cache_store,
        issues=issues,
    )


def result_to_dict(result: CostCacheResult) -> Dict[str, object]:
    return {
        "date": result.date,
        "window_days": result.window_days,
        "min_cache_hit_rate_pct": result.min_cache_hit_rate_pct,
        "max_llm_calls": result.max_llm_calls,
        "total_cache_hit": result.total_cache_hit,
        "total_calls": result.total_calls,
        "total_llm_calls": result.total_llm_calls,
        "aggregate_cache_hit_rate_pct": result.aggregate_cache_hit_rate_pct,
        "billing_truth": result.billing_truth,
        "days": [asdict(day) for day in result.days],
        "cache_store": asdict(result.cache_store),
        "issues": [asdict(issue) for issue in result.issues],
    }


def print_result(result: CostCacheResult) -> None:
    print("Cost/cache governance")
    print("date: %s" % result.date)
    print("window_days: %s" % result.window_days)
    print("billing_truth: %s" % result.billing_truth)
    print("")
    print("| severity | code | check | detail | runbook |")
    print("|---|---|---|---|---|")
    if not result.issues:
        print("| OK | CCG000 | summary | cost/cache governance verified | %s#ccg000 |" % RUNBOOK_PATH)
    for issue in result.issues:
        print(
            "| %s | %s | %s | %s | %s |"
            % (
                issue.severity,
                issue.code,
                issue.name,
                issue.detail.replace("|", "/"),
                issue.runbook,
            )
        )

    print("")
    print("| metric | value |")
    print("|---|---:|")
    print("| total_cache_hit | %s |" % result.total_cache_hit)
    print("| total_calls | %s |" % result.total_calls)
    print("| total_llm_calls | %s |" % result.total_llm_calls)
    print("| aggregate_cache_hit_rate_pct | %s |" % result.aggregate_cache_hit_rate_pct)
    print("| cache_entry_count | %s |" % result.cache_store.entry_count)
    print("| cache_observed_hit_rate_pct | %s |" % result.cache_store.observed_hit_rate_pct)

    print("")
    print("| date | source | mode | cache_hit | total_calls | llm_calls | hit_rate_pct | selected | local_only | duplicate | enrichment | budget_decision | budget_reason |")
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
    for day in result.days:
        print(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                day.date,
                day.source,
                day.mode,
                day.cache_hit,
                day.total_calls,
                day.llm_calls,
                day.cache_hit_rate_pct,
                day.selection_llm_selected_posts,
                day.selection_local_only_posts,
                day.selection_duplicate_posts,
                day.enrichment_replay_status or "-",
                day.budget_decision or "-",
                day.budget_reason or "-",
            )
        )


def exit_code_for(result: CostCacheResult) -> int:
    return 1 if (result.blocking_count > 0 or result.degraded_count > 0) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check cost/cache governance metrics.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--date", default=taipei_today(), help="Window end date YYYY-MM-DD.")
    parser.add_argument("--window-days", type=int, default=7, help="Window length. Default: 7.")
    parser.add_argument(
        "--min-cache-hit-rate-pct",
        type=int,
        default=20,
        help="Advisory threshold for aggregate cache hit rate. Default: 20.",
    )
    parser.add_argument(
        "--max-llm-calls",
        type=int,
        default=20,
        help="Degraded threshold for total LLM calls in the window. Default: 20.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = evaluate_cost_cache(
            Path(args.repo_root),
            args.date,
            window_days=args.window_days,
            min_cache_hit_rate_pct=args.min_cache_hit_rate_pct,
            max_llm_calls=args.max_llm_calls,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2
    if args.json:
        print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    else:
        print_result(result)
    return exit_code_for(result)


if __name__ == "__main__":
    sys.exit(main())
