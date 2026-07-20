"""
Integration tests for the FastAPI application — real pipeline, real
report engine, real (in-memory) database. clamav_mode="skip" via
CLAMAV_MODE (set in tests/conftest.py). The bridge client is a fake
(fixed BridgeResult, see _FakeBridgeClient below) injected via
monkeypatching examina.api.routes.analyze.get_bridge_client — since
Phase 7, LocalBridgeClient makes a real subprocess call into PRISM, and
these API-layer tests must stay hermetic and PRISM-independent (see
tests/integration/test_real_bridge.py for the real-PRISM-backed tests).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import examina.api.routes.analyze as analyze_module
from examina.api.app import create_app
from examina.api.database import get_session
from examina.bridge.client import BridgeClient
from examina.bridge.types import (
    BridgeConfidence,
    BridgeError,
    BridgeFact,
    BridgeHypothesis,
    BridgeRequest,
    BridgeResult,
    BridgeTimelineEvent,
)
from examina.pipeline.exceptions import DecompressionBombError, MalwareDetectedError

JPEG_BYTES = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 20

INVITE_HEADERS = {"Authorization": "Bearer test-invite-code"}
ADMIN_HEADERS = {"Authorization": "Bearer test-admin-token"}


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


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    mp = pytest.MonkeyPatch()
    mp.setattr(analyze_module, "get_bridge_client", lambda: _FakeBridgeClient())
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    mp.undo()


def _upload_jpeg(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/analyze",
        headers=INVITE_HEADERS,
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 200
    result: dict[str, object] = response.json()
    return result


@pytest.fixture(scope="module")
def analyzed(client: TestClient) -> dict[str, object]:
    return _upload_jpeg(client)


class TestStatus:
    def test_returns_200_with_status_ok(self, client: TestClient) -> None:
        response = client.get("/status")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_requires_no_auth_token(self, client: TestClient) -> None:
        response = client.get("/status")
        assert response.status_code == 200


class TestHealth:
    def test_returns_200_or_503(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code in (200, 503)

    def test_response_contains_status_field(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "status" in response.json()

    def test_returns_error_status_and_503_on_database_failure(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import examina.api.routes.health as health_module

        def _broken_get_engine() -> None:
            raise SQLAlchemyError("simulated database outage")

        monkeypatch.setattr(health_module, "get_engine", _broken_get_engine)
        response = client.get("/health")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "error"
        assert body["database_status"] == "error"

    def test_returns_degraded_status_on_low_disk(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import examina.api.routes.health as health_module

        class _FakeDiskUsage:
            free = 100 * 1024**2  # 100MB — well under the 1GB threshold

        monkeypatch.setattr(health_module.shutil, "disk_usage", lambda path: _FakeDiskUsage())
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"


class TestAnalyzeAuth:
    def test_without_invite_code_returns_401(self, client: TestClient) -> None:
        response = client.post("/analyze", files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")})
        assert response.status_code == 401

    def test_with_wrong_invite_code_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/analyze",
            headers={"Authorization": "Bearer wrong-code"},
            files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")},
        )
        assert response.status_code == 401


class TestAnalyzeSuccess:
    def test_returns_200(self, analyzed: dict[str, object]) -> None:
        assert analyzed["status"] == "complete"

    def test_response_contains_report_id(self, analyzed: dict[str, object]) -> None:
        assert isinstance(analyzed["report_id"], str) and analyzed["report_id"]

    def test_response_contains_file_hash(self, analyzed: dict[str, object]) -> None:
        assert isinstance(analyzed["file_hash"], str)
        assert len(analyzed["file_hash"]) == 64

    def test_overall_confidence_in_valid_range(self, analyzed: dict[str, object]) -> None:
        overall_confidence = analyzed["overall_confidence"]
        assert isinstance(overall_confidence, int | float)
        assert 0.0 <= overall_confidence <= 1.0

    def test_natural_language_summary_non_empty(self, analyzed: dict[str, object]) -> None:
        assert isinstance(analyzed["natural_language_summary"], str)
        assert len(analyzed["natural_language_summary"]) > 0

    def test_recommendation_non_empty(self, analyzed: dict[str, object]) -> None:
        assert isinstance(analyzed["recommendation"], str)
        assert len(analyzed["recommendation"]) > 0

    def test_what_would_change_non_empty(self, analyzed: dict[str, object]) -> None:
        assert isinstance(analyzed["what_would_change"], str)
        assert len(analyzed["what_would_change"]) > 0


class TestGetReport:
    def test_returns_200_for_existing_report(
        self, client: TestClient, analyzed: dict[str, object]
    ) -> None:
        response = client.get(f"/report/{analyzed['report_id']}", headers=INVITE_HEADERS)
        assert response.status_code == 200

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.get("/report/does-not-exist", headers=INVITE_HEADERS)
        assert response.status_code == 404

    def test_response_contains_report_dict(
        self, client: TestClient, analyzed: dict[str, object]
    ) -> None:
        response = client.get(f"/report/{analyzed['report_id']}", headers=INVITE_HEADERS)
        body = response.json()
        assert isinstance(body["report"], dict)
        assert "assessment" in body["report"]

    def test_report_file_hash_matches_analyze_response(
        self, client: TestClient, analyzed: dict[str, object]
    ) -> None:
        response = client.get(f"/report/{analyzed['report_id']}", headers=INVITE_HEADERS)
        assert response.json()["file_hash"] == analyzed["file_hash"]


class TestDeleteReport:
    def test_unknown_id_returns_404(self, client: TestClient) -> None:
        response = client.delete("/report/does-not-exist", headers=INVITE_HEADERS)
        assert response.status_code == 404


class TestAnalyzeFailureModes:
    def test_text_bytes_returns_415(self, client: TestClient) -> None:
        response = client.post(
            "/analyze",
            headers=INVITE_HEADERS,
            files={"file": ("notes.txt", b"plain text, not an image", "text/plain")},
        )
        assert response.status_code == 415

    def test_oversized_bytes_returns_413(self, client: TestClient) -> None:
        oversized = b"x" * (20 * 1024 * 1024 + 1)
        response = client.post(
            "/analyze",
            headers=INVITE_HEADERS,
            files={"file": ("big.jpg", oversized, "image/jpeg")},
        )
        assert response.status_code == 413

    def test_malware_detected_returns_400_without_detection_name(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import examina.pipeline.pipeline as pipeline_module

        def _raise_malware(*args: object, **kwargs: object) -> None:
            raise MalwareDetectedError(
                message="File rejected for security reasons",
                detection_name="Secret-Internal-Signature",
            )

        monkeypatch.setattr(pipeline_module, "scan_for_malware", _raise_malware)
        response = client.post(
            "/analyze",
            headers=INVITE_HEADERS,
            files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")},
        )
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "file_rejected"
        assert "Secret-Internal-Signature" not in response.text

    def test_decompression_bomb_returns_400(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import examina.pipeline.pipeline as pipeline_module

        def _raise_bomb(*args: object, **kwargs: object) -> None:
            raise DecompressionBombError(message="Archive exceeds the maximum allowed size")

        monkeypatch.setattr(pipeline_module, "check_archive_bomb", _raise_bomb)
        response = client.post(
            "/analyze",
            headers=INVITE_HEADERS,
            files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "file_rejected"

    def test_bridge_error_returns_503(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import examina.api.routes.analyze as analyze_module

        class _FailingBridgeClient:
            def get_bridge_version(self) -> str:
                return "bridge:1.0"

            async def health_check(self) -> bool:
                return True

            async def analyze(self, request: BridgeRequest) -> BridgeResult:
                del request
                raise BridgeError(code="BRIDGE_UNAVAILABLE", message="PRISM unreachable")

        monkeypatch.setattr(analyze_module, "get_bridge_client", lambda: _FailingBridgeClient())
        response = client.post(
            "/analyze",
            headers=INVITE_HEADERS,
            files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")},
        )
        assert response.status_code == 503
        assert response.json()["error"] == "analysis_unavailable"

    def test_unexpected_exception_returns_500(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import examina.api.routes.analyze as analyze_module

        def _raise_unexpected(*args: object, **kwargs: object) -> None:
            raise RuntimeError("unexpected internal failure detail")

        monkeypatch.setattr(analyze_module, "assemble_report", _raise_unexpected)
        response = client.post(
            "/analyze",
            headers=INVITE_HEADERS,
            files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")},
        )
        assert response.status_code == 500
        body = response.json()
        assert body["error"] == "internal_error"
        assert "unexpected internal failure detail" not in response.text


class TestFeedback:
    def test_returns_200_with_report_id(
        self, client: TestClient, analyzed: dict[str, object]
    ) -> None:
        response = client.post("/feedback", json={"report_id": analyzed["report_id"]})
        assert response.status_code == 200

    def test_returns_200_without_report_id(self, client: TestClient) -> None:
        response = client.post("/feedback", json={})
        assert response.status_code == 200

    def test_score_of_six_returns_422(self, client: TestClient) -> None:
        response = client.post("/feedback", json={"understandability_score": 6})
        assert response.status_code == 422

    def test_with_changed_assessment_returns_200(self, client: TestClient) -> None:
        response = client.post("/feedback", json={"changed_assessment": "yes_significantly"})
        assert response.status_code == 200

    def test_with_would_use_in_workflow_returns_200(self, client: TestClient) -> None:
        response = client.post("/feedback", json={"would_use_in_workflow": "maybe"})
        assert response.status_code == 200

    def test_invalid_changed_assessment_returns_422(self, client: TestClient) -> None:
        response = client.post("/feedback", json={"changed_assessment": "invalid_value"})
        assert response.status_code == 422


class TestFeedbackDatabaseFailure:
    def test_db_failure_returns_200_anyway(self) -> None:
        class _BrokenSession:
            def add(self, record: object) -> None:
                del record

            def commit(self) -> None:
                raise SQLAlchemyError("simulated database failure")

            def close(self) -> None:
                pass

        def _broken_session_dependency() -> Iterator[_BrokenSession]:
            yield _BrokenSession()

        app = create_app()
        app.dependency_overrides[get_session] = _broken_session_dependency
        with TestClient(app) as broken_client:
            response = broken_client.post("/feedback", json={})
        assert response.status_code == 200


class TestReportIncorrect:
    def test_unknown_report_id_returns_404(self, client: TestClient) -> None:
        response = client.post("/report-incorrect", json={"report_id": "does-not-exist"})
        assert response.status_code == 404

    def test_known_report_id_returns_200(
        self, client: TestClient, analyzed: dict[str, object]
    ) -> None:
        response = client.post("/report-incorrect", json={"report_id": analyzed["report_id"]})
        assert response.status_code == 200
        body = response.json()
        assert "submission_id" in body


class TestRateLimitExceeded:
    def test_report_incorrect_eventually_returns_429(self, client: TestClient) -> None:
        seen_429 = False
        for _ in range(10):
            response = client.post("/report-incorrect", json={"report_id": "does-not-exist"})
            if response.status_code == 429:
                seen_429 = True
                assert response.json()["error"] == "rate_limit_exceeded"
                break
        assert seen_429


class TestAdmin:
    def test_overview_without_admin_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/admin/overview")
        assert response.status_code == 401

    def test_overview_with_correct_admin_token_returns_200(self, client: TestClient) -> None:
        response = client.get("/admin/overview", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert "total_analyses" in response.json()

    def test_feedback_returns_paginated_results(self, client: TestClient) -> None:
        response = client.get("/admin/feedback", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "page" in body
        assert "items" in body

    def test_rules_returns_empty_list(self, client: TestClient) -> None:
        response = client.get("/admin/rules", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert response.json()["rules"] == []

    def test_incorrect_returns_items(self, client: TestClient) -> None:
        response = client.get("/admin/incorrect", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        assert "items" in response.json()


class TestFullWorkflow:
    def test_analyze_then_get_then_delete_then_404(self, client: TestClient) -> None:
        report_id = _upload_jpeg(client)["report_id"]

        get_response = client.get(f"/report/{report_id}", headers=INVITE_HEADERS)
        assert get_response.status_code == 200

        delete_response = client.delete(f"/report/{report_id}", headers=INVITE_HEADERS)
        assert delete_response.status_code == 200

        final_get = client.get(f"/report/{report_id}", headers=INVITE_HEADERS)
        assert final_get.status_code == 404
