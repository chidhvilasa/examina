"""
Upload pipeline step 6 — archive/decompression-bomb detection.

None of EXAMINA's 4 allowed file types (JPEG/PNG/WebP/PDF) are archives.
This step exists purely as defense-in-depth: if `check_mime_type()`
worked correctly, `check_archive_bomb()` always receives a non-archive
`detected_mime_type` and returns None immediately. It only does real
work if a future signature-table change, or an adjacent code path, ever
passes archive bytes through to this step.
"""

from __future__ import annotations

import zipfile
from io import BytesIO

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import DecompressionBombError, ScanFailureError

_ARCHIVE_MIME_TYPES = frozenset(
    {
        "application/zip",
        "application/gzip",
        "application/x-tar",
        "application/x-bzip2",
        "application/x-7z-compressed",
    }
)

_UNSUPPORTED_ARCHIVE_MESSAGE = (
    "Archive format requires a vetted extraction library not yet approved "
    "for EXAMINA; it is rejected rather than partially inspected"
)


def _check_zip_bomb(data: bytes, config: UploadConfig) -> None:
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            total_uncompressed = sum(info.file_size for info in archive.infolist())
    except (zipfile.BadZipFile, OSError) as exc:
        raise ScanFailureError(
            message="Security scan failed unexpectedly", scan_type="archive"
        ) from exc

    if total_uncompressed > config.max_uncompressed_bytes:
        raise DecompressionBombError(
            message="Archive exceeds the maximum allowed uncompressed size"
        )

    if len(data) > 0:
        ratio = total_uncompressed / len(data)
        if ratio > config.max_compression_ratio:
            raise DecompressionBombError(
                message="Archive compression ratio exceeds the maximum allowed",
                detected_ratio=ratio,
            )


def _check_gzip_bomb(data: bytes, config: UploadConfig) -> None:
    # The gzip trailer's last 4 bytes store the uncompressed size modulo
    # 2**32 (RFC 1952). Reading it avoids ever decompressing untrusted,
    # potentially bomb-sized data just to measure it.
    if len(data) < 4:
        raise ScanFailureError(message="Security scan failed unexpectedly", scan_type="archive")

    total_uncompressed = int.from_bytes(data[-4:], byteorder="little")

    if total_uncompressed > config.max_uncompressed_bytes:
        raise DecompressionBombError(
            message="Archive exceeds the maximum allowed uncompressed size"
        )

    if len(data) > 0:
        ratio = total_uncompressed / len(data)
        if ratio > config.max_compression_ratio:
            raise DecompressionBombError(
                message="Archive compression ratio exceeds the maximum allowed",
                detected_ratio=ratio,
            )


def check_archive_bomb(data: bytes, detected_mime_type: str, config: UploadConfig) -> None:
    if detected_mime_type not in _ARCHIVE_MIME_TYPES:
        return

    if detected_mime_type == "application/zip":
        _check_zip_bomb(data, config)
        return

    if detected_mime_type == "application/gzip":
        _check_gzip_bomb(data, config)
        return

    # tar, bzip2, 7z: rejected immediately — see specs/TECH_DEBT.md.
    raise DecompressionBombError(message=_UNSUPPORTED_ARCHIVE_MESSAGE)
