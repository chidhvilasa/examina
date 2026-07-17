"""LocalBridgeClient — development-mode bridge to a local PRISM subprocess."""

from __future__ import annotations

from pathlib import Path

from examina.bridge.client import BridgeClient
from examina.bridge.types import (
    BridgeConfidence,
    BridgeFact,
    BridgeHypothesis,
    BridgeRequest,
    BridgeResult,
    BridgeTimelineEvent,
)


class LocalBridgeClient(BridgeClient):
    """
    Used in development when PRISM runs as a local subprocess.

    Phase 1 note: `analyze` is a STUB. It returns a fixed, valid
    BridgeResult with realistic-looking placeholder data and does not
    invoke PRISM at all. It must be replaced with a real subprocess/
    in-process call into PRISM's public entry point before this client
    is used against real files (Phase 2 report engine work depends on
    that replacement, not this phase).
    """

    def __init__(self, prism_path: Path, timeout_seconds: int = 60) -> None:
        self.prism_path = prism_path
        self.timeout_seconds = timeout_seconds

    async def analyze(self, request: BridgeRequest) -> BridgeResult:
        """
        STUB — returns fixed placeholder data, never touches PRISM.
        Replaced in Phase 2 when the report engine needs real PRISM
        output to test against.
        """
        result = BridgeResult(
            request_id=request.request_id,
            bridge_version="bridge:1.0",
            prism_version="stub:1.0",
            rule_set_version="stub:1.0",
            extractor_versions={"stub": "1.0"},
            processing_time_ms=0,
            facts=[
                BridgeFact(
                    fact_id="fact-stub-1",
                    statement="This file declares creation metadata consistent with its format.",
                    fact_type="PROVENANCE",
                    provenance_source_type="declared",
                    extractor="stub-extractor:1.0",
                    extraction_confidence=0.9,
                    source_reliability=0.8,
                    raw_value={"stub": True},
                ),
                BridgeFact(
                    fact_id="fact-stub-2",
                    statement="This file's structural layout matches its declared format.",
                    fact_type="STRUCTURAL",
                    provenance_source_type="observed",
                    extractor="stub-extractor:1.0",
                    extraction_confidence=0.85,
                    source_reliability=0.9,
                    raw_value={"stub": True},
                ),
            ],
            contradictions=[],
            hypotheses=[
                BridgeHypothesis(
                    hypothesis_id="hyp-stub-1",
                    description="This file is consistent with an unedited original.",
                    confidence=0.6,
                    rank=1,
                ),
                BridgeHypothesis(
                    hypothesis_id="hyp-stub-2",
                    description="This file shows signs of routine re-encoding only.",
                    confidence=0.25,
                    rank=2,
                ),
                BridgeHypothesis(
                    hypothesis_id="hyp-stub-3",
                    description="This file shows signs consistent with targeted editing.",
                    confidence=0.1,
                    rank=3,
                ),
                BridgeHypothesis(
                    hypothesis_id="hyp-stub-4",
                    description="Insufficient evidence to distinguish between the above.",
                    confidence=0.05,
                    rank=4,
                ),
            ],
            timeline=[
                BridgeTimelineEvent(
                    sequence=1,
                    description="File was created by the declared source application.",
                    confidence=0.7,
                ),
            ],
            reconstruction_confidence=BridgeConfidence(
                overall=0.72,
                penalty_from_contradictions=0.0,
                unresolved_contradictions=0,
                active_hypotheses=4,
            ),
            errors=[],
            partial_analysis=False,
            partial_reason=None,
        )
        self.validate_result(result)
        return result

    async def health_check(self) -> bool:
        """
        STUB — always returns True.
        Real implementation checks subprocess/PRISM availability
        (e.g. that `self.prism_path` exists and PRISM's entry point
        can be invoked).
        """
        return True

    def get_bridge_version(self) -> str:
        return "bridge:1.0"
