"""URL 正規化工具 (P65-L1)：去除追蹤參數、統一格式，供 dedup 使用。"""

from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

_STRIP_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "utm_id", "utm_ref",
    "fbclid", "gclid", "msclkid", "dclid",
    "ref", "referrer", "source",
    "_ga", "_gl",
})


def normalize(url: str) -> str:
    """
    正規化 URL：
    - 去追蹤 query params（utm_*, fbclid 等）
    - 去尾部斜線（路徑非根目錄時）
    - 小寫 scheme + host
    """
    if not url or url == "#":
        return url

    try:
        parsed = urlparse(url)
    except Exception:
        return url

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"

    clean_qs = urlencode(
        [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() not in _STRIP_PARAMS]
    )

    return urlunparse((scheme, netloc, path, parsed.params, clean_qs, ""))
