"""GET /report/{report_id} and DELETE /report/{report_id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from examina.api.auth import verify_invite_code
from examina.api.database import delete_report, get_report, get_session
from examina.api.models import ErrorResponse, ReportResponse
from examina.api.rate_limit import REPORT_RATE_LIMIT, get_limiter

router = APIRouter()
limiter = get_limiter()


def _not_found(report_id: str) -> JSONResponse:
    body = ErrorResponse(
        error="report_not_found",
        detail=f"No report found for id {report_id}.",
        status_code=404,
    )
    return JSONResponse(status_code=404, content=body.model_dump())


@router.get("/report/{report_id}")
@limiter.limit(REPORT_RATE_LIMIT)
async def get_report_route(
    request: Request,
    report_id: str,
    _invite_code: str = Depends(verify_invite_code),
    session: Session = Depends(get_session),
) -> JSONResponse:
    report = get_report(report_id, session)
    if report is None:
        return _not_found(report_id)

    response = ReportResponse(
        report_id=str(report.report_id),
        file_hash=report.file_hash,
        file_type=report.file_type,
        analysis_timestamp=report.created_at.isoformat(),
        expires_at=report.expires_at.isoformat(),
        report=report.model_dump(mode="json"),
    )
    return JSONResponse(status_code=200, content=response.model_dump())


@router.delete("/report/{report_id}")
async def delete_report_route(
    report_id: str,
    _invite_code: str = Depends(verify_invite_code),
    session: Session = Depends(get_session),
) -> JSONResponse:
    deleted = delete_report(report_id, session)
    if not deleted:
        return _not_found(report_id)
    return JSONResponse(status_code=200, content={"deleted": True, "report_id": report_id})
