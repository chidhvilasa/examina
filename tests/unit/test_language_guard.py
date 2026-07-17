"""Tests for src/examina/language/guard.py — see specs/LANGUAGE_SPEC_v1.0.md."""

from __future__ import annotations

import pytest

from examina.language.guard import LanguageViolationError, check_language

FORBIDDEN_EXAMPLES = [
    "fake",
    "FAKE",
    "forgery",
    "fraud",
    "fraudulent",
    "definitely",
    "guaranteed",
    "confirmed",
    "proof",
    "proven",
]


class TestForbiddenWords:
    @pytest.mark.parametrize("word", FORBIDDEN_EXAMPLES)
    def test_forbidden_word_raises(self, word: str) -> None:
        with pytest.raises(LanguageViolationError):
            check_language(f"This text contains the word {word} in it.")


class TestWholeWordMatching:
    def test_makeshift_does_not_raise(self) -> None:
        check_language("This was a makeshift solution.")

    def test_disproof_does_not_raise(self) -> None:
        check_language("There is no disproof of this claim.")


class TestCleanAndEmptyText:
    def test_clean_text_returns_none(self) -> None:
        assert check_language("This image shows signs consistent with editing.") is None

    def test_empty_string_returns_none(self) -> None:
        assert check_language("") is None


class TestLanguageViolationErrorContents:
    def test_error_contains_word_and_context(self) -> None:
        with pytest.raises(LanguageViolationError) as exc_info:
            check_language("This is fake.", context="EvidenceSection.summary")
        assert exc_info.value.word == "fake"
        assert exc_info.value.context == "EvidenceSection.summary"
