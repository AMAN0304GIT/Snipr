import secrets
import string
import ipaddress
from datetime import datetime, timezone
from typing import Optional, Tuple
from urllib.parse import urlparse

ALPHABET = string.ascii_letters + string.digits  # Base62
RESERVED_CODES = {"api", "docs", "redoc", "openapi.json", "health", "favicon.ico"}


def generate_code(length: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite returns naive datetimes; make them timezone-aware (UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_user_agent(ua: str) -> Tuple[str, str]:
    s = (ua or "").lower()

    if "ipad" in s or "tablet" in s or ("android" in s and "mobile" not in s):
        device = "Tablet"
    elif "mobile" in s or "iphone" in s or "android" in s:
        device = "Mobile"
    else:
        device = "Desktop"

    if "edg/" in s or "edge" in s:
        browser = "Edge"
    elif "opr/" in s or "opera" in s:
        browser = "Opera"
    elif "firefox" in s or "fxios" in s:
        browser = "Firefox"
    elif "chrome" in s or "crios" in s:
        browser = "Chrome"
    elif "safari" in s:
        browser = "Safari"
    else:
        browser = "Other"

    return device, browser


def referrer_domain(ref: Optional[str]) -> str:
    if not ref:
        return "Direct"
    return urlparse(ref).netloc or "Direct"

def validate_target_url(url: str, own_host: Optional[str]) -> Optional[str]:
    """Return an error message if the URL must not be shortened, else None."""
    if len(url) > 2048:
        return "URL is too long (max 2048 characters)"

    host = (urlparse(url).hostname or "").lower()
    if not host:
        return "Invalid URL"
    if own_host and host == own_host.lower():
        return "You can't shorten a Snipr link"
    if host == "localhost" or host.endswith(".local"):
        return "Local addresses can't be shortened"

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None  # a normal domain name

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
        return "Private IP addresses can't be shortened"
    return None