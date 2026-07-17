"""
Upload pipeline exceptions.

See specs/FAILURE_SPEC_v1.0.md. Every failure mode the upload pipeline
can raise maps onto one of these types. UploadSecurityError itself is
never raised directly — only its subclasses.
"""

from __future__ import annotations

from typing import Literal


class UploadSecurityError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FileTooLargeError(UploadSecurityError):
    def __init__(self, message: str, size_bytes: int, limit_bytes: int) -> None:
        super().__init__(message)
        self.size_bytes = size_bytes
        self.limit_bytes = limit_bytes


class InvalidMimeTypeError(UploadSecurityError):
    def __init__(self, message: str, detected_type: str, allowed_types: frozenset[str]) -> None:
        super().__init__(message)
        self.detected_type = detected_type
        self.allowed_types = allowed_types


class MalwareDetectedError(UploadSecurityError):
    """
    detection_name is for internal logging only (Constitution Principle
    7) — it must never be included in any user-facing message or output.
    """

    def __init__(self, message: str, detection_name: str) -> None:
        super().__init__(message)
        self.detection_name = detection_name


class DecompressionBombError(UploadSecurityError):
    def __init__(self, message: str, detected_ratio: float | None = None) -> None:
        super().__init__(message)
        self.detected_ratio = detected_ratio


class ScanFailureError(UploadSecurityError):
    def __init__(self, message: str, scan_type: Literal["clamav", "mime", "archive"]) -> None:
        super().__init__(message)
        self.scan_type = scan_type


class UnsupportedFileTypeError(UploadSecurityError):
    def __init__(self, message: str, detected_type: str) -> None:
        super().__init__(message)
        self.detected_type = detected_type
