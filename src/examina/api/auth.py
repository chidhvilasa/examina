"""
Authentication — invite-code gating for the public API and a separate
admin token for the admin surfaces (specs/DEPLOYMENT_SPEC_v1.0.md's
`EXAMINA_INVITE_CODE` / `EXAMINA_ADMIN_TOKEN`). No user accounts, no
OAuth: a research-beta invite code, simple, auditable, rotatable.
"""

from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer()


def get_invite_code() -> str:
    code = os.environ.get("EXAMINA_INVITE_CODE")
    if not code:
        raise RuntimeError("EXAMINA_INVITE_CODE environment variable not set")
    return code


def get_admin_token() -> str:
    token = os.environ.get("EXAMINA_ADMIN_TOKEN")
    if not token:
        raise RuntimeError("EXAMINA_ADMIN_TOKEN environment variable not set")
    return token


def verify_invite_code(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
) -> str:
    invite_code = get_invite_code()
    if not hmac.compare_digest(credentials.credentials, invite_code):
        raise HTTPException(status_code=401, detail="Invalid invite code")
    return invite_code


def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
) -> str:
    try:
        admin_token = get_admin_token()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Admin interface not configured") from exc

    if not hmac.compare_digest(credentials.credentials, admin_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return admin_token
