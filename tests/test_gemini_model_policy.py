import httpx

from analyzer.gemini_client import (
    GEMINI_MODELS,
    _masked_url,
    _redact_secret_text,
    _safe_error_message,
)


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


def test_secret_redaction_masks_google_api_key_in_urls():
    fake_key = "AIza" + "A" * 35
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={fake_key}"

    masked = _masked_url(url)

    assert fake_key not in masked
    assert "key=***" in masked


def test_secret_redaction_masks_keys_inside_httpx_error_message():
    fake_key = "AIza" + "B" * 35
    request = httpx.Request(
        "POST",
        f"https://generativelanguage.googleapis.com/v1beta/models?key={fake_key}",
    )
    response = httpx.Response(429, request=request)
    exc = httpx.HTTPStatusError(
        f"Client error '429 Too Many Requests' for url '{request.url}'",
        request=request,
        response=response,
    )

    safe = _safe_error_message(exc)

    assert fake_key not in safe
    assert "key=***" in safe


def test_secret_redaction_masks_openrouter_like_values():
    fake_key = "sk-" + "or-v1-" + "c" * 40

    redacted = _redact_secret_text(f"provider failed: {fake_key}")

    assert fake_key not in redacted
    assert "***REDACTED***" in redacted
