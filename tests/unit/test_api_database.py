"""Tests for src/examina/api/database.py."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

import examina.api.database as database_module
from examina.api.database import (
    delete_expired_reports,
    delete_report,
    get_engine,
    get_report,
    save_report,
)
from examina.bridge.local_client import LocalBridgeClient
from examina.bridge.types import BridgeRequest, BridgeResult
from examina.report.assembler import assemble_report
from examina.report.schema import ExaminaReport

VALID_HASH = "a" * 64


def _bridge_result() -> BridgeResult:
    request = BridgeRequest(
        file_bytes=b"stub-bytes",
        file_hash=VALID_HASH,
        file_type="JPEG",
        examina_version="0.4.0",
    )
    return asyncio.run(LocalBridgeClient(prism_path=Path("../PRISM")).analyze(request))


def _make_report() -> ExaminaReport:
    return assemble_report(
        bridge_result=_bridge_result(),
        file_hash=VALID_HASH,
        file_type="JPEG",
        file_size_bytes=1024,
        examina_version="0.4.0",
    )


def _make_expired_report() -> ExaminaReport:
    report = _make_report()
    now = datetime.now(UTC)
    return report.model_copy(
        update={"created_at": now - timedelta(hours=48), "expires_at": now - timedelta(hours=24)}
    )


@pytest.fixture
def session() -> Iterator[Session]:
    session_factory = sessionmaker(bind=get_engine())
    db_session = session_factory()
    try:
        yield db_session
    finally:
        db_session.close()


class TestSaveAndGetReport:
    def test_save_report_persists_retrievable_report(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        retrieved = get_report(str(report.report_id), session)
        assert retrieved is not None
        assert retrieved.report_id == report.report_id

    def test_get_report_returns_none_for_unknown_id(self, session: Session) -> None:
        assert get_report("does-not-exist", session) is None

    def test_get_report_returns_examina_report_for_known_id(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        retrieved = get_report(str(report.report_id), session)
        assert isinstance(retrieved, ExaminaReport)

    def test_saved_and_retrieved_report_has_identical_file_hash(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        retrieved = get_report(str(report.report_id), session)
        assert retrieved is not None
        assert retrieved.file_hash == report.file_hash

    def test_saved_and_retrieved_report_has_identical_verdict(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        retrieved = get_report(str(report.report_id), session)
        assert retrieved is not None
        assert retrieved.assessment.verdict == report.assessment.verdict

    def test_save_report_duplicate_id_does_not_raise(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        save_report(report, session)  # must not raise
        retrieved = get_report(str(report.report_id), session)
        assert retrieved is not None


class TestDeleteReport:
    def test_delete_report_returns_true_for_existing(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        assert delete_report(str(report.report_id), session) is True

    def test_delete_report_returns_false_for_unknown(self, session: Session) -> None:
        assert delete_report("does-not-exist", session) is False

    def test_deleted_report_is_no_longer_retrievable(self, session: Session) -> None:
        report = _make_report()
        save_report(report, session)
        delete_report(str(report.report_id), session)
        assert get_report(str(report.report_id), session) is None


class TestDeleteExpiredReports:
    def test_deletes_only_expired_records(self, session: Session) -> None:
        expired = _make_expired_report()
        fresh = _make_report()
        save_report(expired, session)
        save_report(fresh, session)

        delete_expired_reports(session)

        assert get_report(str(expired.report_id), session) is None
        assert get_report(str(fresh.report_id), session) is not None

    def test_returns_correct_count(self, session: Session) -> None:
        expired_one = _make_expired_report()
        expired_two = _make_expired_report()
        save_report(expired_one, session)
        save_report(expired_two, session)

        count = delete_expired_reports(session)

        assert count == 2

    def test_non_expired_records_not_deleted(self, session: Session) -> None:
        fresh = _make_report()
        save_report(fresh, session)
        delete_expired_reports(session)
        assert get_report(str(fresh.report_id), session) is not None


class TestGetEngineNonTestMode:
    def test_uses_database_url_when_not_in_test_mode(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        original_engine = database_module._engine
        monkeypatch.setattr(database_module, "_engine", None)
        monkeypatch.delenv("EXAMINA_TEST_MODE", raising=False)
        db_url = f"sqlite:///{tmp_path / 'test-non-test-mode.db'}"
        monkeypatch.setenv("DATABASE_URL", db_url)

        try:
            engine = database_module.get_engine()
            assert str(engine.url) == db_url
        finally:
            database_module._engine = original_engine
