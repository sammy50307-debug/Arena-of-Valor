"""Shared provider-call budget guard (P93)."""

from __future__ import annotations

from typing import Any


def ensure_budget_for_provider_call(client: Any, *, record_call: bool = True) -> None:
    """Call a compatible client's budget guard when it exposes one.

    Existing GeminiClient owns the P90 budget ledger. P93 deliberately keeps
    this helper duck-typed so future provider adapters can reuse the same guard
    without importing Gemini-specific classes.
    """

    guard = getattr(client, "_ensure_budget_for_provider_call", None)
    if callable(guard):
        guard(record_call=record_call)
