import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Simple in-memory sliding-window limiter (per IP, per process)."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.hits = defaultdict(deque)

    def __call__(self, request: Request):
        ip = client_ip(request)
        now = time.monotonic()
        hits = self.hits[ip]

        while hits and now - hits[0] > self.window:
            hits.popleft()

        if len(hits) >= self.max_requests:
            retry_after = int(self.window - (now - hits[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)