"""
Language guard — enforces specs/LANGUAGE_SPEC_v1.0.md's forbidden
vocabulary (Constitution Principle 4).
"""

from __future__ import annotations

import re

FORBIDDEN_WORDS: frozenset[str] = frozenset(
    {
        "fake",
        "forgery",
        "forged",
        "fraud",
        "fraudulent",
        "definitely",
        "guaranteed",
        "confirmed",
        "proof",
        "proven",
    }
)


class LanguageViolationError(Exception):
    def __init__(self, word: str, context: str) -> None:
        self.word = word
        self.context = context
        self.message = f"Forbidden word '{word}' found in {context}"
        super().__init__(self.message)


def check_language(text: str, context: str = "") -> None:
    """
    Raise LanguageViolationError if `text` contains any FORBIDDEN_WORDS
    word as a whole word (case-insensitive). Never modifies `text`.
    """
    for word in FORBIDDEN_WORDS:
        pattern = rf"(?<![\w-]){re.escape(word)}(?![\w-])"
        if re.search(pattern, text, re.IGNORECASE):
            raise LanguageViolationError(word=word, context=context)
