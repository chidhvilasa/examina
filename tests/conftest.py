"""
Shared test environment. Set before any `examina.api` module is
imported so `get_engine()`'s test-mode detection and auth's env-var
reads see these values from the very first call.
"""

from __future__ import annotations

import os

os.environ.setdefault("EXAMINA_TEST_MODE", "1")
os.environ.setdefault("EXAMINA_INVITE_CODE", "test-invite-code")
os.environ.setdefault("EXAMINA_ADMIN_TOKEN", "test-admin-token")
os.environ.setdefault("CLAMAV_MODE", "skip")
