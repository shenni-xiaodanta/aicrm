"""URL 工具。"""
from urllib.parse import urlsplit


def _parts(value):
    return urlsplit((value or "").strip())


def is_origin(value):
    """是否为 http(s) 站点根地址（只有协议 + 域名，可带端口）。"""
    parts = _parts(value)
    return (
        parts.scheme in ("http", "https")
        and bool(parts.netloc)
        and parts.path in ("", "/")
        and not parts.query
        and not parts.fragment
    )


def has_path(value):
    """是否为带非根路径的 http(s) 地址。"""
    parts = _parts(value)
    return (
        parts.scheme in ("http", "https")
        and bool(parts.netloc)
        and parts.path not in ("", "/")
    )


def normalize_source(base_domain, list_url):
    """base_domain / list_url 填反时自动交换。"""
    base = (base_domain or "").strip().rstrip("/")
    url = (list_url or "").strip()
    if is_origin(url) and has_path(base):
        return url, base
    return base, url


def origin(value):
    """提取 http(s) 站点根地址，失败返回空字符串。"""
    parts = _parts(value)
    if parts.scheme in ("http", "https") and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return ""
