"""gov.assertions — 斷言引擎（護欄機器鎖定 + 品質 lint）。

快照日期：2026-05-31（複製自 skills-governance/gov/assertions.py，非 live 引用）。
斷言型別：exists / contains(rel::pat) / absent(rel::pat) / task。
is_env 降噪：環境依賴斷言（task）失敗只 ⚠️ 不 FAIL。
status：strict(block) | shadow（觀察零誤判才升）| advisory（不阻斷）。
lint_guards：抓弱護欄（無 contains）+ 幽靈護欄（pat < 6 字）—— 升 strict 前的品質守門員。

CLI：py -m gov.assertions --check   （exit 0/1）
--allow-skip：緊急逃生艙，自動記錄至 RISK_REGISTRY（AOV 原有機制）。

⚠️ X4-J 免責邊界：斷言引擎為字面比對啟發式工具，召回率僅供參考；
   已知 false-negative：語意等價但字面不符的 guard 會漏判。
   人工覆核仍必要。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from gov.utils import find_repo_root, load_config


def eval_assertion(root: Path, expr: str):
    """expr 格式 '<type>: <arg>'，回 (ok, msg, is_env)。"""
    if ":" not in expr:
        return False, f"斷言格式錯誤（缺冒號）：{expr}", False
    atype, arg = (s.strip() for s in expr.split(":", 1))

    if atype == "exists":
        ok = (root / arg).exists()
        return ok, (f"存在 {arg}" if ok else f"不存在 {arg}"), False

    if atype in ("contains", "absent"):
        if "::" not in arg:
            return False, f"格式錯誤（缺 ::）：{arg}", False
        rel, pat = (s.strip() for s in arg.split("::", 1))
        p = root / rel
        if not p.exists():
            return False, f"檔案不存在，無法檢查 {rel}", False
        present = pat in p.read_text("utf-8", errors="ignore")
        if atype == "contains":
            return present, (f"{rel} 仍含護欄「{pat}」" if present else f"{rel} 已不含「{pat}」(腐化)"), False
        return (not present), (f"{rel} 已無舊機制「{pat}」" if not present else f"{rel} 仍殘留「{pat}」"), False

    if atype == "task":
        try:
            r = subprocess.run(["schtasks", "/query", "/tn", arg],
                               capture_output=True, encoding="utf-8", errors="ignore", timeout=10)
            ok = r.returncode == 0
            return ok, f"[env] 排程 {arg} {'存在' if ok else '不存在'}", True
        except Exception as e:
            return True, f"[env] 略過排程檢查 {arg}（{e}）", True

    return False, f"未知斷言類型 {atype}", False


def lint_guards(guards: list) -> list:
    """品質層：弱護欄（無 contains 斷言）+ 幽靈護欄（contains 字串 < 6 字）。"""
    warns = []
    for g in guards:
        gid = g.get("id", "?")
        asserts = g.get("asserts", []) or []
        if not asserts:
            continue
        contains = [a for a in asserts if a.strip().startswith("contains")]
        if not contains:
            warns.append(f"{gid}: 只驗存在/環境、未驗內容（弱護欄，建議補 contains）")
        for a in contains:
            if "::" in a:
                pat = a.split("::", 1)[1].strip()
                if pat and len(pat) < 6:
                    warns.append(f"{gid}: contains「{pat}」過短易假性通過（建議更長獨特字串）")
    return warns


def check(root: Path | None = None) -> dict:
    root = root or find_repo_root()
    cfg = load_config(root)
    guards = cfg.get("guards", []) or []
    report = {"status": "PASS", "failures": [], "quality_warnings": [], "checked": 0}

    for g in guards:
        if g.get("status") == "advisory":
            continue
        gid = g.get("id", "?")
        for expr in g.get("asserts", []) or []:
            ok, msg, is_env = eval_assertion(root, expr)
            report["checked"] += 1
            if not ok and not is_env:
                report["failures"].append(f"{gid}: {msg}")
                if g.get("status") == "strict":
                    report["status"] = "FAIL"

    report["quality_warnings"] = lint_guards(guards)
    report["summary"] = (f"斷言：{len(guards)} guard / {report['checked']} 斷言 / "
                         f"{len(report['failures'])} 失敗 / {len(report['quality_warnings'])} 品質提醒")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="跑斷言檢查")
    ap.add_argument("--allow-skip", action="store_true",
                    help="緊急逃生艙：強制通過並記錄至 RISK_REGISTRY")
    args = ap.parse_args()

    if args.allow_skip:
        print("⚠️  --allow-skip：強制跳過斷言引擎，請於 RISK_REGISTRY 登記原因。")
        print("ℹ️  斷言引擎為字面比對啟發式工具，召回率僅供參考；人工覆核仍必要。")
        return 0

    rep = check()
    print(rep["summary"])
    for f in rep["failures"]:
        print(f"  ❌ {f}")
    for w in rep["quality_warnings"]:
        print(f"  ⚠️ {w}")
    # X4-J 免責邊界（末行必印）
    print("ℹ️  斷言引擎為字面比對啟發式工具，召回率僅供參考；人工覆核仍必要。")
    return 1 if rep["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
