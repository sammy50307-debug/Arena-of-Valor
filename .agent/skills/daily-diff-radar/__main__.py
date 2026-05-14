"""daily-diff-radar — CLI entry point (P71.9).

Usage:
  python __main__.py                    # 自動偵測今日 analysis JSON 並 diff
  python __main__.py --date 2026-05-11  # 指定基準日
  python __main__.py --output json      # JSON 格式輸出
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
    parser = argparse.ArgumentParser(description="daily-diff-radar: 今日 vs 昨日英雄數據差異")
    parser.add_argument("--date", default=None, help="基準日 YYYY-MM-DD (default: 今日)")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    from radar import DailyDiffRadar

    print("[daily-diff-radar 已啟動]")
    radar = DailyDiffRadar(data_dir=_PROJECT_ROOT / "data" / "analysis")
    result = radar.radar(today_date=args.date)

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    alert = result.get("alert_level", "—")
    print(f"警戒等級：{alert}")
    heroes = result.get("hero_shifts", [])
    if heroes:
        print(f"\n英雄變動（Top {min(5, len(heroes))}）：")
        for h in heroes[:5]:
            print(f"  {h.get('hero'):12s}  聲量Δ {h.get('vol_pct',0):+.1f}%  情緒Δ {h.get('sent_delta',0):+.3f}")
    else:
        print("（無英雄數據）")


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
        _rec("daily-diff-radar", _dur, _rc)
    except Exception:
        pass
    sys.exit(_rc)


if __name__ == "__main__":
    _run_with_metrics()
