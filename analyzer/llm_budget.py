"""Raw-free LLM budget ledger and cooldown helper (P90)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from analyzer.data_writer import atomic_write_json


SCHEMA_VERSION = 1
BILLING_TRUTH = "pipeline proxy only; not provider billing truth"
DEFAULT_RETENTION_DAYS = 14

REASON_AVAILABLE = "budget_available"
REASON_BUDGET_EXHAUSTED = "budget_exhausted"
REASON_COOLDOWN_ACTIVE = "cooldown_active"
REASON_QUOTA_ERROR = "quota_error"
REASON_STATE_MALFORMED = "budget_state_malformed"
REASON_STATE_WRITE_FAILED = "budget_state_write_failed"

ALLOWED_REASON_CODES = {
    "",
    REASON_AVAILABLE,
    REASON_BUDGET_EXHAUSTED,
    REASON_COOLDOWN_ACTIVE,
    REASON_QUOTA_ERROR,
    REASON_STATE_MALFORMED,
    REASON_STATE_WRITE_FAILED,
}
ALLOWED_DECISIONS = {"call_llm", "skip_llm"}


@dataclass(frozen=True)
class BudgetDecision:
    date: str
    should_call_llm: bool
    decision: str
    reason: str
    snapshot: Dict[str, Any]


class LLMBudgetSkip(RuntimeError):
    """Raised when the local budget ledger decides to skip provider calls."""

    def __init__(self, decision: BudgetDecision):
        self.decision = decision
        super().__init__("%s: %s" % (decision.decision, decision.reason))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    return max(0, number)


def _clean_reason(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text in ALLOWED_REASON_CODES else default


def _new_state(retention_days: int) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "billing_truth": BILLING_TRUTH,
        "updated_at_utc": "",
        "retention_days": max(1, int(retention_days or DEFAULT_RETENTION_DAYS)),
        "days": {},
    }


def _new_day(run_date: str, max_daily_llm_calls: int) -> Dict[str, Any]:
    return {
        "date": run_date,
        "max_daily_llm_calls": max(0, int(max_daily_llm_calls)),
        "llm_calls_used": 0,
        "cooldown_active": False,
        "cooldown_reason": "",
        "cooldown_until_utc": "",
        "quota_error_count": 0,
        "last_quota_error_at_utc": "",
        "budget_exhausted": False,
    }


def _validate_state(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("budget state must be object")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("budget schema_version must be %s" % SCHEMA_VERSION)
    days = raw.get("days")
    if not isinstance(days, dict):
        raise ValueError("budget days must be object")
    state = _new_state(_non_negative_int(raw.get("retention_days", DEFAULT_RETENTION_DAYS)) or DEFAULT_RETENTION_DAYS)
    state["updated_at_utc"] = str(raw.get("updated_at_utc", ""))
    for date_key, day in days.items():
        if not isinstance(date_key, str) or not isinstance(day, dict):
            continue
        clean = _new_day(date_key, _non_negative_int(day.get("max_daily_llm_calls", 0)))
        clean["llm_calls_used"] = _non_negative_int(day.get("llm_calls_used", 0))
        clean["cooldown_reason"] = _clean_reason(day.get("cooldown_reason", ""))
        clean["cooldown_until_utc"] = str(day.get("cooldown_until_utc", "") or "")
        clean["quota_error_count"] = _non_negative_int(day.get("quota_error_count", 0))
        clean["last_quota_error_at_utc"] = str(day.get("last_quota_error_at_utc", "") or "")
        clean["budget_exhausted"] = bool(day.get("budget_exhausted", False))
        clean["cooldown_active"] = bool(day.get("cooldown_active", False))
        state["days"][date_key] = clean
    return state


def _load_state(path: Path, retention_days: int) -> Tuple[Dict[str, Any], str]:
    if not path.exists():
        return _new_state(retention_days), ""
    try:
        import json

        raw = json.loads(path.read_text(encoding="utf-8"))
        return _validate_state(raw), ""
    except Exception as exc:
        return _new_state(retention_days), "%s: %s" % (type(exc).__name__, exc)


def _ensure_day(state: Dict[str, Any], run_date: str, max_daily_llm_calls: int) -> Dict[str, Any]:
    days = state.setdefault("days", {})
    day = days.get(run_date)
    if not isinstance(day, dict):
        day = _new_day(run_date, max_daily_llm_calls)
        days[run_date] = day
    day["date"] = run_date
    day["max_daily_llm_calls"] = max(0, int(max_daily_llm_calls))
    return day


def _prune_days(state: Dict[str, Any], run_date: str, retention_days: int) -> None:
    days = state.get("days", {})
    if not isinstance(days, dict):
        state["days"] = {}
        return
    try:
        end = datetime.strptime(run_date, "%Y-%m-%d")
    except ValueError:
        return
    start = end - timedelta(days=max(1, retention_days) - 1)
    for key in list(days.keys()):
        try:
            current = datetime.strptime(key, "%Y-%m-%d")
        except ValueError:
            del days[key]
            continue
        if current < start:
            del days[key]


def build_budget_snapshot(
    day: Dict[str, Any],
    *,
    decision: str,
    decision_reason: str,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now or utc_now()
    cooldown_until = str(day.get("cooldown_until_utc", "") or "")
    parsed_until = _parse_utc(cooldown_until)
    cooldown_active = bool(parsed_until and parsed_until > now)
    max_calls = _non_negative_int(day.get("max_daily_llm_calls", 0))
    used = _non_negative_int(day.get("llm_calls_used", 0))
    budget_exhausted = used >= max_calls if max_calls >= 0 else False
    return {
        "schema_version": SCHEMA_VERSION,
        "billing_truth": BILLING_TRUTH,
        "date": str(day.get("date", "")),
        "max_daily_llm_calls": max_calls,
        "llm_calls_used": used,
        "remaining_llm_calls": max(0, max_calls - used),
        "cooldown_active": cooldown_active,
        "cooldown_reason": _clean_reason(day.get("cooldown_reason", "")),
        "cooldown_until_utc": cooldown_until,
        "quota_error_count": _non_negative_int(day.get("quota_error_count", 0)),
        "last_quota_error_at_utc": str(day.get("last_quota_error_at_utc", "") or ""),
        "budget_exhausted": budget_exhausted,
        "decision": decision if decision in ALLOWED_DECISIONS else "skip_llm",
        "decision_reason": _clean_reason(decision_reason, REASON_STATE_MALFORMED),
    }


def normalize_budget_snapshot(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    day = _new_day(str(value.get("date", "")), _non_negative_int(value.get("max_daily_llm_calls", 0)))
    day["llm_calls_used"] = _non_negative_int(value.get("llm_calls_used", 0))
    day["cooldown_reason"] = _clean_reason(value.get("cooldown_reason", ""))
    day["cooldown_until_utc"] = str(value.get("cooldown_until_utc", "") or "")
    day["quota_error_count"] = _non_negative_int(value.get("quota_error_count", 0))
    day["last_quota_error_at_utc"] = str(value.get("last_quota_error_at_utc", "") or "")
    decision = str(value.get("decision", "") or "")
    if decision not in ALLOWED_DECISIONS:
        decision = "skip_llm"
    return build_budget_snapshot(
        day,
        decision=decision,
        decision_reason=_clean_reason(value.get("decision_reason", ""), REASON_STATE_MALFORMED),
    )


def validate_budget_snapshot(value: Any) -> Tuple[bool, list[str]]:
    if value in ({}, None):
        return True, []
    if not isinstance(value, dict):
        return False, ["budget must be object"]
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("budget.schema_version must be %s" % SCHEMA_VERSION)
    if value.get("billing_truth") != BILLING_TRUTH:
        errors.append("budget.billing_truth must be pipeline proxy only")
    for key in ("date", "cooldown_reason", "cooldown_until_utc", "last_quota_error_at_utc", "decision", "decision_reason"):
        if key not in value:
            errors.append("budget.%s is required" % key)
        elif not isinstance(value.get(key), str):
            errors.append("budget.%s must be string" % key)
    for key in ("max_daily_llm_calls", "llm_calls_used", "remaining_llm_calls", "quota_error_count"):
        if not isinstance(value.get(key), int) or isinstance(value.get(key), bool) or value.get(key) < 0:
            errors.append("budget.%s must be non-negative integer" % key)
    for key in ("cooldown_active", "budget_exhausted"):
        if not isinstance(value.get(key), bool):
            errors.append("budget.%s must be boolean" % key)
    if value.get("decision") not in ALLOWED_DECISIONS:
        errors.append("budget.decision must be one of: %s" % ", ".join(sorted(ALLOWED_DECISIONS)))
    for key in ("cooldown_reason", "decision_reason"):
        if value.get(key) not in ALLOWED_REASON_CODES:
            errors.append("budget.%s must be an allowed reason code" % key)
    return len(errors) == 0, errors


class LLMBudgetManager:
    def __init__(
        self,
        state_path: Path,
        *,
        max_daily_llm_calls: int,
        cooldown_minutes: int,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ):
        self.state_path = Path(state_path)
        self.max_daily_llm_calls = max(0, int(max_daily_llm_calls))
        self.cooldown_minutes = max(1, int(cooldown_minutes))
        self.retention_days = max(1, int(retention_days or DEFAULT_RETENTION_DAYS))

    def decide(self, run_date: str, now: Optional[datetime] = None) -> BudgetDecision:
        now = now or utc_now()
        state, error = _load_state(self.state_path, self.retention_days)
        if error:
            day = _new_day(run_date, self.max_daily_llm_calls)
            day["cooldown_reason"] = REASON_STATE_MALFORMED
            snapshot = build_budget_snapshot(
                day,
                decision="skip_llm",
                decision_reason=REASON_STATE_MALFORMED,
                now=now,
            )
            return BudgetDecision(run_date, False, "skip_llm", REASON_STATE_MALFORMED, snapshot)

        day = _ensure_day(state, run_date, self.max_daily_llm_calls)
        snapshot = build_budget_snapshot(day, decision="call_llm", decision_reason=REASON_AVAILABLE, now=now)

        if snapshot["cooldown_active"]:
            snapshot["decision"] = "skip_llm"
            snapshot["decision_reason"] = REASON_COOLDOWN_ACTIVE
            return BudgetDecision(run_date, False, "skip_llm", REASON_COOLDOWN_ACTIVE, snapshot)

        if snapshot["budget_exhausted"]:
            snapshot["decision"] = "skip_llm"
            snapshot["decision_reason"] = REASON_BUDGET_EXHAUSTED
            return BudgetDecision(run_date, False, "skip_llm", REASON_BUDGET_EXHAUSTED, snapshot)

        return BudgetDecision(run_date, True, "call_llm", REASON_AVAILABLE, snapshot)

    def snapshot(self, run_date: str, now: Optional[datetime] = None) -> Dict[str, Any]:
        return self.decide(run_date, now=now).snapshot

    def _save(self, state: Dict[str, Any], run_date: str, now: datetime) -> None:
        _prune_days(state, run_date, self.retention_days)
        state["schema_version"] = SCHEMA_VERSION
        state["billing_truth"] = BILLING_TRUTH
        state["retention_days"] = self.retention_days
        state["updated_at_utc"] = iso_utc(now)
        atomic_write_json(self.state_path, state)

    def record_llm_call(self, run_date: str, now: Optional[datetime] = None) -> BudgetDecision:
        now = now or utc_now()
        state, error = _load_state(self.state_path, self.retention_days)
        if error:
            return self.decide(run_date, now=now)
        day = _ensure_day(state, run_date, self.max_daily_llm_calls)
        day["llm_calls_used"] = _non_negative_int(day.get("llm_calls_used", 0)) + 1
        day["budget_exhausted"] = day["llm_calls_used"] >= day["max_daily_llm_calls"]
        self._save(state, run_date, now)
        return self.decide(run_date, now=now)

    def record_quota_error(self, run_date: str, now: Optional[datetime] = None) -> BudgetDecision:
        now = now or utc_now()
        state, error = _load_state(self.state_path, self.retention_days)
        if error:
            return self.decide(run_date, now=now)
        day = _ensure_day(state, run_date, self.max_daily_llm_calls)
        day["quota_error_count"] = _non_negative_int(day.get("quota_error_count", 0)) + 1
        day["last_quota_error_at_utc"] = iso_utc(now)
        day["cooldown_reason"] = REASON_QUOTA_ERROR
        day["cooldown_until_utc"] = iso_utc(now + timedelta(minutes=self.cooldown_minutes))
        day["cooldown_active"] = True
        day["budget_exhausted"] = _non_negative_int(day.get("llm_calls_used", 0)) >= day["max_daily_llm_calls"]
        self._save(state, run_date, now)
        return self.decide(run_date, now=now)
