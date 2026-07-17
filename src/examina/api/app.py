"""FastAPI application factory."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

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

_DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173"


def _get_allowed_origins() -> list[str]:
    raw = os.environ.get("EXAMINA_ALLOWED_ORIGINS", _DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Sets baseline security headers on every response. Content-Security-Policy
    is deliberately left to the Nginx/Caddy layer (see deployment/), since it
    varies between the API and the UI's static-file responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response


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
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

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
