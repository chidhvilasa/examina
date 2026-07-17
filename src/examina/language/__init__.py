"""
Language package — enforces the EXAMINA Language Specification.
See specs/LANGUAGE_SPEC_v1.0.md.
Forbidden words: fake, forgery, forged, fraud, fraudulent, definitely,
guaranteed, confirmed, proof, proven.
Every string that reaches a user must pass through this package.
"""

from examina.language.guard import FORBIDDEN_WORDS, LanguageViolationError, check_language

__all__ = ["FORBIDDEN_WORDS", "LanguageViolationError", "check_language"]
