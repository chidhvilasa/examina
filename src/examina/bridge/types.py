"""
Bridge types — EXAMINA-native translations of PRISM output.

See specs/BRIDGE_SPEC_v1.1.md for the complete field-level contract, and
docs/adr/ADR-0001-bridge-type-schema-amendment.md for why this schema
supersedes specs/BRIDGE_SPEC_v1.0.md. No PRISM-internal schema name
(Fact, Evidence, Contradiction, Hypothesis, rule_id, etc.) appears here;
every field below is an EXAMINA-side concept.
"""

from __future__ import annotations

import re
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class BridgeRequest(BaseModel):
    file_bytes: bytes
    file_hash: str
    file_type: Literal["JPEG", "PNG", "WEBP", "PDF"]
    request_id: UUID = Field(default_factory=uuid4)
    clamav_mode: Literal["enforce", "skip"] = "skip"
    examina_version: str

    @field_validator("file_hash")
    @classmethod
    def _validate_file_hash(cls, value: str) -> str:
        if not _HEX64_RE.match(value):
            raise ValueError("file_hash must be exactly 64 lowercase hex characters")
        return value


class BridgeFact(BaseModel):
    fact_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    fact_type: Literal["STRUCTURAL", "TEMPORAL", "STATISTICAL", "SEMANTIC", "PROVENANCE"]
    provenance_source_type: Literal["declared", "observed", "derived", "inferred"]
    extractor: str = Field(min_length=1)
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    source_reliability: float = Field(ge=0.0, le=1.0)
    raw_value: dict[str, Any]


class BridgeContradiction(BaseModel):
    contradiction_id: str = Field(min_length=1)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    explanation: str = Field(min_length=1)
    confidence_impact: float = Field(ge=-1.0, le=0.0)
    top_resolution: str = Field(min_length=1)


class BridgeHypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)


class BridgeTimelineEvent(BaseModel):
    sequence: int = Field(ge=1)
    description: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class BridgeConfidence(BaseModel):
    overall: float = Field(ge=0.0, le=1.0)
    penalty_from_contradictions: float = Field(ge=0.0, le=1.0)
    unresolved_contradictions: int = Field(ge=0)
    active_hypotheses: int = Field(ge=0)


class BridgeResult(BaseModel):
    request_id: UUID
    bridge_version: str = Field(min_length=1)
    prism_version: str = Field(min_length=1)
    rule_set_version: str = Field(min_length=1)
    extractor_versions: dict[str, str]
    processing_time_ms: int = Field(ge=0)
    facts: list[BridgeFact] = Field(default_factory=list)
    contradictions: list[BridgeContradiction] = Field(default_factory=list)
    hypotheses: list[BridgeHypothesis] = Field(default_factory=list)
    timeline: list[BridgeTimelineEvent] = Field(default_factory=list)
    reconstruction_confidence: BridgeConfidence
    errors: list[str] = Field(default_factory=list)
    partial_analysis: bool = False
    partial_reason: str | None = None

    @model_validator(mode="after")
    def _validate_partial_analysis(self) -> BridgeResult:
        if self.partial_analysis:
            if not self.partial_reason:
                raise ValueError("partial_reason must be set when partial_analysis is True")
        elif self.partial_reason is not None:
            raise ValueError("partial_reason must be None when partial_analysis is False")
        return self

    @model_validator(mode="after")
    def _validate_hypotheses_ranked(self) -> BridgeResult:
        ranks = [h.rank for h in self.hypotheses]
        if len(set(ranks)) != len(ranks):
            raise ValueError("hypotheses ranks must be unique")
        if ranks and set(ranks) != set(range(1, len(ranks) + 1)):
            raise ValueError("hypotheses ranks must be contiguous starting from 1")
        if ranks != sorted(ranks):
            raise ValueError("hypotheses must be sorted by rank ascending")
        return self


class BridgeError(Exception):
    def __init__(
        self,
        code: Literal[
            "BRIDGE_UNAVAILABLE",
            "VERSION_MISMATCH",
            "ANALYSIS_TIMEOUT",
            "PRISM_ERROR",
            "INVALID_RESPONSE",
        ],
        message: str,
        request_id: UUID | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(message)
