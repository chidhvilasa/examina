"""
Decision model — maps PRISM's top hypothesis and overall confidence to a
VerdictEnum, and renders the fixed Assessment templates.

See specs/DECISION_MODEL_v1.0.md.
"""

from __future__ import annotations

from examina.bridge.types import BridgeContradiction, BridgeHypothesis
from examina.report.schema import (
    Assessment,
    ConfidenceLabelEnum,
    TraceableString,
    VerdictEnum,
)

_CRITICAL_ESCALATION_TEXT = (
    " One or more high-severity signal conflicts were detected. These conflicts "
    "have been factored into the confidence score but warrant manual review."
)

_VERDICT_PLAIN: dict[VerdictEnum, str] = {
    VerdictEnum.LIKELY_AUTHENTIC: (
        "Evidence is consistent with authentic origin. Signals examined "
        "do not indicate manipulation or synthetic generation."
    ),
    VerdictEnum.LIKELY_MANIPULATED: (
        "Evidence suggests this file has been modified after original "
        "creation. This does not confirm malicious intent, but publication "
        "requires additional verification."
    ),
    VerdictEnum.LIKELY_AI_GENERATED: (
        "Evidence suggests this file may have been produced by a "
        "generative model. AI-generated images should not be published "
        "as documentary content per most editorial standards."
    ),
    VerdictEnum.AI_ASSISTED: (
        "Evidence suggests this file was captured or created "
        "authentically but subsequently edited, possibly with AI "
        "assistance."
    ),
    VerdictEnum.MIXED_SIGNALS: (
        "Forensic signals are contradictory. A reliable assessment "
        "is not possible with available evidence."
    ),
    VerdictEnum.INSUFFICIENT_EVIDENCE: (
        "There is not enough evidence to support a reliable assessment. "
        "This result should not be used to make a publication decision."
    ),
}

_LIKELY_AUTHENTIC_RECOMMENDATION: dict[ConfidenceLabelEnum, str] = {
    ConfidenceLabelEnum.HIGH: "Standard editorial verification is sufficient.",
    ConfidenceLabelEnum.MEDIUM: "Corroborate with source contact or reverse image search.",
    ConfidenceLabelEnum.LOW: "Do not rely on this analysis alone. Request original file.",
}

_RECOMMENDATION: dict[VerdictEnum, str] = {
    VerdictEnum.LIKELY_MANIPULATED: "Request the original unedited file. Consult a photo editor.",
    VerdictEnum.LIKELY_AI_GENERATED: (
        "Do not publish as documentary content. Seek an authentic source."
    ),
    VerdictEnum.AI_ASSISTED: "Determine the extent of editing. Disclose if material to the story.",
    VerdictEnum.MIXED_SIGNALS: "Request the original file. Consider independent verification.",
    VerdictEnum.INSUFFICIENT_EVIDENCE: (
        "Use other verification methods. Do not rely on this report."
    ),
}

_WHAT_WOULD_CHANGE: dict[VerdictEnum, str] = {
    VerdictEnum.LIKELY_AUTHENTIC: (
        "A matching C2PA credential or original camera RAW file would "
        "increase confidence in this assessment."
    ),
    VerdictEnum.LIKELY_MANIPULATED: (
        "An unedited original file from the same source would allow "
        "comparison and potentially resolve this assessment."
    ),
    VerdictEnum.LIKELY_AI_GENERATED: (
        "A matching camera capture record or C2PA content credential "
        "would contradict this assessment."
    ),
    VerdictEnum.AI_ASSISTED: (
        "Documentation of the editing process or the unedited original "
        "would clarify the extent of post-processing."
    ),
    VerdictEnum.MIXED_SIGNALS: (
        "Additional signals from the original source file or metadata "
        "would help resolve the contradictory evidence."
    ),
    VerdictEnum.INSUFFICIENT_EVIDENCE: (
        "Additional file copies, source metadata, or a C2PA credential "
        "from the creator would enable a more reliable assessment."
    ),
}


def _label_from_overall(overall_confidence: float) -> ConfidenceLabelEnum:
    if overall_confidence >= 0.70:
        return ConfidenceLabelEnum.HIGH
    if overall_confidence >= 0.45:
        return ConfidenceLabelEnum.MEDIUM
    if overall_confidence >= 0.25:
        return ConfidenceLabelEnum.LOW
    return ConfidenceLabelEnum.INSUFFICIENT


def determine_verdict(
    hypotheses: list[BridgeHypothesis],
    overall_confidence: float,
) -> tuple[VerdictEnum, ConfidenceLabelEnum]:
    if overall_confidence < 0.25 or len(hypotheses) == 0:
        return (VerdictEnum.INSUFFICIENT_EVIDENCE, ConfidenceLabelEnum.INSUFFICIENT)

    top = next(h for h in hypotheses if h.rank == 1)
    second = next((h for h in hypotheses if h.rank == 2), None)
    label = _label_from_overall(overall_confidence)
    description = top.description.lower()

    if "generative model" in description and top.confidence > 0.55:
        return (VerdictEnum.LIKELY_AI_GENERATED, label)

    if (
        "camera" in description
        and "not been re-encoded" in description
        and top.confidence > 0.55
    ):
        return (VerdictEnum.LIKELY_AUTHENTIC, label)

    if "re-encoded" in description and top.confidence > 0.45:
        return (VerdictEnum.AI_ASSISTED, label)

    if ("post-processed" in description or "composited" in description) and top.confidence > 0.45:
        return (VerdictEnum.LIKELY_MANIPULATED, label)

    if second is not None and second.confidence > 0.35:
        return (VerdictEnum.MIXED_SIGNALS, label)

    return (VerdictEnum.INSUFFICIENT_EVIDENCE, ConfidenceLabelEnum.INSUFFICIENT)


def generate_assessment(
    verdict: VerdictEnum,
    confidence_label: ConfidenceLabelEnum,
    hypotheses: list[BridgeHypothesis],
    contradictions: list[BridgeContradiction],
    signal_ids: list[str],
) -> Assessment:
    top = next((h for h in hypotheses if h.rank == 1), None)

    verdict_plain_trace_ids = list(signal_ids)
    if top is not None:
        verdict_plain_trace_ids.append(top.hypothesis_id)

    verdict_plain_text = _VERDICT_PLAIN[verdict]
    if any(c.severity == "CRITICAL" for c in contradictions):
        verdict_plain_text += _CRITICAL_ESCALATION_TEXT
        verdict_plain_trace_ids.extend(c.contradiction_id for c in contradictions)

    if verdict == VerdictEnum.LIKELY_AUTHENTIC:
        recommendation_text = _LIKELY_AUTHENTIC_RECOMMENDATION[confidence_label]
    else:
        recommendation_text = _RECOMMENDATION[verdict]

    return Assessment(
        verdict=verdict,
        verdict_plain=TraceableString(
            text=verdict_plain_text, trace_ids=verdict_plain_trace_ids, generated=True
        ).checked(),
        recommendation=TraceableString(
            text=recommendation_text, trace_ids=list(signal_ids), generated=True
        ).checked(),
        what_would_change=TraceableString(
            text=_WHAT_WOULD_CHANGE[verdict], trace_ids=list(signal_ids), generated=True
        ).checked(),
        confidence_label=confidence_label,
    )
