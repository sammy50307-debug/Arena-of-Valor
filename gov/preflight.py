"""gov.preflight — preflight 編排器（一鍵自檢總指揮）。

快照日期：2026-05-31（複製自 skills-governance/gov/preflight.py，非 live 引用）。
blocking/warning 分級 + 防遞迴（GOV_PREFLIGHT_RUNNING）。
從 governance_config.yaml 讀 profiles/checks，編排執行各 check、分級彙整、單一退出碼。

CLI：py -m gov.preflight [--profile fast|full]   （exit 0=通過 / 1=阻斷）
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from gov.utils import find_repo_root, load_config


def _resolve_python(cmd: str) -> str:
    """把 check 字串開頭的 'python ' 換成當前解譯器，避免 Windows 上 python Store stub 失效。"""
    if cmd.startswith("python "):
        return f'"{sys.executable}" ' + cmd[len("python "):]
    return cmd


def run_profile(profile: str = "fast", root: Path | None = None) -> dict:
    root = root or find_repo_root()
    cfg = load_config(root)
    pf = cfg.get("preflight", {}) or {}
    guard_env = pf.get("recursion_guard_env", "GOV_PREFLIGHT_RUNNING")

    # 防遞迴：巢狀呼叫直接略過（取自 Hermes HERMES_PREFLIGHT_TESTS 設計）
    if os.environ.get(guard_env) == "1":
        return {"ok": True, "blocking": [], "warnings": [], "results": [],
                "summary": "（巢狀呼叫，略過 preflight 防遞迴）"}

    checks = pf.get("checks", {}) or {}
    profile_ids = pf.get("profiles", {}).get(profile) or list(checks.keys())
    blocking, warnings, results = [], [], []
    child_env = dict(os.environ, **{guard_env: "1"})

    for cid in profile_ids:
        spec = checks.get(cid)
        if not spec:
            warnings.append(f"{cid}: 未定義於 config")
            continue
        cmd = _resolve_python(spec.get("run", ""))
        level = spec.get("level", "warning")
        timeout = spec.get("timeout", 60)
        try:
            r = subprocess.run(cmd, shell=True, cwd=root, env=child_env,
                               capture_output=True, encoding="utf-8", errors="ignore", timeout=timeout)
            ok = r.returncode == 0
            out = (r.stdout or "").strip().splitlines()
            tail = out[-1] if out else ("(無輸出)" if ok else (r.stderr or "").strip()[:120])
            results.append((cid, ok, level, tail))
            if not ok:
                (blocking if level == "blocking" else warnings).append(f"{cid}: {tail}")
        except Exception as e:
            results.append((cid, False, level, str(e)))
            (blocking if level == "blocking" else warnings).append(f"{cid}: 執行異常 {e}")

    ok = not blocking
    return {"ok": ok, "blocking": blocking, "warnings": warnings, "results": results,
            "summary": ("✅ preflight 通過" if ok else f"🔴 preflight 未通過（{len(blocking)} 阻斷級問題）")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="fast", choices=["fast", "full", "ci"], help="檢查層級（P117：+ci 報告產後驗證）")
    args = ap.parse_args()
    rep = run_profile(args.profile)
    for cid, ok, level, tail in rep.get("results", []):
        icon = "✅" if ok else ("🔴" if level == "blocking" else "⚠️")
        print(f"  {icon} [{level}] {cid}: {tail}")
    for w in rep["warnings"]:
        print(f"  ⚠️ {w}")
    print(rep["summary"])
    # 末行免責邊界（X4-J：啟發式工具召回率僅供參考，人工覆核仍必要）
    print("ℹ️  preflight 為規則型自動化，召回率僅供參考；人工覆核仍必要。")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
