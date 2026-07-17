"""Tests for src/examina/bridge/types.py — see specs/BRIDGE_SPEC_v1.1.md."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from examina.bridge.types import (
    BridgeConfidence,
    BridgeContradiction,
    BridgeError,
    BridgeFact,
    BridgeHypothesis,
    BridgeRequest,
    BridgeResult,
    BridgeTimelineEvent,
)

VALID_HASH = "a" * 64


def _valid_request(**overrides: object) -> BridgeRequest:
    fields: dict[str, object] = {
        "file_bytes": b"stub-bytes",
        "file_hash": VALID_HASH,
        "file_type": "JPEG",
        "examina_version": "0.1.0",
    }
    fields.update(overrides)
    return BridgeRequest(**fields)  # type: ignore[arg-type]


def _valid_fact(**overrides: object) -> BridgeFact:
    fields: dict[str, object] = {
        "fact_id": "fact-1",
        "statement": "This file declares a creation timestamp.",
        "fact_type": "PROVENANCE",
        "provenance_source_type": "declared",
        "extractor": "exif-extractor:1.0",
        "extraction_confidence": 0.9,
        "source_reliability": 0.8,
        "raw_value": {"key": "value"},
    }
    fields.update(overrides)
    return BridgeFact(**fields)  # type: ignore[arg-type]


def _valid_contradiction(**overrides: object) -> BridgeContradiction:
    fields: dict[str, object] = {
        "contradiction_id": "contradiction-1",
        "severity": "HIGH",
        "explanation": "Declared timestamp conflicts with structural metadata.",
        "confidence_impact": -0.2,
        "top_resolution": "Prefer the structural metadata timestamp.",
    }
    fields.update(overrides)
    return BridgeContradiction(**fields)  # type: ignore[arg-type]


def _valid_hypothesis(**overrides: object) -> BridgeHypothesis:
    fields: dict[str, object] = {
        "hypothesis_id": "hyp-1",
        "description": "This file is consistent with an unedited original.",
        "confidence": 0.6,
        "rank": 1,
    }
    fields.update(overrides)
    return BridgeHypothesis(**fields)  # type: ignore[arg-type]


def _valid_timeline_event(**overrides: object) -> BridgeTimelineEvent:
    fields: dict[str, object] = {
        "sequence": 1,
        "description": "File was created.",
        "confidence": 0.7,
    }
    fields.update(overrides)
    return BridgeTimelineEvent(**fields)  # type: ignore[arg-type]


def _valid_confidence(**overrides: object) -> BridgeConfidence:
    fields: dict[str, object] = {
        "overall": 0.72,
        "penalty_from_contradictions": 0.0,
        "unresolved_contradictions": 0,
        "active_hypotheses": 1,
    }
    fields.update(overrides)
    return BridgeConfidence(**fields)  # type: ignore[arg-type]


def _valid_result(**overrides: object) -> BridgeResult:
    fields: dict[str, object] = {
        "request_id": UUID(int=1),
        "bridge_version": "bridge:1.0",
        "prism_version": "stub:1.0",
        "rule_set_version": "stub:1.0",
        "extractor_versions": {"stub": "1.0"},
        "processing_time_ms": 0,
        "facts": [_valid_fact()],
        "contradictions": [],
        "hypotheses": [_valid_hypothesis(rank=1), _valid_hypothesis(hypothesis_id="hyp-2", rank=2)],
        "timeline": [_valid_timeline_event()],
        "reconstruction_confidence": _valid_confidence(),
        "errors": [],
        "partial_analysis": False,
        "partial_reason": None,
    }
    fields.update(overrides)
    return BridgeResult(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# BridgeRequest
# ---------------------------------------------------------------------------


class TestBridgeRequest:
    def test_instantiates_correctly(self) -> None:
        request = _valid_request()
        assert request.file_type == "JPEG"
        assert request.file_hash == VALID_HASH
        assert request.clamav_mode == "skip"

    def test_file_hash_wrong_length_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_request(file_hash="a" * 63)

    def test_file_hash_uppercase_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_request(file_hash="A" * 64)

    def test_file_hash_non_hex_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_request(file_hash="z" * 64)

    def test_request_id_auto_generated_is_uuid(self) -> None:
        request = _valid_request()
        assert isinstance(request.request_id, UUID)


# ---------------------------------------------------------------------------
# BridgeFact
# ---------------------------------------------------------------------------


class TestBridgeFact:
    def test_instantiates_correctly(self) -> None:
        fact = _valid_fact()
        assert fact.fact_type == "PROVENANCE"

    def test_extraction_confidence_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_fact(extraction_confidence=-0.1)

    def test_extraction_confidence_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_fact(extraction_confidence=1.1)

    def test_source_reliability_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_fact(source_reliability=-0.1)

    def test_source_reliability_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_fact(source_reliability=1.1)

    def test_empty_statement_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_fact(statement="")


# ---------------------------------------------------------------------------
# BridgeContradiction
# ---------------------------------------------------------------------------


class TestBridgeContradiction:
    def test_instantiates_correctly(self) -> None:
        contradiction = _valid_contradiction()
        assert contradiction.severity == "HIGH"

    def test_confidence_impact_above_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_contradiction(confidence_impact=0.1)

    def test_confidence_impact_below_negative_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_contradiction(confidence_impact=-1.1)

    def test_empty_explanation_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_contradiction(explanation="")


# ---------------------------------------------------------------------------
# BridgeHypothesis
# ---------------------------------------------------------------------------


class TestBridgeHypothesis:
    def test_instantiates_correctly(self) -> None:
        hypothesis = _valid_hypothesis()
        assert hypothesis.rank == 1

    def test_rank_below_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_hypothesis(rank=0)

    def test_confidence_outside_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_hypothesis(confidence=1.1)


# ---------------------------------------------------------------------------
# BridgeTimelineEvent / BridgeConfidence (exercised for coverage)
# ---------------------------------------------------------------------------


class TestBridgeTimelineEventAndConfidence:
    def test_timeline_event_instantiates(self) -> None:
        event = _valid_timeline_event()
        assert event.sequence == 1

    def test_confidence_instantiates(self) -> None:
        confidence = _valid_confidence()
        assert confidence.overall == 0.72


# ---------------------------------------------------------------------------
# BridgeResult
# ---------------------------------------------------------------------------


class TestBridgeResult:
    def test_instantiates_correctly(self) -> None:
        result = _valid_result()
        assert result.bridge_version == "bridge:1.0"
        assert len(result.hypotheses) == 2

    def test_partial_true_reason_none_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_result(partial_analysis=True, partial_reason=None)

    def test_partial_false_reason_set_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_result(partial_analysis=False, partial_reason="some reason")

    def test_hypotheses_non_unique_ranks_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_result(
                hypotheses=[
                    _valid_hypothesis(hypothesis_id="hyp-1", rank=1),
                    _valid_hypothesis(hypothesis_id="hyp-2", rank=1),
                ]
            )

    def test_hypotheses_non_contiguous_ranks_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_result(
                hypotheses=[
                    _valid_hypothesis(hypothesis_id="hyp-1", rank=1),
                    _valid_hypothesis(hypothesis_id="hyp-2", rank=3),
                ]
            )

    def test_hypotheses_not_sorted_ascending_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_result(
                hypotheses=[
                    _valid_hypothesis(hypothesis_id="hyp-2", rank=2),
                    _valid_hypothesis(hypothesis_id="hyp-1", rank=1),
                ]
            )


# ---------------------------------------------------------------------------
# BridgeError
# ---------------------------------------------------------------------------


class TestBridgeError:
    @pytest.mark.parametrize(
        "code",
        [
            "BRIDGE_UNAVAILABLE",
            "VERSION_MISMATCH",
            "ANALYSIS_TIMEOUT",
            "PRISM_ERROR",
            "INVALID_RESPONSE",
        ],
    )
    def test_instantiates_with_each_valid_code(self, code: str) -> None:
        error = BridgeError(code=code, message="something went wrong", request_id=None)  # type: ignore[arg-type]
        assert error.code == code
        assert error.message == "something went wrong"

    def test_is_instance_of_exception(self) -> None:
        error = BridgeError(code="PRISM_ERROR", message="msg", request_id=None)
        assert isinstance(error, Exception)
