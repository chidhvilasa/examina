"""
API package — FastAPI application.
"""

from examina.api.auth import verify_admin_token, verify_invite_code
from examina.api.database import (
    delete_expired_reports,
    delete_report,
    get_engine,
    get_report,
    get_session,
    save_report,
)
from examina.api.models import (
    AnalyzeResponse,
    ErrorResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    IncorrectAnalysisRequest,
    IncorrectAnalysisResponse,
    ReportResponse,
)
from examina.api.rate_limit import (
    ADMIN_RATE_LIMIT,
    ANALYZE_RATE_LIMIT,
    FEEDBACK_RATE_LIMIT,
    INCORRECT_RATE_LIMIT,
    REPORT_RATE_LIMIT,
    get_limiter,
)

__all__ = [
    "ADMIN_RATE_LIMIT",
    "ANALYZE_RATE_LIMIT",
    "FEEDBACK_RATE_LIMIT",
    "INCORRECT_RATE_LIMIT",
    "REPORT_RATE_LIMIT",
    "AnalyzeResponse",
    "ErrorResponse",
    "FeedbackRequest",
    "FeedbackResponse",
    "HealthResponse",
    "IncorrectAnalysisRequest",
    "IncorrectAnalysisResponse",
    "ReportResponse",
    "delete_expired_reports",
    "delete_report",
    "get_engine",
    "get_limiter",
    "get_report",
    "get_session",
    "save_report",
    "verify_admin_token",
    "verify_invite_code",
]
