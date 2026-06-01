"""P105 provider registry — 把 provider 名稱對應到具體的 LLMProviderClient。

換首發 provider 只需把 ``config.PRIMARY_PROVIDER`` 設成下方 ``REGISTRY`` 註冊過的
名稱（或在 ``.env`` 設 ``PRIMARY_PROVIDER``）。``build_provider()`` 負責吸收各
client ``__init__`` 簽名的差異：

* ``GeminiClient`` 自帶 ``CacheManager`` 與 P90 budget ledger，不接受外部注入。
* ``LLMClient``（OpenAI）接受外部注入的 ``cache_manager`` 與 ``model``。

新增 provider 時：在 ``REGISTRY`` 註冊 name→class，並在 ``build_provider`` 補一個
建構分支（處理該 client 的 ``__init__`` 簽名）。
"""

from __future__ import annotations

from typing import Any, Optional

from analyzer.gemini_client import GeminiClient
from analyzer.llm_client import LLMClient

# name → 具體 client class（接手者一眼看有哪些 provider 可當首發/fallback）
REGISTRY = {
    "gemini": GeminiClient,
    "openai": LLMClient,
}


def build_provider(
    name: str,
    *,
    cache_manager: Optional[Any] = None,
    model: Optional[str] = None,
):
    """依名稱實例化已註冊的 provider client，吸收各 client 的 __init__ 簽名差異。

    Args:
        name: ``REGISTRY`` 註冊過的 provider 名稱（大小寫不敏感）。
        cache_manager: 注入用的快取管理器（僅對支援注入的 client 有效，如 OpenAI）。
        model: 指定 model id（僅對支援的 client 有效，如 OpenAI）；空字串視為不指定。

    Raises:
        ValueError: 名稱未註冊。
    """
    key = (name or "").strip().lower()
    if key not in REGISTRY:
        raise ValueError(
            f"Unknown provider {name!r}; registered providers: {sorted(REGISTRY)}"
        )
    if key == "gemini":
        # GeminiClient 自帶 CacheManager + P90 budget ledger，不注入外部 cache。
        return GeminiClient()
    if key == "openai":
        return LLMClient(cache_manager=cache_manager, model=model or None)
    # 防呆：REGISTRY 有註冊但忘了補建構分支。
    raise ValueError(f"Provider {key!r} registered but has no builder branch")
