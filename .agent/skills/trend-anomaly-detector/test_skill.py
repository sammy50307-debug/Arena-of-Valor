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
    
    # 模擬過去 14 天的正常聲量波型 (平靜時期)
    historical_volumes = [42, 38, 45, 50, 41, 39, 47, 44, 43, 46, 40, 48, 42, 41]

    # ── 測試一：今日聲量正常波動 ──────────────────────────
    print("【測試一】今日聲量正常：47 篇 (預期 NORMAL)")
    result = detector.detect(historical_volumes, current_value=47)
    print(f"  基準平均值: {result['baseline_mean']} | 標準差: {result['baseline_std']}")
    print(f"  Z-Score: {result['z_score']} | 判定: {result['severity']}")
    assert result['severity'] == "NORMAL", "❌ 測試一失敗"
    print("  ✅ 通過\n")
    
    # ── 測試二：出現黃色警戒區域 ──────────────────────────
    # 均値=43.29, 標準差=3.54, 黃色區 = 2σ~3σ => ~50.4~54.0
    print("【測試二】今日聲量輕微爆衝：51 篇 (預期 YELLOW_ALERT)")
    result = detector.detect(historical_volumes, current_value=51)
    print(f"  Z-Score: {result['z_score']} | 判定: {result['severity']}")
    assert "YELLOW" in result['severity'], "❌ 測試二失敗"
    print("  ✅ 通過\n")

    # ── 測試三：觸發核爆級警報 ─────────────────────────────
    print("【測試三】論壇突然暴動！今日聲量急速飆升：300 篇 (預期 RED_ALERT)")
    result = detector.detect(historical_volumes, current_value=300)
    print(f"  Z-Score: {result['z_score']} | 判定: {result['severity']}")
    assert "RED" in result['severity'], "❌ 測試三失敗"
    print("  ✅ 通過\n")
    
    # ── 測試四：情緒分數崩潰警報 (負面聲量判定) ───────────
    print("【測試四】過去情緒分數穩定在 +0.6，今日突然崩落至 -0.2 (預期 RED_ALERT)")
    historical_sentiments = [0.62, 0.58, 0.65, 0.60, 0.61, 0.59, 0.63, 0.62, 0.64, 0.58]
    result = detector.detect(historical_sentiments, current_value=-0.2)
    print(f"  基準情緒均值: {result['baseline_mean']} | 今日數值: -0.2")
    print(f"  Z-Score: {result['z_score']} | 判定: {result['severity']}")
    assert "RED" in result['severity'], "❌ 測試四失敗"
    print("  ✅ 通過\n")

    print("[✓] ALL TESTS PASSED - 輿情核爆觀測儀已就位，隨時可攔截炎上事件！")

if __name__ == "__main__":
    run_test()
