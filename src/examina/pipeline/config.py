"""
Upload pipeline configuration.

See specs/DEPLOYMENT_SPEC_v1.0.md's environment variables table
(CLAMAV_MODE, CLAMAV_SOCKET) and Constitution Principle 8 (security
before features) — every limit here is enforced before any file reaches
analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class UploadConfig(BaseModel):
    max_file_size_bytes: int = Field(default=20_971_520, gt=0)
    max_compression_ratio: int = Field(default=100, gt=1)
    max_uncompressed_bytes: int = Field(default=524_288_000, gt=0)
    allowed_mime_types: frozenset[str] = frozenset(
        {
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf",
        }
    )
    clamav_mode: Literal["enforce", "skip"] = "skip"
    clamav_socket: str = "/var/run/clamav/clamd.ctl"
    temp_dir: Path = Path("/tmp/examina-upload")
