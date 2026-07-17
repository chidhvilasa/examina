"""Tests for src/examina/bridge/validator.py — see specs/BRIDGE_SPEC_v1.1.md."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from examina.bridge.types import BridgeError, BridgeResult
from examina.bridge.validator import parse_bridge_payload, validate_bridge_payload


def _valid_payload() -> dict[str, Any]:
    return {
        "bridge_version": "bridge:1.0",
        "prism_version": "0.3.1",
        "rule_set_version": "1.0.0",
        "extractor_versions": {"jpeg_adapter": "1.0.0"},
        "processing_time_ms": 42,
        "partial_analysis": False,
        "partial_reason": None,
        "errors": [],
        "facts": [
            {
                "fact_id": "fact-1",
                "statement": "This file declares a creation timestamp.",
                "fact_type": "PROVENANCE",
                "provenance_source_type": "declared",
                "extractor": "exif_extractor:1.0.0",
                "extraction_confidence": 0.9,
                "source_reliability": 0.8,
                "raw_value": {"key": "value"},
            }
        ],
        "contradictions": [
            {
                "contradiction_id": "contradiction-1",
                "fact_a_id": "fact-1",
                "fact_b_id": "fact-2",
                "severity": "HIGH",
                "explanation": "Two facts disagree.",
                "confidence_impact": -0.3,
                "top_resolution": "One signal may be unreliable.",
            }
        ],
        "hypotheses": [
            {
                "hypothesis_id": "hyp-2",
                "description": "Second hypothesis.",
                "confidence": 0.3,
                "rank": 2,
            },
            {
                "hypothesis_id": "hyp-1",
                "description": "First hypothesis.",
                "confidence": 0.6,
                "rank": 1,
            },
        ],
        "timeline": [
            {"sequence": 1, "description": "File was created.", "confidence": 0.7},
        ],
        "reconstruction_confidence": {
            "overall": 0.55,
            "penalty_from_contradictions": 0.1,
            "unresolved_contradictions": 1,
            "active_hypotheses": 2,
        },
    }


class TestValidateBridgePayload:
    def test_valid_complete_payload_passes(self) -> None:
        validate_bridge_payload(_valid_payload())  # must not raise

    def test_missing_bridge_version_raises(self) -> None:
        payload = _valid_payload()
        del payload["bridge_version"]
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_unsupported_bridge_version_raises(self) -> None:
        payload = _valid_payload()
        payload["bridge_version"] = "bridge:99.0"
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_missing_facts_key_raises(self) -> None:
        payload = _valid_payload()
        del payload["facts"]
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_missing_hypotheses_key_raises(self) -> None:
        payload = _valid_payload()
        del payload["hypotheses"]
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_missing_timeline_key_raises(self) -> None:
        payload = _valid_payload()
        del payload["timeline"]
        with pytest.raises(BridgeError):
            validate_bridge_payload(payload)

    def test_missing_contradictions_key_raises(self) -> None:
        payload = _valid_payload()
        del payload["contradictions"]
        with pytest.raises(BridgeError):
            validate_bridge_payload(payload)

    def test_missing_reconstruction_confidence_raises(self) -> None:
        payload = _valid_payload()
        del payload["reconstruction_confidence"]
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_missing_overall_in_reconstruction_confidence_raises(self) -> None:
        payload = _valid_payload()
        del payload["reconstruction_confidence"]["overall"]
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_non_float_overall_in_reconstruction_confidence_raises(self) -> None:
        payload = _valid_payload()
        payload["reconstruction_confidence"]["overall"] = "not-a-number"
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_bool_overall_in_reconstruction_confidence_raises(self) -> None:
        payload = _valid_payload()
        payload["reconstruction_confidence"]["overall"] = True
        with pytest.raises(BridgeError) as exc_info:
            validate_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_facts_not_a_list_raises(self) -> None:
        payload = _valid_payload()
        payload["facts"] = "not-a-list"
        with pytest.raises(BridgeError):
            validate_bridge_payload(payload)

    def test_reconstruction_confidence_not_a_dict_raises(self) -> None:
        payload = _valid_payload()
        payload["reconstruction_confidence"] = "not-a-dict"
        with pytest.raises(BridgeError):
            validate_bridge_payload(payload)

    def test_never_raises_non_bridge_error(self) -> None:
        payload: dict[str, Any] = {}
        try:
            validate_bridge_payload(payload)
        except BridgeError:
            pass
        except Exception as exc:  # pragma: no cover - failure path documentation
            pytest.fail(
                f"validate_bridge_payload raised {type(exc).__name__}, not BridgeError: {exc}"
            )


class TestParseBridgePayload:
    def test_returns_bridge_result_from_valid_payload(self) -> None:
        result = parse_bridge_payload(_valid_payload())
        assert isinstance(result, BridgeResult)

    def test_hypotheses_sorted_by_rank(self) -> None:
        result = parse_bridge_payload(_valid_payload())
        ranks = [h.rank for h in result.hypotheses]
        assert ranks == sorted(ranks)
        assert ranks == [1, 2]
        assert result.hypotheses[0].hypothesis_id == "hyp-1"

    def test_fact_has_correct_fact_id(self) -> None:
        result = parse_bridge_payload(_valid_payload())
        assert result.facts[0].fact_id == "fact-1"

    def test_contradiction_has_correct_contradiction_id(self) -> None:
        result = parse_bridge_payload(_valid_payload())
        assert result.contradictions[0].contradiction_id == "contradiction-1"

    def test_confidence_impact_is_negative(self) -> None:
        result = parse_bridge_payload(_valid_payload())
        assert result.contradictions[0].confidence_impact <= 0

    def test_malformed_fact_dict_raises_invalid_response(self) -> None:
        payload = _valid_payload()
        del payload["facts"][0]["statement"]
        with pytest.raises(BridgeError) as exc_info:
            parse_bridge_payload(payload)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_reconstruction_confidence_overall_matches_payload(self) -> None:
        payload = _valid_payload()
        result = parse_bridge_payload(payload)
        expected = payload["reconstruction_confidence"]["overall"]
        assert result.reconstruction_confidence.overall == expected

    def test_deep_copy_of_payload_unaffected_by_parsing(self) -> None:
        payload = _valid_payload()
        original = copy.deepcopy(payload)
        parse_bridge_payload(payload)
        assert payload == original
