"""P105.1 S3.1 B 架構矩陣鎖：PROVIDER_CHAIN（provider:model 鏈）+ per-model budget。

驗 config 解析、``build_default_llm_client`` 組鏈、``OpenRouterClient`` per-model
budget 隔離。不真發 API：對 client 型別/屬性斷言；OpenRouter 需非空 key 故注入測試 key。
向後相容鐵律：無 PROVIDER_CHAIN 時退回 S1 路徑（不破 test_provider_switch.py 基線）。
"""

from pathlib import Path

import config


# ── config 解析：PROVIDER_CHAIN ──────────────────────────
class TestParseProviderChain:
    def test_parses_provider_model_levels(self):
        chain = config.parse_provider_chain(
            "openrouter:deepseek/deepseek-chat, openrouter:deepseek/deepseek-r1, gemini"
        )
        assert chain == [
            ("openrouter", "deepseek/deepseek-chat"),
            ("openrouter", "deepseek/deepseek-r1"),
            ("gemini", None),
        ]

    def test_empty_returns_empty_list(self):
        assert config.parse_provider_chain("") == []
        assert config.parse_provider_chain("   ") == []

    def test_model_slash_not_split_by_colon(self):
        # partition(":")：只切第一個冒號，model 的 / 不是分隔符。
        assert config.parse_provider_chain("openrouter:deepseek/deepseek-chat") == [
            ("openrouter", "deepseek/deepseek-chat")
        ]

    def test_provider_without_model_is_none(self):
        assert config.parse_provider_chain("gemini, openai") == [
            ("gemini", None),
            ("openai", None),
        ]

    def test_skips_blank_levels(self):
        assert config.parse_provider_chain("gemini, , openai,") == [
            ("gemini", None),
            ("openai", None),
        ]


# ── config 解析：OPENROUTER_MODEL_BUDGETS ────────────────
class TestParseModelBudgets:
    def test_parses_model_budgets(self):
        assert config.parse_openrouter_model_budgets(
            "deepseek/deepseek-chat:80000, deepseek/deepseek-r1:20000"
        ) == {"deepseek/deepseek-chat": 80000, "deepseek/deepseek-r1": 20000}

    def test_empty_returns_empty_dict(self):
        assert config.parse_openrouter_model_budgets("") == {}

    def test_model_slash_preserved(self):
        # rpartition(":")：budget 取最右段，model 含 / 不被切錯。
        assert config.parse_openrouter_model_budgets("deepseek/deepseek-chat:80000") == {
            "deepseek/deepseek-chat": 80000
        }

    def test_skips_invalid_budget(self):
        assert config.parse_openrouter_model_budgets("a/b:notanumber, c/d:500") == {
            "c/d": 500
        }


# ── build_default_llm_client 組鏈 ────────────────────────
class TestBuildDefaultChain:
    def test_no_chain_falls_back_to_s1(self, monkeypatch):
        """無 PROVIDER_CHAIN → 退回 S1（primary = build_provider(PRIMARY_PROVIDER)）。"""
        monkeypatch.setattr(config, "PROVIDER_CHAIN", [])
        monkeypatch.setattr(config, "PRIMARY_PROVIDER", "gemini")
        monkeypatch.setattr(config, "PROVIDER_ROUTER_ENABLED", False)
        from analyzer.gemini_client import GeminiClient
        from analyzer.provider_router import build_default_llm_client

        client = build_default_llm_client()
        assert isinstance(client.primary, GeminiClient)

    def test_chain_primary_is_first_level(self, monkeypatch):
        """PROVIDER_CHAIN 首級＝首發，帶其指定 model。"""
        monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-test")
        monkeypatch.setattr(config, "PROVIDER_ROUTER_ENABLED", False)
        monkeypatch.setattr(
            config,
            "PROVIDER_CHAIN",
            [("openrouter", "deepseek/deepseek-chat"), ("gemini", None)],
        )
        from analyzer.provider_clients.openrouter_client import OpenRouterClient
        from analyzer.provider_router import build_default_llm_client

        client = build_default_llm_client()
        assert isinstance(client.primary, OpenRouterClient)
        assert client.primary.model == "deepseek/deepseek-chat"

    def test_chain_fallbacks_assembled_in_order(self, monkeypatch):
        """chain[1:] → 逐級 fallback，各帶自己的 model。"""
        monkeypatch.setattr(config, "OPENROUTER_API_KEY", "sk-test")
        monkeypatch.setattr(config, "PROVIDER_ROUTER_ENABLED", False)
        monkeypatch.setattr(
            config,
            "PROVIDER_CHAIN",
            [
                ("openrouter", "deepseek/deepseek-chat"),
                ("openrouter", "deepseek/deepseek-r1"),
                ("gemini", None),
            ],
        )
        from analyzer.gemini_client import GeminiClient
        from analyzer.provider_clients.openrouter_client import OpenRouterClient
        from analyzer.provider_router import build_default_llm_client

        client = build_default_llm_client()
        assert len(client.fallbacks) == 2
        assert isinstance(client.fallbacks[0], OpenRouterClient)
        assert client.fallbacks[0].model == "deepseek/deepseek-r1"
        assert isinstance(client.fallbacks[1], GeminiClient)


