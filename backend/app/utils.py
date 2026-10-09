import secrets
import string
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