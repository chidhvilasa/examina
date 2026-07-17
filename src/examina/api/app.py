"""FastAPI application factory."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import examina
from examina.api.database import get_engine
from examina.api.models import ErrorResponse
from examina.api.rate_limit import get_limiter
from examina.api.routes.admin import router as admin_router
from examina.api.routes.analyze import router as analyze_router
from examina.api.routes.feedback import router as feedback_router
from examina.api.routes.health import router as health_router
from examina.api.routes.report import router as report_router
from examina.api.routes.status import router as status_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="EXAMINA API",
        description="Digital Evidence Intelligence for Journalists",
        version=examina.__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.on_event("startup")
    async def startup() -> None:
        app.state.startup_time = datetime.now(UTC)
        get_engine()

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        del request
        body = ErrorResponse(
            error="rate_limit_exceeded",
            detail="Too many requests. Please slow down and try again shortly.",
            status_code=429,
        )
        return JSONResponse(status_code=429, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        detail = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        body = ErrorResponse(error="validation_error", detail=detail, status_code=422)
        return JSONResponse(status_code=422, content=body.model_dump())

    app.include_router(status_router, prefix="")
    app.include_router(health_router, prefix="")
    app.include_router(analyze_router, prefix="")
    app.include_router(report_router, prefix="")
    app.include_router(feedback_router, prefix="")
    app.include_router(admin_router, prefix="")

    return app
