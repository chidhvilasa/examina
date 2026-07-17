"""
Real-file pipeline stress tests — Phase 6 hardening.

Verifies byte-budget and limit enforcement on realistically-sized
synthetic files. Every file used here is constructed programmatically in
memory; none are read from disk (Constitution Principle 7 — no real or
disk-resident material is needed to exercise these limits).
"""

from __future__ import annotations

import logging
import os
import struct
import zlib
from io import BytesIO

import fitz
import pytest
from PIL import Image

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import FileTooLargeError, InvalidMimeTypeError
from examina.pipeline.pipeline import UploadResult, process_upload
from examina.pipeline.steps.size_check import check_file_size

_TWENTY_MB = 20_971_520


def _logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _random_jpeg_bytes(width: int, height: int, quality: int = 95) -> bytes:
    """High-entropy pixel data compresses poorly, producing a large JPEG
    for a given resolution — unlike a solid-color image, which JPEG
    compresses to near-nothing regardless of quality setting."""
    raw = os.urandom(width * height * 3)
    image = Image.frombytes("RGB", (width, height), raw)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def _lying_zip_bytes(claimed_uncompressed: int, real_data: bytes) -> bytes:
    """Builds a ZIP file by hand whose local header and central directory
    both claim `claimed_uncompressed` bytes of uncompressed content, while
    the actual stored payload is `real_data` — a central-directory-lie
    zip bomb. Uses ZIP_STORED (no compression) so `real_data`'s on-disk
    size is exact and independently controllable from the claimed size.
    """
    filename = b"bomb.txt"
    crc = zlib.crc32(real_data) & 0xFFFFFFFF
    compressed_size = len(real_data)

    local_header = struct.pack(
        "<4sHHHHHIIIHH",
        b"PK\x03\x04",
        20,  # version needed to extract
        0,  # general purpose bit flag
        0,  # compression method: stored
        0,  # last mod file time
        0,  # last mod file date
        crc,
        compressed_size,
        claimed_uncompressed,  # LIE: inflated uncompressed size
        len(filename),
        0,  # extra field length
    )
    local_entry = local_header + filename + real_data

    central_header = struct.pack(
        "<4sHHHHHHIIIHHHHHII",
        b"PK\x01\x02",
        20,  # version made by
        20,  # version needed to extract
        0,  # general purpose bit flag
        0,  # compression method: stored
        0,  # last mod file time
        0,  # last mod file date
        crc,
        compressed_size,
        claimed_uncompressed,  # LIE: inflated uncompressed size
        len(filename),
        0,  # extra field length
        0,  # file comment length
        0,  # disk number start
        0,  # internal file attributes
        0,  # external file attributes
        0,  # relative offset of local header
    )
    central_entry = central_header + filename

    end_of_central_dir = struct.pack(
        "<4sHHHHIIH",
        b"PK\x05\x06",
        0,  # number of this disk
        0,  # disk where central directory starts
        1,  # central directory records on this disk
        1,  # total central directory records
        len(central_entry),
        len(local_entry),
        0,  # comment length
    )

    return local_entry + central_entry + end_of_central_dir


class TestLargeJpegPipeline:
    def test_large_jpeg_pipeline_completes(self) -> None:
        jpeg_bytes = _random_jpeg_bytes(1400, 1400, quality=95)
        assert len(jpeg_bytes) > 1_000_000  # confirms this is a genuinely large file

        config = UploadConfig(clamav_mode="skip")
        result = process_upload(jpeg_bytes, "stress.jpg", config, _logger("stress-jpeg"))

        assert isinstance(result, UploadResult)
        assert result.file_size_bytes == len(jpeg_bytes)


class TestSizeCheckBoundary:
    def test_jpeg_at_exactly_20mb_passes(self) -> None:
        data = b"\xff\xd8\xff\xe0" + (b"\x00" * (_TWENTY_MB - 4))
        assert len(data) == _TWENTY_MB

        check_file_size(data, UploadConfig())  # must not raise

    def test_jpeg_one_byte_over_limit_raises(self) -> None:
        data = b"\xff\xd8\xff\xe0" + (b"\x00" * (_TWENTY_MB - 3))
        assert len(data) == _TWENTY_MB + 1

        with pytest.raises(FileTooLargeError):
            check_file_size(data, UploadConfig())


class TestPdfWithLargeEmbeddedContent:
    def test_pdf_with_large_embedded_content(self) -> None:
        doc = fitz.open()
        try:
            for _ in range(3):
                image_bytes = _random_jpeg_bytes(600, 600, quality=90)
                assert len(image_bytes) > 300_000  # approximately 500KB-scale content
                page = doc.new_page()
                page.insert_image(page.rect, stream=image_bytes)
            pdf_bytes = doc.tobytes()
        finally:
            doc.close()

        config = UploadConfig(clamav_mode="skip")
        result = process_upload(pdf_bytes, "stress.pdf", config, _logger("stress-pdf"))

        assert isinstance(result, UploadResult)
        assert result.mime_type == "application/pdf"


class TestZipBombRejectedByMimeAllowlist:
    def test_zip_bomb_rejected_before_pipeline_completes(self) -> None:
        real_data = b"A" * 1024  # 1KB actual payload
        claimed_uncompressed = 200 * 1024 * 1024  # 200MB claimed
        zip_bytes = _lying_zip_bytes(claimed_uncompressed, real_data)
        assert zip_bytes[:4] == b"PK\x03\x04"  # a genuine ZIP local file header

        config = UploadConfig(clamav_mode="skip")
        with pytest.raises(InvalidMimeTypeError):
            process_upload(zip_bytes, "bomb.zip", config, _logger("stress-zip"))
