"""tests/test_health.py — gov.health（skill smoke + LINE 告警）的契約測試。

先寫測試再實作（TDD）：本檔定義 gov.health 的 API 契約，health.py 必須對齊。
快照日期：2026-05-31（P104.2 / G2）。

測試慣例對齊 tests/test_assertions.py：sys.path 注入 PROJECT_ROOT、tmp_path 隔離 repo、
write_text 一律 encoding="utf-8"（Windows cp950 陷阱）。

關鍵隔離手法：
- run(root=...) 接受 root 參數 → tmp_path 隔離；否則 find_repo_root 會往上找到真 repo
  的 governance_config.yaml，測試會誤掃真實 .agent/skills。
- 告警一律 mock，絕不真的發送（FakeNotifier 攔截，或 patch config token="" 走 graceful）。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gov.health import check_skill, run, notify_via_aov, main


# ── 測試輔助：造隔離 skill ──────────────────────────────
def _make_skill(root: Path, name: str, exit_code: int | None, in_scripts: bool = False) -> Path:
    """在 root/.agent/skills/<name> 造一個 skill。

    exit_code=None → 不放 test_skill.py（純 prompt skill，應 skip）。
    exit_code=0/1  → 放一個 sys.exit(exit_code) 的 test_skill.py（smoke 過/壞）。
    in_scripts=True → test 放在 scripts/ 子層（驗雙路徑相容）。
    """
    d = root / ".agent" / "skills" / name
    target = d / "scripts" if in_scripts else d
    target.mkdir(parents=True, exist_ok=True)
    if exit_code is not None:
        (target / "test_skill.py").write_text(
            f"import sys\nsys.exit({exit_code})\n", encoding="utf-8"
        )
    return d


# ── 假 notifier：保證測試絕不真的發送 ──────────────────
class _FakeNotifier:
    """攔截 LineBotNotifier，記錄呼叫、永不發網路。"""

    instances: list = []

    def __init__(self, *args, **kwargs):
        self.sent: list = []
        _FakeNotifier.instances.append(self)

    async def send_daily_report(self, payload: dict) -> bool:
        self.sent.append(payload)
        return True


# ── 1. graceful：token 未設時只回 False、不拋、不真發（Exit③）──
def test_notify_graceful_when_no_token(monkeypatch):
    # config token 在 import 時固化，須 patch 屬性（不可用 setenv，那時已固化失效）
    monkeypatch.setattr("config.LINE_CHANNEL_ACCESS_TOKEN", "")
    monkeypatch.setattr("config.LINE_USER_ID", "")
    # 真 LineBotNotifier：token="" → send_daily_report 立刻 return False，不發網路
    assert notify_via_aov("健檢測試告警") is False


# ── 2. 純 prompt skill skip：無 test_skill.py 不算 fail（防 instagram skill 永遠紅）──
def test_skill_without_test_is_skipped_not_failed(tmp_path: Path):
    d = _make_skill(tmp_path, "promptonly", exit_code=None)
    rep = check_skill(d, tmp_path)
    assert rep["ok"] is True, "無 test_skill.py 應 skip 視為 ok，不可當 fail"
    assert rep["name"] == "promptonly"


# ── 3a. smoke 通過：test_skill.py exit 0 → ok ──
def test_check_skill_passing(tmp_path: Path):
    d = _make_skill(tmp_path, "goodskill", exit_code=0)
    rep = check_skill(d, tmp_path)
    assert rep["ok"] is True


# ── 3b. smoke 失敗：test_skill.py exit 1 → not ok ──
def test_check_skill_failing(tmp_path: Path):
    d = _make_skill(tmp_path, "badskill", exit_code=1)
    rep = check_skill(d, tmp_path)
    assert rep["ok"] is False


# ── 4. 雙路徑相容：test 在 scripts/ 子層也要被找到 ──
def test_check_skill_dual_path_scripts_subdir(tmp_path: Path):
    d = _make_skill(tmp_path, "subskill", exit_code=0, in_scripts=True)
    rep = check_skill(d, tmp_path)
    assert rep["ok"] is True, "scripts/test_skill.py（雙路徑）也要能被 smoke 到"


# ── 5. run 彙整：過/壞/skip 正確分類，failed 只含真壞的 ──
def test_run_collects_pass_fail_skip(tmp_path: Path):
    _make_skill(tmp_path, "goodskill", 0)
    _make_skill(tmp_path, "badskill", 1)
    _make_skill(tmp_path, "promptonly", None)
    rep = run(root=tmp_path, notify=False)
    failed_names = [r["name"] for r in rep["failed"]]
    assert "badskill" in failed_names
    assert "goodskill" not in failed_names
    assert "promptonly" not in failed_names, "純 prompt skill 不可進 failed"
    assert rep["ok"] is False
    assert isinstance(rep["results"], list)


# ── 6. 空 skills 目錄不 crash ──
def test_run_clean_on_empty_repo(tmp_path: Path):
    (tmp_path / ".agent" / "skills").mkdir(parents=True)
    rep = run(root=tmp_path, notify=False)
    assert rep["ok"] is True  # 沒 skill → 沒 fail
    assert rep["failed"] == []
    assert rep["notified"] is False


# ── 7. 韌性：.agent/skills 完全不存在時也不炸 ──
def test_run_when_skills_dir_missing(tmp_path: Path):
    rep = run(root=tmp_path, notify=False)
    assert rep["ok"] is True
    assert rep["failed"] == []


# ── 8. notify=False 時不發告警、不建 notifier ──
def test_no_notify_when_disabled(tmp_path: Path, monkeypatch):
    _FakeNotifier.instances = []
    monkeypatch.setattr("gov.health.LineBotNotifier", _FakeNotifier)
    _make_skill(tmp_path, "badskill", 1)
    rep = run(root=tmp_path, notify=False)
    assert rep["notified"] is False
    assert _FakeNotifier.instances == [], "notify=False 不該建 notifier / 發送"


# ── 9. smoke 失敗 + notify=True → 有發告警，payload 借用 send_daily_report 形狀 ──
def test_notify_called_on_failure(tmp_path: Path, monkeypatch):
    _FakeNotifier.instances = []
    monkeypatch.setattr("gov.health.LineBotNotifier", _FakeNotifier)
    _make_skill(tmp_path, "badskill", 1)
    rep = run(root=tmp_path, notify=True)
    assert rep["ok"] is False
    assert rep["notified"] is True, "smoke 失敗 + notify=True 應發告警"
    assert len(_FakeNotifier.instances) >= 1
    sent = _FakeNotifier.instances[0].sent
    assert sent and "title" in sent[0], "payload 須含 title（借用 send_daily_report 契約）"


# ── 10. 全過時 notify=True 也不發（沒壞就不吵）──
def test_no_notify_when_all_pass(tmp_path: Path, monkeypatch):
    _FakeNotifier.instances = []
    monkeypatch.setattr("gov.health.LineBotNotifier", _FakeNotifier)
    _make_skill(tmp_path, "goodskill", 0)
    rep = run(root=tmp_path, notify=True)
    assert rep["ok"] is True
    assert rep["notified"] is False
    assert _FakeNotifier.instances == [], "全過不該發告警"


# ── 11. main() exit code：ok→0 ──
def test_main_exit_zero_when_ok(monkeypatch):
    monkeypatch.setattr("sys.argv", ["gov.health"])
    monkeypatch.setattr(
        "gov.health.run",
        lambda skill_name=None, notify=False, root=None: {
            "ok": True, "results": [], "failed": [], "notified": False},
    )
    assert main() == 0


# ── 12. main() exit code：fail→1 ──
def test_main_exit_one_when_fail(monkeypatch):
    monkeypatch.setattr("sys.argv", ["gov.health"])
    monkeypatch.setattr(
        "gov.health.run",
        lambda skill_name=None, notify=False, root=None: {
            "ok": False,
            "results": [{"ok": False, "name": "x", "summary": "bad"}],
            "failed": [{"ok": False, "name": "x", "summary": "bad"}],
            "notified": False},
    )
    assert main() == 1
