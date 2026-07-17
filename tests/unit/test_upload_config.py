"""Tests for src/examina/pipeline/config.py."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from examina.pipeline.config import UploadConfig


class TestDefaults:
    def test_instantiates_with_defaults(self) -> None:
        config = UploadConfig()
        assert config.max_file_size_bytes == 20_971_520
        assert config.max_compression_ratio == 100
        assert config.max_uncompressed_bytes == 524_288_000

    def test_default_allowed_mime_types_has_exactly_four(self) -> None:
        config = UploadConfig()
        assert config.allowed_mime_types == frozenset(
            {"image/jpeg", "image/png", "image/webp", "application/pdf"}
        )

    def test_default_clamav_mode_is_skip(self) -> None:
        assert UploadConfig().clamav_mode == "skip"


class TestValidators:
    def test_zero_max_file_size_raises(self) -> None:
        with pytest.raises(ValidationError):
            UploadConfig(max_file_size_bytes=0)

    def test_compression_ratio_of_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            UploadConfig(max_compression_ratio=1)

    def test_zero_max_uncompressed_bytes_raises(self) -> None:
        with pytest.raises(ValidationError):
            UploadConfig(max_uncompressed_bytes=0)
