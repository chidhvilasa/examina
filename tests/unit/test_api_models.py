"""Tests for src/examina/api/models.py."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from examina.api.models import AnalyzeResponse, FeedbackRequest, IncorrectAnalysisRequest


class TestAnalyzeResponse:
    def test_instantiates_with_all_required_fields(self) -> None:
        response = AnalyzeResponse(
            report_id="report-1",
            file_hash="a" * 64,
            file_type="JPEG",
            status="complete",
            verdict="INSUFFICIENT_EVIDENCE",
            confidence_label="INSUFFICIENT",
            overall_confidence=0.5,
            active_hypotheses=2,
            unresolved_contradictions=0,
            natural_language_summary="Summary text.",
            recommendation="Recommendation text.",
            what_would_change="What would change text.",
            report_url="/report/report-1",
            expires_at="2026-01-01T00:00:00+00:00",
        )
        assert response.report_id == "report-1"
        assert response.status == "complete"


class TestFeedbackRequestUnderstandabilityScore:
    def test_score_of_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(understandability_score=0)

    def test_score_of_six_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(understandability_score=6)

    @pytest.mark.parametrize("score", [1, 2, 3, 4, 5])
    def test_score_1_to_5_is_valid(self, score: int) -> None:
        request = FeedbackRequest(understandability_score=score)
        assert request.understandability_score == score

    def test_score_none_is_valid(self) -> None:
        request = FeedbackRequest(understandability_score=None)
        assert request.understandability_score is None


class TestFeedbackRequestCommentLength:
    def test_optional_comment_over_500_chars_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(optional_comment="x" * 501)

    def test_optional_comment_at_500_chars_is_valid(self) -> None:
        request = FeedbackRequest(optional_comment="x" * 500)
        assert request.optional_comment is not None
        assert len(request.optional_comment) == 500

    def test_confusing_section_over_100_chars_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(confusing_section="x" * 101)


class TestIncorrectAnalysisRequest:
    def test_user_comment_over_500_chars_raises(self) -> None:
        with pytest.raises(ValidationError):
            IncorrectAnalysisRequest(report_id="report-1", user_comment="x" * 501)

    def test_user_comment_at_500_chars_is_valid(self) -> None:
        request = IncorrectAnalysisRequest(report_id="report-1", user_comment="x" * 500)
        assert request.user_comment is not None
