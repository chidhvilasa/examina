"""
Bridge payload validator — verifies a JSON blob received from PRISM
conforms to the bridge schema (specs/BRIDGE_SPEC_v1.1.md) before EXAMINA
parses it into typed `Bridge*` objects.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from examina.bridge.types import (
    BridgeConfidence,
    BridgeContradiction,
    BridgeError,
    BridgeFact,
    BridgeHypothesis,
    BridgeResult,
    BridgeTimelineEvent,
)

SUPPORTED_BRIDGE_VERSIONS = frozenset({"bridge:1.0"})

_REQUIRED_LIST_FIELDS = ("facts", "hypotheses", "timeline", "contradictions")


def validate_bridge_payload(payload: dict[str, Any]) -> None:
    """Raise BridgeError(code=INVALID_RESPONSE) if `payload` does not
    structurally conform to the bridge schema. Returns None on success.
    Never raises any exception other than BridgeError.
    """
    bridge_version = payload.get("bridge_version")
    if bridge_version is None:
        raise BridgeError(code="INVALID_RESPONSE", message="bridge_version key is missing")
    if bridge_version not in SUPPORTED_BRIDGE_VERSIONS:
        raise BridgeError(
            code="INVALID_RESPONSE",
            message=f"unsupported bridge_version: {bridge_version!r}",
        )

    for field_name in _REQUIRED_LIST_FIELDS:
        if field_name not in payload:
            raise BridgeError(
                code="INVALID_RESPONSE", message=f"{field_name!r} key is missing"
            )
        if not isinstance(payload[field_name], list):
            raise BridgeError(
                code="INVALID_RESPONSE", message=f"{field_name!r} must be a list"
            )

    confidence = payload.get("reconstruction_confidence")
    if confidence is None:
        raise BridgeError(
            code="INVALID_RESPONSE", message="reconstruction_confidence key is missing"
        )
    if not isinstance(confidence, dict):
        raise BridgeError(
            code="INVALID_RESPONSE", message="reconstruction_confidence must be a dict"
        )

    overall = confidence.get("overall")
    if overall is None:
        raise BridgeError(
            code="INVALID_RESPONSE",
            message="reconstruction_confidence.overall key is missing",
        )
    if not isinstance(overall, float | int) or isinstance(overall, bool):
        raise BridgeError(
            code="INVALID_RESPONSE",
            message="reconstruction_confidence.overall must be a float",
        )


def _parse_fact(payload_fact: dict[str, Any]) -> BridgeFact:
    return BridgeFact(
        fact_id=payload_fact["fact_id"],
        statement=payload_fact["statement"],
        fact_type=payload_fact["fact_type"],
        provenance_source_type=payload_fact["provenance_source_type"],
        extractor=payload_fact["extractor"],
        extraction_confidence=payload_fact["extraction_confidence"],
        source_reliability=payload_fact["source_reliability"],
        raw_value=payload_fact.get("raw_value", {}),
    )


def _parse_contradiction(payload_contradiction: dict[str, Any]) -> BridgeContradiction:
    return BridgeContradiction(
        contradiction_id=payload_contradiction["contradiction_id"],
        severity=payload_contradiction["severity"],
        explanation=payload_contradiction["explanation"],
        confidence_impact=payload_contradiction["confidence_impact"],
        top_resolution=payload_contradiction["top_resolution"],
    )


def _parse_hypothesis(payload_hypothesis: dict[str, Any]) -> BridgeHypothesis:
    return BridgeHypothesis(
        hypothesis_id=payload_hypothesis["hypothesis_id"],
        description=payload_hypothesis["description"],
        confidence=payload_hypothesis["confidence"],
        rank=payload_hypothesis["rank"],
    )


def _parse_timeline_event(payload_event: dict[str, Any]) -> BridgeTimelineEvent:
    return BridgeTimelineEvent(
        sequence=payload_event["sequence"],
        description=payload_event["description"],
        confidence=payload_event["confidence"],
    )


def _parse_confidence(payload_confidence: dict[str, Any]) -> BridgeConfidence:
    return BridgeConfidence(
        overall=payload_confidence["overall"],
        penalty_from_contradictions=payload_confidence["penalty_from_contradictions"],
        unresolved_contradictions=payload_confidence["unresolved_contradictions"],
        active_hypotheses=payload_confidence["active_hypotheses"],
    )


def parse_bridge_payload(payload: dict[str, Any]) -> BridgeResult:
    """Parse an already-validated bridge payload dict into a BridgeResult.

    Call validate_bridge_payload(payload) first. Raises BridgeError with
    code INVALID_RESPONSE (naming the failing field) on any parsing
    error. Never raises any exception other than BridgeError.
    """
    try:
        hypotheses = sorted(
            (_parse_hypothesis(h) for h in payload["hypotheses"]), key=lambda h: h.rank
        )
        result = BridgeResult(
            request_id=payload.get("request_id", uuid4()),
            bridge_version=payload["bridge_version"],
            prism_version=payload.get("prism_version", "unknown"),
            rule_set_version=payload.get("rule_set_version", "unknown"),
            extractor_versions=payload.get("extractor_versions", {}),
            processing_time_ms=payload.get("processing_time_ms", 0),
            facts=[_parse_fact(f) for f in payload["facts"]],
            contradictions=[_parse_contradiction(c) for c in payload["contradictions"]],
            hypotheses=hypotheses,
            timeline=[_parse_timeline_event(e) for e in payload["timeline"]],
            reconstruction_confidence=_parse_confidence(payload["reconstruction_confidence"]),
            errors=payload.get("errors", []),
            partial_analysis=payload.get("partial_analysis", False),
            partial_reason=payload.get("partial_reason"),
        )
    except (KeyError, TypeError, ValidationError) as exc:
        raise BridgeError(
            code="INVALID_RESPONSE", message=f"failed to parse bridge payload: {exc}"
        ) from exc

    return result
