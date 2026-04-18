import json
import sys
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REGISTRY_PATH = Path(__file__).parent.parent / "resources" / "skill_registry.json"


class SmartTaskRouter:
    """
    智能任務路由器
    分析輸入描述，以關鍵字比對方式判斷最適合的特種兵技能。
    """

    def __init__(self):
        self.skills: List[Dict] = []
        self.task_type_map: Dict[str, str] = {}
        self._load_registry()

    def _load_registry(self):
        try:
            with open(REGISTRY_PATH, encoding="utf-8") as f:
                data = json.load(f)
            self.skills = data.get("skills", [])
            self.task_type_map = data.get("task_type_map", {})
        except Exception as e:
            self.skills = []

    def _score_skill(self, skill: Dict, query: str) -> int:
        """計算一個 skill 與輸入 query 的關鍵字匹配分數"""
        query_lower = query.lower()
        score = 0
        for kw in skill.get("keywords", []):
            if kw.lower() in query_lower:
                score += 1
        return score

    def route(self, query: str, top_n: int = 3) -> Dict[str, Any]:
        """
        輸入任務描述，回傳最適合的特種兵推薦清單。
        top_n: 回傳前 N 名候選技能
        """
        if not query.strip():
            return {"error": "輸入描述為空，無法路由", "recommendations": []}

        scored = []
        for skill in self.skills:
            score = self._score_skill(skill, query)
            if score > 0:
                scored.append({
                    "skill_id": skill["id"],
                    "skill_name": skill["name"],
                    "milestone": skill["milestone"],
                    "phase": skill["phase"],
                    "task_type": skill["task_type"],
                    "task_type_desc": self.task_type_map.get(skill["task_type"], ""),
                    "description": skill["description"],
                    "match_score": score
                })

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        recommendations = scored[:top_n]

        best = recommendations[0] if recommendations else None
        routing_decision = best["skill_id"] if best else "unknown"
        task_type = best["task_type"] if best else "unknown"

        return {
            "query": query,
            "routing_decision": routing_decision,
            "task_type": task_type,
            "task_type_desc": self.task_type_map.get(task_type, "未知任務類型"),
            "confidence": "HIGH" if best and best["match_score"] >= 2 else "LOW",
            "recommendations": recommendations,
            "total_candidates": len(scored)
        }

    def list_all_skills(self) -> List[Dict]:
        """列出所有已登記的特種兵"""
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "milestone": s["milestone"],
                "phase": s["phase"],
                "task_type": s["task_type"],
                "description": s["description"]
            }
            for s in self.skills
        ]
