"""Tests for src/examina/report/schema.py — see specs/REPORT_SCHEMA_v1.0.md."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from examina.language.guard import LanguageViolationError
from examina.report.schema import (
    EXAMINA_DISCLAIMER,
    Assessment,
    CertaintyEnum,
    ConfidenceDimension,
    ConfidenceLabelEnum,
    ConfidenceSection,
    EvidenceFamily,
    EvidenceSection,
    ExaminaReport,
    HistoryEvent,
    HistorySection,
    Signal,
    TraceableString,
    VerdictEnum,
)

VALID_HASH = "a" * 64


def _signal(signal_id: str = "metadata_000") -> Signal:
    return Signal(
        signal_id=signal_id,
        statement=TraceableString(
            text="File declares metadata.", trace_ids=["fact-1"], generated=False
        ),
        direction="NEUTRAL",
        extraction_confidence=0.9,
        source_reliability=0.8,
        produced_by="stub-extractor:1.0",
        affected_region=None,
        raw_value={},
    )


def _evidence_family() -> EvidenceFamily:
    return EvidenceFamily(
        family_id="metadata",
        family_name="File Metadata",
        family_finding=TraceableString(
            text="File contains declared metadata establishing claimed origin.",
            trace_ids=["fact-1"],
            generated=True,
        ),
        signals=[_signal()],
        correlated=True,
    )


def _evidence_section() -> EvidenceSection:
    return EvidenceSection(
        families=[_evidence_family()],
        total_signals=1,
        signals_supporting_verdict=0,
        signals_contradicting_verdict=0,
        signals_neutral=1,
    )


def _history_event(sequence: int = 1) -> HistoryEvent:
    return HistoryEvent(
        sequence=sequence,
        description=TraceableString(text="File was created.", trace_ids=[], generated=False),
        certainty=CertaintyEnum.CONFIRMED,
        certainty_note=TraceableString(
            text="This event is well-supported by multiple consistent signals.",
            trace_ids=[],
            generated=True,
        ),
        supporting_signals=[],
    )


def _history_section() -> HistorySection:
    return HistorySection(events=[_history_event()], reconstruction_complete=True, unknown_gaps=[])


def _confidence_dimension() -> ConfidenceDimension:
    return ConfidenceDimension(
        value=0.8,
        label="high",
        note=TraceableString(text="Some note.", trace_ids=[], generated=True),
    )


def _confidence_section(disclaimer: str = EXAMINA_DISCLAIMER) -> ConfidenceSection:
    return ConfidenceSection(
        overall=0.8,
        overall_label=ConfidenceLabelEnum.HIGH,
        extraction=_confidence_dimension(),
        reliability=_confidence_dimension(),
        inference=_confidence_dimension(),
        hypothesis=_confidence_dimension(),
        penalty=_confidence_dimension(),
        limitations=["Some limitation."],
        disclaimer=disclaimer,
    )


def _assessment() -> Assessment:
    return Assessment(
        verdict=VerdictEnum.LIKELY_AUTHENTIC,
        verdict_plain=TraceableString(
            text="Evidence is consistent with authentic origin.",
            trace_ids=["fact-1"],
            generated=True,
        ),
        recommendation=TraceableString(
            text="Standard editorial verification is sufficient.",
            trace_ids=[],
            generated=True,
        ),
        what_would_change=TraceableString(
            text="A matching C2PA credential would increase confidence.",
            trace_ids=[],
            generated=True,
        ),
        confidence_label=ConfidenceLabelEnum.HIGH,
    )


def _valid_report(**overrides: object) -> ExaminaReport:
    created_at_raw = overrides.pop("created_at", datetime.now(UTC))
    assert isinstance(created_at_raw, datetime)
    created_at = created_at_raw
    expires_at = overrides.pop("expires_at", created_at + timedelta(hours=24))
    fields: dict[str, object] = {
        "file_hash": VALID_HASH,
        "file_name_sanitized": str(uuid4()),
        "file_type": "JPEG",
        "file_size_bytes": 1024,
        "created_at": created_at,
        "expires_at": expires_at,
        "examina_version": "0.2.0",
        "prism_version": "stub:1.0",
        "rule_set_version": "stub:1.0",
        "assessment": _assessment(),
        "evidence": _evidence_section(),
        "history": _history_section(),
        "confidence": _confidence_section(),
    }
    fields.update(overrides)
    return ExaminaReport(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TraceableString
# ---------------------------------------------------------------------------


class TestTraceableString:
    def test_instantiates_correctly(self) -> None:
        ts = TraceableString(text="Clean text.", trace_ids=["fact-1"], generated=True)
        assert ts.text == "Clean text."
        assert ts.trace_ids == ["fact-1"]
        assert ts.generated is True

    def test_checked_returns_self_for_clean_text(self) -> None:
        ts = TraceableString(text="Clean text.", trace_ids=[], generated=True)
        assert ts.checked() is ts

    def test_checked_raises_for_fake(self) -> None:
        ts = TraceableString(text="This is fake.", trace_ids=[], generated=True)
        with pytest.raises(LanguageViolationError):
            ts.checked()

    def test_checked_raises_for_proof(self) -> None:
        ts = TraceableString(text="This is proof.", trace_ids=[], generated=True)
        with pytest.raises(LanguageViolationError):
            ts.checked()

    def test_empty_text_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            TraceableString(text="", trace_ids=[], generated=True)


# ---------------------------------------------------------------------------
# EvidenceSection
# ---------------------------------------------------------------------------


class TestEvidenceSection:
    def test_rejects_mismatched_counts(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceSection(
                families=[_evidence_family()],
                total_signals=5,
                signals_supporting_verdict=0,
                signals_contradicting_verdict=0,
                signals_neutral=1,
            )

    def test_accepts_matching_counts(self) -> None:
        section = _evidence_section()
        assert section.total_signals == 1


# ---------------------------------------------------------------------------
# HistorySection
# ---------------------------------------------------------------------------


class TestHistorySection:
    def test_duplicate_sequence_raises(self) -> None:
        with pytest.raises(ValidationError):
            HistorySection(
                events=[_history_event(sequence=1), _history_event(sequence=1)],
                reconstruction_complete=True,
                unknown_gaps=[],
            )

    def test_unsorted_sequence_raises(self) -> None:
        with pytest.raises(ValidationError):
            HistorySection(
                events=[_history_event(sequence=2), _history_event(sequence=1)],
                reconstruction_complete=True,
                unknown_gaps=[],
            )


# ---------------------------------------------------------------------------
# ExaminaReport
# ---------------------------------------------------------------------------


class TestExaminaReport:
    def test_expires_before_created_raises(self) -> None:
        created_at = datetime.now(UTC)
        with pytest.raises(ValidationError):
            _valid_report(created_at=created_at, expires_at=created_at - timedelta(hours=1))

    def test_bad_file_hash_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_report(file_hash="not-a-hash")

    def test_bad_file_name_sanitized_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_report(file_name_sanitized="not-a-uuid")

    def test_disclaimer_mismatch_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_report(confidence=_confidence_section(disclaimer="Wrong disclaimer text."))

    def test_to_json_produces_valid_json_string(self) -> None:
        report = _valid_report()
        parsed = json.loads(report.to_json())
        assert parsed["file_hash"] == VALID_HASH

    def test_from_json_to_json_roundtrip(self) -> None:
        report = _valid_report()
        roundtripped = ExaminaReport.from_json(report.to_json())
        assert roundtripped == report
