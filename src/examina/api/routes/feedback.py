"""POST /feedback and POST /report-incorrect — unauthenticated, rate limited."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from examina.api.database import (
    FeedbackRecord,
    IncorrectAnalysisRecord,
    get_report,
    get_session,
)
from examina.api.models import (
    ErrorResponse,
    FeedbackRequest,
    FeedbackResponse,
    IncorrectAnalysisRequest,
    IncorrectAnalysisResponse,
)
from examina.api.rate_limit import FEEDBACK_RATE_LIMIT, INCORRECT_RATE_LIMIT, get_limiter

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = get_limiter()


@router.post("/feedback")
@limiter.limit(FEEDBACK_RATE_LIMIT)
async def submit_feedback(
    request: Request,
    feedback: FeedbackRequest,
    session: Session = Depends(get_session),
) -> FeedbackResponse:
    try:
        record = FeedbackRecord(
            report_id=feedback.report_id,
            understandability_score=feedback.understandability_score,
            conclusion_correct=feedback.conclusion_correct,
            confusing_section=feedback.confusing_section,
            analysis_duration_ok=feedback.analysis_duration_ok,
            would_trust=feedback.would_trust,
            optional_comment=feedback.optional_comment,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return FeedbackResponse(feedback_id=record.id, message="Feedback received. Thank you.")
    except SQLAlchemyError:
        # Feedback failure must never interrupt the user's experience
        # (it is not part of the core analysis flow) — logged, not raised.
        logger.error("Failed to persist feedback", exc_info=True)
        return FeedbackResponse(feedback_id=-1, message="Feedback received. Thank you.")


@router.post("/report-incorrect")
@limiter.limit(INCORRECT_RATE_LIMIT)
async def report_incorrect(
    request: Request,
    submission: IncorrectAnalysisRequest,
    session: Session = Depends(get_session),
) -> JSONResponse:
    report = get_report(submission.report_id, session)
    if report is None:
        body = ErrorResponse(
            error="report_not_found",
            detail=f"No report found for id {submission.report_id}.",
            status_code=404,
        )
        return JSONResponse(status_code=404, content=body.model_dump())

    # ExaminaReport does not carry a raw contradiction count (Phase 2's
    # report engine folds contradictions into confidence/limitations
    # text rather than exposing PRISM-side counts) — approximate for
    # logging from the limitation entries that mention contradictions.
    contradiction_related_limitations = sum(
        1 for item in report.confidence.limitations if "contradiction" in item.lower()
    )
    logger.info(
        "Incorrect-analysis report received: report_id=%s overall_confidence=%s "
        "contradiction_related_limitations=%s",
        submission.report_id,
        report.confidence.overall,
        contradiction_related_limitations,
    )

    record = IncorrectAnalysisRecord(
        report_id=submission.report_id,
        fired_rule_ids=None,
        overall_confidence=report.confidence.overall,
        user_comment=submission.user_comment,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    response = IncorrectAnalysisResponse(
        submission_id=record.id,
        message="Thank you — this report has been flagged for review.",
    )
    return JSONResponse(status_code=200, content=response.model_dump())
