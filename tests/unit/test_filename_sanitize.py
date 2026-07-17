"""Tests for src/examina/pipeline/steps/filename_sanitize.py."""

from __future__ import annotations

from uuid import UUID

from examina.pipeline.steps.filename_sanitize import sanitize_filename


class TestSanitizeFilename:
    def test_returns_valid_uuid4_string(self) -> None:
        result = sanitize_filename("photo.jpg")
        parsed = UUID(result)
        assert parsed.version == 4

    def test_two_calls_return_different_values(self) -> None:
        assert sanitize_filename("a.jpg") != sanitize_filename("a.jpg")

    def test_none_input_returns_valid_uuid(self) -> None:
        UUID(sanitize_filename(None))

    def test_path_traversal_input_returns_uuid_without_passwd(self) -> None:
        result = sanitize_filename("../../../etc/passwd")
        assert "passwd" not in result
        UUID(result)

    def test_null_byte_input_returns_valid_uuid(self) -> None:
        result = sanitize_filename("evil\x00.jpg")
        UUID(result)

    def test_windows_path_separator_input_returns_valid_uuid(self) -> None:
        result = sanitize_filename("C:\\Windows\\System32\\evil.exe")
        UUID(result)

    def test_return_value_is_36_characters(self) -> None:
        assert len(sanitize_filename("anything.png")) == 36
