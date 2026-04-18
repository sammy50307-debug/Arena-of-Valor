"""
API Quota Guardian — 付費搜尋 API 額度守衛。

事前主動追蹤 Tavily（或其他 provider）月用量，
達 80% 警告、95% 建議切換至免費備援源。
狀態持久化至 data/quota_state.json，月初自動 rollover。
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path(__file__).resolve().parents[4] / "data" / "quota_state.json"

WARN_THRESHOLD = 0.80      # 80% 警告
CRITICAL_THRESHOLD = 0.95  # 95% 建議切換備援


class APIQuotaGuardian:
    """
    付費搜尋 API 月額度守衛。

    使用方式：
        g = APIQuotaGuardian(provider="tavily", monthly_limit=1000)
        g.record(1)                    # 每次 API 呼叫後記錄
        if g.should_fallback(): ...    # 瀑布鏈呼叫前檢查
        info = g.status()              # 取得當前狀態
    """

    def __init__(
        self,
        provider: str = "tavily",
        monthly_limit: int = 1000,
        state_path: Optional[Path] = None,
    ):
        self.provider = provider
        self.monthly_limit = monthly_limit
        self.state_path = Path(state_path) if state_path else DEFAULT_STATE_PATH
        self.logger = logging.getLogger(f"{__name__}.APIQuotaGuardian[{provider}]")
        self._ensure_state()

    # ── 公開介面 ──────────────────────────────────────

    def record(self, count: int = 1) -> Dict:
        """記錄一次 API 呼叫（或一批 count 次）。"""
        self._rollover_if_needed()
        state = self._load_all()
        prov_state = state.setdefault(self.provider, self._fresh_provider_state())
        prov_state["used"] = int(prov_state.get("used", 0)) + int(count)
        prov_state["limit"] = self.monthly_limit
        prov_state["month"] = self._current_month()
        self._save_all(state)

        status = self._compute_status(prov_state)
        self._log_threshold_crossing(status)
        return status

    def status(self) -> Dict:
        """回傳當前額度狀態（不遞增 used）。"""
        self._rollover_if_needed()
        state = self._load_all()
        prov_state = state.get(self.provider) or self._fresh_provider_state()
        return self._compute_status(prov_state)

    def should_fallback(self) -> bool:
        """當使用率 >= CRITICAL_THRESHOLD 時回傳 True。"""
        return self.status()["percent"] >= CRITICAL_THRESHOLD * 100

    def reset(self) -> None:
        """手動重置當前 provider 的用量（供測試 / 新月份手動歸零用）。"""
        state = self._load_all()
        state[self.provider] = self._fresh_provider_state()
        self._save_all(state)

    # ── 內部工具 ──────────────────────────────────────

    def _current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def _fresh_provider_state(self) -> Dict:
        return {
            "month": self._current_month(),
            "used": 0,
            "limit": self.monthly_limit,
        }

    def _ensure_state(self) -> None:
        """確保狀態檔存在（若不存在則建立空檔）。"""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self.state_path.write_text("{}", encoding="utf-8")

    def _load_all(self) -> Dict:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_all(self, state: Dict) -> None:
        self.state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _rollover_if_needed(self) -> None:
        """若 state 中 month 與當前不同 → 歸零該 provider 用量。"""
        state = self._load_all()
        prov = state.get(self.provider)
        if prov and prov.get("month") != self._current_month():
            self.logger.info(
                f"[Guardian] 月份變更 {prov.get('month')} → {self._current_month()}，"
                f"{self.provider} 用量歸零"
            )
            state[self.provider] = self._fresh_provider_state()
            self._save_all(state)

    def _compute_status(self, prov_state: Dict) -> Dict:
        used = int(prov_state.get("used", 0))
        limit = int(prov_state.get("limit", self.monthly_limit)) or self.monthly_limit
        percent = round(used / limit * 100, 2) if limit > 0 else 0.0

        if percent >= CRITICAL_THRESHOLD * 100:
            verdict = "CRITICAL"
        elif percent >= WARN_THRESHOLD * 100:
            verdict = "WARN"
        else:
            verdict = "OK"

        return {
            "provider": self.provider,
            "month": prov_state.get("month", self._current_month()),
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used),
            "percent": percent,
            "verdict": verdict,
        }

    def _log_threshold_crossing(self, status: Dict) -> None:
        v = status["verdict"]
        if v == "CRITICAL":
            self.logger.warning(
                f"[Guardian] 🚨 CRITICAL: {self.provider} 已用 "
                f"{status['used']}/{status['limit']} ({status['percent']}%)，"
                f"瀑布鏈將自動跳過此源。"
            )
        elif v == "WARN":
            self.logger.warning(
                f"[Guardian] ⚠️  WARN: {self.provider} 已用 "
                f"{status['used']}/{status['limit']} ({status['percent']}%)"
            )


# ── 直接執行測試 ──────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    g = APIQuotaGuardian(provider="tavily", monthly_limit=1000)
    print("目前狀態:", json.dumps(g.status(), ensure_ascii=False, indent=2))