# ── OpenRouterClient per-model budget 隔離 ───────────────
class TestPerModelBudget:
    def test_distinct_models_distinct_state_files(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            config, "OPENROUTER_BUDGET_STATE_FILE", str(tmp_path / "openrouter_budget_state.json")
        )
        monkeypatch.setattr(config, "OPENROUTER_MODEL_BUDGETS", {})
        from analyzer.provider_clients.openrouter_client import OpenRouterClient

        c1 = OpenRouterClient(api_key="sk-test", model="deepseek/deepseek-chat")
        c2 = OpenRouterClient(api_key="sk-test", model="deepseek/deepseek-r1")
        f1, f2 = str(c1._budget_manager.state_path), str(c2._budget_manager.state_path)
        assert f1 != f2
        assert "deepseek_deepseek-chat" in f1
        assert "deepseek_deepseek-r1" in f2

    def test_model_budget_limit_from_config(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            config, "OPENROUTER_BUDGET_STATE_FILE", str(tmp_path / "s.json")
        )
        monkeypatch.setattr(config, "OPENROUTER_DAILY_BUDGET", 100000)
        monkeypatch.setattr(
            config, "OPENROUTER_MODEL_BUDGETS", {"deepseek/deepseek-chat": 80000}
        )
        from analyzer.provider_clients.openrouter_client import OpenRouterClient

        c = OpenRouterClient(api_key="sk-test", model="deepseek/deepseek-chat")
        assert c._budget_manager.max_daily_llm_calls == 80000

    def test_model_budget_falls_back_to_daily(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            config, "OPENROUTER_BUDGET_STATE_FILE", str(tmp_path / "s.json")
        )
        monkeypatch.setattr(config, "OPENROUTER_DAILY_BUDGET", 100000)
        monkeypatch.setattr(config, "OPENROUTER_MODEL_BUDGETS", {})
        from analyzer.provider_clients.openrouter_client import OpenRouterClient

        c = OpenRouterClient(api_key="sk-test", model="deepseek/deepseek-r1")
        assert c._budget_manager.max_daily_llm_calls == 100000

    def test_model_name_sanitized_no_path_traversal(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            config, "OPENROUTER_BUDGET_STATE_FILE", str(tmp_path / "openrouter_budget_state.json")
        )
        monkeypatch.setattr(config, "OPENROUTER_MODEL_BUDGETS", {})
        from analyzer.provider_clients.openrouter_client import OpenRouterClient

        c = OpenRouterClient(api_key="sk-test", model="../../etc/passwd")
        state = Path(c._budget_manager.state_path)
        # sanitize 後 / 被換成 _，state 檔仍落在 tmp_path 內（未逃出目錄）。
        assert state.parent == tmp_path

    def test_no_model_backward_compatible_single_file(self, monkeypatch, tmp_path):
        """無 model（空）→ 退回 S2 單一 state 檔 + OPENROUTER_DAILY_BUDGET。"""
        single = tmp_path / "openrouter_budget_state.json"
        monkeypatch.setattr(config, "OPENROUTER_BUDGET_STATE_FILE", str(single))
        monkeypatch.setattr(config, "OPENROUTER_DAILY_BUDGET", 100000)
        monkeypatch.setattr(config, "OPENROUTER_MODEL", "")
        from analyzer.provider_clients.openrouter_client import OpenRouterClient

        c = OpenRouterClient(api_key="sk-test", model="")
        assert Path(c._budget_manager.state_path) == single
        assert c._budget_manager.max_daily_llm_calls == 100000
