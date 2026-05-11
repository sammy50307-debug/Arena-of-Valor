import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

_SKILL_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SKILL_DIR / "data"

REQUIRED_CSV = [
    ("styles.csv",     "Style Category",   50),
    ("colors.csv",     "Primary (Hex)",    10),
    ("typography.csv", None,                5),
    ("charts.csv",     None,                3),
]


def run_tests():
    print("[*] 啟動 ui-ux-pro-max 資料完整性測試...\n")
    passed = 0
    total = 0

    # 測試一：data/ 目錄存在
    total += 1
    if _DATA_DIR.exists():
        print("【測試一】data/ 目錄存在\n  ✅ 通過\n")
        passed += 1
    else:
        print(f"【測試一】data/ 目錄不存在：{_DATA_DIR}\n  ❌ 失敗\n")

    # 測試二：必要 CSV 檔案皆可讀，且行數達最低門檻
    for fname, key_col, min_rows in REQUIRED_CSV:
        total += 1
        fpath = _DATA_DIR / fname
        if not fpath.exists():
            print(f"【測試二-{fname}】檔案不存在\n  ❌ 失敗\n")
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            row_count = len(rows)
            if key_col and rows and key_col not in rows[0]:
                print(f"【測試二-{fname}】缺少欄位 '{key_col}'（有 {row_count} 行）\n  ❌ 失敗\n")
                continue
            if row_count < min_rows:
                print(f"【測試二-{fname}】行數不足（{row_count} < {min_rows}）\n  ❌ 失敗\n")
                continue
            print(f"【測試二-{fname}】{row_count} 行，欄位正確\n  ✅ 通過\n")
            passed += 1
        except Exception as e:
            print(f"【測試二-{fname}】讀取失敗：{e}\n  ❌ 失敗\n")

    # 測試三：styles.csv 第一筆包含 AI Prompt Keywords
    total += 1
    try:
        with open(_DATA_DIR / "styles.csv", encoding="utf-8") as f:
            first = next(csv.DictReader(f))
        if "AI Prompt Keywords" in first and len(first["AI Prompt Keywords"]) > 10:
            print("【測試三】styles.csv 第一筆含 AI Prompt Keywords\n  ✅ 通過\n")
            passed += 1
        else:
            print("【測試三】AI Prompt Keywords 欄位為空或太短\n  ❌ 失敗\n")
    except Exception as e:
        print(f"【測試三】讀取失敗：{e}\n  ❌ 失敗\n")

    print("-" * 50)
    print(f"[{'✓' if passed == total else '✗'}] {passed}/{total} 測試通過")
    if passed == total:
        print("[✓] ALL TESTS PASSED - ui-ux-pro-max 資料庫完整，設計情報就位！")
    else:
        print("[!] 部分測試失敗，請檢查上方錯誤訊息")


if __name__ == "__main__":
    run_tests()
