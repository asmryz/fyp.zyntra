"""
Simple in-memory rate limiting for sensitive authentication endpoints.

This works for a single backend process (the normal setup for this project).
If the backend is ever run with several worker processes, each process keeps
its own counters. Verification and reset codes also have database-backed
attempt limits, which do not depend on this module.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = defaultdict(deque)
        self._lock = Lock()

    def _drop_old_hits(self, hits, now):
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

    def check(self, key: str):
        """Raise 429 if `key` has already reached the limit (does not count as a hit)."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            self._drop_old_hits(hits, now)
            if not hits:
                # Forget keys with no recent hits so the table does not grow forever
                del self._hits[key]
                return
            if len(hits) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - hits[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many attempts. Please try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

    def record(self, key: str):
        with self._lock:
            self._hits[key].append(time.monotonic())

    def reset(self, key: str):
        with self._lock:
            self._hits.pop(key, None)

    def __call__(self, request: Request):
        """Use as a FastAPI dependency: limits requests per client IP and path."""
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        self.check(key)
        self.record(key)


# Requests per IP address to each auth endpoint
auth_ip_limiter = RateLimiter(max_requests=20, window_seconds=300)
# Failed logins per email address
failed_login_limiter = RateLimiter(max_requests=5, window_seconds=900)
# AI assistant questions per student (each can keep the AI service busy for a while)
assistant_limiter = RateLimiter(max_requests=10, window_seconds=60)
