"""
Persistence layer — report metadata, feedback, and incorrect-analysis
reports. Never stores raw uploaded file content (Constitution Principle
7): `report_json` is the already-generated, PII-free `ExaminaReport`.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from examina.report.schema import ExaminaReport


def _naive_utcnow() -> datetime:
    """
    Equivalent to the deprecated `datetime.utcnow()`: a naive datetime
    holding the current UTC time. All columns here are naive (SQLite has
    no native timezone-aware storage) so every comparison in this module
    stays naive-to-naive.
    """
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    file_hash: Mapped[str] = mapped_column(String, index=True, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    analysis_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_naive_utcnow, nullable=False)


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    understandability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conclusion_correct: Mapped[str | None] = mapped_column(String, nullable=True)
    confusing_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    analysis_duration_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    would_trust: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    optional_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_naive_utcnow, nullable=False)


class IncorrectAnalysisRecord(Base):
    __tablename__ = "incorrect_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    fired_rule_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_naive_utcnow, nullable=False)


_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Return the process-wide SQLAlchemy engine, creating it (and its
    tables) on first call. `EXAMINA_TEST_MODE=1` selects an in-memory
    SQLite database shared across the process via `StaticPool`, so
    successive requests within a test process see the same data.
    """
    global _engine
    if _engine is not None:
        return _engine

    if os.environ.get("EXAMINA_TEST_MODE") == "1":
        _engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        database_url = os.environ.get("DATABASE_URL", "sqlite:///./examina_dev.db")
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _engine = create_engine(database_url, connect_args=connect_args)

    Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=get_engine())
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def save_report(report: ExaminaReport, session: Session) -> None:
    """Idempotent: a report_id already present is left untouched."""
    if session.get(ReportRecord, str(report.report_id)) is not None:
        return

    record = ReportRecord(
        id=str(report.report_id),
        file_hash=report.file_hash,
        file_type=report.file_type,
        analysis_timestamp=report.created_at.replace(tzinfo=None),
        expires_at=report.expires_at.replace(tzinfo=None),
        report_json=report.to_json(),
    )
    session.add(record)
    session.commit()


def get_report(report_id: str, session: Session) -> ExaminaReport | None:
    record = session.get(ReportRecord, report_id)
    if record is None:
        return None
    return ExaminaReport.from_json(record.report_json)


def delete_report(report_id: str, session: Session) -> bool:
    record = session.get(ReportRecord, report_id)
    if record is None:
        return False
    session.delete(record)
    session.commit()
    return True


def delete_expired_reports(session: Session) -> int:
    now = _naive_utcnow()
    expired = session.query(ReportRecord).filter(ReportRecord.expires_at < now).all()
    count = len(expired)
    for record in expired:
        session.delete(record)
    if expired:
        session.commit()
    return count
