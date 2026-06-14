"""P117 gov.preflight 統一總指揮防復發測試。

驗：①聚合 blocking/warning 分級 ②防遞迴 guard ③config profiles 無孤兒引用
④ci profile 含預期 report 檢查。

刻意設計：
- aggregation 用 mock subprocess（跨平台、不真跑 checker）；
- 不跑 full/tests profile（避免 pytest→preflight→pytest 遞迴，靠防遞迴 guard + 受控 config 雙保險）。
"""
from __future__ import annotations

import types

import gov.preflight as pf
import gov.utils as gu


def test_recursion_guard(monkeypatch):
    """GOV_PREFLIGHT_RUNNING=1（巢狀呼叫）→ 直接略過、回 ok=True、零 results（防無限遞迴）。"""
    monkeypatch.setenv("GOV_PREFLIGHT_RUNNING", "1")
    rep = pf.run_profile("ci")
    assert rep["ok"] is True
    assert rep["results"] == []
    assert "巢狀" in rep["summary"]


def test_aggregation_levels(monkeypatch):
    """聚合分級：blocking 失敗→ok=False 進 blocking；warning 失敗→進 warnings 不擋；pass 不進兩者。"""
    monkeypatch.delenv("GOV_PREFLIGHT_RUNNING", raising=False)
    fake_cfg = {
        "preflight": {
            "recursion_guard_env": "GOV_PREFLIGHT_RUNNING",
            "profiles": {"t": ["okcheck", "warncheck", "blockcheck"]},
            "checks": {
                "okcheck": {"run": "RC0", "level": "warning", "timeout": 5},
                "warncheck": {"run": "RC1W", "level": "warning", "timeout": 5},
                "blockcheck": {"run": "RC1B", "level": "blocking", "timeout": 5},
            },
        }
    }
    monkeypatch.setattr(pf, "load_config", lambda root: fake_cfg)

    def _fake_run(cmd, **kw):
        rc = 0 if "RC0" in cmd else 1
        return types.SimpleNamespace(returncode=rc, stdout="tail-line", stderr="")

    monkeypatch.setattr(pf.subprocess, "run", _fake_run)

    rep = pf.run_profile("t")
    assert rep["ok"] is False, "有 blocking 失敗應 ok=False"
    assert len(rep["blocking"]) == 1, "blockcheck 應進 blocking"
    assert len(rep["warnings"]) == 1, "warncheck 應進 warnings（不擋）"
    assert len(rep["results"]) == 3


def test_config_profiles_no_orphan_refs():
    """真實 governance_config.yaml：每個 profile 引用的 check id 都必須定義於 checks（防孤兒引用）。"""
    cfg = gu.load_config(gu.find_repo_root())
    pfg = cfg.get("preflight", {})
    checks = set((pfg.get("checks") or {}).keys())
    for prof, ids in (pfg.get("profiles") or {}).items():
        for cid in ids or []:
            assert cid in checks, f"profile '{prof}' 引用未定義的 check: {cid}"


def test_ci_profile_registers_report_checks():
    """ci profile（接管 daily_report.yml）必須含取代原 4 個個別 step 的報告檢查。"""
    cfg = gu.load_config(gu.find_repo_root())
    ci = (cfg.get("preflight", {}).get("profiles", {}) or {}).get("ci") or []
    for cid in ("report_health", "system_doctor", "report_freshness", "slo"):
        assert cid in ci, f"ci profile 缺 {cid}（接管 CI 不完整）"


def test_full_profile_registers_scattered_checkers():
    """full profile 必須把原本散落的 dev/治理/source checker 都註冊進來（一鍵總指揮目標）。"""
    cfg = gu.load_config(gu.find_repo_root())
    full = (cfg.get("preflight", {}).get("profiles", {}) or {}).get("full") or []
    for cid in ("known_issue_guard", "artifact_hygiene", "root_legacy", "handoff_truth", "no_fake_stats"):
        assert cid in full, f"full profile 缺 {cid}（checker 仍散落）"
