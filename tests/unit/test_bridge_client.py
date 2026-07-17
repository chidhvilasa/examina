"""Tests for src/examina/bridge/client.py, local_client.py, remote_client.py, factory.py."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

import pytest

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


class TestLocalBridgeClient:
    def _client(self) -> LocalBridgeClient:
        return LocalBridgeClient(prism_path=Path("../PRISM"))

    def test_analyze_returns_bridge_result(self) -> None:
        result = asyncio.run(self._client().analyze(_valid_request()))
        assert isinstance(result, BridgeResult)

    def test_analyze_returns_bridge_version_1_0(self) -> None:
        result = asyncio.run(self._client().analyze(_valid_request()))
        assert result.bridge_version == "bridge:1.0"

    def test_analyze_returns_exactly_two_facts(self) -> None:
        result = asyncio.run(self._client().analyze(_valid_request()))
        assert len(result.facts) == 2

    def test_analyze_returns_exactly_four_hypotheses(self) -> None:
        result = asyncio.run(self._client().analyze(_valid_request()))
        assert len(result.hypotheses) == 4

    def test_analyze_hypotheses_sorted_by_rank(self) -> None:
        result = asyncio.run(self._client().analyze(_valid_request()))
        ranks = [h.rank for h in result.hypotheses]
        assert ranks == sorted(ranks)

    def test_analyze_returns_prism_version_stub(self) -> None:
        result = asyncio.run(self._client().analyze(_valid_request()))
        assert result.prism_version == "stub:1.0"

    def test_health_check_returns_true(self) -> None:
        assert asyncio.run(self._client().health_check()) is True

    def test_get_bridge_version_returns_bridge_1_0(self) -> None:
        assert self._client().get_bridge_version() == "bridge:1.0"


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
