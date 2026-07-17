"""Upload pipeline step 4 — SHA-256 hashing, the file's canonical identity."""

from __future__ import annotations

import hashlib


def compute_file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
