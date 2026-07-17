"""GET /health — unauthenticated, unrate-limited operational health check."""

from __future__ import annotations

import logging
import shutil
from datetime import UTC, datetime
from typing import Literal

import psutil
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import examina
from examina.api.database import get_engine
from examina.api.models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_MIN_DISK_FREE_GB = 1.0
_MIN_MEMORY_FREE_MB = 256.0


def _check_database() -> Literal["ok", "error"]:
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except SQLAlchemyError:
        logger.error("Health check: database connectivity check failed", exc_info=True)
        return "error"


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> JSONResponse:
    database_status = _check_database()

    disk_free_gb = shutil.disk_usage(".").free / (1024**3)
    memory_free_mb = psutil.virtual_memory().available / (1024**2)
    startup_time: datetime = request.app.state.startup_time
    uptime_seconds = (datetime.now(UTC) - startup_time).total_seconds()

    if database_status == "error":
        status: Literal["ok", "degraded", "error"] = "error"
    elif disk_free_gb <= _MIN_DISK_FREE_GB or memory_free_mb < _MIN_MEMORY_FREE_MB:
        status = "degraded"
    else:
        status = "ok"

    response = HealthResponse(
        status=status,
        version=examina.__version__,
        database_status=database_status,
        # EXAMINA has no OCR of its own — OCR is entirely PRISM's concern,
        # reached only through the bridge, so this is always True here.
        ocr_available=True,
        disk_free_gb=disk_free_gb,
        memory_free_mb=memory_free_mb,
        uptime_seconds=uptime_seconds,
        timestamp=datetime.now(UTC).isoformat(),
    )

    status_code = 200 if status != "error" else 503
    return JSONResponse(content=response.model_dump(), status_code=status_code)
