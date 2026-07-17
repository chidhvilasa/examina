"""
Security-focused tests for the upload pipeline (Constitution Principle
11's threat model: the malicious uploader).
"""

from __future__ import annotations

import io
import logging
import shutil
import struct
import zipfile
from uuid import UUID

import pytest

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import (
    DecompressionBombError,
    FileTooLargeError,
    InvalidMimeTypeError,
    MalwareDetectedError,
)
from examina.pipeline.steps.archive_check import check_archive_bomb
from examina.pipeline.steps.clamav_scan import scan_for_malware
from examina.pipeline.steps.filename_sanitize import sanitize_filename
from examina.pipeline.steps.mime_check import check_mime_type
from examina.pipeline.steps.size_check import check_file_size

# EICAR standard antivirus test string — not malware, a recognized industry
# test signature every AV engine (including ClamAV) is expected to flag.
EICAR_STRING = (br"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*")

CLAMAV_NOT_AVAILABLE = shutil.which("clamdscan") is None


def _forged_zip_bomb(declared_uncompressed_size: int) -> bytes:
    """
    Build a syntactically valid ZIP whose central directory declares an
    uncompressed size far larger than its real (tiny) compressed
    payload — the same declared-size-forging technique a real zip bomb
    uses. `check_archive_bomb` never extracts archive content (per
    specs/DEPLOYMENT_SPEC_v1.0.md's "do not extract to disk" rule), so
    this is precisely the attack it must catch from metadata alone.
    """
    content = b"x" * 777  # length chosen for a distinctive 4-byte LE encoding
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("payload.bin", content)

    real_size_bytes = struct.pack("<I", len(content))
    forged_size_bytes = struct.pack("<I", declared_uncompressed_size)
    return buffer.getvalue().replace(real_size_bytes, forged_size_bytes)


class TestSizeLimitBoundary:
    def test_exactly_20mb_passes(self) -> None:
        config = UploadConfig()
        data = b"x" * config.max_file_size_bytes
        assert check_file_size(data, config) is None

    def test_20mb_plus_one_byte_raises(self) -> None:
        config = UploadConfig()
        data = b"x" * (config.max_file_size_bytes + 1)
        with pytest.raises(FileTooLargeError):
            check_file_size(data, config)


class TestPathTraversalFilename:
    def test_path_traversal_produces_no_path_separators(self) -> None:
        result = sanitize_filename("../../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result
        UUID(result)

    def test_null_byte_filename_produces_safe_uuid(self) -> None:
        result = sanitize_filename("evil\x00.jpg")
        assert "\x00" not in result
        UUID(result)


class TestFakeJpeg:
    def test_text_content_with_jpg_name_raises(self) -> None:
        # sanitize_filename/mime_check never receive a filename to be
        # fooled by in this call — mime_check takes bytes only.
        with pytest.raises(InvalidMimeTypeError):
            check_mime_type(b"just plain text, not a real jpeg", UploadConfig())


class TestZipBomb:
    def test_ratio_bomb_raises(self) -> None:
        data = _forged_zip_bomb(declared_uncompressed_size=10_000_000)
        config = UploadConfig()  # default ratio limit: 100
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(data, "application/zip", config)

    def test_500mb_uncompressed_bomb_raises(self) -> None:
        data = _forged_zip_bomb(declared_uncompressed_size=600_000_000)
        config = UploadConfig()  # default max_uncompressed_bytes: 500MB
        with pytest.raises(DecompressionBombError):
            check_archive_bomb(data, "application/zip", config)


@pytest.mark.skipif(CLAMAV_NOT_AVAILABLE, reason="clamdscan not installed — see specs/TECH_DEBT.md")
class TestEicarClamAv:
    def test_eicar_string_raises_malware_detected(self) -> None:
        config = UploadConfig(clamav_mode="enforce")
        with pytest.raises(MalwareDetectedError):
            scan_for_malware(EICAR_STRING, config, logging.getLogger("eicar-test"))
