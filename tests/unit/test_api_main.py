"""Tests for src/examina/api/main.py."""

from __future__ import annotations

from fastapi import FastAPI

from examina.api.main import app


class TestMainEntrypoint:
    def test_app_is_a_fastapi_instance(self) -> None:
        assert isinstance(app, FastAPI)
