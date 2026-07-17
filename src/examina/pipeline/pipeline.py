"""
Upload pipeline orchestrator — runs the 7 security steps in fixed order
before any file reaches analysis (Constitution Principle 8).
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import UploadSecurityError
from examina.pipeline.steps.archive_check import check_archive_bomb
from examina.pipeline.steps.clamav_scan import scan_for_malware
from examina.pipeline.steps.filename_sanitize import sanitize_filename
from examina.pipeline.steps.hash_file import compute_file_hash
from examina.pipeline.steps.mime_check import check_mime_type
from examina.pipeline.steps.size_check import check_file_size


class UploadResult(BaseModel):
    file_id: str
    file_hash: str
    mime_type: str
    file_size_bytes: int
    analysis_ready: bool


def process_upload(
    data: bytes,
    original_filename: str | None,
    config: UploadConfig,
    logger: logging.Logger,
) -> UploadResult:
    try:
        check_file_size(data, config)
        mime_type = check_mime_type(data, config)
        file_id = sanitize_filename(original_filename)
        file_hash = compute_file_hash(data)
        scan_for_malware(data, config, logger)
        check_archive_bomb(data, mime_type, config)
    except UploadSecurityError as exc:
        logger.warning("Upload rejected: %s: %s", type(exc).__name__, exc.message)
        raise

    logger.info("Upload pipeline complete: file_id=%s hash=%s...", file_id, file_hash[:8])

    return UploadResult(
        file_id=file_id,
        file_hash=file_hash,
        mime_type=mime_type,
        file_size_bytes=len(data),
        analysis_ready=True,
    )
