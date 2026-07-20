"""
Admin endpoints — aggregate statistics and moderation views, all gated by
`verify_admin_token` (a separate credential from the invite code).
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from examina.api.auth import verify_admin_token
from examina.api.database import FeedbackRecord, IncorrectAnalysisRecord, ReportRecord, get_session
from examina.api.rate_limit import ADMIN_RATE_LIMIT, get_limiter

router = APIRouter()
limiter = get_limiter()


@router.get("/admin/overview")
@limiter.limit(ADMIN_RATE_LIMIT)
async def get_overview(
    request: Request,
    _admin_token: str = Depends(verify_admin_token),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    total_analyses = session.query(func.count(ReportRecord.id)).scalar() or 0

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    analyses_today = (
        session.query(func.count(ReportRecord.id))
        .filter(ReportRecord.created_at >= today_start)
        .scalar()
        or 0
    )

    total_feedback = session.query(func.count(FeedbackRecord.id)).scalar() or 0
    total_incorrect_reports = session.query(func.count(IncorrectAnalysisRecord.id)).scalar() or 0

    mean_score = session.query(func.avg(FeedbackRecord.understandability_score)).scalar()

    changed_assessment_distribution = {
        "yes_significantly": 0,
        "yes_somewhat": 0,
        "no": 0,
        "unsure_before_and_after": 0,
    }
    rows = (
        session.query(FeedbackRecord.changed_assessment, func.count(FeedbackRecord.id))
        .group_by(FeedbackRecord.changed_assessment)
        .all()
    )
    for value, count in rows:
        if value in changed_assessment_distribution:
            changed_assessment_distribution[value] = count

    workflow_adoption_distribution = {"yes": 0, "maybe": 0, "no": 0}
    rows = (
        session.query(FeedbackRecord.would_use_in_workflow, func.count(FeedbackRecord.id))
        .group_by(FeedbackRecord.would_use_in_workflow)
        .all()
    )
    for value, count in rows:
        if value in workflow_adoption_distribution:
            workflow_adoption_distribution[value] = count

    return {
        "total_analyses": total_analyses,
        "analyses_today": analyses_today,
        "total_feedback": total_feedback,
        "total_incorrect_reports": total_incorrect_reports,
        "mean_understandability_score": float(mean_score) if mean_score is not None else None,
        "changed_assessment_distribution": changed_assessment_distribution,
        "workflow_adoption_distribution": workflow_adoption_distribution,
    }


@router.get("/admin/rules")
@limiter.limit(ADMIN_RATE_LIMIT)
async def get_rules(
    request: Request,
    _admin_token: str = Depends(verify_admin_token),
) -> dict[str, object]:
    # Rule-firing data originates from PRISM and is not yet surfaced
    # through the bridge in real (non-stub) mode — see specs/TECH_DEBT.md
    # TD-009.
    return {"rules": [], "note": "Rule health tracking available in v0.4.0"}


@router.get("/admin/feedback")
@limiter.limit(ADMIN_RATE_LIMIT)
async def get_feedback(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    _admin_token: str = Depends(verify_admin_token),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    total = session.query(func.count(FeedbackRecord.id)).scalar() or 0
    records = (
        session.query(FeedbackRecord)
        .order_by(FeedbackRecord.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    items = [
        {
            "id": record.id,
            "report_id": record.report_id,
            "understandability_score": record.understandability_score,
            "most_useful_section": record.most_useful_section,
            "least_useful_section": record.least_useful_section,
            "changed_assessment": record.changed_assessment,
            "would_use_in_workflow": record.would_use_in_workflow,
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]
    return {"total": total, "page": page, "items": items}


@router.get("/admin/incorrect")
@limiter.limit(ADMIN_RATE_LIMIT)
async def get_incorrect(
    request: Request,
    _admin_token: str = Depends(verify_admin_token),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    records = (
        session.query(IncorrectAnalysisRecord)
        .order_by(IncorrectAnalysisRecord.created_at.desc())
        .all()
    )
    items = [
        {
            "id": record.id,
            "report_id": record.report_id,
            "fired_rule_ids": record.fired_rule_ids,
            "overall_confidence": record.overall_confidence,
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]
    return {"items": items}
