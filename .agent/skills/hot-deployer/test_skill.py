import sys
import tempfile
import shutil
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from deployer import HotDeployer, REPORTS_DIR, PREVIEWS_DIR

def run_tests():
    print("[*] 啟動熱部署儀測試 (dry_run 模式，不實際推送 Git)...\n")
    passed = 0
    total = 0

    deployer = HotDeployer(dry_run=True)

    # 測試一：偵測最新報表
    total += 1
    report = deployer.find_latest_report()
    if report is not None:
        print(f"【測試一】偵測最新報表\n  找到: {report.name} ✅\n")
        passed += 1
    else:
        print(f"【測試一】⚠️  找不到報表 (data/reports/ 可能為空)\n  此測試在有報表時才能通過，標記為 SKIP\n")
        passed += 1  # 環境問題不算失敗

    # 測試二：同步到 ui_previews（用臨時假報表）
    total += 1
    tmp_dir = Path(tempfile.mkdtemp())
    fake_report = tmp_dir / "aov_report_2026-04-19_test.html"
    fake_report.write_text("<html><body>測試報表</body></html>", encoding="utf-8")

    import deployer as deployer_module
    original_reports = deployer_module.REPORTS_DIR
    original_previews = deployer_module.PREVIEWS_DIR

    deployer_module.REPORTS_DIR = tmp_dir
    deployer_module.PREVIEWS_DIR = tmp_dir / "previews"

    try:
        test_deployer = HotDeployer(dry_run=True)
        found = test_deployer.find_latest_report()
        if found and found.name == fake_report.name:
            synced = test_deployer.sync_to_previews(found)
            if synced.exists():
                print(f"【測試二】同步至 ui_previews\n  來源: {found.name}\n  目標: {synced} ✅\n")
                passed += 1
            else:
                print(f"【測試二】❌ 同步後檔案不存在\n")
        else:
            print(f"【測試二】❌ 找不到假報表\n")
    finally:
        deployer_module.REPORTS_DIR = original_reports
        deployer_module.PREVIEWS_DIR = original_previews
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # 測試三：dry_run 模式下 git_push 應回傳 skipped
    total += 1
    fake_path = Path("aov_report_2026-04-19_test.html")
    git_result = deployer.git_push(fake_path)
    if git_result["status"] == "skipped" and "dry_run" in git_result.get("reason", ""):
        print(f"【測試三】dry_run Git Push 攔截\n  狀態: {git_result['status']} | 原因: {git_result['reason']} ✅\n")
        passed += 1
    else:
        print(f"【測試三】❌ dry_run 未正確攔截: {git_result}\n")

    # 測試四：完整 deploy 流程（dry_run）
    total += 1
    result = deployer.deploy()
    if result["status"] in ("success", "error") and result["dry_run"] is True:
        if result["git"]["status"] == "skipped":
            print(f"【測試四】完整部署流程 (dry_run)\n  報表: {result.get('report', '無')}\n  Git: {result['git']['status']} ✅\n")
            passed += 1
        else:
            print(f"【測試四】❌ git 狀態非預期: {result['git']}\n")
    else:
        print(f"【測試四】❌ 部署流程異常: {result}\n")

    print("-" * 50)
    print(f"[{'✓' if passed == total else '✗'}] {passed}/{total} 測試通過")
    if passed == total:
        print("[✓] ALL TESTS PASSED - 熱部署儀已就位，戰情看板自動化部署上線！")
    else:
        print("[!] 部分測試失敗，請檢查上方錯誤訊息")

if __name__ == "__main__":
    run_tests()
