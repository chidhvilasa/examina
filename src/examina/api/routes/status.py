"""GET /status — unauthenticated, unrate-limited uptime-monitor endpoint."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

import examina

router = APIRouter()


class StatusResponse(BaseModel):
    status: Literal["ok"]
    version: str
    supported_types: list[str]


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return StatusResponse(
        status="ok",
        version=examina.__version__,
        supported_types=["JPEG", "PNG", "WebP", "PDF"],
    )
