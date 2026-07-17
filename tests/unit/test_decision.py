"""Tests for src/examina/report/decision.py — see specs/DECISION_MODEL_v1.0.md."""

from __future__ import annotations

from examina.bridge.types import BridgeContradiction, BridgeHypothesis
from examina.language.guard import FORBIDDEN_WORDS, check_language
from examina.report.decision import _label_from_overall, determine_verdict, generate_assessment
from examina.report.schema import ConfidenceLabelEnum, VerdictEnum


def _hypothesis(
    hypothesis_id: str, description: str, confidence: float, rank: int
) -> BridgeHypothesis:
    return BridgeHypothesis(
        hypothesis_id=hypothesis_id, description=description, confidence=confidence, rank=rank
    )


def _contradiction(severity: str = "LOW") -> BridgeContradiction:
    return BridgeContradiction(
        contradiction_id="contradiction-1",
        severity=severity,  # type: ignore[arg-type]
        explanation="Signals disagree.",
        confidence_impact=-0.1,
        top_resolution="Manual review.",
    )


class TestDetermineVerdict:
    def test_generative_model_produces_ai_generated(self) -> None:
        hypotheses = [_hypothesis("h1", "Consistent with a generative model origin.", 0.6, 1)]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.LIKELY_AI_GENERATED
        assert label == ConfidenceLabelEnum.HIGH

    def test_camera_not_reencoded_produces_authentic(self) -> None:
        hypotheses = [
            _hypothesis(
                "h1", "Consistent with a camera capture that has not been re-encoded.", 0.6, 1
            )
        ]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.LIKELY_AUTHENTIC
        assert label == ConfidenceLabelEnum.HIGH

    def test_reencoded_produces_ai_assisted(self) -> None:
        hypotheses = [_hypothesis("h1", "File appears to have been re-encoded.", 0.5, 1)]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.AI_ASSISTED
        assert label == ConfidenceLabelEnum.HIGH

    def test_post_processed_produces_manipulated(self) -> None:
        hypotheses = [_hypothesis("h1", "File appears to have been post-processed.", 0.5, 1)]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.LIKELY_MANIPULATED
        assert label == ConfidenceLabelEnum.HIGH

    def test_composited_produces_manipulated(self) -> None:
        hypotheses = [_hypothesis("h1", "File appears to have been composited.", 0.5, 1)]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.LIKELY_MANIPULATED

    def test_two_competing_hypotheses_produce_mixed_signals(self) -> None:
        hypotheses = [
            _hypothesis("h1", "This does not match any known template phrase.", 0.4, 1),
            _hypothesis("h2", "Second competing explanation.", 0.36, 2),
        ]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.MIXED_SIGNALS
        assert label == ConfidenceLabelEnum.HIGH

    def test_low_overall_confidence_produces_insufficient_evidence(self) -> None:
        hypotheses = [_hypothesis("h1", "Consistent with a generative model origin.", 0.9, 1)]
        verdict, label = determine_verdict(hypotheses, 0.1)
        assert verdict == VerdictEnum.INSUFFICIENT_EVIDENCE
        assert label == ConfidenceLabelEnum.INSUFFICIENT

    def test_empty_hypotheses_produces_insufficient_evidence(self) -> None:
        verdict, label = determine_verdict([], 0.8)
        assert verdict == VerdictEnum.INSUFFICIENT_EVIDENCE
        assert label == ConfidenceLabelEnum.INSUFFICIENT

    def test_no_matching_rule_and_no_second_hypothesis_is_insufficient(self) -> None:
        hypotheses = [_hypothesis("h1", "This does not match any known template phrase.", 0.4, 1)]
        verdict, label = determine_verdict(hypotheses, 0.8)
        assert verdict == VerdictEnum.INSUFFICIENT_EVIDENCE
        assert label == ConfidenceLabelEnum.INSUFFICIENT

    def test_medium_label_range(self) -> None:
        hypotheses = [_hypothesis("h1", "Consistent with a generative model origin.", 0.9, 1)]
        _, label = determine_verdict(hypotheses, 0.5)
        assert label == ConfidenceLabelEnum.MEDIUM

    def test_low_label_range(self) -> None:
        hypotheses = [_hypothesis("h1", "Consistent with a generative model origin.", 0.9, 1)]
        _, label = determine_verdict(hypotheses, 0.3)
        assert label == ConfidenceLabelEnum.LOW

    def test_label_from_overall_insufficient_branch(self) -> None:
        assert _label_from_overall(0.1) == ConfidenceLabelEnum.INSUFFICIENT


class TestGenerateAssessment:
    def test_critical_contradiction_adds_escalation_text(self) -> None:
        hypotheses = [_hypothesis("h1", "Consistent with a generative model origin.", 0.6, 1)]
        assessment = generate_assessment(
            VerdictEnum.LIKELY_AI_GENERATED,
            ConfidenceLabelEnum.HIGH,
            hypotheses,
            [_contradiction(severity="CRITICAL")],
            ["metadata_000"],
        )
        assert "high-severity signal conflicts" in assessment.verdict_plain.text

    def test_non_critical_contradiction_does_not_escalate(self) -> None:
        hypotheses = [_hypothesis("h1", "Consistent with a generative model origin.", 0.6, 1)]
        assessment = generate_assessment(
            VerdictEnum.LIKELY_AI_GENERATED,
            ConfidenceLabelEnum.HIGH,
            hypotheses,
            [_contradiction(severity="LOW")],
            ["metadata_000"],
        )
        assert "high-severity signal conflicts" not in assessment.verdict_plain.text

    def test_likely_authentic_recommendation_varies_by_confidence_label(self) -> None:
        for label, expected in (
            (ConfidenceLabelEnum.HIGH, "Standard editorial verification"),
            (ConfidenceLabelEnum.MEDIUM, "Corroborate with source contact"),
            (ConfidenceLabelEnum.LOW, "Do not rely on this analysis alone"),
        ):
            assessment = generate_assessment(VerdictEnum.LIKELY_AUTHENTIC, label, [], [], [])
            assert expected in assessment.recommendation.text

    def test_all_verdicts_produce_language_clean_text(self) -> None:
        for verdict in VerdictEnum:
            assessment = generate_assessment(verdict, ConfidenceLabelEnum.MEDIUM, [], [], [])
            check_language(assessment.verdict_plain.text, context="test")
            check_language(assessment.recommendation.text, context="test")
            check_language(assessment.what_would_change.text, context="test")

    def test_no_forbidden_words_in_any_template_output(self) -> None:
        for verdict in VerdictEnum:
            for label in ConfidenceLabelEnum:
                if (
                    verdict == VerdictEnum.LIKELY_AUTHENTIC
                    and label == ConfidenceLabelEnum.INSUFFICIENT
                ):
                    continue  # LIKELY_AUTHENTIC never pairs with INSUFFICIENT
                assessment = generate_assessment(verdict, label, [], [], [])
                combined = " ".join(
                    [
                        assessment.verdict_plain.text,
                        assessment.recommendation.text,
                        assessment.what_would_change.text,
                    ]
                ).lower()
                for word in FORBIDDEN_WORDS:
                    assert word not in combined
