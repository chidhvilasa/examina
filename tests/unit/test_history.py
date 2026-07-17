"""Tests for src/examina/report/history.py."""

from __future__ import annotations

from examina.bridge.types import BridgeTimelineEvent
from examina.language.guard import check_language
from examina.report.history import build_history
from examina.report.schema import CertaintyEnum


def _event(sequence: int, confidence: float) -> BridgeTimelineEvent:
    return BridgeTimelineEvent(
        sequence=sequence, description=f"Event at sequence {sequence}.", confidence=confidence
    )


class TestEmptyTimeline:
    def test_empty_timeline_produces_unknown_gaps(self) -> None:
        section = build_history([], [])
        assert len(section.unknown_gaps) == 1
        assert section.events == []


class TestEventOrdering:
    def test_events_returned_in_sequence_order(self) -> None:
        events = [_event(1, 0.9), _event(2, 0.9)]
        section = build_history(events, [])
        assert [e.sequence for e in section.events] == [1, 2]


class TestCertaintyMapping:
    def test_confidence_075_produces_confirmed(self) -> None:
        section = build_history([_event(1, 0.75)], [])
        assert section.events[0].certainty == CertaintyEnum.CONFIRMED

    def test_confidence_between_045_and_075_produces_probable(self) -> None:
        section = build_history([_event(1, 0.5)], [])
        assert section.events[0].certainty == CertaintyEnum.PROBABLE

    def test_confidence_below_045_produces_inferred(self) -> None:
        section = build_history([_event(1, 0.2)], [])
        assert section.events[0].certainty == CertaintyEnum.INFERRED


class TestReconstructionComplete:
    def test_all_confirmed_or_probable_is_complete(self) -> None:
        section = build_history([_event(1, 0.9), _event(2, 0.5)], [])
        assert section.reconstruction_complete is True

    def test_any_inferred_is_incomplete(self) -> None:
        section = build_history([_event(1, 0.9), _event(2, 0.1)], [])
        assert section.reconstruction_complete is False


class TestLanguageCompliance:
    def test_all_description_text_passes_language_check(self) -> None:
        section = build_history([_event(1, 0.9), _event(2, 0.5), _event(3, 0.1)], [])
        for event in section.events:
            check_language(event.description.text, context="test")
            check_language(event.certainty_note.text, context="test")
