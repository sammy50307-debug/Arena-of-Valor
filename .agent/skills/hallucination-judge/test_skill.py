import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from judge import HallucinationJudge

def run_tests():
    print("[*] 啟動 AI 幻覺裁判測試...\n")
    judge = HallucinationJudge()
    passed = 0
    total = 0

    # 測試一：乾淨的正常戰報（應 PASS）
    total += 1
    clean_text = '''
    今日台服輿情分析：英雄【芽芽】相關討論量上升，玩家對新版本評價正面。
    {"sentiment_score": 0.75}
    勝率約 52%，情緒整體穩定。
    '''
    result = judge.judge(clean_text)
    if result["verdict"] == "PASS" and result["confidence_score"] == 100:
        print(f"【測試一】乾淨戰報 (預期 PASS)\n  裁決: {result['verdict']} | 信心分: {result['confidence_score']}\n  ✅ 通過\n")
        passed += 1
    else:
        print(f"【測試一】乾淨戰報 ❌ 失敗: {result}\n")

    # 測試二：包含不存在英雄（應 FAIL / WARN）
    total += 1
    fake_hero_text = '英雄「滅世龍帝」與英雄「芽芽」對決，英雄「暗黑審判者」登場。'
    result = judge.judge(fake_hero_text)
    has_unknown = len(result["details"]["hero_check"]["unknown_heroes"]) > 0
    if has_unknown and result["verdict"] != "PASS":
        print(f"【測試二】假英雄名稱 (預期偵測到未知英雄)\n  裁決: {result['verdict']} | 信心分: {result['confidence_score']}")
        print(f"  未知英雄: {result['details']['hero_check']['unknown_heroes']}\n  ✅ 通過\n")
        passed += 1
    else:
        print(f"【測試二】假英雄名稱 ❌ 失敗: {result}\n")

    # 測試三：sentiment_score 越界（應偵測數值異常）
    total += 1
    bad_numeric_text = '{"sentiment_score": 1.95} 今日情緒超級正面！'
    result = judge.judge(bad_numeric_text)
    violations = result["details"]["numeric_check"]["violations"]
    if len(violations) > 0 and result["verdict"] != "PASS":
        print(f"【測試三】情緒分數越界 1.95 (預期 FAIL/WARN)\n  裁決: {result['verdict']} | 信心分: {result['confidence_score']}")
        print(f"  違規項目: {violations[0]['field']} = {violations[0]['value']}\n  ✅ 通過\n")
        passed += 1
    else:
        print(f"【測試三】情緒分數越界 ❌ 失敗: {result}\n")

    # 測試四：勝率超過 100%（應偵測幻覺模式）
    total += 1
    impossible_text = '芽芽本週勝率高達 150%，創下歷史新高！'
    result = judge.judge(impossible_text)
    triggered = result["details"]["pattern_check"]["triggered_patterns"]
    numeric_violations = result["details"]["numeric_check"]["violations"]
    if len(triggered) > 0 or len(numeric_violations) > 0:
        print(f"【測試四】勝率 150% 幻覺 (預期偵測異常)\n  裁決: {result['verdict']} | 信心分: {result['confidence_score']}")
        print(f"  偵測到問題數: {len(result['issues'])}\n  ✅ 通過\n")
        passed += 1
    else:
        print(f"【測試四】勝率 150% 幻覺 ❌ 失敗: {result}\n")

    # 測試五：合法英雄 + 合法數值（應 PASS）
    total += 1
    valid_text = '英雄【悟空】與英雄【超人】的對決備受關注。{"sentiment_score": -0.3} 負面比例 45%'
    result = judge.judge(valid_text)
    if result["verdict"] == "PASS":
        print(f"【測試五】合法英雄+數值 (預期 PASS)\n  裁決: {result['verdict']} | 信心分: {result['confidence_score']}\n  ✅ 通過\n")
        passed += 1
    else:
        print(f"【測試五】合法英雄+數值 ❌ 失敗: {result['issues']}\n")

    print("-" * 50)
    print(f"[{'✓' if passed == total else '✗'}] {passed}/{total} 測試通過")
    if passed == total:
        print("[✓] ALL TESTS PASSED - AI 幻覺裁判已就位，戰報品質守門員上線！")
    else:
        print("[!] 部分測試失敗，請檢查上方錯誤訊息")

if __name__ == "__main__":
    run_tests()
