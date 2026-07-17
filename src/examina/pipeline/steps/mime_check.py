"""
Upload pipeline step 2 — MIME type verification from raw bytes.

Detection reads only the file's own byte signature — never a
client-supplied Content-Type header, never a filename or extension
(Constitution Principle 11: attackers control both). See
docs/adr/ADR-0002-mime-detection-signature-table.md for why this is a
dependency-free signature table rather than python-magic/libmagic.
"""

from __future__ import annotations

from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import InvalidMimeTypeError

# (mime_type, [(offset, signature_bytes), ...]) — a type matches when
# every (offset, signature_bytes) pair in its list matches `data`.
_SIGNATURES: list[tuple[str, list[tuple[int, bytes]]]] = [
    ("image/jpeg", [(0, b"\xff\xd8\xff")]),
    ("image/png", [(0, b"\x89PNG\r\n\x1a\n")]),
    ("image/webp", [(0, b"RIFF"), (8, b"WEBP")]),
    ("application/pdf", [(0, b"%PDF-")]),
]


def _detect_type(data: bytes) -> str | None:
    for mime_type, signatures in _SIGNATURES:
        if all(data[offset : offset + len(sig)] == sig for offset, sig in signatures):
            return mime_type
    return None


def check_mime_type(data: bytes, config: UploadConfig) -> str:
    detected = _detect_type(data)

    if detected is None or detected not in config.allowed_mime_types:
        raise InvalidMimeTypeError(
            message="File type is not supported",
            detected_type=detected or "unknown",
            allowed_types=config.allowed_mime_types,
        )

    return detected
