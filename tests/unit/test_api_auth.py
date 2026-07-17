"""Tests for src/examina/api/auth.py."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from examina.api.auth import (
    get_admin_token,
    get_invite_code,
    verify_admin_token,
    verify_invite_code,
)


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestInviteCode:
    def test_verify_invite_code_raises_401_for_wrong_code(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            verify_invite_code(credentials=_creds("wrong-code"))
        assert exc_info.value.status_code == 401

    def test_verify_invite_code_returns_code_for_correct_code(self) -> None:
        result = verify_invite_code(credentials=_creds("test-invite-code"))
        assert result == "test-invite-code"

    def test_get_invite_code_raises_runtime_error_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EXAMINA_INVITE_CODE", raising=False)
        with pytest.raises(RuntimeError):
            get_invite_code()


class TestAdminToken:
    def test_verify_admin_token_raises_401_for_wrong_token(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(credentials=_creds("wrong-token"))
        assert exc_info.value.status_code == 401

    def test_verify_admin_token_returns_token_for_correct_token(self) -> None:
        result = verify_admin_token(credentials=_creds("test-admin-token"))
        assert result == "test-admin-token"

    def test_verify_admin_token_returns_503_when_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EXAMINA_ADMIN_TOKEN", raising=False)
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(credentials=_creds("anything"))
        assert exc_info.value.status_code == 503

    def test_get_admin_token_raises_runtime_error_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EXAMINA_ADMIN_TOKEN", raising=False)
        with pytest.raises(RuntimeError):
            get_admin_token()
