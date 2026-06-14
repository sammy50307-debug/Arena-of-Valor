"""P111 self-heal 防復發測試（G-i 真跑 generate 5 case + G-ii 零額度 guard）。

G-i：真實呼叫 ReportGenerator.generate（不用 _fake_generate 寫死路徑），釘住 self-heal 與
三方路徑（report / sidecar / manifest）契約；三隔離（config→tmp、patch _indexer.save_index、
chdir tmp）+ 跑後真 repo `git status --porcelain` 零新增改動。
G-ii：乾淨子進程 import scripts.replay_run，斷言 sys.modules 不含具體 LLM client（零額度前提機器化）。
"""
from __future__ import annotations

import json
import subprocess
import sys
import types
from pathlib import Path

import scripts.replay_run as replay
import reporter.generator as gen_mod
from reporter.generator import ReportGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-06-14"
DATE_COMPACT = "20260614"
CANON_NAME = "aov_report_%s.html" % DATE
SIDECAR_NAME = "aov_report_%s.freshness.json" % DATE


def _write_analysis(data_dir: Path, *, mode: str = "production", quality_tier: str = "production_full") -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / ("analysis_%s.json" % DATE_COMPACT)).write_text(
        json.dumps(
            {
                "date": DATE,
                "overview": "ok",
                "overall": {"sentiment_score": 0.5, "trend": "Stable"},
                "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
                "_meta": {"mode": mode, "quality_tier": quality_tier},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _write_prior_manifest(data_dir: Path, *, status: str, error: str) -> None:
    """P112：模擬 main.py 先寫的失敗 manifest（self-heal 會讀它取 error 再覆蓋）。"""
    mdir = data_dir / "runs" / DATE
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "run_manifest.json").write_text(
        json.dumps({"status": status, "error": error}, ensure_ascii=False), encoding="utf-8"
    )


def _isolate(tmp_path: Path, monkeypatch):
    """三隔離 + generate 呼叫計數器（仍真跑：delegate 原函數）。回 (data_dir, reports_dir, index_file, calls)。"""
    data_dir = tmp_path / "data"
    reports_dir = data_dir / "reports"
    monkeypatch.setattr(replay.config, "DATA_DIR", data_dir)
    monkeypatch.setattr(replay.config, "REPORTS_DIR", reports_dir)
    # 隔離2：patch 真實 news_history_index 寫入（_INDEX_PATH import 時綁定，故 patch save_index 本身）
    monkeypatch.setattr(gen_mod._indexer, "save_index", lambda *a, **k: None)
    # 隔離3：chdir tmp（中和 generate 內 Path("yaya_bg.png") CWD 相對複製）
    monkeypatch.chdir(tmp_path)
    # 隔離4：generate 內 ui_previews 備份寫死 Path(__file__).parent.parent/ui_previews（真 repo，不受 config/chdir 隔離，
    # 且 .gitignore 忽略使 git status 看不到 → 會給「零副作用」假保證）。fake 掉 shutil.copy2（generator 僅用 copy2）
    # 使 generate 真正零真-repo 寫入；不影響 replay 的 quarantine（其 shutil 屬另一模組）。
    monkeypatch.setattr(gen_mod, "shutil", types.SimpleNamespace(copy2=lambda *a, **k: None))
    # 隔離1：landing index 導 tmp（heal 的 repo_root=config.DATA_DIR.parent=tmp → index_file=tmp/index.html）
    index_file = tmp_path / "index.html"
    index_file.write_text(
        '<a href="data/reports/old.html" class="main-btn">進入最新戰報 (2026-06-01)</a>',
        encoding="utf-8",
    )
    calls = {"generate": 0}
    orig = ReportGenerator.generate

    def _counting(self, *a, **k):
        calls["generate"] += 1
        return orig(self, *a, **k)

    monkeypatch.setattr(ReportGenerator, "generate", _counting)
    return data_dir, reports_dir, index_file, calls


def _git_porcelain() -> str:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return out.stdout


# ── case ①：缺 + publishable + health pass → promote + canonical + index 指向 + manifest is_backfill + git 零改動 ──
def test_heal_promotes_when_missing_and_passes_gate(tmp_path, monkeypatch, capsys):
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir)
    # 先清掉先前跑可能留下的 gitignored ui_previews 測試殘留，跑後斷言未被重建 → 證明隔離4 生效
    stray = REPO_ROOT / "ui_previews" / CANON_NAME
    stray.unlink(missing_ok=True)
    before = _git_porcelain()

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    assert calls["generate"] == 1, "應真跑 generate 重產一次"
    canonical = reports_dir / CANON_NAME
    assert canonical.exists(), "publishable + 過閘門 → 應 promote 出 canonical"
    assert (reports_dir / SIDECAR_NAME).exists(), "修法A：promote 成功才寫 freshness sidecar"
    assert ('aov_report_%s.html" class="main-btn"' % DATE) in index_file.read_text(encoding="utf-8"), "index 應指向重產報告"
    manifest = json.loads((data_dir / "runs" / DATE / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["is_backfill"] is True
    assert manifest["self_heal"] is True
    assert manifest["promoted"] is True
    # 隔離4 已 fake 掉 ui_previews 寫入 → generate 真正零真-repo 寫入（含 .gitignore 看不到的工作目錄殘留）
    assert _git_porcelain() == before, "真跑 generate 不得在真 repo 留下 git 可見改動"
    assert not stray.exists(), "隔離4 應使測試不在真 repo ui_previews 留殘留（修正審查揪出的假保證盲區）"


# ── case ②：tier 非 publishable → no-op + ::warning::（generate 前置擋下，零重產）──
def test_heal_noop_when_tier_not_publishable(tmp_path, monkeypatch, capsys):
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir, quality_tier="error_fallback")

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    assert calls["generate"] == 0, "tier 非 publishable 應在 generate 前收手"
    assert not (reports_dir / CANON_NAME).exists()
    assert "::warning::" in capsys.readouterr().out


# ── case ②b：tier 空 → 同樣 no-op + ::warning::（plan「含空」高頻路徑）──
def test_heal_noop_when_tier_empty(tmp_path, monkeypatch, capsys):
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir, quality_tier="")

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    assert calls["generate"] == 0
    assert not (reports_dir / CANON_NAME).exists()
    assert "::warning::" in capsys.readouterr().out


# ── case ③：publishable + health fail → candidate 在但不 promote + sidecar 缺 + index 未改 ──
def test_heal_noop_when_gate_fails(tmp_path, monkeypatch, capsys):
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    # tier publishable 過 heal 前置；mode=showcase → 閘門 metadata-mode 檢查 FAIL（expected production）
    _write_analysis(data_dir, mode="showcase", quality_tier="production_full")
    index_before = index_file.read_text(encoding="utf-8")

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0, "閘門不過應 no-op 降級（不 return 1）"
    assert calls["generate"] == 1, "應重產 candidate 才能跑閘門"
    # candidate 第一版檔名即 canonical 名，故檔在；但「未 promote」由 sidecar 缺 + index 未改判定
    assert not (reports_dir / SIDECAR_NAME).exists(), "未 promote → 不得寫 sidecar（不留孤兒）"
    assert index_file.read_text(encoding="utf-8") == index_before, "未 promote → index 不得變"
    manifest = json.loads((data_dir / "runs" / DATE / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["self_heal"] is True
    assert manifest["promoted"] is False
    assert "::warning::" in capsys.readouterr().out


# ── case ④：report 已在 → no-op，零副作用（mtime 不變 + generate 未呼叫）──
def test_heal_noop_when_report_exists(tmp_path, monkeypatch, capsys):
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    canonical = reports_dir / CANON_NAME
    existing = "<!-- mode: production -->\n<html>existing</html>\n"
    canonical.write_text(existing, encoding="utf-8")
    mtime_before = canonical.stat().st_mtime_ns

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    assert calls["generate"] == 0, "report 已在 → 不重產（抗重入）"
    assert canonical.stat().st_mtime_ns == mtime_before, "零副作用：既有報告 mtime 不得變"
    assert canonical.read_text(encoding="utf-8") == existing


# ── case ⑤：analysis 缺 → return 1（既有契約，heal 不繞過）──
def test_heal_returns_1_when_analysis_missing(tmp_path, monkeypatch):
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    # 不寫 analysis

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 1
    assert calls["generate"] == 0


# ── 修法A 契約釘樁：sidecar 綁定發布事件——cron 式「generate(promote=False) 後外部 promote_candidate」必寫；
#    只 generate 不 promote 不寫（防孤兒 + 防 cron 因修法A 失去 sidecar，視角2 揪出的 coverage 缺口）──
def test_sidecar_bound_to_promote_event(tmp_path, monkeypatch):
    monkeypatch.setattr(gen_mod._indexer, "save_index", lambda *a, **k: None)
    monkeypatch.setattr(gen_mod, "shutil", types.SimpleNamespace(copy2=lambda *a, **k: None))
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "reports"
    reports.mkdir()
    index_file = tmp_path / "index.html"
    index_file.write_text(
        '<a href="data/reports/old.html" class="main-btn">進入最新戰報 (2026-06-01)</a>',
        encoding="utf-8",
    )
    summary = {
        "date": DATE,
        "overview": "ok",
        "overall": {"sentiment_score": 0.5, "trend": "Stable"},
        "sentiment_distribution": {"positive": 1, "negative": 0, "neutral": 0},
        "_meta": {"mode": "production", "quality_tier": "production_full"},
    }
    gen = ReportGenerator()
    sidecar = reports / SIDECAR_NAME

    # cron 式序列第一步：generate(promote=False) → 此時 sidecar 不該存在（修法A 解孤兒）
    candidate = gen.generate(summary, [], output_dir=reports, promote=False)
    assert not sidecar.exists(), "generate(promote=False) 不得寫 sidecar（candidate-only 不留孤兒）"

    # cron 式序列第二步：外部 promote_candidate（main.py/self-heal 真實序列）→ sidecar 此時才寫
    gen.promote_candidate(candidate, DATE, output_dir=reports, index_file=index_file)
    assert sidecar.exists(), "promote_candidate 後 sidecar 必須寫（修法A 不可讓 cron 失去 sidecar）"


# ── P112：self-heal 保留 generate 失敗原因（manifest pre_heal_error，持久+可診斷）──
def test_pre_heal_error_captured_from_failed_manifest(tmp_path, monkeypatch, capsys):
    """主路徑：main.py 先寫 status=failed manifest → self-heal 讀其 error 帶進 pre_heal_error，再覆蓋。"""
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir)  # publishable production → heal 會 promote
    _write_prior_manifest(data_dir, status="failed", error="BOOM: generate exploded")

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    manifest = json.loads((data_dir / "runs" / DATE / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["self_heal"] is True
    assert manifest["promoted"] is True
    assert manifest["pre_heal_error"] == "BOOM: generate exploded", "應從失敗 manifest 保留 generate 失敗原因"


def test_pre_heal_error_empty_when_no_prior_manifest(tmp_path, monkeypatch, capsys):
    """無 pre-existing manifest（generate 在 manifest 寫入前更早期崩）→ pre_heal_error 空（誠實標示盲區）。"""
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir)

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    manifest = json.loads((data_dir / "runs" / DATE / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["pre_heal_error"] == ""


def test_pre_heal_error_ignored_when_prior_status_ok(tmp_path, monkeypatch, capsys):
    """既有 manifest status!=failed（非失敗）→ 不捕獲其 error（只保留真失敗原因）。"""
    data_dir, reports_dir, index_file, calls = _isolate(tmp_path, monkeypatch)
    _write_analysis(data_dir)
    _write_prior_manifest(data_dir, status="ok", error="should not be captured")

    rc = replay.main(["--date", DATE, "--heal-if-missing", "--check-health"])

    assert rc == 0
    manifest = json.loads((data_dir / "runs" / DATE / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["pre_heal_error"] == ""


def test_build_manifest_pre_heal_error_field():
    """純函數層：build_manifest 傳 pre_heal_error 出現在輸出、不傳為 ""（additive 契約）。"""
    from analyzer.run_manifest import build_manifest

    m = build_manifest(
        run_date=DATE, mode="production", raw_path=None, analysis_path=None,
        report_path=None, pre_heal_error="BOOM",
    )
    assert m["pre_heal_error"] == "BOOM"
    m2 = build_manifest(
        run_date=DATE, mode="production", raw_path=None, analysis_path=None, report_path=None,
    )
    assert m2["pre_heal_error"] == ""


# ── G-ii：零額度 guard——乾淨子進程 import 後 sys.modules 不含具體 LLM client ──
def test_zero_llm_sdk_on_import():
    blacklist = ("openai", "google.genai", "google.generativeai", "anthropic", "httpx", "openrouter")
    code = (
        "import sys\n"
        "sys.path.insert(0, %r)\n" % str(REPO_ROOT)
        + "import scripts.replay_run\n"
        + "BL = %r\n" % (blacklist,)
        + "hits = sorted(m for m in sys.modules if any(b in m for b in BL))\n"
        + "print('HITS:' + ','.join(hits))\n"
        + "sys.exit(1 if hits else 0)\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, (
        "import scripts.replay_run 載入了具體 LLM client（破零額度前提）：\nstdout=%s\nstderr=%s"
        % (proc.stdout, proc.stderr)
    )
