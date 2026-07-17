"""Tests for src/examina/pipeline/steps/archive_check.py — archives built via stdlib only."""

from __future__ import annotations

import gzip
import io
import zipfile

import pytest

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import DecompressionBombError, ScanFailureError
from examina.pipeline.steps.archive_check import check_archive_bomb


def _zip_bytes(content: bytes, compression: int = zipfile.ZIP_STORED) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
        archive.writestr("payload.bin", content)
    return buffer.getvalue()


class TestNonArchiveTypes:
    def test_non_archive_mime_type_returns_none(self) -> None:
        assert check_archive_bomb(b"anything", "image/jpeg", UploadConfig()) is None


class TestZip:
    def test_valid_tiny_zip_below_limits_returns_none(self) -> None:
        data = _zip_bytes(b"hello world")
        assert check_archive_bomb(data, "application/zip", UploadConfig()) is None

    def test_uncompressed_size_exceeding_max_raises(self) -> None:
        data = _zip_bytes(b"x" * 1000)
        config = UploadConfig(max_uncompressed_bytes=100)
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(data, "application/zip", config)

    def test_ratio_exceeding_max_raises(self) -> None:
        data = _zip_bytes(b"A" * 200_000, compression=zipfile.ZIP_DEFLATED)
        config = UploadConfig(max_compression_ratio=10)
        with pytest.raises(DecompressionBombError) as exc_info:
            check_archive_bomb(data, "application/zip", config)
        assert exc_info.value.detected_ratio is not None
        assert exc_info.value.detected_ratio > 10

    def test_malformed_zip_raises_scan_failure(self) -> None:
        with pytest.raises(ScanFailureError) as exc_info:
            check_archive_bomb(b"not a real zip file", "application/zip", UploadConfig())
        assert exc_info.value.scan_type == "archive"


class TestGzip:
    def test_below_limits_returns_none(self) -> None:
        data = gzip.compress(b"Ordinary content that does not compress dramatically well.")
        assert check_archive_bomb(data, "application/gzip", UploadConfig()) is None

    def test_exceeding_size_raises(self) -> None:
        data = gzip.compress(b"x" * 1000)
        config = UploadConfig(max_uncompressed_bytes=100)
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(data, "application/gzip", config)

    def test_exceeding_ratio_raises(self) -> None:
        data = gzip.compress(b"A" * 200_000)
        config = UploadConfig(max_compression_ratio=10)
        with pytest.raises(DecompressionBombError) as exc_info:
            check_archive_bomb(data, "application/gzip", config)
        assert exc_info.value.detected_ratio is not None
        assert exc_info.value.detected_ratio > 10

    def test_too_short_to_contain_footer_raises_scan_failure(self) -> None:
        with pytest.raises(ScanFailureError) as exc_info:
            check_archive_bomb(b"ab", "application/gzip", UploadConfig())
        assert exc_info.value.scan_type == "archive"


class TestUnsupportedArchiveFormats:
    def test_tar_raises_immediately(self) -> None:
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(b"", "application/x-tar", UploadConfig())

    def test_seven_zip_raises_immediately(self) -> None:
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(b"", "application/x-7z-compressed", UploadConfig())

    def test_bzip2_raises_immediately(self) -> None:
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(b"", "application/x-bzip2", UploadConfig())
