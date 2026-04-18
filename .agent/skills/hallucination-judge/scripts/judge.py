import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

WHITELIST_PATH = Path(__file__).parent.parent / "resources" / "hero_whitelist.json"

HALLUCINATION_PATTERNS = [
    r"勝率[為是達]?\s*[\d]{3,}%",       # 勝率超過 100%
    r"[-]?\d+\.\d+.*情緒.*[>＞]\s*1",   # 情緒分數 > 1
    r"討論量.*[增加上升]\s*\d{4,}",      # 單日討論量暴增萬篇以上（不合理）
]

NUMERIC_RULES = [
    {
        "name": "sentiment_score",
        "pattern": r'"sentiment_score"\s*:\s*(-?\d+\.?\d*)',
        "min": -1.0,
        "max": 1.0,
        "description": "情緒分數必須介於 -1.0 到 1.0 之間"
    },
    {
        "name": "win_rate_pct",
        "pattern": r'(?:勝率|win_rate)[^\d]*(\d+\.?\d*)\s*%',
        "min": 0.0,
        "max": 100.0,
        "description": "勝率百分比必須介於 0 到 100 之間"
    },
    {
        "name": "negative_ratio",
        "pattern": r'(?:負面|negative)[^\d]*(\d+\.?\d*)\s*%',
        "min": 0.0,
        "max": 100.0,
        "description": "負面比例必須介於 0 到 100 之間"
    }
]


class HallucinationJudge:
    """
    AI 幻覺裁判
    校驗 AI 生成的戰報文本，偵測不存在的英雄名稱與超出合理範圍的數值。
    """

    def __init__(self):
        self.hero_names: List[str] = []
        self._load_whitelist()

    def _load_whitelist(self):
        try:
            with open(WHITELIST_PATH, encoding="utf-8") as f:
                data = json.load(f)
            self.hero_names = data.get("all_names", [])
        except Exception as e:
            self.hero_names = ["芽芽", "皮皮"]

    def check_hero_names(self, text: str) -> Dict[str, Any]:
        """偵測文本中被標記為英雄但不在白名單內的名稱"""
        # 擷取常見英雄提及模式：「英雄 XXX」、「[英雄名]」
        suspected = re.findall(r'英雄[「『"\s]*([\w\u4e00-\u9fff]+)', text)
        suspected += re.findall(r'[\[【]([\w\u4e00-\u9fff]{2,6})[\]】]', text)

        unknown = [s for s in suspected if s not in self.hero_names]
        known = [s for s in suspected if s in self.hero_names]

        return {
            "suspected_hero_mentions": suspected,
            "known_heroes": known,
            "unknown_heroes": unknown,
            "passed": len(unknown) == 0
        }

    def check_numeric_bounds(self, text: str) -> Dict[str, Any]:
        """校驗文本中數值型指標是否在合理範圍"""
        violations = []
        for rule in NUMERIC_RULES:
            matches = re.findall(rule["pattern"], text, re.IGNORECASE)
            for match in matches:
                try:
                    val = float(match)
                    if not (rule["min"] <= val <= rule["max"]):
                        violations.append({
                            "field": rule["name"],
                            "value": val,
                            "expected_range": f"{rule['min']} ~ {rule['max']}",
                            "description": rule["description"]
                        })
                except ValueError:
                    pass

        return {
            "violations": violations,
            "passed": len(violations) == 0
        }

    def check_hallucination_patterns(self, text: str) -> Dict[str, Any]:
        """透過正規表達式偵測明顯幻覺敘述"""
        triggered = []
        for pattern in HALLUCINATION_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                triggered.append({"pattern": pattern, "matched": matches})

        return {
            "triggered_patterns": triggered,
            "passed": len(triggered) == 0
        }

    def judge(self, text: str) -> Dict[str, Any]:
        """
        整合三層校驗，輸出最終裁決報告。
        confidence_score: 0 (完全不可信) ~ 100 (完全可信)
        """
        hero_result = self.check_hero_names(text)
        numeric_result = self.check_numeric_bounds(text)
        pattern_result = self.check_hallucination_patterns(text)

        issues = []
        deduction = 0

        if not hero_result["passed"]:
            for name in hero_result["unknown_heroes"]:
                issues.append(f"[英雄幻覺] 未知英雄名稱：'{name}' 不在官方白名單中")
                deduction += 20

        if not numeric_result["passed"]:
            for v in numeric_result["violations"]:
                issues.append(f"[數值越界] {v['field']} = {v['value']}，應在 {v['expected_range']}")
                deduction += 25

        if not pattern_result["passed"]:
            for p in pattern_result["triggered_patterns"]:
                issues.append(f"[幻覺特徵] 偵測到可疑敘述：{p['matched']}")
                deduction += 15

        confidence_score = max(0, 100 - deduction)
        verdict = "PASS" if len(issues) == 0 else ("WARN" if confidence_score >= 60 else "FAIL")

        return {
            "verdict": verdict,
            "confidence_score": confidence_score,
            "issues": issues,
            "details": {
                "hero_check": hero_result,
                "numeric_check": numeric_result,
                "pattern_check": pattern_result
            }
        }
