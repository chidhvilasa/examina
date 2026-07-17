"""Tests for src/examina/bridge/client.py, local_client.py, remote_client.py, factory.py.

LocalBridgeClient.analyze() calls a real PRISM subprocess since Phase 7;
its own unit tests mock subprocess.run so they stay hermetic and never
require a real PRISM checkout (see tests/integration/test_real_bridge.py
for the real-PRISM-backed tests)."""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

import examina.bridge.local_client as local_client_module
from examina.bridge.factory import get_bridge_client
from examina.bridge.local_client import LocalBridgeClient
from examina.bridge.remote_client import RemoteBridgeClient
from examina.bridge.types import (
    BridgeConfidence,
    BridgeError,
    BridgeFact,
    BridgeHypothesis,
    BridgeRequest,
    BridgeResult,
    BridgeTimelineEvent,
)

VALID_HASH = "b" * 64


def _valid_request() -> BridgeRequest:
    return BridgeRequest(
        file_bytes=b"stub-bytes",
        file_hash=VALID_HASH,
        file_type="JPEG",
        examina_version="0.1.0",
    )


def _valid_result(request_id: UUID | None = None, **overrides: object) -> BridgeResult:
    fields: dict[str, object] = {
        "request_id": request_id or UUID(int=1),
        "bridge_version": "bridge:1.0",
        "prism_version": "stub:1.0",
        "rule_set_version": "stub:1.0",
        "extractor_versions": {"stub": "1.0"},
        "processing_time_ms": 0,
        "facts": [
            BridgeFact(
                fact_id="fact-1",
                statement="Statement.",
                fact_type="STRUCTURAL",
                provenance_source_type="observed",
                extractor="extractor:1.0",
                extraction_confidence=0.9,
                source_reliability=0.9,
                raw_value={},
            )
        ],
        "contradictions": [],
        "hypotheses": [
            BridgeHypothesis(
                hypothesis_id="hyp-1", description="Description.", confidence=0.6, rank=1
            ),
            BridgeHypothesis(
                hypothesis_id="hyp-2", description="Description.", confidence=0.4, rank=2
            ),
        ],
        "timeline": [BridgeTimelineEvent(sequence=1, description="Event.", confidence=0.7)],
        "reconstruction_confidence": BridgeConfidence(
            overall=0.72,
            penalty_from_contradictions=0.0,
            unresolved_contradictions=0,
            active_hypotheses=2,
        ),
        "errors": [],
        "partial_analysis": False,
        "partial_reason": None,
    }
    fields.update(overrides)
    return BridgeResult(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# LocalBridgeClient
# ---------------------------------------------------------------------------


def _valid_bridge_payload() -> dict[str, Any]:
    return {
        "bridge_version": "bridge:1.0",
        "prism_version": "0.3.2",
        "rule_set_version": "1.0.0",
        "extractor_versions": {"jpeg_adapter": "1.0.0"},
        "processing_time_ms": 12,
        "partial_analysis": False,
        "partial_reason": None,
        "errors": [],
        "facts": [
            {
                "fact_id": "fact-1",
                "statement": "This file declares a creation timestamp.",
                "fact_type": "PROVENANCE",
                "provenance_source_type": "declared",
                "extractor": "exif_extractor:1.0.0",
                "extraction_confidence": 0.9,
                "source_reliability": 0.8,
                "raw_value": {},
            }
        ],
        "contradictions": [],
        "hypotheses": [
            {"hypothesis_id": "hyp-1", "description": "First.", "confidence": 0.6, "rank": 1},
        ],
        "timeline": [{"sequence": 1, "description": "Event.", "confidence": 0.7}],
        "reconstruction_confidence": {
            "overall": 0.65,
            "penalty_from_contradictions": 0.0,
            "unresolved_contradictions": 0,
            "active_hypotheses": 1,
        },
    }


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestLocalBridgeClient:
    def _client(self) -> LocalBridgeClient:
        return LocalBridgeClient(prism_path=Path("../PRISM"), python_executable="fake-python")

    def test_analyze_returns_bridge_result_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stdout = json.dumps(_valid_bridge_payload()).encode("utf-8")
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(0, stdout=stdout),
        )
        request = _valid_request()
        result = asyncio.run(self._client().analyze(request))
        assert isinstance(result, BridgeResult)
        assert result.bridge_version == "bridge:1.0"
        assert result.request_id == request.request_id

    def test_analyze_timeout_raises_analysis_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise subprocess.TimeoutExpired(cmd="prism.bridge.cli", timeout=60)

        monkeypatch.setattr(local_client_module.subprocess, "run", _raise)
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "ANALYSIS_TIMEOUT"

    def test_analyze_file_not_found_raises_bridge_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise FileNotFoundError("no such file")

        monkeypatch.setattr(local_client_module.subprocess, "run", _raise)
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "BRIDGE_UNAVAILABLE"

    def test_analyze_unexpected_exception_raises_bridge_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("something odd")

        monkeypatch.setattr(local_client_module.subprocess, "run", _raise)
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "BRIDGE_UNAVAILABLE"

    def test_analyze_nonzero_returncode_with_json_stderr_raises_prism_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stderr = json.dumps(
            {
                "bridge_version": "bridge:1.0",
                "error": True,
                "error_code": "PRISM_ERROR",
                "error_message": "adapter blew up",
            }
        ).encode("utf-8")
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(1, stderr=stderr),
        )
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "PRISM_ERROR"
        assert exc_info.value.message == "adapter blew up"

    def test_analyze_nonzero_returncode_with_non_json_stderr_raises_prism_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(1, stderr=b"not json at all"),
        )
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "PRISM_ERROR"
        assert exc_info.value.message == "PRISM process failed"

    def test_analyze_nonzero_returncode_with_unrecognized_error_code_normalized(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stderr = json.dumps({"error_code": "SOMETHING_ELSE", "error_message": "x"}).encode(
            "utf-8"
        )
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(1, stderr=stderr),
        )
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "PRISM_ERROR"

    def test_analyze_invalid_stdout_json_raises_invalid_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(0, stdout=b"not json"),
        )
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_analyze_stdout_failing_schema_validation_raises_invalid_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stdout = json.dumps({"bridge_version": "bridge:1.0"}).encode("utf-8")
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(0, stdout=stdout),
        )
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_health_check_returns_true_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(0),
        )
        assert asyncio.run(self._client().health_check()) is True

    def test_health_check_returns_false_on_nonzero_returncode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            local_client_module.subprocess,
            "run",
            lambda *a, **k: _FakeCompletedProcess(1),
        )
        assert asyncio.run(self._client().health_check()) is False

    def test_health_check_returns_false_on_os_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise OSError("no python")

        monkeypatch.setattr(local_client_module.subprocess, "run", _raise)
        assert asyncio.run(self._client().health_check()) is False

    def test_health_check_returns_false_on_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise subprocess.TimeoutExpired(cmd="import prism", timeout=5)

        monkeypatch.setattr(local_client_module.subprocess, "run", _raise)
        assert asyncio.run(self._client().health_check()) is False

    def test_get_bridge_version_returns_bridge_1_0(self) -> None:
        assert self._client().get_bridge_version() == "bridge:1.0"

    def test_constructor_defaults_prism_path_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PRISM_PATH", "/env-configured-prism")
        client = LocalBridgeClient()
        assert client.prism_path == Path("/env-configured-prism")

    def test_constructor_defaults_python_executable_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PRISM_PYTHON", "/env/bin/python")
        client = LocalBridgeClient(prism_path=Path("../PRISM"))
        assert client.python_executable == "/env/bin/python"


