import os
import sys

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from anomaly_detector import TrendAnomalyDetector

def run_test():
    print("[*] 啟動輿情核爆觀測儀壓力測試...\n")
    
    detector = TrendAnomalyDetector(red_alert_threshold=3.0, yellow_alert_threshold=2.0)

    # 模擬過去 7 天非常平穩的「芽芽」討論聲量 (每天大約 50 篇正常抱怨)
    history_baseline = [48, 52, 50, 47, 53, 49, 51]
    
    print(f"[*] 歷史 7 天平穩基準數據: {history_baseline}")

    # 測試一：今日正常聲量
    today_normal = 55
    res1 = detector.detect(history_baseline, today_normal)
    print("\n【測試一】今日討論量: 55 篇 (預期正常)")
    print(f"   => 平均值: {res1['baseline_mean']} | 標準差: {res1['baseline_std']}")
    print(f"   => 測得 Z-Score: {res1['z_score']}")
    print(f"   => 警報狀態: [{res1['severity']}] (Trigger: {res1['trigger_alert']})")

    # 測試二：官方宣布芽芽增強，引發玩家炎上核爆！(聲量飆升至 200 篇)
    today_nuke = 200
    res2 = detector.detect(history_baseline, today_nuke)
    print("\n【測試二】今日討論量: 200 篇 (預期引發 RED_ALERT 輿情核爆)")
    print(f"   => 測得 Z-Score: {res2['z_score']}")
    print(f"   => 警報狀態: [{res2['severity']}] (Trigger: {res2['trigger_alert']})")
    
    if res2['trigger_alert'] and "RED_ALERT" in res2['severity']:
         print("\n[✓] ALL TESTS PASSED - Z-Score 防禦機制觸發成功，觀測儀上線！")
    else:
         print("\n[-] 測試失敗：未能正確捕捉異常離群值。")

if __name__ == "__main__":
    run_test()
