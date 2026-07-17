"""
Full analysis orchestrator — connects the upload pipeline to the PRISM
bridge and the report engine.

`run_analysis` is async because `BridgeClient.analyze` is async
(specs/BRIDGE_SPEC_v1.1.md). The API layer (Phase 4) calls this via
`asyncio` from its request handlers; no synchronous wrapper is provided
here.
"""

from __future__ import annotations

import logging
from typing import Literal

from examina.bridge.factory import get_bridge_client
from examina.bridge.types import BridgeError, BridgeRequest
from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import UnsupportedFileTypeError
from examina.pipeline.pipeline import process_upload
from examina.report.assembler import assemble_report
from examina.report.schema import ExaminaReport

_MIME_TO_FILE_TYPE: dict[str, Literal["JPEG", "PNG", "WEBP", "PDF"]] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
    "application/pdf": "PDF",
}


def mime_type_to_file_type(mime_type: str) -> Literal["JPEG", "PNG", "WEBP", "PDF"]:
    file_type = _MIME_TO_FILE_TYPE.get(mime_type)
    if file_type is None:
        raise UnsupportedFileTypeError(
            message="File type is not supported for analysis",
            detected_type=mime_type,
        )
    return file_type


async def run_analysis(
    data: bytes,
    original_filename: str | None,
    examina_version: str,
    upload_config: UploadConfig,
    logger: logging.Logger,
) -> ExaminaReport:
    upload_result = process_upload(data, original_filename, upload_config, logger)

    file_type = mime_type_to_file_type(upload_result.mime_type)

    bridge_client = get_bridge_client()
    bridge_request = BridgeRequest(
        file_bytes=data,
        file_hash=upload_result.file_hash,
        file_type=file_type,
        clamav_mode=upload_config.clamav_mode,
        examina_version=examina_version,
    )

    try:
        bridge_result = await bridge_client.analyze(bridge_request)
    except BridgeError as exc:
        logger.error("PRISM bridge call failed: %s: %s", exc.code, exc.message)
        raise

    report = assemble_report(
        bridge_result=bridge_result,
        file_hash=upload_result.file_hash,
        file_type=file_type,
        file_size_bytes=upload_result.file_size_bytes,
        examina_version=examina_version,
    )

    logger.info("Analysis complete: report %s", report.report_id)

    return report
