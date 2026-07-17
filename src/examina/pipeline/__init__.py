"""
Pipeline package — secure upload processing.
See specs/FAILURE_SPEC_v1.0.md for all failure modes.
Every file is treated as potentially malicious before analysis.
"""

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import (
    DecompressionBombError,
    FileTooLargeError,
    InvalidMimeTypeError,
    MalwareDetectedError,
    ScanFailureError,
    UnsupportedFileTypeError,
    UploadSecurityError,
)
from examina.pipeline.orchestrator import run_analysis
from examina.pipeline.pipeline import UploadResult, process_upload

__all__ = [
    "DecompressionBombError",
    "FileTooLargeError",
    "InvalidMimeTypeError",
    "MalwareDetectedError",
    "ScanFailureError",
    "UnsupportedFileTypeError",
    "UploadConfig",
    "UploadResult",
    "UploadSecurityError",
    "process_upload",
    "run_analysis",
]
