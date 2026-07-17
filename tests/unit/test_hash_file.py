"""Tests for src/examina/pipeline/steps/hash_file.py."""

from __future__ import annotations

import re

from examina.pipeline.steps.hash_file import compute_file_hash

EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestComputeFileHash:
    def test_empty_bytes_produce_known_hash(self) -> None:
        assert compute_file_hash(b"") == EMPTY_HASH

    def test_same_bytes_always_produce_same_hash(self) -> None:
        assert compute_file_hash(b"identical content") == compute_file_hash(b"identical content")

    def test_different_bytes_produce_different_hash(self) -> None:
        assert compute_file_hash(b"content a") != compute_file_hash(b"content b")

    def test_return_value_is_64_char_lowercase_hex(self) -> None:
        result = compute_file_hash(b"some file bytes")
        assert len(result) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result)
