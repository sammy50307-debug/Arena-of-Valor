import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from router import SmartTaskRouter

def run_tests():
    print("[*] 啟動智能任務路由器測試...\n")
    router = SmartTaskRouter()
    passed = 0
    total = 0

    # 測試一：情報收集任務 → 應路由至爬蟲類 skill
    total += 1
    result = router.route("我要從 Instagram 的 FB 粉絲頁抓取今日貼文，但網頁是 JavaScript 動態渲染的 SPA")
    if result["routing_decision"] == "firecrawl-dynamic-breacher":
        print(f"【測試一】動態渲染爬蟲任務\n  路由決策: {result['routing_decision']} ✅\n  信心: {result['confidence']}\n")
        passed += 1
    else:
        print(f"【測試一】❌ 預期 firecrawl-dynamic-breacher，實際得到: {result['routing_decision']}\n  候選: {[r['skill_id'] for r in result['recommendations']]}\n")

    # 測試二：快取任務 → 應路由至語意快取神盾
    total += 1
    result = router.route("幫我攔截重複洗版的貼文，避免相同內容反覆消耗 API 費用")
    if result["routing_decision"] == "semantic-cache-shield":
        print(f"【測試二】快取攔截任務\n  路由決策: {result['routing_decision']} ✅\n  信心: {result['confidence']}\n")
        passed += 1
    else:
        print(f"【測試二】❌ 預期 semantic-cache-shield，實際得到: {result['routing_decision']}\n")

    # 測試三：異常偵測任務 → 應路由至輿情觀測儀
    total += 1
    result = router.route("論壇今天突然炎上，聲量爆衝，需要即時警報通知")
    if result["routing_decision"] == "trend-anomaly-detector":
        print(f"【測試三】輿情異常偵測任務\n  路由決策: {result['routing_decision']} ✅\n  信心: {result['confidence']}\n")
        passed += 1
    else:
        print(f"【測試三】❌ 預期 trend-anomaly-detector，實際得到: {result['routing_decision']}\n")

    # 測試四：部署任務 → 應路由至熱部署儀
    total += 1
    result = router.route("把最新的報表自動推送到 GitHub 部署，發布至戰情看板")
    if result["routing_decision"] == "hot-deployer":
        print(f"【測試四】自動部署任務\n  路由決策: {result['routing_decision']} ✅\n  信心: {result['confidence']}\n")
        passed += 1
    else:
        print(f"【測試四】❌ 預期 hot-deployer，實際得到: {result['routing_decision']}\n")

    # 測試五：驗證任務 → 應路由至幻覺裁判
    total += 1
    result = router.route("AI 生成的戰報中有奇怪的英雄名稱，需要驗證準確性")
    if result["routing_decision"] == "hallucination-judge":
        print(f"【測試五】幻覺驗證任務\n  路由決策: {result['routing_decision']} ✅\n  信心: {result['confidence']}\n")
        passed += 1
    else:
        print(f"【測試五】❌ 預期 hallucination-judge，實際得到: {result['routing_decision']}\n")

    # 測試六：列出所有技能 → 應回傳 12 個（M1~M4 累計）
    total += 1
    all_skills = router.list_all_skills()
    if len(all_skills) == 12:
        print(f"【測試六】技能冊完整性 (預期 12 個，含 Milestone 4 新增)\n  實際: {len(all_skills)} 個 ✅\n")
        passed += 1
    else:
        print(f"【測試六】❌ 技能數量不符，實際: {len(all_skills)}\n")

    print("-" * 50)
    print(f"[{'✓' if passed == total else '✗'}] {passed}/{total} 測試通過")
    if passed == total:
        print("[✓] ALL TESTS PASSED - 智能任務路由器已就位，指揮大腦正式上線！")
    else:
        print("[!] 部分測試失敗，請檢查上方錯誤訊息")

if __name__ == "__main__":
    run_tests()
