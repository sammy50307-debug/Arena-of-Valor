import math
import sys
from typing import List, Dict, Union

# 強制 UTF-8
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class TrendAnomalyDetector:
    """
    輿情核爆觀測儀
    透過計算過去時間段的平均值 (Mean) 與標準差 (StdDev)，算出最新資料點的 Z-Score。
    """
    def __init__(self, red_alert_threshold: float = 3.0, yellow_alert_threshold: float = 2.0):
        self.red_alert_threshold = red_alert_threshold
        self.yellow_alert_threshold = yellow_alert_threshold

    def calculate_stats(self, historical_data: List[float]) -> Dict[str, float]:
        """計算平均值與標準差"""
        if not historical_data:
            return {"mean": 0.0, "std_dev": 0.0}
        
        n = len(historical_data)
        mean = sum(historical_data) / n
        
        if n < 2:
            return {"mean": mean, "std_dev": 0.0}
            
        variance = sum((x - mean) ** 2 for x in historical_data) / (n - 1)
        std_dev = math.sqrt(variance)
        
        return {"mean": mean, "std_dev": std_dev}

    def detect(self, historical_data: List[float], current_value: float) -> Dict[str, Union[float, str, bool]]:
        """針對最新的單點數值，診斷是否引發警報"""
        stats = self.calculate_stats(historical_data)
        mean = stats["mean"]
        std_dev = stats["std_dev"]
        
        # 避免分母為 0 的極端情況 (代表過去數據毫無波動)，此時若現在突然爆衝，則給予無限大的 Z-score
        if std_dev == 0:
            if current_value > mean:
                z_score = 999.0 
            elif current_value < mean:
                z_score = -999.0
            else:
                z_score = 0.0
        else:
            z_score = (current_value - mean) / std_dev

        is_red_alert = z_score >= self.red_alert_threshold
        is_yellow_alert = not is_red_alert and (z_score >= self.yellow_alert_threshold)

        severity = "NORMAL"
        if is_red_alert:
            severity = "RED_ALERT (輿情核爆)"
        elif is_yellow_alert:
            severity = "YELLOW_ALERT (異常增溫)"

        return {
            "current_value": current_value,
            "baseline_mean": round(mean, 2),
            "baseline_std": round(std_dev, 2),
            "z_score": round(z_score, 2),
            "severity": severity,
            "trigger_alert": is_red_alert or is_yellow_alert
        }
