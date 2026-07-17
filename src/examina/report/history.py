"""
History reconstruction — converts BridgeTimelineEvents into the report's
HistorySection.
"""

from __future__ import annotations

from examina.bridge.types import BridgeFact, BridgeTimelineEvent
from examina.report.schema import CertaintyEnum, HistoryEvent, HistorySection, TraceableString

_CERTAINTY_NOTE: dict[CertaintyEnum, str] = {
    CertaintyEnum.CONFIRMED: "This event is well-supported by multiple consistent signals.",
    CertaintyEnum.PROBABLE: (
        "This event is supported by available signals but cannot be independently verified."
    ),
    CertaintyEnum.INFERRED: (
        "This event is inferred from indirect evidence and should be treated with caution."
    ),
}


def _certainty_from_confidence(confidence: float) -> CertaintyEnum:
    if confidence >= 0.75:
        return CertaintyEnum.CONFIRMED
    if confidence >= 0.45:
        return CertaintyEnum.PROBABLE
    return CertaintyEnum.INFERRED


def _build_event(event: BridgeTimelineEvent) -> HistoryEvent:
    certainty = _certainty_from_confidence(event.confidence)
    return HistoryEvent(
        sequence=event.sequence,
        description=TraceableString(
            text=event.description, trace_ids=[], generated=False
        ).checked(),
        certainty=certainty,
        certainty_note=TraceableString(
            text=_CERTAINTY_NOTE[certainty], trace_ids=[], generated=True
        ).checked(),
        supporting_signals=[],
    )


def build_history(
    timeline_events: list[BridgeTimelineEvent],
    facts: list[BridgeFact],
) -> HistorySection:
    del facts  # TD-003: signal_ids wiring deferred to Phase 3 integration

    events = [_build_event(event) for event in timeline_events]

    reconstruction_complete = all(
        event.certainty in (CertaintyEnum.CONFIRMED, CertaintyEnum.PROBABLE) for event in events
    )

    unknown_gaps: list[str] = []
    if not timeline_events:
        unknown_gaps.append(
            "No processing history could be reconstructed from available signals."
        )

    return HistorySection(
        events=events,
        reconstruction_complete=reconstruction_complete,
        unknown_gaps=unknown_gaps,
    )
