"""session-handoff-packager — CLI entry point (P71.9).

Usage:
  python __main__.py --doing "Phase 71 開發" --next "跑 P71.9 測試"
  python __main__.py --doing "..." --stuck "測試第 2 項失敗" --next "..."
  python __main__.py --output json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR / "scripts"))

_PROJECT_ROOT = _SKILL_DIR.parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="session-handoff-packager: 收工前打包任務快照")
    parser.add_argument("--doing", default="", help="目前正在做什麼")
    parser.add_argument("--stuck", default="", help="卡在哪裡（選填）")
    parser.add_argument("--next", default="", help="下個視窗的第一步")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    from packager import SessionHandoffPackager

    print("[session-handoff-packager 已啟動]")
    p = SessionHandoffPackager(project_root=_PROJECT_ROOT)
    result = p.pack(doing=args.doing, stuck=args.stuck or None, next_step=args.next or None)

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    paths = p.save(result)
    print(f"✅ lite 版 → {paths.get('lite', '—')}")
    print(f"✅ full 版 → {paths.get('full', '—')}")


def _run_with_metrics() -> None:
    import time as _time
    _t0 = _time.perf_counter()
    _rc = 0
    try:
        _ret = main()
        _rc = _ret if isinstance(_ret, int) else 0
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else (0 if _e.code is None else 1)
    except Exception:
        _rc = 1
    finally:
        _dur = (_time.perf_counter() - _t0) * 1000
    try:
        _scripts = str(Path(__file__).resolve().parents[3] / "scripts")
        if _scripts not in sys.path:
            sys.path.insert(0, _scripts)
        from skill_metrics_logger import record as _rec
        _rec("session-handoff-packager", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
