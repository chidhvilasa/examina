"""API request/response models — see specs/REPORT_SCHEMA_v1.0.md for the underlying report shape."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnalyzeResponse(BaseModel):
    report_id: str
    file_hash: str
    file_type: str
    status: Literal["complete", "failed"]
    verdict: str
    confidence_label: str
    overall_confidence: float
    active_hypotheses: int
    unresolved_contradictions: int
    natural_language_summary: str
    recommendation: str
    what_would_change: str
    report_url: str
    expires_at: str


class ReportResponse(BaseModel):
    report_id: str
    file_hash: str
    file_type: str
    analysis_timestamp: str
    expires_at: str
    report: dict[str, object]


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    version: str
    database_status: Literal["ok", "error"]
    ocr_available: bool
    disk_free_gb: float
    memory_free_mb: float
    uptime_seconds: float
    timestamp: str


class FeedbackRequest(BaseModel):
    report_id: str | None = None
    understandability_score: int | None = None
    most_useful_section: (
        Literal["assessment", "history", "evidence", "confidence", "none"] | None
    ) = None
    least_useful_section: (
        Literal["assessment", "history", "evidence", "confidence", "none"] | None
    ) = None
    changed_assessment: (
        Literal["yes_significantly", "yes_somewhat", "no", "unsure_before_and_after"] | None
    ) = None
    would_use_in_workflow: Literal["yes", "maybe", "no"] | None = None
    missing_information: str | None = Field(default=None, max_length=500)

    @field_validator("understandability_score")
    @classmethod
    def _validate_understandability_score(cls, value: int | None) -> int | None:
        if value is not None and not (1 <= value <= 5):
            raise ValueError("understandability_score must be between 1 and 5")
        return value


class FeedbackResponse(BaseModel):
    feedback_id: int
    message: str


class IncorrectAnalysisRequest(BaseModel):
    report_id: str
    user_comment: str | None = Field(default=None, max_length=500)


class IncorrectAnalysisResponse(BaseModel):
    submission_id: int
    message: str
