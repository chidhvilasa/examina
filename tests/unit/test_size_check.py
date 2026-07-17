"""Tests for src/examina/pipeline/steps/size_check.py."""

from __future__ import annotations

import pytest

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import FileTooLargeError
from examina.pipeline.steps.size_check import check_file_size


class TestCheckFileSize:
    def test_file_exactly_at_limit_passes(self) -> None:
        config = UploadConfig(max_file_size_bytes=10)
        assert check_file_size(b"x" * 10, config) is None

    def test_file_one_byte_over_limit_raises(self) -> None:
        config = UploadConfig(max_file_size_bytes=10)
        with pytest.raises(FileTooLargeError):
            check_file_size(b"x" * 11, config)

    def test_error_contains_correct_size_bytes(self) -> None:
        config = UploadConfig(max_file_size_bytes=10)
        with pytest.raises(FileTooLargeError) as exc_info:
            check_file_size(b"x" * 11, config)
        assert exc_info.value.size_bytes == 11

    def test_error_contains_correct_limit_bytes(self) -> None:
        config = UploadConfig(max_file_size_bytes=10)
        with pytest.raises(FileTooLargeError) as exc_info:
            check_file_size(b"x" * 11, config)
        assert exc_info.value.limit_bytes == 10

    def test_empty_bytes_passes(self) -> None:
        config = UploadConfig()
        assert check_file_size(b"", config) is None

    def test_zero_limit_config_not_possible_uses_minimum_valid_limit(self) -> None:
        config = UploadConfig(max_file_size_bytes=1)
        with pytest.raises(FileTooLargeError):
            check_file_size(b"xx", config)
