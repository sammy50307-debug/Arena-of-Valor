"""Disabled-by-default LLM provider router (P93).

The router is intentionally fail-closed: P93 creates provider slots and
diagnostics, but it does not implement live Groq / Cloudflare / GitHub Models
calls. The existing Gemini/OpenAI fallback path remains the default daily route.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import config
from analyzer.provider_clients.base import LLMProviderClient


PROVIDER_DIAGNOSTICS_SCHEMA_VERSION = 1
PROVIDER_DIAGNOSTICS_TRUTH = "raw-free provider routing snapshot only"

STATUS_DISABLED_BY_DEFAULT = "disabled_by_default"
STATUS_ENABLED_BUT_BLOCKED = "enabled_but_blocked"
STATUS_MISSING_SECRET = "missing_secret"
STATUS_READY_MANUAL_ONLY = "ready_manual_only"
STATUS_UNKNOWN = "unknown"

ROUTE_LEGACY_DEFAULT = "router_disabled_legacy_default"
ROUTE_PRIMARY_ONLY = "router_enabled_primary_only"
ROUTE_BLOCKED_EXPERIMENTAL_SLOT = "blocked_enabled_experimental_slot"
ROUTE_UNKNOWN = "unknown"

ATTEMPT_CALLED = "called"
ATTEMPT_BLOCKED = "blocked"
ATTEMPT_FAILED = "failed"

ALLOWED_SLOT_STATUS = {
    STATUS_DISABLED_BY_DEFAULT,
    STATUS_ENABLED_BUT_BLOCKED,
    STATUS_MISSING_SECRET,
    STATUS_READY_MANUAL_ONLY,
    STATUS_UNKNOWN,
}
ALLOWED_ROUTE_STATUS = {
    ROUTE_LEGACY_DEFAULT,
    ROUTE_PRIMARY_ONLY,
    ROUTE_BLOCKED_EXPERIMENTAL_SLOT,
    ROUTE_UNKNOWN,
}
ALLOWED_ATTEMPT_STATUS = {ATTEMPT_CALLED, ATTEMPT_BLOCKED, ATTEMPT_FAILED}
ALLOWED_PROVIDERS = {"gemini_primary", "openai_fallback", "groq", "cloudflare_ai", "github_models"}


def _positive_int(value: Any, default: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, parsed)


@dataclass(frozen=True)
class ProviderSlot:
    name: str
    provider_type: str
    enabled: bool = False
    secret_configured: bool = False
    manual_only: bool = True
    status: str = STATUS_DISABLED_BY_DEFAULT

    def as_dict(self) -> Dict[str, Any]:
        status = self.status if self.status in ALLOWED_SLOT_STATUS else STATUS_UNKNOWN
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "enabled": bool(self.enabled),
            "secret_configured": bool(self.secret_configured),
            "manual_only": bool(self.manual_only),
            "status": status,
        }


class ProviderRouteBlocked(RuntimeError):
    """Raised when a non-default provider slot is enabled before live support."""


def _slot_status(
    *,
    enabled: bool,
    secret_configured: bool,
    router_enabled: bool,
    experimental_enabled: bool,
) -> str:
    if not enabled:
        return STATUS_DISABLED_BY_DEFAULT
    if not router_enabled or not experimental_enabled:
        return STATUS_ENABLED_BUT_BLOCKED
    if not secret_configured:
        return STATUS_MISSING_SECRET
    return STATUS_READY_MANUAL_ONLY


def build_provider_slots(
    *,
    router_enabled: Optional[bool] = None,
    experimental_enabled: Optional[bool] = None,
) -> List[ProviderSlot]:
    """Build raw-free provider slot metadata from config flags."""

    router = config.PROVIDER_ROUTER_ENABLED if router_enabled is None else bool(router_enabled)
    experimental = (
        config.EXPERIMENTAL_FREE_PROVIDERS_ENABLED
        if experimental_enabled is None
        else bool(experimental_enabled)
    )
    candidates = [
        (
            "groq",
            "openai_compatible",
            bool(config.AOV_PROVIDER_GROQ_ENABLED),
            bool(config.GROQ_API_KEY),
        ),
        (
            "cloudflare_ai",
            "openai_compatible",
            bool(config.AOV_PROVIDER_CLOUDFLARE_AI_ENABLED),
            bool(config.CLOUDFLARE_API_TOKEN and config.CLOUDFLARE_ACCOUNT_ID),
        ),
        (
            "github_models",
            "openai_compatible",
            bool(config.AOV_PROVIDER_GITHUB_MODELS_ENABLED),
            bool(config.GITHUB_MODELS_TOKEN),
        ),
    ]
    return [
        ProviderSlot(
            name=name,
            provider_type=provider_type,
            enabled=enabled,
            secret_configured=secret_configured,
            manual_only=True,
            status=_slot_status(
                enabled=enabled,
                secret_configured=secret_configured,
                router_enabled=router,
                experimental_enabled=experimental,
            ),
        )
        for name, provider_type, enabled, secret_configured in candidates
    ]


def _clean_slot(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return ProviderSlot("", "unknown", status=STATUS_UNKNOWN).as_dict()
    name = str(value.get("name", "") or "")
    if name not in ALLOWED_PROVIDERS:
        name = "unknown"
    status = str(value.get("status", STATUS_UNKNOWN) or STATUS_UNKNOWN)
    if status not in ALLOWED_SLOT_STATUS:
        status = STATUS_UNKNOWN
    return {
        "name": name,
        "provider_type": str(value.get("provider_type", "") or "unknown"),
        "enabled": bool(value.get("enabled", False)),
        "secret_configured": bool(value.get("secret_configured", False)),
        "manual_only": bool(value.get("manual_only", True)),
        "status": status,
    }


def _clean_attempt(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    provider = str(value.get("provider", "") or "")
    if provider not in ALLOWED_PROVIDERS:
        provider = "unknown"
    status = str(value.get("status", "") or "")
    if status not in ALLOWED_ATTEMPT_STATUS:
        status = ATTEMPT_FAILED
    return {
        "provider": provider,
        "role": str(value.get("role", "") or ""),
        "status": status,
        "failure_class": str(value.get("failure_class", "") or ""),
        "budget_decision": str(value.get("budget_decision", "") or ""),
    }


def build_provider_diagnostics(
    *,
    router_enabled: Optional[bool] = None,
    experimental_enabled: Optional[bool] = None,
    route_status: str = "",
    active_provider: str = "gemini_primary",
    slots: Optional[List[ProviderSlot]] = None,
    attempts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    router = config.PROVIDER_ROUTER_ENABLED if router_enabled is None else bool(router_enabled)
    experimental = (
        config.EXPERIMENTAL_FREE_PROVIDERS_ENABLED
        if experimental_enabled is None
        else bool(experimental_enabled)
    )
    if not route_status:
        route_status = ROUTE_PRIMARY_ONLY if router else ROUTE_LEGACY_DEFAULT
    if route_status not in ALLOWED_ROUTE_STATUS:
        route_status = ROUTE_UNKNOWN
    if active_provider not in ALLOWED_PROVIDERS:
        active_provider = "gemini_primary"
    slot_dicts = [slot.as_dict() for slot in (slots or build_provider_slots(router_enabled=router, experimental_enabled=experimental))]
    return {
        "schema_version": PROVIDER_DIAGNOSTICS_SCHEMA_VERSION,
        "provider_truth": PROVIDER_DIAGNOSTICS_TRUTH,
        "router_enabled": router,
        "experimental_free_providers_enabled": experimental,
        "active_provider": active_provider,
        "route_status": route_status,
        "budget_guard": "required_before_provider_call",
        "raw_payload_logging": False,
        "secrets_logged": False,
        "max_attempts": _positive_int(getattr(config, "PROVIDER_ROUTER_MAX_ATTEMPTS", 1) or 1),
        "slots": slot_dicts,
        "attempts": [_clean_attempt(x) for x in (attempts or [])],
    }


def normalize_provider_diagnostics(value: Any) -> Dict[str, Any]:
    """Normalize raw-free provider diagnostics for run_manifest.json."""

    if not isinstance(value, dict):
        return build_provider_diagnostics()
    route_status = str(value.get("route_status", "") or "")
    if route_status not in ALLOWED_ROUTE_STATUS:
        route_status = ROUTE_UNKNOWN
    active_provider = str(value.get("active_provider", "") or "gemini_primary")
    if active_provider not in ALLOWED_PROVIDERS:
        active_provider = "gemini_primary"
    slots = value.get("slots", [])
    if not isinstance(slots, list):
        slots = []
    attempts = value.get("attempts", [])
    if not isinstance(attempts, list):
        attempts = []
    return {
        "schema_version": PROVIDER_DIAGNOSTICS_SCHEMA_VERSION,
        "provider_truth": PROVIDER_DIAGNOSTICS_TRUTH,
        "router_enabled": bool(value.get("router_enabled", False)),
        "experimental_free_providers_enabled": bool(value.get("experimental_free_providers_enabled", False)),
        "active_provider": active_provider,
        "route_status": route_status,
        "budget_guard": "required_before_provider_call",
        "raw_payload_logging": False,
        "secrets_logged": False,
        "max_attempts": _positive_int(value.get("max_attempts", 1) or 1),
        "slots": [_clean_slot(x) for x in slots],
        "attempts": [_clean_attempt(x) for x in attempts],
    }


def validate_provider_diagnostics(value: Any) -> tuple[bool, list[str]]:
    if value in ({}, None):
        return True, []
    if not isinstance(value, dict):
        return False, ["provider.routing must be object"]
    errors: list[str] = []
    if value.get("schema_version") != PROVIDER_DIAGNOSTICS_SCHEMA_VERSION:
        errors.append("provider.routing.schema_version must be %s" % PROVIDER_DIAGNOSTICS_SCHEMA_VERSION)
    if value.get("provider_truth") != PROVIDER_DIAGNOSTICS_TRUTH:
        errors.append("provider.routing.provider_truth must be raw-free provider routing snapshot only")
    for key in ("router_enabled", "experimental_free_providers_enabled", "raw_payload_logging", "secrets_logged"):
        if not isinstance(value.get(key), bool):
            errors.append("provider.routing.%s must be boolean" % key)
    if value.get("raw_payload_logging") is not False:
        errors.append("provider.routing.raw_payload_logging must be false")
    if value.get("secrets_logged") is not False:
        errors.append("provider.routing.secrets_logged must be false")
    if value.get("route_status") not in ALLOWED_ROUTE_STATUS:
        errors.append("provider.routing.route_status must be an allowed status")
    if value.get("active_provider") not in ALLOWED_PROVIDERS:
        errors.append("provider.routing.active_provider must be an allowed provider")
    if not isinstance(value.get("max_attempts"), int) or isinstance(value.get("max_attempts"), bool) or value.get("max_attempts") < 1:
        errors.append("provider.routing.max_attempts must be positive integer")
    slots = value.get("slots")
    if not isinstance(slots, list):
        errors.append("provider.routing.slots must be list")
    else:
        for index, slot in enumerate(slots):
            if not isinstance(slot, dict):
                errors.append("provider.routing.slots[%s] must be object" % index)
                continue
            if slot.get("name") not in ALLOWED_PROVIDERS and slot.get("name") != "unknown":
                errors.append("provider.routing.slots[%s].name invalid" % index)
            if slot.get("status") not in ALLOWED_SLOT_STATUS:
                errors.append("provider.routing.slots[%s].status invalid" % index)
            for key in ("enabled", "secret_configured", "manual_only"):
                if not isinstance(slot.get(key), bool):
                    errors.append("provider.routing.slots[%s].%s must be boolean" % (index, key))
    attempts = value.get("attempts")
    if not isinstance(attempts, list):
        errors.append("provider.routing.attempts must be list")
    else:
        for index, attempt in enumerate(attempts):
            if not isinstance(attempt, dict):
                errors.append("provider.routing.attempts[%s] must be object" % index)
                continue
            if attempt.get("provider") not in ALLOWED_PROVIDERS and attempt.get("provider") != "unknown":
                errors.append("provider.routing.attempts[%s].provider invalid" % index)
            if attempt.get("status") not in ALLOWED_ATTEMPT_STATUS:
                errors.append("provider.routing.attempts[%s].status invalid" % index)
    return len(errors) == 0, errors


class ProviderRouter:
    """Delegate to the existing primary client unless experimental slots are enabled."""

    CONCURRENCY_LIMIT = 1

    def __init__(
        self,
        primary: Optional[LLMProviderClient] = None,
        *,
        router_enabled: Optional[bool] = None,
        experimental_enabled: Optional[bool] = None,
        slots: Optional[List[ProviderSlot]] = None,
    ):
        if primary is None:
            from analyzer.fallback_llm_client import FallbackLLMClient

            primary = FallbackLLMClient()
        self.primary = primary
        self.router_enabled = config.PROVIDER_ROUTER_ENABLED if router_enabled is None else bool(router_enabled)
        self.experimental_enabled = (
            config.EXPERIMENTAL_FREE_PROVIDERS_ENABLED
            if experimental_enabled is None
            else bool(experimental_enabled)
        )
        self.slots = slots or build_provider_slots(
            router_enabled=self.router_enabled,
            experimental_enabled=self.experimental_enabled,
        )
        self.last_route_status = ROUTE_PRIMARY_ONLY if self.router_enabled else ROUTE_LEGACY_DEFAULT
        self.last_attempts: List[Dict[str, Any]] = []
        self.CONCURRENCY_LIMIT = getattr(self.primary, "CONCURRENCY_LIMIT", 1)

    @property
    def cache_manager(self):
        return self.primary.cache_manager

    @property
    def fallback_configured(self) -> bool:
        return bool(getattr(self.primary, "fallback_configured", False))

    @property
    def last_fallback_used(self) -> bool:
        return bool(getattr(self.primary, "last_fallback_used", False))

    def _enabled_candidate_slots(self) -> List[ProviderSlot]:
        return [slot for slot in self.slots if slot.enabled]

    def _guard_candidate_slots(self) -> None:
        enabled = self._enabled_candidate_slots()
        if not enabled:
            return
        self.last_route_status = ROUTE_BLOCKED_EXPERIMENTAL_SLOT
        self.last_attempts = [
            {
                "provider": slot.name,
                "role": "candidate",
                "status": ATTEMPT_BLOCKED,
                "failure_class": "ProviderRouteBlocked",
                "budget_decision": "",
            }
            for slot in enabled
        ]
        raise ProviderRouteBlocked("enabled provider slots require a later manual-only smoke phase")

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        temperature: float = 0.3,
        response_schema: Optional[dict] = None,
    ) -> Union[dict, str]:
        self._guard_candidate_slots()
        self.last_route_status = ROUTE_PRIMARY_ONLY if self.router_enabled else ROUTE_LEGACY_DEFAULT
        self.last_attempts = [{"provider": "gemini_primary", "role": "primary", "status": ATTEMPT_CALLED, "failure_class": "", "budget_decision": ""}]
        try:
            return await self.primary.chat(
                system_prompt,
                user_prompt,
                json_mode=json_mode,
                temperature=temperature,
                response_schema=response_schema,
            )
        except Exception as exc:
            self.last_attempts[-1]["status"] = ATTEMPT_FAILED
            self.last_attempts[-1]["failure_class"] = type(exc).__name__
            raise

    async def batch_chat(
        self,
        system_prompt: str,
        user_prompts: List[str],
        json_mode: bool = True,
        concurrency: Optional[int] = None,
        response_schema: Optional[dict] = None,
    ) -> List[Union[dict, str]]:
        self._guard_candidate_slots()
        self.last_route_status = ROUTE_PRIMARY_ONLY if self.router_enabled else ROUTE_LEGACY_DEFAULT
        self.last_attempts = [{"provider": "gemini_primary", "role": "primary", "status": ATTEMPT_CALLED, "failure_class": "", "budget_decision": ""}]
        try:
            return await self.primary.batch_chat(
                system_prompt,
                user_prompts,
                json_mode=json_mode,
                concurrency=concurrency,
                response_schema=response_schema,
            )
        except Exception as exc:
            self.last_attempts[-1]["status"] = ATTEMPT_FAILED
            self.last_attempts[-1]["failure_class"] = type(exc).__name__
            raise

    def provider_diagnostics(self) -> Dict[str, Any]:
        return build_provider_diagnostics(
            router_enabled=self.router_enabled,
            experimental_enabled=self.experimental_enabled,
            route_status=self.last_route_status,
            active_provider="gemini_primary",
            slots=self.slots,
            attempts=self.last_attempts,
        )


def _build_chain_llm_client(chain: List[tuple]) -> "FallbackLLMClient":
    """依 ``PROVIDER_CHAIN``（``[(provider, model), ...]``）組首發＋多級 fallback。

    首級＝首發、其餘＝逐級 fallback；fallback 共用 primary 的 ``cache_manager``
    （與 S1 ``_build_default_fallbacks`` 一致，避免重複快取）。
    """
    from analyzer.fallback_llm_client import FallbackLLMClient
    from analyzer.provider_registry import build_provider

    primary_provider, primary_model = chain[0]
    primary = build_provider(primary_provider, model=primary_model)
    fallbacks = [
        build_provider(name, model=model, cache_manager=primary.cache_manager)
        for name, model in chain[1:]
    ]
    return FallbackLLMClient(primary=primary, fallbacks=fallbacks)


def build_default_llm_client() -> LLMProviderClient:
    """組裝預設 LLM client。

    優先讀 ``config.PROVIDER_CHAIN``（P105.1 B 架構：鏈每級 ``provider:model``）組首發＋
    多級 fallback；無 ``PROVIDER_CHAIN`` 時退回 S1 路徑——``FallbackLLMClient`` 依
    ``config.PRIMARY_PROVIDER`` / ``FALLBACK_PROVIDERS`` 動態組裝。``PROVIDER_ROUTER_ENABLED``
    時再包一層 ``ProviderRouter``。換首發／調鏈／調額度只需改 ``.env``。
    """
    from analyzer.fallback_llm_client import FallbackLLMClient

    if config.PROVIDER_CHAIN:
        primary = _build_chain_llm_client(config.PROVIDER_CHAIN)
    else:
        primary = FallbackLLMClient()
    if not config.PROVIDER_ROUTER_ENABLED:
        return primary
    return ProviderRouter(primary=primary)
