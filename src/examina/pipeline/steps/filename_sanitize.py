"""Upload pipeline step 3 — filename sanitization."""

from __future__ import annotations

from uuid import uuid4


def sanitize_filename(original_filename: str | None) -> str:
    """
    Discard the original filename entirely and return a fresh UUID4
    string as the file's internal identity.

    `original_filename` exists only to satisfy the pipeline step
    interface — it is never read, inspected, logged, or used to derive
    the return value in any way (Constitution Principle 7: original
    filenames are never logged or retained).
    """
    del original_filename
    return str(uuid4())
