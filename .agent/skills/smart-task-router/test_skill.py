"""
smart-task-router test suite（P71.6 升級版）
測試新的 S1 schema 接入 + 數值信心分數 + V1 觸發塊格式。
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from router import SmartTaskRouter, THRESHOLD_CONFIRM

REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "skills" / "registry.json"


def make_router() -> SmartTaskRouter:
    return SmartTaskRouter(registry_path=REGISTRY_PATH)


def run_tests():
    print("[*] smart-task-router P71.6 測試啟動...\n")
    passed = 0
    total = 0
    router = make_router()

    # ─────────────────────────────────────────────
    # 測試 0：registry 載入成功（非空）
    # ─────────────────────────────────────────────
    total += 1
    if len(router.skills) > 0:
        print(f"【測試 0】registry 載入 ✅  ({len(router.skills)} 個 skill)\n")
        passed += 1
    else:
        print(f"【測試 0】❌ 無法載入 registry.json，路徑：{REGISTRY_PATH}\n")

    # ─────────────────────────────────────────────
    # 測試 1：多 keyword 強匹配 → history-trend-query，信心達 CONFIRM 以上
    # 查詢包含 6 個 trigger_keyword：聲量/走勢/趨勢/輿情/最近幾天/歷史查詢 → 1.0
    # ─────────────────────────────────────────────
    total += 1
    result = router.route("芽芽聲量走勢趨勢輿情最近幾天歷史查詢")
    best = result.get("best_match") or {}
    if best.get("name") == "history-trend-query" and result["confidence"] >= THRESHOLD_CONFIRM:
        print(f"【測試 1】強匹配 history-trend-query ✅  信心={result['confidence']:.2f}  動作={result['action']}\n")
        passed += 1
    else:
        print(f"【測試 1】❌ 預期 history-trend-query，實際={best.get('name')} 信心={result['confidence']:.2f}\n")

    # ─────────────────────────────────────────────
    # 測試 2：多 keyword 強匹配 → hallucination-judge，信心達 CONFIRM 以上
    # 查詢包含 4 個 trigger_keyword：幻覺/英雄名稱驗證/戰報驗證/hallucination → 0.8
    # ─────────────────────────────────────────────
    total += 1
    result = router.route("戰報有幻覺英雄名稱驗證失敗戰報驗證hallucination")
    best = result.get("best_match") or {}
    if best.get("name") == "hallucination-judge" and result["confidence"] >= THRESHOLD_CONFIRM:
        print(f"【測試 2】強匹配 hallucination-judge ✅  信心={result['confidence']:.2f}  動作={result['action']}\n")
        passed += 1
    else:
        print(f"【測試 2】❌ 預期 hallucination-judge，實際={best.get('name')} 信心={result['confidence']:.2f}\n")

    # ─────────────────────────────────────────────
    # 測試 3：低信心 → NO_MATCH（無關語句）
    # ─────────────────────────────────────────────
    total += 1
    result = router.route("今天天氣很好，適合出去走走")
    if result["action"] == "NO_MATCH":
        print(f"【測試 3】低信心 NO_MATCH ✅  信心={result['confidence']:.2f}\n")
        passed += 1
    else:
        print(f"【測試 3】❌ 預期 NO_MATCH，實際={result['action']}  best={result.get('best_match', {}).get('name')}\n")

    # ─────────────────────────────────────────────
    # 測試 4：閾值邏輯驗證（信心計算正確性）
    # ─────────────────────────────────────────────
    total += 1
    result_high = router.route("聲量走勢趨勢輿情最近幾天比較")
    result_low = router.route("吃飯睡覺打遊戲")

    high_conf = result_high["confidence"]
    low_conf = result_low["confidence"]
    if high_conf > low_conf and low_conf < THRESHOLD_CONFIRM:
        print(f"【測試 4】閾值邏輯正確 ✅  高信心={high_conf:.2f} 低信心={low_conf:.2f}\n")
        passed += 1
    else:
        print(f"【測試 4】❌ 閾值邏輯異常：高={high_conf:.2f} 低={low_conf:.2f}\n")

    # ─────────────────────────────────────────────
    # 測試 5：V1 觸發塊格式驗證
    # ─────────────────────────────────────────────
    total += 1
    block = router.format_v1_block(
        skill_name="history-trend-query",
        trigger_reason="匹配 trigger_keyword 「聲量」",
        confidence=0.92,
        action="AUTO",
        source="smart-task-router (L2)",
    )
    required_parts = ["history-trend-query", "0.92", "smart-task-router (L2)"]
    if all(p in block for p in required_parts):
        print(f"【測試 5】V1 觸發塊格式 ✅\n  {block[:80]}...\n")
        passed += 1
    else:
        print(f"【測試 5】❌ V1 觸發塊缺少必要欄位\n  block: {block}\n")

    # ─────────────────────────────────────────────
    # 測試 6：list_skills 回傳非空清單
    # ─────────────────────────────────────────────
    total += 1
    skills = router.list_skills()
    if len(skills) > 0 and all("name" in s for s in skills):
        print(f"【測試 6】list_skills ✅  ({len(skills)} 個)\n")
        passed += 1
    else:
        print(f"【測試 6】❌ list_skills 回傳異常：{skills[:2]}\n")

    # ─────────────────────────────────────────────
    # 測試 7：JSON 輸出格式完整性（route 回傳欄位）
    # ─────────────────────────────────────────────
    total += 1
    result = router.route("幫我抓取 IG 貼文，JS 動態渲染的 SPA")
    required_keys = {"query", "action", "confidence", "candidates", "registry_path"}
    if required_keys.issubset(result.keys()):
        json.dumps(result, ensure_ascii=False)  # 確認可序列化
        print(f"【測試 7】JSON 輸出格式 ✅  欄位齊全，序列化 OK\n")
        passed += 1
    else:
        missing = required_keys - result.keys()
        print(f"【測試 7】❌ 缺少欄位：{missing}\n")

    # ─────────────────────────────────────────────
    print("-" * 55)
    print(f"[{'✓' if passed == total else '✗'}] {passed}/{total} 測試通過")
    if passed == total:
        print("[✓] ALL TESTS PASSED — smart-task-router L2 路由引擎已就位！")
    else:
        print("[!] 部分測試失敗，請檢查上方錯誤訊息")
    return passed == total


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
