"""Integration tests against a real, locally-checked-out PRISM (Phase 7 —
bridge integration).

These tests require PRISM to be present and functional at PRISM_PATH (or
the default ../PRISM) — they exercise a real subprocess call into
PRISM's `prism.bridge.cli`, not a stub. Skipped entirely when PRISM is
not available, so this file never breaks CI or a checkout without a
sibling PRISM repository.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import os
from pathlib import Path

import fitz
import pytest
from PIL import Image

import examina
from examina.bridge.local_client import LocalBridgeClient
from examina.bridge.types import BridgeError, BridgeRequest, BridgeResult
from examina.pipeline.config import UploadConfig
from examina.pipeline.orchestrator import run_analysis
from examina.report.schema import ExaminaReport

PRISM_PATH = os.environ.get("PRISM_PATH", "../PRISM")
PRISM_AVAILABLE = os.path.exists(PRISM_PATH)

pytestmark = pytest.mark.skipif(
    not PRISM_AVAILABLE, reason="PRISM not available at PRISM_PATH"
)


def _jpeg_bytes() -> bytes:
    image = Image.new("RGB", (200, 200), color=(120, 140, 200))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    doc = fitz.open()
    try:
        doc.set_metadata({"title": "Real bridge test document", "author": "EXAMINA tests"})
        doc.new_page()
        return doc.tobytes()
    finally:
        doc.close()


def _client() -> LocalBridgeClient:
    return LocalBridgeClient(prism_path=Path(PRISM_PATH))


def _logger() -> logging.Logger:
    return logging.getLogger("test-real-bridge")


class TestRealBridgeAnalyzesJpeg:
    def test_real_bridge_analyzes_jpeg(self) -> None:
        data = _jpeg_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        request = BridgeRequest(
            file_bytes=data, file_hash=file_hash, file_type="JPEG", examina_version="0.7.0"
        )

        result = asyncio.run(_client().analyze(request))

        assert isinstance(result, BridgeResult)
        assert result.bridge_version == "bridge:1.0"
        assert len(result.facts) > 0
        assert len(result.hypotheses) == 4
        assert 0.0 <= result.reconstruction_confidence.overall <= 1.0
        ranks = [h.rank for h in result.hypotheses]
        assert ranks == sorted(ranks)


class TestRealBridgeAnalyzesPdf:
    def test_real_bridge_analyzes_pdf(self) -> None:
        data = _pdf_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        request = BridgeRequest(
            file_bytes=data, file_hash=file_hash, file_type="PDF", examina_version="0.7.0"
        )

        result = asyncio.run(_client().analyze(request))

        assert isinstance(result, BridgeResult)
        assert result.bridge_version == "bridge:1.0"
        assert len(result.facts) > 0
        assert 0.0 <= result.reconstruction_confidence.overall <= 1.0


class TestRealBridgeIsDeterministic:
    def test_real_bridge_is_deterministic(self) -> None:
        data = _jpeg_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        request = BridgeRequest(
            file_bytes=data, file_hash=file_hash, file_type="JPEG", examina_version="0.7.0"
        )

        client = _client()
        first = asyncio.run(client.analyze(request))
        second = asyncio.run(client.analyze(request))

        assert len(first.facts) == len(second.facts)
        assert [f.statement for f in first.facts] == [f.statement for f in second.facts]

        assert len(first.hypotheses) == len(second.hypotheses)
        for h1, h2 in zip(first.hypotheses, second.hypotheses, strict=True):
            assert abs(h1.confidence - h2.confidence) < 0.001

        assert (
            abs(
                first.reconstruction_confidence.overall
                - second.reconstruction_confidence.overall
            )
            < 0.001
        )


class TestFullPipelineRealPrism:
    def test_full_pipeline_real_prism_jpeg(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EXAMINA_INVITE_CODE", "test-real-bridge")
        monkeypatch.setenv("PRISM_PATH", PRISM_PATH)
        monkeypatch.delenv("EXAMINA_ENV", raising=False)

        report = asyncio.run(
            run_analysis(
                data=_jpeg_bytes(),
                original_filename="real.jpg",
                examina_version=examina.__version__,
                upload_config=UploadConfig(clamav_mode="skip"),
                logger=_logger(),
            )
        )

        assert isinstance(report, ExaminaReport)
        assert report.assessment is not None
        assert len(report.evidence.families) > 0
        assert 0.0 <= report.confidence.overall <= 1.0
        assert report.history is not None
        assert report.confidence.disclaimer != ""

    def test_full_pipeline_real_prism_pdf(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EXAMINA_INVITE_CODE", "test-real-bridge")
        monkeypatch.setenv("PRISM_PATH", PRISM_PATH)
        monkeypatch.delenv("EXAMINA_ENV", raising=False)

        report = asyncio.run(
            run_analysis(
                data=_pdf_bytes(),
                original_filename="real.pdf",
                examina_version=examina.__version__,
                upload_config=UploadConfig(clamav_mode="skip"),
                logger=_logger(),
            )
        )

        assert isinstance(report, ExaminaReport)
        assert report.assessment is not None
        assert len(report.evidence.families) > 0
        assert 0.0 <= report.confidence.overall <= 1.0
        assert report.history is not None
        assert report.confidence.disclaimer != ""


class TestPrismOfflineReturnsBridgeError:
    def test_prism_offline_returns_bridge_error(self) -> None:
        client = LocalBridgeClient(prism_path=Path("C:/definitely-not-a-real-prism-path"))
        request = BridgeRequest(
            file_bytes=_jpeg_bytes(),
            file_hash="a" * 64,
            file_type="JPEG",
            examina_version="0.7.0",
        )

        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(client.analyze(request))

        assert exc_info.value.code == "BRIDGE_UNAVAILABLE"
