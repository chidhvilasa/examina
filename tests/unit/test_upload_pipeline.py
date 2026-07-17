"""Tests for src/examina/pipeline/pipeline.py — clamav_mode='skip' throughout."""

from __future__ import annotations

import logging
import re
from uuid import UUID

import pytest

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import FileTooLargeError, InvalidMimeTypeError
from examina.pipeline.pipeline import UploadResult, process_upload

JPEG_BYTES = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 20
SECRET_FILENAME = "super-secret-source-name.jpg"
SECRET_CONTENT_MARKER = b"UNIQUE_FILE_CONTENT_MARKER_98765"


def _logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class TestProcessUpload:
    def test_succeeds_for_valid_jpeg(self) -> None:
        result = process_upload(JPEG_BYTES, "photo.jpg", UploadConfig(), _logger("t1"))
        assert isinstance(result, UploadResult)

    def test_returns_analysis_ready_true(self) -> None:
        result = process_upload(JPEG_BYTES, "photo.jpg", UploadConfig(), _logger("t2"))
        assert result.analysis_ready is True

    def test_oversized_input_raises_file_too_large(self) -> None:
        config = UploadConfig(max_file_size_bytes=10)
        with pytest.raises(FileTooLargeError):
            process_upload(JPEG_BYTES, "photo.jpg", config, _logger("t3"))

    def test_non_image_bytes_raise_invalid_mime_type(self) -> None:
        with pytest.raises(InvalidMimeTypeError):
            process_upload(b"plain text content", "notes.txt", UploadConfig(), _logger("t4"))

    def test_file_id_is_valid_uuid(self) -> None:
        result = process_upload(JPEG_BYTES, "photo.jpg", UploadConfig(), _logger("t5"))
        UUID(result.file_id)

    def test_file_hash_is_64_char_lowercase_hex(self) -> None:
        result = process_upload(JPEG_BYTES, "photo.jpg", UploadConfig(), _logger("t6"))
        assert re.fullmatch(r"[0-9a-f]{64}", result.file_hash)

    def test_mime_type_matches_detected_type(self) -> None:
        result = process_upload(JPEG_BYTES, "photo.jpg", UploadConfig(), _logger("t7"))
        assert result.mime_type == "image/jpeg"


class TestPrivacyLogging:
    def test_never_logs_original_filename(self, caplog: pytest.LogCaptureFixture) -> None:
        logger = _logger("t8-filename")
        with caplog.at_level(logging.DEBUG, logger="t8-filename"):
            process_upload(JPEG_BYTES, SECRET_FILENAME, UploadConfig(), logger)
        for record in caplog.records:
            assert SECRET_FILENAME not in record.getMessage()

    def test_never_logs_original_filename_on_failure(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = _logger("t8b-filename-fail")
        config = UploadConfig(max_file_size_bytes=5)
        with caplog.at_level(logging.DEBUG, logger="t8b-filename-fail"):
            with pytest.raises(FileTooLargeError):
                process_upload(JPEG_BYTES, SECRET_FILENAME, config, logger)
        for record in caplog.records:
            assert SECRET_FILENAME not in record.getMessage()

    def test_never_logs_file_content(self, caplog: pytest.LogCaptureFixture) -> None:
        logger = _logger("t9-content")
        data = JPEG_BYTES + SECRET_CONTENT_MARKER
        with caplog.at_level(logging.DEBUG, logger="t9-content"):
            process_upload(data, "photo.jpg", UploadConfig(), logger)
        for record in caplog.records:
            assert SECRET_CONTENT_MARKER.decode() not in record.getMessage()
