"""
Upload pipeline step 5 — ClamAV malware scan.

See specs/FAILURE_SPEC_v1.0.md category 4 (malicious upload pattern
detected). `clamav_mode="skip"` is a development-only bypass — it is
always logged loudly so it can never be mistaken for a passed scan.
"""

from __future__ import annotations

import logging
import subprocess
from uuid import uuid4

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import MalwareDetectedError, ScanFailureError


def _parse_detection_name(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.endswith("FOUND"):
            _, _, remainder = line.rpartition(": ")
            name = remainder.removesuffix("FOUND").strip()
            if name:
                return name
    return "unknown"


def scan_for_malware(data: bytes, config: UploadConfig, logger: logging.Logger) -> None:
    if config.clamav_mode == "skip":
        logger.warning("ClamAV scan bypassed — clamav_mode=skip. Not safe for production.")
        return

    config.temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = config.temp_dir / str(uuid4())
    temp_path.write_bytes(data)

    try:
        try:
            result = subprocess.run(
                ["clamdscan", "--no-summary", str(temp_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            logger.error("ClamAV (clamdscan) is not available on this system.")
            raise ScanFailureError(
                message="ClamAV is not available", scan_type="clamav"
            ) from exc

        if result.returncode == 0:
            return

        if result.returncode == 1:
            detection_name = _parse_detection_name(result.stdout)
            logger.warning("ClamAV detected malware in an upload: %s", detection_name)
            raise MalwareDetectedError(
                message="File rejected for security reasons",
                detection_name=detection_name,
            )

        logger.error("ClamAV scan failed with return code %s", result.returncode)
        raise ScanFailureError(message="Security scan failed unexpectedly", scan_type="clamav")
    finally:
        temp_path.unlink(missing_ok=True)
