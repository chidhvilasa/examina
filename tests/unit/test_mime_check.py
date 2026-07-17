"""Tests for src/examina/pipeline/steps/mime_check.py."""

from __future__ import annotations

import pytest

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import InvalidMimeTypeError
from examina.pipeline.steps.mime_check import check_mime_type

JPEG_BYTES = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 20
PNG_BYTES = bytes.fromhex("89504e470d0a1a0a") + b"\x00" * 20
WEBP_BYTES = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 20
PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< >>\nendobj\n"


class TestValidSignatures:
    def test_jpeg_bytes_return_image_jpeg(self) -> None:
        assert check_mime_type(JPEG_BYTES, UploadConfig()) == "image/jpeg"

    def test_png_bytes_return_image_png(self) -> None:
        assert check_mime_type(PNG_BYTES, UploadConfig()) == "image/png"

    def test_webp_bytes_return_image_webp(self) -> None:
        assert check_mime_type(WEBP_BYTES, UploadConfig()) == "image/webp"

    def test_pdf_bytes_return_application_pdf(self) -> None:
        assert check_mime_type(PDF_BYTES, UploadConfig()) == "application/pdf"


class TestInvalidSignatures:
    def test_text_bytes_raise(self) -> None:
        with pytest.raises(InvalidMimeTypeError):
            check_mime_type(b"This is just plain text content.", UploadConfig())

    def test_python_source_bytes_raise(self) -> None:
        with pytest.raises(InvalidMimeTypeError):
            check_mime_type(b"import os\nprint('hello world')\n", UploadConfig())

    def test_error_contains_detected_type(self) -> None:
        with pytest.raises(InvalidMimeTypeError) as exc_info:
            check_mime_type(b"plain text", UploadConfig())
        assert exc_info.value.detected_type == "unknown"

    def test_filename_is_ignored_text_disguised_as_jpeg(self) -> None:
        # mime_check has no filename parameter at all — this test simply
        # confirms detection is bytes-only regardless of what a caller
        # might have named the file.
        fake_jpeg_content = b"just some text pretending to be a .jpg file"
        with pytest.raises(InvalidMimeTypeError):
            check_mime_type(fake_jpeg_content, UploadConfig())
