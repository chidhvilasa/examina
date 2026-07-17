"""Tests for src/examina/pipeline/exceptions.py."""

from __future__ import annotations

from examina.pipeline.exceptions import (
    DecompressionBombError,
    FileTooLargeError,
    InvalidMimeTypeError,
    MalwareDetectedError,
    ScanFailureError,
    UnsupportedFileTypeError,
    UploadSecurityError,
)


class TestExceptionHierarchy:
    def test_upload_security_error_is_exception_subclass(self) -> None:
        assert issubclass(UploadSecurityError, Exception)

    def test_upload_security_error_instantiates_with_message(self) -> None:
        err = UploadSecurityError("something went wrong")
        assert err.message == "something went wrong"

    def test_file_too_large_error_is_subclass(self) -> None:
        assert issubclass(FileTooLargeError, UploadSecurityError)

    def test_invalid_mime_type_error_is_subclass(self) -> None:
        assert issubclass(InvalidMimeTypeError, UploadSecurityError)

    def test_malware_detected_error_is_subclass(self) -> None:
        assert issubclass(MalwareDetectedError, UploadSecurityError)

    def test_decompression_bomb_error_is_subclass(self) -> None:
        assert issubclass(DecompressionBombError, UploadSecurityError)

    def test_scan_failure_error_is_subclass(self) -> None:
        assert issubclass(ScanFailureError, UploadSecurityError)

    def test_unsupported_file_type_error_is_subclass(self) -> None:
        assert issubclass(UnsupportedFileTypeError, UploadSecurityError)


class TestExceptionFields:
    def test_file_too_large_error_stores_fields(self) -> None:
        err = FileTooLargeError(message="too big", size_bytes=100, limit_bytes=50)
        assert err.message == "too big"
        assert err.size_bytes == 100
        assert err.limit_bytes == 50

    def test_invalid_mime_type_error_stores_fields(self) -> None:
        err = InvalidMimeTypeError(
            message="bad type",
            detected_type="text/plain",
            allowed_types=frozenset({"image/jpeg"}),
        )
        assert err.detected_type == "text/plain"
        assert err.allowed_types == frozenset({"image/jpeg"})

    def test_malware_detected_error_stores_detection_name(self) -> None:
        err = MalwareDetectedError(message="rejected", detection_name="Eicar-Test-Signature")
        assert err.detection_name == "Eicar-Test-Signature"

    def test_decompression_bomb_error_stores_ratio(self) -> None:
        err = DecompressionBombError(message="bomb", detected_ratio=150.0)
        assert err.detected_ratio == 150.0

    def test_decompression_bomb_error_ratio_defaults_to_none(self) -> None:
        err = DecompressionBombError(message="bomb")
        assert err.detected_ratio is None

    def test_scan_failure_error_stores_scan_type(self) -> None:
        err = ScanFailureError(message="scan failed", scan_type="clamav")
        assert err.scan_type == "clamav"

    def test_unsupported_file_type_error_stores_detected_type(self) -> None:
        err = UnsupportedFileTypeError(message="unsupported", detected_type="video/mp4")
        assert err.detected_type == "video/mp4"
