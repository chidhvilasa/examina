"""Tests for src/examina/report/confidence.py — see specs/CONFIDENCE_TRANSLATION_v1.0.md."""

from __future__ import annotations

from examina.bridge.types import BridgeConfidence, BridgeFact
from examina.language.guard import check_language
from examina.report.confidence import translate_confidence
from examina.report.schema import (
    EXAMINA_DISCLAIMER,
    ConfidenceLabelEnum,
    ConfidenceSection,
    EvidenceSection,
)


def _fact(
    fact_id: str,
    extraction_confidence: float,
    source_reliability: float,
) -> BridgeFact:
    return BridgeFact(
        fact_id=fact_id,
        statement="Statement.",
        fact_type="STRUCTURAL",
        provenance_source_type="observed",
        extractor="stub-extractor:1.0",
        extraction_confidence=extraction_confidence,
        source_reliability=source_reliability,
        raw_value={},
    )


def _bridge_confidence(**overrides: object) -> BridgeConfidence:
    fields: dict[str, object] = {
        "overall": 0.8,
        "penalty_from_contradictions": 0.0,
        "unresolved_contradictions": 0,
        "active_hypotheses": 1,
    }
    fields.update(overrides)
    return BridgeConfidence(**fields)  # type: ignore[arg-type]


def _empty_evidence_section() -> EvidenceSection:
    return EvidenceSection(
        families=[],
        total_signals=0,
        signals_supporting_verdict=0,
        signals_contradicting_verdict=0,
        signals_neutral=0,
    )


class TestReturnType:
    def test_returns_confidence_section(self) -> None:
        result = translate_confidence(
            _bridge_confidence(), [_fact("f1", 0.9, 0.9)], _empty_evidence_section(), 0.8
        )
        assert isinstance(result, ConfidenceSection)


class TestDimensionAverages:
    def test_extraction_value_is_average(self) -> None:
        facts = [_fact("f1", 0.9, 0.5), _fact("f2", 0.7, 0.5)]
        result = translate_confidence(_bridge_confidence(), facts, _empty_evidence_section(), 0.8)
        assert result.extraction.value == 0.8

    def test_reliability_value_is_average(self) -> None:
        facts = [_fact("f1", 0.5, 0.9), _fact("f2", 0.5, 0.7)]
        result = translate_confidence(_bridge_confidence(), facts, _empty_evidence_section(), 0.8)
        assert result.reliability.value == 0.8

    def test_no_facts_yields_zero_values(self) -> None:
        result = translate_confidence(_bridge_confidence(), [], _empty_evidence_section(), 0.8)
        assert result.extraction.value == 0.0
        assert result.reliability.value == 0.0
        assert result.inference.value == 0.0


class TestOverallLabelThresholds:
    def test_high_at_070(self) -> None:
        result = translate_confidence(
            _bridge_confidence(overall=0.70),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert result.overall_label == ConfidenceLabelEnum.HIGH

    def test_medium_between_045_and_070(self) -> None:
        result = translate_confidence(
            _bridge_confidence(overall=0.50),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert result.overall_label == ConfidenceLabelEnum.MEDIUM

    def test_low_between_025_and_045(self) -> None:
        result = translate_confidence(
            _bridge_confidence(overall=0.30),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert result.overall_label == ConfidenceLabelEnum.LOW

    def test_insufficient_below_025(self) -> None:
        result = translate_confidence(
            _bridge_confidence(overall=0.10),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert result.overall_label == ConfidenceLabelEnum.INSUFFICIENT


class TestDimensionLabelBranches:
    def test_reliability_moderate_label(self) -> None:
        result = translate_confidence(
            _bridge_confidence(), [_fact("f1", 0.9, 0.7)], _empty_evidence_section(), 0.8
        )
        assert result.reliability.label == "moderate"

    def test_hypothesis_weakly_supported_label(self) -> None:
        result = translate_confidence(
            _bridge_confidence(), [_fact("f1", 0.9, 0.9)], _empty_evidence_section(), 0.2
        )
        assert "weakly supported" in result.hypothesis.label


class TestDisclaimer:
    def test_disclaimer_equals_constant(self) -> None:
        result = translate_confidence(
            _bridge_confidence(), [_fact("f1", 0.9, 0.9)], _empty_evidence_section(), 0.8
        )
        assert result.disclaimer == EXAMINA_DISCLAIMER


class TestLimitations:
    def test_unresolved_contradictions_adds_limitation(self) -> None:
        result = translate_confidence(
            _bridge_confidence(unresolved_contradictions=2),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert any("2 signal contradiction" in item for item in result.limitations)

    def test_low_reliability_fact_adds_limitation(self) -> None:
        result = translate_confidence(
            _bridge_confidence(),
            [_fact("f1", 0.9, 0.5)],
            _empty_evidence_section(),
            0.8,
        )
        assert any("limited accuracy" in item for item in result.limitations)

    def test_limitations_always_has_at_least_one_item(self) -> None:
        result = translate_confidence(_bridge_confidence(), [], _empty_evidence_section(), 0.8)
        assert len(result.limitations) >= 1


class TestPenaltyNote:
    def test_penalty_at_or_below_005_produces_no_penalty_note(self) -> None:
        result = translate_confidence(
            _bridge_confidence(penalty_from_contradictions=0.05),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert "No contradictions" in result.penalty.note.text

    def test_penalty_above_005_produces_dynamic_note(self) -> None:
        result = translate_confidence(
            _bridge_confidence(penalty_from_contradictions=0.2),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        assert "20%" in result.penalty.note.text


class TestLanguageCompliance:
    def test_all_note_strings_pass_language_check(self) -> None:
        result = translate_confidence(
            _bridge_confidence(penalty_from_contradictions=0.2, unresolved_contradictions=1),
            [_fact("f1", 0.9, 0.9)],
            _empty_evidence_section(),
            0.8,
        )
        for dimension in (
            result.extraction,
            result.reliability,
            result.inference,
            result.hypothesis,
            result.penalty,
        ):
            check_language(dimension.note.text, context="test")