# ---------------------------------------------------------------------------
# RemoteBridgeClient
# ---------------------------------------------------------------------------


class TestRemoteBridgeClient:
    def _client(self) -> RemoteBridgeClient:
        return RemoteBridgeClient(base_url="http://prism-server:9000", token="shared-secret")

    def test_analyze_raises_bridge_unavailable(self) -> None:
        with pytest.raises(BridgeError) as exc_info:
            asyncio.run(self._client().analyze(_valid_request()))
        assert exc_info.value.code == "BRIDGE_UNAVAILABLE"

    def test_health_check_returns_false(self) -> None:
        assert asyncio.run(self._client().health_check()) is False

    def test_get_bridge_version_returns_bridge_1_0(self) -> None:
        assert self._client().get_bridge_version() == "bridge:1.0"


# ---------------------------------------------------------------------------
# validate_result
# ---------------------------------------------------------------------------


class TestValidateResult:
    def _client(self) -> LocalBridgeClient:
        return LocalBridgeClient(prism_path=Path("../PRISM"))

    def test_valid_result_passes(self) -> None:
        self._client().validate_result(_valid_result())

    def test_bad_bridge_version_raises(self) -> None:
        result = _valid_result()
        result.bridge_version = "not-a-bridge-version"
        with pytest.raises(BridgeError) as exc_info:
            self._client().validate_result(result)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_non_unique_ranks_raises(self) -> None:
        result = _valid_result()
        result.hypotheses = [
            BridgeHypothesis(hypothesis_id="hyp-1", description="D.", confidence=0.6, rank=1),
            BridgeHypothesis(hypothesis_id="hyp-2", description="D.", confidence=0.4, rank=1),
        ]
        with pytest.raises(BridgeError) as exc_info:
            self._client().validate_result(result)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_non_contiguous_ranks_raises(self) -> None:
        result = _valid_result()
        result.hypotheses = [
            BridgeHypothesis(hypothesis_id="hyp-1", description="D.", confidence=0.6, rank=1),
            BridgeHypothesis(hypothesis_id="hyp-2", description="D.", confidence=0.4, rank=3),
        ]
        with pytest.raises(BridgeError) as exc_info:
            self._client().validate_result(result)
        assert exc_info.value.code == "INVALID_RESPONSE"

    def test_partial_true_reason_none_raises(self) -> None:
        result = _valid_result()
        result.partial_analysis = True
        with pytest.raises(BridgeError) as exc_info:
            self._client().validate_result(result)
        assert exc_info.value.code == "INVALID_RESPONSE"


