"""
Confidence translation — turns numeric BridgeConfidence into the five
plain-language dimensions of ConfidenceSection.

See specs/CONFIDENCE_TRANSLATION_v1.0.md.
"""

from __future__ import annotations

from examina.bridge.types import BridgeConfidence, BridgeFact
from examina.report.schema import (
    EXAMINA_DISCLAIMER,
    ConfidenceDimension,
    ConfidenceLabelEnum,
    ConfidenceSection,
    EvidenceSection,
    TraceableString,
)

_NO_PENALTY_NOTE = "No contradictions were significant enough to reduce overall confidence."


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _extraction_dimension(facts: list[BridgeFact]) -> ConfidenceDimension:
    value = _average([fact.extraction_confidence for fact in facts])
    if value >= 0.85:
        label = "high"
    elif value >= 0.65:
        label = "moderate"
    else:
        label = "limited"
    note_text = f"Our analyzers read the file's signals with {label} reliability."
    return ConfidenceDimension(
        value=value,
        label=label,
        note=TraceableString(text=note_text, trace_ids=[], generated=True).checked(),
    )


def _reliability_dimension(facts: list[BridgeFact]) -> ConfidenceDimension:
    value = _average([fact.source_reliability for fact in facts])
    if value >= 0.80:
        label = "strong"
    elif value >= 0.60:
        label = "moderate"
    else:
        label = "limited"
    note_text = f"The analyzers used here have {label} accuracy on verified test datasets."
    return ConfidenceDimension(
        value=value,
        label=label,
        note=TraceableString(text=note_text, trace_ids=[], generated=True).checked(),
    )


def _inference_dimension(facts: list[BridgeFact]) -> ConfidenceDimension:
    value = _average([fact.extraction_confidence * fact.source_reliability for fact in facts])
    if value >= 0.75:
        label = "well-supported"
    elif value >= 0.55:
        label = "reasonable"
    else:
        label = "uncertain"
    note_text = f"The interpretation of detected signals is {label}."
    return ConfidenceDimension(
        value=value,
        label=label,
        note=TraceableString(text=note_text, trace_ids=[], generated=True).checked(),
    )


def _hypothesis_dimension(top_hypothesis_confidence: float) -> ConfidenceDimension:
    value = top_hypothesis_confidence
    if value >= 0.70:
        label = "well-supported by the evidence"
    elif value >= 0.45:
        label = "moderately supported"
    else:
        label = "weakly supported — treat with caution"
    note_text = f"The overall assessment is {label}."
    return ConfidenceDimension(
        value=value,
        label=label,
        note=TraceableString(text=note_text, trace_ids=[], generated=True).checked(),
    )


def _penalty_dimension(bridge_confidence: BridgeConfidence) -> ConfidenceDimension:
    value = bridge_confidence.penalty_from_contradictions
    if value <= 0.05:
        label = "minimal"
        note_text = _NO_PENALTY_NOTE
    else:
        label = "reduced"
        note_text = f"Contradictions between signals reduced overall confidence by {value:.0%}."
    return ConfidenceDimension(
        value=value,
        label=label,
        note=TraceableString(text=note_text, trace_ids=[], generated=True).checked(),
    )


def _overall_label(overall: float) -> ConfidenceLabelEnum:
    if overall >= 0.70:
        return ConfidenceLabelEnum.HIGH
    if overall >= 0.45:
        return ConfidenceLabelEnum.MEDIUM
    if overall >= 0.25:
        return ConfidenceLabelEnum.LOW
    return ConfidenceLabelEnum.INSUFFICIENT


def _limitations(bridge_confidence: BridgeConfidence, facts: list[BridgeFact]) -> list[str]:
    limitations = [
        "This analysis reflects the state of EXAMINA's analyzers at the time of "
        "report generation. New content generation techniques may not be detected."
    ]
    if any(fact.source_reliability < 0.65 for fact in facts):
        limitations.append(
            "One or more analyzers have limited accuracy on benchmark datasets. "
            "Signals from these analyzers have been weighted accordingly."
        )
    if bridge_confidence.unresolved_contradictions > 0:
        limitations.append(
            f"{bridge_confidence.unresolved_contradictions} signal contradiction(s) "
            "could not be fully resolved. These are reflected in the confidence penalty."
        )
    return limitations


def translate_confidence(
    bridge_confidence: BridgeConfidence,
    facts: list[BridgeFact],
    evidence_section: EvidenceSection,
    top_hypothesis_confidence: float,
) -> ConfidenceSection:
    del evidence_section  # not needed for dimension computation; kept for signature parity

    return ConfidenceSection(
        overall=bridge_confidence.overall,
        overall_label=_overall_label(bridge_confidence.overall),
        extraction=_extraction_dimension(facts),
        reliability=_reliability_dimension(facts),
        inference=_inference_dimension(facts),
        hypothesis=_hypothesis_dimension(top_hypothesis_confidence),
        penalty=_penalty_dimension(bridge_confidence),
        limitations=_limitations(bridge_confidence, facts),
        disclaimer=EXAMINA_DISCLAIMER,
    )
