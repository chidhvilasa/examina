"""
Tests for src/examina/pipeline/orchestrator.py branches not already
exercised by tests/integration/test_analysis_pipeline.py: the
mime_type_to_file_type failure branch and BridgeError propagation.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from examina.bridge.types import BridgeError, BridgeRequest, BridgeResult
from examina.pipeline import orchestrator
from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import UnsupportedFileTypeError
from examina.pipeline.orchestrator import mime_type_to_file_type, run_analysis

JPEG_BYTES = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 20


class TestMimeTypeToFileType:
    def test_maps_known_types(self) -> None:
        assert mime_type_to_file_type("image/jpeg") == "JPEG"
        assert mime_type_to_file_type("image/png") == "PNG"
        assert mime_type_to_file_type("image/webp") == "WEBP"
        assert mime_type_to_file_type("application/pdf") == "PDF"

    def test_unknown_type_raises_unsupported_file_type(self) -> None:
        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            mime_type_to_file_type("video/mp4")
        assert exc_info.value.detected_type == "video/mp4"


class _FailingBridgeClient:
    def get_bridge_version(self) -> str:
        return "bridge:1.0"

    async def health_check(self) -> bool:
        return True

    async def analyze(self, request: BridgeRequest) -> BridgeResult:
        del request
        raise BridgeError(code="BRIDGE_UNAVAILABLE", message="PRISM is unreachable")


class TestBridgeErrorPropagation:
    def test_bridge_error_is_logged_and_reraised(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr(orchestrator, "get_bridge_client", lambda: _FailingBridgeClient())
        logger = logging.getLogger("orchestrator-bridge-error-test")

        with caplog.at_level(logging.ERROR, logger="orchestrator-bridge-error-test"):
            with pytest.raises(BridgeError) as exc_info:
                asyncio.run(
                    run_analysis(
                        data=JPEG_BYTES,
                        original_filename="photo.jpg",
                        examina_version="0.3.0",
                        upload_config=UploadConfig(),
                        logger=logger,
                    )
                )

        assert exc_info.value.code == "BRIDGE_UNAVAILABLE"
        assert any(record.levelno == logging.ERROR for record in caplog.records)
