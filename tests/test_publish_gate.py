from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from main import evaluate_publish_gate


def test_publish_gate_blocks_nonpublishable_quality_tier():
    reasons, checks = evaluate_publish_gate(
        "2026-05-16",
        "showcase",
        quality_tier="showcase_manual",
    )

    assert reasons == ["quality_tier is showcase_manual (not publishable)"]
    assert checks == []


def test_publish_gate_accepts_local_only_quality_tier(monkeypatch):
    fake_health = ModuleType("check_daily_report_health")
    fake_health.run_checks = lambda *args, **kwargs: [SimpleNamespace(failed=False)]
    monkeypatch.setitem(sys.modules, "check_daily_report_health", fake_health)

    reasons, checks = evaluate_publish_gate(
        "2026-05-16",
        "production",
        quality_tier="production_local_only",
    )

    assert reasons == []
    assert len(checks) == 1
