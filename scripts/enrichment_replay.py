"""Replay P92 enrichment queue for local-only posts."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from analyzer.data_writer import atomic_write_json
from analyzer.enrichment_queue import (
    STATUS_COMPLETED,
    STATUS_DRY_RUN,
    STATUS_FAILED,
    STATUS_NO_ELIGIBLE,
    STATUS_PARTIAL,
    STATUS_SKIPPED_BUDGET,
    build_enrichment_snapshot,
    eligible_records,
    enrichment_queue_path,
    load_enrichment_queue,
    validate_enrichment_queue,
)
from analyzer.fallback_llm_client import FallbackLLMClient
from analyzer.llm_budget import LLMBudgetManager
from analyzer.local_analyzer import analyze_posts_locally
from analyzer.run_context import build_run_context
from analyzer.run_manifest import manifest_path, validate_manifest
from analyzer.sentiment import SentimentAnalyzer
from analyzer.source_selection import build_source_id
from reporter.generator import ReportGenerator
from scrapers.tavily_searcher import SearchResult


def validate_date(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")


def replay_budget_date() -> str:
    return build_run_context(timezone_name=getattr(config, "TIMEZONE", "Asia/Taipei")).run_date


def analysis_path_for(date_str: str) -> Path:
    return config.DATA_DIR / ("analysis_%s.json" % date_str.replace("-", ""))


def raw_path_for(date_str: str) -> Path:
    return config.DATA_DIR / ("raw_%s.json" % date_str.replace("-", ""))


def enriched_posts_path_for(date_str: str) -> Path:
    return config.ENRICHMENT_QUEUE_DIR / date_str / "enriched_posts.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _search_result_from_record(record: Dict[str, Any]) -> SearchResult:
    raw = record.get("raw_post", {})
    if not isinstance(raw, dict):
        raw = {}
    detected = raw.get("detected_heroes", [])
    if not isinstance(detected, list):
        detected = []
    try:
        score = float(raw.get("score", 0.0) or 0.0)
    except (TypeError, ValueError):
        score = 0.0
    return SearchResult(
        title=str(raw.get("title", "") or ""),
        content=str(raw.get("content", "") or ""),
        url=str(raw.get("url", "") or ""),
        source=str(raw.get("source", "") or raw.get("author", "") or ""),
        platform=str(raw.get("platform", "web") or "web"),
        score=score,
        region=str(raw.get("region", "TW") or "TW"),
        published_date=str(raw.get("published_date", "") or ""),
        detected_heroes=[str(x) for x in detected],
    )


def _search_result_from_raw(raw: Dict[str, Any]) -> SearchResult:
    record = {"raw_post": raw}
    return _search_result_from_record(record)


def _count_llm_enriched(entries: List[Dict[str, Any]]) -> int:
    count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        analysis = entry.get("analysis", {})
        if not isinstance(analysis, dict):
            continue
        contract = analysis.get("llm_contract", {})
        if isinstance(contract, dict) and contract.get("status") == "ok":
            count += 1
    return count


def _merge_entries(raw_posts: List[Dict[str, Any]], enriched_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw_results = [_search_result_from_raw(item) for item in raw_posts if isinstance(item, dict)]
    merged = analyze_posts_locally(raw_results, getattr(config, "HERO_WATCHLIST", []))
    enriched_by_id: Dict[str, Dict[str, Any]] = {}
    for entry in enriched_entries:
        post = entry.get("post", {}) if isinstance(entry, dict) else {}
        if isinstance(post, dict):
            enriched_by_id[build_source_id(post)] = entry
    return [enriched_by_id.get(build_source_id(entry.get("post", {})), entry) for entry in merged]


def _write_manifest_enrichment(date_str: str, snapshot: Dict[str, Any]) -> Optional[Path]:
    path = manifest_path(config.DATA_DIR, date_str)
    if not path.exists():
        return None
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("manifest must be object")
    payload["enrichment"] = snapshot
    ok, errors = validate_manifest(payload)
    if not ok:
        raise ValueError("invalid manifest after enrichment replay: %s" % "; ".join(errors))
    atomic_write_json(path, payload)
    return path


async def _analyze(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    posts = [_search_result_from_record(record) for record in records]
    analyzer = SentimentAnalyzer(llm_client=FallbackLLMClient(enable_openai=False))
    result = await analyzer.analyze_posts(posts, showcase=False)
    if isinstance(result, dict):
        entries = result.get("posts", [])
        if not isinstance(entries, list):
            entries = []
        return entries, result
    return [], {"analysis_source": "unknown"}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Replay P92 enrichment queue within the active LLM budget.")
    parser.add_argument("--date", required=True, help="Target report date, format YYYY-MM-DD.")
    parser.add_argument("--queue-path", default="", help="Override enrichment queue JSON path.")
    parser.add_argument("--max-items", type=int, default=None, help="Maximum eligible posts to replay.")
    parser.add_argument("--apply", action="store_true", help="Write enriched_posts.json and update manifest snapshot.")
    parser.add_argument("--write-report", action="store_true", help="With --apply, generate a candidate report from merged entries.")
    args = parser.parse_args(argv)

    date_str = validate_date(args.date)
    queue_path = Path(args.queue_path) if args.queue_path else enrichment_queue_path(config.ENRICHMENT_QUEUE_DIR, date_str)
    if not queue_path.exists():
        print("FAIL: enrichment queue missing: %s" % queue_path)
        return 1

    queue = load_enrichment_queue(queue_path)
    ok, errors = validate_enrichment_queue(queue)
    if not ok:
        print("FAIL: invalid enrichment queue: %s" % "; ".join(errors))
        return 1

    max_items = args.max_items if args.max_items is not None else getattr(config, "ENRICHMENT_REPLAY_MAX_POSTS", 4)
    records = eligible_records(queue, max_items=max_items)
    budget_date = replay_budget_date()
    budget_manager = LLMBudgetManager(
        config.LLM_BUDGET_STATE_FILE,
        max_daily_llm_calls=getattr(config, "LLM_DAILY_BUDGET", 20),
        cooldown_minutes=getattr(config, "LLM_BUDGET_COOLDOWN_MINUTES", 360),
        retention_days=getattr(config, "LLM_BUDGET_RETENTION_DAYS", 14),
    )
    budget_snapshot = budget_manager.snapshot(budget_date)

    if not records:
        snapshot = build_enrichment_snapshot(
            queue,
            queue_path=queue_path,
            replay_status=STATUS_NO_ELIGIBLE,
            budget_snapshot=budget_snapshot,
            artifact_retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
        )
        if args.apply:
            _write_manifest_enrichment(date_str, snapshot)
        print("OK: no eligible enrichment posts; skipped=%s" % snapshot.get("skipped_posts", 0))
        return 0

    if (
        budget_snapshot.get("decision") != "call_llm"
        or bool(budget_snapshot.get("cooldown_active", False))
        or bool(budget_snapshot.get("budget_exhausted", False))
    ):
        snapshot = build_enrichment_snapshot(
            queue,
            queue_path=queue_path,
            replay_status=STATUS_SKIPPED_BUDGET,
            budget_snapshot=budget_snapshot,
            artifact_retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
        )
        if args.apply:
            _write_manifest_enrichment(date_str, snapshot)
        print(
            "OK: budget skip; decision=%s reason=%s"
            % (budget_snapshot.get("decision", ""), budget_snapshot.get("decision_reason", ""))
        )
        return 0

    remaining = int(budget_snapshot.get("remaining_llm_calls", 0) or 0)
    records = records[: max(0, min(len(records), remaining))]
    if not records:
        print("OK: no budget remaining for eligible enrichment posts")
        return 0

    if not args.apply:
        snapshot = build_enrichment_snapshot(
            queue,
            queue_path=queue_path,
            replay_status=STATUS_DRY_RUN,
            budget_snapshot=budget_snapshot,
            artifact_retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
        )
        print(
            "DRY-RUN: eligible=%s will_replay=%s remaining_budget=%s status=%s"
            % (queue.get("eligible_count", 0), len(records), remaining, snapshot["replay_status"])
        )
        return 0

    enriched_entries, analysis_result = asyncio.run(_analyze(records))
    enriched_count = _count_llm_enriched(enriched_entries)
    if enriched_count == len(records) and len(records) == int(queue.get("eligible_count", 0) or 0):
        replay_status = STATUS_COMPLETED
    elif enriched_count > 0:
        replay_status = STATUS_PARTIAL
    else:
        replay_status = STATUS_FAILED
    snapshot = build_enrichment_snapshot(
        queue,
        queue_path=queue_path,
        replay_status=replay_status,
        enriched_posts=enriched_count,
        budget_snapshot=budget_manager.snapshot(budget_date),
        artifact_retention_days=getattr(config, "ENRICHMENT_ARTIFACT_RETENTION_DAYS", 3),
    )

    enriched_payload = {
        "schema_version": 1,
        "run_date": date_str,
        "queue_digest": snapshot.get("queue_digest", ""),
        "replay_status": replay_status,
        "analysis_source": analysis_result.get("analysis_source", ""),
        "enriched_posts": enriched_entries,
    }
    atomic_write_json(enriched_posts_path_for(date_str), enriched_payload)
    manifest_out = _write_manifest_enrichment(date_str, snapshot)

    if args.write_report:
        analysis_path = analysis_path_for(date_str)
        raw_path = raw_path_for(date_str)
        if not analysis_path.exists() or not raw_path.exists():
            print("WARN: skip report; missing analysis or raw file")
        else:
            summary = _load_json(analysis_path)
            raw_posts = _load_json(raw_path)
            if isinstance(summary, dict) and isinstance(raw_posts, list):
                summary.setdefault("_meta", {})
                summary["_meta"]["enrichment"] = snapshot
                summary["_meta"]["replay"] = True
                summary["_meta"]["replay_source"] = "enrichment_queue"
                atomic_write_json(analysis_path, summary)
                merged_entries = _merge_entries(raw_posts, enriched_entries)
                report_path = ReportGenerator().generate(summary, merged_entries, promote=False)
                print("OK: candidate report generated: %s" % report_path)

    print(
        "OK: enrichment replay %s; enriched=%s/%s%s"
        % (
            replay_status,
            enriched_count,
            len(records),
            "; manifest=%s" % manifest_out if manifest_out else "",
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
