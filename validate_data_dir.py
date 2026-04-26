"""
validate_data_dir.py — Phase 56.5 維運 CLI

掃整個 data/ 目錄，列出哪些 analysis_*.json 違反契約。
不修改任何檔案——純診斷。

用法：
  py validate_data_dir.py                # 掃預設 data/
  py validate_data_dir.py path/to/data   # 掃指定目錄
  py validate_data_dir.py --quiet        # 只印失敗

退出碼：0=全部健康；1=有違規檔；2=目錄不存在
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analyzer.data_writer import validate_summary  # noqa: E402


def scan(data_dir: Path, quiet: bool = False) -> int:
    if not data_dir.is_dir():
        print(f"[ERROR] 目錄不存在：{data_dir}")
        return 2

    files = sorted(data_dir.glob("analysis_*.json"))
    if not files:
        print(f"[INFO] {data_dir} 內找不到 analysis_*.json")
        return 0

    healthy = []
    violations = []

    for f in files:
        try:
            size = f.stat().st_size
            if size == 0:
                violations.append((f, "0-byte 空檔（atomic write 治本前殘檔）", []))
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            ok, missing = validate_summary(data)
            if ok:
                healthy.append(f)
            else:
                violations.append((f, "schema 契約不合", missing))
        except json.JSONDecodeError as e:
            violations.append((f, f"JSON 解析失敗：{e}", []))
        except Exception as e:
            violations.append((f, f"{type(e).__name__}: {e}", []))

    if not quiet:
        print(f"=== 掃描 {data_dir} ===")
        print(f"健康檔 {len(healthy)} 支 / 違規檔 {len(violations)} 支 / 總共 {len(files)} 支")

    if violations:
        print("--- 違規清單 ---")
        for f, reason, missing in violations:
            line = f"  [VIOLATION] {f.name}：{reason}"
            if missing:
                line += f"（缺 {missing}）"
            print(line)

    if not quiet and not violations:
        print("[OK] data/ 全部健康")

    return 1 if violations else 0


def main() -> int:
    args = [a for a in sys.argv[1:] if a not in ("--quiet", "-q")]
    quiet = any(a in ("--quiet", "-q") for a in sys.argv[1:])
    target = Path(args[0]) if args else (ROOT / "data")
    return scan(target, quiet=quiet)


if __name__ == "__main__":
    sys.exit(main())
