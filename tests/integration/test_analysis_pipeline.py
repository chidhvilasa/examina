"""
Integration tests for src/examina/pipeline/orchestrator.py — exercises
the full upload -> bridge -> report pipeline against a fake bridge
client (a fixed BridgeResult, injected via monkeypatching
get_bridge_client). Real-PRISM-backed orchestrator tests live in
tests/integration/test_real_bridge.py, gated behind PRISM's
availability; this file stays hermetic so it always runs in CI,
exercising the orchestrator's own logic (upload validation, hashing,
report assembly, failure propagation) independent of PRISM.
clamav_mode='skip' throughout.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

import examina.pipeline.orchestrator as orchestrator_module
from examina.bridge.client import BridgeClient
from examina.bridge.types import (
    BridgeConfidence,
    BridgeFact,
    BridgeHypothesis,
    BridgeRequest,
    BridgeResult,
    BridgeTimelineEvent,
)
from examina.pipeline.config import UploadConfig
from examina.pipeline.exceptions import FileTooLargeError, InvalidMimeTypeError
from examina.pipeline.orchestrator import run_analysis
from examina.pipeline.steps.hash_file import compute_file_hash
from examina.report.schema import EXAMINA_DISCLAIMER, ExaminaReport

JPEG_BYTES = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 20


def _fake_bridge_result(request: BridgeRequest) -> BridgeResult:
    return BridgeResult(
        request_id=request.request_id,
        bridge_version="bridge:1.0",
        prism_version="fake:1.0",
        rule_set_version="fake:1.0",
        extractor_versions={"fake": "1.0"},
        processing_time_ms=0,
        facts=[
            BridgeFact(
                fact_id="fact-1",
                statement="This file declares creation metadata.",
                fact_type="PROVENANCE",
                provenance_source_type="declared",
                extractor="fake-extractor:1.0",
                extraction_confidence=0.9,
                source_reliability=0.8,
                raw_value={},
            )
        ],
        contradictions=[],
        hypotheses=[
            BridgeHypothesis(
                hypothesis_id="hyp-1",
                description="This file is consistent with an unedited original.",
                confidence=0.6,
                rank=1,
            ),
        ],
        timeline=[BridgeTimelineEvent(sequence=1, description="Event.", confidence=0.7)],
        reconstruction_confidence=BridgeConfidence(
            overall=0.72,
            penalty_from_contradictions=0.0,
            unresolved_contradictions=0,
            active_hypotheses=1,
        ),
        errors=[],
        partial_analysis=False,
        partial_reason=None,
    )


class _FakeBridgeClient(BridgeClient):
    async def analyze(self, request: BridgeRequest) -> BridgeResult:
        return _fake_bridge_result(request)

    async def health_check(self) -> bool:
        return True

    def get_bridge_version(self) -> str:
        return "bridge:1.0"


@pytest.fixture(autouse=True)
def _fake_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orchestrator_module, "get_bridge_client", lambda: _FakeBridgeClient())


def _run(data: bytes = JPEG_BYTES, config: UploadConfig | None = None) -> ExaminaReport:
    return asyncio.run(
        run_analysis(
            data=data,
            original_filename="photo.jpg",
            examina_version="0.3.0",
            upload_config=config or UploadConfig(),
            logger=logging.getLogger("integration-test"),
        )
    )


class TestRunAnalysis:
    def test_returns_examina_report(self) -> None:
        assert isinstance(_run(), ExaminaReport)

    def test_file_hash_matches_sha256_of_input(self) -> None:
        report = _run()
        assert report.file_hash == compute_file_hash(JPEG_BYTES)

    def test_file_type_equals_jpeg(self) -> None:
        assert _run().file_type == "JPEG"

    def test_expires_at_is_24_hours_after_created_at(self) -> None:
        report = _run()
        assert (report.expires_at - report.created_at).total_seconds() == 24 * 3600

    def test_assessment_is_not_none(self) -> None:
        assert _run().assessment is not None

    def test_confidence_disclaimer_equals_constant(self) -> None:
        assert _run().confidence.disclaimer == EXAMINA_DISCLAIMER


class TestRunAnalysisFailures:
    def test_oversized_input_raises_file_too_large(self) -> None:
        config = UploadConfig(max_file_size_bytes=10)
        with pytest.raises(FileTooLargeError):
            _run(config=config)

    def test_text_bytes_raise_invalid_mime_type(self) -> None:
        with pytest.raises(InvalidMimeTypeError):
            _run(data=b"plain text content, not an image")


class TestDeterminism:
    def test_same_bytes_produce_matching_hash_verdict_and_confidence(self) -> None:
        first = _run()
        second = _run()
        assert first.report_id != second.report_id
        assert first.file_hash == second.file_hash
        assert first.assessment.verdict == second.assessment.verdict
        assert first.confidence.overall == second.confidence.overall
