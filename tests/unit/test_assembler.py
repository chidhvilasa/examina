"""Tests for src/examina/report/assembler.py — uses inline BridgeResult fixtures.

BridgeResult objects are built directly here rather than via
LocalBridgeClient, which since Phase 7 makes a real subprocess call into
PRISM — unit tests must stay hermetic and PRISM-independent (see
tests/integration/test_real_bridge.py for the real-PRISM-backed tests).
"""

from __future__ import annotations

from uuid import UUID

from examina.bridge.types import (
    BridgeConfidence,
    BridgeFact,
    BridgeHypothesis,
    BridgeResult,
    BridgeTimelineEvent,
)
from examina.report.assembler import assemble_report, build_evidence_section
from examina.report.schema import (
    EXAMINA_DISCLAIMER,
    EvidenceFamily,
    ExaminaReport,
    Signal,
    TraceableString,
)

VALID_HASH = "c" * 64


def _stub_bridge_result() -> BridgeResult:
    return _bridge_result()


def _bridge_result(**overrides: object) -> BridgeResult:
    fields: dict[str, object] = {
        "request_id": UUID(int=1),
        "bridge_version": "bridge:1.0",
        "prism_version": "stub:1.0",
        "rule_set_version": "stub:1.0",
        "extractor_versions": {"stub": "1.0"},
        "processing_time_ms": 0,
        "facts": [
            BridgeFact(
                fact_id="fact-1",
                statement="This file declares creation metadata.",
                fact_type="PROVENANCE",
                provenance_source_type="declared",
                extractor="stub-extractor:1.0",
                extraction_confidence=0.9,
                source_reliability=0.8,
                raw_value={},
            )
        ],
        "contradictions": [],
        "hypotheses": [
            BridgeHypothesis(
                hypothesis_id="hyp-1",
                description="This file is consistent with an unedited original.",
                confidence=0.6,
                rank=1,
            ),
        ],
        "timeline": [BridgeTimelineEvent(sequence=1, description="Event.", confidence=0.7)],
        "reconstruction_confidence": BridgeConfidence(
            overall=0.72,
            penalty_from_contradictions=0.0,
            unresolved_contradictions=0,
            active_hypotheses=1,
        ),
        "errors": [],
        "partial_analysis": False,
        "partial_reason": None,
    }
    fields.update(overrides)
    return BridgeResult(**fields)  # type: ignore[arg-type]


def _assemble() -> ExaminaReport:
    return assemble_report(
        bridge_result=_stub_bridge_result(),
        file_hash=VALID_HASH,
        file_type="JPEG",
        file_size_bytes=2048,
        examina_version="0.2.0",
    )


class TestAssembleReport:
    def test_returns_examina_report(self) -> None:
        assert isinstance(_assemble(), ExaminaReport)

    def test_file_hash_matches_input(self) -> None:
        assert _assemble().file_hash == VALID_HASH

    def test_file_type_matches_input(self) -> None:
        assert _assemble().file_type == "JPEG"

    def test_expires_at_is_24_hours_after_created_at(self) -> None:
        report = _assemble()
        assert (report.expires_at - report.created_at).total_seconds() == 24 * 3600

    def test_file_name_sanitized_is_valid_uuid(self) -> None:
        report = _assemble()
        UUID(report.file_name_sanitized)  # raises if invalid

    def test_schema_version_equals_100(self) -> None:
        assert _assemble().schema_version == "1.0.0"

    def test_assessment_is_not_none(self) -> None:
        assert _assemble().assessment is not None

    def test_evidence_families_not_empty(self) -> None:
        report = _assemble()
        assert len(report.evidence.families) > 0

    def test_history_is_not_none(self) -> None:
        assert _assemble().history is not None

    def test_confidence_disclaimer_equals_constant(self) -> None:
        assert _assemble().confidence.disclaimer == EXAMINA_DISCLAIMER

    def test_json_roundtrip_preserves_all_fields(self) -> None:
        report = _assemble()
        roundtripped = ExaminaReport.from_json(report.to_json())
        assert roundtripped == report

    def test_two_calls_produce_different_report_ids(self) -> None:
        first = _assemble()
        second = _assemble()
        assert first.report_id != second.report_id


class TestBuildEvidenceSection:
    def test_counts_supporting_and_contradicting_signals(self) -> None:
        def _signal(signal_id: str, direction: str) -> Signal:
            return Signal(
                signal_id=signal_id,
                statement=TraceableString(text="Signal text.", trace_ids=["f1"], generated=False),
                direction=direction,  # type: ignore[arg-type]
                extraction_confidence=0.9,
                source_reliability=0.9,
                produced_by="stub-extractor:1.0",
                affected_region=None,
                raw_value={},
            )

        family = EvidenceFamily(
            family_id="metadata",
            family_name="File Metadata",
            family_finding=TraceableString(
                text="Combined finding.", trace_ids=["f1"], generated=True
            ),
            signals=[
                _signal("metadata_000", "SUPPORTS"),
                _signal("metadata_001", "CONTRADICTS"),
                _signal("metadata_002", "NEUTRAL"),
            ],
            correlated=True,
        )
        section = build_evidence_section([family], _stub_bridge_result())
        assert section.signals_supporting_verdict == 1
        assert section.signals_contradicting_verdict == 1
        assert section.signals_neutral == 1
        assert section.total_signals == 3


class TestPartialAnalysis:
    def test_partial_analysis_adds_limitation(self) -> None:
        bridge_result = _bridge_result(partial_analysis=True, partial_reason="Timeout on page 4.")
        report = assemble_report(
            bridge_result=bridge_result,
            file_hash=VALID_HASH,
            file_type="PDF",
            file_size_bytes=4096,
            examina_version="0.2.0",
        )
        assert any(
            "Analysis is incomplete: Timeout on page 4." in item
            for item in report.confidence.limitations
        )
