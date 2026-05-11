"""
Smart Task Router — L2 路由引擎（P71.6）
讀取 skills/registry.json（S1 schema），對輸入 query 計算每個 skill 的信心分數，
依閾值決定 AUTO / CONFIRM / NO_MATCH 動作。
"""
import json
import os
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 預設 registry 路徑：從 scripts/ 往上 5 層到專案根 → skills/registry.json
_DEFAULT_REGISTRY = (
    Path(__file__).parent.parent.parent.parent.parent / "skills" / "registry.json"
)

# 信心閾值（D3 決定）
THRESHOLD_AUTO = 0.9       # ≥ 0.9 → 直接執行
THRESHOLD_CONFIRM = 0.7    # 0.7~0.89 → 詢問主公
# < 0.7 → NO_MATCH，不觸發


def _is_plain() -> bool:
    return bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()


class SmartTaskRouter:
    """
    L2 路由引擎：純 Python 規則匹配，不呼叫 LLM，不燒 token。
    signal 欄位優先序：trigger_keywords（強）> when_to_use（弱）> when_NOT_to_use（負）。
    """

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = Path(registry_path) if registry_path else _DEFAULT_REGISTRY
        self.skills: list[dict] = []
        self._load_registry()

    def _load_registry(self) -> None:
        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)
            self.skills = data.get("skills", [])
        except FileNotFoundError:
            self.skills = []
        except json.JSONDecodeError:
            self.skills = []

    # ------------------------------------------------------------------
    # 信心分數計算
    # ------------------------------------------------------------------

    def _compute_confidence(self, skill: dict, query: str) -> float:
        q = query.lower()
        score = 0.0

        # 強匹配：trigger_keywords，每個精確命中 +0.2
        for kw in skill.get("trigger_keywords", []):
            if kw.lower() in q:
                score += 0.2

        # 弱匹配：when_to_use，每條描述中 ≥2 個關鍵詞命中 +0.05
        for use_case in skill.get("when_to_use", []):
            tokens = [t for t in use_case.lower().split() if len(t) >= 2]
            if sum(1 for t in tokens if t in q) >= 2:
                score += 0.05

        # 負向：when_NOT_to_use，有命中 -0.2（避免誤觸）
        for excl in skill.get("when_NOT_to_use", []):
            tokens = [t for t in excl.lower().split() if len(t) >= 3]
            if sum(1 for t in tokens if t in q) >= 2:
                score -= 0.2

        return round(min(max(score, 0.0), 1.0), 2)

    # ------------------------------------------------------------------
    # 核心路由
    # ------------------------------------------------------------------

    def route(self, query: str, top_n: int = 3) -> dict[str, Any]:
        """
        回傳路由決策字典。
        action: AUTO | CONFIRM | NO_MATCH
        """
        if not query.strip():
            return {"error": "輸入描述為空", "action": "NO_MATCH", "candidates": []}

        scored = []
        for skill in self.skills:
            if skill.get("status") in ("archived",):
                continue
            conf = self._compute_confidence(skill, query)
            if conf > 0:
                scored.append({
                    "name": skill["name"],
                    "confidence": conf,
                    "description": skill.get("description", ""),
                    "type": skill.get("type", ""),
                    "status": skill.get("status", ""),
                    "entry_points": skill.get("entry_points", {}),
                })

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        candidates = scored[:top_n]

        best = candidates[0] if candidates else None
        if best is None or best["confidence"] < THRESHOLD_CONFIRM:
            action = "NO_MATCH"
        elif best["confidence"] >= THRESHOLD_AUTO:
            action = "AUTO"
        else:
            action = "CONFIRM"

        return {
            "query": query,
            "action": action,
            "best_match": best,
            "confidence": best["confidence"] if best else 0.0,
            "candidates": candidates,
            "registry_path": str(self.registry_path),
        }

    def list_skills(self) -> list[dict]:
        """列出所有非歸檔 skill 的簡要資訊。"""
        return [
            {
                "name": s["name"],
                "status": s.get("status", ""),
                "description": s.get("description", ""),
                "trigger_keywords": s.get("trigger_keywords", []),
            }
            for s in self.skills
            if s.get("status") not in ("archived",)
        ]

    # ------------------------------------------------------------------
    # V1 觸發塊格式化
    # ------------------------------------------------------------------

    def format_v1_block(
        self,
        skill_name: str,
        trigger_reason: str,
        confidence: float,
        action: str,
        source: str = "smart-task-router (L2)",
    ) -> str:
        """
        輸出 V1 觸發塊。plain 模式（NO_COLOR=1 / 非 TTY）去掉框線。
        """
        action_label = {
            "AUTO": f"直接執行 {skill_name}",
            "CONFIRM": f"待主公確認後執行 {skill_name} [Y/n]",
            "NO_MATCH": "無高信心匹配，不觸發",
        }.get(action, action)

        if _is_plain():
            return (
                f"[{skill_name} 已觸發] "
                f"觸發理由: {trigger_reason} "
                f"信心: {confidence:.2f} "
                f"來源: {source} "
                f"動作: {action_label}"
            )
        return (
            f"🪧 [{skill_name} 已觸發]\n"
            f"├─ 觸發理由：{trigger_reason}\n"
            f"├─ 信心分數：{confidence:.2f}\n"
            f"├─ 來源層：{source}\n"
            f"└─ 動作：{action_label}"
        )
