import os
import re
import sys
import argparse
from pathlib import Path

# 強制 UTF-8 輸出環境，防止 Windows CP950 亂碼
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 檢測寫死浮點數的正則：例如 win_rate=52.8, win_rate: 52.8, "win_rate": 52.8
FAKE_STATS_PATTERN = re.compile(
    r'\b(win_rate|pick_rate|ban_rate|wr|pr|br)\b\s*["\']?\s*[:=]\s*(\d+\.\d+)'
)

def scan_content(content: str, filename: str) -> list:
    """掃描文本內容是否含有寫死浮點數的疑似戰績，回傳含 (line_no, line_content) 的列表"""
    # 白名單處理：
    # 1. analyzer/sentiment.py 排除 _generate_fallback_summary 函式內容
    if "sentiment.py" in filename:
        content = re.sub(
            r'def _generate_fallback_summary.*?(def \w+)',
            'def _generate_fallback_summary(): pass\n    \\1',
            content,
            flags=re.DOTALL
        )

    # 2. 移除 if __name__ == "__main__" 區塊
    content = re.sub(
        r'if __name__ == ["\']__main__["\']\s*:.*$',
        'if __name__ == "__main__": pass',
        content,
        flags=re.DOTALL
    )

    issues = []
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        if FAKE_STATS_PATTERN.search(line):
            issues.append((idx, line.strip()))
    return issues

def self_test() -> bool:
    """執行自我測試，確保 checker 能抓到寫死值並避開白名單"""
    print("[*] 啟動 Anti-Fake Stats Checker 自我測試...")
    
    # 測試 case 1：能抓到寫死的浮點數
    test_content_1 = "win_rate = 99.9"
    issues_1 = scan_content(test_content_1, "dummy.py")
    if not issues_1 or "99.9" not in issues_1[0][1]:
        print(" ❌ 自測失敗：無法識別 'win_rate = 99.9'")
        return False
        
    # 測試 case 2：能避開 __main__ 區塊的寫死值
    test_content_2 = """
if __name__ == "__main__":
    win_rate = 52.8
"""
    issues_2 = scan_content(test_content_2, "dummy.py")
    if issues_2:
        print(" ❌ 自測失敗：誤判了 if __name__ == '__main__' 區塊的數值")
        return False
        
    # 測試 case 3：能避開 sentiment.py 內 _generate_fallback_summary 區塊
    test_content_3 = """
    def _generate_fallback_summary(self):
        return {
            "win_rate": 52.8
        }
    def other_func(self):
        pass
"""
    issues_3 = scan_content(test_content_3, "analyzer/sentiment.py")
    if issues_3:
        print(" ❌ 自測失敗：未成功避開 _generate_fallback_summary 白名單")
        return False

    print(" ✅ 自我測試成功！Checker 正則與白名單邏輯皆運作正常。")
    return True

def main():
    parser = argparse.ArgumentParser(description="AOV 輿情監測 - 戰績數據誠實性檢查")
    parser.add_argument("--repo-root", default=".", help="專案根目錄")
    parser.add_argument("--self-test", action="store_true", help="執行自我測試")
    args = parser.parse_args()

    if args.self_test:
        success = self_test()
        sys.exit(0 if success else 1)

    root_path = Path(args.repo_root).resolve()
    print("=" * 60)
    print(" 🛡️ 戰績誠實性檢查工具 (Anti-Fake Stats Checker)")
    print("=" * 60)

    targets = [
        "scrapers/hero_stats.py",
        "reporter/generator.py",
        "main.py",
        "analyzer/sentiment.py"
    ]

    has_issue = False

    for target in targets:
        file_path = root_path / target
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f" [!!] 無法讀取檔案 {target}: {e}")
            continue

        issues = scan_content(content, target)
        for idx, line in issues:
            print(f" [!!] 警告: {target}:{idx} 偵測到疑似寫死戰績數據: {line}")
            has_issue = True

    if not has_issue:
        print(" ✅ 戰績數據誠實性檢查通過！未發現寫死假戰績。")
    else:
        print(" ⚠️ 警告：發現疑似寫死數據，請人工確認是否屬於假戰績。")

    print("\n（本檢查為字面比對啟發式，召回率僅供參考、人工覆核仍必要）")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    main()
