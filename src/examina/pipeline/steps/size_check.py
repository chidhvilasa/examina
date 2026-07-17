"""Upload pipeline step 1 — file size check."""

from __future__ import annotations

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import FileTooLargeError


def check_file_size(data: bytes, config: UploadConfig) -> None:
    if len(data) > config.max_file_size_bytes:
        raise FileTooLargeError(
            message="File exceeds maximum allowed size",
            size_bytes=len(data),
            limit_bytes=config.max_file_size_bytes,
        )