# ---------------------------------------------------------------------------
# get_bridge_client
# ---------------------------------------------------------------------------


class TestGetBridgeClient:
    def test_development_returns_local_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EXAMINA_ENV", "development")
        assert isinstance(get_bridge_client(), LocalBridgeClient)

    def test_unset_returns_local_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("EXAMINA_ENV", raising=False)
        assert isinstance(get_bridge_client(), LocalBridgeClient)

    def test_production_without_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EXAMINA_ENV", "production")
        monkeypatch.delenv("PRISM_BRIDGE_URL", raising=False)
        monkeypatch.delenv("PRISM_BRIDGE_TOKEN", raising=False)
        with pytest.raises(RuntimeError):
            get_bridge_client()

    def test_production_without_token_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EXAMINA_ENV", "production")
        monkeypatch.setenv("PRISM_BRIDGE_URL", "http://prism-server:9000")
        monkeypatch.delenv("PRISM_BRIDGE_TOKEN", raising=False)
        with pytest.raises(RuntimeError):
            get_bridge_client()

    def test_production_with_both_returns_remote_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("EXAMINA_ENV", "production")
        monkeypatch.setenv("PRISM_BRIDGE_URL", "http://prism-server:9000")
        monkeypatch.setenv("PRISM_BRIDGE_TOKEN", "shared-secret")
        assert isinstance(get_bridge_client(), RemoteBridgeClient)
