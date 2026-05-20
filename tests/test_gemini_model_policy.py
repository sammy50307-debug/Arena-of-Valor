from analyzer.gemini_client import GEMINI_MODELS


def test_p86_gemini_model_order_uses_gemini_3_stable_models():
    assert GEMINI_MODELS == [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ]


def test_p86_gemini_model_policy_excludes_deprecated_models():
    forbidden_models = {
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    }

    assert forbidden_models.isdisjoint(GEMINI_MODELS)
