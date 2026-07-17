"""
Rate limiting — slowapi with an in-memory backend.

The in-memory backend tracks limits per-process. It is adequate for a
single-worker development/beta deployment; a multi-worker production
deployment needs a shared backend (Redis) so limits are enforced across
workers rather than reset per-process — see specs/TECH_DEBT.md.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

ANALYZE_RATE_LIMIT = "10/minute"
REPORT_RATE_LIMIT = "60/minute"
FEEDBACK_RATE_LIMIT = "5/minute"
INCORRECT_RATE_LIMIT = "3/minute"
ADMIN_RATE_LIMIT = "30/minute"

_limiter: Limiter | None = None


def get_limiter() -> Limiter:
    global _limiter
    if _limiter is None:
        _limiter = Limiter(key_func=get_remote_address)
    return _limiter
