"""
POST /analyze — the primary upload-and-analyze endpoint.

This route composes the same steps `examina.pipeline.orchestrator.
run_analysis()` performs (upload pipeline -> bridge -> report engine)
rather than calling it directly, so it can also surface
`BridgeConfidence.active_hypotheses`/`unresolved_contradictions` in
`AnalyzeResponse` — numbers `ExaminaReport` itself does not carry, and
`report/`/`pipeline/` are out of scope to modify this phase. Every step
is otherwise byte-for-byte the same call into unmodified pipeline/bridge/
report code.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import examina
from examina.api.auth import verify_invite_code
from examina.api.database import delete_expired_reports, get_session, save_report
from examina.api.models import AnalyzeResponse, ErrorResponse
from examina.api.rate_limit import ANALYZE_RATE_LIMIT, get_limiter
from examina.bridge.factory import get_bridge_client
from examina.bridge.types import BridgeError, BridgeRequest
from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import (
    DecompressionBombError,
    FileTooLargeError,
    InvalidMimeTypeError,
    MalwareDetectedError,
    UnsupportedFileTypeError,
)
from examina.pipeline.orchestrator import mime_type_to_file_type
from examina.pipeline.pipeline import process_upload
from examina.report.assembler import assemble_report

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = get_limiter()


def _get_clamav_mode() -> str:
    return os.environ.get("CLAMAV_MODE", "skip")


def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    body = ErrorResponse(error=error, detail=detail, status_code=status_code)
    return JSONResponse(status_code=status_code, content=body.model_dump())


@router.post("/analyze")
@limiter.limit(ANALYZE_RATE_LIMIT)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    _invite_code: str = Depends(verify_invite_code),
    session: Session = Depends(get_session),
) -> JSONResponse:
    data = await file.read()
    upload_config = UploadConfig(clamav_mode=_get_clamav_mode())  # type: ignore[arg-type]

    try:
        upload_result = process_upload(data, file.filename, upload_config, logger)
        file_type = mime_type_to_file_type(upload_result.mime_type)

        bridge_client = get_bridge_client()
        bridge_request = BridgeRequest(
            file_bytes=data,
            file_hash=upload_result.file_hash,
            file_type=file_type,
            clamav_mode=upload_config.clamav_mode,
            examina_version=examina.__version__,
        )
        bridge_result = await bridge_client.analyze(bridge_request)

        report = assemble_report(
            bridge_result=bridge_result,
            file_hash=upload_result.file_hash,
            file_type=file_type,
            file_size_bytes=upload_result.file_size_bytes,
            examina_version=examina.__version__,
        )
    except FileTooLargeError:
        return _error_response(413, "file_too_large", "File exceeds the 20MB limit.")
    except (InvalidMimeTypeError, UnsupportedFileTypeError):
        return _error_response(
            415,
            "unsupported_media_type",
            "File type is not supported. EXAMINA accepts JPEG, PNG, WebP, and PDF files.",
        )
    except MalwareDetectedError:
        return _error_response(
            400, "file_rejected", "This file was rejected for security reasons."
        )
    except DecompressionBombError:
        return _error_response(
            400, "file_rejected", "This file was rejected for security reasons."
        )
    except BridgeError:
        return _error_response(
            503,
            "analysis_unavailable",
            "Analysis service is temporarily unavailable. Please try again in a few minutes.",
        )
    except Exception:
        logger.error("Unexpected error during analysis", exc_info=True)
        return _error_response(500, "internal_error", "An unexpected error occurred.")

    delete_expired_reports(session)
    save_report(report, session)

    logger.info(
        "Analysis complete: report_id=%s file_type=%s", report.report_id, report.file_type
    )

    response = AnalyzeResponse(
        report_id=str(report.report_id),
        file_hash=report.file_hash,
        file_type=report.file_type,
        status="complete",
        verdict=report.assessment.verdict.value,
        confidence_label=report.assessment.confidence_label.value,
        overall_confidence=report.confidence.overall,
        active_hypotheses=bridge_result.reconstruction_confidence.active_hypotheses,
        unresolved_contradictions=bridge_result.reconstruction_confidence.unresolved_contradictions,
        natural_language_summary=report.assessment.verdict_plain.text,
        recommendation=report.assessment.recommendation.text,
        what_would_change=report.assessment.what_would_change.text,
        report_url=f"/report/{report.report_id}",
        expires_at=report.expires_at.isoformat(),
    )
    return JSONResponse(status_code=200, content=response.model_dump())
