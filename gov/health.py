"""gov.health — skill 健康檢查 + LINE 告警（「壞了會叫」的 runtime checker）。

對 .agent/skills/ 下每個 skill 跑 smoke（test_skill.py），失敗 → 印出 + 可選發 LINE 告警。

與 scripts/gen_skill_health.py 的分工（避免接手者混淆兩者）：
  - 本檔 gov.health：**實際 subprocess 跑 test_skill.py**，出 stdout ✅/🔴 + exit 0/1
    （可當 CI gate）+ LINE 告警。定位＝runtime checker（壞了會叫）。
  - scripts/gen_skill_health.py：**只讀 registry.json 出 Markdown 看板**，從不執行 test。
    定位＝靜態文件生成器（出報表）。

CLI：py -m gov.health [--skill <name>] [--notify]   （exit 0 全過 / 1 有異常）
快照日期：2026-05-31（P104.2 / G2，回填自 skills-governance，在地化接 AOV notifier/）。
"""
from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

from gov.utils import find_repo_root
from notifier.line_bot import LineBotNotifier


def check_skill(skill_dir: Path, root: Path) -> dict:
    """跑單一 skill 的 smoke test，回 {ok, name, summary}。

    雙路徑相容：<skill>/test_skill.py 優先，否則 <skill>/scripts/test_skill.py。
    無 test_skill.py → skip（視為 ok，純 prompt skill 不算 fail，否則永遠紅）。
    任何例外都 graceful（回 ok=False + 異常摘要，不拋出拖垮整批）。
    """
    name = skill_dir.name
    root_test = skill_dir / "test_skill.py"
    sub_test = skill_dir / "scripts" / "test_skill.py"
    test = root_test if root_test.exists() else sub_test
    if not test.exists():
        return {"ok": True, "name": name, "summary": "無 test_skill.py（純 prompt skill，跳過）"}
    try:
        r = subprocess.run(
            [sys.executable, str(test)], cwd=root,
            capture_output=True, encoding="utf-8", errors="ignore", timeout=120,
        )
        out = (r.stdout or "").strip().splitlines()
        tail = next((l.strip() for l in reversed(out)
                     if "測試結果" in l or "PASS" in l or "FAIL" in l), "")
        ok = r.returncode == 0
        return {"ok": ok, "name": name, "summary": tail or ("通過" if ok else "失敗")}
    except Exception as e:  # noqa: BLE001 — 健檢不可因單一 skill 異常而中斷
        return {"ok": False, "name": name, "summary": f"執行異常 {e}"}


def notify_via_aov(title: str) -> bool:
    """skill smoke 失敗時發 LINE 告警；token 未設 → notifier 自己回 False（graceful）。

    借用 LineBotNotifier.send_daily_report（只認 title/report_url）。主體保持同步，
    只在這一步用 asyncio.run 包 async 呼叫。告警失敗（網路/token）絕不拖垮健檢主流程。
    """
    payload = {"title": f"🔴 [GOV 健檢] {title}", "report_url": ""}
    try:
        return asyncio.run(LineBotNotifier().send_daily_report(payload))
    except Exception:  # noqa: BLE001 — 告警失敗不可拖垮健檢
        return False


def run(skill_name: str | None = None, notify: bool = False, root: Path | None = None) -> dict:
    """列舉 .agent/skills 下 skill → 逐一 smoke → 彙整 → 失敗且 notify 時告警。

    回 {ok, results, failed, notified}。
    root 預設 find_repo_root()；測試可傳 tmp_path 隔離（避免掃到真實 repo）。
    .agent/skills 不存在時 graceful 回空報告（不炸）。
    """
    root = root or find_repo_root()
    skills_dir = root / ".agent" / "skills"
    if not skills_dir.exists():
        return {"ok": True, "results": [], "failed": [], "notified": False}
    if skill_name:
        targets = [skills_dir / skill_name]
    else:
        targets = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    results = [check_skill(d, root) for d in targets]
    failed = [r for r in results if not r["ok"]]
    report = {"ok": not failed, "results": results, "failed": failed, "notified": False}
    if failed and notify:
        msg = "skill 異常：" + "，".join(f"{r['name']}（{r['summary']}）" for r in failed)
        report["notified"] = notify_via_aov(msg)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="skill 健康檢查 + LINE 告警")
    ap.add_argument("--skill", default=None, help="只檢查指定 skill")
    ap.add_argument("--notify", action="store_true", help="失敗時發 LINE 告警")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # CLI 下確保中文/emoji 不亂碼
    except Exception:  # pytest 捕獲 stdout 時無 reconfigure，graceful 略過
        pass
    rep = run(args.skill, args.notify)
    for r in rep["results"]:
        print(f"  {'✅' if r['ok'] else '🔴'} {r['name']}: {r['summary']}")
    if rep["failed"]:
        tail = "，已發 LINE 告警" if rep["notified"] else "，未發告警（無 token 或 --notify 未開）"
        print(f"🔴 健檢未通過（{len(rep['failed'])} skill 異常）{tail}")
    else:
        print("✅ 健檢通過（全部 skill smoke 過）")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
