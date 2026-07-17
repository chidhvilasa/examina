"""Tests for src/examina/api/rate_limit.py."""

from __future__ import annotations

from slowapi import Limiter

from examina.api.rate_limit import (
    ADMIN_RATE_LIMIT,
    ANALYZE_RATE_LIMIT,
    FEEDBACK_RATE_LIMIT,
    INCORRECT_RATE_LIMIT,
    REPORT_RATE_LIMIT,
    get_limiter,
)


class TestGetLimiter:
    def test_returns_limiter_instance(self) -> None:
        assert isinstance(get_limiter(), Limiter)


class TestRateLimitConstants:
    def test_analyze_rate_limit(self) -> None:
        assert ANALYZE_RATE_LIMIT == "10/minute"

    def test_report_rate_limit(self) -> None:
        assert REPORT_RATE_LIMIT == "60/minute"

    def test_feedback_rate_limit(self) -> None:
        assert FEEDBACK_RATE_LIMIT == "5/minute"

    def test_incorrect_rate_limit(self) -> None:
        assert INCORRECT_RATE_LIMIT == "3/minute"

    def test_admin_rate_limit(self) -> None:
        assert ADMIN_RATE_LIMIT == "30/minute"
